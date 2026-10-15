"""SIMULATED: exercise actual R1/R2 create/dispatch and R2 durable stage gates."""
from contextlib import contextmanager, redirect_stdout
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import importlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
R1 = importlib.import_module('s10_ui1_r1_control')
R2 = importlib.import_module('s10_ui1_r2_control')
from s10_ui1_r2_evidence import read_complete, write_once
from s10_ui1_r2_contract import baseline_record

checks = []

class FakeSocket:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def bind(self, address):
        assert address[0] == '127.0.0.1'

class FakeCursor:
    def __init__(self, state): self.state = state
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def execute(self, query):
        assert str(query).startswith('Composed(')
        self.state['create_calls'] += 1
        if self.state.get('create_failure'):
            raise RuntimeError('SIMULATED CREATE rejected')
        self.state['created'] = True

class FakeConnection:
    def __init__(self, state, module):
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status': module.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
        self.state = state
    def cursor(self): return FakeCursor(self.state)
    def close(self): pass

@contextmanager
def sandbox(module, root, *, corrupt_source=False, create_failure=False, oid_mismatch=False):
    name = module.NAME
    source_run = root / 'source'
    source_fs = source_run / 'data/filestore' / module.SOURCE
    source_fs.mkdir(parents=True)
    files = {'alpha': b'nonempty source alpha', 'sub/beta': b'nonempty source beta'}
    expected = {}
    for rel, data in files.items():
        path = source_fs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        expected[rel] = {'sha256': hashlib.sha256(data).hexdigest()}
    if corrupt_source:
        (source_fs / 'alpha').write_bytes(b'changed after index')
    local = root / '.local'
    local.mkdir()
    run = local / name
    state = {'created': False, 'create_calls': 0, 'identity_after_calls': 0,
             'create_failure': create_failure}
    def fake_identity(expect_target=False):
        if expect_target:
            assert state['created'], 'target must actually exist'
            state['identity_after_calls'] += 1
            oid = 314159 if oid_mismatch and state['identity_after_calls'] > 1 else 271828
        else:
            assert not state['created'], 'source-only identity required'
            oid = None
        return {'password': 'SIMULATED_ONLY'}, expected, oid
    changes = {'ROOT': root, 'SOURCE_RUN': source_run, 'RUN': run,
               'identity': fake_identity}
    with patch.multiple(module, **changes), \
         patch.object(module.socket, 'socket', return_value=FakeSocket()), \
         patch.object(module.psycopg2, 'connect', side_effect=lambda **kw: FakeConnection(state, module)):
        yield run, state, files

