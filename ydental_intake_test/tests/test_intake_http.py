import json
import re

from odoo.tests import HttpCase

from .common import key, patient, price, qualify, setup


class TestIntakeHTTP(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def select(self, role='frontdesk', store=None):
        self.authenticate(self.users[role].login, 's05-test-password')
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
