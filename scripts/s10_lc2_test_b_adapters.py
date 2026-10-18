"""Synthetic files through actual B evidence producers, parsers and consumers.

Every connection/process/request is an explicit in-memory substitute. The native
diagnostic module has no ORM dependency; its real formatter/handler produce the
temporary JSONL and seals, rather than pre-filled server receipts.
"""
import copy
import builtins
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from functools import wraps
import hashlib
import importlib.util
import json
import logging
import os
from pathlib import Path
import re
import select
import stat
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import URLError
import uuid

import s10_lc2_evidence as evidence
import s10_lc2_http as http
from s10_lc2_logging import strict_loads
from s10_lc2_supervisor import append_plain
from s10_lc2_test_b_caller import (
    PureBoundaryCase, ROOT, MAIN, CASES, actual_definitions, literal,
    FakeBudget, FakeOpener, FakeResponse, MemoryFacts,
    SyntheticCursor, SyntheticEnvironment, SyntheticAccessError, FIXTURE, FIXTURE_PROCESS,
)


def write_json(path, value):
    path = Path(path)
    path.write_text(json.dumps(value, sort_keys=True) + '\n')
    path.chmod(0o600)


class SyntheticRows:
    """Only returns explicitly supplied rows; never imports a DB client."""
    def __init__(self, rows):
        self.rows = copy.deepcopy(rows)
        self.connections = []
        self.calls = []

    def connect(self, **arguments):
        self.calls.append(arguments)
        connection = SyntheticConnection(self)
        self.connections.append(connection)
        return connection


class SyntheticConnection:
    def __init__(self, owner):
        self.owner = owner
        self.closed = False
        self.rolled_back = False
        self.options = None

    def set_session(self, **options):
        self.options = options

    def cursor(self, name=None):
        return SyntheticRowCursor(self, name)

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class SyntheticRowCursor:
    def __init__(self, connection, name):
        self.connection, self.name = connection, name
        self.returned = False

    def __enter__(self):
        return self

    def __exit__(self, *ignored):
        return False

    def execute(self, query, parameters=None):
        self.query = query
        self.parameters = parameters

    def fetchone(self):
        if 'current_database()' not in self.query:
            raise AssertionError('UNEXPECTED_SYNTHETIC_IDENTITY_QUERY')
        return (MAIN, 2144129, evidence.CLUSTER, 4242, 'on', 'repeatable read',
                'odoo', '127.0.0.1', 5432, 'UTC')

    def fetchmany(self, size):
        if self.returned:
            return []
        self.returned = True
        if self.name is None or not self.name.startswith('lc2_'):
            raise AssertionError('UNEXPECTED_SYNTHETIC_ROWS_QUERY')
        table = self.name.removeprefix('lc2_')
        rows = []
        for value in self.connection.owner.rows[table]:
            text = json.dumps(value, sort_keys=True, separators=(',', ':'))
            rows.append((table, 999, text, hashlib.sha256(text.encode()).hexdigest()))
        return rows


class ProducerFiles(PureBoundaryCase):
    def setUp(self):
        super().setUp()
        self.binding = {'run_id': 'synthetic-r2-run', 'task_id': 'synthetic-r2-task',
                        'product_commit': 'a' * 40, 'test_commit': 'b' * 40,
                        'core_commit': evidence.CORE,
                        'identity': {'database': MAIN, 'oid': 2144129,
                                     'cluster': evidence.CLUSTER}}
        self.target = self.directory / MAIN
        self.target.mkdir(mode=0o700)
        self.diagnostics = self.target / 'diagnostics'
        self.diagnostics.mkdir(mode=0o700)
        self.config = self.target / 'odoo.conf'
        self.config.write_text('[options]\n; synthetic only\n')
        self.config.chmod(0o600)
        write_json(self.target / 'database.json', {
            **self.binding['identity'], 'core': evidence.CORE,
            'product_commit': self.binding['product_commit'],
            'test_commit': self.binding['test_commit'],
            'config_sha256': hashlib.sha256(self.config.read_bytes()).hexdigest()})
        self.app = self.directory / 'synthetic-app'
        self.app.mkdir(mode=0o700)
        write_json(self.app / 'launch-intent.json', {
            **{key: self.binding[key] for key in ('product_commit', 'test_commit', 'core_commit')},
            **{key: self.binding['identity'][key] for key in ('database', 'oid')},
            'effective_db_system': MAIN})
        write_json(self.app / 'identity-probe.json', {
            **self.binding['identity'], 'read_only': 'on', 'rollback_returned': True})
        (self.app / 'identity-probe-exit.tsv').write_text('CLOSED\t0\n')
        self.started = __import__('time').time_ns()
        self.pid = os.getpid()  # Real test process, never a claimed application PID.
        self.parent = self.app / 'parent-exit.tsv'
        append_plain(self.parent, ['child.start', self.started, self.pid])
        native_path = ROOT / 'ydental_access/diagnostics.py'
        specification = importlib.util.spec_from_file_location('synthetic_native_diagnostics_' + uuid.uuid4().hex,
                                                             native_path)
        self.native = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.native)
        self.native._LOGGER = logging.Logger('synthetic-native-' + uuid.uuid4().hex, logging.INFO)
        self.handler = self.native.PidFileHandler(self.diagnostics)
        self.handler.setFormatter(self.native.JsonlFormatter())
        self.native._LOGGER.addHandler(self.handler)
        self.addCleanup(self.handler.close)
        self.closed = False
        self.native._lifecycle_event('run.start', self.labels(), 'DIAGNOSTIC_READY')
        self.request = SimpleNamespace(env=SimpleNamespace(uid=16, su=False),
                                       httprequest=SimpleNamespace(headers={}))
        self.http_producer = actual_definitions(ROOT / 'ydental_access/controllers/diagnostics.py',
            ['_environment_label', 'observed_http'], os=os, wraps=wraps,
            _LABEL=re.compile(r'[A-Za-z0-9_.:-]{1,96}\Z'), _CASE_IDS={'B-RPC-6'},
            request=self.request, bind_context=self.native.bind_context,
            reset_context=self.native.reset_context, emit_event=self.native.emit_event,
            record_exception=self.native.record_exception)

    def labels(self):
        return {key: self.binding[key] for key in
                ('run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit')}

    def emit_request(self, operation='B-pre-B-RPC-1-write-attempt-1'):
        self.request.httprequest.headers = {'X-YDental-Case-ID': 'B-RPC-6',
            'X-YDental-Operation-Ref': operation, 'X-YDental-Attempt': '1'}
        environment = {'YDENTAL_' + key.upper(): value for key, value in self.labels().items()}
        with patch.dict(os.environ, environment):
            self.http_producer['observed_http']('synthetic.controller')(lambda: None)()

    def finish(self):
        self.native._lifecycle_event('run.end', self.labels(), 'DIAGNOSTIC_CLOSING')
        self.handler.close()
        self.closed = True
        append_plain(self.parent, ['parent.end', time.time_ns(), self.pid,
                                  0, None, 'TRANSACTION_NOT_OBSERVED'])

    def parse(self, final=False):
        return evidence.parse_b_server_events(binding=self.binding,
            app_directory=self.app, target_directory=self.target, pid=self.pid, final=final)

    def collect(self, rows, selections=None, point='before', check_id='B-RPC-1-write', phase='B-pre'):
        source = SyntheticRows(rows)
        budget = SimpleNamespace(profile=None, consume=lambda kind: None)
        selections = selections or [{'table': table, 'columns': evidence._B_PROJECTIONS[table][0].split(),
                                     'row_digest': evidence._B_PROJECTIONS[table][1],
                                     'ids': [value['id'] for value in values]} for table, values in rows.items()]
        reference = evidence.collect_b_source(source.connect,
            {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}, binding=self.binding,
            point=point, check_id=check_id, phase=phase, selections=selections,
            directory=self.directory / ('synthetic-capture-' + uuid.uuid4().hex), budget=budget,
            target_directory=self.target, config_path=self.config)
        self.assertTrue(all(connection.closed and connection.rolled_back for connection in source.connections))
        self.assertTrue(all(connection.options == {'readonly': True,
            'isolation_level': 'REPEATABLE READ', 'autocommit': False} for connection in source.connections))
        return reference, source


