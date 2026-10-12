from datetime import timedelta
import json
import re

from odoo import fields
from odoo.tests import HttpCase

from .common import clinical_source, key, patient, price, qualify, setup


class TestIntakeHTTP(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def select(self, role='frontdesk', store=None, user=None):
        self.authenticate((user or self.users[role]).login, 's05-test-password')
        page = self.url_open('/ydental/access')
        self.token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        rev = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        response = self.url_open('/ydental/access/action', data={'csrf_token': self.token, 'revision': rev,
            'operation': 'switch', 'payload': json.dumps({'store_id': (store or self.stores[0]).id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        self.revision = response.json()['revision']

    def action(self, operation, payload, request_key=None, revision=None):
        return self.url_open('/ydental/intake/action', data={'csrf_token': self.token, 'key': request_key or key(),
            'revision': self.revision if revision is None else revision, 'operation': operation,
            'payload': json.dumps(payload), 'output': 'json'})

    def rpc(self, model, method, args, context=None):
        return self.url_open('/web/dataset/call_kw/' + model + '/' + method, data=json.dumps({
            'jsonrpc': '2.0', 'method': 'call', 'id': 1, 'params': {'model': model, 'method': method,
                'args': args, 'kwargs': {'context': dict(context or {}, ydental_revision=self.revision)}}}),
            headers={'Content-Type': 'application/json'}).json()

    def test_http_arrival_report_void_idempotency(self):
        q = qualify(self)
        self.select()
        self.assertEqual(self.url_open('/ydental/intake').status_code, 200)
        self.assertEqual(self.rpc('ydental.intake.task', 'read', [[q['task_id']], ['name']])['result'][0]['name'], self.root['ydental.intake.task'].browse(q['task_id']).name)
        self.assertEqual(self.action('arrive', {'patient_id': q['patient_id']}).status_code, 200)
        args = {'task_id': q['task_id'], 'version': q['task_version']}
        response = self.action('report', args, 'http-report')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.action('report', args, 'http-report').json()['id'], response.json()['id'])
        self.assertEqual(self.action('void', {'task_id': q['task_id'], 'version': response.json()['version'],
            'reason': 'HTTP position only void', 'cancel_qualification': False}).status_code, 200)
        self.assertEqual(self.root['ydental.intake.entitlement'].browse(q['id']).state, 'held')

    def test_http_permissions_csrf_stale_scope_and_private_actions(self):
        person = patient(self)
        self.select('reader')
        self.assertNotIn('Acquire qualification', self.url_open('/ydental/intake').text)
        self.assertEqual(self.action('arrive', {'patient_id': person}).status_code, 403)
        self.assertEqual(self.action('arrive', {'patient_id': person}, revision=self.revision - 1).status_code, 409)
        response = self.url_open('/ydental/intake/action', data={'operation': 'arrive', 'revision': self.revision,
            'key': key(), 'payload': json.dumps({'patient_id': person})})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.action('start', {'task_id': 1, 'version': 1}).status_code, 403)
        self.assertIn('error', self.rpc('ydental.intake.service', '_operate', ['arrive', {'patient_id': person}, key()]))

    def test_http_native_and_business_state_bypass_blocked(self):
        q = qualify(self)
        version = price(self)
        self.select('manager')
        self.assertIn('error', self.rpc('ydental.intake.task', 'write', [[q['task_id']], {'state': 'started'}], {'ydental_intake_mutation': True}))
        rule_id = self.root['ydental.intake.price'].browse(version['id']).ydental_rule_id.id
        self.assertIn('error', self.rpc('product.pricelist.item', 'write', [[rule_id], {'fixed_price': 0}]))
        self.assertIn('error', self.rpc('product.template', 'write', [[self.catalogs[0].ydental_product_id.product_tmpl_id.id], {'name': 'Native bypass'}]))
        self.select('frontdesk', self.stores[1])
        self.assertEqual(self.action('cancel', {'record_id': q['id'], 'version': q['version'], 'reason': 'Cross-store'}).status_code, 403)

    def test_http_price_publish_snapshot_missing_and_unpublished_policy(self):
        price(self)
        self.select('manager')
        self.assertEqual(self.url_open('/ydental/intake/prices').status_code, 200)
        args = {'catalog_id': self.catalogs[0].id, 'currency_id': self.currency.id, 'quantity': 1, 'source': 'HTTP demo source', 'policy': 'demo_confirmation'}
        frozen = self.action('snapshot', args, 'http-snapshot')
        self.assertEqual(frozen.status_code, 200, frozen.text)
        self.assertEqual(frozen.json()['amount'], 600)
        self.assertEqual(self.action('snapshot', args, 'http-snapshot').json()['id'], frozen.json()['id'])
        self.assertEqual(self.action('snapshot', dict(args, catalog_id=self.catalogs[1].id, source='HTTP missing')).status_code, 409)
        self.assertEqual(self.action('snapshot', dict(args, policy='production')).status_code, 409)
        self.select('reader')
        self.assertNotIn('id="demo-snapshot"', self.url_open('/ydental/intake/prices').text)
        self.assertEqual(self.action('snapshot', dict(args, source='readonly-denied')).status_code, 403)
        self.select()
        self.assertEqual(self.url_open('/ydental/intake/prices').status_code, 403)
        self.assertEqual(self.action('catalog', {}).status_code, 403)

    def test_http_revocation_next_request_no_read_or_write(self):
        q = qualify(self)
        self.select()
        self.assertEqual(self.url_open('/ydental/intake').status_code, 200)
        self.admin._grant(self.users['frontdesk'].id, self.stores[0].id, {'frontdesk': 'none'})
        self.assertEqual(self.action('arrive', {'patient_id': q['patient_id']}).status_code, 403)
        self.assertTrue(self.rpc('ydental.intake.task', 'read', [[q['task_id']], ['name']]).get('error'))

    def test_http_missing_capability_atomic_registration(self):
        self.select()
        response = self.action('register', {'patient_id': patient(self), 'mapping_id': self.mappings[0][2].id,
            'start': '2099-01-01 09:00:00', 'end': '2099-01-01 10:00:00'})
        self.assertEqual(response.status_code, 409)
        self.assertFalse(self.root['ydental.intake.task'].search([('ydental_mapping_id', '=', self.mappings[0][2].id)]))

    def test_http_untyped_task_files_and_payload_field_injection_denied(self):
        q = qualify(self)
        attachment = self.root['ir.attachment'].create({'name': 'S05 synthetic untyped task.txt',
            'res_model': 'ydental.intake.task', 'res_id': q['task_id'], 'raw': b'SYNTHETIC ONLY', 'public': True})
        self.select('manager')
        self.assertEqual(self.url_open('/web/content/%s?download=true' % attachment.id).status_code, 404)
        self.assertEqual(self.action('reserve', {'patient_id': q['patient_id'], 'mapping_id': self.mappings[0][0].id,
            'start': '2099-01-01 09:00:00', 'end': '2099-01-01 10:00:00', 'doctor_id': self.users['manager'].id}).status_code, 409)
        self.assertEqual(self.root['ydental.intake.entitlement'].search_count([('ydental_patient_id', '=', q['patient_id'])]), 1)

    def test_http_cross_store_timed_and_untimed_referral_reception(self):
        q = clinical_source(self, qualify(self))
        args = {'source_task_id': q['task_id'], 'version': q['task_version'], 'mapping_id': self.mappings[1][0].id,
            'reason': 'HTTP controlled source referral'}
        self.select('doctor')
        self.assertEqual(self.action('refer_timed', dict(args, start=fields.Datetime.to_string(self.start), end=fields.Datetime.to_string(self.end))).status_code, 403)
        timed = self.doctor._synthetic_referral_action('refer_timed', dict(args, start=fields.Datetime.to_string(self.start), end=fields.Datetime.to_string(self.end)), key())
        self.assertEqual(self.slots[1][0].ydental_reservation_free, 1)
        self.assertEqual(self.action('refer_untimed', dict(args, valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=7)))).status_code, 403)
        untimed = self.doctor._synthetic_referral_action('refer_untimed', dict(args, valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=7))), key())
        self.assertEqual(self.slots[1][0].ydental_walkin_free, 4)
        self.select('frontdesk', self.stores[1])
        self.assertEqual(self.action('arrive', {'patient_id': q['patient_id']}).status_code, 200)
        t = timed
        self.assertEqual(self.action('report', {'task_id': t['task_id'], 'version': t['task_version']}).status_code, 200)
        self.assertEqual(self.slots[1][0].ydental_reservation_free, 1)
        r = untimed
        reception = self.action('accept_referral', {'record_id': r['id'], 'version': r['version'],
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)})
        self.assertEqual(reception.status_code, 200, reception.text)
        self.assertEqual(self.slots[1][0].ydental_walkin_free, 3)

    def test_http_rework_group_without_price_and_live_group_revocation(self):
        self.admin._grant(self.users['manager'].id, self.stores[0].id, {'price': 'none'})
        self.select('manager')
        page = self.url_open('/ydental/intake/prices')
        self.assertEqual(page.status_code, 200)
        self.assertIn('id="create-catalog"', page.text)
        self.assertNotIn('id="demo-snapshot"', page.text)
        self.assertNotIn('value="mapping"', page.text)
        args = {'code': 's05_http_group_' + key(), 'name': 'S05 Group No Price', 'kind': 'care',
            'capability_id': self.capabilities[0].id, 'uom_id': self.uom.id}
        c = self.action('catalog', args)
        self.assertEqual(c.status_code, 200, c.text)
        item = c.json()
        edit = self.action('catalog_edit', {'record_id': item['id'], 'version': item['version'], 'name': 'S05 Renamed No Price', 'active': False})
        self.assertEqual(edit.status_code, 200, edit.text)
        record = self.root['ydental.intake.catalog'].browse(item['id'])
        native = self.rpc('product.template', 'read', [[record.ydental_product_id.product_tmpl_id.id], ['name', 'active']])
        self.assertEqual(native['result'][0]['name'], 'S05 Renamed No Price')
        self.assertFalse(native['result'][0]['active'])
        for operation in ('mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot'):
            self.assertEqual(self.action(operation, {}).status_code, 403)
        self.users['manager'].write({'group_ids': [fields.Command.unlink(self.root.ref('ydental_access.ydental_group_manager').id)]})
        self.assertEqual(self.action('catalog', args).status_code, 403)
        self.assertEqual(self.url_open('/ydental/intake/prices').status_code, 403)

    def test_http_rework_catalog_only_group_has_no_store_data_authority(self):
        self.select('catalog')
        self.assertEqual(self.url_open('/ydental/intake/prices').status_code, 200)
        self.assertIn('result', self.rpc('ydental.intake.catalog', 'read', [[self.catalogs[0].id], ['name']]))
        self.assertIn('result', self.rpc('product.template', 'read', [[self.catalogs[0].ydental_product_id.product_tmpl_id.id], ['name']]))
        self.assertIn('error', self.rpc('ydental.intake.mapping', 'read', [[self.mappings[0][0].id], ['name']]))
        for operation in ('mapping', 'price', 'snapshot'):
            self.assertEqual(self.action(operation, {}).status_code, 403)

    def test_http_rework_future_reservation_rejected_same_day_early_zero_balance(self):
        from .common import make_slot
        future_start, future_end = self.start + timedelta(days=1), self.end + timedelta(days=1)
        slot = make_slot(self, self.group, self.stations[0][0], future_start, future_end, total=3)
        q = qualify(self, start=future_start, end=future_end)
        self.select()
        self.assertEqual(self.action('arrive', {'patient_id': q['patient_id']}).status_code, 200)
        response = self.action('report', {'task_id': q['task_id'], 'version': q['task_version']})
        self.assertEqual(response.status_code, 409)
        self.assertIn('reporting_date_mismatch', response.text)
        self.assertEqual(slot.ydental_reservation_free, 0)
        self.assertEqual(self.root['ydental.intake.task'].browse(q['task_id']).state, 'pending')
        for model in ('ydental.intake.position', 'ydental.intake.test.queue'):
            self.assertFalse(self.root[model].search([('ydental_task_id', '=', q['task_id'])]))
        start, end = self.start + timedelta(hours=3), self.end + timedelta(hours=3)
        today = make_slot(self, self.group, self.stations[0][0], start, end, total=3)
        same_day = qualify(self, start=start, end=end)
        self.assertEqual(self.action('arrive', {'patient_id': same_day['patient_id']}).status_code, 200)
        report = self.action('report', {'task_id': same_day['task_id'], 'version': same_day['task_version']})
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(today.ydental_reservation_free, 0)

    def test_http_rework_cross_legal_trusted_source_and_arbitrary_target_denial(self):
        from .common import cross_legal_target
        store, desk, mapping, slot, manager, user = cross_legal_target(self)
        self.admin._remove(self.users['doctor'].id, self.stores[1].id)
        q = clinical_source(self, qualify(self))
        args = {'source_task_id': q['task_id'], 'version': q['task_version'], 'mapping_id': mapping.id,
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end), 'reason': 'HTTP cross-legal stand-in'}
        self.select('doctor')
        for op in ('refer_timed', 'refer_untimed'):
            self.assertEqual(self.action(op, args).status_code, 403)
            self.assertIn('error', self.rpc('ydental.intake.service', '_referral_action', [op, args, key(), {'actor_id': self.users['doctor'].id}], {'ydental_referral_permit': True}))
        timed = self.doctor._synthetic_referral_action('refer_timed', args, key())
        untimed_args = {k: v for k, v in args.items() if k not in ('start', 'end')}
        untimed = self.doctor._synthetic_referral_action('refer_untimed', dict(untimed_args,
            valid_until=fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=7))), key())
        self.assertNotIn(store.company_id, self.users['doctor'].company_ids)
        self.assertFalse(self.admin._membership(self.users['doctor'].id, store.id))
        for op, payload in [('reserve', {'patient_id': q['patient_id'], 'mapping_id': mapping.id, 'start': args['start'], 'end': args['end']}),
                ('cancel', {'record_id': timed['id'], 'version': timed['version'], 'reason': 'HTTP forbidden target'}), ('mapping_edit', {}), ('price', {})]:
            self.assertEqual(self.action(op, payload).status_code, 403)
        self.assertIn('error', self.rpc('ydental.intake.task', 'write', [[timed['task_id']], {'state': 'cancelled'}]))
        switch = self.url_open('/ydental/access/action', data={'csrf_token': self.token, 'revision': self.revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': store.id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 403)
        self.select(store=store, user=user)
        self.assertEqual((slot.ydental_reservation_free, slot.ydental_walkin_free), (1, 4))
        result = self.action('accept_referral', {'record_id': untimed['id'], 'version': untimed['version'],
            'start': args['start'], 'end': args['end']})
        self.assertEqual(result.status_code, 200, result.text)
        self.assertEqual((slot.ydental_reservation_free, slot.ydental_walkin_free), (1, 3))
