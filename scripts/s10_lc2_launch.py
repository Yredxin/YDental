"""Owned LC2 application launch with fresh identity, fixed candidate and raw limits."""
import argparse
import configparser
import hashlib
import json
from datetime import datetime, timezone
import os
from pathlib import Path
import socket
import stat
import subprocess
import time
import uuid

from s10_lc2_evidence import CLUSTER, CORE, runtime_gate, save_once, target_guard
from s10_lc2_logging import strict_loads
from s10_lc2_supervisor import append_plain, private_file, safe_plain, save_primary, launch
from s10_lc2_targets import (EXEC_ROOT, LEGACY_EXEC_ROOT, PLAN, RUN_ROOT, PackageBudget,
                            bind_dispatch_owner, release_dispatch_owner, freeze_dispatch,
                            require_dispatch_unfrozen)
from s10_lc2_process_guard import ObservationBlocked, ProcessLogGuard

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT.parent / '.venv/bin/python'
STOP = EXEC_ROOT / 'HARD-STOP.json'
ACTION_ROLES = {'scratch-tests': 'scratch', 'upgrade': 'main', 'main-upgrade': 'main',
                'main-service': 'main', 'scratch-service': 'scratch', 'scratch-upgrade': 'scratch',
                'main-fixture': 'main', 'scratch-fixture': 'scratch'}


def keep_primary(directory, error, *, stage, root_event_id=None):
    """Diagnostic persistence never prevents exact-owned-child cleanup."""
    try:
        return save_primary(directory, error, stage=stage, root_event_id=root_event_id)
    except BaseException:
        try:
            os.write(2, b'LC2_PRIMARY_EVIDENCE_UNAVAILABLE\n')
        except BaseException:
            pass
        return {'event_id': None, 'saved': False}


def stop(reason, **facts):
    if not STOP.exists():
        save_once(STOP, {'reason': reason, 'ts_utc': datetime.now(timezone.utc).isoformat(), **facts})


