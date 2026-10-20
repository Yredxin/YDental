from datetime import timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import queue_bind, serving, setup


@tagged('post_install', '-at_install')
class TestClinicalEmptyExecutionRecovery(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def test_timed_out_empty_execution_requires_onsite_recovery_and_new_capacity(self):
        queue, lease, execution = serving(self)
        task = execution.ydental_task_id
        old_entitlement = task.ydental_entitlement_id
        entry = execution.ydental_entry_id
        replacement_slot = self.slots[0][0]
        lease_record = queue._model('lease').browse(lease['lease_id'])
        lease_record._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()

        resolver = queue_bind(self, self.second)
        args = {
            'execution_id': execution.id,
            'confirmed': False,
            'replacement_slot_id': replacement_slot.id,
            'reason': 'Synthetic on-site recovery before opening a clinical document',
        }
        with self.assertRaises(AccessError):
            resolver._operate('recover_empty_execution', args)

        claims = self.root['ydental.supply.claim']
        claims_before = claims.search_count([])
        tasks_before = self.root['ydental.intake.task'].search_count([])
        entitlements_before = self.root['ydental.intake.entitlement'].search_count([])
        recoveries_before = self.root['ydental.access.audit'].search_count([
            ('ydental_event', '=', 'queue.empty_execution_recovered')])
        reservation_free = replacement_slot.ydental_reservation_free
        replacement_slot._save({'ydental_reservation_free': 0})
        with self.assertRaises(UserError):
            resolver._operate('recover_empty_execution', args | {'confirmed': True})
        self.assertEqual((execution.state, task.state, entry.state), ('verify', 'started', 'verify'))
        self.assertEqual(claims.search_count([]), claims_before)
        self.assertEqual(self.root['ydental.intake.task'].search_count([]), tasks_before)
        self.assertEqual(self.root['ydental.intake.entitlement'].search_count([]), entitlements_before)
        self.assertEqual(self.root['ydental.access.audit'].search_count([
            ('ydental_event', '=', 'queue.empty_execution_recovered')]), recoveries_before)
        replacement_slot._save({'ydental_reservation_free': reservation_free})

        stock_before = (self.root['stock.move'].search_count([]), self.root['stock.quant'].search_count([]))
        result = resolver._operate('recover_empty_execution', args | {'confirmed': True})
        replacement = self.root['ydental.intake.task'].browse(result['replacement_task_id'])
        new_entitlement = replacement.ydental_entitlement_id

        self.assertEqual(execution.state, 'interrupted')
        self.assertEqual(task.state, 'cancelled')
        self.assertEqual(entry.state, 'void')
        self.assertEqual((old_entitlement.state, old_entitlement.ydental_claim_id.state), ('started', 'consumed'))
        self.assertEqual((replacement.state, new_entitlement.state, new_entitlement.ydental_claim_id.state),
                         ('pending', 'held', 'held'))
        self.assertEqual(new_entitlement.ydental_claim_id.ydental_slot_id, replacement_slot)
        self.assertEqual(new_entitlement.ydental_source_task_id, task)
        self.assertEqual(stock_before, (self.root['stock.move'].search_count([]), self.root['stock.quant'].search_count([])))
        self.assertFalse(self.root['ydental.clinical.document'].search_count([
            ('ydental_current_execution_id', '=', execution.id)]))
        self.assertFalse(self.root['ydental.treatment.event'].search_count([('ydental_execution_id', '=', execution.id)]))
        self.assertEqual(self.root['ydental.access.audit'].search_count([
            ('ydental_event', '=', 'queue.empty_execution_recovered'),
            ('ydental_target_id', '=', execution.id),
        ]), 1)
        claims_after_recovery = claims.search_count([])
        with self.assertRaises(UserError):
            resolver._operate('recover_empty_execution', args | {'confirmed': True})
        self.assertEqual(claims.search_count([]), claims_after_recovery)
        self.assertEqual(self.root['ydental.intake.task'].search_count([]), tasks_before + 1)
        self.assertEqual(self.root['ydental.intake.entitlement'].search_count([]), entitlements_before + 1)

        replacement_lease = queue._operate('enter', {'station_id': self.stations[0][0].id})
        queue._operate('exit', {'lease_id': replacement_lease['lease_id'], 'token': replacement_lease['token']})

    def test_document_immutable_execution_source_blocks_recovery(self):
        queue, lease, execution = serving(self)
        clinical = queue.env['ydental.clinical.service']
        document = clinical._operate('open', {
            'execution_id': execution.id,
            'lease_id': lease['lease_id'],
            'lease_token': lease['token'],
        })
        doc = self.root['ydental.clinical.document'].browse(document['document_id'])

        _, _, other_execution = serving(self, user=self.users['manager'], station=self.other_station)
        doc._save({'ydental_current_execution_id': other_execution.id})
        lease_record = queue._model('lease').browse(lease['lease_id'])
        lease_record._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()

        resolver = queue_bind(self, self.second)
        with self.assertRaises(AccessError):
            resolver._operate('recover_empty_execution', {
                'execution_id': execution.id,
                'confirmed': True,
                'replacement_slot_id': self.slots[0][0].id,
                'reason': 'Synthetic recovery must preserve the immutable document source',
            })
        self.assertEqual(doc.ydental_execution_id, execution)
        self.assertEqual(doc.ydental_current_execution_id, other_execution)
        self.assertEqual(execution.state, 'verify')
