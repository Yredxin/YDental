from datetime import timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import accepted, bind, enter, key, lease_args, qualify, queue_bind, setup
from .rework_common import mixed_fixture
from ..models.adapter import Clock, QualificationSource
from odoo.addons.ydental_queue.models.ydental_queue_service import YDentalQueueService


@tagged('post_install', '-at_install')
class TestQueueRework(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def entry(self, task):
        return self.root['ydental.queue.entry'].search([('ydental_task_id', '=', task.id)])

    def serving(self):
        task = accepted(self)
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        return task, queue, lease

    def test_b1_verify_retains_actor_station_patient_and_status(self):
        task, queue, lease = self.serving()
        expired = queue.with_context(ydental_queue_test_clock=Clock(queue._now() + timedelta(seconds=30)))
        result = expired._operate('heartbeat', lease_args(lease))
        self.assertTrue(result['verification_required'])
        self.assertFalse(queue._own())
        self.assertEqual(queue._actor_execution().state, 'verify')
        self.assertEqual(queue._status()['state'], 'verify')
        self.assertEqual(queue.with_context(lang='zh_CN')._status()['state_label'], '待现场核实')
        self.assertEqual(queue._status()['station'], self.stations[0][0].name)
        with self.assertRaisesRegex(UserError, 'handover_required'):
            queue_bind(self)._operate('enter', {'station_id': self.other_station.id})
        with self.assertRaises(AccessError):
            queue._operate('heartbeat', lease_args(lease))
        with self.assertRaises(UserError):
            queue_bind(self, self.second)._operate('enter', {'station_id': self.stations[0][0].id})
        other, other_lease = enter(self, queue_bind(self, self.second), self.other_station)
        with self.assertRaises(UserError):
            other._operate('call', lease_args(other_lease))
        another = accepted(self)
        call = other._operate('call', lease_args(other_lease))
        self.assertEqual(call['task_id'], another.id)
        other._operate('start', dict(lease_args(other_lease), entry_id=call['entry_id']))
        self.assertEqual(self.entry(task).state, 'verify')
        self.assertEqual(self.root['ydental.queue.execution'].search_count([('ydental_store_id', 'in', self.stores.ids)]), 2)

    def test_b1_execution_store_fence_survives_new_session_and_store_switch(self):
        task, queue, lease = self.serving()
        queue.with_context(ydental_queue_test_clock=Clock(queue._now() + timedelta(seconds=30)))._timeout()
        self.admin._grant(self.users['doctor'].id, self.stores[1].id, {'medical': 'write', 'frontdesk': 'write'})
        elsewhere = bind(self, self.users['doctor'], self.stores[1])
        access = elsewhere.env['ydental.access.service']
        self.assertEqual(access._get_execution_store_id(), self.stores[0].id)
        with self.assertRaisesRegex(AccessError, 'another store'):
            access._check('medical', 'write', write=True)
        with self.assertRaises(AccessError):
            qualify(self, mapping=self.mappings[1][0], service=elsewhere)
        status = elsewhere.env['ydental.queue.service']._status()
        self.assertEqual((status['store'], status['station'], status['state']),
                         (self.stores[0].name, self.stations[0][0].name, 'verify'))

    def test_b2_execution_area_same_reporting_same_capability_rechecked_at_start(self):
        mixed = mixed_fixture(self)
        task = accepted(self, mixed.mappings[2])
        wrong, wrong_lease = enter(self, station=mixed.wrong)
        self.assertIn('execution_area_mismatch', wrong._eligibility(self.entry(task), mixed.wrong))
        with self.assertRaises(UserError):
            wrong._operate('call', lease_args(wrong_lease))
        wrong._operate('exit', lease_args(wrong_lease))
        queue, lease = enter(self, station=mixed.stations[2])
        call = queue._operate('call', lease_args(lease))
        self.assertEqual(call['task_id'], task.id)
        mixed.mappings[2]._save({'ydental_execution_area_id': mixed.wrong_area.id})
        with self.assertRaisesRegex(AccessError, 'execution_area_mismatch'):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')
        mixed.mappings[2]._save({'ydental_execution_area_id': mixed.execution_areas[2].id})
        self.assertEqual(queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))['state'], 'serving')

    def test_b2_qualification_default_closed_trusted_provider_and_revalidation(self):
        task = accepted(self)
        self.catalogs[0]._save({'ydental_qualification': 'S06A synthetic special qualification'})
        queue, lease = enter(self)
        self.assertFalse(YDentalQueueService._qualification_satisfied(queue, task, self.stations[0][0], self.users['doctor']))
        with self.assertRaises(UserError):
            queue.with_context(ydental_qualification=True, ydental_queue_test_qualification={'satisfied': True})._operate('call', lease_args(lease))
        with self.assertRaises(AccessError):
            queue._test_qualification({'satisfied': True})
        source = QualificationSource(self.users['doctor'].id, task.id, self.stations[0][0].id,
                                     self.catalogs[0].ydental_qualification, True)
        queue._test_qualification(source)
        call = queue._operate('call', lease_args(lease))
        queue._test_qualification(QualificationSource(source.actor_id, source.task_id, source.station_id, source.requirement, False))
        with self.assertRaisesRegex(AccessError, 'qualification_required'):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(self.entry(task).state, 'calling')
        queue._test_qualification(source)
        queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))

    def test_b2_catalog_capability_change_cannot_start_old_entry(self):
        task = accepted(self)
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        self.catalogs[0]._save({'ydental_capability_id': self.capabilities[1].id})
        with self.assertRaisesRegex(AccessError, 'capability_mismatch'):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')

    def test_b3_mixed_capability_rank_three_moves_two_not_to_head(self):
        mixed = mixed_fixture(self)
        tasks = [accepted(self, mixed.mappings[i]) for i in (0, 1, 2, 2, 2)]
        queue, lease = enter(self, station=mixed.stations[2])
        before = queue._ordered(mixed.area.id).ids
        call = queue._operate('call', lease_args(lease))
        entry = self.entry(tasks[2])
        self.assertEqual((call['task_id'], entry.ydental_call_rank), (tasks[2].id, 3))
        queue._operate('missed', dict(lease_args(lease), entry_id=entry.id))
        self.assertEqual(queue._ordered(mixed.area.id).ids, [before[i] for i in (0, 1, 3, 4, 2)])
        self.assertEqual(tasks[2].ydental_missed_count, 1)

    def test_b3_mixed_rank_four_short_tail_and_repeat_report(self):
        mixed = mixed_fixture(self)
        tasks = [accepted(self, mixed.mappings[i]) for i in (0, 1, 0, 2, 2)]
        queue, lease = enter(self, station=mixed.stations[2])
        before = queue._ordered(mixed.area.id).ids
        call = queue._operate('call', lease_args(lease))
        self.assertEqual(self.entry(tasks[3]).ydental_call_rank, 4)
        queue._operate('missed', dict(lease_args(lease), entry_id=call['entry_id']))
        self.front._operate('report', {'task_id': tasks[3].id, 'version': tasks[3].ydental_version}, key())
        self.assertEqual(queue._ordered(mixed.area.id).ids, [before[i] for i in (0, 1, 2, 4, 3)])
        self.assertEqual(tasks[3].ydental_missed_count, 1)

    def test_b3_return_missed_loses_opportunity_moves_from_priority_rank(self):
        tasks = [accepted(self) for _ in range(3)]
        returned = self.entry(tasks[2])
        returned._save({'ydental_return': True})
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        self.assertEqual(returned.ydental_call_rank, 1)
        queue._operate('missed', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(queue._ordered(returned.ydental_area_id.id).ydental_task_id.ids, [t.id for t in tasks])
        self.assertTrue(returned.ydental_opportunity_used)

    def test_b3_fault_restores_mixed_call_rank_order_and_opportunity(self):
        mixed = mixed_fixture(self)
        tasks = [accepted(self, mixed.mappings[i]) for i in (0, 1, 2, 2)]
        queue, lease = enter(self, station=mixed.stations[2])
        before = queue._ordered(mixed.area.id).ids
        original = self.entry(tasks[2]).ydental_order
        queue._operate('call', lease_args(lease))
        queue.with_context(ydental_queue_test_clock=Clock(queue._now() + timedelta(seconds=30)))._timeout()
        self.assertEqual(queue._ordered(mixed.area.id).ids, before)
        self.assertEqual(self.entry(tasks[2]).ydental_order, original)
        self.assertFalse(self.entry(tasks[2]).ydental_opportunity_used)
        self.assertEqual(tasks[2].ydental_missed_count, 0)

    def test_b3_n_unpublished_blocks_call_before_state_change(self):
        task = accepted(self)
        queue, lease = enter(self)
        self.areas[0][0].write({'ydental_version': self.areas[0][0].ydental_version, 'ydental_missed_limit': 0})
        with self.assertRaisesRegex(UserError, 'configuration_required'):
            queue._operate('call', lease_args(lease))
        entry = self.entry(task)
        self.assertEqual(entry.state, 'waiting')
        self.assertFalse(entry.ydental_lease_id)
        self.assertFalse(queue._busy(queue._own()))

    def test_b4_request_and_cron_use_identical_automation_audit_semantics(self):
        queue, lease = enter(self)
        old = queue._model('lease').browse(lease['lease_id'])
        old._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        other, second_lease = enter(self, queue_bind(self, self.second), self.other_station)
        audit = self.root['ydental.access.audit'].search([('ydental_event', '=', 'queue.connection_timeout'),
            ('ydental_target_id', '=', old.id)], limit=1)
        self.assertEqual(audit.ydental_user_id, self.root.ref('base.user_root'))
        self.assertNotEqual(audit.ydental_user_id, self.second)
        self.assertEqual(audit.ydental_source, 'workstation_timeout_automation')
        self.assertEqual(audit.ydental_after['holder_user_id'], self.users['doctor'].id)
        self.assertEqual(audit.ydental_after['station_id'], self.stations[0][0].id)
        clock = Clock(other._now() + timedelta(seconds=30))
        self.root['ydental.queue.service'].with_context(ydental_queue_test_clock=clock)._timeout()
        cron_audit = self.root['ydental.access.audit'].search([('ydental_event', '=', 'queue.connection_timeout'),
            ('ydental_target_id', '=', second_lease['lease_id'])], limit=1)
        self.assertEqual(cron_audit.ydental_user_id, audit.ydental_user_id)
        self.assertEqual(cron_audit.ydental_source, audit.ydental_source)
        self.assertEqual(cron_audit.ydental_after['holder_user_id'], self.second.id)
        self.assertEqual(set(cron_audit.ydental_after), set(audit.ydental_after))
