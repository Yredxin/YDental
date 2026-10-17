"""Synthetic events and mocked processes only; no app, socket or child process."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from s10_lc2_process_guard import ObservationBlocked, ProcessEvents, ProcessLogGuard
from s10_lc2_launch import OwnedApplication
from s10_lc2_launch import candidate_marker, launch_guard
from s10_lc2_targets import (PackageBudget, bind_dispatch_owner, release_dispatch_owner,
                            require_dispatch_unfrozen)
import s10_lc2_targets as targets
from s10_lc2_browser import BrowserBoundaryError, BrowserSession, driver_environment


def event(seq, name='operation.rejected', **extra):
    return {'schema_version': '1.0', 'event_id': 'event-%s' % seq,
            'event': name, 'pid': 123, 'process_seq': seq, 'run_id': 'synthetic-run',
            'ts_utc': '2026-10-17T00:00:00Z', 'monotonic_ns': seq, **extra}


class FakeProcess:
    pid = 123
    returncode = None

    def poll(self):
        return self.returncode

    def terminate(self):
        self.returncode = -15

    def wait(self, timeout):
        return self.returncode


class GuardCase(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix='lc2-events-mock-')
        self.addCleanup(directory.cleanup)
        self.directory = Path(directory.name)
        self.logs = self.directory / 'diagnostics'
        self.logs.mkdir()
        for name, value in [('_DISPATCH_OWNER', None), ('_DISPATCH_FAILURE', None)]:
            item = patch.object(targets, name, value)
            item.start()
            self.addCleanup(item.stop)
        stop = patch('s10_lc2_launch.STOP', self.directory / 'synthetic-STOP.json')
        stop.start()
        self.addCleanup(stop.stop)

    def write(self, rows, segment=0, *, seal=False):
        path = self.logs / ('events-123-synthetic-%03d.jsonl' % segment)
        path.write_bytes(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
        path.chmod(0o600)
        if seal:
            raw = path.read_bytes()
            Path(str(path) + '.seal').write_text(json.dumps({
                'file': path.name, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
                'segment': segment}))
        return path

    def application(self, code=None):
        app = object.__new__(OwnedApplication)
        app.process = FakeProcess()
        app.process.returncode = code
        app.run = self.directory
        app.directory = self.directory
        app.budget = MagicMock()
        app.started = time.monotonic()
        app.streams = []
        app.event_guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
        return app

    def test_normal_refusal_and_no_renderer_events_are_not_native_failure(self):
        self.write([event(1, 'run.start'), event(2, error_class='BUSINESS_REJECTION',
                    error_code='ACCESS_DENIED', outcome='denied'), event(3, 'run.end')], seal=True)
        guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
        self.assertTrue(guard.observe(final=True))
        self.assertIsNone(guard.state.failure)

    def test_negative_signal_first_event_is_latched_not_replaced_by_secondary(self):
        for signal in (4, 6, 7, 8, 9, 11, 15):
            with self.subTest(signal=signal):
                state = ProcessEvents(123, 'synthetic-run')
                state.consume(event(1, 'run.start'))
                primary = event(2, 'renderer.exit', renderer_signal=signal)
                with self.assertRaises(ObservationBlocked):
                    state.consume(primary)
                first = dict(state.failure)
                with self.assertRaises(ObservationBlocked):
                    state.consume(event(3, 'renderer.cleanup_failed', outcome='REAP_FAILED'))
                self.assertEqual(state.failure, first)
                self.assertEqual(first['event_id'], primary['event_id'])

    def test_reap_failed_unknown_and_positive_failure_all_block_without_native_claim(self):
        for fields in ({'outcome': 'REAP_FAILED', 'root_event_id': 'original-primary'},
                       {'event': 'renderer.error', 'outcome': 'UNKNOWN'},
                       {'event': 'renderer.exit', 'outcome': 'UNKNOWN'},
                       {'event': 'renderer.exit', 'renderer_exit_code': 1}):
            state = ProcessEvents(123, 'synthetic-run')
            state.consume(event(1, 'run.start'))
            row = event(2, 'renderer.cleanup_failed') | fields
            with self.assertRaises(ObservationBlocked):
                state.consume(row)
            self.assertNotIn('NATIVE', state.failure['reason'])
            self.assertEqual(state.failure['root_event_id'], fields.get('root_event_id'))

    def test_run_pid_sequence_replay_and_renderer_type_are_checked(self):
        variants = [{'pid': 124}, {'run_id': 'other-run'}, {'process_seq': 9},
                    {'event_id': 'event-1'}, {'renderer_signal': True},
                    {'renderer_signal': -11}, {'outcome': []}]
        for values in variants:
            state = ProcessEvents(123, 'synthetic-run')
            state.consume(event(1, 'run.start'))
            with self.assertRaises(ObservationBlocked):
                state.consume(event(2) | values)

    def test_missing_log_only_has_bounded_startup_exception_not_dispatch_permission(self):
        guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
        self.assertFalse(guard.observe(allow_starting=True))
        with self.assertRaisesRegex(ObservationBlocked, 'MISSING'):
            guard.observe()

    def test_incremental_rotation_and_final_seals(self):
        first = self.write([event(1, 'run.start')], seal=True)
        guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
        self.assertTrue(guard.observe())
        self.write([event(2), event(3, 'run.end')], segment=1, seal=True)
        self.assertTrue(guard.observe(final=True))
        self.assertEqual(guard.state.sequence, 3)
        self.assertEqual(guard.files[first.name][1], first.stat().st_size)

    def test_live_partial_and_terminal_truncated_json_fail_as_evidence(self):
        for final in (False, True):
            guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
            path = self.write([event(1, 'run.start'), event(2)])
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaisesRegex(ObservationBlocked, 'PARTIAL'):
                guard.observe(final=final)
            self.assertNotIn('NATIVE', guard.state.failure['reason'])

    def test_removed_shrunk_or_replaced_file_is_not_silent_success(self):
        for mode in ('removed', 'shrunk', 'replaced'):
            path = self.write([event(1, 'run.start')])
            guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
            guard.observe()
            if mode == 'removed':
                path.unlink()
            elif mode == 'shrunk':
                path.write_bytes(b'')
            else:
                new = self.logs / 'replacement'
                new.write_bytes(path.read_bytes())
                new.replace(path)
            with self.assertRaises(ObservationBlocked):
                guard.observe()

    def test_segment_gap_oversize_line_and_invalid_json_are_bounded_failures(self):
        path = self.write([event(1, 'run.start')])
        path.write_bytes(b'x' * (16384 + 1))
        with self.assertRaisesRegex(ObservationBlocked, 'PARTIAL_OR_OVERSIZE'):
            ProcessLogGuard(self.logs, 123, 'synthetic-run').observe()
        path.write_bytes(b'{"schema_version":NaN}\n')
        with self.assertRaisesRegex(ObservationBlocked, 'JSON_INVALID'):
            ProcessLogGuard(self.logs, 123, 'synthetic-run').observe()
        path.unlink()
        self.write([event(1, 'run.start')], segment=1)
        with self.assertRaisesRegex(ObservationBlocked, 'ORDER_INVALID'):
            ProcessLogGuard(self.logs, 123, 'synthetic-run').observe()

    def test_terminal_missing_end_missing_seal_or_same_length_edit_is_unknown(self):
        for mode in ('end', 'seal', 'same-length-edit'):
            rows = [event(1, 'run.start'), event(2, 'run.end')]
            if mode == 'end':
                rows.pop()
            path = self.write(rows, seal=True)
            guard = ProcessLogGuard(self.logs, 123, 'synthetic-run')
            guard.observe()
            if mode == 'seal':
                Path(str(path) + '.seal').unlink()
            elif mode == 'same-length-edit':
                path.write_bytes(path.read_bytes().replace(b'00:00:00Z', b'00:00:01Z'))
            with self.assertRaises(ObservationBlocked):
                guard.observe(final=True)
            self.assertNotIn('NATIVE', guard.state.failure['reason'])

    def test_service_check_blocks_followup_budget_before_request_dispatch(self):
        self.write([event(1, 'run.start'), event(2, 'renderer.exit', renderer_signal=11)])
        app = self.application()
        bind_dispatch_owner(app)
        with patch('s10_lc2_evidence.Budget.consume') as dispatch:
            with self.assertRaises(ObservationBlocked):
                PackageBudget(self.directory).consume('http')
            dispatch.assert_not_called()

    def test_wait_observes_running_renderer_fault_and_reaps_only_fake_process(self):
        self.write([event(1, 'run.start'), event(2, 'renderer.cleanup_failed', outcome='REAP_FAILED')])
        app = self.application()
        with patch('s10_lc2_launch.keep_primary', return_value={'event_id': 'kept-primary'}):
            with self.assertRaisesRegex(ObservationBlocked, 'UNCONFIRMED'):
                app.wait(10)
        self.assertEqual(app.process.returncode, -15)
        self.assertEqual(app.event_guard.state.failure['event_id'], 'event-2')

    def test_wait_checks_exit_tail_even_when_process_was_already_done(self):
        self.write([event(1, 'run.start')])
        app = self.application(code=0)
        with self.assertRaises(ObservationBlocked):
            app.wait(10)
        self.assertEqual(app.event_guard.state.failure['reason'], 'DIAGNOSTIC_SEAL_MISSING_OR_INVALID')

    def test_normal_completed_wait_consumes_end_and_releases_owner(self):
        self.write([event(1, 'run.start'), event(2, 'run.end')], seal=True)
        app = self.application(code=0)
        bind_dispatch_owner(app)
        self.assertEqual(app.wait(10), 0)
        self.assertIsNone(targets._DISPATCH_OWNER)
        self.assertIsNone(targets._DISPATCH_FAILURE)

    def test_actual_parent_negative_exit_is_preserved_even_when_logs_are_incomplete(self):
        for complete in (False, True):
            with patch.object(targets, '_DISPATCH_FAILURE', None):
                rows = [event(1, 'run.start')]
                if complete:
                    rows.append(event(2, 'run.end'))
                self.write(rows, seal=True)
                app = self.application(code=-11)
                with patch('s10_lc2_launch.stop') as stop:
                    if complete:
                        self.assertEqual(app.wait(10), -11)
                    else:
                        with self.assertRaises(ObservationBlocked):
                            app.wait(10)
                    self.assertTrue(any(call.kwargs.get('signal') == 11 for call in stop.call_args_list))
                expected = 'NATIVE_PROCESS_EXIT' if complete else 'DIAGNOSTIC_END_MISSING'
                self.assertEqual(targets._DISPATCH_FAILURE['reason'], expected)

    def test_exited_service_checks_terminal_end_not_just_poll(self):
        self.write([event(1, 'run.start')], seal=True)
        with self.assertRaisesRegex(ObservationBlocked, 'END_MISSING'):
            self.application(code=0).check()

    def test_failed_diagnostic_marker_latches_without_reclassifying_as_native(self):
        self.write([event(1, 'run.start')])
        (self.logs / 'diagnostics-failed-synthetic.txt').write_text('synthetic failure')
        with self.assertRaisesRegex(ObservationBlocked, 'CHAIN_UNAVAILABLE'):
            self.application().check()
        self.assertEqual(targets._DISPATCH_FAILURE['reason'], 'DIAGNOSTIC_CHAIN_UNAVAILABLE')

    def test_actual_native_observer_events_feed_the_same_dispatch_state_machine(self):
        from s10_lc2_test_renderer import observer_fixture
        for code in (0, 1, -11, None, True):
            fixture = observer_fixture(code=code)
            returned = fixture.report._run_pdf_engine_without_processing(
                'wkhtmltopdf', ['synthetic-body'], 'synthetic-report-ref', landscape=False)
            self.assertIs(returned, fixture.native_result)
            state = ProcessEvents(123, 'synthetic-run')
            state.consume(event(1, 'run.start'))
            row = event(2) | fixture.events[-1]
            if type(code) is int and code == 0:
                state.consume(row)
                self.assertIsNone(state.failure)
            else:
                with self.assertRaises(ObservationBlocked):
                    state.consume(row)
                self.assertEqual(state.failure['event_id'], row['event_id'])

    def test_native_observer_exception_keeps_primary_and_forbids_followup(self):
        from s10_lc2_test_renderer import observer_fixture
        original = OSError('synthetic renderer error')
        fixture = observer_fixture(exception=original)
        with self.assertRaises(OSError) as caught:
            fixture.report._run_pdf_engine_without_processing('wkhtmltopdf', [], 'synthetic-ref')
        self.assertIs(caught.exception, original)
        state = ProcessEvents(123, 'synthetic-run')
        state.consume(event(1, 'run.start'))
        with self.assertRaises(ObservationBlocked):
            state.consume(event(2) | fixture.events[-1])
        self.assertEqual(state.failure['root_event_id'], 'synthetic-primary')

    def test_stop_writer_failure_cannot_unfreeze_on_close_or_new_application(self):
        self.write([event(1, 'run.start'), event(2, 'renderer.exit', renderer_signal=11)])
        app = self.application()
        bind_dispatch_owner(app)
        with patch('s10_lc2_launch.stop', side_effect=OSError('synthetic save failure')), \
                patch('s10_lc2_launch.keep_primary', return_value={'event_id': 'secondary'}) as keep:
            with self.assertRaises(ObservationBlocked):
                app.check()
            first = dict(targets._DISPATCH_FAILURE)
            app.close(primary={'event_id': 'original-primary'})
        self.assertIsNone(targets._DISPATCH_OWNER)
        self.assertEqual(targets._DISPATCH_FAILURE, first)
        self.assertTrue(any(c.kwargs.get('root_event_id') == 'event-2' for c in keep.call_args_list))
        with self.assertRaisesRegex(RuntimeError, 'FROZEN'):
            bind_dispatch_owner(object())
        with self.assertRaisesRegex(RuntimeError, 'FROZEN'):
            PackageBudget(self.directory).consume('http')
        with self.assertRaisesRegex(RuntimeError, 'FROZEN'):
            require_dispatch_unfrozen()
        with patch('s10_lc2_launch.runtime_gate') as gate:
            for entry in (candidate_marker, launch_guard):
                with self.assertRaisesRegex(RuntimeError, 'FROZEN'):
                    entry({}, approval='synthetic', product_commit='p', test_commit='t', action='main-service')
            gate.assert_not_called()


class DriverEnvironmentCase(unittest.IsolatedAsyncioTestCase):
    def test_whitelist_is_a_copy_and_does_not_modify_input_or_global_environment(self):
        before = dict(os.environ)
        ambient = {'PATH': '/synthetic/bin', 'LANG': 'zh_CN.UTF-8', 'HOME': '/synthetic/private'}
        clean = driver_environment(ambient)
        self.assertEqual(clean, ambient)
        self.assertIsNot(clean, ambient)
        clean['LANG'] = 'en_US.UTF-8'
        self.assertEqual(ambient['LANG'], 'zh_CN.UTF-8')
        self.assertEqual(dict(os.environ), before)

    async def test_debug_preload_proxy_and_unknown_env_are_rejected_before_factory(self):
        for key in ('DEBUG', 'PWDEBUG', 'DEBUG_FILE', 'NODE_OPTIONS', 'LD_PRELOAD',
                    'MOZ_DISABLE_CONTENT_SANDBOX', 'HTTPS_PROXY', 'UNREVIEWED_SETTING'):
            with tempfile.TemporaryDirectory() as directory:
                factory = MagicMock()
                budget = MagicMock()
                db = 'ydental_s10_test_20261017105432_810a7d9c'
                session = BrowserSession('http://127.0.0.1:18410', database=db,
                    owned_targets={db: 'http://127.0.0.1:18410'}, budget=budget,
                    directory=Path(directory) / 'private', playwright_factory=factory)
                ambient = {'PATH': '/synthetic/bin', key: 'synthetic-private-value'}
                with patch.dict(os.environ, ambient, clear=True):
                    before = dict(os.environ)
                    with self.assertRaisesRegex(BrowserBoundaryError, 'ENVIRONMENT_NOT_WHITELISTED'):
                        await session.__aenter__()
                    self.assertEqual(dict(os.environ), before)
                factory.assert_not_called()
                budget.consume.assert_not_called()

    async def test_fake_driver_and_firefox_receive_only_local_whitelisted_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            driver = MagicMock()
            driver.firefox.launch = AsyncMock(return_value=MagicMock())
            factory = MagicMock()
            factory.return_value.start = AsyncMock(return_value=driver)
            db = 'ydental_s10_test_20261017105432_810a7d9c'
            session = BrowserSession('http://127.0.0.1:18410', database=db,
                owned_targets={db: 'http://127.0.0.1:18410'}, budget=MagicMock(),
                directory=Path(directory) / 'private', playwright_factory=factory)
            session._new_context = AsyncMock()
            ambient = {'PATH': '/synthetic/bin', 'LANG': 'zh_CN.UTF-8'}
            with patch.dict(os.environ, ambient, clear=True):
                before = dict(os.environ)
                await session.__aenter__()
                self.assertEqual(dict(os.environ), before)
                self.assertEqual(driver.firefox.launch.call_args.kwargs['env'], ambient)
                self.assertIsNot(driver.firefox.launch.call_args.kwargs['env'], os.environ)
            session._watchdog.cancel()

    def test_browser_phase_does_not_set_global_driver_debugging(self):
        # Inspect only this unrelated driver adapter. Never import/call cases or
        # the stopped account-material check that happens to share that file.
        import ast
        source = Path(__file__).with_name('s10_lc2_cases.py')
        module = ast.parse(source.read_text())
        phase = next(node for node in module.body if isinstance(node, ast.AsyncFunctionDef)
                     and node.name == 'browser_phase')
        self.assertNotIn("os.environ", ast.unparse(phase))


if __name__ == '__main__':
    unittest.main(verbosity=2)
