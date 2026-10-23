"""PURE safety/acceptance-oracle tests; no Odoo, database, HTTP or service.

Synthetic cursor objects exercise abort/unknown boundaries only. They are
never offered as MODEL competition, server waits or committed-state evidence.
"""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path

import race_lab_cancel_receive as cancel
import race_lab_putaway_duplicate as putaway
import race_lab_receipt_duplicate as common


class NativeAbort(Exception):
    pgcode = '40001'


class RetryRequest(Exception):
    pass


class BusinessError(Exception):
    pass


class Cursor:
    def __init__(self, commit_error=None, rollback_error=None):
        self.commit_error = commit_error
        self.rollback_error = rollback_error
        self.closed = False
        self._cnx = self
        self.calls = []

    def execute(self, sql, params=None):
        self.calls.append('execute')

    def fetchone(self):
        return 700001, 'repeatable read', 'synthetic-unit-only'

    def commit(self):
        self.calls.append('commit')
        if self.commit_error:
            raise self.commit_error

    def rollback(self):
        self.calls.append('rollback')
        if self.rollback_error:
            raise self.rollback_error

    def get_transaction_status(self):
        # Native Odoo reset hooks can reopen a transaction after rollback;
        # safe known-abort cleanup must not misreport this as unknown commit.
        return 2

    def close(self):
        self.calls.append('close')
        self.closed = True


class Registry:
    def __init__(self, cursor):
        self.value = cursor

    def cursor(self):
        return self.value


class Service:
    def __init__(self, action_error=None):
        self.action_error = action_error
        self.env = self

    def __getitem__(self, model):
        return self

    def _existing_session_for_key(self, key):
        return type('Session', (), {'id': 10001})()

    def _bind(self, session):
        return self

    def _operate(self, operation, payload, key):
        if self.action_error:
            raise self.action_error
        return {'result': 'accepted', 'state': 'received', 'order_id': 20001,
                'inventory_event_id': False}


class API:
    def __init__(self, service):
        self.service = service

    def Environment(self, *args):
        return self.service


def baseline():
    return {'order_id': 20001, 'store_id': 1, 'patient_id': 30001,
            'source_event_id': 40001, 'responsible_id': 11, 'followup_id': None,
            'followups': [], 'jobs': [], 'activities': []}


def plan():
    return {'id': 50001, 'ydental_store_id': [1, 'synthetic'], 'state': 'planned',
            'ydental_lab_order_id': 20001, 'ydental_lab_cycle_key': 'order',
            'ydental_lab_contact_stage': 'waiting', 'ydental_followup_type': 'lab_arrival',
            'ydental_patient_id': [30001, 'synthetic'], 'ydental_source_event_id': [40001, 'synthetic'],
            'ydental_responsible_id': [11, 'synthetic'], 'ydental_schedule_version': 4,
            'ydental_active_notification_request_id': False,
            'ydental_active_notification_schedule_version': 0}


