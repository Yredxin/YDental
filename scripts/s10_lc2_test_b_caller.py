"""Synthetic-only regression of actual B callers and HTTP dispatch boundaries.

Application/ORM callers are extracted from their checked-out AST and receive
explicit fake boundaries. No Odoo module, provider, registry or service starts.
"""
import ast
import builtins
from contextlib import closing, contextmanager
import copy
from datetime import datetime, timezone
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib.error import URLError
import uuid

import s10_lc2_http as http

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / 'scripts/s10_lc2_cases.py'
FIXTURE_PROCESS = ROOT / 'scripts/s10_lc2_fixture_process.py'
FIXTURE = ROOT / 'ydental_settlement_test/models/lc2_fixture.py'
MAIN = 'ydental_s10_test_20261017105432_810a7d9c'


def literal(path, name):
    tree = ast.parse(path.read_bytes())
    return ast.literal_eval(next(node.value for node in tree.body
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)))


def actual_definitions(path, names, **boundaries):
    """Compile exact actual definitions; never execute a script's top-level main."""
    tree = ast.parse(path.read_bytes(), filename=str(path))
    nodes = [copy.deepcopy(node) for node in tree.body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    if {node.name for node in nodes} != set(names):
        raise AssertionError('ACTUAL_DEFINITION_MISSING')
    namespace = {'__file__': str(path), 'json': json, 'hashlib': hashlib, 'uuid': uuid,
                 'Path': Path, 'time': time, 'datetime': datetime, 'timezone': timezone, 're': re}
    namespace.update(boundaries)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(path), 'exec'), namespace)
    return namespace


class PureBoundaryCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='synthetic-b-caller-', dir=ROOT / '.local')
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        for owner, name in ((socket, 'socket'), (subprocess, 'Popen'), (subprocess, 'run'),
                            (subprocess, 'check_output')):
            guard = patch.object(owner, name, side_effect=AssertionError('EXTERNAL_PROCESS_OR_NETWORK_FORBIDDEN'))
            guard.start()
            self.addCleanup(guard.stop)


class FakeBudget:
    def __init__(self, failure=None, profile=None):
        self.profile = profile
        self.failure = failure
        self.intents = []

    def consume(self, kind):
        if self.failure is not None:
            raise self.failure
        self.intents.append(kind)


class FakeResponse:
    def __init__(self, body=b'{}', status=200):
        self.body, self.status = body, status
        self.headers = {'Content-Type': 'application/json'}
        self.closed = False

    def read(self, bound):
        return self.body[:bound]

    def close(self):
        self.closed = True


class FakeOpener:
    handlers = ()

    def __init__(self, response):
        self.response = response
        self.requests = []

    def open(self, request, timeout):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        if callable(self.response):
            return self.response(request)
        return self.response


class MemoryFacts:
    def __init__(self):
        self.rows = []

    def save(self, name, value):
        self.rows.append((name, copy.deepcopy(value)))

    def get(self, name):
        return next(value for key, value in self.rows if key == name)


def synthetic_manifest():
    fields = literal(CASES, 'B_TARGET_FIELDS')
    return {'schema': 'LC2_B_MANIFEST_1',
        'identity': {'database': MAIN, 'oid': 2144129, 'cluster': '7694897083368259627'},
        'actor': {'uid': 16, 'active': True, 'internal': True, 'application_user': True,
                  'su': False, 'is_admin': False, 'is_system': False, 'metadata_ref': 'synthetic/actor-metadata'},
        'store_id': 1, 'source_ref': 'synthetic/manifest',
        'targets': [{'model': model, 'id': index + 100, 'values': {
            column: 'LC2 denied tampering' if column == 'ydental_reason' else 1},
            'source_ref': 'synthetic/target-%d' % index} for index, (model, column) in enumerate(fields.items(), 1)]}