class ActualEvidenceSources(ProducerFiles):
    def test_existing_collector_default_full_row_projection_contract(self):
        source = SyntheticRows({'res_users': [{'id': 101, 'active': True, 'company_id': 1}]})
        budget = FakeBudget()
        output = self.directory / 'synthetic-legacy-collector'
        index = evidence.collect_selection(source.connect,
            {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}, database=MAIN,
            expected_oid=2144129, selections=[{'table': 'res_users', 'ids': [101]}],
            directory=output, budget=budget, allowed_target_names=[MAIN],
            target_directory=self.target, config_path=self.config)
        self.assertEqual(index[0]['rows'], 1)
        wrapper = strict_loads((output / 'res_users.rows.jsonl').read_bytes())
        self.assertEqual(strict_loads(wrapper['server_json_text']), source.rows['res_users'][0])
        self.assertEqual(budget.intents, ['target_ro'])
        self.assertTrue(source.connections[0].closed)

    def test_actual_collector_bad_projection_rejected_before_budget_or_connect(self):
        source, budget = SyntheticRows({}), FakeBudget()
        selections = [
            {'table': 'res_users', 'columns': 'id'},
            {'table': 'res_users', 'columns': ['id', 'id']},
            {'table': 'res_users', 'columns': ['id;not_sql']},
            {'table': 'res_users', 'columns': []},
            {'table': 'res_users', 'columns': ['id'], 'null_columns': ['id', 'id']},
            {'table': 'res_users', 'columns': ['id'], 'row_digest': 'true'},
            {'table': 'res_users', 'columns': ['id'], 'equals': {'id': '101'}},
        ]
        for selection in selections:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                evidence.collect_selection(source.connect,
                    {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}, database=MAIN,
                    expected_oid=2144129, selections=[selection], directory=self.directory / 'not-created',
                    budget=budget, allowed_target_names=[MAIN], target_directory=self.target,
                    config_path=self.config)
        self.assertEqual(source.calls, [])
        self.assertEqual(budget.intents, [])
        self.assertFalse((self.directory / 'not-created').exists())

    def test_actual_collector_closed_transaction_then_parser(self):
        reference, connection = self.collect({'res_users': [{'id': 101, 'active': True, 'company_id': 1}]})
        parsed = evidence.read_b_source(reference, binding=self.binding, used=set())
        self.assertEqual(parsed['rows'], {'res_users': [{'id': 101, 'active': True, 'company_id': 1}]})
        self.assertEqual(parsed['point'], 'before')
        self.assertEqual(len(connection.calls), 1)

    def test_missing_corrupt_candidate_and_reused_measurement_refused(self):
        reference, _ = self.collect({'res_users': [{'id': 101, 'active': True, 'company_id': 1}]})
        used = set()
        evidence.read_b_source(reference, binding=self.binding, used=used)
        with self.assertRaisesRegex(ValueError, 'MEASUREMENT_REUSED'):
            evidence.read_b_source(reference, binding=self.binding, used=used)
        for key in ('run_id', 'task_id', 'product_commit', 'test_commit'):
            with self.subTest(key=key):
                wrong = copy.deepcopy(self.binding)
                wrong[key] = 'wrong' if key.endswith('_id') else 'c' * 40
                with self.assertRaisesRegex(ValueError, 'CANDIDATE_OR_TARGET_DRIFT'):
                    evidence.read_b_source(reference, binding=wrong)
        with self.assertRaisesRegex(ValueError, 'B_SOURCE_BINDING_INVALID'):
            evidence.read_b_source(reference, binding=self.binding | {'core_commit': 'c' * 40})
        body = Path(reference['path'])
        raw = body.read_bytes()
        body.write_bytes(raw + b' ')
        with self.assertRaisesRegex(ValueError, 'REFERENCE_DRIFT'):
            evidence.read_b_source(reference, binding=self.binding)
        body.unlink()
        with self.assertRaisesRegex(ValueError, 'FILE_INVALID'):
            evidence.read_b_source(reference, binding=self.binding)

    def test_actual_source_parser_rechecks_server_row_hash_and_transaction_exit(self):
        for failure in ('server_row', 'not_closed'):
            reference, _ = self.collect({'res_users': [{'id': 101, 'active': True, 'company_id': 1}]})
            source = strict_loads(Path(reference['path']).read_bytes())
            directory = Path(reference['path']).parent
            if failure == 'server_row':
                path = directory / 'res_users.rows.jsonl'
                wrapped = strict_loads(path.read_bytes())
                write_json(path, wrapped | {'server_sha256': '0' * 64})
                index = strict_loads((directory / 'sealed-index.json').read_bytes())
                index['files'][0].update(bytes=path.stat().st_size,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                write_json(directory / 'sealed-index.json', index)
            else:
                (directory / 'observer-exit.tsv').write_text('ROLLBACK_RETURNED\t0\n')
            source['files'] = {name: evidence._b_file_ref(directory / name) for name in source['files']}
            write_json(reference['path'], source)
            reference = evidence._b_file_ref(Path(reference['path']))
            with self.subTest(failure=failure), self.assertRaisesRegex(ValueError,
                    'SERVER_ROW_DRIFT' if failure == 'server_row' else 'TRANSACTION_NOT_CLOSED'):
                evidence.read_b_source(reference, binding=self.binding)

    def test_real_native_live_prefix_then_seal_parser_and_consumer(self):
        operation = 'B-pre-B-RPC-1-write-attempt-1'
        self.emit_request(operation)
        live = self.parse()
        raw = strict_loads(next(self.diagnostics.glob('*.jsonl')).read_bytes().splitlines()[1])
        self.assertNotIn('evidence_ref', raw)
        self.assertNotIn('database', raw)
        self.assertFalse(list(self.diagnostics.glob('*.seal')))
        self.assertEqual(len(live['events']), 1)
        intent = {'operation_ref_sha256': hashlib.sha256(('ydental-client-operation:' + operation).encode()).hexdigest(),
                  'attempt': 1}
        response = {'started_utc': raw['ts_utc'], 'ended_utc': raw['ts_utc'], 'dispatch_state': 'RESPONSE_RECEIVED'}
        consumer = actual_definitions(CASES, ['_b_ref', '_b_time', 'correlate_b_server'])
        linked = consumer['correlate_b_server'](intent, response, live['events'])
        self.assertEqual(linked['actor_id'], 16)
        self.assertFalse(linked['su_flag'])
        self.assertTrue(linked['evidence_ref'])
        self.finish()
        final = self.parse(final=True)
        self.assertTrue(evidence.verify_b_log_prefixes([live], final))
        self.assertEqual(len(list(self.diagnostics.glob('*.seal'))), 1)

    def test_ambiguous_real_server_events_not_a_match(self):
        operation = 'B-pre-B-RPC-1-write-attempt-1'
        self.emit_request(operation)
        self.emit_request(operation)
        parsed = self.parse()
        event = parsed['events'][0]
        response = {'started_utc': event['ts_utc'], 'ended_utc': parsed['events'][-1]['ts_utc'],
                    'dispatch_state': 'RESPONSE_RECEIVED'}
        consumer = actual_definitions(CASES, ['_b_ref', '_b_time', 'correlate_b_server'])
        self.assertIsNone(consumer['correlate_b_server']({'attempt': 1,
            'operation_ref_sha256': event['operation_ref']}, response, parsed['events']))

    def test_log_final_requires_closed_parent_seal_and_immutable_live_bytes(self):
        self.emit_request()
        live = self.parse()
        with self.assertRaisesRegex(ValueError, 'OWNED_PID_OR_EXIT_DRIFT'):
            self.parse(final=True)
        self.finish()
        final = self.parse(final=True)
        path = next(self.diagnostics.glob('*.jsonl'))
        raw = path.read_bytes()
        path.write_bytes(raw.replace(b'synthetic.controller', b'synthetic.controlleX'))
        with self.assertRaisesRegex(ValueError, 'LIVE_PREFIX_CHANGED'):
            evidence.verify_b_log_prefixes([live], final)
        with self.assertRaises(Exception):
            self.parse(final=True)

    def test_actual_live_parser_rejects_wrong_run_task_product_test_core_or_launch_target(self):
        self.emit_request()
        path = next(self.diagnostics.glob('*.jsonl'))
        original = path.read_bytes()
        for key in ('run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit'):
            rows = [strict_loads(line) for line in original.splitlines()]
            for row in rows:
                row[key] = 'wrong' if key.endswith('_id') else 'c' * 40
            path.write_bytes(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
            with self.subTest(key=key), self.assertRaises(Exception):
                self.parse()
            path.write_bytes(original)
        launch_path = self.app / 'launch-intent.json'
        launch = strict_loads(launch_path.read_bytes())
        write_json(launch_path, launch | {'oid': 999})
        with self.assertRaisesRegex(ValueError, 'LAUNCH_CANDIDATE_OR_TARGET_DRIFT'):
            self.parse()

    def test_actual_log_old_process_timestamp_and_missing_seal_refused(self):
        self.emit_request()
        path = next(self.diagnostics.glob('*.jsonl'))
        original = path.read_bytes()
        rows = [strict_loads(line) for line in original.splitlines()]
        for row in rows:
            row['ts_utc'] = '2000-01-01T00:00:00+00:00'
        path.write_bytes(b''.join(json.dumps(row).encode() + b'\n' for row in rows))
        with self.assertRaisesRegex(ValueError, 'OLD_PROCESS_OBSERVATION'):
            self.parse()
        path.write_bytes(original)
        self.finish()
        next(self.diagnostics.glob('*.seal')).unlink()
        with self.assertRaises(Exception):
            self.parse(final=True)

    def test_actual_source_safe_projection_blocks_secret_columns_before_connect(self):
        rows = SyntheticRows({})
        for selection in ({'table': 'res_users', 'columns': ['id', 'password'], 'row_digest': False},
                          {'table': 'res_users', 'columns': ['id', 'active', 'company_id'], 'row_digest': True}):
            with self.subTest(selection=selection), self.assertRaisesRegex(ValueError, 'SAFE_PROJECTION'):
                evidence.collect_b_source(rows.connect, {}, binding=self.binding,
                    point='before', check_id='B-RPC-1-write', phase='B-pre', selections=[selection],
                    directory=self.directory / 'forbidden-capture', budget=None,
                    target_directory=self.target, config_path=self.config)
        self.assertEqual(rows.calls, [])


class ActualBAdapters(ProducerFiles):
    def setUp(self):
        super().setUp()
        self.ns = actual_definitions(CASES, ['_b_ref', '_b_sha', '_b_message', 'validate_b_inputs',
            'b_selections', '_b_one', '_b_relations', 'manifest_from_b_source', 'receipt_from_b_source',
            '_b_time', '_b_snapshot_valid', '_b_preserved', 'correlate_b_server', 'main_b', 'Actor',
            '_b_model_complete', '_run_b_only_checks',
            'b_evidence_callbacks', 'b_collect_step'],
            B_TARGET_FIELDS=literal(CASES, 'B_TARGET_FIELDS'), NAMES={'main': MAIN}, OIDS={'main': 2144129},
            read_b_source=evidence.read_b_source, Client=http.Client,
            RequestNotSent=http.RequestNotSent, parse_b_server_events=self.parse_for_callbacks,
            verify_b_log_prefixes=evidence.verify_b_log_prefixes,
            collect_b_source=evidence.collect_b_source, save_once=evidence.save_once)
        self.requested = {'uid': 16, 'store_id': 1, 'patient_id': 1, 'source_id': 101,
                          'payment_id': 102, 'audit_id': 103, 'invoice_id': 1,
                          'line_id': 1, 'native_payment_id': 1}
        self.provider = {'ref': '.local/synthetic/provider-reference-never-read', 'actor_id': 16}
        self.raw_session = {'uid': 16, 'db': MAIN, 'is_admin': False, 'is_system': False,
                        'is_internal_user': True, 'ydental_store_name': 'Synthetic store',
                        'user_context': {'ydental_revision': 2},
                        'user_companies': {'allowed_companies': {'1': {'id': 1}}},
                        'session_token': 'synthetic-irrelevant-not-exported'}
        self.rows = {
            'res_users': [{'id': 16, 'active': True, 'company_id': 1}],
            'res_groups_users_rel': [{'uid': 16, 'gid': 10}],
            'res_groups_implied_rel': [{'gid': 10, 'hid': 11}],
            'ir_model_data': [{'id': index, 'module': module, 'name': name, 'model': 'res.groups', 'res_id': gid}
                for index, (module, name, gid) in enumerate((('base', 'group_user', 11),
                    ('base', 'group_system', 12), ('base', 'group_erp_manager', 13),
                    ('ydental_base', 'ydental_base_group_user', 10)), 1)],
            'ydental_access_store': [{'id': 1, 'active': True, 'company_id': 1, 'name': 'Synthetic store'}],
            'ydental_access_membership': [{'id': 1, 'active': True, 'ydental_user_id': 16,
                'ydental_store_id': 1, 'ydental_employee_id': 11}],
            'hr_employee': [{'id': 11, 'active': True, 'user_id': 16, 'company_id': 1}],
            'ydental_access_session': [{'ydental_user_id': 16, 'ydental_store_id': 1, 'ydental_revision': 2}],
            'ydental_settlement_source': [{'id': 101, 'ydental_store_id': 1, 'ydental_patient_id': 1,
                'ydental_invoice_id': 1, 'ydental_line_id': 1, '__row_sha256': '1' * 64}],
            'ydental_settlement_payment': [{'id': 102, 'ydental_store_id': 1, 'ydental_patient_id': 1,
                'ydental_payment_id': 1, '__row_sha256': '2' * 64}],
            'ydental_settlement_payment_invoice_rel': [{'settlement_payment_id': 102, 'invoice_id': 1,
                                                       '__row_sha256': '3' * 64}],
            'ydental_access_audit': [{'id': 103, 'ydental_user_id': 16, 'ydental_store_id': 1,
                'ydental_target_model': 'synthetic.old', 'ydental_target_id': 1, '__row_sha256': '4' * 64}],
            'ydental_patient': [{'id': 1, 'ydental_partner_id': 5}],
            'account_move': [{'id': 1, 'company_id': 1, 'partner_id': 5, '__row_sha256': '5' * 64}],
            'account_move_line': [{'id': 1, 'move_id': 1, '__row_sha256': '6' * 64}],
            'account_payment': [{'id': 1, 'company_id': 1, '__row_sha256': '7' * 64}],
            'ydental_clinical_document': [{'id': 1, 'state': 'confirmed', 'ydental_version': 4,
                'ydental_author_id': 7, 'ydental_responsible_id': 7, 'ydental_editor_id': None,
                'ydental_session_id': None, 'ydental_session_revision': 0,
                'ydental_editor_expires': None, 'ydental_editor_lease_id': None,
                'ydental_connection_hash_is_null': True, 'ydental_editor_hash_is_null': True,
                '__row_sha256': '8' * 64}],
            'ydental_clinical_version': [{'id': 9, '__row_sha256': '9' * 64},
                                        {'id': 10, '__row_sha256': 'a' * 64}],
        }
        self.used = set()
        self.baselines = []
        self.live = []
        self.facts = MemoryFacts()
        self.collector_rows = SyntheticRows(self.rows)
        self.collector = self.ns['b_collect_step'](binding=self.binding,
            connect=self.collector_rows.connect,
            connection_args={'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'},
            directory=self.directory / 'synthetic-steps', budget=FakeBudget(),
            target_directory=self.target, config_path=self.config)
        self.metadata_requests = []
        metadata_actor = self.ns['Actor'].__new__(self.ns['Actor'])
        metadata_actor.uid, metadata_actor.role, metadata_actor.revision = 16, 'main', 1
        metadata_actor.csrf = 'synthetic-csrf'
        def metadata_wire(request):
            if self.closed:
                raise AssertionError('METADATA_REQUEST_AFTER_OWNED_SERVICE_CLOSED')
            self.metadata_requests.append(request.full_url)
            if request.full_url.endswith('/ydental/access/action'):
                return FakeResponse(json.dumps({'revision': 2}).encode())
            if not request.full_url.endswith('/web/session/get_session_info'):
                raise AssertionError('UNEXPECTED_METADATA_ROUTE')
            sent = json.loads(request.data)
            self.assertEqual(sent['params'], {})
            return FakeResponse(json.dumps({'jsonrpc': '2.0', 'id': sent['id'],
                                            'result': self.raw_session}).encode())
        metadata_actor.client = http.Client('http://127.0.0.1:18410', database=MAIN,
            owned_targets={MAIN: 'http://127.0.0.1:18410'}, budget=FakeBudget(),
            directory=self.directory / 'synthetic-session-client', opener=FakeOpener(metadata_wire))
        metadata_actor.switch(1)
        self.metadata_actor = metadata_actor
        self.session = self.get_session()
        self.manifest_reference = self.capture_source('manifest', 'manifest', 'B-manifest')
        self.manifest = self.ns['manifest_from_b_source'](self.manifest_reference,
            binding=self.binding, session_info=self.session, provider_ref=self.provider, requested=self.requested)
        self.callbacks = self.ns['b_evidence_callbacks'](binding=self.binding, manifest=self.manifest,
            requested=self.requested, manifest_reference=self.manifest_reference, session_info=self.get_session,
            collect_step=self.collect_step, log_source={'app_directory': self.app,
                'target_directory': self.target, 'pid': self.pid}, close_owned_service=self.finish)

    def get_session(self):
        self.session = self.metadata_actor.session_metadata(binding=self.binding)
        self.assertNotIn('session_token', self.session)
        return self.session

    def parse_for_callbacks(self, **arguments):
        parsed = evidence.parse_b_server_events(**arguments)
        if not arguments['final']:
            self.live.append(parsed)
        return parsed

    def collect_step(self, *, point, check_id, phase, selections):
        self.collector_rows.rows = copy.deepcopy(self.rows)
        reference = self.collector(point=point, check_id=check_id, phase=phase, selections=selections)
        self.assertTrue(self.collector_rows.connections[-1].closed)
        self.assertTrue(self.collector_rows.connections[-1].rolled_back)
        return reference

    def capture_source(self, point, check_id, phase, rows=None):
        selection = self.ns['b_selections'](self.requested,
            **({} if point == 'manifest' else {'old_audit_ids': [103]}))
        reference, _ = self.collect(self.rows if rows is None else rows, selections=selection,
                                    point=point, check_id=check_id, phase=phase)
        return reference

    def receipt(self, point, check_id, target, phase='B-pre', rows=None):
        info = self.session if self.closed else self.get_session()
        reference = self.capture_source(point, check_id, phase, rows=rows)
        return self.ns['receipt_from_b_source'](reference, binding=self.binding, manifest=self.manifest,
            requested=self.requested, session_info=info, check_id=check_id, phase=phase,
            point=point, target=target, old_audit_ids=[103], used=self.used)

    def observe(self, point, check_id, target):
        return self.callbacks['observe'](point, check_id, target)

    def server_events(self, intent, observation):
        return self.callbacks['server_events'](intent, observation)

    def terminal(self, manifest):
        return self.callbacks['terminal'](manifest)

    def actor(self, failure=None):
        def wire(request):
            if failure == 'unknown':
                raise URLError('synthetic loss after open')
            body = json.loads(request.data)
            headers = {key.lower(): value for key, value in request.header_items()}
            self.emit_request(headers['x-ydental-operation-ref'])
            if failure == 'ambiguous':
                self.emit_request(headers['x-ydental-operation-ref'])
            data = {'jsonrpc': '2.0', 'id': body['id'], 'error': {'data': {
                'name': 'odoo.exceptions.AccessError',
                'arguments': [self.ns['_b_message'](body['params']['model'], body['params']['method'])]}}}
            return FakeResponse(json.dumps(data).encode())
        actor = self.ns['Actor'].__new__(self.ns['Actor'])
        actor.uid, actor.role, actor.revision = 16, 'main', 2
        self.opener = FakeOpener(wire)
        actor.client = http.Client('http://127.0.0.1:18410', database=MAIN,
            owned_targets={MAIN: 'http://127.0.0.1:18410'}, budget=FakeBudget(),
            directory=self.directory / ('synthetic-client-' + uuid.uuid4().hex), opener=self.opener)
        return actor

    def run_rpc(self, failure=None, **changes):
        options = dict(manifest=self.manifest, provider_ref=self.provider, observe=self.observe,
                       server_events=self.server_events, terminal=self.terminal)
        options.update(changes)
        return self.ns['main_b'](self.actor(failure), self.facts, **options)

    def read_reference(self, reference):
        path = Path(reference['path'])
        raw = path.read_bytes()
        self.assertEqual(len(raw), reference['bytes'])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), reference['sha256'])
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)
        return strict_loads(raw)

    def test_actual_ro_manifest_and_native_session_then_six_rpc_live_and_terminal(self):
        result = self.run_rpc()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(self.opener.requests), 6)
        self.assertEqual(len(self.live), 6)
        self.assertTrue(self.closed)
        for row in result['checks']:
            self.assertNotEqual(row['request_id'], row['server']['request_id'])
            self.assertEqual(row['preservation'], 'VERIFIED')
            self.assertEqual(row['server_identity'], 'VERIFIED')
            durable = self.read_reference(row['server']['source_reference'])
            self.assertEqual(durable['binding'], self.binding)
            self.assertEqual(durable['manifest_source_reference'], self.manifest_reference)
            self.assertNotIn('events', durable)
            location = durable['locations'][row['server']['evidence_ref']]
            native = strict_loads(Path(location['path']).read_bytes().splitlines()[location['line'] - 1])
            self.assertEqual(native['request_id'], row['server']['request_id'])
            for key, point in (('before_source', 'before'), ('after_source', 'after')):
                source = self.read_reference(row[key])
                self.assertEqual(source['point'], point)
                self.assertEqual(source['binding'], self.binding)
        self.assertEqual(len(result['terminal_sources']), 6)
        for terminal in result['terminal_sources']:
            self.assertEqual(self.read_reference(terminal['source_reference'])['point'], 'terminal')
            final = self.read_reference(terminal['sealed_log_reference'])
            self.assertTrue(final['final'])
            self.assertTrue(final['live_prefixes_verified'])
            self.assertEqual(final['manifest_source_reference'], self.manifest_reference)
            for prefix in final['prefixes']:
                seal = strict_loads(Path(prefix['path'] + '.seal').read_bytes())
                self.assertEqual((seal['sha256'], seal['bytes']), (prefix['sha256'], prefix['bytes']))

    def test_actual_live_mapping_persistence_failure_cannot_pass_or_send_next_request(self):
        def save(path, value):
            if Path(path).name.startswith('b-log-live-'):
                raise OSError('synthetic map persistence unavailable')
            return evidence.save_once(path, value)
        self.ns['save_once'] = save
        result = self.run_rpc()
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(result['checks'][0]['server_identity'], 'PENDING')
        self.assertTrue(self.facts.get('B-RPC-1-write-transport'))

    def test_actual_manifest_native_session_missing_admin_wrong_uid_store_or_revision_refused(self):
        for field, value in (('uid', 17), ('is_admin', True), ('is_system', True),
                             ('is_internal_user', False), ('db', 'wrong'), ('ydental_store_name', 'Other')):
            info = copy.deepcopy(self.session)
            info[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.ns['manifest_from_b_source'](self.manifest_reference,
                    binding=self.binding, session_info=info, provider_ref=self.provider, requested=self.requested)
        info = copy.deepcopy(self.session)
        info['user_context']['ydental_revision'] = 3
        with self.assertRaises(ValueError):
            self.ns['manifest_from_b_source'](self.manifest_reference,
                binding=self.binding, session_info=info, provider_ref=self.provider, requested=self.requested)

    def test_actual_manifest_nonempty_relations_and_cross_patient_company_refused(self):
        changes = [('ydental_access_membership', 'active', False), ('hr_employee', 'user_id', 17),
                   ('account_move', 'partner_id', 99), ('account_move', 'company_id', 2),
                   ('account_move_line', 'move_id', 2), ('ydental_settlement_payment', 'ydental_payment_id', 2),
                   ('ydental_settlement_source', 'ydental_patient_id', 2)]
        for table, field, value in changes:
            rows = copy.deepcopy(self.rows)
            rows[table][0][field] = value
            reference = self.capture_source('manifest', 'manifest', 'B-manifest', rows=rows)
            with self.subTest(table=table, field=field), self.assertRaises(ValueError):
                self.ns['manifest_from_b_source'](reference, binding=self.binding,
                    session_info=self.session, provider_ref=self.provider, requested=self.requested)
        for table in ('ydental_settlement_source', 'ydental_access_membership'):
            rows = copy.deepcopy(self.rows)
            rows[table] = []
            reference = self.capture_source('manifest', 'manifest', 'B-manifest', rows=rows)
            with self.subTest(missing=table), self.assertRaises(ValueError):
                self.ns['manifest_from_b_source'](reference, binding=self.binding,
                    session_info=self.session, provider_ref=self.provider, requested=self.requested)

    def test_actual_group_metadata_implied_admin_or_missing_application_role_refused(self):
        for state in ('missing_application', 'implied_system', 'implied_admin', 'missing_xmlids', 'duplicate_session'):
            rows = copy.deepcopy(self.rows)
            if state == 'missing_application':
                rows['res_groups_users_rel'] = [{'uid': 16, 'gid': 11}]
            if state == 'implied_system':
                rows['res_groups_implied_rel'].append({'gid': 10, 'hid': 12})
            if state == 'implied_admin':
                rows['res_groups_implied_rel'].append({'gid': 10, 'hid': 13})
            if state == 'missing_xmlids':
                rows['ir_model_data'].pop()
            if state == 'duplicate_session':
                rows['ydental_access_session'] *= 2
            reference = self.capture_source('manifest', 'manifest', 'B-manifest', rows=rows)
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.ns['manifest_from_b_source'](reference, binding=self.binding,
                    session_info=self.session, provider_ref=self.provider, requested=self.requested)

    def test_actual_native_session_projection_needs_bound_fresh_switch_provenance(self):
        for state in ('missing', 'old', 'wrong_candidate', 'wrong_switch'):
            info = copy.deepcopy(self.session)
            if state == 'missing':
                info.pop('source')
            elif state == 'old':
                info['source']['started_utc'] = info['source']['ended_utc'] = '2000-01-01T00:00:00+00:00'
            elif state == 'wrong_candidate':
                info['source']['binding']['test_commit'] = 'c' * 40
            else:
                info['source']['requested_store_id'] = 2
            with self.subTest(state=state), self.assertRaises(ValueError):
                self.ns['manifest_from_b_source'](self.manifest_reference, binding=self.binding,
                    session_info=info, provider_ref=self.provider, requested=self.requested)

    def test_actual_callback_reused_source_cannot_pass(self):
        captured = []
        def reuse(**arguments):
            if not captured:
                captured.append(self.collect_step(**arguments))
            return captured[0]
        callback = self.ns['b_evidence_callbacks'](binding=self.binding, manifest=self.manifest,
            requested=self.requested, manifest_reference=self.manifest_reference, session_info=self.get_session,
            collect_step=reuse,
            log_source={'app_directory': self.app, 'target_directory': self.target, 'pid': self.pid},
            close_owned_service=self.finish)
        result = self.run_rpc(**callback)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(result['checks'][0]['preservation'], 'PENDING')

    def test_actual_callback_missing_terminal_seal_blocks_six_rpc_pass(self):
        def close_without_seal():
            self.finish()
            next(self.diagnostics.glob('*.seal')).unlink()
        callbacks = self.ns['b_evidence_callbacks'](binding=self.binding, manifest=self.manifest,
            requested=self.requested, manifest_reference=self.manifest_reference, session_info=self.get_session,
            collect_step=self.collect_step, log_source={'app_directory': self.app,
                'target_directory': self.target, 'pid': self.pid}, close_owned_service=close_without_seal)
        result = self.run_rpc(**callbacks)
        self.assertEqual(len(self.opener.requests), 6)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['terminal_preservation'], 'PENDING')

    def test_actual_server_env_su_flag_cannot_be_intent_claim(self):
        self.request.env.su = True
        result = self.run_rpc()
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['checks'][0]['server_identity'], 'MISMATCH')

    def test_actual_adapter_editor_not_empty_rejected_before_any_request(self):
        self.rows['ydental_clinical_document'][0]['ydental_editor_id'] = 7
        result = self.run_rpc()
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 0)
        self.assertEqual(result['checks'][0]['classification'], 'NOT_SENT')

    def test_actual_native_ambiguous_or_unknown_stops_once_preserves_transport(self):
        result = self.run_rpc(failure='ambiguous')
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(result['checks'][0]['server_identity'], 'PENDING')
        self.assertTrue(self.facts.get('B-RPC-1-write-transport'))

    def test_actual_client_unknown_not_retried_by_adapter_consumer(self):
        result = self.run_rpc(failure='unknown')
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(result['checks'][0]['classification'], 'UNKNOWN')
        self.assertEqual(self.facts.get('B-RPC-1-write-transport')['dispatch_state'], 'UNKNOWN')
        # switch, initial native metadata, one fresh before; no after/terminal HTTP.
        self.assertEqual(len(self.metadata_requests), 3)

    def test_actual_adapter_after_failure_saves_previous_and_current_transport(self):
        def observe(point, check_id, target):
            if point == 'after' and check_id == 'B-RPC-1-unlink':
                raise RuntimeError('synthetic capture failure')
            return self.observe(point, check_id, target)
        result = self.run_rpc(observe=observe)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(len(self.opener.requests), 2)
        self.assertEqual(result['checks'][0]['preservation'], 'VERIFIED')
        self.assertEqual(result['checks'][1]['preservation'], 'PENDING')
        self.assertTrue(self.facts.get('B-RPC-1-unlink-transport'))


