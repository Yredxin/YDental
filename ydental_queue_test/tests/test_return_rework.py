from datetime import timedelta

from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, tagged

from .common import accepted, enter, key, lease_args, queue_bind
from .return_common import appender, close, external, report, reserve, serving, source
from ..models.return_adapter import ReturnSource


@tagged('post_install', '-at_install')
class TestQueueReturnRework(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from .common import setup
        setup(cls)

    def expire(self, queue, lease):
        queue._model('lease').browse(lease['lease_id'])._save({'ydental_expires_at': queue._now() - timedelta(seconds=1)})
        queue._timeout()

    def test_verify_takeover_save_failure_history_and_new_connection(self):
        queue, lease, old = serving(self)
        self.expire(queue, lease)
        resolver = queue_bind(self, self.second)
        args = {'execution_id': old.id, 'confirmed': True, 'reason': 'On-site patient and workstation check'}
        with self.assertRaises(AccessError):
            resolver._operate('takeover_verify', args)
        source(queue, old, save_ok=False)
        with self.assertRaises(UserError):
            resolver._operate('takeover_verify', args)
        self.assertEqual(old.state, 'verify')
        self.assertFalse(resolver._own())
        source(queue, old)
        events = self.root['ydental.supply.event'].search_count([])
        result = resolver._operate('takeover_verify', args)
        new = resolver._model('execution').browse(result['execution_id'])
        self.assertEqual(old.state, 'interrupted')
        self.assertEqual(new.ydental_resumed_from_id, old)
        self.assertEqual(new.ydental_task_id, old.ydental_task_id)
        self.assertEqual(new.state, 'serving')
        self.assertEqual(old.ydental_lease_id.ydental_actor_id, self.users['doctor'])
        self.assertEqual(new.ydental_lease_id.ydental_actor_id, self.second)
        self.assertNotEqual(result['lease_id'], lease['lease_id'])
        self.assertNotEqual(result['token'], lease['token'])
        self.assertFalse(queue._actor_execution())
        self.assertEqual(events, self.root['ydental.supply.event'].search_count([]))
        with self.assertRaises(UserError):
            resolver._operate('takeover_verify', args)
        with self.assertRaises(AccessError):
            queue._operate('heartbeat', lease_args(result))
        self.expire(resolver, result)
        self.assertEqual(resolver._model('entry').search([('ydental_task_id', '=', old.ydental_task_id.id)]).state, 'verify')
        with self.assertRaises(AccessError):
            old.unlink()

    def test_verify_requires_onsite_staff_permission_capability_and_qualification(self):
        queue, lease, old = serving(self)
        source(queue, old)
        self.expire(queue, lease)
        args = {'execution_id': old.id, 'confirmed': False, 'reason': 'On site'}
        resolver = queue_bind(self, self.second)
        with self.assertRaises(AccessError):
            resolver._operate('takeover_verify', args)
        args['confirmed'] = True
        with self.assertRaises(AccessError):
            queue_bind(self, self.users['reader'])._operate('takeover_verify', args)
        self.second.write({'ydental_capability_ids': [(6, 0, [])]})
        with self.assertRaises(AccessError):
            resolver._operate('takeover_verify', args)
        self.second.write({'ydental_capability_ids': [(6, 0, self.capabilities.ids)]})
        self.catalogs[0]._save({'ydental_qualification': 'live license'})
        with self.assertRaises(AccessError):
            resolver._operate('takeover_verify', args)
        self.assertEqual(old.state, 'verify')

    def test_verify_hold_save_then_continuation_no_fake_completion(self):
        queue, lease, old = serving(self)
        hold, target = reserve(self, queue, lease, old)
        self.expire(queue, lease)
        resolver = queue_bind(self, self.second)
        args = {'execution_id': old.id, 'confirmed': True, 'reason': 'Original station inspected in person'}
        source(queue, old, target, save_ok=False)
        with self.assertRaises(UserError):
            resolver._operate('handover_verify_hold', args)
        self.assertEqual(hold.state, 'verify')
        self.assertEqual(old.state, 'reserved')
        source(queue, old, target)
        before = self.root['ydental.supply.event'].search_count([])
        result = resolver._operate('handover_verify_hold', args)
        self.assertEqual(hold.state, 'handover')
        self.assertEqual(old.state, 'handover')
        self.assertEqual(hold.ydental_actor_id, self.users['doctor'])
        self.assertEqual(hold.ydental_lease_id.id, lease['lease_id'])
        self.assertEqual(hold.ydental_resolution_lease_id.id, result['lease_id'])
        self.assertEqual(self.root['ydental.intake.task'].browse(result['continuation_task_id']).state, 'pending')
        self.assertFalse(queue._hold(actor_id=self.users['doctor'].id))
        self.assertEqual(before, self.root['ydental.supply.event'].search_count([]))
        with self.assertRaises(UserError):
            queue._operate('handover_verify_hold', args)
        accepted(self)
        self.assertEqual(resolver._operate('call', lease_args(result))['state'], 'calling')

    def test_hold_rejects_unrelated_care_report_call_start_and_restores_normal_rules(self):
        queue, lease, old = serving(self)
        care = external(self, old, self.mappings[0][0], independent=True)
        hold, target = reserve(self, queue, lease, old)
        with self.assertRaises(UserError):
            report(self, care)
        with self.assertRaises(UserError):
            report(self, old.ydental_task_id)
        entry = queue._model('entry').search([('ydental_task_id', '=', old.ydental_task_id.id)])
        self.assertIn('hold_target_required', queue_bind(self, self.second)._hold_target_reason(care))
        # A pre-existing/stale queue row must be blocked independently at call
        # and start, even without going through today's report validation.
        values = entry.copy_data()[0]
        values.update(ydental_task_id=care.id, state='waiting', ydental_lease_id=False)
        stale = queue._model('entry')._new(values)
        other, other_lease = enter(self, queue_bind(self, self.second), self.other_station)
        with self.assertRaises(UserError):
            other._operate('call', lease_args(other_lease))
        stale._save({'state': 'calling', 'ydental_lease_id': other_lease['lease_id']})
        with self.assertRaises(AccessError):
            other._operate('start', dict(lease_args(other_lease), entry_id=stale.id))
        stale._save({'state': 'void', 'ydental_lease_id': False})
        other._operate('exit', lease_args(other_lease))

        report(self, target)
        self.expire(queue, lease)
        with self.assertRaises(UserError):
            report(self, care)
        queue_bind(self, self.second)._operate('handover_verify_hold', {'execution_id': old.id, 'confirmed': True, 'reason': 'On-site release'})
        report(self, care)
        self.assertEqual(care.state, 'accepted')

    def test_hold_multiple_external_targets_need_trusted_hook_not_client_dict(self):
        queue, lease, old = serving(self)
        hold, target = reserve(self, queue, lease, old)
        extra = external(self, old)
        with self.assertRaises(UserError):
            self.front.with_context(ydental_external_target={'execution_id': old.id, 'task_id': extra.id}, ydental_external_order=True)._operate('report', {'task_id': extra.id, 'version': extra.ydental_version}, key())
        # Independent frozen server source for the extra target; initial hold
        # target remains authorized even when the test source adds another order.
        source(queue, old, extra)
        report(self, extra)
        self.front._withdraw(extra, 'Synthetic switch between valid orders')
        report(self, target)
        self.assertFalse(queue._hold_target_reason(extra))
        self.assertFalse(queue._hold_target_reason(target))

    def test_revoke_closed_reopen_ordinary_start_same_held_entitlement(self):
        task = accepted(self)
        entitlement, claim = task.ydental_entitlement_id, task.ydental_entitlement_id.ydental_claim_id
        close(self)
        app = appender(self)
        permit = app._operate('append', {'task_id': task.id, 'reason': 'Explicit stopped admission'})
        queue, lease = enter(self)
        call = queue._operate('call', lease_args(lease))
        before = self.root['ydental.supply.event'].search_count([])
        app._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'Revoke closed exception'})
        with self.assertRaises(UserError):
            queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        with self.assertRaises(UserError):
            report(self, task)
        self.assertEqual(entitlement.state, 'held')
        self.assertEqual(claim.state, 'held')
        self.assertEqual(before, self.root['ydental.supply.event'].search_count([]))
        business = self.root['ydental.supply.service']._business_record(self.stores[0], self.areas[0][0].id)
        business._save({'state': 'open'})
        report(self, task)
        call = queue._operate('call', lease_args(lease))
        queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
        self.assertEqual(task.ydental_entitlement_id, entitlement)
        self.assertEqual(claim.state, 'consumed')
        self.assertEqual(queue._model('append.permit').browse(permit['permit_id']).state, 'revoked')
        self.assertEqual(queue._model('append.permit').search_count([('ydental_task_id', '=', task.id)]), 1)
        self.assertEqual(self.root['ydental.supply.event'].search_count([]), before + 1)
