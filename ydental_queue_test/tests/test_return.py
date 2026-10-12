from datetime import timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import setup, accepted, enter, key, lease_args, qualify, queue_bind
from .return_common import appender, close, external, report, reserve, serving, source
from ..models.adapter import DocumentSource


@tagged('post_install', '-at_install')
class TestQueueReturn(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def test_execution_history_reuse_patient_lease_and_no_repeat_entry(self):
        queue, lease, execution = serving(self)
        source(queue, execution)
        handover = queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        task = self.root['ydental.intake.task'].browse(handover['continuation_task_id'])
        report(self, task)
        call = queue._operate('call', lease_args(lease))
        new = queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertNotEqual(new['execution_id'], execution.id)
        self.assertEqual(execution.state, 'handover')
        self.assertEqual(queue._model('execution').search_count([('ydental_patient_id', '=', execution.ydental_patient_id.id)]), 2)
        with self.assertRaises(UserError):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        with self.assertRaises(AccessError):
            execution.unlink()

    def test_hold_external_report_query_has_no_business_side_effect(self):
        queue, lease, execution = serving(self)
        hold, task = reserve(self, queue, lease, execution)
        report(self, task)
        before = {m: self.root[m].search_count([]) for m in ('ydental.queue.entry', 'ydental.intake.task', 'ydental.supply.event', 'ydental.access.audit')}
        hint = self.front.env['ydental.queue.service']._operate('query_return', {'patient_id': execution.ydental_patient_id.id})
        self.assertEqual(hint['state'], 'holding')
        self.assertEqual(before, {m: self.root[m].search_count([]) for m in before})
        self.assertFalse(queue._unresolved_execution(execution.ydental_patient_id.id))
        self.assertEqual(hold.state, 'active')
        self.assertEqual(queue._operate('reserve', dict(lease_args(lease), execution_id=execution.id, target_task_id=task.id))['hold_id'], hold.id)
        for op in ('call', 'exit'):
            with self.assertRaises(UserError):
                queue._operate(op, lease_args(lease))
        with self.assertRaises(UserError):
            queue._operate('switch', dict(lease_args(lease), station_id=self.other_station.id))

    def test_reserve_requires_frozen_source_not_json_or_context(self):
        queue, lease, execution = serving(self)
        task = external(self, execution)
        with self.assertRaises(AccessError):
            queue.with_context(ydental_external_order=True)._operate('reserve', dict(lease_args(lease), execution_id=execution.id, target_task_id=task.id))
        self.assertEqual(execution.state, 'serving')
        self.assertFalse(queue._hold(patient_id=execution.ydental_patient_id.id))

    def test_restore_calling_clears_other_holder_without_capacity_or_new_number(self):
        queue, lease, execution = serving(self)
        hold, task = reserve(self, queue, lease, execution)
        report(self, task)
        other, other_lease = enter(self, queue_bind(self, self.second), self.stations[0][2])
        call = other._operate('call', lease_args(other_lease))
        before = queue._model('entry').search_count([]), self.root['ydental.supply.event'].search_count([])
        close(self)
        result = queue._operate('restore', dict(lease_args(lease), hold_id=hold.id, confirmed=True))
        self.assertEqual(result['state'], 'serving')
        self.assertEqual(hold.state, 'restored')
        self.assertEqual(queue._model('entry').browse(call['entry_id']).state, 'void')
        self.assertFalse(other._busy(other._model('lease').browse(other_lease['lease_id'])))
        self.assertEqual(task.state, 'pending')
        self.assertEqual(before, (queue._model('entry').search_count([]), self.root['ydental.supply.event'].search_count([])))
        self.assertEqual(queue._operate('restore', dict(lease_args(lease), hold_id=hold.id, confirmed=True))['execution_id'], result['execution_id'])

    def test_restore_refuses_external_serving_and_verify(self):
        queue, lease, execution = serving(self)
        hold, task = reserve(self, queue, lease, execution)
        report(self, task)
        other, other_lease, actual = serving(self, self.second, self.stations[0][2], task)
        for state in ('serving', 'verify'):
            actual._save({'state': state})
            with self.assertRaises(UserError):
                queue._operate('restore', dict(lease_args(lease), hold_id=hold.id, confirmed=True))
            self.assertEqual(hold.state, 'active')
        self.assertEqual(queue._unresolved_execution(task.ydental_patient_id.id), actual)

    def test_hold_timeout_keeps_reservation_and_actor_station_fences(self):
        queue, lease, execution = serving(self)
        hold, task = reserve(self, queue, lease, execution)
        queue._model('lease').browse(lease['lease_id'])._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()
        self.assertEqual(hold.state, 'verify')
        self.assertEqual(queue._status()['state'], 'verify')
        self.assertEqual(queue.env['ydental.access.service']._get_execution_store_id(), self.stores[0].id)
        self.assertEqual(self.front.env['ydental.queue.service']._operate('query_return', {'patient_id': task.ydental_patient_id.id})['state'], 'verify')
        with self.assertRaises(UserError):
            queue._operate('enter', {'station_id': self.other_station.id})
        with self.assertRaises(UserError):
            queue_bind(self, self.second)._operate('enter', {'station_id': self.stations[0][0].id})
        with self.assertRaises(AccessError):
            queue._operate('restore', dict(lease_args(lease), hold_id=hold.id, confirmed=True))

    def test_handover_fail_closed_then_save_failure_and_atomic_retry(self):
        queue, lease, execution = serving(self)
        doc = DocumentSource(key(), lease['lease_id'], lease['token'])
        queue._document_lock(doc, 'acquire')
        before = self.root['ydental.intake.task'].search_count([])
        with self.assertRaises(AccessError):
            queue.with_context(saved=True)._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        source(queue, execution, save_ok=False, document_key=doc.key)
        with self.assertRaises(UserError):
            queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        self.assertEqual(execution.state, 'serving')
        self.assertTrue(self.root['ydental.queue.test.document'].search([('ydental_key', '=', doc.key)]).ydental_active)
        self.assertEqual(before, self.root['ydental.intake.task'].search_count([]))
        source(queue, execution, document_key=doc.key)
        first = queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        again = queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        self.assertEqual(first['continuation_task_id'], again['continuation_task_id'])
        self.assertFalse(self.root['ydental.queue.test.document'].search([('ydental_key', '=', doc.key)]).ydental_active)
        self.assertTrue(queue._model('lease').browse(lease['lease_id']).ydental_active)
        self.assertFalse(queue._busy(queue._model('lease').browse(lease['lease_id'])))
        self.assertEqual(accepted(self).state, 'accepted')
        self.assertEqual(queue._operate('call', lease_args(lease))['state'], 'calling')

    def test_continuation_another_chair_preserves_only_outpatient_requirements(self):
        queue, lease, execution = serving(self)
        hold, external_task = reserve(self, queue, lease, execution)
        result = queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        task = self.root['ydental.intake.task'].browse(result['continuation_task_id'])
        self.assertEqual(task.ydental_mapping_id, self.mappings[0][0])
        self.assertEqual(task.ydental_continuation_snapshot['capability_id'], self.capabilities[0].id)
        self.assertFalse(task.ydental_entitlement_id)
        self.assertEqual(hold.state, 'handover')
        report(self, task)
        other, other_lease = enter(self, queue_bind(self, self.second), self.other_station)
        self.assertEqual(other._operate('call', lease_args(other_lease))['task_id'], task.id)
        self.assertEqual(external_task.state, 'pending')

    def test_handover_rejects_independent_catalog_and_rolls_back_save(self):
        queue, lease, execution = serving(self)
        fact = source(queue, execution)
        with self.assertRaises(UserError):
            queue._operate('handover', dict(lease_args(lease), execution_id=execution.id, mapping_id=self.mappings[0][1].id, reason='new independent service'))
        self.assertEqual(execution.state, 'serving')
        self.assertEqual(self.root['ydental.queue.test.return.source'].browse(fact).ydental_saved, 0)

    def test_append_authorization_two_factors_and_no_capacity(self):
        q = qualify(self)
        task = self.root['ydental.intake.task'].browse(q['task_id'])
        close(self)
        payload = {'task_id': task.id, 'reason': 'explicit task append'}
        with self.assertRaises(AccessError):
            self.front.env['ydental.queue.service']._operate('append', payload)
        app = appender(self)
        self.users['reader'].write({'group_ids': [(4, self.root.ref('ydental_queue.ydental_group_append').id)]})
        with self.assertRaises(AccessError):
            self.reader.env['ydental.queue.service']._operate('append', payload)
        before = self.root['ydental.supply.event'].search_count([])
        result = app._operate('append', payload)
        self.assertEqual(app._operate('append', payload)['permit_id'], result['permit_id'])
        self.assertEqual(before, self.root['ydental.supply.event'].search_count([]))
        self.users['frontdesk'].write({'group_ids': [(3, self.root.ref('ydental_queue.ydental_group_append').id)]})
        with self.assertRaises(AccessError):
            app._operate('append', payload)

    def test_closed_permit_missed_fault_report_do_not_refresh_priority(self):
        task = accepted(self)
        close(self)
        app = appender(self)
        permit = app._operate('append', {'task_id': task.id, 'reason': 'stopped-area explicit append'})
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        queue._operate('missed', dict(lease_args(lease), entry_id=call['entry_id']))
        entry = queue._model('entry').browse(call['entry_id'])
        rank = entry.ydental_order
        report(self, task)
        self.assertEqual(task.ydental_missed_count, 1)
        self.assertEqual(entry.ydental_order, rank)
        self.assertEqual(app._operate('append', {'task_id': task.id, 'reason': 'retry'})['permit_id'], permit['permit_id'])
        queue._operate('call', lease_args(lease))
        queue._model('lease').browse(lease['lease_id'])._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()
        self.assertEqual(entry.state, 'waiting')
        self.assertEqual(task.ydental_missed_count, 1)
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        with self.assertRaises(UserError):
            app._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'too late'})

    def test_revoke_before_start_withdraws_only_queue_not_qualification(self):
        task = accepted(self)
        close(self)
        app = appender(self)
        permit = app._operate('append', {'task_id': task.id, 'reason': 'explicit append'})
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        before = self.root['ydental.supply.event'].search_count([])
        app._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'explicit revoke'})
        with self.assertRaises(UserError):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(task.ydental_entitlement_id.state, 'held')
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')
        self.assertEqual(before, self.root['ydental.supply.event'].search_count([]))
        self.assertEqual(queue._model('entry').browse(call['entry_id']).state, 'void')

    def test_permit_does_not_transfer_task_or_day_and_hold_blocks_append(self):
        task = accepted(self)
        another = accepted(self)
        close(self)
        app = appender(self)
        p = app._operate('append', {'task_id': task.id, 'reason': 'explicit append'})
        queue, lease = enter(self)
        self.assertEqual(queue._operate('call', lease_args(lease))['task_id'], task.id)
        self.assertFalse(queue._permit_valid(another))
        permit = queue._model('append.permit').browse(p['permit_id'])
        permit._save({'ydental_business_date': permit.ydental_business_date - timedelta(days=1)})
        with self.assertRaises(AccessError):
            queue._operate('start', dict(lease_args(lease), entry_id=queue._model('entry').search([('ydental_task_id', '=', task.id)]).id))

    def test_pharmacy_uniform_queue_and_number_void_retains_capacity(self):
        # This is a task/queue contract only, with no stock, prescription or dispensing.
        from odoo import fields
        catalog = self.catalogs[2]
        catalog._save({'ydental_kind': 'medicine'})
        self.stations[0][2].write({'ydental_kind': 'pharmacy', 'ydental_version': self.stations[0][2].ydental_version})
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'pharmacy': 'write'})
        task = accepted(self, mapping=self.mappings[0][2])
        queue, lease = enter(self, station=self.stations[0][2])
        call = queue._operate('call', lease_args(lease))
        self.front._operate('void', {'task_id': task.id, 'version': task.ydental_version, 'reason': 'number only'}, key())
        self.assertEqual(task.ydental_entitlement_id.ydental_claim_id.state, 'held')
        report(self, task)
        call = queue._operate('call', lease_args(lease))
        self.assertEqual(queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))['state'], 'serving')

    def test_continuation_qualification_is_inherited_and_rechecked(self):
        from ..models.adapter import QualificationSource
        task = accepted(self)
        task.ydental_mapping_id.ydental_catalog_id._save({'ydental_qualification': 'synthetic outpatient license'})
        queue = queue_bind(self)
        queue._test_qualification(QualificationSource(self.users['doctor'].id, task.id, self.stations[0][0].id, 'synthetic outpatient license', True))
        queue, lease, execution = serving(self, task=task)
        source(queue, execution)
        result = queue._operate('handover', dict(lease_args(lease), execution_id=execution.id))
        continuation = self.root['ydental.intake.task'].browse(result['continuation_task_id'])
        self.assertEqual(continuation.ydental_continuation_snapshot['qualification'], 'synthetic outpatient license')
        report(self, continuation)
        other, held = enter(self, queue_bind(self, self.second), self.other_station)
        with self.assertRaises(UserError):
            other._operate('call', lease_args(held))
        other._test_qualification(QualificationSource(self.second.id, continuation.id, self.other_station.id, 'synthetic outpatient license', True))
        called = other._operate('call', lease_args(held))
        other._test_qualification(QualificationSource(self.second.id, continuation.id, self.other_station.id, 'synthetic outpatient license', False))
        with self.assertRaises(AccessError):
            other._operate('start', dict(lease_args(held), entry_id=called['entry_id']))

    def test_hold_wrong_patient_target_and_restore_service_drift_refused(self):
        queue, lease, execution = serving(self)
        wrong = self.root['ydental.intake.task'].browse(qualify(self, mapping=self.mappings[0][2])['task_id'])
        source(queue, execution, wrong)
        with self.assertRaises(AccessError):
            queue._operate('reserve', dict(lease_args(lease), execution_id=execution.id, target_task_id=wrong.id))
        self.assertEqual(execution.state, 'serving')
        hold, task = reserve(self, queue, lease, execution)
        execution.ydental_task_id.ydental_mapping_id.ydental_catalog_id._save({'ydental_qualification': 'changed after original execution'})
        with self.assertRaises(UserError):
            queue._operate('restore', dict(lease_args(lease), hold_id=hold.id, confirmed=True))
        self.assertEqual(hold.state, 'active')

    def test_ordinary_closed_report_requires_permit_and_open_append_refused(self):
        task = accepted(self)
        app = appender(self)
        with self.assertRaises(UserError):
            app._operate('append', {'task_id': task.id, 'reason': 'area still open'})
        close(self)
        with self.assertRaises(UserError):
            report(self, task)
        queue, lease = enter(self)
        with self.assertRaises(UserError):
            queue._operate('call', lease_args(lease))
