"""SIMULATED complete W1 create dispatch, copy and ordered process gates."""

from contextlib import contextmanager, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import s10_e2e_w1_control as control
from s10_e2e_w1_evidence import read_complete, write_once


class FakeSocket:
    def __enter__(self): return self
    def __exit__(self, *_args): return None
    def bind(self, address): assert address == ('127.0.0.1', control.PORT)


class FakeCursor:
    def __init__(self, state): self.state = state
    def __enter__(self): return self
    def __exit__(self, *_args): return None
    def execute(self, query):
        assert 'CREATE DATABASE' in str(query)
        self.state['calls'] += 1
        if self.state['create_failure']: raise RuntimeError('SIMULATED CREATE failure')
        self.state['created'] = True


class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status': control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self): return FakeCursor(self.state)
    def close(self): return None


@contextmanager
def sandbox(root, *, corrupt_source=False, create_failure=False, oid_mismatch=False):
    source = root / 'source' / 'data/filestore' / control.SOURCE
    source.mkdir(parents=True)
    files = {'alpha': b'nonempty synthetic source', 'deep/beta': b'another checked synthetic file'}
    expected = {}
    for rel, content in files.items():
        item = source / rel
        item.parent.mkdir(parents=True, exist_ok=True)
        item.write_bytes(content)
        expected[rel] = {'sha256': hashlib.sha256(content).hexdigest()}
    if corrupt_source: (source / 'alpha').write_bytes(b'corrupted')
    local = root / '.local'; local.mkdir()
    state = {'created':False, 'calls':0, 'create_failure':create_failure,
             'target_checks':0}
    def identity(expect_target=False):
        assert state['created'] == expect_target
        if expect_target:
            state['target_checks'] += 1
            oid = 4712 if oid_mismatch and state['target_checks'] > 1 else 4711
        else: oid = None
        return {'password':'SIMULATED_ONLY'}, expected, oid
    with patch.multiple(control, ROOT=root, SOURCE_RUN=source.parents[2], RUN=local / control.NAME,
                        identity=identity), \
         patch.object(control.socket, 'socket', return_value=FakeSocket()), \
         patch.object(control.psycopg2, 'connect', side_effect=lambda **_kw: FakeConnection(state)):
        yield local / control.NAME, state, files


def reject(call):
    try: call()
    except (AssertionError, RuntimeError, ValueError, FileExistsError, FileNotFoundError, json.JSONDecodeError):
        return
    raise AssertionError('Offline expected rejection was accepted')


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix='w1-control-offline-') as tmp:
        base = Path(tmp)
        with sandbox(base / 'success') as (run, state, files):
            with redirect_stdout(io.StringIO()): control.dispatch('create')
            assert state['calls'] == 1 and state['target_checks'] == 2
            assert all((run / 'data/filestore' / control.NAME / rel).read_bytes() == content
                       for rel, content in files.items())
            assert control.target() == 4711
            assert read_complete(run / 'create-complete.json')['phase'] == 'VERIFIED'
            assert read_complete(run / 'database.json')['source_oid'] == 2100080
            checks.append('actual_dispatch_copy_create_marker_adapter_return')
            reject(lambda: control.dispatch('create'))
            assert state['calls'] == 1
            reject(lambda: control.dispatch('unknown'))
            checks.append('one_time_create_and_unknown_command_rejected')
        for label, options, calls in (
            ('copy_failure', {'corrupt_source':True}, 0),
            ('create_failure', {'create_failure':True}, 1),
            ('post_create_identity_failure', {'oid_mismatch':True}, 1)):
            with sandbox(base / label, **options) as (run, state, _files):
                reject(lambda: control.dispatch('create'))
                assert state['calls'] == calls
                assert not (run / 'create-complete.json').exists()
                checks.append(label + '_stops')
        with sandbox(base / 'gates') as (run, state, _files):
            with redirect_stdout(io.StringIO()): control.dispatch('create')
            reject(lambda: control.dispatch('serve'))
            with patch.object(control, 'bounded', side_effect=RuntimeError('SIMULATED process')):
                reject(lambda: control.dispatch('prepare'))
            reject(lambda: control.dispatch('serve'))
            good = {'pid':111,'exit_code':0,'signal11':False,'timed_out':False,
                    'oid':4711,'config_sha256':control.digest(run / 'odoo.conf'),
                    'log_sha256':'a'*64,'log_bytes':1}
            path = run / 'prepare-attempt.json.result'
            for change in ({'exit_code':1},{'signal11':True},{'timed_out':True},
                           {'oid':17},{'config_sha256':'b'*64}):
                write_once(path, dict(good, **change))
                reject(lambda: control.dispatch('serve'))
                path.unlink()
            path.write_text('{')
            reject(lambda: control.dispatch('serve'))
            path.unlink()
            write_once(path, good)
            with patch.object(control.subprocess, 'Popen', side_effect=RuntimeError('SIMULATED HTTP launch')):
                reject(lambda: control.dispatch('serve'))
            checks.append('prepare_exit_signal_timeout_identity_and_partial_gate')
        assert control.COMMANDS.keys() == {'preflight','create','verify-target',
                                           'prepare','serve','wait-http','stop'}
        checks.append('exact_cli_dispatch_and_no_upgrade')
    print(json.dumps({'status':'SIMULATED_PASS','checks':checks}))


if __name__ == '__main__': main()