class TransactionEvidenceTests(unittest.TestCase):
    def run_attempt(self, action_error=None, commit_error=None, rollback_error=None, expected=None):
        cr = Cursor(commit_error, rollback_error)
        with tempfile.TemporaryDirectory(prefix='s11-race-pure-') as folder:
            journal = common.Journal(Path(folder) / 'stages.jsonl')
            spec = {'operation': 'receive', 'payload': {'order_id': 20001}, 'key': 'synthetic-key-only'}
            if expected:
                spec['expected_error'] = expected
            result = common.execute_attempt(Registry(cr), API(Service(action_error)), 13,
                'synthetic-session-only', spec, 1, 1, threading.Barrier(1), journal,
                threading.local(), RetryRequest, BusinessError)
            journal.close()
            content = journal.path.read_text()
            rows = [json.loads(line) for line in content.splitlines()]
            self.assertNotIn('synthetic-key-only', content)
            self.assertNotIn('synthetic-session-only', content)
            self.assertEqual(journal.path.stat().st_mode & 0o777, 0o600)
        return cr, result, rows

    def test_accepted_is_recorded_after_commit_return(self):
        cr, result, rows = self.run_attempt()
        self.assertTrue(result['commit_returned'])
        stages = [r['stage'] for r in rows]
        self.assertLess(stages.index('action_returned'), stages.index('commit_started'))
        self.assertLess(stages.index('commit_started'), stages.index('commit_returned'))
        self.assertLess(stages.index('commit_returned'), stages.index('cursor_closed'))
        self.assertEqual(cr.calls.count('commit'), 1)
        self.assertNotIn('rollback', cr.calls)

    def test_native_precommit_abort_is_retryable_only_after_rollback_and_close(self):
        cr, result, rows = self.run_attempt(action_error=NativeAbort('not logged'))
        self.assertTrue(result['retry_safe'])
        self.assertFalse(result['commit_started'])
        self.assertTrue(result['rollback_returned'])
        self.assertTrue(result['cursor_closed'])
        self.assertNotIn('commit', cr.calls)
        self.assertEqual([r['stage'] for r in rows][-3:],
                         ['rollback_started', 'rollback_returned', 'cursor_closed'])

    def test_native_odoo_request_abort_is_also_known(self):
        _, result, _ = self.run_attempt(action_error=RetryRequest('not logged'))
        self.assertTrue(result['retry_safe'])

    def test_commit_time_40001_stays_unknown_and_never_retries(self):
        _, result, rows = self.run_attempt(commit_error=NativeAbort('not logged'))
        self.assertEqual(result['kind'], 'unknown_commit')
        self.assertFalse(result['retry_safe'])
        self.assertTrue(result['commit_started'])
        self.assertNotIn('commit_returned', [r['stage'] for r in rows])

    def test_postcommit_callback_failure_is_not_replayed(self):
        _, result, _ = self.run_attempt(commit_error=RuntimeError('after actual commit, synthetic boundary'))
        self.assertEqual(result['kind'], 'unknown_commit')
        self.assertFalse(result['retry_safe'])

    def test_failed_rollback_prevents_known_abort_retry(self):
        _, result, _ = self.run_attempt(action_error=NativeAbort(), rollback_error=RuntimeError())
        self.assertFalse(result['retry_safe'])
        self.assertFalse(result['rollback_returned'])

    def test_expected_loser_uses_rollback_without_commit(self):
        cr, result, _ = self.run_attempt(action_error=BusinessError('state conflict'), expected='state conflict')
        self.assertEqual(result['kind'], 'expected_state_conflict')
        self.assertNotIn('commit', cr.calls)
        self.assertTrue(result['rollback_returned'])
        self.assertFalse(result['retry_safe'])

    def test_other_usererror_cannot_be_labeled_expected_loser(self):
        _, result, _ = self.run_attempt(action_error=BusinessError('access denied'), expected='state conflict')
        self.assertEqual(result['kind'], 'aborted')
        self.assertFalse(result['retry_safe'])

    def test_unexpected_error_payload_is_not_persisted(self):
        _, _, rows = self.run_attempt(action_error=RuntimeError('secret clinical text do not log'))
        self.assertNotIn('secret clinical text', json.dumps(rows))

    def test_journal_exclusive_path_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'stages.jsonl'
            first = common.Journal(p)
            first.add('original')
            first.close()
            original = p.read_bytes()
            with self.assertRaises(FileExistsError):
                common.Journal(p)
            self.assertEqual(original, p.read_bytes())

    def test_client_barrier_timing_is_not_server_lock_evidence(self):
        rows = [dict(worker_id=w, attempt=1, stage=s, monotonic_ns=t)
                for w, s, t in [(1, 'action_started', 1), (2, 'action_started', 2),
                                 (1, 'commit_returned', 5), (2, 'rollback_returned', 6)]]
        metrics = common.overlap_evidence(rows)
        self.assertEqual(metrics['first_attempt_action_overlap_ns'], 3)
        self.assertFalse(metrics['native_lab_lock_contention_observed'])
        rows.append(dict(worker_id=1, attempt=1, stage='native_lock_state_observed', monotonic_ns=3,
                         locks=[{'pid': 101, 'granted': True}, {'pid': 102, 'granted': False}]))
        self.assertTrue(common.overlap_evidence(rows)['native_lab_lock_contention_observed'])
        rows[-1]['locks'][1]['pid'] = 101
        self.assertFalse(common.overlap_evidence(rows)['native_lab_lock_contention_observed'])

    def test_native_lock_instrumentation_forwards_exact_sql_and_return_value(self):
        class NativeCursor:
            def __init__(self):
                self.calls = []

            def execute(self, query, params=None):
                self.calls.append((query, params))
                return 'actual-native-return-value'

        cursor = NativeCursor()
        original = NativeCursor.execute
        local = threading.local()
        local.context = {'worker_id': 1, 'operation': 'receive', 'attempt': 1, 'backend_pid': 700001}
        local.cursor = cursor
        with tempfile.TemporaryDirectory() as folder:
            journal = common.Journal(Path(folder) / 'native.jsonl')
            with common.observe_native_locks(NativeCursor, journal, local, threading.Barrier(1)):
                value = cursor.execute('SELECT pg_advisory_xact_lock(%s)', [31911])
                self.assertEqual(value, 'actual-native-return-value')
                self.assertEqual(cursor.calls, [('SELECT pg_advisory_xact_lock(%s)', [31911])])
                self.assertEqual([r['stage'] for r in journal.rows],
                                 ['native_lock_call_started', 'native_lock_call_returned'])
                self.assertFalse(common.overlap_evidence(journal.rows)['native_lab_lock_contention_observed'])
            journal.close()
        self.assertIs(NativeCursor.execute, original)


