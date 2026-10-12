import json

from odoo.tests import tagged

from .common import accepted, key
from .return_common import appender, close, external, report, source
from .test_http import TestQueueHTTP


@tagged('post_install', '-at_install')
class TestQueueReturnHTTP(TestQueueHTTP):
    def start_http(self):
        task = accepted(self)
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        result = self.action('start', dict(args, entry_id=call['entry_id']))
        self.assertEqual(result.status_code, 200, result.text)
        return args, self.root['ydental.queue.execution'].browse(result.json()['execution_id'])

    def test_http_hold_query_and_confirmed_restore(self):
        args, execution = self.start_http()
        target = external(self, execution)
        queue = self.front.env['ydental.queue.service']
        source(queue, execution, target)
        held = self.action('reserve', dict(args, execution_id=execution.id, target_task_id=target.id))
        self.assertEqual(held.status_code, 200, held.text)
        self.assertIn('Reserved return', self.url_open('/ydental/queue').text)
        report(self, target)
        query = self.action('query_return', {'patient_id': target.ydental_patient_id.id})
        self.assertEqual(query.json()['result'], 'hint_only')
        self.assertEqual(self.action('call', args).status_code, 409)
        self.assertEqual(self.action('restore', dict(args, hold_id=held.json()['hold_id'], confirmed=False)).status_code, 403)
        restored = self.action('restore', dict(args, hold_id=held.json()['hold_id'], confirmed=True))
        self.assertEqual(restored.status_code, 200, restored.text)
        self.assertEqual(restored.json()['state'], 'serving')
        self.assertEqual(target.state, 'pending')

    def test_http_save_failure_retry_and_continuation(self):
        args, execution = self.start_http()
        payload = dict(args, execution_id=execution.id)
        self.assertEqual(self.action('handover', payload).status_code, 403)
        queue = self.front.env['ydental.queue.service']
        source(queue, execution, save_ok=False)
        self.assertEqual(self.action('handover', payload).status_code, 409)
        self.assertEqual(execution.state, 'serving')
        source(queue, execution)
        response = self.action('handover', payload)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(self.action('handover', payload).json()['continuation_task_id'], response.json()['continuation_task_id'])
        task = self.root['ydental.intake.task'].browse(response.json()['continuation_task_id'])
        self.assertEqual(task.state, 'pending')
        self.assertFalse(task.ydental_entitlement_id)
        self.assertEqual(self.action('heartbeat', args).status_code, 200)

    def test_http_explicit_append_closed_missed_and_revoke(self):
        task = accepted(self)
        close(self)
        self.select('frontdesk')
        payload = {'task_id': task.id, 'reason': 'HTTP explicit append'}
        self.assertEqual(self.action('append', payload).status_code, 403)
        appender(self)
        permit = self.action('append', payload)
        self.assertEqual(permit.status_code, 200, permit.text)
        self.assertEqual(self.action('append', payload).json()['permit_id'], permit.json()['permit_id'])
        self.select()
        args = self.lease()
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.assertEqual(self.action('missed', dict(args, entry_id=call.json()['entry_id'])).status_code, 200)
        self.select('frontdesk')
        self.assertEqual(self.action('revoke', {'permit_id': permit.json()['permit_id'], 'reason': 'HTTP revoke'}).status_code, 200)
        self.assertEqual(task.ydental_entitlement_id.state, 'held')

    def test_http_append_start_then_revoke_denied(self):
        task = accepted(self)
        close(self)
        appender(self)
        self.select('frontdesk')
        permit = self.action('append', {'task_id': task.id, 'reason': 'HTTP explicit append'}).json()
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        self.assertEqual(self.action('start', dict(args, entry_id=call['entry_id'])).status_code, 200)
        self.select('frontdesk')
        self.assertEqual(self.action('revoke', {'permit_id': permit['permit_id'], 'reason': 'too late'}).status_code, 409)
        self.assertEqual(task.state, 'started')

    def test_rpc_hold_permit_and_synthetic_source_bypass_denied(self):
        args, execution = self.start_http()
        for model, values in (
                ('ydental.queue.hold', {'ydental_execution_id': execution.id}),
                ('ydental.queue.append.permit', {'state': 'active'}),
                ('ydental.queue.execution', {'state': 'handover'}),
                ('ydental.intake.task', {'ydental_source_execution_id': execution.id}),
                ('ydental.queue.test.return.source', {'ydental_execution_id': execution.id, 'ydental_save_ok': True})):
            self.assertIn('error', self.rpc(model, 'create', [values], {'ydental_queue_mutation': True, 'ydental_return_test_source': True}))
        self.assertIn('error', self.rpc('ydental.queue.service', '_save_before_handover', [execution.id]))
        self.assertEqual(self.action('handover', dict(args, execution_id=execution.id, saved=True)).status_code, 409)

    def test_http_pharmacy_only_read_and_exact_task_start(self):
        catalog = self.catalogs[2]
        catalog._save({'ydental_kind': 'medicine'})
        self.stations[0][2].write({'ydental_kind': 'pharmacy', 'ydental_version': self.stations[0][2].ydental_version})
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'exam': 'none', 'pharmacy': 'write'})
        task = accepted(self, mapping=self.mappings[0][2])
        self.select()
        self.assertEqual(self.url_open('/ydental/queue').status_code, 200)
        lease = self.action('enter', {'station_id': self.stations[0][2].id})
        self.assertEqual(lease.status_code, 200, lease.text)
        args = {k: lease.json()[k] for k in ('lease_id', 'token')}
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.assertEqual(self.action('start', dict(args, entry_id=call.json()['entry_id'])).status_code, 200)