class ActualBCaller(PureBoundaryCase):
    def setUp(self):
        super().setUp()
        self.manifest = synthetic_manifest()
        self.provider = {'ref': '.local/synthetic-b-provider/reference.json', 'actor_id': 16}
        self.facts = MemoryFacts()
        self.calls, self.baselines = [], []
        self.terminal_calls = 0
        self.gate_calls = []
        self.ns = actual_definitions(CASES, ['_b_ref', '_b_sha', '_b_message', 'validate_b_inputs',
            '_b_time', '_b_snapshot_valid', '_b_preserved', '_b_model_complete', 'correlate_b_server',
            'main_b', 'run_b_only', '_run_b_only_checks', 'Actor'],
            B_TARGET_FIELDS=literal(CASES, 'B_TARGET_FIELDS'), NAMES={'main': MAIN}, OIDS={'main': 2144129},
            Client=http.Client, RequestNotSent=http.RequestNotSent, OutcomeUnknown=http.OutcomeUnknown, datetime=SyntheticClock,
            EXEC_ROOT=self.directory, require_dispatch_unfrozen=lambda: None,
            runtime_gate=self.gate, main_a=self.forbidden, main_c=self.forbidden,
            existing_main_accounts=self.forbidden, run_fixture=self.forbidden,
            upgrade=self.forbidden, d_flow=self.forbidden)
        self.actor = SimpleNamespace(uid=16, role='main', revision=1, rpc_observed=self.rpc)

    def forbidden(self, *args, **kwargs):
        raise AssertionError('UNRELATED_A_C_D_E_OR_PROVIDER_READING_FORBIDDEN')

    def gate(self, *args, **kwargs):
        self.gate_calls.append((args, kwargs))
        return {'scope': 'B_ONLY', 'allowed_b_cases': ['B-MODEL-6', 'B-RPC-6'], 'allowed_target_names': [MAIN]}

    def snapshot(self, point, check_id, target, phase='B-pre'):
        return {'layer': 'INDEPENDENT_RO', 'independent': True,
            'ref': 'synthetic/%s/%s' % (point, check_id),
            'connection_ref': 'synthetic/connection/%s/%s' % (point, check_id),
            'phase': phase, 'point': point, 'check_id': check_id,
            'baseline_ref': self.manifest['source_ref'],
            'captured_utc': {'before': '2098-12-31T23:59:59+00:00', 'after': '2099-01-01T00:00:02+00:00',
                             'terminal': '2099-01-01T00:00:03+00:00'}[point],
            'transaction': {'read_only': True, 'closed': True, 'outcome': 'ROLLBACK'},
            'identity': self.manifest['identity'], 'actor': self.manifest['actor'],
            'source_ref': target['source_ref'], 'model': target['model'], 'id': target['id'],
            'row_sha256': 'a' * 64, 'old_audit_sha256': 'b' * 64, 'protected_sha256': 'c' * 64,
            'editor': {'document_id': 1, 'state': 'confirmed', 'version': 4,
                       'author_id': 7, 'responsible_id': 7,
                       'ydental_editor_id': None, 'ydental_session_id': None, 'ydental_session_revision': 0,
                       'ydental_connection_hash_is_null': True, 'ydental_editor_hash_is_null': True,
                       'ydental_editor_expires': None, 'ydental_editor_lease_id': None}}

    def observe(self, phase, check_id, target):
        result = self.snapshot(phase, check_id, target)
        if phase == 'before':
            self.baselines.append((check_id, target))
        return result

    def rpc(self, model, method, args, *, operation_ref, attempt):
        self.calls.append({'model': model, 'method': method, 'args': copy.deepcopy(args),
                           'operation_ref': operation_ref, 'attempt': attempt})
        return {'started_utc': '2099-01-01T00:00:00+00:00', 'ended_utc': '2099-01-01T00:00:01+00:00',
            'dispatch_state': 'RESPONSE_RECEIVED', 'request_id': 'synthetic-client-%d' % len(self.calls),
            'http_status': 200, 'native_error_name': 'odoo.exceptions.AccessError',
            'native_public_arguments_exact_expected': True, 'result_present': False, 'response_format_valid': True}

    def server_events(self, intent, observation):
        return [{'event': 'request.received', 'case_id': 'B-RPC-6', 'attempt': 1,
            'operation_ref': intent['operation_ref_sha256'], 'ts_utc': '2099-01-01T00:00:00.5+00:00',
            'request_id': 'synthetic-server-' + intent['check_id'], 'trace_id': 'synthetic-trace-' + intent['check_id'],
            'actor_id': 16, 'effective_uid': 16, 'su_flag': False, 'evidence_ref': 'synthetic/server-event'}]

    def terminal(self, manifest):
        self.terminal_calls += 1
        return [self.snapshot('terminal', check_id, target) for check_id, target in self.baselines]

    def run_main(self, **overrides):
        options = dict(manifest=self.manifest, provider_ref=self.provider, observe=self.observe,
                       server_events=self.server_events, terminal=self.terminal)
        options.update(overrides)
        return self.ns['main_b'](self.actor, self.facts, **options)

    def run_only(self, **overrides):
        options = dict(manifest=self.manifest, provider_ref=self.provider, approval='synthetic-approval',
            product_commit='synthetic-product', test_commit='synthetic-test', facts=self.facts,
            model_probe=lambda manifest: {'six_denied': False, 'actor_id': 16, 'independent_preservation': 'PENDING'},
            actor_factory=lambda *args: self.actor, observe=self.observe,
            server_events=self.server_events, terminal=self.terminal)
        options.update(overrides)
        for key in ('approval', 'product_commit', 'test_commit'):
            options.pop(key)
        return self.ns['_run_b_only_checks'](**options)

    def complete_synthetic_model(self):
        helper = model_namespace(self.manifest)
        env = SyntheticEnvironment(SyntheticCursor(), 16, {})
        model = helper['_model_denials'](env, uid=16, targets=self.manifest['targets'], run_directory=str(self.directory))
        for row in model['checks']:
            target = next(target for target in self.manifest['targets'] if target['model'] == row['model'])
            for point in ('before', 'after', 'terminal'):
                row[point] = self.snapshot(point, row['check_id'], target, phase='B-model')
                row[point]['row_sha256'] = row['existing_target_sha256']
        return model

    def test_actual_six_rpc_calls_correlate_different_client_server_ids(self):
        result = self.run_main()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(self.calls), 6)
        self.assertEqual({(row['model'], row['method']) for row in self.calls},
                         {(item['model'], method) for item in self.manifest['targets'] for method in ('write', 'unlink')})
        for row in result['checks']:
            self.assertNotEqual(row['request_id'], row['server']['request_id'])
            self.assertEqual(row['server_identity'], 'VERIFIED')
            self.assertEqual(row['preservation'], 'VERIFIED')
            intent_index = next(i for i, (name, _) in enumerate(self.facts.rows) if name == row['check_id'] + '-intent')
            transport_index = next(i for i, (name, _) in enumerate(self.facts.rows) if name == row['check_id'] + '-transport')
            observed_index = next(i for i, (name, _) in enumerate(self.facts.rows) if name == row['check_id'] + '-observation')
            self.assertLess(intent_index, transport_index)
            self.assertLess(transport_index, observed_index)

    def test_actual_missing_manifest_target_identity_or_provider_rejected_before_calls(self):
        changes = [('manifest', None), ('provider_ref', None)]
        for key, value in changes:
            with self.subTest(key=key), self.assertRaises((ValueError, TypeError)):
                self.run_main(**{key: value})
        for mutation in ('missing_target', 'zero_target', 'actor7', 'su', 'wrong_identity'):
            manifest = copy.deepcopy(self.manifest)
            if mutation == 'missing_target': manifest['targets'].pop()
            if mutation == 'zero_target': manifest['targets'][0]['id'] = 0
            if mutation == 'actor7': manifest['actor']['uid'] = 7
            if mutation == 'su': manifest['actor']['su'] = True
            if mutation == 'wrong_identity': manifest['identity']['oid'] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.run_main(manifest=manifest)
        self.assertEqual(self.calls, [])

    def test_actual_actor_mismatch_rejected(self):
        self.actor.uid = 18
        with self.assertRaises(ValueError): self.run_main()
        self.assertEqual(self.calls, [])

    def test_actual_missing_before_evidence_is_not_sent_pending(self):
        result = self.run_main(observe=None)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(self.calls, [])
        self.assertEqual(result['checks'][0]['classification'], 'NOT_SENT')

    def test_actual_missing_after_terminal_or_released_editor_cannot_pass(self):
        for missing in ('after', 'terminal', 'editor'):
            self.baselines = []
            self.calls = []
            self.facts = MemoryFacts()
            def observe(phase, check_id, target):
                row = self.observe(phase, check_id, target)
                if missing == 'after' and phase == 'after': return None
                if missing == 'editor': row['editor']['ydental_editor_id'] = 16
                return row
            with self.subTest(missing=missing):
                result = self.run_main(observe=observe, terminal=None if missing == 'terminal' else self.terminal)
                self.assertEqual(result['status'], 'PENDING')

    def test_actual_missing_ambiguous_wrong_actor_or_wrong_correlation_server_events_pending(self):
        for invalid in ('missing', 'ambiguous', 'actor', 'su', 'opref', 'attempt', 'outside_window'):
            self.calls, self.baselines, self.facts = [], [], MemoryFacts()
            def events(intent, observation):
                rows = self.server_events(intent, observation)
                if invalid == 'missing': return []
                if invalid == 'ambiguous': return rows + copy.deepcopy(rows)
                if invalid == 'actor': rows[0]['effective_uid'] = 1
                if invalid == 'su': rows[0]['su_flag'] = True
                if invalid == 'opref': rows[0]['operation_ref'] = 'wrong'
                if invalid == 'attempt': rows[0]['attempt'] = 2
                if invalid == 'outside_window': rows[0]['ts_utc'] = '2099-01-01T00:03:00+00:00'
                return rows
            with self.subTest(invalid=invalid):
                self.assertEqual(self.run_main(server_events=events)['status'], 'PENDING')
                self.assertEqual(len(self.calls), 1)

    def test_actual_wrong_native_name_arguments_or_auth_rejection_preserved_not_model_pass(self):
        for override in ({'native_error_name': 'odoo.exceptions.UserError'},
                         {'native_public_arguments_exact_expected': False},
                         {'http_status': 403, 'native_error_name': 'odoo.exceptions.AccessDenied'},
                         {'result_present': True}):
            self.calls, self.baselines, self.facts = [], [], MemoryFacts()
            def rpc(*args, **kwargs): return self.rpc(*args, **kwargs) | override
            self.actor.rpc_observed = rpc
            with self.subTest(override=override):
                result = self.run_main()
                self.assertEqual(result['status'], 'PENDING')
                expected = ('AUTHENTICATION_OR_AUTHORIZATION_PRECONDITION' if override.get('http_status') == 403
                            else 'OTHER_NATIVE_RESULT_OR_REJECTION')
                self.assertEqual(result['checks'][0]['classification'], expected)
                self.assertEqual(self.facts.get(result['checks'][0]['check_id'] + '-transport')['http_status'], override.get('http_status', 200))

    def test_actual_unknown_and_local_not_sent_never_retry_or_count_denial(self):
        for state in ('NOT_SENT', 'UNKNOWN'):
            self.calls, self.baselines, self.facts = [], [], MemoryFacts()
            def rpc(*args, **kwargs): return self.rpc(*args, **kwargs) | {'dispatch_state': state}
            self.actor.rpc_observed = rpc
            with self.subTest(state=state):
                result = self.run_main()
                self.assertEqual(result['status'], 'PENDING')
                self.assertEqual(result['checks'][0]['classification'], state)
                self.assertEqual(len(self.calls), 1)
                self.assertEqual(self.calls[0]['attempt'], 1)

    def test_actual_midstream_callback_failure_keeps_prior_and_current_transport(self):
        def events(intent, observation):
            if len(self.calls) == 3: raise RuntimeError('synthetic third observation failure')
            return self.server_events(intent, observation)
        self.assertEqual(self.run_main(server_events=events)['status'], 'PENDING')
        names = [name for name, _ in self.facts.rows]
        self.assertIn('B-RPC-1-write-observation', names)
        self.assertIn('B-RPC-1-unlink-observation', names)
        self.assertIn('B-RPC-2-write-transport', names)
        self.assertEqual(len(self.calls), 3)

    def test_actual_b_dispatch_rejects_no_authority_stop_old_main_a_before_dependencies(self):
        for forbidden in ('no_authority', 'stop', 'old_main_a', 'frozen'):
            with self.subTest(forbidden=forbidden):
                self.ns['runtime_gate'] = self.gate
                self.ns['require_dispatch_unfrozen'] = lambda: None
                stop = self.directory / 'HARD-STOP.json'
                if stop.exists(): stop.unlink()
                if forbidden == 'no_authority':
                    self.ns['runtime_gate'] = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('NO_VALID_APPLICATION_AUTHORITY'))
                if forbidden == 'stop': stop.write_text('{"synthetic_stop":true}')
                if forbidden == 'old_main_a': self.ns['runtime_gate'] = lambda *a, **k: {'message_id': 'YD-S10-LC2-MAIN-A-20261018-04', 'allowed_target_names': [MAIN]}
                if forbidden == 'frozen': self.ns['require_dispatch_unfrozen'] = lambda: (_ for _ in ()).throw(RuntimeError('DISPATCH_FROZEN'))
                with self.assertRaises(RuntimeError):
                    self.ns['run_b_only'](manifest=self.manifest, provider_ref=self.provider,
                        approval='synthetic', product_commit='synthetic', test_commit='synthetic',
                        facts=self.facts, model_probe=self.forbidden, actor_factory=self.forbidden,
                        observe=self.forbidden, server_events=self.forbidden, terminal=self.forbidden)
        self.assertEqual(self.calls, [])

    def test_actual_b_dispatch_model_pending_does_not_create_actor_or_rpc(self):
        result = self.run_only(actor_factory=self.forbidden)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['rpc'], 'NOT_RUN')
        self.assertEqual(self.calls, [])

    def test_actual_pure_b_composition_consumes_six_model_records_then_six_rpc(self):
        model = self.complete_synthetic_model()
        factories = []
        def actor_factory(provider, manifest):
            factories.append((provider, manifest))
            self.assertEqual(self.facts.get('B-model-observation'), model)
            return self.actor
        result = self.run_only(model_probe=lambda manifest: model, actor_factory=actor_factory)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(len(result['model']['checks']), 6)
        self.assertEqual(len(result['rpc']['checks']), 6)
        self.assertEqual(len(factories), 1)
        self.assertEqual(factories[0][0], self.provider)
        self.assertFalse(result['rpc']['native_runtime_claimed'])

    def test_actual_model_consumer_rejects_flags_only_missing_or_inconsistent_percase_proof(self):
        baseline = self.complete_synthetic_model()
        self.assertTrue(self.ns['_b_model_complete'](baseline, self.manifest))
        for invalid in ('empty', 'target', 'uid', 'su', 'admin', 'default_env', 'class', 'arguments',
                        'before', 'after', 'terminal', 'old_audit_hash', 'wrong_check', 'same_connection', 'editor'):
            model = copy.deepcopy(baseline)
            row = model['checks'][0]
            if invalid == 'empty': model['checks'] = []
            if invalid == 'target': row['id'] = 999
            if invalid == 'uid': row['effective_uid'] = 1
            if invalid == 'su': row['su_flag'] = True
            if invalid == 'admin': row['is_admin'] = True
            if invalid == 'default_env': row['default_env_su'] = True
            if invalid == 'class': row['exception_name'] = 'odoo.exceptions.UserError'
            if invalid == 'arguments': row['native_public_arguments'] = ['synthetic wrong message']
            if invalid in ('before', 'after', 'terminal'): row[invalid] = None
            if invalid == 'old_audit_hash': row['after']['old_audit_sha256'] = 'd' * 64
            if invalid == 'wrong_check': row['before']['check_id'] = 'wrong'
            if invalid == 'same_connection': row['after']['connection_ref'] = row['before']['connection_ref']
            if invalid == 'editor': row['terminal']['editor']['ydental_session_id'] = 109
            with self.subTest(invalid=invalid):
                result = self.run_only(model_probe=lambda manifest: model, actor_factory=self.forbidden)
                self.assertEqual(result['status'], 'PENDING')
                self.assertEqual(result['rpc'], 'NOT_RUN')
        self.assertEqual(self.calls, [])

    def test_actual_percase_receipts_reject_crosscheck_phase_time_unclosed_or_drift(self):
        for invalid in ('check', 'phase', 'point', 'baseline', 'naive_time', 'stale', 'unclosed', 'drift', 'editor_hash'):
            self.calls, self.baselines, self.facts = [], [], MemoryFacts()
            def observe(point, check_id, target):
                row = self.observe(point, check_id, target)
                if point != 'after': return row
                if invalid == 'check': row['check_id'] = 'wrong'
                if invalid == 'phase': row['phase'] = 'wrong'
                if invalid == 'point': row['point'] = 'before'
                if invalid == 'baseline': row['baseline_ref'] = 'wrong'
                if invalid == 'naive_time': row['captured_utc'] = '2099-01-01T00:00:02'
                if invalid == 'stale': row['captured_utc'] = '2098-12-31T23:59:50+00:00'
                if invalid == 'unclosed': row['transaction']['closed'] = False
                if invalid == 'drift': row['row_sha256'] = 'd' * 64
                if invalid == 'editor_hash': row['editor']['ydental_editor_hash_is_null'] = False
                return row
            with self.subTest(invalid=invalid):
                self.assertEqual(self.run_main(observe=observe)['status'], 'PENDING')
                self.assertEqual(len(self.calls), 1)

    def test_actual_observer_or_terminal_exception_preserves_results_and_stops_without_retry(self):
        for failure in ('before', 'after', 'terminal'):
            self.calls, self.baselines, self.facts = [], [], MemoryFacts()
            def observe(point, check_id, target):
                if point == failure: raise RuntimeError('synthetic independent observer failure')
                return self.observe(point, check_id, target)
            def terminal(manifest):
                if failure == 'terminal': raise RuntimeError('synthetic terminal failure')
                return self.terminal(manifest)
            with self.subTest(failure=failure):
                result = self.run_main(observe=observe, terminal=terminal)
                self.assertEqual(result['status'], 'PENDING')
                self.assertEqual(len(self.calls), 0 if failure == 'before' else 1 if failure == 'after' else 6)
                if self.calls: self.assertIsNotNone(self.facts.get('B-RPC-1-write-transport'))

    def test_actual_terminal_must_follow_last_batch_result_not_just_its_own_check(self):
        def rpc(*args, **kwargs):
            row = self.rpc(*args, **kwargs)
            if len(self.calls) == 6: row['ended_utc'] = '2099-01-01T00:00:04+00:00'
            return row
        self.actor.rpc_observed = rpc
        def observe(point, check_id, target):
            row = self.observe(point, check_id, target)
            if point == 'after': row['captured_utc'] = '2099-01-01T00:00:05+00:00'
            return row
        def terminal(manifest):
            rows = self.terminal(manifest)
            for row in rows: row['captured_utc'] = '2099-01-01T00:00:06+00:00'
            rows[0]['captured_utc'] = '2099-01-01T00:00:02+00:00'
            return rows
        result = self.run_main(observe=observe, terminal=terminal)
        self.assertEqual(len(self.calls), 6)
        self.assertEqual(result['status'], 'PENDING')
        self.assertEqual(result['terminal_preservation'], 'PENDING')

    def test_actual_actor_parses_real_client_envelope_and_exact_error_before_caller_assertions(self):
        actor = self.ns['Actor'].__new__(self.ns['Actor'])
        actor.revision = 1
        for failure in ('none', 'type', 'arguments', 'format', 'auth'):
            def wire(request):
                sent = json.loads(request.data)
                body = {'jsonrpc': '2.0', 'id': sent['id'], 'error': {'data': {
                    'name': 'odoo.exceptions.AccessError', 'arguments': ['Audit events cannot be changed.']}}}
                if failure == 'type': body['error']['data']['name'] = 'odoo.exceptions.UserError'
                if failure == 'arguments': body['error']['data']['arguments'] = ['synthetic mismatch']
                if failure == 'format': body.pop('jsonrpc')
                if failure == 'auth': body['error']['data']['name'] = 'odoo.exceptions.AccessDenied'
                return FakeResponse(json.dumps(body).encode(), 403 if failure == 'auth' else 200)
            opener = FakeOpener(wire)
            actor.client = http.Client('http://127.0.0.1:18410', database='ydental_s10_test_20990101000000_abcdef12',
                owned_targets={'ydental_s10_test_20990101000000_abcdef12': 'http://127.0.0.1:18410'}, budget=FakeBudget(),
                directory=self.directory / ('wire-' + failure), opener=opener)
            row = actor.rpc_observed('ydental.access.audit', 'write', [[103], {'ydental_reason': 'LC2 denied tampering'}],
                                      operation_ref='B-pre.B-RPC-3-write')
            with self.subTest(failure=failure):
                self.assertEqual(len(opener.requests), 1)
                self.assertEqual(row['dispatch_state'], 'RESPONSE_RECEIVED')
                if failure == 'none':
                    self.assertEqual(row['native_error_name'], 'odoo.exceptions.AccessError')
                    self.assertTrue(row['native_public_arguments_exact_expected'])
                elif failure == 'arguments': self.assertFalse(row['native_public_arguments_exact_expected'])
                elif failure == 'format': self.assertFalse(row['response_format_valid'])
                else: self.assertNotEqual(row['native_error_name'], 'odoo.exceptions.AccessError')

    def test_actual_actor_uses_real_client_pre_rejection_vs_open_unknown(self):
        native_actor = self.ns['Actor'].__new__(self.ns['Actor'])
        native_actor.revision = 1
        for phase in ('budget', 'callback', 'open'):
            target = self.directory / phase
            budget = FakeBudget(RuntimeError('synthetic stopped budget')) if phase == 'budget' else FakeBudget()
            opener = FakeOpener(URLError('synthetic disconnect'))
            client = http.Client('http://127.0.0.1:18410', database='ydental_s10_test_20990101000000_abcdef12',
                owned_targets={'ydental_s10_test_20990101000000_abcdef12': 'http://127.0.0.1:18410'},
                budget=budget, directory=target, opener=opener)
            native_actor.client = client
            if phase == 'callback':
                original_rpc = client.rpc
                def fail_callback(*args, **kwargs):
                    kwargs['dispatch_observer'] = lambda metadata: (_ for _ in ()).throw(RuntimeError('synthetic local observer failure'))
                    return original_rpc(*args, **kwargs)
                client.rpc = fail_callback
            observed = native_actor.rpc_observed('ydental.access.audit', 'write', [[103], {'ydental_reason': 'LC2 denied tampering'}], operation_ref='B-pre.B-RPC-3-write')
            with self.subTest(phase=phase):
                self.assertEqual(observed['dispatch_state'], 'UNKNOWN' if phase == 'open' else 'NOT_SENT')
                self.assertEqual(len(opener.requests), 1 if phase == 'open' else 0)