with tempfile.TemporaryDirectory(prefix='ui1-r2-flow-') as base:
    base = Path(base)
    with sandbox(R1, base / 'r1') as (run, state, files):
        try:
            with redirect_stdout(io.StringIO()): R1.COMMANDS['create']()
        except TypeError as exc:
            assert 'PosixPath' in str(exc) or 'WindowsPath' in str(exc), str(exc)
        else:
            raise AssertionError('Old R1 create unexpectedly passed')
        assert state['create_calls'] == 1 and state['created']
        assert (run / 'database.json').exists() and (run / 'odoo.conf').exists()
        assert state['identity_after_calls'] == 1
        checks.append('old_r1_actual_create_exposes_shadow_TypeError')

    with sandbox(R2, base / 'success') as (run, state, files):
        with redirect_stdout(io.StringIO()): R2.dispatch('create')
        assert state['create_calls'] == 1 and state['identity_after_calls'] == 2
        assert all((run / 'data/filestore' / R2.NAME / rel).read_bytes() == data
                   for rel, data in files.items())
        assert R2.target() == 271828
        with redirect_stdout(io.StringIO()):
            assert R2.dispatch('verify-target') is None
        assert read_complete(run / 'database.json')['oid'] == 271828
        assert read_complete(run / 'create-sql-committed.json')['phase'] == 'CREATE_SUCCEEDED'
        assert read_complete(run / 'create-complete.json')['phase'] == 'VERIFIED'
        assert (run / 'odoo.conf').stat().st_size > 100
        checks.append('r2_actual_dispatch_create_copy_fake_create_marker_adapter_tail_return')
        try:
            R2.dispatch('create')
        except (AssertionError, FileExistsError):
            assert state['create_calls'] == 1
            checks.append('one_time_cli_repeat_rejected_before_create')
        else: raise AssertionError('repeat create accepted')
        try: R2.dispatch('unknown')
        except ValueError: checks.append('unknown_cli_rejected')
        else: raise AssertionError('unknown CLI accepted')

    for label, flags, expected_calls, marker_expected in (
        ('copy_hash_failure', {'corrupt_source': True}, 0, False),
        ('create_failure', {'create_failure': True}, 1, False),
        ('postcreate_oid_validation_failure', {'oid_mismatch': True}, 1, True),
    ):
        with sandbox(R2, base / label, **flags) as (run, state, files):
            try:
                with redirect_stdout(io.StringIO()): R2.dispatch('create')
            except (AssertionError, RuntimeError, ValueError): pass
            else: raise AssertionError(label + ' accepted')
            assert state['create_calls'] == expected_calls
            assert (run / 'database.json').exists() is marker_expected
            assert not (run / 'create-complete.json').exists()
            assert (run / 'create-sql-committed.json').exists() is (label == 'postcreate_oid_validation_failure')
            checks.append(label + '_fails_closed')

    typed = {'today': date(2026, 10, 15),
             'instant': datetime(2026, 10, 15, 1, 35, 45, 123456, tzinfo=timezone.utc),
             'amount': Decimal('123456789.0000012300'),
             'nested': [{'due': date(2026, 11, 1), 'amounts': [Decimal('0.10'), Decimal('0.20')]}]}
    evidence = base / 'typed.json'
    write_once(evidence, typed)
    assert read_complete(evidence) == typed
    assert read_complete(evidence)['amount'].as_tuple() == typed['amount'].as_tuple()
    checks.append('typed_date_datetime_decimal_nested_exact_readback')
    with patch('s10_ui1_r2_evidence.os.replace', side_effect=OSError('SIMULATED publish failure')):
        try: write_once(base / 'partial.json', typed)
        except OSError: pass
        else: raise AssertionError('partial publish accepted')
    assert not (base / 'partial.json').exists()
    assert not (base / 'partial.json.partial').exists()
    checks.append('failed_partial_evidence_not_success')

    # Stage checks use the real R2 gate functions and completed marker/adapter.
    with sandbox(R2, base / 'gates') as (run, state, files):
        with redirect_stdout(io.StringIO()): R2.dispatch('create')
        with patch.object(R2, 'bounded', side_effect=RuntimeError('SIMULATED prepare boundary')):
            try: R2.dispatch('prepare')
            except RuntimeError as exc: assert 'prepare boundary' in str(exc)
            else: raise AssertionError('prepare CLI did not reach bounded process')
        try: R2.dispatch('serve-before')
        except (ValueError, FileNotFoundError): pass
        else: raise AssertionError('missing prepare result admitted to HTTP')
        checks.append('actual_cli_prepare_boundary_and_failed_prepare_blocks_http')
        good = {'pid': 123, 'exit_code': 0, 'signal11': False, 'timed_out': False,
                'oid': 271828, 'config_sha256': R2.digest(run / 'odoo.conf'),
                'log_sha256': 'a'*64, 'log_bytes': 1}
        before = run / 'prepare-attempt.json.result'
        for change in ({'exit_code': 1}, {'signal11': True}, {'timed_out': True},
                       {'oid': 999}, {'config_sha256': 'b'*64}):
            write_once(before, dict(good, **change))
            try: R2.successful_result(before.name)
            except (AssertionError, ValueError): pass
            else: raise AssertionError('bad prepare admitted ' + str(change))
            before.unlink()
        # A present but malformed/partial result cannot release a later stage.
        before.write_text('{')
        try: R2.serve('before')
        except (ValueError, json.JSONDecodeError): pass
        else: raise AssertionError('malformed prepare admitted')
        before.unlink()
        write_once(before, good)
        assert R2.successful_result(before.name) == good
        checks.append('prepare_exit_signal_timeout_identity_and_partial_gate')

        proof = {'complete': True, 'classification': 'REPRODUCED_JSON_NAVIGATION',
                 'reproduced': True, 'oid': 271828, 'finance_verified': True,
                 'request_content_type': 'application/x-www-form-urlencoded',
                 'content_type': 'application/json; charset=utf-8',
                 'page_path': '/ydental/settlement/action'}
        for bad in ({'complete': False}, {'finance_verified': False}, {'oid': 99},
                    {'classification': 'NOT_REPRODUCED_WORKBENCH'}):
            write_once(run / 'baseline-proved.json', dict(proof, **bad))
            try: R2.baseline_proof()
            except (AssertionError, ValueError): pass
            else: raise AssertionError('bad baseline admitted ' + str(bad))
            (run / 'baseline-proved.json').unlink()
        write_once(run / 'baseline-proved.json', proof)
        assert R2.baseline_proof() == proof
        checks.append('baseline_complete_semantics_and_finance_gate')

        write_once(run / 'http-before.result.json', dict(good, exit_code=1))
        try: R2.upgrade()
        except (AssertionError, ValueError): pass
        else: raise AssertionError('abnormal HTTP admitted to upgrade')
        (run / 'http-before.result.json').unlink()
        write_once(run / 'http-before.result.json', dict(good, exit_code=-2))
        # Intercept only the external subprocess boundary after checking the real gate.
        with patch.object(R2, 'bounded', side_effect=RuntimeError('SIMULATED subprocess boundary')):
            try: R2.upgrade()
            except RuntimeError as exc: assert 'subprocess boundary' in str(exc)
            else: raise AssertionError('valid upgrade gate did not reach boundary')
        checks.append('before_http_exit_gate_and_valid_upgrade_dispatch')

        write_once(run / 'upgrade-attempt.json.result', dict(good, signal11=True))
        try: R2.serve('after')
        except (AssertionError, ValueError): pass
        else: raise AssertionError('failed upgrade admitted after HTTP')
        (run / 'upgrade-attempt.json.result').unlink()
        write_once(run / 'upgrade-attempt.json.result', good)
        with patch.object(R2.subprocess, 'Popen', side_effect=RuntimeError('SIMULATED HTTP boundary')):
            try: R2.serve('after')
            except RuntimeError as exc: assert 'HTTP boundary' in str(exc)
            else: raise AssertionError('valid after gate did not reach boundary')
        checks.append('upgrade_failure_blocks_after_and_success_reaches_boundary')

    counts_before = {'ydental_settlement_receipt': 0, 'account_move': 0}
    counts_after = {'ydental_settlement_receipt': 1, 'account_move': 1}
    common = {'request_url': '/ydental/settlement/action',
              'request_content_type': 'application/x-www-form-urlencoded',
              'before': {'counts': counts_before}, 'after': {'counts': counts_after}}
    variants = (
        ('json', dict(status=200, response_content_type='application/json',
                      location=None, page_path='/ydental/settlement/action', has_workbench=False),
         {'result': 'accepted', 'amount': 100}, True),
        ('html', dict(status=200, response_content_type='text/html',
                      location=None, page_path='/ydental/settlement', has_workbench=True), None, False),
        ('303_workbench', dict(status=303, response_content_type='text/html',
                      location='/ydental/settlement', page_path='/ydental/settlement', has_workbench=True), None, False),
    )
    for label, observation, parsed, reproduced in variants:
        proof = baseline_record(dict(common, **observation), oid=271828, parsed_json=parsed)
        assert proof['reproduced'] is reproduced
        filename = 'baseline-proved.json' if reproduced else 'baseline-not-reproduced.json'
        location = base / label
        location.mkdir()
        write_once(location / filename, proof)
        assert read_complete(location / filename) == proof
        assert (location / 'baseline-proved.json').exists() is reproduced
        checks.append('browser_' + label + '_classify_record_and_continue_marker')
    bad = dict(common, status=303, response_content_type='text/html',
               location='/ydental/settlement', page_path='/ydental/settlement/action',
               has_workbench=False)
    try: baseline_record(bad, oid=271828)
    except ValueError: checks.append('redirect_header_without_landed_workbench_rejected')
    else: raise AssertionError('Location-only redirect accepted')
    try: baseline_record(dict(common, **variants[0][1], after={'counts': counts_before}),
                         oid=271828, parsed_json=variants[0][2])
    except ValueError: checks.append('browser_finance_failure_blocks_proof')
    else: raise AssertionError('finance-free response accepted')

print(json.dumps({'status': 'SIMULATED_PASS', 'checks': checks,
                  'actual_create_r1_and_r2': True, 'actual_cli_dispatch_r2': True,
                  'new_database_created': False, 'odoo_processes': 0, 'firefox_processes': 0},
                 ensure_ascii=False, indent=2))
