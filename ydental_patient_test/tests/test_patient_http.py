import json
import re
import secrets
from unittest.mock import patch
from urllib.parse import urlencode

from lxml import html
from odoo.tests import HttpCase
from odoo.tools import mute_logger
from odoo.tools.misc import limited_field_access_token

from .common import clinical, create, merge, setup_patient


class TestPatientHTTP(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_patient(cls)

    def select(self, role='frontdesk', store=None):
        self.authenticate(self.users[role].login, 's04-test-password')
        page = self.url_open('/ydental/access')
        self.token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        response = self.url_open('/ydental/access/action', data={'csrf_token': self.token,
            'revision': str(revision), 'operation': 'switch', 'payload': json.dumps({'store_id': (store or self.stores[0]).id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        self.revision = response.json()['revision']

    def action(self, operation, payload, key=None, revision=None):
        return self.url_open('/ydental/patients/action', data={'csrf_token': self.token,
            'key': key or secrets.token_hex(8), 'revision': self.revision if revision is None else revision,
            'operation': operation, 'payload': json.dumps(payload), 'output': 'json'})

    def rpc(self, model, method, args, context=None):
        response = self.url_open('/web/dataset/call_kw/' + model + '/' + method,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {'model': model, 'method': method,
            'args': args, 'kwargs': {'context': dict(context or {}, ydental_revision=self.revision)}}}),
            headers={'Content-Type': 'application/json'})
        return response.json()

    def test_http_create_retry_real_arrival_and_store_policy_render(self):
        self.select()
        self.assertEqual(self.url_open('/ydental/patients').status_code, 200)
        args = {'values': {'name': 'S04 HTTP Synthetic', 'phone': '2025550100'}}
        response = self.action('create', args, key='http-retry')
        self.assertEqual(response.status_code, 200)
        patient = response.json()
        self.assertEqual(self.action('create', args, key='http-retry').json()['id'], patient['id'])
        page = self.url_open('/ydental/patients/%s' % patient['id'])
        self.assertEqual(page.status_code, 200)
        self.assertIn('Manual phone verification', page.text)
        self.assertIn('Not yet recorded', page.text)
        self.assertIn('Policy text or approval needs completion', page.text)
        self.assertEqual(self.action('arrival', {'patient_id': patient['id']}).status_code, 200)
        self.assertNotIn('Not yet recorded', self.url_open('/ydental/patients/%s' % patient['id']).text)

    def test_http_frontdesk_cannot_open_clinical_rpc_search_export_attachment(self):
        person = create(self)
        record_id = clinical(self, person['id'], self.stores[2])['id']
        attachment = self.root['ir.attachment'].create({'name': 'S04 HTTP synthetic clinical.txt',
            'res_model': 'ydental.patient.clinical', 'res_id': record_id, 'raw': b'Synthetic clinical data', 'public': True})
        self.select()
        self.assertNotIn('Open clinical background', self.url_open('/ydental/patients/%s' % person['id']).text)
        self.assertEqual(self.url_open('/ydental/patients/%s/clinical?purpose=diagnosis' % person['id']).status_code, 403)
        for method, args in [('read', [[record_id], ['ydental_allergies']]), ('search_read', [[], ['ydental_allergies']]),
                             ('export_data', [[record_id], ['ydental_allergies']])]:
            result = self.rpc('ydental.patient.clinical', method, args)
            self.assertTrue(result.get('error') or result.get('result') == [])
        self.assertEqual(self.url_open('/web/content/%s?download=true' % attachment.id).status_code, 404)
        token = limited_field_access_token(attachment, 'raw', scope='binary')
        self.assertEqual(self.url_open('/web/content/%s?download=true&access_token=%s' % (
            attachment.id, token)).status_code, 404)

    def test_http_doctor_reads_selected_patient_cross_store_and_rejects_cross_write(self):
        person = create(self)
        record_id = clinical(self, person['id'], self.stores[2], 'S04 CROSS STORE SYNTHETIC') ['id']
        self.select('doctor')
        page = self.url_open('/ydental/patients/%s/clinical?purpose=diagnosis' % person['id'])
        self.assertEqual(page.status_code, 200)
        self.assertIn('S04 CROSS STORE SYNTHETIC', page.text)
        self.assertIn('Cross-store clinical history is read only.', page.text)
        response = self.action('clinical', {'patient_id': person['id'], 'record_id': record_id, 'version': 1,
            'values': {'allergies': 'Forged cross-store write'}})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.root['ydental.access.audit'].search([('ydental_event', '=', 'patient.care.open'),
            ('ydental_user_id', '=', self.users['doctor'].id)]))

    def test_http_forged_care_context_does_not_grant_rpc_history_or_finance(self):
        person = create(self)
        record_id = clinical(self, person['id'], self.stores[2])['id']
        self.select('doctor')
        context = {'ydental_patient_care': {'patient_id': person['id'], 'purpose': 'diagnosis'},
                   'ydental_purpose': 'care', 'allowed_company_ids': self.root.user.company_ids.ids}
        self.assertIn('error', self.rpc('ydental.patient.clinical', 'read', [[record_id], ['ydental_allergies']], context))
        self.assertEqual(self.url_open('/ydental/patients/%s/clinical?purpose=anything' % person['id']).status_code, 422)

    def test_http_native_partner_cannot_edit_notes_or_read_untyped_files(self):
        person = create(self)
        patient = self.root['ydental.patient'].browse(person['id'])
        partner = patient.ydental_partner_id
        attachment = self.root['ir.attachment'].create({'name': 'S04 partner HTTP.txt', 'res_model': 'res.partner',
            'res_id': partner.id, 'raw': b'Synthetic untyped file', 'public': True})
        self.select()
        self.assertIn('error', self.rpc('res.partner', 'write', [[partner.id], {'comment': 'Bypass'}]))
        result = self.rpc('res.partner', 'read', [[partner.id], ['name', 'comment']])
        self.assertFalse(result['result'][0]['comment'])
        self.assertEqual(self.url_open('/web/content/%s?download=true' % attachment.id).status_code, 404)
        self.assertEqual(self.action('clinical', {'patient_id': person['id'], 'values': {'allergies': 'Bypass'}}).status_code, 403)

    def test_http_group_merge_only_and_old_number_search(self):
        a, b = create(self), create(self)
        request = merge(self, a['id'], b['id'])
        args = {'request_id': request['id'], 'version': 1, 'reason': 'HTTP group verified synthetic identity'}
        self.select()
        self.assertEqual(self.action('confirm', args).status_code, 403)
        self.select('manager')
        result = self.action('confirm', args, key='http-confirm')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(self.action('confirm', args, key='http-confirm').json()['result'], 'already_accepted')
        self.assertIn(b['number'], self.url_open('/ydental/patients?q=' + a['number']).text)

    def test_merge_selector_paginates_same_names_and_preserves_legacy_form(self):
        source = create(self, name='Merge source unique')
        candidates = [create(self, name='S13 Same Merge Candidate') for _ in range(53)]
        self.select()
        def page(number):
            return self.url_open('/ydental/patients/%s?%s' % (source['id'], urlencode({
                'merge_q': 'S13 Same Merge Candidate', 'merge_page': number})))
        selected = []
        for number, expected in ((1, 20), (2, 20), (3, 13)):
            response = page(number)
            self.assertEqual(response.status_code, 200, response.text)
            document = html.fromstring(response.content)
            options = document.xpath('//input[@name="target_id"]/@value')
            self.assertEqual(len(options), expected)
            selected.extend(int(value) for value in options)
            self.assertEqual(len(document.xpath('//input[@name="target_id"]/../span[2]')), expected)
            self.assertEqual(bool(document.xpath('//a[text()="下一页"]')), number < 3)
        self.assertEqual(set(selected), {candidate['id'] for candidate in candidates})
        self.assertEqual(len(selected), len(set(selected)))
        self.assertNotIn(source['id'], selected)
        response = self.url_open('/ydental/patients/action', data={'csrf_token': self.token,
            'revision': self.revision, 'key': secrets.token_hex(8), 'operation': 'request_merge',
            'patient_id': source['id'], 'target_id': candidates[0]['id'], 'reason': 'Synthetic legacy form'},
            allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertFalse(self.root['ydental.patient'].browse(source['id']).ydental_merged_into_id)
        self.assertEqual(self.root['ydental.patient.merge'].search_count([
            ('ydental_source_id', '=', source['id']), ('ydental_target_id', '=', candidates[0]['id']),
            ('state', '=', 'requested')]), 1)

    def test_merge_selector_rechecks_permissions_scope_and_patient_state(self):
        source = create(self, name='S13 Merge Source')
        target = create(self, name='S13 Merge Target')
        archived = create(self, name='S13 Merge Archived')
        service = self.service
        service._operate('archive', {'patient_id': archived['id'], 'version': 1, 'reason': 'Synthetic archive'}, secrets.token_hex(8))
        self.select()
        query = '/ydental/patients/%s?%s' % (source['id'], urlencode({'merge_q': 'S13 Merge'}))
        page = self.url_open(query)
        document = html.fromstring(page.content)
        options = document.xpath('//input[@name="target_id"]/@value')
        self.assertIn(str(target['id']), options)
        self.assertNotIn(str(source['id']), options)
        self.assertNotIn(str(archived['id']), options)
        payload = {'source_id': source['id'], 'target_id': source['id'], 'reason': 'Synthetic request'}
        self.assertEqual(self.action('request_merge', payload).status_code, 409)
        payload['target_id'] = archived['id']
        self.assertEqual(self.action('request_merge', payload).status_code, 409)
        self.assertEqual(self.url_open('/ydental/patients/%s?merge_q=S13&merge_page=0' % source['id']).status_code, 400)
        no_csrf = self.url_open('/ydental/patients/action', data={'revision': self.revision,
            'key': secrets.token_hex(8), 'operation': 'request_merge', 'patient_id': source['id'],
            'target_id': target['id'], 'reason': 'Synthetic request'})
        self.assertEqual(no_csrf.status_code, 400)
        self.select('reader')
        page = self.url_open(query)
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('name="target_id"', page.text)
        payload['target_id'] = target['id']
        self.assertEqual(self.action('request_merge', payload).status_code, 403)
        self.select('frontdesk')
        old_revision = self.revision
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'frontdesk': 'read'})
        self.assertEqual(self.action('request_merge', payload).status_code, 403)
        self.assertNotIn('name="target_id"', self.url_open(query).text)
        self.assertEqual(self.action('request_merge', payload, revision=old_revision - 1).status_code, 409)

    def test_merge_selector_rejects_target_changed_after_search_and_cross_store(self):
        source, target, canonical = create(self), create(self), create(self)
        self.select('manager')
        query = '/ydental/patients/%s?%s' % (source['id'], urlencode({'merge_q': target['number']}))
        self.assertIn('value="%s"' % target['id'], self.url_open(query).text)
        request = merge(self, target['id'], canonical['id'])
        self.group._operate('confirm', {'request_id': request['id'], 'version': request['version'],
            'reason': 'Synthetic verified merge'}, secrets.token_hex(8))
        payload = {'source_id': source['id'], 'target_id': target['id'], 'reason': 'Synthetic request'}
        self.assertEqual(self.action('request_merge', payload).status_code, 409)
        response = self.url_open(query)
        self.assertNotIn('value="%s"' % target['id'], response.text)
        self.assertIn('value="%s"' % canonical['id'], response.text)
        self.assertIn(canonical['number'], response.text)
        canonical_query = '/ydental/patients/%s?%s' % (canonical['id'], urlencode({'merge_q': target['number']}))
        canonical_page = self.url_open(canonical_query)
        options = html.fromstring(canonical_page.content).xpath('//input[@name="target_id"]/@value')
        self.assertNotIn(str(canonical['id']), options)
        self.select('manager', self.stores[1])
        payload['target_id'] = canonical['id']
        self.assertEqual(self.action('request_merge', payload).status_code, 403)

    def test_merge_selector_rechecks_archived_target_after_search(self):
        source, target = create(self), create(self)
        self.select()
        query = '/ydental/patients/%s?%s' % (source['id'], urlencode({'merge_q': target['number']}))
        self.assertIn('value="%s"' % target['id'], self.url_open(query).text)
        self.service._operate('archive', {'patient_id': target['id'], 'version': 1,
            'reason': 'Synthetic archive after selection'}, secrets.token_hex(8))
        response = self.action('request_merge', {'source_id': source['id'], 'target_id': target['id'],
            'reason': 'Synthetic request'})
        self.assertEqual(response.status_code, 409, response.text)
        self.assertNotIn('value="%s"' % target['id'], self.url_open(query).text)

    def test_http_csrf_write_revision_and_read_only_permissions(self):
        self.select('reader')
        self.assertNotIn('Create administrative patient identity', self.url_open('/ydental/patients').text)
        self.assertEqual(self.action('create', {'values': {'name': 'Denied'}}).status_code, 403)
        self.assertEqual(self.action('create', {'values': {'name': 'Stale'}}, revision=self.revision - 1).status_code, 409)
        response = self.url_open('/ydental/patients/action', data={'operation': 'create', 'revision': self.revision,
            'key': 'csrf-forged', 'payload': json.dumps({'values': {'name': 'Denied'}})})
        self.assertEqual(response.status_code, 400)

    def test_http_patient_denial_audit_and_audit_failure(self):
        self.select('reader')
        Audit = self.root['ydental.access.audit']
        domain = [('ydental_event', '=', 'patient.action.denied'),
                  ('ydental_user_id', '=', self.users['reader'].id)]
        before = set(Audit.search(domain).ids)
        payload = {'values': {'name': 'S04 denied synthetic'}}
        response = self.action('create', payload)
        self.assertEqual(response.status_code, 403)
        denial = Audit.browse(list(set(Audit.search(domain).ids) - before))
        self.assertEqual(len(denial), 1)
        self.assertEqual(denial.ydental_result, 'denied')
        self.assertEqual(denial.ydental_store_id, self.stores[0])

        before = set(Audit.search(domain).ids)
        response = self.action('create', payload, revision=self.revision - 1)
        self.assertEqual(response.status_code, 409)
        self.assertIn('version_conflict', response.json()['error'])
        denial = Audit.browse(list(set(Audit.search(domain).ids) - before))
        self.assertEqual(len(denial), 1)
        self.assertEqual(denial.ydental_result, 'denied')

        model = type(self.root['ydental.access.service'])
        with mute_logger('odoo.addons.ydental_patient.controllers.patient'), \
                patch.object(model, '_audit', side_effect=RuntimeError('synthetic audit failure')):
            response = self.action('create', payload)
        self.assertEqual(response.status_code, 403)
        self.assertIn('access_denied', response.json()['error'])
        with mute_logger('odoo.addons.ydental_patient.controllers.patient'), \
                patch.object(model, '_denial', side_effect=RuntimeError('synthetic log failure')):
            response = self.action('create', payload)
        self.assertEqual(response.status_code, 403)
        self.assertIn('access_denied', response.json()['error'])

        original_lookup = model._existing_session_for_key
        calls = []
        def audit_lookup(service, key):
            calls.append(key)
            if len(calls) == 1:
                return original_lookup(service, key)
            raise RuntimeError('synthetic audit lookup failure')
        with mute_logger('odoo.addons.ydental_patient.controllers.patient'), \
                patch.object(model, '_existing_session_for_key', autospec=True, side_effect=audit_lookup):
            response = self.action('create', payload)
        self.assertEqual(response.status_code, 403)
        self.assertIn('access_denied', response.json()['error'])
        self.assertEqual(len(calls), 2)

        before_sessions = set(self.root['ydental.access.session'].search([]).ids)
        calls = []
        def missing_audit_session(service, key):
            calls.append(key)
            return original_lookup(service, key) if len(calls) == 1 else service.env['ydental.access.session']
        with patch.object(model, '_existing_session_for_key', autospec=True, side_effect=missing_audit_session):
            response = self.action('create', payload)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(calls), 2)
        self.assertEqual(set(self.root['ydental.access.session'].search([]).ids), before_sessions)

    def test_http_selected_patient_attachment_scope_and_revocation(self):
        a, b = create(self), create(self)
        record_id = clinical(self, a['id'], self.stores[2])['id']
        attachment = self.root['ir.attachment'].create({'name': 'S04 scoped.txt', 'res_model': 'ydental.patient.clinical',
            'res_id': record_id, 'raw': b'S04 synthetic authorized attachment', 'public': True})
        self.select('doctor')
        url = '/ydental/patients/%s/attachment/%s?purpose=diagnosis'
        self.assertEqual(self.url_open(url % (a['id'], attachment.id)).status_code, 200)
        self.assertEqual(self.url_open(url % (b['id'], attachment.id)).status_code, 403)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        self.assertEqual(self.url_open(url % (a['id'], attachment.id)).status_code, 403)
