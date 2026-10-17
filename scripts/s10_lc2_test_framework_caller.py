"""TR-01 caller checks: actual HttpCase method AST, private files and fake send only."""
import ast
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import types
import sys
import unittest
from unittest.mock import MagicMock, patch

from s10_lc2_evidence import Budget, CORE, CLUSTER, save_once
import s10_lc2_targets as parent_targets

ROOT = Path(__file__).resolve().parents[1]
HTTP_SOURCE = ROOT / 'ydental_settlement_test/tests/test_log_closeout.py'


def separate_module(name, filename):
    """Fresh globals, not an alias to the parent's process-local owner/latch."""
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def actual_http_class(environment, sender):
    tree = ast.parse(HTTP_SOURCE.read_text())
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                    and node.name == 'TestLogCloseoutHTTP')
    method = next(node for node in original.body if isinstance(node, ast.FunctionDef)
                  and node.name == 'url_open')
    adapter = ast.ClassDef(name='TestLogCloseoutHTTP', bases=[ast.Name(id='HttpCase', ctx=ast.Load())],
                           keywords=[], body=[method], decorator_list=[])

    class HttpCase:
        def url_open(self, *args, **kwargs):
            return sender(*args, **kwargs)

    namespace = {'HttpCase': HttpCase, 'os': types.SimpleNamespace(environ=environment)}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[adapter], type_ignores=[])),
                 str(HTTP_SOURCE), 'exec'), namespace)
    return namespace['TestLogCloseoutHTTP']


class ParentCallerCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lc2-parent-caller-pure-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.scope = ExitStack()
        self.addCleanup(self.scope.close)
        self.scope.enter_context(patch.object(parent_targets, '_DISPATCH_OWNER', None))
        self.scope.enter_context(patch.object(parent_targets, '_DISPATCH_FAILURE', None))
        self.scope.enter_context(patch.object(parent_targets, 'EXEC_ROOT', self.directory))

    def test_parent_owner_check_precedes_one_shared_budget_reservation(self):
        events = []
        owner = types.SimpleNamespace(check=lambda: events.append('check'))
        parent_targets.bind_dispatch_owner(owner)
        budget = parent_targets.PackageBudget(self.directory, started_epoch=time.time())
        self.scope.enter_context(patch.object(budget, 'check_storage', lambda: None))
        self.assertEqual(budget.consume('http'), 1)
        self.assertEqual(events, ['check'])
        self.assertEqual(json.loads(budget.path.read_text())['counts']['http'], 1)

    def test_parent_still_refuses_missing_owner_and_frozen_owner(self):
        budget = parent_targets.PackageBudget(self.directory, started_epoch=time.time())
        with self.assertRaisesRegex(RuntimeError, 'NO_ACTIVE_APPLICATION_DISPATCH_GUARD'):
            budget.consume('http')
        owner = types.SimpleNamespace(check=lambda: self.fail('frozen owner checked'))
        parent_targets.bind_dispatch_owner(owner)
        parent_targets.freeze_dispatch({'reason': 'SYNTHETIC_FIRST'})
        with self.assertRaisesRegex(RuntimeError, 'APPLICATION_DISPATCH_FROZEN_SYNTHETIC_FIRST'):
            budget.consume('http')
        self.assertEqual(json.loads(budget.path.read_text())['counts'], {})

    def test_separate_targets_namespace_does_not_inherit_parent_owner(self):
        owner = types.SimpleNamespace(check=lambda: None)
        parent_targets.bind_dispatch_owner(owner)
        child = separate_module('lc2_child_targets_synthetic', 's10_lc2_targets.py')
        child.EXEC_ROOT = self.directory / 'child-shared-state'
        self.assertIsNone(child._DISPATCH_OWNER)
        self.assertIsNone(child._DISPATCH_FAILURE)
        self.assertIs(parent_targets._DISPATCH_OWNER, owner)