class ActualHTTPDispatchBoundary(PureBoundaryCase):
    def client(self, *, response=None, budget=None):
        self.opener = FakeOpener(response or FakeResponse())
        self.budget = budget or FakeBudget()
        return http.Client('http://127.0.0.1:18410',
            database='ydental_s10_test_20990101000000_abcdef12',
            owned_targets={'ydental_s10_test_20990101000000_abcdef12': 'http://127.0.0.1:18410'},
            budget=self.budget, directory=self.directory, opener=self.opener)

    def rpc(self, client, callback):
        return client.rpc('ydental.access.audit', 'write', [[99], {'ydental_reason': 'synthetic'}],
            case_id='B-RPC-6', operation_ref='B-pre.B-audit-write', dispatch_observer=callback)

    def test_actual_client_callback_after_budget_and_intent_before_open(self):
        client = self.client()
        observed = []
        def callback(metadata):
            self.assertEqual(self.budget.intents, ['http'])
            self.assertEqual(len(list(self.directory.glob('*-intent.public.json'))), 1)
            self.assertEqual(self.opener.requests, [])
            observed.append(metadata)
        response = self.rpc(client, callback)
        self.assertEqual(len(observed), 1)
        self.assertEqual(response.request_id, observed[0]['request_id'])
        self.assertEqual(len(self.opener.requests), 1)
        self.assertEqual(response.commit_observation, 'NOT_OBSERVED')

    def test_actual_client_budget_and_path_failure_do_not_notify_or_open(self):
        client = self.client(budget=FakeBudget(RuntimeError('synthetic budget STOP')))
        observed = []
        with self.assertRaises(RuntimeError):
            self.rpc(client, observed.append)
        self.assertEqual(observed, [])
        self.assertEqual(self.opener.requests, [])
        with self.assertRaises(ValueError):
            client.request('POST', 'http://127.0.0.1:18411/web/dataset/call_kw',
                json_body={}, case_id='B-RPC-6', dispatch_observer=observed.append)
        self.assertEqual(observed, [])
        self.assertEqual(self.opener.requests, [])

    def test_actual_old_main_a_client_boundary_rejects_b_before_budget_or_open(self):
        from s10_lc2_task_profile import MAIN_A_ORIGINAL_UI
        profile = SimpleNamespace(message_id=MAIN_A_ORIGINAL_UI, verify=lambda: None,
                                  validate_target=lambda *args: None)
        opener = FakeOpener(FakeResponse())
        budget = FakeBudget(profile=profile)
        client = http.Client('http://127.0.0.1:18410', database=MAIN, owned_targets={MAIN: 'http://127.0.0.1:18410'},
            budget=budget, directory=self.directory / 'legacy-main-a', opener=opener)
        observed = []
        with self.assertRaises(ValueError): self.rpc(client, observed.append)
        self.assertEqual(observed, [])
        self.assertEqual(budget.intents, [])
        self.assertEqual(opener.requests, [])

    def test_actual_client_intent_save_failure_is_not_sent(self):
        client = self.client()
        observed = []
        original = http.save_once
        def save(path, value):
            if str(path).endswith('-intent.public.json'):
                raise OSError('synthetic evidence failure')
            return original(path, value)
        with patch.object(http, 'save_once', side_effect=save), self.assertRaises(OSError):
            self.rpc(client, observed.append)
        self.assertEqual(observed, [])
        self.assertEqual(self.opener.requests, [])

    def test_actual_client_callback_failure_is_explicit_not_sent(self):
        client = self.client()
        def callback(metadata):
            raise RuntimeError('synthetic observer failure')
        with self.assertRaises(http.RequestNotSent):
            self.rpc(client, callback)
        self.assertEqual(len(self.opener.requests), 0)

    def test_actual_client_open_unknown_is_one_attempt_without_retry(self):
        client = self.client(response=URLError('synthetic disconnect'))
        observed = []
        response = self.rpc(client, observed.append)
        self.assertEqual(response.transport_outcome, 'DISCONNECTED')
        self.assertEqual(response.commit_observation, 'UNKNOWN')
        with self.assertRaises(http.OutcomeUnknown): response.json()
        self.assertEqual(len(observed), 1)
        self.assertEqual(len(self.opener.requests), 1)
        outcomes = [json.loads(path.read_bytes()) for path in self.directory.glob('*-outcome.public.json')]
        self.assertEqual(outcomes[0]['commit_observation'], 'UNKNOWN')


