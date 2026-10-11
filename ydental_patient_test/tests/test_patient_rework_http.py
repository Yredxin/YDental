import secrets

from odoo.tools.misc import limited_field_access_token
from odoo.tests import new_test_user

from .common import bind, clinical, create
from .test_patient_http import TestPatientHTTP


class TestPatientReworkHTTP(TestPatientHTTP):
    # Only the new methods are collected here; original HTTP tests still run
    # from their original class. Reuse its real authentication/RPC helpers.

    def partners(self):
        person = create(self, name='S04 HTTP Protected', phone='+1 202 555 0100', email='patient@example.invalid')
        result = self.service._operate('contact', {'patient_id': person['id'], 'name': 'S04 HTTP Guardian',
            'relation': 'guardian', 'relationship': 'Declared parent', 'phone': '+1 202 555 0101',
            'email': 'guardian@example.invalid'}, secrets.token_hex(8))
        return self.root['ydental.patient'].browse(person['id']).ydental_partner_id | self.root[
            'ydental.patient.contact'].browse(result['id']).ydental_partner_id

    def test_http_r1_none_native_contacts_queries_export_ordinary(self):
        partners = self.partners()
        self.admin._grant(self.users['none'].id, self.stores[0].id, {'export': 'write'})
        ordinary = self.root['res.partner'].create({'name': 'S04 HTTP Ordinary'})
        self.select('none')
        for partner in partners:
            self.assertIn('error', self.rpc('res.partner', 'read', [[partner.id], ['name', 'phone', 'email']]))
            self.assertIn('error', self.rpc('res.partner', 'export_data', [[partner.id], ['name', 'phone', 'email']]))
        for field, value in [('name', 'S04 HTTP'), ('phone', '202'), ('email', '@example.invalid')]:
            domain = [('id', 'in', partners.ids), (field, 'ilike', value)]
            for method, args in [('search', [domain]), ('search_read', [domain, ['name', 'phone', 'email']]),
                                 ('name_search', ['S04 HTTP', domain]), ('search_count', [domain]),
                                 ('read_group', [domain, ['id'], ['__count']])]:
                result = self.rpc('res.partner', method, args)
                self.assertIn(result.get('result'), ([], 0), result)
        self.assertEqual(self.rpc('res.partner', 'read', [[ordinary.id], ['name']])['result'][0]['name'], ordinary.name)
        # Native Contacts for an ordinary internal account without the YDental
        # application group or any store session retain Odoo's permissions.
        internal = new_test_user(self.root, login='s04_plain_' + self.suffix,
            password='s04-test-password', groups='base.group_user')
        self.authenticate(internal.login, 's04-test-password')
        self.assertEqual(self.rpc('res.partner', 'read', [[ordinary.id], ['name']])['result'][0]['name'], ordinary.name)
        self.assertIn('error', self.rpc('res.partner', 'read', [partners.ids, ['name']]))
        self.assertEqual(self.rpc('res.partner', 'search_count', [[('id', 'in', partners.ids)]])['result'], 0)

    def test_http_r1_revoke_next_request_and_image_token_guardian(self):
        partners = self.partners()
        self.select()
        self.assertEqual(len(self.rpc('res.partner', 'read', [partners.ids, ['name', 'phone', 'email']])['result']), 2)
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'frontdesk': 'none', 'export': 'write'})
        self.assertIn('error', self.rpc('res.partner', 'read', [partners.ids, ['name', 'phone', 'email']]))
        self.assertEqual(self.rpc('res.partner', 'search_count', [[('id', 'in', partners.ids)]])['result'], 0)
        for partner in partners:
            token = limited_field_access_token(partner, 'avatar_128', scope='binary')
            for access_token in ('', token):
                # download=true avoids the native image controller's harmless
                # placeholder response on denied/missing images.
                url = '/web/image?model=res.partner&id=%s&field=avatar_128&download=true' % partner.id
                if access_token:
                    url += '&access_token=' + access_token
                self.assertIn(self.url_open(url).status_code, (403, 404))

    def test_http_r2_b_only_explicit_a_relation_then_care_and_write(self):
        b = bind(self, self.manager, 'http-b-only', self.stores[1])
        person = create(self, name='S04 HTTP B Only', service=b)
        history = clinical(self, person['id'], self.stores[1])['id']
        self.select('doctor')
        url = '/ydental/patients/%s/clinical?purpose=diagnosis' % person['id']
        self.assertEqual(self.url_open(url).status_code, 403)
        self.assertIn('error', self.rpc('ydental.patient.clinical', 'read', [[history], ['ydental_allergies']]))
        self.assertEqual(self.action('clinical', {'patient_id': person['id'], 'values': {'allergies': 'Denied'}}).status_code, 403)
        domain = [('ydental_patient_id', '=', person['id']), ('ydental_store_id', '=', self.stores[0].id)]
        self.assertFalse(self.root['ydental.patient.relation'].search(domain))
        self.select()
        self.assertEqual(self.action('relation', {'patient_id': person['id']}).status_code, 200)
        relation = self.root['ydental.patient.relation'].search(domain)
        self.assertEqual(len(relation), 1)
        self.assertFalse(relation.ydental_first_arrival)
        self.select('doctor')
        self.assertEqual(self.url_open(url).status_code, 200)
        result = self.action('clinical', {'patient_id': person['id'], 'values': {'allergies': 'S04 HTTP A allowed'}})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.rpc('ydental.patient.clinical', 'read', [[result.json()['id']], ['ydental_allergies']])['result'][0]['ydental_allergies'], 'S04 HTTP A allowed')
        self.assertFalse(relation.ydental_first_arrival)
        self.assertTrue(self.root['ydental.access.audit'].search([('ydental_event', '=', 'patient.care.open'),
            ('ydental_user_id', '=', self.users['doctor'].id), ('ydental_target_id', '=', person['id'])]))
        self.assertEqual(self.action('clinical', {'patient_id': person['id'], 'record_id': history, 'version': 1,
            'values': {'allergies': 'Cross-store denied'}}).status_code, 403)

    def test_http_r2_relation_invalidated_next_request_denied(self):
        person = create(self)
        history = clinical(self, person['id'], self.stores[2])['id']
        local = clinical(self, person['id'])['id']
        self.select('doctor')
        url = '/ydental/patients/%s/clinical?purpose=diagnosis' % person['id']
        self.assertEqual(self.url_open(url).status_code, 200)
        relation = self.service._current_relation(self.root['ydental.patient'].browse(person['id']), self.stores[0])
        other = create(self)
        replacement = self.service._current_relation(self.root['ydental.patient'].browse(other['id']), self.stores[0])
        relation._save({'ydental_superseded_by_id': replacement.id})
        self.assertEqual(self.url_open(url).status_code, 403)
        self.assertIn('error', self.rpc('ydental.patient.clinical', 'read', [[local], ['ydental_allergies']]))
        self.assertEqual(self.action('clinical', {'patient_id': person['id'], 'record_id': local, 'version': 1,
            'values': {'allergies': 'Denied'}}).status_code, 403)
