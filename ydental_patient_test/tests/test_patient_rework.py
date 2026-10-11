import secrets

from odoo.exceptions import AccessError
from odoo.tests import TransactionCase

from .common import bind, clinical, create, merge, setup_patient


class TestPatientRework(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_patient(cls)

    def protected_partners(self):
        person = create(self, name='S04 Protected Primary', phone='+1 202 555 0100', email='primary@example.invalid')
        contact = self.service._operate('contact', {'patient_id': person['id'], 'name': 'S04 Protected Guardian',
            'relation': 'guardian', 'relationship': 'Declared parent', 'phone': '+1 202 555 0101',
            'email': 'guardian@example.invalid'}, secrets.token_hex(8))
        return self.root['ydental.patient'].browse(person['id']).ydental_partner_id | self.root[
            'ydental.patient.contact'].browse(contact['id']).ydental_partner_id

    def test_r1_none_contacts_all_queries_export_and_ordinary_partner(self):
        protected = self.protected_partners()
        none = bind(self, self.users['none'], 'none-native')
        self.admin._grant(self.users['none'].id, self.stores[0].id, {'export': 'write'})
        partners = none.env['res.partner']
        protected.read(['name', 'phone', 'email'])  # Preload sudo data/cache.
        for record in protected.with_env(none.env):
            with self.assertRaises(AccessError):
                record.read(['name', 'phone', 'email'])
            with self.assertRaises(AccessError):
                record.export_data(['name', 'phone', 'email'])
        for field, value in [('name', 'S04 Protected'), ('phone', '202'), ('email', '@example.invalid')]:
            domain = [('id', 'in', protected.ids), (field, 'ilike', value)]
            self.assertFalse(partners.search(domain))
            self.assertEqual(partners.search_read(domain, ['name', 'phone', 'email']), [])
            self.assertFalse(partners.name_search('S04 Protected', domain=domain))
            self.assertEqual(partners.search_count(domain), 0)
            self.assertEqual(partners.read_group(domain, ['id:count'], ['id']), [])
            self.assertEqual(partners._read_group(domain, ['id'], ['__count']), [])
        ordinary = self.root['res.partner'].create({'name': 'S04 Ordinary Contact', 'email': 'ordinary@example.invalid'})
        self.assertEqual(partners.browse(ordinary.id).read(['name'])[0]['name'], ordinary.name)
        self.assertEqual(partners.search([('id', '=', ordinary.id)]).ids, [ordinary.id])
        self.assertEqual(partners.browse(ordinary.id).export_data(['name'])['datas'], [[ordinary.name]])
        with self.assertRaises(AccessError):
            none.with_context(ydental_patient_partner_read=True).env['res.partner'].browse(protected.id if len(protected) == 1 else protected[0].id).read(['name'])

    def test_r1_live_revocation_primary_and_guardian_and_export_dual_permission(self):
        protected = self.protected_partners().with_env(self.service.env)
        self.assertEqual(len(protected.read(['name', 'phone', 'email'])), 2)
        self.assertEqual(len(protected.export_data(['name'])['datas']), 2)
        with self.assertRaises(AccessError):
            protected.with_env(self.reader.env).export_data(['name'])
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'export': 'write'})
        with self.assertRaises(AccessError):
            protected.read(['name', 'phone', 'email'])
        self.assertFalse(self.service.env['res.partner'].search([('id', 'in', protected.ids)]))
        self.assertFalse(self.service.env['res.partner'].with_context(ydental_patient_partner_read=True).search([('id', 'in', protected.ids)]))
        self.assertTrue(self.reader.env['res.partner'].browse(protected.ids).read(['name']))
        self.assertTrue(self.doctor.env['res.partner'].browse(protected.ids).read(['name']))

    def test_r2_b_only_requires_explicit_relation_without_arrival(self):
        b = bind(self, self.manager, 'b-only', self.stores[1])
        person = create(self, service=b)
        history = clinical(self, person['id'], self.stores[1])['id']
        patient = self.root['ydental.patient'].browse(person['id'])
        access = self.doctor.env['ydental.access.service']
        with self.assertRaises(AccessError):
            access._patient_care(person['id'], 'diagnosis')
        with self.assertRaises(AccessError):
            self.doctor._operate('clinical', {'patient_id': person['id'], 'values': {'allergies': 'Denied'}}, 'no-relation')
        self.assertFalse(self.service._current_relation(patient, self.stores[0], required=False))
        result = self.service._operate('relation', {'patient_id': person['id']}, 'explicit-a')
        relation = self.root['ydental.patient.relation'].browse(result['id'])
        self.assertFalse(relation.ydental_first_arrival)
        care = access._patient_care(person['id'], 'history_review')
        self.assertEqual(care.env['ydental.patient.clinical'].browse(history).read(['ydental_allergies'])[0]['id'], history)
        local = clinical(self, person['id'])['id']
        self.assertEqual(self.root['ydental.patient.clinical'].browse(local).ydental_store_id, self.stores[0])
        self.assertFalse(relation.ydental_first_arrival)
        other = create(self)
        replacement = self.service._current_relation(self.root['ydental.patient'].browse(other['id']), self.stores[0])
        relation._save({'ydental_superseded_by_id': replacement.id})
        with self.assertRaises(AccessError):
            care.env['ydental.patient.clinical'].browse(history).read(['ydental_allergies'])
        with self.assertRaises(AccessError):
            self.doctor.env['ydental.patient.clinical'].browse(local).read(['ydental_allergies'])
        with self.assertRaises(AccessError):
            self.doctor._operate('clinical', {'patient_id': person['id'], 'record_id': local, 'version': 1,
                'values': {'allergies': 'Denied update'}}, 'inactive-relation')

    def test_r2_merge_canonical_current_relation_and_old_scope(self):
        source, target = create(self), create(self)
        historical = clinical(self, source['id'], self.stores[2])['id']
        old_care = self.doctor.env['ydental.access.service']._patient_care(source['id'], 'diagnosis')
        request = merge(self, source['id'], target['id'])
        self.group._operate('confirm', {'request_id': request['id'], 'version': 1, 'reason': 'Verified synthetic merge'}, 'merge-relation')
        with self.assertRaises(AccessError):
            old_care.env['ydental.patient.clinical'].browse(historical).read(['ydental_allergies'])
        current = self.service._current_relation(self.root['ydental.patient'].browse(source['id']), self.stores[0])
        self.assertEqual(current.ydental_patient_id.id, target['id'])
        self.assertFalse(current.ydental_superseded_by_id)
        care = self.doctor.env['ydental.access.service']._patient_care(source['id'], 'diagnosis')
        self.assertEqual(care.env['ydental.patient.clinical'].browse(historical).read(['ydental_allergies'])[0]['id'], historical)
        source_history = self.root['ydental.patient.relation'].search([('ydental_patient_id', '=', source['id']),
            ('ydental_store_id', '=', self.stores[0].id)])
        self.assertTrue(source_history.ydental_superseded_by_id)
        current._save({'ydental_superseded_by_id': source_history.id})
        with self.assertRaises(AccessError):
            self.doctor.env['ydental.access.service']._patient_care(source['id'], 'diagnosis')
