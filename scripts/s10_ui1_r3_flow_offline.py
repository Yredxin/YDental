"""SIMULATED R3 actual clone/dispatch with fake external dependencies."""

from contextlib import contextmanager, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_ui1_r3_control as control
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
        if self.state['create_failure']:
            raise RuntimeError('SIMULATED CREATE rejected')
        self.state['created'] = True

class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status':
            control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self): return FakeCursor(self.state)
    def close(self): pass

@contextmanager
def sandbox(root, *, corrupt_source=False, create_failure=False, oid_mismatch=False):
    root.mkdir()
    local = root / '.local'; local.mkdir()
    source_run = local / control.SOURCE
    source_fs = source_run / 'data/filestore' / control.SOURCE
    source_fs.mkdir(parents=True)
    files = {'alpha': b'nonempty inherited source', 'sub/beta': b'second inherited attachment'}
    expected = {}
    for rel, data in files.items():
        path = source_fs / rel; path.parent.mkdir(parents=True, exist_ok=True);path.write_bytes(data)
        expected[rel] = {'sha256': hashlib.sha256(data).hexdigest()}
    (source_run / 'fixture.json').write_text(json.dumps({'db': control.SOURCE,
        'oid': 2100240, 'fees': [1, 2], 'actors': {'manager': 5}}))
    if corrupt_source: (source_fs / 'alpha').write_bytes(b'changed after manifest')
    run = local / control.NAME
    state = {'created': False, 'create_calls': 0, 'postcalls': 0,
             'create_failure': create_failure}
    def identity(expect_target=False):
        if expect_target:
            assert state['created']
            state['postcalls'] += 1
            oid = 314159 if oid_mismatch and state['postcalls'] > 1 else 271828
        else:
            assert not state['created']
            oid = None
        return {'password': 'SIMULATED_ONLY'}, expected, oid
    changes = {'ROOT': root, 'SOURCE_RUN': source_run, 'RUN': run, 'identity': identity}
    with patch.multiple(control, **changes), \
         patch.object(control.socket, 'socket', return_value=FakeSocket()), \
         patch.object(control.psycopg2, 'connect', side_effect=lambda **kw: FakeConnection(state)):
        yield run, state, files

with tempfile.TemporaryDirectory(prefix='ui1-r3-flow-') as temp:
    base = Path(temp)
    with sandbox(base / 'success') as (run, state, files):
        with redirect_stdout(io.StringIO()): control.dispatch('create')
        assert state['create_calls'] == 1 and state['postcalls'] == 2
        assert read_complete(run / 'create-sql-committed.json')['phase'] == 'CREATE_SUCCEEDED'
        assert read_complete(run / 'create-complete.json')['phase'] == 'VERIFIED'
        assert all((run / 'data/filestore' / control.NAME / rel).read_bytes() == data
                   for rel,data in files.items())
        fixture = read_complete(run / 'fixture.json')
        assert fixture['db'] == control.NAME and fixture['oid'] == 271828
        assert fixture['inherited_from']['oid'] == 2100240
        with patch.object(control, 'assert_source_baseline', return_value={'fixture': True}), \
             patch.object(control, 'finance_snapshot', return_value={'fixture': True}):
            with redirect_stdout(io.StringIO()): control.dispatch('verify-target')
        checks.append('actual_create_copy_fake_sql_new_marker_new_fixture_tail_adapter_and_dispatch')
        try: control.dispatch('create')
        except (AssertionError, FileExistsError):
            assert state['create_calls'] == 1
        else: raise AssertionError('repeat CREATE allowed')
        checks.append('one_time_create_repeat_rejected')
        expected_options = {'db_name': [control.NAME], 'init': {}, 'update': {'ydental_settlement': True},
                            'test_enable': False, 'test_tags': None, 'test_file': '',
                            'http_enable': False, 'stop_after_init': True}
        proof = {'status': 'CLI_PARSE_PASS', 'mode': 'upgrade',
                 'argv': control.argv('upgrade'), 'config_sha256': control.digest(run / 'odoo.conf'),
                 'options': expected_options}
        write_once(run / 'cli-upgrade.json', proof)
        assert control.cli_proof('upgrade') == proof
        with patch.object(control, 'assert_source_baseline', return_value={'fixture': True}), \
             patch.object(control, 'finance_snapshot', return_value={'fixture': True}), \
             patch.object(control, 'bounded', side_effect=RuntimeError('SIMULATED Odoo boundary')):
            try: control.dispatch('upgrade')
            except RuntimeError as e: assert 'Odoo boundary' in str(e)
            else: raise AssertionError('upgrade did not reach bounded process')
        checks.append('real_upgrade_dispatch_checks_cli_and_finance_before_process')
        assert not (run / 'upgrade-complete.json').exists()
        try: control.dispatch('serve-after')
        except (ValueError, FileNotFoundError): pass
        else: raise AssertionError('HTTP admitted without upgrade complete')
        checks.append('failed_upgrade_blocks_http')
    for label, flags, calls, sql_marker in (
        ('copy_failure', {'corrupt_source': True}, 0, False),
        ('create_failure', {'create_failure': True}, 1, False),
        ('postcreate_identity_failure', {'oid_mismatch': True}, 1, True),
    ):
        with sandbox(base / label, **flags) as (run, state, files):
            try:
                with redirect_stdout(io.StringIO()): control.dispatch('create')
            except (AssertionError, RuntimeError, ValueError): pass
            else: raise AssertionError(label + ' accepted')
            assert state['create_calls'] == calls
            assert (run / 'create-sql-committed.json').exists() is sql_marker
            assert not (run / 'create-complete.json').exists()
            checks.append(label + '_fails_closed')

print(json.dumps({'status': 'SIMULATED_PASS', 'checks': checks,
                  'real_create_and_dispatch_called': True, 'new_database_created': False,
                  'odoo_processes': 0, 'browser_processes': 0}, indent=2))
