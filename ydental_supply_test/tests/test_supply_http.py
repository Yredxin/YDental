import json
import re
import secrets
from datetime import datetime, timedelta

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

    def local_form(self, operation, values):
        return self.url_open('/ydental/supply/action', data={'csrf_token': self.token, 'key': secrets.token_hex(8),
            'revision': str(self.revision), 'operation': operation, 'output': 'json', **values})

    def test_http_rework_suggestions_filter_partial_coverage_and_direct_assignment(self):
        self.staff.write({'ydental_capability_ids': [fields.Command.set(self.capabilities[:1].ids)]})
        now = fields.Datetime.now()
        result = self.service._operate('assign', {'user_id': self.staff.id, 'area_id': self.area.id,
            'start': fields.Datetime.to_string(now), 'end': fields.Datetime.to_string(now + timedelta(hours=1))}, 'http-clean-area')
        self.authenticate(self.staff.login, 's03-test-password')
        self.select()
        response = self.action('suggest', {'id': result['id']})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['station_ids'], self.stations[:1].ids)
        assignment = self.root['ydental.supply.assignment'].browse(result['id'])
        self.service._operate('cancel_assignment', {'id': assignment.id, 'version': assignment.ydental_version,
            'reason': 'Check direct HTTP suggestion'}, 'http-cancel-area')
        result = self.service._operate('assign', {'user_id': self.staff.id, 'station_id': self.stations[1].id,
            'start': fields.Datetime.to_string(now), 'end': fields.Datetime.to_string(now + timedelta(hours=1))}, 'http-clean-direct')
        self.assertTrue(result['warning'])
        self.assertEqual(self.action('suggest', {'id': result['id']}).json()['station_ids'], [])
        self.staff.write({'ydental_capability_ids': [fields.Command.set(self.capabilities.ids)]})
        self.assertEqual(self.action('suggest', {'id': result['id']}).json()['station_ids'], self.stations[1:].ids)

    def test_http_rework_assignment_handling_visible_and_resolve_authorized(self):
        result = self.service._operate('assign', {'user_id': self.staff.id, 'station_id': self.stations[1].id,
            'start': fields.Datetime.to_string(self.start), 'end': fields.Datetime.to_string(self.end)}, 'http-before-absence')
        assignment = self.root['ydental.supply.assignment'].browse(result['id'])
        leave = self.root['resource.calendar.leaves'].create({'name': 'Synthetic HTTP absence',
            'resource_id': assignment.ydental_employee_id.resource_id.id, 'date_from': self.start, 'date_to': self.end})
        pending = self.root['ydental.supply.disposition'].search([('ydental_assignment_id', '=', assignment.id), ('ydental_slot_id', '=', False)])
        self.assertEqual(len(pending), 1)
        self.authenticate(self.reader.login, 's03-test-password')
        self.select()
        self.assertIn('Assignment conflict:', self.url_open('/ydental/supply').text)
        args = {'entity': 'disposition', 'id': pending.id, 'version': pending.ydental_version, 'reason': 'Reviewed HTTP handling'}
        self.assertEqual(self.action('resolve', args).status_code, 403)
        leave.write({'date_from': self.end + timedelta(hours=1), 'date_to': self.end + timedelta(hours=2)})
        self.assertEqual(pending.state, 'pending')
        self.authenticate(self.writer.login, 's03-test-password')
        self.select()
        self.assertEqual(self.action('resolve', args).status_code, 200)
        pending.invalidate_recordset()
        self.assertEqual(pending.state, 'resolved')
        self.assertIn('Reviewed HTTP handling', self.url_open('/ydental/supply').text)
        self.assertEqual(assignment.state, 'active')

    def test_http_rework_all_local_forms_reject_dst_gap_and_fold_atomically(self):
        self.stores[0].write({'ydental_timezone': 'America/New_York'})
        result = self.service._operate('assign', {'user_id': self.staff.id, 'station_id': self.stations[0].id,
            'start': '2026-11-02 14:00:00', 'end': '2026-11-02 15:00:00'}, 'http-existing-assignment')
        assignment = self.root['ydental.supply.assignment'].browse(result['id'])
        capacity = slot(self, start=datetime(2026, 11, 2, 14), end=datetime(2026, 11, 2, 15))
        self.authenticate(self.writer.login, 's03-test-password')
        self.select()
        before_assignments = self.root['ydental.supply.assignment'].search([('ydental_store_id', '=', self.stores[0].id)])
        before_slots = self.root['ydental.supply.slot'].search([('ydental_store_id', '=', self.stores[0].id)])
        for day, start, end, message in [('2026-03-08', '02:30', '03:30', 'does not exist'),
                                         ('2026-11-01', '01:30', '02:30', 'ambiguous')]:
            base = {'user_id': str(self.staff.id), 'station_id': str(self.stations[0].id),
                'start': day + 'T' + start, 'end': day + 'T' + end, 'reason': 'Synthetic invalid wall time'}
            cases = [
                ('assign', base),
                ('adjust', dict(base, id=str(assignment.id), version=str(assignment.ydental_version))),
                ('batch', {'user_id': str(self.staff.id), 'area_id': str(self.area.id),
                    'dates': ('2026-03-07,' if day.endswith('03-08') else '2026-10-31,') + day,
                    'start_time': start, 'end_time': end, 'reason': base['reason']}),
                ('slot', dict(base, total='6', capability_ids=[str(self.capabilities[0].id)])),
                ('extend', {'id': str(capacity.id), 'version': str(capacity.ydental_version), 'end': day + 'T' + start, 'reason': base['reason']}),
            ]
            for operation, values in cases:
                with self.subTest(day=day, operation=operation):
                    response = self.local_form(operation, values)
                    self.assertEqual(response.status_code, 409)
                    self.assertIn(message, response.json()['error'])
        self.assertEqual(self.root['ydental.supply.assignment'].search([('ydental_store_id', '=', self.stores[0].id)]), before_assignments)
        self.assertEqual(self.root['ydental.supply.slot'].search([('ydental_store_id', '=', self.stores[0].id)]), before_slots)
        assignment.invalidate_recordset()
        capacity.invalidate_recordset()
        self.assertEqual(assignment.ydental_start, datetime(2026, 11, 2, 14))
        self.assertEqual(capacity.ydental_end, datetime(2026, 11, 2, 15))

    def test_http_rework_normal_local_forms_store_exact_utc(self):
        self.stores[0].write({'ydental_timezone': 'America/New_York'})
        self.authenticate(self.writer.login, 's03-test-password')
        self.select()
        values = {'user_id': str(self.staff.id), 'station_id': str(self.stations[0].id),
            'start': '2026-11-02T09:15', 'end': '2026-11-02T10:15', 'reason': 'Synthetic local round trip'}
        response = self.local_form('assign', values)
        self.assertEqual(response.status_code, 200)
        assignment = self.root['ydental.supply.assignment'].browse(response.json()['id'])
        self.assertEqual(assignment.ydental_start, datetime(2026, 11, 2, 14, 15))
        values.update(id=str(assignment.id), version=str(assignment.ydental_version), start='2026-11-03T09:15', end='2026-11-03T10:15')
        self.assertEqual(self.local_form('adjust', values).status_code, 200)
        assignment.invalidate_recordset()
        self.assertEqual(assignment.ydental_start, datetime(2026, 11, 3, 14, 15))
        batch = self.local_form('batch', {'user_id': str(self.staff.id), 'area_id': str(self.area.id),
            'dates': '2026-11-04,2026-11-05', 'start_time': '09:15', 'end_time': '10:15', 'reason': 'Synthetic local batch'})
        self.assertEqual(batch.status_code, 200)
        records = self.root['ydental.supply.assignment'].browse(batch.json()['ids'])
        self.assertEqual(records.mapped('ydental_start'), [datetime(2026, 11, 4, 14, 15), datetime(2026, 11, 5, 14, 15)])
        response = self.local_form('slot', {'station_id': str(self.stations[1].id), 'start': '2026-11-06T09:15',
            'end': '2026-11-06T10:15', 'total': '6', 'capability_ids': [str(self.capabilities[0].id)], 'reason': 'Synthetic local capacity'})
        self.assertEqual(response.status_code, 200)
        capacity = self.root['ydental.supply.slot'].browse(response.json()['id'])
        self.assertEqual(capacity.ydental_start, datetime(2026, 11, 6, 14, 15))
        response = self.local_form('extend', {'id': str(capacity.id), 'version': str(capacity.ydental_version),
            'end': '2026-11-06T11:15', 'reason': 'Synthetic local extension'})
        self.assertEqual(response.status_code, 200)
        capacity.invalidate_recordset()
        self.assertEqual(capacity.ydental_end, datetime(2026, 11, 6, 16, 15))

    def test_http_week_today_forms_and_private_downstream(self):
        self.authenticate(self.writer.login, 's03-test-password')
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
        self.authenticate(self.reader.login, 's03-test-password')
        self.select()
        page = self.url_open('/ydental/supply')
        self.assertEqual(page.status_code, 200)
        self.assertIn('Read only', page.text)
        self.assertNotIn('name="operation" value="resize"', page.text)
        self.assertEqual(self.action('resize', {'id': record.id, 'version': record.ydental_version, 'total': 100, 'reason': 'Denied'}).status_code, 403)
        self.authenticate(self.writer.login, 's03-test-password')
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
        self.authenticate(self.staff.login, 's03-test-password')
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
        self.authenticate(self.writer.login, 's03-test-password')
        self.select()
        result = self.action('policy', {'name': 'HTTP explicit demo', 'mode': 'demo', 'rounding': 'floor', 'phone_pool': 'reservation', 'cutoff_minutes': 0, 'reason': 'Synthetic HTTP'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['preview'][3]['reservation'], 2)
        self.assertEqual(self.action('business', {'area_id': self.area.id, 'state': 'open', 'reason': 'HTTP explicit open'}).status_code, 200)
        self.assertEqual(record.ydental_total, 6)