class PhysicalBusinessOracleTests(unittest.TestCase):
    def test_legacy_missing_plan_is_not_backfilled_by_preflight(self):
        data = baseline()
        original = copy.deepcopy(data)
        common.validate_waiting_plan(data)
        self.assertEqual(data, original)

    def test_new_waiting_plan_and_real_appointment_job_are_accepted(self):
        data = baseline()
        data.update(followup_id=50001, followups=[plan()],
                    jobs=[{'id': 1, 'ydental_event_type': 'appointment_reminder', 'ydental_state': 'pending'}])
        common.validate_waiting_plan(data)

    def test_wrong_source_store_or_stage_plan_is_refused(self):
        for field, value in [('ydental_source_event_id', [999, 'other']),
                             ('ydental_store_id', [2, 'other']), ('ydental_lab_contact_stage', 'ready')]:
            data = baseline()
            row = plan()
            row[field] = value
            data.update(followup_id=50001, followups=[row])
            with self.subTest(field=field), self.assertRaises(common.Refusal):
                common.validate_waiting_plan(data)

    def test_prearrival_job_is_not_accepted_as_a_fixture(self):
        data = baseline()
        data.update(followup_id=50001, followups=[plan()],
                    jobs=[{'id': 1, 'ydental_event_type': 'lab_arrival', 'ydental_state': 'accepted'}])
        with self.assertRaises(common.Refusal):
            common.validate_waiting_plan(data)

    def test_cancellation_retires_pending_preserves_sent_unknown_and_done(self):
        before = baseline()
        row = plan()
        row['state'] = 'done'
        before.update(followup_id=50001, followups=[row], jobs=[
            {'id': i, 'ydental_state': state, 'ydental_attempt_count': attempt}
            for i, state, attempt in [(1, 'pending', 0), (2, 'accepted', 1), (3, 'unknown', 1)]])
        after = copy.deepcopy(before)
        after['followups'][0].update(ydental_lab_contact_stage='stopped', ydental_schedule_version=5)
        after['jobs'][0]['ydental_state'] = 'cancelled'
        self.assertTrue(cancel.cancelled_plan_is_exact(before, after))
        after['jobs'][1]['ydental_attempt_count'] = 2
        self.assertFalse(cancel.cancelled_plan_is_exact(before, after))

    def test_cancel_cannot_keep_open_waiting_plan(self):
        before = baseline()
        before.update(followup_id=50001, followups=[plan()])
        after = copy.deepcopy(before)
        after['followups'][0].update(ydental_lab_contact_stage='stopped', ydental_schedule_version=5)
        self.assertFalse(cancel.cancelled_plan_is_exact(before, after))
        after['followups'][0]['state'] = 'closed'
        self.assertTrue(cancel.cancelled_plan_is_exact(before, after))

    def test_legacy_cancel_requires_two_real_responsible_activities(self):
        before = baseline()
        after = copy.deepcopy(before)
        physical = {'id': 1, 'active': True, 'res_model': 'ydental.lab.order', 'res_id': 20001,
                    'user_id': [13, 'synthetic'], 'physical_financial_instructions': True,
                    'communication_instructions': False}
        communication = dict(physical, id=2, user_id=[11, 'synthetic'],
                             physical_financial_instructions=False, communication_instructions=True)
        after['activities'] = [physical, communication]
        self.assertTrue(cancel.cancellation_activities_are_real(before, after, 13))
        after['activities'][1]['user_id'] = [13, 'wrong actor']
        self.assertFalse(cancel.cancellation_activities_are_real(before, after, 13))
        after['activities'] = [physical]
        self.assertFalse(cancel.cancellation_activities_are_real(before, after, 13))

    def test_putaway_activates_same_plan_once_preserves_done(self):
        before = baseline()
        before.update(followup_id=50001, followups=[plan()])
        after = copy.deepcopy(before)
        after['followups'][0].update(ydental_lab_contact_stage='ready', ydental_schedule_version=5)
        self.assertTrue(putaway.plan_transition_is_exact(before, after))
        after['followups'][0]['id'] = 50002
        self.assertFalse(putaway.plan_transition_is_exact(before, after))
        before['followups'][0]['state'] = 'done'
        after = copy.deepcopy(before)
        self.assertTrue(putaway.plan_transition_is_exact(before, after))

    def test_physical_history_includes_fee_and_sent_snapshot(self):
        before = {'lab_events': [{'id': 1, 'ydental_kind': 'sent'}],
                  'economic': {'fee': [{'id': 1, 'ydental_amount': 137.25}], 'sent_snapshots': [{'cost': 42.75}]},
                  'purchase_cost_source': {'line_id': 9, 'total': 42.75}}
        after = copy.deepcopy(before)
        after['lab_events'].append({'id': 2, 'ydental_kind': 'received'})
        self.assertTrue(common.physical_history_preserved(before, after))
        after['economic']['fee'][0]['ydental_amount'] = 0
        self.assertFalse(common.physical_history_preserved(before, after))


if __name__ == '__main__':
    unittest.main()
