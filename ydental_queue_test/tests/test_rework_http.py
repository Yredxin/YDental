import json
from datetime import timedelta

from .common import accepted, key
from .rework_common import mixed_fixture
from .test_http import TestQueueHTTP
from ..models.adapter import QualificationSource


class TestQueueReworkHTTP(TestQueueHTTP):
    def test_http_b1_verify_blocks_actor_new_station_and_cross_store_write(self):
        task = accepted(self)
        self.select()
        args = self.lease()
        call = self.action('call', args).json()
        self.assertEqual(self.action('start', dict(args, entry_id=call['entry_id'])).status_code, 200)
        self.root['ydental.queue.lease'].browse(args['lease_id'])._save({
            'ydental_expires_at': self.front._now() - timedelta(seconds=1)})
        self.assertTrue(self.action('heartbeat', args).json()['verification_required'])
        page = self.url_open('/ydental/queue')
        self.assertIn('data-state="verify"', page.text)
        self.assertIn(self.stations[0][0].name, page.text)
        self.assertNotIn('data-operation="enter"', page.text)
        self.assertIn('Resolve your existing execution', page.text)
        self.assertEqual(self.action('enter', {'station_id': self.other_station.id}).status_code, 409)
        self.assertEqual(self.action('heartbeat', args).status_code, 403)
        self.select()  # A real new authenticated session cannot shed execution.
        self.assertEqual(self.action('enter', {'station_id': self.other_station.id}).status_code, 409)
        self.admin._grant(self.users['doctor'].id, self.stores[1].id, {'frontdesk': 'write', 'medical': 'write'})
        switched = self.url_open('/ydental/access/action', data={'csrf_token': self.csrf, 'revision': self.revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switched.status_code, 200, switched.text)
        self.revision = switched.json()['revision']
        self.assertEqual(self.action('enter', {'station_id': self.stations[1][0].id}).status_code, 403)
        reserve = self.url_open('/ydental/intake/action', data={'csrf_token': self.csrf, 'revision': self.revision,
            'key': key(), 'operation': 'reserve', 'payload': json.dumps({'patient_id': task.ydental_patient_id.id,
                'mapping_id': self.mappings[1][0].id, 'start': str(self.start), 'end': str(self.end),
                'channel': 'reservation'}), 'output': 'json'})
        self.assertEqual(reserve.status_code, 403, reserve.text)
        page = self.url_open('/ydental/queue')
        self.assertIn('data-state="verify"', page.text)
        self.assertIn(self.stores[0].name, page.text)

    def test_http_b2_wrong_execution_area_cannot_call_or_start(self):
        mixed = mixed_fixture(self)
        task = accepted(self, mixed.mappings[2])
        self.select()
        entered = self.action('enter', {'station_id': mixed.wrong.id}).json()
        args = {k: entered[k] for k in ('lease_id', 'token')}
        self.assertEqual(self.action('call', args).status_code, 409)
        self.assertIn('execution_area_mismatch', self.url_open('/ydental/queue').text)
        self.assertEqual(self.action('exit', args).status_code, 200)
        entered = self.action('enter', {'station_id': mixed.stations[2].id}).json()
        args = {k: entered[k] for k in ('lease_id', 'token')}
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.assertEqual(call.json()['task_id'], task.id)
        mixed.mappings[2]._save({'ydental_execution_area_id': mixed.wrong_area.id})
        failed = self.action('start', dict(args, entry_id=call.json()['entry_id']))
        self.assertEqual(failed.status_code, 403, failed.text)
        self.assertIn('execution_area_mismatch', failed.text)
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')

    def test_http_b2_qualification_cannot_be_forged_and_is_rechecked(self):
        task = accepted(self)
        self.catalogs[0]._save({'ydental_qualification': 'S06A synthetic HTTP qualification'})
        self.select()
        args = self.lease()
        self.assertEqual(self.action('call', args).status_code, 409)
        self.assertIn('qualification_required', self.url_open('/ydental/queue').text)
        self.assertIn('error', self.rpc('ydental.queue.test.qualification', 'create', [{
            'ydental_actor_id': self.users['doctor'].id, 'ydental_task_id': task.id,
            'ydental_station_id': self.stations[0][0].id, 'ydental_requirement': self.catalogs[0].ydental_qualification,
            'ydental_satisfied': True}], {'ydental_queue_test_qualification': True}))
        source = QualificationSource(self.users['doctor'].id, task.id, self.stations[0][0].id,
                                     self.catalogs[0].ydental_qualification, True)
        self.root['ydental.queue.service']._test_qualification(source)
        call = self.action('call', args)
        self.assertEqual(call.status_code, 200, call.text)
        self.root['ydental.queue.service']._test_qualification(QualificationSource(
            source.actor_id, source.task_id, source.station_id, source.requirement, False))
        failed = self.action('start', dict(args, entry_id=call.json()['entry_id']))
        self.assertEqual(failed.status_code, 403, failed.text)
        self.assertIn('qualification_required', failed.text)
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')
        self.root['ydental.queue.service']._test_qualification(source)
        self.assertEqual(self.action('start', dict(args, entry_id=call.json()['entry_id'])).status_code, 200)

    def test_http_b3_n_zero_blocks_call_and_mixed_missed_moves_back(self):
        mixed = mixed_fixture(self)
        tasks = [accepted(self, mixed.mappings[i]) for i in (0, 1, 2, 2, 2)]
        self.select()
        entered = self.action('enter', {'station_id': mixed.stations[2].id}).json()
        args = {k: entered[k] for k in ('lease_id', 'token')}
        mixed.area.write({'ydental_version': mixed.area.ydental_version, 'ydental_missed_limit': 0})
        response = self.action('call', args)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn('configuration_required', response.text)
        self.assertIn('data-operation="call" disabled=', self.url_open('/ydental/queue').text)
        self.assertFalse(self.root['ydental.queue.entry'].search_count([('ydental_store_id', '=', self.stores[0].id), ('state', '=', 'calling')]))
        mixed.area.write({'ydental_version': mixed.area.ydental_version, 'ydental_missed_limit': 2})
        call = self.action('call', args).json()
        self.assertEqual(call['task_id'], tasks[2].id)
        response = self.action('missed', dict(args, entry_id=call['entry_id']))
        self.assertEqual(response.status_code, 200, response.text)
        ordered = self.root['ydental.queue.service']._ordered(mixed.area.id).ydental_task_id.ids
        self.assertEqual(ordered, [tasks[i].id for i in (0, 1, 3, 4, 2)])

    def test_http_b4_unrelated_request_timeout_records_automation(self):
        self.select()
        args = self.lease()
        old = self.root['ydental.queue.lease'].browse(args['lease_id'])
        old._save({'ydental_expires_at': self.front._now() - timedelta(seconds=1)})
        self.select('manager')
        response = self.action('enter', {'station_id': self.other_station.id})
        self.assertEqual(response.status_code, 200, response.text)
        audit = self.root['ydental.access.audit'].search([('ydental_event', '=', 'queue.connection_timeout'),
            ('ydental_target_id', '=', old.id)], limit=1)
        self.assertEqual(audit.ydental_user_id, self.root.ref('base.user_root'))
        self.assertNotEqual(audit.ydental_user_id, self.users['manager'])
        self.assertEqual(audit.ydental_after['holder_user_id'], self.users['doctor'].id)
        self.assertEqual(audit.ydental_source, 'workstation_timeout_automation')