SyntheticAccessError = type('AccessError', (Exception,), {'__module__': 'odoo.exceptions'})


class SyntheticClock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2099, 1, 1, tzinfo=tz)


class SyntheticCursor:
    def __init__(self, *, restore=True):
        self.version = 0
        self.savepoint_rollbacks = 0
        self.outer_rollbacks = 0
        self.commits = 0
        self.restore = restore
        self.closed = False

    def __enter__(self): return self

    def __exit__(self, *args): self.closed = True

    def savepoint(self):
        previous = self.version
        cursor = self
        class Point:
            def close(self):
                cursor.savepoint_rollbacks += 1
                if cursor.restore: cursor.version = previous
        return Point()

    def rollback(self): self.outer_rollbacks += 1

    def commit(self):
        self.commits += 1
        raise AssertionError('B_MUST_NOT_COMMIT')


class SyntheticEnvironment:
    def __init__(self, cursor, uid, context, *, failure=None, fail_at=1):
        self.cr, self.uid, self.su = cursor, uid, False
        self.context = context
        self.transaction = SimpleNamespace(default_env=self)
        self.user = SimpleNamespace(active=True, _is_internal=lambda: True, has_group=lambda group: True)
        self.failure, self.fail_at, self.calls = failure, fail_at, []
        self.admin = self.system = False

    def is_admin(self): return self.admin

    def is_system(self): return self.system

    def __getitem__(self, model):
        env = self
        class Record:
            def __init__(self): self.env = env
            def browse(self, record_id):
                self.record_id = record_id
                return self
            def execute(self, method, values=None):
                env.calls.append((model, method, self.record_id, values))
                env.cr.version += 1  # proves the explicit savepoint fake restores state.
                if len(env.calls) == env.fail_at:
                    if env.failure == 'return': return True
                    if env.failure == 'type': raise ValueError('synthetic unexpected private message')
                    if env.failure == 'arguments': raise SyntheticAccessError('synthetic wrong public args')
                    if env.failure == 'subclass':
                        error_type = type('DerivedAccessError', (SyntheticAccessError,), {'__module__': 'odoo.exceptions'})
                        raise error_type('synthetic wrong exact class')
                message = actual_definitions(CASES, ['_b_message'])['_b_message'](model, method)
                raise SyntheticAccessError(message)
            def write(self, values): return self.execute('write', values)
            def unlink(self): return self.execute('unlink')
        return Record()