def candidate_marker(marker, *, approval, product_commit, test_commit, action):
    """Preserve every prior new-target marker byte before candidate metadata advances."""
    require_dispatch_unfrozen()
    if STOP.exists():
        raise RuntimeError('LC2_HARD_STOP_ACTIVE')
    dispatch = runtime_gate(approval, product_commit=product_commit, test_commit=test_commit)
    if action not in dispatch.get('allowed_actions', []) or marker['database'] not in dispatch.get('allowed_target_names', []):
        raise RuntimeError('MARKER_CANDIDATE_NOT_DISPATCHED')
    expected_role = ACTION_ROLES.get(action)
    target = next((item for item in strict_loads(PLAN.read_bytes())['targets']
                   if item['database'] == marker['database']), None)
    if (expected_role is None or target is None or target['role'] != expected_role
            or marker.get('role') != expected_role or marker.get('lc2_role') != expected_role
            or target['port'] != marker['port']):
        raise RuntimeError('MARKER_ROLE_ACTION_DRIFT')
    run = RUN_ROOT / marker['database']
    actual = target_guard(marker['database'], run, allowed_names=dispatch['allowed_target_names'], config_path=run / 'odoo.conf')
    immutable = set(marker) - {'product_commit', 'test_commit'}
    if any(actual.get(key) != marker[key] for key in immutable) or actual['core'] != CORE:
        raise RuntimeError('MARKER_IDENTITY_DRIFT')
    if actual.get('product_commit') == product_commit and actual.get('test_commit') == test_commit:
        return actual
    for field, desired in [('product_commit', product_commit), ('test_commit', test_commit)]:
        previous = actual.get(field)
        if previous is None or subprocess.run(['git', '-C', str(ROOT), 'merge-base', '--is-ancestor', previous, desired],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode:
            raise RuntimeError('MARKER_CANDIDATE_NOT_LINEAR')
    path = run / 'database.json'
    old_raw = path.read_bytes()
    old_sha = hashlib.sha256(old_raw).hexdigest()
    preserved = run / ('database-marker-' + old_sha + '.json')
    if not preserved.exists():
        with private_file(preserved) as stream:
            stream.write(old_raw)
            stream.flush()
            os.fsync(stream.fileno())
    if preserved.read_bytes() != old_raw:
        raise RuntimeError('PRESERVED_MARKER_BYTES_MISMATCH')
    updated = actual | {'product_commit': product_commit, 'test_commit': test_commit}
    temporary = run / 'database-next.json'
    new_ref = save_once(temporary, updated)
    save_once(run / ('candidate-marker-change-' + new_ref['sha256'] + '.json'), {
        'previous_sha256': old_sha, 'preserved': preserved.name, 'new_sha256': new_ref['sha256'],
        'product_commit': product_commit, 'test_commit': test_commit, 'config_changed': False,
        'database_mutation': False, 'reason': 'approved linear frozen candidate',
    })
    temporary.replace(path)
    return updated


def launch_guard(marker, *, approval, product_commit, test_commit, action):
    require_dispatch_unfrozen()
    if STOP.exists():
        raise RuntimeError('LC2_HARD_STOP_ACTIVE')
    dispatch = runtime_gate(approval, product_commit=product_commit, test_commit=test_commit)
    if action not in dispatch.get('allowed_actions', []):
        raise RuntimeError('APPLICATION_ACTION_NOT_DISPATCHED')
    plan = strict_loads(PLAN.read_bytes())
    names = [item['database'] for item in plan['targets']]
    if set(names) != set(dispatch.get('allowed_target_names', [])):
        raise RuntimeError('APPLICATION_TARGET_SET_DRIFT')
    expected_role = ACTION_ROLES.get(action)
    selected = next((item for item in plan['targets'] if item['database'] == marker['database']), None)
    if (expected_role is None or selected is None or selected['role'] != expected_role
            or marker.get('role') != expected_role or marker.get('lc2_role') != expected_role
            or selected['port'] != marker['port']):
        raise RuntimeError('APPLICATION_ROLE_ACTION_DRIFT')
    run = RUN_ROOT / marker['database']
    actual = target_guard(marker['database'], run, allowed_names=names, config_path=run / 'odoo.conf')
    if (actual != marker or marker['product_commit'] != product_commit
            or marker['test_commit'] != test_commit or marker['core'] != CORE):
        raise RuntimeError('APPLICATION_MARKER_DRIFT')
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(run / 'odoo.conf')
    options = parser['options']
    expected = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
                'db_name': marker['database'], 'dbfilter': '^' + marker['database'] + '$',
                'workers': '0', 'max_cron_threads': '0', 'db_maxconn': '4',
                'http_interface': '127.0.0.1', 'http_port': str(marker['port']),
                'data_dir': str(run / 'data'), 'logfile': str(run / 'odoo-native.log'),
                'log_config': str(ROOT / 'config/logging-s10.example.json'),
                'addons_path': str(ROOT.parent / 'addons') + ',' + str(ROOT)}
    if any(options.get(key) != value for key, value in expected.items()) or not 18410 <= marker['port'] <= 18419:
        raise RuntimeError('APPLICATION_CONFIG_BOUNDARY_DRIFT')
    if list((run / 'diagnostics').glob('diagnostics-failed-*.txt')):
        raise RuntimeError('DIAGNOSTIC_CHAIN_UNAVAILABLE')
    return run, options


