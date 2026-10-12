import json
import re
from datetime import timedelta

from odoo.tests import HttpCase, tagged

from .common import setup, qualify, accepted, key


@tagged('post_install', '-at_install')
class TestQueueHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def select(self, role='doctor'):
        self.authenticate(self.users[role].login, 's06a-test-password')
        page = self.url_open('/ydental/access')
        self.csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        result = self.url_open('/ydental/access/action', data={'csrf_token': self.csrf, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(result.status_code, 200, result.text)
        self.revision = result.json()['revision']
        self.connection = key() + key()

    def action(self, operation, args, connection=None, revision=None):
        return self.url_open('/ydental/queue/action', data={'csrf_token': self.csrf,
            'revision': self.revision if revision is None else revision, 'connection': connection or self.connection,
            'operation': operation, 'payload': json.dumps(args)})

    def rpc(self, model, method, args, context=None):
        return self.url_open('/web/dataset/call_kw/' + model + '/' + method, data=json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': 'call', 'params': {'model': model, 'method': method, 'args': args,
                'kwargs': {'context': dict(context or {}, ydental_revision=self.revision)}}}), headers={'Content-Type': 'application/json'}).json()

    def lease(self):
        response = self.action('enter', {'station_id': self.stations[0][0].id})
        self.assertEqual(response.status_code, 200, response.text)
        lease = response.json()
        return {'lease_id': lease['lease_id'], 'token': lease['token']}

    def test_http_unscheduled_call_missed_report_start(self):
        task = accepted(self)
        self.select()
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200, page.text)
        args = self.lease()
        self.assertIn('No assignment required', self.url_open('/ydental/queue').text)
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        args['entry_id'] = call.json()['entry_id']
        self.assertEqual(self.action('missed', args).status_code, 200)
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        self.assertEqual(task.ydental_missed_count, 1)
        del args['entry_id']
        self.assertEqual(self.action('call', args).status_code, 200)
        args['entry_id'] = call.json()['entry_id']
        self.assertEqual(self.action('start', args).json()['state'], 'serving')
        self.assertEqual(self.action('exit', {k: args[k] for k in ('lease_id', 'token')}).status_code, 409)

    def test_http_readonly_csrf_state_and_secret_field_bypass(self):
        task = accepted(self)
        self.select('reader')
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200)
        self.assertNotIn('data-operation="enter"', page.text)
        self.assertEqual(self.action('enter', {'station_id': self.stations[0][0].id}).status_code, 403)
        self.assertIn('error', self.rpc('ydental.queue.entry', 'write', [[1], {'state': 'serving'}], {'ydental_queue_mutation': True}))
        self.assertIn('error', self.rpc('ydental.queue.service', '_operate', ['enter', {'station_id': self.stations[0][0].id}]))
        self.assertEqual(self.url_open('/ydental/queue/action', data={'operation': 'enter', 'revision': self.revision,
            'connection': self.connection, 'payload': '{}'}).status_code, 400)

    def test_http_other_connection_old_token_and_timeout(self):
        accepted(self)
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        self.assertEqual(self.action('heartbeat', args, connection=key() + key()).status_code, 403)
        self.assertEqual(self.action('heartbeat', dict(args, token='old-token')).status_code, 403)
        lease = self.root['ydental.queue.lease'].browse(args['lease_id'])
        lease._save({'ydental_expires_at': self.front._now() - timedelta(seconds=1)})
        response = self.action('heartbeat', args)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()['result'], 'connection_expired')
        self.assertEqual(self.root['ydental.queue.entry'].browse(call['entry_id']).state, 'waiting')
        self.assertEqual(self.action('heartbeat', args).status_code, 403)
        self.assertIn('error', self.rpc('ydental.queue.lease', 'read', [[lease.id], ['ydental_token_hash']]))

    def test_http_switch_and_old_lease(self):
        self.select()
        args = self.lease()
        moved = self.action('switch', dict(args, station_id=self.other_station.id))
        self.assertEqual(moved.status_code, 200, moved.text)
        self.assertEqual(self.action('heartbeat', args).status_code, 403)
        movedargs = {k: moved.json()[k] for k in ('lease_id', 'token')}
        self.assertEqual(self.action('switch', dict(movedargs, station_id=self.stations[1][0].id)).status_code, 403)
        self.assertEqual(self.root['ydental.queue.lease'].browse(moved.json()['lease_id']).ydental_station_id, self.other_station)

    def test_http_revocation_next_write(self):
        self.select()
        args = self.lease()
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        self.assertEqual(self.action('heartbeat', args).status_code, 403)
        self.assertEqual(self.action('call', args).status_code, 403)

    def test_http_real_s05_hook_atomic_and_no_double_claim(self):
        q = qualify(self)
        claim = self.root['ydental.intake.entitlement'].browse(q['id']).ydental_claim_id
        self.select('frontdesk')
        def intake(operation, args):
            return self.url_open('/ydental/intake/action', data={'csrf_token': self.csrf, 'revision': self.revision,
                'key': key(), 'operation': operation, 'payload': json.dumps(args), 'output': 'json'})
        self.assertEqual(intake('arrive', {'patient_id': q['patient_id']}).status_code, 200)
        response = intake('report', {'task_id': q['task_id'], 'version': q['task_version']})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()['queue_status'], 'waiting')
        task = self.root['ydental.intake.task'].browse(q['task_id'])
        self.assertEqual(intake('report', {'task_id': task.id, 'version': task.ydental_version}).status_code, 200)
        self.assertEqual(self.root['ydental.queue.entry'].search_count([('ydental_task_id', '=', task.id)]), 1)
        self.assertEqual(self.root['ydental.supply.event'].search_count([('ydental_claim_id', '=', claim.id), ('ydental_operation', '=', 'acquire')]), 1)
        self.assertIn('No connected authorized workstation', self.url_open('/ydental/queue').text)
