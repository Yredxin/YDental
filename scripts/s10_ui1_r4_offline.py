"""SIMULATED full R4 CREATE/CLI and PDF response contract checks."""

from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_ui1_r4_control as control
from s10_ui1_r4_pdf_contract import classify_pdf_response
from s10_ui1_r2_evidence import read_complete, write_once

checks = []


class FakeSocket:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def bind(self, address): assert address == ('127.0.0.1', control.PORT)


class FakeCursor:
    def __init__(self, state): self.state = state
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def execute(self, query):
        assert 'CREATE DATABASE' in str(query)
        self.state['create_calls'] += 1
        if self.state['fail_create']:
            raise RuntimeError('SIMULATED CREATE failure')
        self.state['created'] = True


class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status':
            control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self): return FakeCursor(self.state)
    def close(self): pass


def sandbox(root, *, fail_copy=False, fail_create=False, bad_oid=False):
    root.mkdir()
    local = root / '.local'; local.mkdir()
    source_run = local / control.SOURCE
    source_fs = source_run / 'data/filestore' / control.SOURCE
    source_fs.mkdir(parents=True)
    data = {'alpha': b'nonempty R3 source', 'folder/beta': b'second nonempty file'}
    expected = {}
    for rel, raw in data.items():
        path = source_fs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected[rel] = {'sha256': hashlib.sha256(raw).hexdigest()}
    (source_run / 'fixture.json').write_text(json.dumps({'db': control.SOURCE,
        'oid': 2100256, 'fees': [1, 2], 'actors': {'frontdesk': 6}}))
    if fail_copy:
        (source_fs / 'alpha').write_bytes(b'changed after manifest')
    run = local / control.NAME
    state = {'created': False, 'create_calls': 0, 'postcalls': 0,
             'fail_create': fail_create}

    def identity(expect_target=False):
        if expect_target:
            assert state['created']
            state['postcalls'] += 1
            oid = 314159 if bad_oid and state['postcalls'] > 1 else 271828
        else:
            assert not state['created']
            oid = None
        return {'password': 'SIMULATED_ONLY'}, expected, oid

    return source_run, run, state, data, identity


def run_case(root, **flags):
    source_run, run, state, files, identity = sandbox(root, **flags)
    with patch.multiple(control, ROOT=root, SOURCE_RUN=source_run, RUN=run, identity=identity), \
         patch.object(control.socket, 'socket', return_value=FakeSocket()), \
         patch.object(control.psycopg2, 'connect', side_effect=lambda **kw: FakeConnection(state)):
        if flags:
            try:
                with redirect_stdout(io.StringIO()): control.dispatch('create')
            except (AssertionError, RuntimeError, ValueError):
                pass
            else:
                raise AssertionError('Expected CREATE failure did not occur')
            assert not (run / 'create-complete.json').exists()
            expected_calls = 0 if flags.get('fail_copy') else 1
            assert state['create_calls'] == expected_calls
            checks.append('actual_create_' + next(iter(flags)) + '_fails_closed')
            return
        with redirect_stdout(io.StringIO()): control.dispatch('create')
        assert state['create_calls'] == 1 and state['postcalls'] == 2
        assert all((run / 'data/filestore' / control.NAME / rel).read_bytes() == raw
                   for rel, raw in files.items())
        assert read_complete(run / 'create-complete.json')['phase'] == 'VERIFIED'
        fixture = read_complete(run / 'fixture.json')
        assert fixture['db'] == control.NAME and fixture['oid'] == 271828
        assert fixture['inherited_from']['oid'] == 2100256
        with patch.object(control, 'assert_source_baseline', return_value={'finance': True}), \
             patch.object(control, 'finance_snapshot', return_value={'finance': True}), \
             patch.object(control, 'qweb_loaded', return_value=True):
            with redirect_stdout(io.StringIO()): control.dispatch('verify-target')
        checks.append('actual_create_copy_fake_sql_marker_adapter_tail_and_cli_dispatch')
        try: control.dispatch('create')
        except (AssertionError, FileExistsError): pass
        else: raise AssertionError('repeat CREATE was allowed')
        assert state['create_calls'] == 1
        checks.append('one_time_create_repeat_rejected')
        with patch.object(control, 'inherited_baseline', side_effect=RuntimeError('bad inherited finance')):
            try: control.dispatch('serve')
            except RuntimeError: pass
            else: raise AssertionError('HTTP admitted after bad finance')
        assert not (run / 'http-r4.attempt.json').exists()
        checks.append('finance_failure_blocks_http')
        with patch.object(control, 'inherited_baseline', return_value={'finance': True}), \
             patch.object(control, 'qweb_loaded', return_value=False):
            try: control.dispatch('serve')
            except AssertionError: pass
            else: raise AssertionError('HTTP admitted before candidate QWeb')
        assert not (run / 'http-r4.attempt.json').exists()
        checks.append('qweb_failure_blocks_http')
        try: control.dispatch('unknown')
        except ValueError: pass
        else: raise AssertionError('unknown CLI admitted')
        checks.append('unknown_cli_rejected')


with tempfile.TemporaryDirectory(prefix='ui1-r4-flow-') as temp:
    root = Path(temp)
    run_case(root / 'success')
    run_case(root / 'copy', fail_copy=True)
    run_case(root / 'sql', fail_create=True)
    run_case(root / 'oid', bad_oid=True)
    typed = {'date': date(2026, 10, 15), 'at': datetime(2026, 10, 15, tzinfo=timezone.utc),
             'nested': {'amount': Decimal('60.00'), 'part': Decimal('0.0001')}}
    path = root / 'typed.json'
    write_once(path, typed)
    assert read_complete(path) == typed
    try: write_once(path, {'false_success': True})
    except FileExistsError: pass
    else: raise AssertionError('Evidence overwrite allowed')
    checks.append('typed_date_datetime_decimal_exact_roundtrip_and_no_overwrite')

assert classify_pdf_response(200, 'application/pdf', b'') == 'PDF_200'
assert classify_pdf_response(403, 'application/json', b'{"error":"access_denied: no export"}') == 'ACCESS_DENIED'
assert classify_pdf_response(409, 'application/json; charset=utf-8',
    b'{"error":"Unable to find the pdf engine on this system. The PDF can not be created."}') == 'RENDERER_ONLY_ERROR'
assert classify_pdf_response(409, 'application/json',
    b'{"error":"render_failed: Settlement PDF could not be generated."}') == 'RENDER_FAILED_UNATTRIBUTED'
assert classify_pdf_response(409, 'text/html', b'<html>error</html>') == 'UNKNOWN_RESPONSE'
assert classify_pdf_response(409, 'application/json', b'{"error":"version_conflict: changed"}') == 'SCOPE_OR_VERSION_CONFLICT'
checks.append('actual_pdf_200_403_409_renderer_unknown_scope_classification')

print(json.dumps({'status': 'SIMULATED_PASS', 'checks': checks,
                  'actual_create_and_dispatch_called': True, 'new_databases_created': 0,
                  'odoo_processes': 0, 'firefox_processes': 0}, indent=2))
