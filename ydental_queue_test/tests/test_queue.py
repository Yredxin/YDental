from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import setup, queue_bind, enter, lease_args, accepted, qualify, arrive_report, key, bind, patient, price
from ..models.adapter import DocumentSource


@tagged('post_install', '-at_install')
class TestQueue(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def test_t01_one_actor_one_station_no_admin_force(self):
        a, lease = enter(self)
        with self.assertRaises(UserError):
            queue_bind(self, self.second)._operate('enter', {'station_id': self.stations[0][0].id})
        with self.assertRaises(UserError):
            queue_bind(self)._operate('enter', {'station_id': self.other_station.id})
        with self.assertRaises(AccessError):
            queue_bind(self, self.users['manager'])._operate('force_release', {'lease_id': lease['lease_id']})
        with self.assertRaises(AccessError):
            self.root['ydental.queue.lease'].browse(lease['lease_id']).write({'ydental_active': False})
        self.assertEqual(self.root['ydental.queue.lease'].search_count([('ydental_active', '=', True)]), 1)

    def test_t02_real_report_call_start_capacity_once(self):
        task = accepted(self)
        claim = task.ydental_entitlement_id.ydental_claim_id
        a, lease = enter(self)
        call = a._operate('call', lease_args(lease))
        self.assertEqual(call['task_id'], task.id)
        result = a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(result['state'], 'serving')
        self.assertEqual((task.state, claim.state), ('started', 'consumed'))
        self.assertFalse(self.front._position(task.ydental_patient_id))
        self.assertTrue(self.root['ydental.queue.execution'].search_count([('ydental_patient_id', '=', task.ydental_patient_id.id)]))
        with self.assertRaises(UserError):
            a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(self.root['ydental.supply.event'].search_count([('ydental_claim_id', '=', claim.id), ('ydental_operation', '=', 'consume')]), 1)

    def test_t03_panorama_never_cbct(self):
        task = accepted(self, self.mappings[0][2])
        a, lease = enter(self, station=self.stations[0][3])
        with self.assertRaises(UserError):
            a._operate('call', lease_args(lease))
        self.assertEqual(task.ydental_mapping_id, self.mappings[0][2])
        self.assertEqual(self.root['ydental.queue.entry'].search([('ydental_task_id', '=', task.id)]).state, 'waiting')

    def test_t04_missed_repeated_report_switch_and_fault(self):
        tasks = [accepted(self) for _ in range(3)]
        entries = self.root['ydental.queue.entry'].search([('ydental_task_id', 'in', [t.id for t in tasks])])
        entries[2]._save({'ydental_return': True})  # Fixed test source classification for F1.
        a, lease = enter(self)
        call = a._operate('call', lease_args(lease))
        self.assertEqual(call['task_id'], tasks[2].id)
        a._operate('missed', dict(lease_args(lease), entry_id=call['entry_id']))
        self.front._operate('report', {'task_id': tasks[2].id, 'version': tasks[2].ydental_version}, key())
        self.assertEqual(tasks[2].ydental_missed_count, 1)
        self.assertEqual(a._operate('call', lease_args(lease))['task_id'], tasks[0].id)
        expired_at = a._now() + timedelta(seconds=30)
        with patch(type(a), '_now', return_value=expired_at):
            result = a._operate('heartbeat', lease_args(lease))
        self.assertEqual(result['result'], 'connection_expired')
        self.assertEqual(tasks[2].ydental_missed_count, 1)
        self.assertTrue(entries[2].ydental_opportunity_used)
        self.assertEqual(entries[0].state, 'waiting')

    def test_t04_return_from_real_started_history_not_once_per_day(self):
        # Historical execution identity only, no S08 completion API is implemented.
        historic = accepted(self)
        h = self.root['ydental.queue.entry'].search([('ydental_task_id', '=', historic.id)])
        h._save({'state': 'void', 'ydental_started_at': fields.Datetime.now()})
        p = self.front._position(historic.ydental_patient_id)
        p._save({'ydental_active': False})
        historic._save({'state': 'done'})
        for i in range(2):
            q = qualify(self, historic.ydental_patient_id)
            arrive_report(self, q)
            row = self.root['ydental.queue.entry'].search([('ydental_task_id', '=', q['task_id'])])
            self.assertTrue(row.ydental_return)
            self.front._operate('void', {'task_id': q['task_id'], 'version': row.ydental_task_id.ydental_version, 'reason': 'Synthetic return test'}, key())

    def test_t05_session_token_revision_context_and_idle(self):
        a, lease = enter(self)
        before = self.root['ydental.queue.lease'].browse(lease['lease_id']).ydental_expires_at
        a._operate('heartbeat', lease_args(lease))
        self.assertGreaterEqual(self.root['ydental.queue.lease'].browse(lease['lease_id']).ydental_expires_at, before)
        with self.assertRaises(AccessError):
            queue_bind(self)._operate('heartbeat', lease_args(lease))
        with self.assertRaises(AccessError):
            a.with_context(ydental_queue_connection={'actor_id': self.users['doctor'].id})._operate('heartbeat', lease_args(lease))
        with self.assertRaises(AccessError):
            a._operate('heartbeat', dict(lease_args(lease), token='old-token'))
        access = a.env['ydental.access.service']
        access._switch(self.stores[1].id)
        with self.assertRaises(UserError):
            a._operate('heartbeat', lease_args(lease))
        self.assertTrue(self.root['ydental.queue.lease'].browse(lease['lease_id']).ydental_active)

    def test_t05_serving_timeout_stays_exclusive(self):
        task = accepted(self)
        a, lease = enter(self)
        call = a._operate('call', lease_args(lease))
        a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        with patch(type(a), '_now', return_value=a._now() + timedelta(seconds=30)):
            result = a._operate('heartbeat', lease_args(lease))
        self.assertTrue(result['verification_required'])
        execution = self.root['ydental.queue.execution'].search([('ydental_patient_id', '=', task.ydental_patient_id.id)])
        self.assertEqual(execution.state, 'verify')
        self.assertEqual(task.state, 'started')
        with self.assertRaises(UserError):
            queue_bind(self, self.second)._operate('enter', {'station_id': self.stations[0][0].id})
        with self.assertRaises(AccessError):
            a._handover_contract(execution.id)
        q = qualify(self, task.ydental_patient_id.id, self.mappings[0][1])
        with self.assertRaises(UserError):
            arrive_report(self, q)

    def test_t14_revoke_employee_and_forged_store(self):
        a, lease = enter(self)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        with self.assertRaises(AccessError):
            a._operate('heartbeat', lease_args(lease))
        with self.assertRaises(AccessError):
            queue_bind(self, self.second)._operate('enter', {'station_id': self.stations[1][0].id})
        with self.assertRaises(AccessError):
            self.root['ydental.queue.entry'].create({'name': 'untrusted'})

    def test_t17_unscheduled_entry_creates_no_capacity(self):
        before = {m: self.root[m].search_count([]) for m in ('ydental.supply.slot', 'ydental.supply.claim', 'ydental.intake.task')}
        a, lease = enter(self)
        self.assertIn('No assignment required', a._shift_hint(a._own()))
        self.assertEqual(before, {m: self.root[m].search_count([]) for m in before})
        slot = self.slots[0][0]
        # Existing capacity is explicit; entering a station never manufactures it.
        self.assertEqual(slot.ydental_total, 6)

    def test_t18_switch_success_failure_busy(self):
        a, lease = enter(self)
        b, other = enter(self, queue_bind(self, self.second), self.other_station)
        with self.assertRaises(UserError):
            a._operate('switch', dict(lease_args(lease), station_id=self.other_station.id))
        self.assertTrue(a._own().ydental_station_id == self.stations[0][0])
        b._operate('exit', lease_args(other))
        moved = a._operate('switch', dict(lease_args(lease), station_id=self.other_station.id))
        self.assertFalse(self.root['ydental.queue.lease'].browse(lease['lease_id']).ydental_active)
        self.assertEqual(a._own().ydental_station_id, self.other_station)
        with self.assertRaises(AccessError):
            a._operate('heartbeat', lease_args(lease))
        accepted(self)
        a._operate('call', lease_args(moved))
        with self.assertRaises(UserError):
            a._operate('switch', dict(lease_args(moved), station_id=self.stations[0][0].id))
        with self.assertRaises(UserError):
            a._operate('exit', lease_args(moved))

    def test_t19_shift_end_only_hint(self):
        member = self.admin._membership(self.users['doctor'].id, self.stores[0].id)
        self.root['ydental.supply.assignment']._new({'name': 'Synthetic ended shift', 'ydental_store_id': self.stores[0].id,
            'ydental_category': 'capacity', 'ydental_user_id': self.users['doctor'].id, 'ydental_employee_id': member.ydental_employee_id.id,
            'ydental_station_id': self.stations[0][0].id, 'ydental_start': fields.Datetime.now() - timedelta(hours=2),
            'ydental_end': fields.Datetime.now() - timedelta(hours=1), 'ydental_reason': 'Synthetic shift'})
        task = accepted(self)
        a, lease = enter(self)
        self.assertIn('Shift ended', a._shift_hint(a._own()))
        call = a._operate('call', lease_args(lease))
        self.assertEqual(call['task_id'], task.id)
        self.assertEqual(a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))['state'], 'serving')

    def test_t15_real_hook_rollback_and_s05_single_position(self):
        first = accepted(self)
        other = qualify(self, first.ydental_patient_id.id, self.mappings[0][1])
        self.root['ir.config_parameter'].set_str('ydental_queue_test.refuse_task', str(other['task_id']))
        with self.assertRaises(UserError):
            arrive_report(self, other)
        self.assertEqual(self.front._position(first.ydental_patient_id).ydental_task_id, first)
        self.assertEqual(self.root['ydental.queue.entry'].search([('ydental_task_id', '=', first.id)]).state, 'waiting')
        self.assertFalse(self.root['ydental.queue.entry'].search_count([('ydental_task_id', '=', other['task_id'])]))
        self.root['ir.config_parameter'].set_str('ydental_queue_test.refuse_task', '')
        arrive_report(self, other)
        self.assertEqual(self.root['ydental.queue.entry'].search([('ydental_patient_id', '=', first.ydental_patient_id.id), ('state', 'in', ['waiting', 'calling'])]).ydental_task_id.id, other['task_id'])
        arrive_report(self, {'task_id': first.id})
        self.assertEqual(self.root['ydental.queue.entry'].search([('ydental_task_id', '=', first.id)]).state, 'waiting')

    def test_t15_call_void_vs_start_semantics_and_cancel(self):
        task = accepted(self)
        a, lease = enter(self)
        call = a._operate('call', lease_args(lease))
        held = task.ydental_entitlement_id.ydental_claim_id
        self.front._operate('void', {'task_id': task.id, 'version': task.ydental_version, 'reason': 'Real number void only'}, key())
        self.assertEqual(held.state, 'held')
        with self.assertRaises(UserError):
            a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        call = a._operate('call', lease_args(lease))
        a._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        with self.assertRaises(UserError):
            self.front._operate('void', {'task_id': task.id, 'version': task.ydental_version, 'reason': 'Cannot erase execution'}, key())

    def test_t15_price_snapshot_unchanged_and_qualification_cancel(self):
        price(self)
        snap = self.group._operate('snapshot', {'catalog_id': self.catalogs[0].id, 'currency_id': self.currency.id,
            'quantity': 1, 'source': 'synthetic-a', 'policy': 'demo_confirmation'}, key())
        task = accepted(self)
        e = task.ydental_entitlement_id
        self.front._operate('cancel', {'record_id': e.id, 'version': e.ydental_version, 'reason': 'Synthetic cancelled unused'}, key())
        self.assertEqual(e.ydental_claim_id.state, 'cancelled')
        self.assertEqual(self.root['ydental.intake.snapshot'].browse(snap['id']).ydental_amount, 600)

    def test_document_extension_independent_editors(self):
        a, la = enter(self)
        b, lb = enter(self, queue_bind(self, self.second), self.other_station)
        source = DocumentSource('synthetic-independent-A', la['lease_id'], la['token'])
        first = a._document_lock(source, 'acquire')
        self.assertEqual(a._document_lock(source, 'acquire'), first)
        with self.assertRaises(UserError):
            b._document_lock(DocumentSource(source.key, lb['lease_id'], lb['token']), 'acquire')
        b._document_lock(DocumentSource('synthetic-independent-B', lb['lease_id'], lb['token']), 'acquire')
        with self.assertRaises(AccessError):
            a._document_lock({'key': source.key}, 'release')
        a._document_lock(source, 'release')
        b._document_lock(DocumentSource(source.key, lb['lease_id'], lb['token']), 'acquire')

    def test_parameters_fail_closed_no_production_defaults(self):
        self.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '')
        with self.assertRaises(UserError):
            enter(self)
        self.assertFalse(self.root['ydental.queue.lease'].search_count([]))