def model_namespace(manifest):
    def row_sha(env, table, record_id):
        if record_id not in {target['id'] for target in manifest['targets']}:
            raise RuntimeError('SYNTHETIC_NONEMPTY_TARGET_MISSING')
        return hashlib.sha256(str(env.cr.version).encode()).hexdigest()
    return actual_definitions(FIXTURE, ['_ordinary_actor', '_model_denials'],
        _TARGETS=literal(FIXTURE, '_TARGETS'), AccessError=SyntheticAccessError, closing=closing,
        datetime=SyntheticClock, _guard=lambda *args: manifest['identity'] | {'core': 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'},
        _row_sha=row_sha)


class ActualModelHelper(PureBoundaryCase):
    def setUp(self):
        super().setUp()
        self.manifest = synthetic_manifest()
        self.ns = model_namespace(self.manifest)
        self.saved = []

    def probe(self, env=None, **kwargs):
        self.env = env or SyntheticEnvironment(SyntheticCursor(), 16, {})
        return self.ns['_model_denials'](self.env, uid=16, targets=kwargs.pop('targets', self.manifest['targets']),
            run_directory=str(self.directory), observe=lambda row: self.saved.append(copy.deepcopy(row)), **kwargs)

    def test_actual_helper_six_exact_native_errors_real_env_observations_and_rollback(self):
        result = self.probe()
        self.assertTrue(result['six_denied'])
        self.assertEqual(len(self.saved), 6)
        self.assertEqual(self.env.cr.savepoint_rollbacks, 6)
        self.assertEqual(self.env.cr.version, 0)
        self.assertEqual(self.env.cr.commits, 0)
        for row in self.saved:
            self.assertEqual(row['actor_id'], self.env.uid)
            self.assertEqual(row['default_env_uid'], self.env.transaction.default_env.uid)
            self.assertFalse(row['su_flag'])
            self.assertFalse(row['default_env_su'])
            self.assertFalse(row['is_admin'])
            self.assertFalse(row['is_system'])
            self.assertEqual(row['exception_name'], 'odoo.exceptions.AccessError')
            self.assertTrue(row['native_public_arguments_exact_expected'])
            self.assertEqual(row['existing_target_sha256'], row['after_sha256'])
            self.assertEqual(row['independent_preservation'], 'PENDING')

    def test_actual_helper_wrong_class_args_unexpected_error_or_no_error_saved_before_failure(self):
        for failure in ('subclass', 'arguments', 'type', 'return'):
            self.saved = []
            env = SyntheticEnvironment(SyntheticCursor(), 16, {}, failure=failure)
            with self.subTest(failure=failure), self.assertRaises(RuntimeError): self.probe(env)
            self.assertEqual(len(self.saved), 1)
            self.assertFalse(self.saved[0]['native_public_arguments_exact_expected'])
            self.assertEqual(env.cr.savepoint_rollbacks, 1)
            self.assertNotIn('synthetic unexpected private message', json.dumps(self.saved))

    def test_actual_helper_partial_failure_keeps_earlier_and_failed_case_observations(self):
        env = SyntheticEnvironment(SyntheticCursor(), 16, {}, failure='arguments', fail_at=3)
        with self.assertRaises(RuntimeError): self.probe(env)
        self.assertEqual(len(self.saved), 3)
        self.assertTrue(all(row['native_public_arguments_exact_expected'] for row in self.saved[:2]))
        self.assertFalse(self.saved[2]['native_public_arguments_exact_expected'])
        self.assertEqual(env.cr.savepoint_rollbacks, 3)

    def test_actual_helper_drift_is_saved_before_integrity_assertion(self):
        env = SyntheticEnvironment(SyntheticCursor(restore=False), 16, {})
        with self.assertRaises(RuntimeError): self.probe(env)
        self.assertEqual(len(self.saved), 1)
        self.assertNotEqual(self.saved[0]['existing_target_sha256'], self.saved[0]['after_sha256'])

    def test_actual_helper_su_defaultenv_missing_target_or_bad_values_refused(self):
        for invalid in ('uid', 'su', 'default_su', 'target', 'values'):
            env = SyntheticEnvironment(SyntheticCursor(), 16, {})
            targets = copy.deepcopy(self.manifest['targets'])
            if invalid == 'uid': env.uid = 1
            if invalid == 'su': env.su = True
            if invalid == 'default_su': env.transaction.default_env = SimpleNamespace(uid=16, su=True)
            if invalid == 'target': targets[0]['id'] = 999
            if invalid == 'values': targets[0]['values'] = {}
            with self.subTest(invalid=invalid), self.assertRaises((RuntimeError, ValueError)):
                self.probe(env, targets=targets)
            self.assertEqual(env.calls, [])


class ActualFixtureDispatch(PureBoundaryCase):
    def test_actual_main_b_only_dispatch_early_branch_no_other_fixture_or_commit(self):
        manifest = synthetic_manifest()
        observations, environments, scopes = [], [], []
        cursor = SyntheticCursor()
        registry = SimpleNamespace(cursor=lambda: cursor)
        def environment(cr, uid, context):
            env = SyntheticEnvironment(cr, uid, context)
            environments.append(env)
            return env
        @contextmanager
        def scope(**values):
            scopes.append(values)
            yield
        helper = model_namespace(manifest)
        def forbidden(*args, **kwargs): raise AssertionError('UNRELATED_FIXTURE_ACTION')
        fake_fixture_module = SimpleNamespace(_guard=helper['_guard'], _model_denials=helper['_model_denials'],
            _create_reader=forbidden, _initialize_reader_password=forbidden, _limited_token=forbidden)
        def imports(name, *args, **kwargs):
            if name == 'odoo': return SimpleNamespace(Command=object, api=SimpleNamespace(Environment=environment))
            if name == 'odoo.addons.ydental_access.diagnostics': return SimpleNamespace(context_scope=scope)
            if name == 'odoo.addons.ydental_settlement_test.models.lc2_fixture': return fake_fixture_module
            if name == 'logging': return SimpleNamespace(CRITICAL=50, getLogger=lambda name: SimpleNamespace(getEffectiveLevel=lambda: 50))
            raise AssertionError('REAL_APPLICATION_IMPORT_FORBIDDEN:' + name)
        fake_builtins = dict(vars(builtins), __import__=imports)
        ns = actual_definitions(FIXTURE_PROCESS, ['main', 'run_b_model_only', '_save_b_model_observation'],
            os=os, stat=stat, __builtins__=fake_builtins)
        (self.directory / 'diagnostics').mkdir(mode=0o700)
        input_read, input_write = os.pipe()
        output_read, output_write = os.pipe()
        try:
            os.write(input_write, json.dumps({'mode': 'main-b-only', 'manifest': manifest}).encode())
            os.close(input_write)
            with patch.dict(os.environ, {'YDENTAL_S10_RUN_DIR': str(self.directory),
                    'YDENTAL_LC2_INPUT_FD': str(input_read), 'YDENTAL_LC2_OUTPUT_FD': str(output_write)}):
                ns['main'](SimpleNamespace(cr=SimpleNamespace(dbname=MAIN), registry=registry))
            raw = os.read(output_read, 65537)
            response = json.loads(raw)
        finally:
            for fd in (input_read, input_write, output_read, output_write):
                try: os.close(fd)
                except OSError: pass
        self.assertEqual(len(environments), 1)
        self.assertEqual(environments[0].uid, 16)
        self.assertEqual(len(environments[0].calls), 6)
        self.assertEqual(cursor.outer_rollbacks, 1)
        self.assertEqual(cursor.commits, 0)
        self.assertTrue(cursor.closed)
        self.assertEqual(response['safe']['fixture_commits'], 0)
        self.assertEqual(response['ram'], {})
        self.assertEqual(scopes[0]['case_id'], 'B-MODEL-6')
        self.assertEqual(len(list((self.directory / 'diagnostics').glob('*-observation.json'))), 6)


if __name__ == '__main__':
    unittest.main()