def identity_probe(marker, options, *, budget, directory):
    """Fresh owned-target RO connection before every launch, never an old source."""
    import psycopg2
    budget.consume('target_ro')
    started = time.monotonic()
    connection, primary = None, None
    try:
        connection = psycopg2.connect(host=options['db_host'], port=options['db_port'], user=options['db_user'],
                                      password=options['db_password'], dbname=marker['database'], connect_timeout=10,
                                      application_name='ydental_s10_lc2_launch_probe')
        connection.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute("SET LOCAL statement_timeout='30s'")
            cursor.execute("SET LOCAL lock_timeout='3s'")
            cursor.execute("SET LOCAL timezone='UTC'")
            cursor.execute("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),pg_backend_pid(),current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
            identity = cursor.fetchone()
            cursor.execute("SET LOCAL statement_timeout='15s'")
            cursor.execute('SELECT pid,state,backend_type,application_name FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() ORDER BY pid')
            others = cursor.fetchall()
            save_once(Path(directory) / 'target-other-connections.json', {'connections': [
                dict(zip(['pid', 'state', 'backend_type', 'application_name'], row)) for row in others]})
            if others:
                raise RuntimeError('OTHER_TARGET_CONNECTIONS_BEFORE_OWNED_LAUNCH')
            if tuple(identity[:3]) != (marker['database'], marker['oid'], CLUSTER) or tuple(identity[4:]) != ('odoo', 'on', 'repeatable read'):
                raise RuntimeError('LAUNCH_DATABASE_IDENTITY_DRIFT')
        connection.rollback()
        save_once(Path(directory) / 'identity-probe.json', {'database': identity[0], 'oid': identity[1],
                  'cluster': identity[2], 'backend_pid': identity[3], 'user': identity[4],
                  'read_only': identity[5], 'isolation': identity[6], 'rollback_returned': True})
    except BaseException as error:
        primary = keep_primary(directory, error, stage='launch_identity_probe')
        raise
    finally:
        if connection is not None:
            try:
                connection.close()
                safe_plain(Path(directory) / 'identity-probe-exit.tsv', ['CLOSED', time.time_ns()])
            except BaseException as secondary:
                keep_primary(directory, secondary, stage='launch_probe_close',
                             root_event_id=primary['event_id'] if primary else None)
                if primary is None:
                    raise
    if time.monotonic() - started > 60:
        raise TimeoutError('LAUNCH_PROBE_WINDOW_EXHAUSTED')


def environment(run, product_commit, test_commit):
    env = dict(os.environ)
    env.pop('PGOPTIONS', None)
    env.pop('PYTHONHOME', None)
    env.update(PYTHONPATH=os.pathsep.join([str(ROOT / 'scripts'), str(ROOT / '.local/s04-deps')]),
               PYTHONDONTWRITEBYTECODE='1', YDENTAL_S10_RUN_DIR=str(run),
               YDENTAL_RUN_ID='lc2-r12-exec-20261017', YDENTAL_TASK_ID='S10-LOG-AND-CLOSEOUT-v2',
               YDENTAL_PRODUCT_COMMIT=product_commit, YDENTAL_TEST_COMMIT=test_commit, YDENTAL_CORE_COMMIT=CORE,
               YDENTAL_DIAGNOSTIC_DIR=str(run / 'diagnostics'),
               YDENTAL_LC2_BUDGET_DIR=str(EXEC_ROOT), PYTHONFAULTHANDLER='1')
    return env


def dependency_preflight(env, directory):
    result = launch([str(PYTHON), str(ROOT / 'scripts/s10_lc2_preflight.py')],
                    Path(directory) / 'dependency-preflight', env=env, cwd=ROOT, timeout=30, attempt=1)
    if result.get('native_crash') or result['returncode'] in (-4, -6, -7, -8, -11):
        stop('DEPENDENCY_PREFLIGHT_NATIVE_CRASH', pid=result['pid'], signal=result['signal'])
        raise RuntimeError('NATIVE_PREFLIGHT_HARD_STOP')
    if result['returncode'] != 0:
        raise RuntimeError('OFFLINE_DEPENDENCY_PREFLIGHT_FAILED')
    report = strict_loads((Path(directory) / 'dependency-preflight/stdout.log').read_bytes())
    if report['odoo_imported'] or report['database_connection_performed']:
        raise RuntimeError('DEPENDENCY_PREFLIGHT_SCOPE_DRIFT')
    return report


class OwnedApplication:
    """One exact owned Popen; monitor global raw cap while code runs."""
    def __init__(self, marker, *, approval, product_commit, test_commit, action):
        self.action = action
        self.marker = candidate_marker(marker, approval=approval, product_commit=product_commit,
                                       test_commit=test_commit, action=action)
        self.run, options = launch_guard(self.marker, approval=approval, product_commit=product_commit,
                                         test_commit=test_commit, action=action)
        self.budget = PackageBudget(EXEC_ROOT)
        self.directory = EXEC_ROOT / ('application-' + action + '-' + uuid.uuid4().hex[:8])
        self.directory.mkdir(mode=0o700)
        self.env = environment(self.run, product_commit, test_commit)
        dependency_preflight(self.env, self.directory)
        identity_probe(self.marker, options, budget=self.budget, directory=self.directory)
        self.native_logfile = self.directory / 'odoo-native.log'
        command = [str(PYTHON), str(ROOT.parent / 'odoo-bin')]
        if action in {'main-fixture', 'scratch-fixture'}:
            command += ['shell']
        self.command = command + ['-c', str(self.run / 'odoo.conf'), '--logfile', str(self.native_logfile),
                                  '--db-system=' + self.marker['database'],
                                  '--log-handler=werkzeug:WARNING,odoo.http.server:CRITICAL']
        if action in {'main-fixture', 'scratch-fixture'}:
            self.command += ['--no-http']
        self.process = None
        self.streams = []
        self.started = None
        self.event_guard = None

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, tb):
        primary = keep_primary(self.directory, error, stage='application_context') if error is not None else None
        self.close(primary=primary)
        return False

    def start(self, arguments, *, pass_fds=(), stdin_path=None):
        allowed = {
            'scratch-tests': ('--stop-after-init', '--load-language=zh_CN', '-i',
                              'ydental_settlement_test', '--test-enable', '--test-tags=s10_lc2'),
            'upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'main-upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'scratch-upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'main-service': (), 'scratch-service': (), 'main-fixture': (), 'scratch-fixture': (),
        }
        if type(arguments) is not list or tuple(arguments) != allowed.get(self.action):
            raise ValueError('APPLICATION_ARGUMENT_OVERRIDE_REFUSED')
        if any(type(fd) is not int or fd < 3 for fd in pass_fds):
            raise ValueError('INVALID_OWNED_RAM_PIPE_DESCRIPTOR')
        fixture = self.action in {'main-fixture', 'scratch-fixture'}
        expected_stdin = ROOT / 'scripts/s10_lc2_fixture_process.py'
        if fixture:
            if (stdin_path is None or Path(stdin_path).resolve() != expected_stdin
                    or len(pass_fds) != 2 or len(set(pass_fds)) != 2
                    or any(not stat.S_ISFIFO(os.fstat(fd).st_mode) for fd in pass_fds)):
                raise ValueError('FIXTURE_STDIN_AND_ANONYMOUS_PIPES_REQUIRED')
        elif stdin_path is not None or pass_fds:
            raise ValueError('NON_FIXTURE_STDIN_FORBIDDEN')
        with socket.socket() as reservation:
            reservation.bind(('127.0.0.1', self.marker['port']))
        self.budget.consume('odoo_start')
        save_once(self.directory / 'launch-intent.json', {'command': self.command + arguments,
                  'database': self.marker['database'], 'oid': self.marker['oid'],
                  'product_commit': self.env['YDENTAL_PRODUCT_COMMIT'], 'test_commit': self.env['YDENTAL_TEST_COMMIT'],
                  'core_commit': CORE, 'commit_observation': 'NOT_OBSERVED',
                  'effective_logfile': str(getattr(self, 'native_logfile', self.directory / 'odoo-native.log')),
                  'effective_logfile_path_sha256': hashlib.sha256(str(getattr(self, 'native_logfile', self.directory / 'odoo-native.log')).encode()).hexdigest(),
                  'transport_access_logger_level': 'CRITICAL',
                  'transport_access_error_detail_retained': False,
                  'effective_db_system': self.marker['database'], 'maintenance_database_connection_authorized': False,
                  'stdin_sha256': hashlib.sha256(expected_stdin.read_bytes()).hexdigest() if fixture else None})
        stdin = expected_stdin.open('rb') if fixture else subprocess.DEVNULL
        self.started = time.monotonic()
        try:
            bind_dispatch_owner(self)
            for name in ('stdout.log', 'stderr-faulthandler.log'):
                self.streams.append(private_file(self.directory / name))
            self.process = subprocess.Popen(self.command + arguments, cwd=ROOT, env=self.env,
                                            stdin=stdin, stdout=self.streams[0], stderr=self.streams[1],
                                            umask=0o077, pass_fds=tuple(pass_fds))
            self.event_guard = ProcessLogGuard(self.run / 'diagnostics', self.process.pid,
                                              self.env['YDENTAL_RUN_ID'])
            append_plain(self.directory / 'parent-exit.tsv', ['child.start', time.time_ns(), self.process.pid])
        except BaseException as error:
            primary = keep_primary(self.directory, error, stage='application_launch')
            self.close(primary=primary)
            raise
        finally:
            if stdin is not subprocess.DEVNULL:
                stdin.close()
        return self

    def observe_events(self, *, allow_starting=False, final=False):
        if self.event_guard is None:
            raise RuntimeError('APPLICATION_EVENT_GUARD_NOT_INITIALIZED')
        try:
            if list((self.run / 'diagnostics').glob('diagnostics-failed-*.txt')):
                self.event_guard.state.fail('DIAGNOSTIC_CHAIN_UNAVAILABLE')
            return self.event_guard.observe(allow_starting=allow_starting, final=final)
        except ObservationBlocked:
            # The in-memory latch is set first, so even a failed STOP writer
            # cannot permit another request or replace the producer's primary.
            failure = self.event_guard.state.failure
            freeze_dispatch(failure)
            try:
                stop(failure['reason'], pid=self.process.pid,
                     primary_event_id=failure['event_id'], root_event_id=failure['root_event_id'])
            except BaseException as secondary:
                keep_primary(self.directory, secondary, stage='event_stop_persistence',
                             root_event_id=failure['root_event_id'] or failure['event_id'])
            raise

    def observe_native_exit(self, code):
        """A real parent return code is independent of diagnostic completeness."""
        if code not in (-4, -6, -7, -8, -11):
            return
        freeze_dispatch({'reason': 'NATIVE_PROCESS_EXIT', 'event_id': None, 'root_event_id': None})
        try:
            stop('NATIVE_CRASH', pid=self.process.pid, signal=-code)
        except BaseException as secondary:
            keep_primary(self.directory, secondary, stage='native_stop_persistence')

    def check_evidence_markers(self):
        require_dispatch_unfrozen()
        if STOP.exists():
            raise RuntimeError('APPLICATION_DIAGNOSTIC_OR_HARD_STOP')

    def check(self, *, allow_starting=False):
        self.budget.check_storage()
        if time.monotonic() - self.started > 1800:
            stop('OWNED_SERVICE_WINDOW_EXHAUSTED', pid=self.process.pid)
            raise TimeoutError('OWNED_SERVICE_WINDOW_EXHAUSTED')
        self.check_evidence_markers()
        code = self.process.poll()
        try:
            self.observe_events(allow_starting=allow_starting and code is None, final=code is not None)
        finally:
            self.observe_native_exit(code)
        if self.event_guard.state.ended:
            raise RuntimeError('APPLICATION_DIAGNOSTICS_ENDED_NO_DISPATCH')
        if self.process.poll() is not None:
            if self.process.returncode in (-4, -6, -7, -8, -11):
                stop('NATIVE_CRASH', pid=self.process.pid, signal=-self.process.returncode)
            raise RuntimeError('APPLICATION_EXITED')

    def wait_ready(self, timeout=60):
        started = time.monotonic()
        while True:
            self.check(allow_starting=True)
            try:
                with socket.create_connection(('127.0.0.1', self.marker['port']), timeout=.5):
                    self.assert_observed_logging_levels()
                    return
            except OSError:
                if time.monotonic() - started > timeout:
                    raise TimeoutError('OWNED_HTTP_START_TIMEOUT')
                time.sleep(.1)

    def assert_observed_logging_levels(self):
        """The actual service PID must attest privacy levels before token requests."""
        starts = []
        for path in (self.run / 'diagnostics').glob('events-' + str(self.process.pid) + '-*.jsonl'):
            for raw in path.read_bytes().splitlines():
                event = strict_loads(raw)
                if event.get('event') == 'run.start' and event.get('pid') == self.process.pid:
                    starts.append(event)
        if len(starts) != 1 or starts[0].get('native_http_log_level') != 50 or starts[0].get('diagnostic_log_level') != 20:
            raise RuntimeError('ACTUAL_SERVICE_LOG_PRIVACY_LEVEL_NOT_ATTESTED')
        save_once(self.directory / 'actual-log-levels.json', {
            'pid': self.process.pid, 'event_id': starts[0]['event_id'],
            'native_http_log_level': 50, 'diagnostic_log_level': 20,
            'transport_access_error_detail_retained': False})

    def wait(self, timeout):
        try:
            while self.process.poll() is None:
                self.budget.check_storage()
                self.check_evidence_markers()
                self.observe_events(allow_starting=time.monotonic() - self.started < 60)
                if time.monotonic() - self.started > timeout:
                    stop('APPLICATION_TIMEOUT_OUTCOME_NOT_OBSERVED', pid=self.process.pid)
                    raise TimeoutError('APPLICATION_WINDOW_EXHAUSTED')
                time.sleep(.2)
            returncode = self.process.returncode
            try:
                self.observe_events(final=True)
            finally:
                self.observe_native_exit(returncode)
        except BaseException as error:
            primary = keep_primary(self.directory, error, stage='application_wait')
            self.close(primary=primary)
            raise
        else:
            self.close()
        return returncode

    def close(self, primary=None):
        cleanup_error = None

        def retain(error, stage):
            nonlocal cleanup_error
            if cleanup_error is None:
                cleanup_error = error
            keep_primary(self.directory, error, stage=stage,
                         root_event_id=primary['event_id'] if primary else None)

        try:
            if self.process is not None and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        except BaseException as secondary:
            retain(secondary, 'application_owned_cleanup')
            try:
                stop('OWNED_PROCESS_CLEANUP_UNCONFIRMED')
            except BaseException as persistence_error:
                retain(persistence_error, 'hard_stop_persistence')
        finally:
            code = self.process.returncode if self.process is not None else None
            if getattr(self, 'event_guard', None) is not None:
                try:
                    self.observe_events(final=True)
                except BaseException as secondary:
                    retain(secondary, 'application_final_diagnostics')
            self.observe_native_exit(code)
            if not safe_plain(self.directory / 'parent-exit.tsv', ['parent.end', time.time_ns(),
                              self.process.pid if self.process else None, code,
                              -code if code is not None and code < 0 else None, 'TRANSACTION_NOT_OBSERVED']):
                retain(RuntimeError('APPLICATION_EXIT_EVIDENCE_UNAVAILABLE'), 'application_parent_exit')
            for stream in self.streams:
                try:
                    stream.close()
                except BaseException as secondary:
                    retain(secondary, 'application_output_close')
            self.streams = []
            release_dispatch_owner(self)
        if cleanup_error is not None and primary is None:
            raise cleanup_error


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['scratch-tests', 'main-upgrade', 'scratch-upgrade'])
    parser.add_argument('--approval', required=True)
    parser.add_argument('--product-commit', required=True)
    parser.add_argument('--test-commit', required=True)
    args = parser.parse_args()
    markers = strict_loads((LEGACY_EXEC_ROOT / 'owned-target-markers.json').read_bytes())['markers']
    role = ACTION_ROLES[args.mode]
    marker = next(item for item in markers if item['role'] == role)
    app = OwnedApplication(marker, approval=args.approval, product_commit=args.product_commit,
                           test_commit=args.test_commit, action=args.mode)
    arguments = ['--stop-after-init', '--load-language=zh_CN']
    if args.mode == 'scratch-tests':
        arguments += ['-i', 'ydental_settlement_test', '--test-enable', '--test-tags=s10_lc2']
    else:
        arguments += ['-u', 'ydental_settlement']
    app.start(arguments)
    code = app.wait(1200)
    save_once(app.directory / 'result.json', {'exit_code': code, 'pid': app.process.pid,
              'signal': -code if code < 0 else None, 'database': marker['database'],
              'mode': args.mode, 'execution_layer': 'MODEL_HTTP_FRAMEWORK' if args.mode == 'scratch-tests' else 'NATIVE_UPGRADE',
              'real_money_operations': 0})
    print(str(app.directory / 'result.json'))
    return code if code >= 0 else 128 - code


if __name__ == '__main__':
    raise SystemExit(main())
