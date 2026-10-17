"""Meaningful offline LC2 tests. No Odoo, database or business browser is loaded."""
from concurrent.futures import ThreadPoolExecutor
import asyncio
import importlib.util
import hashlib
import json
import os
import logging
from pathlib import Path
import signal
import sys
import tempfile
import unittest
from unittest.mock import patch

from s10_lc2_evidence import ACCIDENT, Budget, CLUSTER, CORE, collect_selection, runtime_gate, save_once, target_guard
from s10_lc2_logging import MAX_LINE, query_timeline, strict_loads, summarize_failure, validate_jsonl
from s10_lc2_supervisor import append_plain, launch, save_primary

ROOT = Path(__file__).resolve().parents[1]
CONNECTION_ARGS = {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}


def record(seq=1, **values):
    return {'schema_version': '1.0', 'event_id': 'event-' + str(seq), 'event': 'run.end',
            'pid': 123, 'process_seq': seq, 'ts_utc': '2026-10-17T00:00:00Z',
            'monotonic_ns': seq, 'run_id': 'synthetic-run', 'case_id': 'synthetic-case', **values}


class ToolCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='s10-lc2-offline-')
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def log(self, raw):
        path = self.directory / ('log-' + str(len(list(self.directory.iterdir()))) + '.jsonl')
        path.write_bytes(raw)
        return validate_jsonl([path])

    def test_valid_query_and_unknown_is_not_commit(self):
        rows = [record(1, event='request.returned'), record(2, event='run.end')]
        result = self.log(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
        self.assertEqual(result['status'], 'VALID')
        self.assertEqual(len(query_timeline(result, case_id='synthetic-case')), 2)
        self.assertEqual(summarize_failure(result)['commit_observation'], 'UNKNOWN')

    def test_bad_lines_cannot_hide_good_or_mark_run_valid(self):
        variants = [b'{"a":1,"a":2}\n', b'{"a":NaN}\n', b'\xff\n', b'{\n', b'{}',
                    b'x' * (MAX_LINE + 1) + b'\n', json.dumps(record(pid=True)).encode() + b'\n']
        for raw in variants:
            with self.subTest(raw=raw[:20]):
                result = self.log(raw + (b'' if not raw.endswith(b'\n') else json.dumps(record()).encode() + b'\n'))
                self.assertEqual(result['status'], 'INVALID')
                self.assertTrue(result['defects'])

    def test_sequence_and_event_replay_detected(self):
        for rows in ([record(1), record(3)], [record(1), record(2, event_id='event-1')]):
            result = self.log(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
            self.assertEqual(result['status'], 'INVALID')

    def test_missing_end_and_empty_never_valid(self):
        self.assertEqual(self.log(b'')['status'], 'INVALID')
        result = self.log(json.dumps(record(event='request.returned')).encode() + b'\n')
        self.assertIn('MISSING_RUN_END', [item['code'] for item in result['defects']])

    def test_primary_secondary_and_checkpoint_independent(self):
        rows = [record(1, event='error', error_class='APPLICATION_ERROR'),
                record(2, event='error', error_class='EVIDENCE_ERROR', root_event_id='event-1'),
                record(3, commit_observation='VERIFIED_COMMITTED', checkpoint_ref='known-before')]
        result = self.log(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
        summary = summarize_failure(result)
        self.assertEqual(summary['first_exception']['record']['event_id'], 'event-1')
        self.assertEqual(summary['secondary'][0]['record']['root_event_id'], 'event-1')
        self.assertEqual(summary['last_verified_checkpoint']['record']['checkpoint_ref'], 'known-before')

    def test_primary_does_not_serialize_exception_secret(self):
        try:
            raise RuntimeError('password=synthetic-secret\nprivate-patient')
        except RuntimeError as error:
            saved = save_primary(self.directory, error, stage='synthetic_failure')
        raw = Path(saved['path']).read_text()
        self.assertIn('RuntimeError', raw)
        self.assertNotIn('synthetic-secret', raw)
        self.assertNotIn('private-patient', raw)

    def test_primary_writer_failure_does_not_replace_original(self):
        error = RuntimeError('first')
        with patch('s10_lc2_supervisor.append_plain', side_effect=OSError('secondary')), patch('os.write') as fallback:
            saved = save_primary(self.directory, error, stage='primary')
        self.assertIsNotNone(saved['event_id'])
        self.assertTrue(fallback.called)

    def test_parent_observes_exit_exception_signal_timeout(self):
        cases = [('normal', 'print("ok")', 2, 0, None),
                 ('error', 'raise ValueError("synthetic failure")', 2, 1, None),
                 ('signal', 'import os,signal; os.kill(os.getpid(), signal.SIGTERM)', 2, -signal.SIGTERM, signal.SIGTERM),
                 ('timeout', 'import time; time.sleep(5)', .05, -signal.SIGTERM, signal.SIGTERM)]
        for name, code, timeout, expected, signum in cases:
            with self.subTest(case=name):
                result = launch([sys.executable, '-c', code], self.directory / name, timeout=timeout, attempt=1)
                self.assertEqual(result['returncode'], expected)
                self.assertEqual(result['signal'], signum)
                self.assertEqual(result['transaction_outcome'], 'NOT_OBSERVED')
                self.assertIn('parent.end', Path(result['exit_path']).read_text())
                self.assertEqual((self.directory / name / 'stdout.log').stat().st_mode & 0o777, 0o600)

    def test_parent_write_error_terminates_and_reaps_only_its_owned_child(self):
        owned_pid = []

        def failing_child_start(path, fields):
            if fields[0] == 'child.start':
                owned_pid.append(fields[2])
                raise OSError('synthetic child-start persistence failure')
            return append_plain(path, fields)

        with patch('s10_lc2_supervisor.append_plain', side_effect=failing_child_start):
            with self.assertRaisesRegex(OSError, 'synthetic child-start'):
                launch([sys.executable, '-c', 'import time; time.sleep(30)'], self.directory / 'orphan-guard',
                       timeout=60, attempt=1)
        self.assertEqual(len(owned_pid), 1)
        with self.assertRaises(ProcessLookupError):
            os.kill(owned_pid[0], 0)
        text = (self.directory / 'orphan-guard' / 'parent-exit.tsv').read_text()
        self.assertIn('child.cleanup_intent', text)
        self.assertIn('OUTCOME_UNKNOWN', text)
        self.assertIn('parent.end', text)

    def test_budget_counts_before_dispatch_and_exhausts(self):
        budget = Budget(self.directory)
        self.assertEqual(budget.consume('maintenance'), 1)
        with self.assertRaisesRegex(RuntimeError, 'RESOURCE_EXHAUSTED'):
            budget.consume('maintenance')
        self.assertEqual(strict_loads(budget.path.read_bytes())['counts']['maintenance'], 1)

    def test_budget_window_no_refill(self):
        budget = Budget(self.directory, started_epoch=1)
        with self.assertRaisesRegex(RuntimeError, 'RUN_WINDOW_EXHAUSTED'):
            budget.consume('http')

    def test_runtime_gate_cannot_run_on_plan_or_unfrozen_candidate(self):
        path = self.directory / 'approval.json'
        save_once(path, {'message_id': 'YD-S10-LC2-EXEC-20261017-01'})
        with self.assertRaisesRegex(RuntimeError, 'RUNTIME_NOT_DISPATCHED'):
            runtime_gate(path, product_commit='product', test_commit='test')

    def test_target_marker_and_protected_identity(self):
        name = 'ydental_s10_test_20261017120000_1234abcd'
        run = self.directory / name
        run.mkdir()
        config = run / 'odoo.conf'
        config.write_text('[options]\n')
        import hashlib
        save_once(run / 'database.json', {'database': name, 'oid': 1, 'cluster': CLUSTER,
                                        'core': CORE, 'config_sha256': hashlib.sha256(config.read_bytes()).hexdigest()})
        self.assertEqual(target_guard(name, run, allowed_names=[name], config_path=config)['oid'], 1)
        with self.assertRaisesRegex(RuntimeError, 'TARGET_NOT_OWNED'):
            target_guard(ACCIDENT, run, allowed_names=[ACCIDENT], config_path=config)
        config.write_text('[options]\nchanged=True\n')
        with self.assertRaisesRegex(RuntimeError, 'TARGET_MARKER_DRIFT'):
            target_guard(name, run, allowed_names=[name], config_path=config)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params=None):
        self.connection.queries.append((sql, params))
        if 't.tableoid::regclass' in sql:
            self.rows = list(self.connection.rows)

    def fetchone(self):
        return (ACCIDENT, self.connection.oid, CLUSTER, 345, 'on', 'repeatable read', 'odoo', '127.0.0.1', 5432, 'UTC')

    def fetchmany(self, size):
        rows, self.rows = self.rows[:size], self.rows[size:]
        return rows

    def fetchall(self):
        return []


class FakeConnection:
    def __init__(self, oid=2144127, rows=None):
        text = '{"id":1,"state":"confirmed"}'
        self.oid, self.rows = oid, rows or [('ydental_clinical_document', 999, text, hashlib.sha256(text.encode()).hexdigest())]
        self.queries, self.session = [], None
        self.closed, self.rolled_back = False, False

    def set_session(self, **values):
        self.session = values

    def cursor(self, name=None):
        return FakeCursor(self)

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class EvidenceCase(unittest.TestCase):
    setUp = ToolCase.setUp
    def test_ro_closes_before_heavy_validation_and_uses_bounded_selection(self):
        connection = FakeConnection()
        real_loads = strict_loads

        def after_close(raw, **kwargs):
            self.assertTrue(connection.closed)
            return real_loads(raw, **kwargs)

        with patch('s10_lc2_evidence.strict_loads', side_effect=after_close):
            # Budget is a stub to isolate the connection/serializer ordering contract.
            budget = type('BudgetStub', (), {'consume': lambda self, kind: 1})()
            index = collect_selection(lambda **kw: connection, CONNECTION_ARGS, database=ACCIDENT,
                                      expected_oid=2144127, selections=[{'table': 'ydental_clinical_document', 'ids': [1]}],
                                      directory=self.directory / 'capture', budget=budget)
        self.assertTrue(connection.rolled_back)
        self.assertEqual(connection.session, {'readonly': True, 'isolation_level': 'REPEATABLE READ', 'autocommit': False})
        self.assertEqual(index[0]['rows'], 1)
        self.assertTrue(any('ANY(%s)' in sql for sql, args in connection.queries))

    def test_identity_drift_is_preserved_and_closes(self):
        connection = FakeConnection(oid=99)
        with self.assertRaisesRegex(RuntimeError, 'DATABASE_IDENTITY'):
            collect_selection(lambda **kw: connection, CONNECTION_ARGS, database=ACCIDENT, expected_oid=2144127,
                              selections=[{'table': 'ydental_clinical_document'}],
                              directory=self.directory / 'capture', budget=Budget(self.directory / 'budget'))
        self.assertTrue(connection.closed)
        self.assertFalse((self.directory / 'capture' / 'sealed-index.json').exists())

    def test_evidence_bound_invalidates_capture_without_truncation_pass(self):
        text = '{"id":1,"large":"' + 'x' * 500 + '"}'
        connection = FakeConnection(rows=[('ydental_clinical_document', 999, text, hashlib.sha256(text.encode()).hexdigest())])
        with self.assertRaisesRegex(RuntimeError, 'EVIDENCE_BOUND'):
            collect_selection(lambda **kw: connection, CONNECTION_ARGS, database=ACCIDENT, expected_oid=2144127,
                              selections=[{'table': 'ydental_clinical_document'}], max_bytes=30,
                              directory=self.directory / 'capture', budget=Budget(self.directory / 'budget'))
        self.assertTrue(connection.closed)
        self.assertFalse((self.directory / 'capture' / 'sealed-index.json').exists())

    def test_no_connection_for_p021_unapproved_target_or_unsafe_query(self):
        calls = []
        for database, table in [('ydental_s10_test_20261017050000_21b0cafe', 'safe'),
                                ('another_database', 'safe'), (ACCIDENT, 'unsafe;drop')]:
            with self.assertRaises((RuntimeError, ValueError)):
                collect_selection(lambda **kw: calls.append(kw), CONNECTION_ARGS, database=database, expected_oid=1,
                                  selections=[{'table': table}], directory=self.directory / 'capture',
                                  budget=Budget(self.directory / 'budget'))
        self.assertEqual(calls, [])

    def test_server_digest_mismatch_invalidates_after_connection_closed(self):
        connection = FakeConnection(rows=[('ydental_clinical_document', 999, '{"id":1}', '0' * 64)])
        with self.assertRaisesRegex(ValueError, 'SERVER_CLIENT_ROW'):
            collect_selection(lambda **kw: connection, CONNECTION_ARGS, database=ACCIDENT, expected_oid=2144127,
                              selections=[{'table': 'ydental_clinical_document'}],
                              directory=self.directory / 'capture', budget=Budget(self.directory / 'budget'))
        self.assertTrue(connection.closed)
        self.assertFalse((self.directory / 'capture' / 'sealed-index.json').exists())

    def test_storage_ninety_percent_pauses_new_dispatch(self):
        budget = Budget(self.directory)
        (self.directory / 'raw.bin').write_bytes(b'x' * 950)
        with patch('s10_lc2_evidence.RAW_LIMIT', 1000), self.assertRaisesRegex(RuntimeError, '90_PERCENT'):
            budget.consume('http')


class DiagnosticsCase(unittest.TestCase):
    setUp = ToolCase.setUp

    def setUp(self):
        ToolCase.setUp(self)
        logger = logging.getLogger('ydental.events')
        previous_handlers, previous_level, previous_propagate = list(logger.handlers), logger.level, logger.propagate
        logger.handlers = []

        def cleanup():
            for handler in list(logger.handlers):
                handler.close()
            logger.handlers = previous_handlers
            logger.setLevel(previous_level)
            logger.propagate = previous_propagate

        self.addCleanup(cleanup)
        spec = importlib.util.spec_from_file_location('_lc2_offline_diagnostics', ROOT / 'ydental_access/diagnostics.py')
        self.diagnostics = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.diagnostics)

    def test_configuration_once_preserves_framework_factory(self):
        factory = logging.getLogRecordFactory()
        self.assertTrue(self.diagnostics.configure_once(str(self.directory)))
        self.assertTrue(self.diagnostics.configure_once(str(self.directory)))
        handlers = [item for item in logging.getLogger('ydental.events').handlers
                    if isinstance(item, self.diagnostics.PidFileHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertIs(logging.getLogRecordFactory(), factory)

    def test_context_isolated_threads_and_async_tasks_and_reset(self):
        def thread_case(value):
            token = self.diagnostics.bind_context(case_id=value)
            try:
                return self.diagnostics.current_context()['case_id']
            finally:
                self.diagnostics.reset_context(token)

        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(thread_case, ['L02-A', 'L02-B'])), ['L02-A', 'L02-B'])

        async def task(value):
            token = self.diagnostics.bind_context(case_id=value)
            try:
                await asyncio.sleep(0)
                return self.diagnostics.current_context()['case_id']
            finally:
                self.diagnostics.reset_context(token)

        async def main():
            return await asyncio.gather(task('L02-C'), task('L02-D'))

        self.assertEqual(asyncio.run(main()), ['L02-C', 'L02-D'])
        self.assertEqual(self.diagnostics.current_context(), {})

    def test_real_threaded_emit_keeps_file_sequence_and_case_isolation(self):
        self.diagnostics.configure_once(str(self.directory))

        def writer(index):
            token = self.diagnostics.bind_context(run_id='synthetic-thread-run', task_id='S10-LC2',
                                                  case_id='L02-' + str(index), trace_id='trace-' + str(index),
                                                  request_id='request-' + str(index))
            try:
                for number in range(50):
                    self.diagnostics.emit_event('synthetic.thread.event', operation='operation-' + str(index))
            finally:
                self.diagnostics.reset_context(token)

        with ThreadPoolExecutor(max_workers=4) as executor:
            list(executor.map(writer, range(4)))
        token = self.diagnostics.bind_context(run_id='synthetic-thread-run')
        try:
            self.diagnostics.emit_event('run.end')
        finally:
            self.diagnostics.reset_context(token)
        result = validate_jsonl(list(self.directory.glob('events-*.jsonl')))
        self.assertEqual(result['status'], 'VALID', result['defects'])
        self.assertEqual(result['record_count'], 201)
        for item in result['records'][:-1]:
            row = item['record']
            suffix = row['case_id'].split('-')[-1]
            self.assertEqual(row['trace_id'], 'trace-' + suffix)
            self.assertEqual(row['request_id'], 'request-' + suffix)
            self.assertEqual(row['operation'], 'operation-' + suffix)

    def test_no_context_is_explicit_and_strict_validator_compatible(self):
        self.diagnostics.configure_once(str(self.directory))
        self.diagnostics.emit_event('run.end')
        for handler in logging.getLogger('ydental.events').handlers:
            handler.flush()
        result = validate_jsonl(list(self.directory.glob('events-*.jsonl')))
        self.assertEqual(result['status'], 'VALID')
        event = result['records'][0]['record']
        self.assertTrue(event['context_missing'])
        self.assertIsNone(event['actor_id'])
        self.assertEqual(event['commit_observation'], 'NOT_OBSERVED')

    def test_invalid_metadata_does_not_raise_or_capture_secrets(self):
        self.diagnostics.configure_once(str(self.directory))
        token = self.diagnostics.bind_context(case_id='password=synthetic-secret\npatient-private')
        self.diagnostics.update_context(password='synthetic-secret')
        self.diagnostics.emit_event('run.end', payload='patient-private')
        self.diagnostics.reset_context(token)
        self.assertTrue(self.diagnostics.diagnostics_failed())
        for path in self.directory.iterdir():
            if path.is_file():
                self.assertNotIn(b'synthetic-secret', path.read_bytes())
                self.assertNotIn(b'patient-private', path.read_bytes())

    def test_first_error_survives_json_serializer_failure(self):
        self.diagnostics.configure_once(str(self.directory))
        token = self.diagnostics.bind_context(run_id='synthetic-run', case_id='L04',
                                             trace_id='synthetic-trace', request_id='synthetic-request')
        try:
            try:
                raise NameError('password=synthetic-secret')
            except NameError as error:
                with patch.object(self.diagnostics.json, 'dumps', side_effect=ValueError('serializer-failed')):
                    self.diagnostics.record_exception(error, component='synthetic', stage='business.start')
        finally:
            self.diagnostics.reset_context(token)
        primaries = list(self.directory.glob('exception-*.txt'))
        self.assertTrue(primaries, 'independent primary must precede complex JSON saving')
        text = '\n'.join(path.read_text() for path in primaries)
        self.assertIn('NameError', text)
        self.assertIn('synthetic-trace', text)
        self.assertNotIn('synthetic-secret', text)

    def test_rotation_stops_at_bound_and_preserves_segments(self):
        handler = self.diagnostics.PidFileHandler(self.directory, segment_bytes=128, max_segments=2)
        handler.setFormatter(self.diagnostics.JsonlFormatter())
        small = logging.LogRecord('ydental.events', logging.INFO, '', 1, '', (), None)
        small.ydental_event = {'schema_version': '1.0', 'event': 'synthetic', 'padding': 'x' * 30}
        handler.handle(small)
        handler.handle(small)
        handler.handle(small)
        handler.close()
        self.assertEqual(len(list(self.directory.glob('events-*.jsonl'))), 2)
        self.assertTrue(self.diagnostics.diagnostics_failed())
        self.assertTrue(all(path.stat().st_size <= 128 for path in self.directory.glob('events-*.jsonl')))


if __name__ == '__main__':
    unittest.main(verbosity=2)