class FrameworkCallerCase(unittest.TestCase):
    """All contexts are synthetic; no Odoo import, process or request is made."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='lc2-framework-caller-pure-')
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.scope = ExitStack()
        self.addCleanup(self.scope.close)
        self.child = separate_module('lc2_framework_child_synthetic', 's10_lc2_framework_caller.py')
        self.scope.enter_context(patch('time.time', return_value=self.child.AUTHORIZATION_EPOCH + 1000))
        self.database = 'ydental_s10_test_20261017120000_1234abcd'
        self.execution = self.directory / 'execution'
        self.run_root = self.directory / 'runs'
        self.run = self.run_root / self.database
        self.application = self.execution / 'application-scratch-tests-1234abcd'
        for path in (self.execution, self.run_root, self.run, self.run / 'diagnostics', self.application):
            path.mkdir(mode=0o700)
        self.scope.enter_context(patch.object(parent_targets, 'EXEC_ROOT', self.execution))
        self.source = self.directory / 'source'
        self.source.mkdir(mode=0o700)
        frozen = {}
        for relative in self.child.FROZEN_FILES:
            path = self.source / relative
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            path.write_bytes(b'synthetic frozen source\n')
            frozen[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.child.ROOT = self.source
        self.child.EXEC_ROOT = self.execution
        self.child.RUN_ROOT = self.run_root
        self.child.LEGACY_EXEC_ROOT = self.directory / 'absent-old-budget'
        self.fake_os = types.SimpleNamespace(**vars(os))
        self.fake_os.getpid = lambda: 100
        self.fake_os.getppid = lambda: 99
        self.child.os = self.fake_os
        self.budget = Budget(self.execution, started_epoch=self.child.AUTHORIZATION_EPOCH)
        # This is the pre-existing cumulative ledger, not a new per-child budget.
        self.budget.path.write_text(json.dumps({'started_epoch': self.child.AUTHORIZATION_EPOCH,
                                               'counts': {'http': 7, 'odoo_start': 1, 'target_ro': 6}}))
        self.budget.lock_path.touch(mode=0o600)
        config = self.run / 'odoo.conf'
        save_once(config, {'synthetic_private_configuration': True})
        self.marker = {'database': self.database, 'oid': 12345, 'core': CORE, 'cluster': CLUSTER,
                       'role': 'scratch', 'lc2_role': 'scratch', 'port': 18411,
                       'product_commit': 'a' * 40, 'test_commit': 'b' * 40,
                       'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest()}
        save_once(self.run / 'database.json', self.marker)
        save_once(self.application / 'identity-probe.json', {
            'database': self.database, 'oid': 12345, 'cluster': CLUSTER,
            'user': 'odoo', 'read_only': 'on', 'isolation': 'repeatable read', 'rollback_returned': True})
        exit_file = self.application / 'identity-probe-exit.tsv'
        exit_file.write_bytes(b'CLOSED\t123456789\n')
        exit_file.chmod(0o600)
        self.events = self.run / 'diagnostics/events-101-synthetic-000.jsonl'
        self.events.write_text(json.dumps({'schema_version': '1.0', 'event_id': 'synthetic-event-1',
            'event': 'run.start', 'pid': 101, 'process_seq': 1, 'run_id': 'synthetic-run',
            'ts_utc': '2026-10-17T00:00:00Z', 'monotonic_ns': 1}) + '\n')
        self.events.chmod(0o600)
        self.grant_path = self.application / self.child.GRANT_NAME
        self.environment = {'YDENTAL_RUN_ID': 'synthetic-run', 'YDENTAL_TASK_ID': 'S10-LOG-AND-CLOSEOUT-v2',
                            'YDENTAL_PRODUCT_COMMIT': 'a' * 40, 'YDENTAL_TEST_COMMIT': 'b' * 40,
                            'YDENTAL_CORE_COMMIT': CORE, 'YDENTAL_S10_RUN_DIR': str(self.run),
                            'YDENTAL_LC2_BUDGET_DIR': str(self.execution),
                            self.child.GRANT_ENV: str(self.grant_path)}
        self.grant = self.child.issue_framework_grant(
            self.grant_path, marker=self.marker, environment=self.environment,
            child_pid=101, frozen_files=frozen)
        self.fake_os.getpid = lambda: 101
        self.fake_os.getppid = lambda: 100
        self.scope.enter_context(patch.dict(sys.modules, {'s10_lc2_framework_caller': self.child}))
        self.sent = []
        self.return_value = object()

        def send(*args, **kwargs):
            self.sent.append((args, kwargs))
            self.assertEqual(self.count(), 8, 'send preceded durable cumulative reservation')
            self.assertTrue((self.application / self.child.PENDING_NAME).is_file())
            self.assertTrue((self.application / self.child.RESERVED_NAME).is_file())
            return self.return_value

        self.sender = send
        self.instance = self.make_instance(send)

    def make_instance(self, sender):
        cls = actual_http_class(self.environment, sender)
        instance = cls()
        instance.env = types.SimpleNamespace(cr=types.SimpleNamespace(dbname=self.database))
        instance.http_port = lambda: 18411
        instance._testMethodName = self.child.PURPOSE.split('.', 1)[1]
        return instance

    def count(self):
        return json.loads(self.budget.path.read_text())['counts']['http']

    def update_grant(self, **changes):
        value = json.loads(self.grant_path.read_text())
        value.update(changes)
        self.grant_path.write_text(json.dumps(value))

    def rejected(self, callback=None):
        with self.assertRaises(Exception):
            (callback or (lambda: self.instance.url_open(self.child.RPC_PATH)))()
        self.assertEqual(self.sent, [], 'a refused actual url_open called super')

    def fresh_namespace(self):
        fresh = separate_module('lc2_framework_child_reinitialized', 's10_lc2_framework_caller.py')
        for name in ('ROOT', 'EXEC_ROOT', 'RUN_ROOT', 'LEGACY_EXEC_ROOT', 'os'):
            setattr(fresh, name, getattr(self.child, name))
        self.child = fresh
        sys.modules['s10_lc2_framework_caller'] = fresh

    def test_actual_method_allows_own_context_without_parent_owner_exactly_once(self):
        with patch.object(parent_targets, '_DISPATCH_OWNER', None):
            result = self.instance.url_open(self.child.RPC_PATH, b'payload', headers={'Case': 'synthetic'},
                                            timeout=9, method='POST')
        self.assertIs(result, self.return_value)
        self.assertEqual(self.sent, [((self.child.RPC_PATH, b'payload'), {
            'headers': {'Case': 'synthetic'}, 'timeout': 9, 'method': 'POST', 'allow_redirects': False})])
        self.assertEqual(self.count(), 8)

    def test_actual_method_order_is_check_then_durable_accounting_then_single_send(self):
        import s10_lc2_evidence as evidence
        events = []
        original_observe = self.child.ProcessLogGuard.observe
        original_save = self.child.save_once
        original_budget_save = evidence.save_once
        original_intent = evidence.append_plain

        def observe(guard, *args, **kwargs):
            result = original_observe(guard, *args, **kwargs)
            events.append('check')
            return result

        def save(path, value):
            result = original_save(path, value)
            events.append({self.child.PENDING_NAME: 'pending', self.child.RESERVED_NAME: 'reserved'}[Path(path).name])
            return result

        def budget_save(path, value):
            result = original_budget_save(path, value)
            events.append('budget')
            return result

        def intent(*args, **kwargs):
            result = original_intent(*args, **kwargs)
            events.append('intent')
            return result

        def send(*args, **kwargs):
            events.append('send')
            return self.sender(*args, **kwargs)

        with patch.object(self.child.ProcessLogGuard, 'observe', observe), \
                patch.object(self.child, 'save_once', save), \
                patch.object(evidence, 'save_once', budget_save), \
                patch.object(evidence, 'append_plain', intent):
            self.assertIs(self.make_instance(send).url_open(self.child.RPC_PATH), self.return_value)
        self.assertEqual(events, ['check', 'pending', 'budget', 'intent', 'reserved', 'send'])

    def test_second_context_cannot_reset_count_or_reuse_consumed_grant(self):
        self.instance.url_open(self.child.RPC_PATH)
        self.sent.clear()
        self.fresh_namespace()
        self.rejected()
        self.assertEqual(self.count(), 8)
        self.assertEqual(json.loads(self.budget.path.read_text())['counts']['target_ro'], 6)

    def test_actual_method_missing_grant_never_sends(self):
        del self.environment[self.child.GRANT_ENV]
        self.rejected()
        self.assertEqual(self.count(), 7)

    def test_missing_budget_cannot_be_initialized_by_child(self):
        self.budget.path.unlink()
        self.rejected()
        self.assertFalse(self.budget.path.exists())

    def test_identity_pid_mismatch_never_sends(self):
        self.fake_os.getpid = lambda: 102
        self.rejected()
        self.assertEqual(self.count(), 7)

    def test_parent_pid_mismatch_never_sends(self):
        self.fake_os.getppid = lambda: 99
        self.rejected()

    def test_actual_framework_database_mismatch_never_sends(self):
        self.instance.env.cr.dbname = 'unapproved_database'
        self.rejected()

    def test_actual_framework_port_mismatch_never_sends(self):
        self.instance.http_port = lambda: 18412
        self.rejected()

    def test_candidate_mismatch_never_sends(self):
        self.environment['YDENTAL_TEST_COMMIT'] = 'c' * 40
        self.rejected()
        self.assertEqual(self.count(), 7)

    def test_frozen_source_mismatch_never_sends(self):
        (self.source / 'scripts/s10_lc2_targets.py').write_text('changed candidate')
        self.rejected()

    def test_missing_candidate_never_sends(self):
        del self.environment['YDENTAL_PRODUCT_COMMIT']
        self.rejected()

    def test_marker_mismatch_never_sends(self):
        (self.run / 'database.json').write_text('{}')
        self.rejected()

    def test_nonprivate_grant_never_sends(self):
        self.grant_path.chmod(0o644)
        self.rejected()

    def test_grant_symlink_never_sends(self):
        saved = self.application / 'synthetic-saved-grant.json'
        self.grant_path.rename(saved)
        self.grant_path.symlink_to(saved)
        self.rejected()

    def test_configuration_mismatch_never_sends(self):
        (self.run / 'odoo.conf').write_text('changed configuration')
        self.rejected()

    def test_purpose_mismatch_never_sends(self):
        self.instance._testMethodName = 'unapproved_method'
        self.rejected()

    def test_existing_shared_stop_never_sends_and_reimport_stays_stopped(self):
        save_once(self.execution / 'HARD-STOP.json', {'reason': 'FIRST_SYNTHETIC_STOP'})
        self.rejected()
        self.fresh_namespace()
        self.rejected()
        self.assertEqual(json.loads((self.execution / 'HARD-STOP.json').read_text())['reason'],
                         'FIRST_SYNTHETIC_STOP')
        self.assertEqual(self.count(), 7)

    def test_diagnostic_failure_never_sends(self):
        (self.run / 'diagnostics/diagnostics-failed-101.txt').write_text('synthetic failure')
        self.rejected()

    def test_missing_own_process_log_never_sends(self):
        self.events.unlink()
        self.rejected()

    def test_own_process_renderer_fault_never_sends(self):
        with self.events.open('a') as stream:
            stream.write(json.dumps({'schema_version': '1.0', 'event_id': 'synthetic-event-2',
                'event': 'renderer.exit', 'pid': 101, 'process_seq': 2, 'run_id': 'synthetic-run',
                'ts_utc': '2026-10-17T00:00:01Z', 'monotonic_ns': 2, 'renderer_signal': 11}) + '\n')
        self.rejected()
        self.assertEqual(self.count(), 7)
        failure = json.loads((self.execution / self.child.FAILURE_NAME).read_text())
        self.assertEqual(failure['event_id'], 'synthetic-event-2')

    def test_own_process_truncated_log_never_sends(self):
        with self.events.open('ab') as stream:
            stream.write(b'{"truncated":')
        self.rejected()
        self.assertEqual(self.count(), 7)

    def test_http_budget_exhaustion_never_sends(self):
        value = json.loads(self.budget.path.read_text())
        value['counts']['http'] = 600
        self.budget.path.write_text(json.dumps(value))
        self.rejected()
        self.assertEqual(self.count(), 600)

    def test_expired_caller_grant_never_sends(self):
        self.update_grant(deadline_epoch=self.child.AUTHORIZATION_EPOCH + 999)
        self.rejected()

    def test_unapproved_endpoint_never_sends(self):
        self.rejected(lambda: self.instance.url_open('/web/unapproved'))

    def test_auto_redirect_refused_before_sending(self):
        self.rejected(lambda: self.instance.url_open(self.child.RPC_PATH, allow_redirects=True))
        self.assertEqual(self.count(), 7)

    def test_send_exception_propagates_same_instance_no_retry_one_count(self):
        original = ValueError('synthetic send failure')

        def send(*args, **kwargs):
            self.sent.append((args, kwargs))
            raise original

        instance = self.make_instance(send)
        with self.assertRaises(ValueError) as caught:
            instance.url_open(self.child.RPC_PATH)
        self.assertIs(caught.exception, original)
        self.assertEqual(len(self.sent), 1)
        self.assertEqual(self.count(), 8)
        self.sent.clear()
        self.fresh_namespace()
        self.rejected(lambda: instance.url_open(self.child.RPC_PATH))
        self.assertEqual(self.count(), 8)

    def test_pending_persistence_failure_never_sends_or_counts(self):
        original = self.child.save_once

        def fail_pending(path, value):
            if Path(path).name == self.child.PENDING_NAME:
                raise OSError('synthetic pending save failure')
            return original(path, value)

        with patch.object(self.child, 'save_once', side_effect=fail_pending):
            self.rejected()
        self.assertEqual(self.count(), 7)
        self.fresh_namespace()
        self.rejected()

    def test_budget_save_failure_pending_latch_survives_fresh_namespace(self):
        import s10_lc2_evidence as evidence
        original = evidence.save_once

        def fail_budget(path, value):
            if Path(path).suffix == '.next':
                raise OSError('synthetic budget save failure')
            return original(path, value)

        with patch.object(evidence, 'save_once', side_effect=fail_budget):
            self.rejected()
        self.assertEqual(self.count(), 7)
        self.assertTrue((self.application / self.child.PENDING_NAME).is_file())
        self.fresh_namespace()
        self.rejected()

    def test_budget_intent_save_failure_keeps_cumulative_debit_never_sends(self):
        with patch('s10_lc2_evidence.append_plain', side_effect=OSError('synthetic intent failure')):
            self.rejected()
        self.assertEqual(self.count(), 8)
        self.fresh_namespace()
        self.rejected()
        self.assertEqual(self.count(), 8)

    def test_reserved_receipt_save_failure_never_sends_or_refunds_budget(self):
        original = self.child.save_once

        def fail_reserved(path, value):
            if Path(path).name == self.child.RESERVED_NAME:
                raise OSError('synthetic reserved save failure')
            return original(path, value)

        with patch.object(self.child, 'save_once', side_effect=fail_reserved):
            self.rejected()
        self.assertEqual(self.count(), 8)
        self.fresh_namespace()
        self.rejected()
        self.assertEqual(self.count(), 8)

    def test_stop_save_failure_still_persists_first_failure_for_parent_and_new_child(self):
        original = self.child.save_once

        def fail_stop(path, value):
            if Path(path).name == 'HARD-STOP.json':
                raise OSError('synthetic STOP save failure')
            return original(path, value)

        del self.environment[self.child.GRANT_ENV]
        with patch.object(self.child, 'save_once', side_effect=fail_stop):
            self.rejected()
        first = (self.execution / self.child.FAILURE_NAME).read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK_CALLER_FAILURE_PERSISTED'):
            self.child.check_framework_failure(self.application)
        self.fresh_namespace()
        self.rejected()
        self.assertEqual((self.execution / self.child.FAILURE_NAME).read_bytes(), first)

    def test_parent_detects_dangling_pending_with_no_shared_failure_record(self):
        save_once(self.application / self.child.PENDING_NAME, {'synthetic_pending': True})
        with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK_RESERVATION_INCOMPLETE'):
            self.child.check_framework_failure(self.application)

    def test_parent_completed_reservation_is_not_a_failure(self):
        self.instance.url_open(self.child.RPC_PATH)
        self.child.check_framework_failure(self.application)

    def test_budget_open_existing_mode_does_not_reset_original_epoch_or_counts(self):
        before = self.budget.path.read_bytes()
        reopened = Budget(self.execution, create=False)
        self.assertEqual(reopened.path.read_bytes(), before)
        with self.assertRaisesRegex(ValueError, 'INVALID_BUDGET_OPEN_MODE'):
            Budget(self.execution, create=False, started_epoch=time.time())
        self.assertEqual(reopened.path.read_bytes(), before)

    def test_budget_open_existing_race_does_not_recreate_missing_ledger(self):
        original = Path.exists
        calls = []

        def exists(path):
            if path == self.budget.path:
                calls.append(path)
                return False
            return original(path)

        with patch.object(Path, 'exists', exists), patch('s10_lc2_evidence.save_once') as writer:
            # A disappearance after is_file() cannot enter the initializer.
            try:
                Budget(self.execution, create=False)
            except RuntimeError:
                pass
        writer.assert_not_called()

    def test_parent_wait_on_already_exited_child_checks_shared_failure(self):
        from s10_lc2_launch import OwnedApplication
        import s10_lc2_launch as launch
        save_once(self.execution / self.child.FAILURE_NAME, {'reason': 'FRAMEWORK_SYNTHETIC_FIRST'})
        app = object.__new__(OwnedApplication)
        app.directory, app.run = self.application, self.run
        app.action = 'scratch-tests'
        app.framework_grant_path = self.grant_path
        app.budget = MagicMock()
        app.started = time.monotonic()
        app.streams = []
        app.process = types.SimpleNamespace(pid=101, returncode=0, poll=lambda: 0)
        app.event_guard = None
        app.observe_events = MagicMock(return_value=True)
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
                app.wait(1200)
        app.budget.consume.assert_not_called()

    def completed_framework_application(self, returncode):
        from s10_lc2_launch import OwnedApplication
        from s10_lc2_process_guard import ProcessLogGuard
        with self.events.open('a') as stream:
            stream.write(json.dumps({'schema_version': '1.0', 'event_id': 'synthetic-event-2',
                'event': 'run.end', 'pid': 101, 'process_seq': 2, 'run_id': 'synthetic-run',
                'ts_utc': '2026-10-17T00:00:01Z', 'monotonic_ns': 2}) + '\n')
        raw = self.events.read_bytes()
        save_once(Path(str(self.events) + '.seal'), {'file': self.events.name, 'bytes': len(raw),
                   'sha256': hashlib.sha256(raw).hexdigest(), 'segment': 0})
        app = object.__new__(OwnedApplication)
        app.directory, app.run = self.application, self.run
        app.action = 'scratch-tests'
        app.framework_grant_path = self.grant_path
        app.budget = MagicMock()
        app.started = time.monotonic()
        app.streams = []
        app.process = types.SimpleNamespace(pid=101, returncode=returncode, poll=lambda: returncode)
        app.event_guard = ProcessLogGuard(self.run / 'diagnostics', 101, 'synthetic-run')
        return app

    def test_scratch_native_negative_exit_keeps_native_fact_before_missing_grant_consumption(self):
        import s10_lc2_launch as launch
        app = self.completed_framework_application(-11)
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(launch, 'stop') as stop, \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            self.assertEqual(app.wait(1200), -11)
            self.assertEqual(parent_targets._DISPATCH_FAILURE['reason'], 'NATIVE_PROCESS_EXIT')
            self.assertTrue(any(call.kwargs.get('signal') == 11 for call in stop.call_args_list))
        self.assertIsNone(app.event_guard.state.failure)

    def test_scratch_zero_exit_missing_grant_consumption_still_rejects(self):
        import s10_lc2_launch as launch
        app = self.completed_framework_application(0)
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
                app.wait(1200)

    def test_direct_close_native_exit_precedes_unconsumed_framework_grant(self):
        import s10_lc2_launch as launch
        app = self.completed_framework_application(-11)
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(launch, 'stop'), \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            app.close()
            self.assertEqual(parent_targets._DISPATCH_FAILURE['reason'], 'NATIVE_PROCESS_EXIT')

    def test_direct_close_producer_first_reference_precedes_framework_uncertainty(self):
        import s10_lc2_launch as launch
        from s10_lc2_process_guard import ObservationBlocked
        app = self.completed_framework_application(0)
        rows = [json.loads(line) for line in self.events.read_text().splitlines()]
        rows[1].update(event='renderer.exit', renderer_signal=11, root_event_id='synthetic-producer-root')
        self.events.write_bytes(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
        raw = self.events.read_bytes()
        Path(str(self.events) + '.seal').write_text(json.dumps({'file': self.events.name, 'bytes': len(raw),
            'sha256': hashlib.sha256(raw).hexdigest(), 'segment': 0}))
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(launch, 'stop'), \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            with self.assertRaises(ObservationBlocked):
                app.close()
            self.assertEqual(parent_targets._DISPATCH_FAILURE['event_id'], 'synthetic-event-2')
            self.assertEqual(parent_targets._DISPATCH_FAILURE['root_event_id'], 'synthetic-producer-root')

    def test_parent_close_observes_failure_even_with_zero_return_code(self):
        from s10_lc2_launch import OwnedApplication
        import s10_lc2_launch as launch
        save_once(self.execution / self.child.FAILURE_NAME, {'reason': 'FRAMEWORK_SYNTHETIC_FIRST'})
        app = object.__new__(OwnedApplication)
        app.directory, app.run = self.application, self.run
        app.action = 'scratch-tests'
        app.framework_grant_path = self.grant_path
        app.process = types.SimpleNamespace(pid=101, returncode=0, poll=lambda: 0)
        app.event_guard = None
        app.streams = []
        with patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                patch.object(parent_targets, '_DISPATCH_OWNER', None):
            with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
                app.close()

    def test_parent_terminal_missing_reservation_is_unknown_not_success(self):
        with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
            self.child.check_framework_failure(self.application, final=True)

    def test_parent_terminal_deleted_grant_cannot_erase_required_framework_context(self):
        self.grant_path.unlink()
        with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
            self.child.check_framework_failure(self.application, final=True, grant_required=True)

    def test_main_terminal_without_framework_grant_remains_normal(self):
        directory = self.execution / 'application-main-service-abcdef12'
        directory.mkdir(mode=0o700)
        self.child.check_framework_failure(directory, final=True, grant_required=False)

    def test_persisted_failure_blocks_new_parent_candidate_launch_and_start_before_tools(self):
        import s10_lc2_launch as launch
        save_once(self.execution / self.child.FAILURE_NAME, {
            'reason': 'FRAMEWORK_SYNTHETIC_FIRST', 'event_id': 'synthetic-first', 'root_event_id': 'synthetic-root'})
        kwargs = {'approval': 'not-opened', 'product_commit': 'a' * 40,
                  'test_commit': 'b' * 40, 'action': 'scratch-tests'}
        app = object.__new__(launch.OwnedApplication)
        for callback in (lambda: launch.candidate_marker({}, **kwargs),
                         lambda: launch.launch_guard({}, **kwargs), lambda: app.start([])):
            with patch.object(parent_targets, '_DISPATCH_FAILURE', None), \
                    patch.object(launch, 'STOP', self.execution / 'HARD-STOP.json'), \
                    patch.object(launch, 'runtime_gate') as gate, \
                    patch.object(launch.subprocess, 'Popen') as popen:
                with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK_SYNTHETIC_FIRST'):
                    callback()
                gate.assert_not_called()
                popen.assert_not_called()
                self.assertEqual(parent_targets._DISPATCH_FAILURE['event_id'], 'synthetic-first')
                self.assertEqual(parent_targets._DISPATCH_FAILURE['root_event_id'], 'synthetic-root')

    def test_all_stop_writes_failure_preserves_same_interpreter_latch(self):
        del self.environment[self.child.GRANT_ENV]
        with patch.object(self.child, 'save_once', side_effect=OSError('synthetic all persistence unavailable')):
            self.rejected()
        self.environment[self.child.GRANT_ENV] = str(self.grant_path)
        self.rejected()
        self.assertEqual(self.count(), 7)
        # No cross-process claim: the parent can only mark this unconsumed grant UNKNOWN at terminal check.
        with self.assertRaisesRegex(RuntimeError, 'FRAMEWORK'):
            self.child.check_framework_failure(self.application, final=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