class ActualModelParentProtocol(ActualBAdapters):
    """Real parent and child protocol, only the process/ORM boundary is fake."""

    def model_pipeline(self, *, outer_failure=None, child_code=0, probe_failure=None,
                       reject_checkpoint=None, terminal_missing=False):
        events, environments, applications = [], [], []
        case = self
        class Cursor(SyntheticCursor):
            def rollback(self):
                super().rollback()
                events.append(('outer-rollback', len(environments[0].calls)))
                if outer_failure == 'rollback':
                    raise RuntimeError('synthetic outer rollback failure')
            def __exit__(self, *args):
                super().__exit__(*args)
                events.append(('outer-close', len(environments[0].calls)))
                if outer_failure == 'close':
                    raise RuntimeError('synthetic outer close failure')
        cursor = Cursor()
        registry = SimpleNamespace(cursor=lambda: cursor)
        def environment(cr, uid, context):
            env = SyntheticEnvironment(cr, uid, context, failure=probe_failure, fail_at=3)
            environments.append(env)
            return env
        helper = actual_definitions(FIXTURE, ['_ordinary_actor', '_model_denials'],
            _TARGETS=literal(FIXTURE, '_TARGETS'), AccessError=SyntheticAccessError, closing=closing,
            _guard=lambda *args: self.manifest['identity'] | {'core': evidence.CORE},
            _row_sha=lambda env, table, record_id: next(row['__row_sha256']
                for row in self.rows[table] if row['id'] == record_id))
        @contextmanager
        def scope(**values):
            events.append(('scope', values['actor_id']))
            yield
        def forbidden(*args, **kwargs):
            raise AssertionError('UNRELATED_FIXTURE_OR_AUTHENTICATION_FORBIDDEN')
        fixture_module = SimpleNamespace(_guard=helper['_guard'], _model_denials=helper['_model_denials'],
            _create_reader=forbidden, _initialize_reader_password=forbidden, _limited_token=forbidden)
        def imports(name, *args, **kwargs):
            if name == 'odoo':
                return SimpleNamespace(Command=object, api=SimpleNamespace(Environment=environment))
            if name == 'odoo.addons.ydental_access.diagnostics':
                return SimpleNamespace(context_scope=scope)
            if name == 'odoo.addons.ydental_settlement_test.models.lc2_fixture':
                return fixture_module
            if name == 'logging':
                return SimpleNamespace(CRITICAL=50,
                    getLogger=lambda name: SimpleNamespace(getEffectiveLevel=lambda: 50))
            raise AssertionError('REAL_APPLICATION_IMPORT_FORBIDDEN:' + name)

        class Application:
            def __init__(app, marker, **arguments):
                applications.append(app)
                app.directory = case.directory / ('synthetic-model-parent-' + uuid.uuid4().hex)
                app.directory.mkdir(mode=0o700)
                app.run = case.directory / ('synthetic-model-child-' + uuid.uuid4().hex)
                app.run.mkdir(mode=0o700)
                (app.run / 'diagnostics').mkdir(mode=0o700)
                app.env = {'YDENTAL_S10_RUN_DIR': str(app.run)}
                app.budget = SimpleNamespace(check_storage=lambda: None)
                app.done = threading.Event()
                app.worker_errors = []
                app.process = SimpleNamespace(poll=lambda: child_code if app.done.is_set() else None)
            def start(app, arguments, *, pass_fds, stdin_path):
                case.assertEqual(arguments, [])
                case.assertEqual(stdin_path, FIXTURE_PROCESS)
                child_environ = dict(app.env)
                for key in ('YDENTAL_LC2_INPUT_FD', 'YDENTAL_LC2_OUTPUT_FD'):
                    child_environ[key] = str(os.dup(int(child_environ[key])))
                child_os = SimpleNamespace(**{name: getattr(os, name) for name in dir(os)
                                               if not name.startswith('__')})
                child_os.environ = child_environ
                child = actual_definitions(FIXTURE_PROCESS,
                    ['main', 'run_b_model_only', '_save_b_model_observation'], os=child_os, stat=stat,
                    __builtins__=dict(vars(builtins), __import__=imports))
                def run():
                    try:
                        child['main'](SimpleNamespace(cr=SimpleNamespace(dbname=MAIN), registry=registry))
                    except BaseException as error:
                        app.worker_errors.append(error)
                    finally:
                        app.done.set()
                app.thread = threading.Thread(target=run, name='synthetic-B-child', daemon=True)
                app.thread.start()
            def check(app):
                return None
            def wait(app, timeout):
                app.thread.join(min(timeout, 5))
                if app.thread.is_alive():
                    raise AssertionError('SYNTHETIC_CHILD_DID_NOT_CLOSE')
                if app.worker_errors:
                    raise app.worker_errors[0]
                return child_code
            def close(app, primary=None):
                app.thread.join(5)
                case.assertFalse(app.thread.is_alive())

        namespaces = actual_definitions(CASES, ['run_fixture', '_b_ref', '_b_sha', 'validate_b_inputs',
            '_b_time', '_b_snapshot_valid', '_b_preserved', '_b_model_complete', '_b_message'],
            B_TARGET_FIELDS=literal(CASES, 'B_TARGET_FIELDS'), NAMES={'main': MAIN}, OIDS={'main': 2144129},
            os=os, select=select, ROOT=ROOT, EXEC_ROOT=self.directory,
            OwnedApplication=Application, marker=lambda role: {'synthetic': role}, strict_loads=strict_loads,
            save_once=evidence.save_once, closed_log_report=lambda app: events.append(('log-final', cursor.closed)))

        def observe(point, check_id, target):
            calls = len(environments[0].calls)
            expected_index = (int(check_id.split('-')[2]) - 1) * 2 + int(check_id.endswith('unlink'))
            self.assertEqual(calls, expected_index + int(point == 'after'))
            self.assertEqual(cursor.version, 0)
            self.assertFalse(cursor.closed)
            events.append((point, check_id, calls))
            if reject_checkpoint == (point, check_id):
                raise RuntimeError('synthetic independent checkpoint failed')
            return self.receipt(point, check_id, target, phase='B-model')

        def terminal(manifest):
            self.assertTrue(applications[0].done.is_set())
            self.assertTrue(cursor.closed)
            self.assertGreaterEqual(cursor.outer_rollbacks, 1)
            events.append(('terminal', len(environments[0].calls)))
            if terminal_missing:
                return []
            return [self.receipt('terminal', 'B-MODEL-%d-%s' % (index, method), target,
                                 phase='B-model') for index, target in enumerate(manifest['targets'], 1)
                    for method in ('write', 'unlink')][:len(environments[0].calls)]
        self.model_test_state = SimpleNamespace(cursor=cursor, events=events, environments=environments,
                                                applications=applications)
        def factory(app):
            self.assertFalse(hasattr(app, 'thread'))
            events.append(('factory-before-start', True))
            return {'observe': observe, 'terminal': terminal}
        return namespaces['run_fixture']('main', approval='synthetic-only-never-read',
            product_commit=self.binding['product_commit'], test_commit=self.binding['test_commit'],
            mode='main-b-only', manifest=self.manifest, provider_ref=self.provider,
            evidence_factory=factory)['safe']['model_checks']

    def assert_failed_model_never_reaches_rpc(self, model):
        def actor_forbidden(*args):
            self.fail('FAILED_MODEL_MUST_NOT_BUILD_RPC_ACTOR')
        result = self.ns['_run_b_only_checks'](manifest=self.manifest, provider_ref=self.provider,
            facts=self.facts, model_probe=lambda manifest: model, actor_factory=actor_forbidden,
            **self.callbacks)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['rpc'], 'NOT_RUN')

    def test_actual_parent_child_checkpoint_source_and_twelve_consumer_chain(self):
        model = self.model_pipeline()
        state = self.model_test_state
        self.assertEqual(len(state.environments), 1)
        self.assertEqual(len(state.environments[0].calls), 6)
        self.assertEqual(state.cursor.savepoint_rollbacks, 6)
        self.assertEqual(state.cursor.commits, 0)
        self.assertEqual(model['independent_preservation'], 'VERIFIED')
        composition = actual_definitions(CASES, ['_run_b_only_checks', '_b_model_complete',
            '_b_ref', '_b_sha', 'validate_b_inputs', '_b_time', '_b_snapshot_valid', '_b_preserved', '_b_message'],
            B_TARGET_FIELDS=literal(CASES, 'B_TARGET_FIELDS'), NAMES={'main': MAIN}, OIDS={'main': 2144129},
            main_b=self.ns['main_b'])
        result = composition['_run_b_only_checks'](manifest=self.manifest, provider_ref=self.provider,
            facts=self.facts, model_probe=lambda manifest: model,
            actor_factory=lambda *args: self.actor(), **self.callbacks)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(self.opener.requests), 6)

    def test_actual_parent_six_observations_outer_rollback_or_close_failure_not_complete(self):
        # Separate synthetic files prevent a retry from overwriting first material.
        model = self.model_pipeline(outer_failure='rollback')
        state = self.model_test_state
        self.assertEqual(len(state.environments[0].calls), 6)
        self.assertEqual(len(model['checks']), 6)
        self.assertEqual(model['producer_status'], 'FAILED')
        self.assertEqual(model['independent_preservation'], 'PENDING')
        self.assertTrue((state.applications[0].directory / 'safe-result.json').is_file())
        self.assert_failed_model_never_reaches_rpc(model)

    def test_actual_parent_six_observations_outer_close_failure_not_complete(self):
        model = self.model_pipeline(outer_failure='close')
        self.assertEqual(len(model['checks']), 6)
        self.assertEqual(model['producer_status'], 'FAILED')
        self.assertEqual(model['independent_preservation'], 'PENDING')
        self.assert_failed_model_never_reaches_rpc(model)

    def test_actual_parent_nonzero_child_exit_preserves_partial_before_raise(self):
        with self.assertRaisesRegex(RuntimeError, 'PROCESS_FAILED_WITH_PRESERVED_STATE'):
            self.model_pipeline(child_code=17)
        app = self.model_test_state.applications[0]
        saved = strict_loads((app.directory / 'safe-result.json').read_bytes())
        self.assertEqual(saved['model_checks']['producer_status'], 'FAILED')
        self.assertEqual(len(saved['model_checks']['checks']), 6)
        self.assertTrue((app.directory / 'b-parent-failure.json').is_file())

    def test_actual_parent_child_midprobe_failure_retains_failed_row_and_stops(self):
        model = self.model_pipeline(probe_failure='arguments')
        self.assertEqual(len(model['checks']), 3)
        self.assertEqual(len(self.model_test_state.environments[0].calls), 3)
        self.assertFalse(model['checks'][-1]['native_public_arguments_exact_expected'])
        self.assertEqual(model['independent_preservation'], 'PENDING')

    def test_actual_parent_before_ack_denial_never_runs_target(self):
        model = self.model_pipeline(reject_checkpoint=('before', 'B-MODEL-1-write'))
        self.assertEqual(self.model_test_state.environments[0].calls, [])
        self.assertEqual(model['checks'], [])
        self.assertEqual(model['producer_status'], 'FAILED')
        app = self.model_test_state.applications[0]
        observed = strict_loads((app.directory / 'B-MODEL-1-write-before.json').read_bytes())
        self.assertEqual(observed['observer_error_type'], 'RuntimeError')
        self.assertFalse(observed['accepted'])

    def test_actual_parent_terminal_missing_cannot_complete_six_model_rows(self):
        model = self.model_pipeline(terminal_missing=True)
        self.assertEqual(len(model['checks']), 6)
        self.assertEqual(model['independent_preservation'], 'PENDING')

    def test_actual_parent_factory_exception_saves_not_sent_and_closes_all_four_fds(self):
        created, applications = [], []
        original_pipe = os.pipe
        case = self
        def pipe():
            pair = original_pipe()
            created.extend(pair)
            return pair
        class Application:
            def __init__(app, *args, **kwargs):
                app.directory = case.directory / 'synthetic-factory-exception'
                app.directory.mkdir(mode=0o700)
                app.closed, app.started = False, False
                applications.append(app)
            def close(app, primary=None):
                app.closed = True
            def start(app, *args, **kwargs):
                app.started = True
                case.fail('FACTORY_ERROR_MUST_NOT_START_APPLICATION')
        def factory(app):
            raise ValueError('synthetic private exception details never serialized')
        namespace = actual_definitions(CASES, ['run_fixture'], os=os, ROOT=ROOT,
            validate_b_inputs=self.ns['validate_b_inputs'], OwnedApplication=Application,
            marker=lambda role: {'synthetic': role}, save_once=evidence.save_once)
        with patch.object(os, 'pipe', pipe), self.assertRaisesRegex(RuntimeError, 'SETUP_FAILED_NOT_SENT'):
            namespace['run_fixture']('main', approval='synthetic-never-opened',
                product_commit=self.binding['product_commit'], test_commit=self.binding['test_commit'],
                mode='main-b-only', manifest=self.manifest, provider_ref=self.provider,
                evidence_factory=factory)
        self.assertEqual(len(created), 4)
        for fd in created:
            with self.assertRaises(OSError):
                os.fstat(fd)
        self.assertTrue(applications[0].closed)
        self.assertFalse(applications[0].started)
        failure = strict_loads((applications[0].directory / 'b-parent-setup-failure.json').read_bytes())
        self.assertEqual(failure, {'failure_type': 'ValueError', 'status': 'NOT_SENT', 'application_started': False})


def load_tests(loader, standard_tests, pattern):
    # The MODEL harness shares setup with RPC tests; each method is run once.
    return unittest.TestSuite(test_class(name) for test_class in
        (ActualEvidenceSources, ActualBAdapters, ActualModelParentProtocol)
        for name in sorted(test_class.__dict__) if name.startswith('test_'))


if __name__ == '__main__':
    unittest.main()
