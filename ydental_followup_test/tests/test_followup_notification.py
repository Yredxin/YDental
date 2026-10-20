import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.ydental_followup.models import (
    ydental_followup_service as followup_service_module,
)
from odoo.addons.ydental_followup.models.ydental_followup_service import (
    _authorize_passive_lab_write,
    _callback_matches_current_request,
    _daily_cap_attempt_counts,
    _reconciliation_action,
    _supplier_expiry_authorized,
    _supplier_qualification_is_current,
)


@tagged('post_install', '-at_install')
class TestFollowupNotification(TransactionCase):

    def setUp(self):
        super().setUp()
        self.store = self.env['ydental.access.store'].sudo().create({
            'name': 'S11 synthetic follow-up store', 'company_id': self.env.company.id,
            'ydental_timezone': 'UTC',
        })
        self.manager = new_test_user(
            self.env, login='s11_followup_' + secrets.token_hex(5),
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager',
            company_ids=[fields.Command.set([self.env.company.id])],
        )
        access = self.env['ydental.access.service'].with_user(self.manager)
        session = access._session_for_key('s11-followup-' + secrets.token_hex(12))
        bound = access._bind(session)
        bound._join(self.manager.id, self.store.id)
        bound._grant(self.manager.id, self.store.id, {'followup': 'write'})
        bound._switch(self.store.id)
        self.followup_service = bound._bind(session).env['ydental.followup.service']
        self.job = self.env['ydental.notification.job'].sudo()._new({
            'name': 'S11 synthetic callback job', 'ydental_store_id': self.store.id,
            'ydental_category': 'followup', 'ydental_source_model': 'ydental.followup',
            'ydental_source_res_id': 999999, 'ydental_event_type': 'followup_contact',
            'ydental_source_version': 1, 'ydental_channel_key': 'patient',
            'ydental_due_at': '2026-10-19 12:00:00',
        })
        self.job._save({'ydental_state': 'unknown', 'ydental_request_id': 's11-test-request-identifier'})
        self.secret = 's11-synthetic-callback-secret-only-for-tests'
        self.env['ir.config_parameter'].sudo().set_str('ydental_followup.callback_secret', self.secret)

    def _callback(self, event_id, status):
        # The callback emulates a later HTTP transaction, which would see this
        # dispatch request after commit. Flush the pending ORM write before the
        # production callback's locking SQL lookup in this same test cursor.
        self.job.flush_recordset(['ydental_request_id'])
        body = json.dumps({
            'request_id': self.job.ydental_request_id, 'event_id': event_id, 'status': status,
        }, separators=(',', ':')).encode()
        signature = 'sha256=' + hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
        return self.env['ydental.followup.service'].sudo()._receive_callback(body, signature)

    def test_followup_direct_create_is_denied_even_for_admin(self):
        with self.assertRaises(AccessError):
            self.env['ydental.followup'].sudo().create({'name': 'Bypass attempt'})

    def test_enqueue_registers_deferred_postcommit_dispatch(self):
        callbacks = self.env.cr.postcommit
        registered = []
        add_callback = type(callbacks).add

        def capture_callback(queue, callback):
            if queue is callbacks:
                registered.append(callback)
            return add_callback(queue, callback)

        with patch.object(followup_service_module, '_dispatch_after_commit') as dispatch:
            with patch.object(type(callbacks), 'add', autospec=True, side_effect=capture_callback):
                job = self.followup_service._enqueue(
                    store=self.store,
                    source_model='ydental.followup',
                    source_id=999998,
                    source_version=1,
                    event_type='followup_contact',
                    due_at=fields.Datetime.now(),
                )

            self.assertEqual(job.ydental_state, 'pending')
            self.assertEqual(len(registered), 1)
            dispatch.assert_not_called()

            # This invokes only the newly registered callback. The dispatcher is
            # mocked, so this proves callback wiring, not transaction commit,
            # independent claiming, transport, or patient delivery.
            registered[0]()
            dispatch.assert_called_once_with(self.env.cr.dbname, (job.id,))

    def test_callback_deduplicates_and_late_acceptance_does_not_regress_delivery(self):
        first = self._callback('provider-event-delivered', 'delivered')
        self.assertEqual(first['state'], 'delivered')
        duplicate = self._callback('provider-event-delivered', 'delivered')
        self.assertEqual(duplicate['result'], 'duplicate')
        late = self._callback('provider-event-late-accepted', 'accepted')
        self.assertEqual(late['state'], 'delivered')
        self.assertEqual(self.job.ydental_state, 'delivered')

    def test_callback_idempotency_key_rejects_conflicting_payload(self):
        self._callback('provider-event-conflict', 'accepted')
        with self.assertRaises(UserError):
            self._callback('provider-event-conflict', 'failed')

    def test_late_callback_is_recorded_but_cannot_revive_cancelled_job(self):
        self.job._save({'ydental_state': 'cancelled'})
        response = self._callback('provider-event-after-cancel', 'delivered')
        self.assertEqual(response['state'], 'cancelled')
        self.assertEqual(self.job.ydental_state, 'cancelled')
        receipt = self.env['ydental.notification.callback'].sudo().search([
            ('ydental_job_id', '=', self.job.id),
            ('ydental_provider_event_id', '=', 'provider-event-after-cancel'),
        ])
        self.assertEqual(len(receipt), 1)

    def test_invalid_callback_signature_is_rejected(self):
        body = json.dumps({
            'request_id': self.job.ydental_request_id, 'event_id': 'provider-event-invalid',
            'status': 'delivered',
        }, separators=(',', ':')).encode()
        with self.assertRaises(AccessError):
            self.env['ydental.followup.service'].sudo()._receive_callback(body, 'sha256=invalid')

    def test_accepted_then_delivered_callback_stays_valid_for_same_request_only(self):
        self._callback('provider-event-accepted', 'accepted')
        delivered = self._callback('provider-event-delivered-after-accept', 'delivered')
        self.assertEqual(delivered['state'], 'delivered')
        self.assertTrue(_callback_matches_current_request(
            'accepted', 4, 5, 'same-request', 5, 'same-request'))
        self.assertFalse(_callback_matches_current_request(
            'accepted', 4, 6, 'same-request', 5, 'same-request'))

    def test_manual_accepted_reconciliation_keeps_same_request_open_to_delivery_callback(self):
        reconciled = self.followup_service._operate('reconcile_unknown', {
            'job_id': self.job.id, 'outcome': 'accepted', 'evidence': 'controlled sink inquiry confirmed acceptance',
        })
        self.assertEqual(reconciled['result'], 'reconciled')
        self.assertEqual(self.job.ydental_state, 'accepted')
        result = self._callback('provider-event-after-manual-check', 'delivered')
        self.assertEqual(result['state'], 'delivered')

    def test_failed_started_outbound_attempt_counts_toward_local_daily_cap(self):
        day_start = datetime(2026, 10, 19, 0, 0, 0)
        day_end = day_start + timedelta(days=1)
        started = datetime(2026, 10, 19, 13, 45, 0)
        self.assertTrue(_daily_cap_attempt_counts(1, started, day_start, day_end))
        self.assertFalse(_daily_cap_attempt_counts(0, started, day_start, day_end))
        self.assertFalse(_daily_cap_attempt_counts(1, day_end, day_start, day_end))

    def test_after_commit_dispatch_does_not_hold_an_extra_registry_cursor(self):
        call_order = []

        def claim(dbname, job_id):
            call_order.append(('claim', dbname, job_id))
            return 'stable-request', False

        def dispatch(dbname, job_id, request_id):
            call_order.append(('dispatch', dbname, job_id, request_id))

        with patch.object(followup_service_module, '_claim_dispatch', side_effect=claim) as claim_mock, \
                patch.object(followup_service_module, '_dispatch_claimed', side_effect=dispatch) as dispatch_mock, \
                patch.object(followup_service_module.Registry, 'cursor') as cursor:
            followup_service_module._dispatch_after_commit('s11_test_db', (41, 41))
        claim_mock.assert_called_once_with('s11_test_db', 41)
        dispatch_mock.assert_called_once_with('s11_test_db', 41, 'stable-request')
        self.assertEqual(call_order, [
            ('claim', 's11_test_db', 41),
            ('dispatch', 's11_test_db', 41, 'stable-request'),
        ])
        cursor.assert_not_called()

    def test_supplier_expiry_claim_requires_current_approved_qualification_and_cooperation(self):
        self.assertTrue(_supplier_qualification_is_current(7, 7, 'approved', '2026-11-01', '2026-11-01', True, True))
        self.assertFalse(_supplier_qualification_is_current(7, 8, 'approved', '2026-12-01', '2026-11-01', True, True))
        self.assertFalse(_supplier_qualification_is_current(7, 7, 'draft', '2026-11-01', '2026-11-01', True, True))
        self.assertFalse(_supplier_qualification_is_current(7, 7, 'approved', '2026-11-01', '2026-11-01', True, False))
        self.assertFalse(_supplier_qualification_is_current(7, 7, 'approved', '2026-12-01', '2026-11-01', True, True))

    def test_supplier_expiry_hook_authorization_is_manager_or_exact_local_cooperation_only(self):
        self.assertTrue(_supplier_expiry_authorized(True, False, True, True, True, True, True, True))
        self.assertTrue(_supplier_expiry_authorized(False, True, True, True, True, True, True, True))
        self.assertFalse(_supplier_expiry_authorized(False, False, True, True, True, True, True, True))
        self.assertFalse(_supplier_expiry_authorized(False, True, True, True, True, True, False, True))
        self.assertFalse(_supplier_expiry_authorized(True, False, True, True, False, True, True, True))
        self.assertFalse(_supplier_expiry_authorized(True, False, True, True, True, True, True, False))

    def test_unknown_reconciliation_is_idempotent_for_same_result_and_rejects_conflict(self):
        self.assertEqual(_reconciliation_action('unknown', 'accepted'), 'apply')
        self.assertEqual(_reconciliation_action('accepted', 'accepted'), 'duplicate')
        self.assertEqual(_reconciliation_action('accepted', 'delivered'), 'conflict')
        self.assertTrue(_callback_matches_current_request(
            'accepted', 3, 4, 's11-test-request-identifier', 4, 's11-test-request-identifier'))

    def test_passive_lab_hook_uses_warehouse_write_without_followup_actor_role(self):
        store = SimpleNamespace(id=71)

        class WarehouseOnlyAccess:
            def __init__(self):
                self.calls = []

            def _scope(self):
                return SimpleNamespace(ydental_store_id=store)

            def _check(self, category, level, store_id, write=False):
                self.calls.append((category, level, store_id, write))
                if category != 'warehouse' or level != 'write' or not write:
                    raise AssertionError('The hook must not require follow-up write from the putaway actor.')

        access = WarehouseOnlyAccess()
        _authorize_passive_lab_write(access, store)
        self.assertEqual(access.calls, [('warehouse', 'write', store.id, True)])

    def test_workbench_shows_contact_history_and_uses_guarded_record_selectors(self):
        view = self.env.ref('ydental_followup.followup_list')
        arch = view.arch_db
        self.assertIn('Contact history', arch)
        self.assertIn('name="source_event_id"', arch)
        self.assertIn('name="appointment_id"', arch)
        self.assertIn('name="arrival_id"', arch)
        self.assertIn('name="event_id"', arch)
        self.assertNotIn('type="number"', arch)
