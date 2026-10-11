import json
import re
import secrets
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase

from .common import setup_supply, slot


class TestSupplyHTTP(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_supply(cls)

    def select(self, store=None):
        page = self.url_open('/ydental/access')
        self.token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        response = self.url_open('/ydental/access/action', data={'csrf_token': self.token,
            'revision': str(revision), 'operation': 'switch', 'payload': json.dumps({'store_id': (store or self.stores[0]).id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200)
        self.revision = response.json()['revision']

    def action(self, operation, payload, revision=None):
        return self.url_open('/ydental/supply/action', data={'csrf_token': self.token, 'key': secrets.token_hex(8),
            'revision': str(self.revision if revision is None else revision), 'operation': operation, 'payload': json.dumps(payload), 'output': 'json'})

    def test_http_week_today_forms_and_private_downstream(self):
        self.authenticate('s03_writer', 's03-test-password')
        self.select()
        page = self.url_open('/ydental/supply?group_by=person')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Weekly plan', page.text)
        self.assertIn('Batch template', page.text)
        self.assertIn('Shared capacity', page.text)
        response = self.action('assign', {'user_id': self.staff.id, 'station_id': self.stations[0].id,
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)})
        self.assertEqual(response.status_code, 200)
        self.assertIn('S03', self.url_open('/ydental/supply?week_start=' + fields.Date.to_string(self.start.date())).text)
        self.assertEqual(self.action('acquire', {}).status_code, 403)
        response = self.url_open('/web/dataset/call_kw', data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': 'ydental.supply.service', 'method': '_capacity_action', 'args': [], 'kwargs': {}}}), headers={'Content-Type': 'application/json'})
        self.assertIn('error', response.json())
        self.assertEqual(self.url_open('/ydental/supply/today').status_code, 200)

    def test_http_readonly_cross_store_stale_page_and_forged_orm(self):
        record = slot(self)
        self.authenticate('s03_reader', 's03-test-password')
        self.select()
        page = self.url_open('/ydental/supply')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Read only', page.text)
        self.assertNotIn('name="operation" value="resize"', page.text)
        self.assertEqual(self.action('resize', {'id': record.id, 'version': record.ydental_version, 'total': 100, 'reason': 'Denied'}).status_code, 403)
        self.authenticate('s03_writer', 's03-test-password')
        self.select()
        stale = self.revision
        self.select(self.stores[1])
        self.assertEqual(self.action('resize', {'id': record.id, 'version': record.ydental_version, 'total': 100, 'reason': 'Cross-store'}).status_code, 403)
        self.assertEqual(self.action('resize', {'id': record.id, 'version': record.ydental_version, 'total': 100, 'reason': 'Old page'}, revision=stale).status_code, 409)
        self.select()
        response = self.url_open('/web/dataset/call_kw', data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': 'ydental.supply.slot', 'method': 'write', 'args': [[record.id], {'ydental_total': 999}],
                       'kwargs': {'context': {'ydental_revision': self.revision, 'ydental_supply_mutation': True}}}}), headers={'Content-Type': 'application/json'})
        self.assertIn('error', response.json())
        record.invalidate_recordset()
        self.assertEqual(record.ydental_total, 6)

    def test_http_staff_today_feedback_and_csrf(self):
        now = fields.Datetime.now()
        result = self.service._operate('assign', {'user_id': self.staff.id, 'area_id': self.area.id,
            'start': fields.Datetime.to_string(now - timedelta(minutes=1)), 'end': fields.Datetime.to_string(now + timedelta(minutes=30))}, 'today')
        self.authenticate('s03_staff', 's03-test-password')
        self.select()
        page = self.url_open('/ydental/supply/today')
        self.assertEqual(page.status_code, 200)
        self.assertIn('S03 Area', page.text)
        self.assertEqual(self.action('feedback', {'id': result['id'], 'reason': 'Synthetic wrong arrangement'}).status_code, 200)
        response = self.action('suggest', {'id': result['id']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['execution'], 'not_connected')
        denied = self.url_open('/ydental/supply/action', data={'operation': 'feedback', 'revision': str(self.revision), 'key': 'no-csrf', 'payload': '{}'})
        self.assertEqual(denied.status_code, 400)
        self.assertEqual(self.url_open('/ydental/supply').status_code, 403)

    def test_http_policy_and_business_no_capacity_side_effect(self):
        record = slot(self)
        self.authenticate('s03_writer', 's03-test-password')
        self.select()
        result = self.action('policy', {'name': 'HTTP explicit demo', 'mode': 'demo', 'rounding': 'floor', 'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'Synthetic HTTP'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['preview'][3]['reservation'], 2)
        self.assertEqual(self.action('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'HTTP explicit open'}).status_code, 200)
        self.assertEqual(record.ydental_total, 6)
