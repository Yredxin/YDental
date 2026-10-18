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
from s10_lc2_framework_caller import (GRANT_ENV, GRANT_NAME, check_framework_failure,
                                      framework_failure_facts, issue_framework_grant)
from s10_lc2_task_profile import CURRENT_PLAN, FRAMEWORK6, MAIN_A_AUTONOMY, MAIN_A_ENGINEERING, MAIN_A_PRIVATE_LOG_PROFILES, MAIN_A_PROFILES

ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT.parent / '.venv/bin/python'
STOP = EXEC_ROOT / 'HARD-STOP.json'
ACTION_ROLES = {'scratch-tests': 'scratch', 'upgrade': 'main', 'main-upgrade': 'main',
                'main-service': 'main', 'scratch-service': 'scratch', 'scratch-upgrade': 'scratch',
                'main-fixture': 'main', 'scratch-fixture': 'scratch', 'main-credential-setup': 'main'}


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


def stop(reason, *, profile=None, **facts):
    path = profile.root / 'HARD-STOP.json' if profile is not None else STOP
    if not path.exists():
        save_once(path, {'reason': reason, 'ts_utc': datetime.now(timezone.utc).isoformat(), **facts})


def candidate_marker(marker, *, approval, product_commit, test_commit, action, profile=None):
    """Preserve every prior new-target marker byte before candidate metadata advances."""
    require_dispatch_unfrozen(profile)
    extra = {'profile': profile} if profile is not None else {}
    if (profile.root / 'HARD-STOP.json' if profile is not None else STOP).exists():
        raise RuntimeError('LC2_HARD_STOP_ACTIVE')
    dispatch = runtime_gate(approval, product_commit=product_commit, test_commit=test_commit, **extra)
    if action not in dispatch.get('allowed_actions', []) or marker['database'] not in dispatch.get('allowed_target_names', []):
        raise RuntimeError('MARKER_CANDIDATE_NOT_DISPATCHED')
    expected_role = ACTION_ROLES.get(action)
    plan_path = profile.root / 'target-plan.json' if profile is not None else PLAN
    target = next((item for item in strict_loads(plan_path.read_bytes())['targets']
                   if item['database'] == marker['database']), None)
    if (expected_role is None or target is None or target['role'] != expected_role
            or marker.get('role') != expected_role or marker.get('lc2_role') != expected_role
            or target['port'] != marker['port']):
        raise RuntimeError('MARKER_ROLE_ACTION_DRIFT')
    run = (profile.run_root if profile is not None else RUN_ROOT) / marker['database']
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


def launch_guard(marker, *, approval, product_commit, test_commit, action, profile=None):
    require_dispatch_unfrozen(profile)
    extra = {'profile': profile} if profile is not None else {}
    if profile is not None:
        profile.validate_target(marker.get('database'), marker.get('oid'), marker.get('port'))
        profile.require_action(action)
        if action not in profile.allowed_actions:
            raise RuntimeError('LC2_TASK_APPLICATION_SCOPE_INVALID')
    if (profile.root / 'HARD-STOP.json' if profile is not None else STOP).exists():
        raise RuntimeError('LC2_HARD_STOP_ACTIVE')
    dispatch = runtime_gate(approval, product_commit=product_commit, test_commit=test_commit, **extra)
    if action not in dispatch.get('allowed_actions', []):
        raise RuntimeError('APPLICATION_ACTION_NOT_DISPATCHED')
    plan = strict_loads((profile.root / 'target-plan.json' if profile is not None else PLAN).read_bytes())
    names = [item['database'] for item in plan['targets']]
    if set(names) != set(dispatch.get('allowed_target_names', [])):
        raise RuntimeError('APPLICATION_TARGET_SET_DRIFT')
    expected_role = ACTION_ROLES.get(action)
    selected = next((item for item in plan['targets'] if item['database'] == marker['database']), None)
    if (expected_role is None or selected is None or selected['role'] != expected_role
            or marker.get('role') != expected_role or marker.get('lc2_role') != expected_role
            or selected['port'] != marker['port']):
        raise RuntimeError('APPLICATION_ROLE_ACTION_DRIFT')
    run = (profile.run_root if profile is not None else RUN_ROOT) / marker['database']
    actual = target_guard(marker['database'], run, allowed_names=names, config_path=run / 'odoo.conf')
    if (actual != marker or marker['product_commit'] != product_commit
            or marker['test_commit'] != test_commit or marker['core'] != CORE):
        raise RuntimeError('APPLICATION_MARKER_DRIFT')
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(run / 'odoo.conf')
    options = parser['options']
    log_config = ROOT / ('config/logging-s10-main-a-engineering.example.json'
                         if profile is not None and (profile.message_id in MAIN_A_PRIVATE_LOG_PROFILES or profile.message_id == CURRENT_PLAN)
                         else 'config/logging-s10.example.json')
    expected = {'db_host': '127.0.0.1', 'db_port': '5432', 'db_user': 'odoo',
                'db_name': marker['database'], 'dbfilter': '^' + marker['database'] + '$',
                'workers': '0', 'max_cron_threads': '0', 'db_maxconn': '4',
                'http_interface': '127.0.0.1', 'http_port': str(marker['port']),
                'data_dir': str(profile.data_dir if profile is not None else run / 'data'), 'logfile': str(run / 'odoo-native.log'),
                'log_config': str(log_config),
                'addons_path': str(ROOT.parent / 'addons') + ',' + str(ROOT)}
    if any(options.get(key) != value for key, value in expected.items()) or not 18410 <= marker['port'] <= 18419:
        raise RuntimeError('APPLICATION_CONFIG_BOUNDARY_DRIFT')
    if list((run / 'diagnostics').glob('diagnostics-failed-*.txt')):
        raise RuntimeError('DIAGNOSTIC_CHAIN_UNAVAILABLE')
    return run, options


def identity_probe(marker, options, *, budget, directory):
    """Fresh owned-target RO connection before every launch, never an old source."""
    import psycopg2
    if budget.profile is not None:
        budget.profile.require_action('target-ro')
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


def environment(run, product_commit, test_commit, profile=None):
    env = dict(os.environ)
    env.pop('PGOPTIONS', None)
    env.pop('PYTHONHOME', None)
    env.pop(GRANT_ENV, None)
    env.pop('YDENTAL_LC2_PROFILE', None)
    env.update(PYTHONPATH=os.pathsep.join([str(ROOT / 'scripts'), str(ROOT / '.local/s04-deps')]),
               PYTHONDONTWRITEBYTECODE='1', YDENTAL_S10_RUN_DIR=str(run),
               YDENTAL_RUN_ID='lc2-r12-exec-20261017', YDENTAL_TASK_ID='S10-LOG-AND-CLOSEOUT-v2',
               YDENTAL_PRODUCT_COMMIT=product_commit, YDENTAL_TEST_COMMIT=test_commit, YDENTAL_CORE_COMMIT=CORE,
               YDENTAL_DIAGNOSTIC_DIR=str(run / 'diagnostics'),
               YDENTAL_LC2_BUDGET_DIR=str(EXEC_ROOT), PYTHONFAULTHANDLER='1')
    if profile is not None:
        profile.verify()
        for key in tuple(env):
            if key.startswith('FAKETIME') or key == 'ODOO_FAKETIME_TEST_MODE':
                env.pop(key)
        if 'faketime' in env.get('LD_PRELOAD', '').lower():
            raise RuntimeError('FRAMEWORK6_FAKETIME_PRELOAD_FORBIDDEN')
        env.update(YDENTAL_LC2_PROFILE=profile.message_id,
                   YDENTAL_RUN_ID=profile.run_id, YDENTAL_LC2_BUDGET_DIR=str(profile.root))
    return env


def dependency_preflight(env, directory, profile=None):
    result = launch([str(PYTHON), str(ROOT / 'scripts/s10_lc2_preflight.py')],
                    Path(directory) / 'dependency-preflight', env=env, cwd=ROOT, timeout=30, attempt=1)
    if result.get('native_crash') or result['returncode'] in (-4, -6, -7, -8, -11):
        stop('DEPENDENCY_PREFLIGHT_NATIVE_CRASH', pid=result['pid'], signal=result['signal'],
             **({'profile': profile} if profile is not None else {}))
        raise RuntimeError('NATIVE_PREFLIGHT_HARD_STOP')
    if result['returncode'] != 0:
        raise RuntimeError('OFFLINE_DEPENDENCY_PREFLIGHT_FAILED')
    report = strict_loads((Path(directory) / 'dependency-preflight/stdout.log').read_bytes())
    if report['odoo_imported'] or report['database_connection_performed']:
        raise RuntimeError('DEPENDENCY_PREFLIGHT_SCOPE_DRIFT')
    return report


class OwnedApplication:
    """One exact owned Popen; monitor global raw cap while code runs."""
    def __init__(self, marker, *, approval, product_commit, test_commit, action, profile=None):
        self.profile = profile
        self.exec_root = profile.root if profile is not None else EXEC_ROOT
        self.stop_path = self.exec_root / 'HARD-STOP.json' if profile is not None else STOP
        extra = {'profile': profile} if profile is not None else {}
        self.action = action
        self.credential_script_sha256 = None
        if action == 'main-credential-setup':
            self.credential_script_sha256 = strict_loads(Path(approval).read_bytes()).get(
                'frozen_files', {}).get('scripts/s10_lc2_main_a_credentials.py')
            if (not isinstance(self.credential_script_sha256, str)
                    or len(self.credential_script_sha256) != 64):
                raise RuntimeError('MAIN_CREDENTIAL_SCRIPT_MUST_BE_FROZEN')
        self.marker = candidate_marker(marker, approval=approval, product_commit=product_commit,
                                       test_commit=test_commit, action=action, **extra)
        self.run, options = launch_guard(self.marker, approval=approval, product_commit=product_commit,
                                         test_commit=test_commit, action=action, **extra)
        self.budget = PackageBudget(self.exec_root, **extra)
        self.directory = self.exec_root / ('application-' + action + '-' + uuid.uuid4().hex[:8])
        self.directory.mkdir(mode=0o700)
        self.env = environment(self.run, product_commit, test_commit, **extra)
        self.framework_grant_path = self.directory / GRANT_NAME if action == 'scratch-tests' else None
        self.framework_frozen_files = {}
        if self.framework_grant_path is not None:
            self.env[GRANT_ENV] = str(self.framework_grant_path)
            self.framework_frozen_files = strict_loads(Path(approval).read_bytes()).get('frozen_files', {})
        dependency_preflight(self.env, self.directory, **extra)
        identity_probe(self.marker, options, budget=self.budget, directory=self.directory)
        self.log_config = Path(options['log_config'])
        self.native_logfile = self.directory / 'odoo-native.log'
        command = [str(PYTHON), str(ROOT.parent / 'odoo-bin')]
        if action in {'main-fixture', 'scratch-fixture', 'main-credential-setup'}:
            command += ['shell']
        self.command = command + ['-c', str(self.run / 'odoo.conf'), '--logfile', str(self.native_logfile),
                                  '--db-system=' + self.marker['database'],
                                  '--log-handler=werkzeug:WARNING,odoo.http.server:CRITICAL']
        if action in {'main-fixture', 'scratch-fixture', 'main-credential-setup'}:
            self.command += ['--no-http']
        self.process = None
        self.streams = []
        self.started = None
        self.event_guard = None

    def __enter__(self):
        return self

    def _stop(self, reason, **facts):
        profile = getattr(self, 'profile', None)
        return stop(reason, **facts, **({'profile': profile} if profile is not None else {}))

    def _freeze(self, failure):
        profile = getattr(self, 'profile', None)
        freeze_dispatch(failure, **({'profile': profile} if profile is not None else {}))

    def __exit__(self, error_type, error, tb):
        primary = keep_primary(self.directory, error, stage='application_context') if error is not None else None
        self.close(primary=primary)
        return False

    def start(self, arguments, *, pass_fds=(), stdin_path=None):
        profile = getattr(self, 'profile', None)
        require_dispatch_unfrozen(profile)
        allowed = {
            'scratch-tests': ('--stop-after-init', '--load-language=zh_CN', '-i',
                              'ydental_settlement_test', '--test-enable', '--test-tags=s10_lc2'),
            'upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'main-upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'scratch-upgrade': ('--stop-after-init', '--load-language=zh_CN', '-u', 'ydental_settlement'),
            'main-service': (), 'scratch-service': (), 'main-fixture': (), 'scratch-fixture': (),
            'main-credential-setup': (),
        }
        candidates = {allowed.get(self.action)}
        if profile is not None and profile.message_id == FRAMEWORK6:
            prefix = ('--stop-after-init', '--load-language=en_US,zh_CN')
            suffix = ('--test-enable', '--test-tags=s10_lc2/ydental_settlement_test')
            candidates = {prefix + operation + suffix for operation in (
                ('-i', 'ydental_settlement_test'), (), ('-u', 'ydental_settlement_test'))}
        if type(arguments) is not list or tuple(arguments) not in candidates:
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
        elif self.action == 'main-credential-setup':
            expected_stdin = ROOT / 'scripts/s10_lc2_main_a_credentials.py'
            if (profile is None or profile.message_id != MAIN_A_AUTONOMY
                    or stdin_path is None or Path(stdin_path).resolve() != expected_stdin
                    or pass_fds or expected_stdin.is_symlink()
                    or hashlib.sha256(expected_stdin.read_bytes()).hexdigest()
                        != self.credential_script_sha256):
                raise ValueError('MAIN_CREDENTIAL_SETUP_FIXED_STDIN_REQUIRED')
        elif stdin_path is not None or pass_fds:
            raise ValueError('NON_FIXTURE_STDIN_FORBIDDEN')
        has_stdin = fixture or self.action == 'main-credential-setup'
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
                  'native_system_connection_authorized': profile is not None,
                  'maintenance_operations_authorized': False,
                  'native_system_connection_mode': 'EXISTENCE_QUERY_ONLY' if profile is not None else 'LEGACY_NOT_AUTHORIZED',
                  'task_message_id': profile.message_id if profile is not None else None,
                  'native_existence_query_allowance': 1 if profile is not None else 0,
                  'native_postgres_dbname_fallback_allowance': 1 if profile is not None else 0,
                  'native_existence_actual_connections': 'UNKNOWN',
                  'native_system_connection_evidence_layer': 'SOURCE_INFERRED_ALLOWANCE_NOT_ACTUAL_COUNT',
                  'stdin_sha256': hashlib.sha256(expected_stdin.read_bytes()).hexdigest() if has_stdin else None,
                  'log_config': str(self.log_config),
                  'log_config_sha256': hashlib.sha256(self.log_config.read_bytes()).hexdigest()})
        stdin = expected_stdin.open('rb') if has_stdin else subprocess.DEVNULL
        self.started = time.monotonic()
        try:
            bind_dispatch_owner(self, **({'profile': profile} if profile is not None else {}))
            for name in ('stdout.log', 'stderr-faulthandler.log'):
                self.streams.append(private_file(self.directory / name))
            self.process = subprocess.Popen(self.command + arguments, cwd=ROOT, env=self.env,
                                            stdin=stdin, stdout=self.streams[0], stderr=self.streams[1],
                                            umask=0o077, pass_fds=tuple(pass_fds))
            if self.action == 'scratch-tests':
                grant_path = getattr(self, 'framework_grant_path', None)
                if grant_path is None:
                    raise RuntimeError('FRAMEWORK_LAUNCH_GRANT_NOT_PREPARED')
                issue_framework_grant(grant_path, marker=self.marker, environment=self.env,
                                      child_pid=self.process.pid, frozen_files=self.framework_frozen_files,
                                      **({'profile': profile} if profile is not None else {}))
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
            self._freeze(failure)
            try:
                self._stop(failure['reason'], pid=self.process.pid,
                     primary_event_id=failure['event_id'], root_event_id=failure['root_event_id'])
            except BaseException as secondary:
                keep_primary(self.directory, secondary, stage='event_stop_persistence',
                             root_event_id=failure['root_event_id'] or failure['event_id'])
            raise

    def observe_native_exit(self, code):
        """A real parent return code is independent of diagnostic completeness."""
        if code not in (-4, -6, -7, -8, -11):
            return
        self._freeze({'reason': 'NATIVE_PROCESS_EXIT', 'event_id': None, 'root_event_id': None})
        try:
            self._stop('NATIVE_CRASH', pid=self.process.pid, signal=-code)
        except BaseException as secondary:
            keep_primary(self.directory, secondary, stage='native_stop_persistence')

    def check_evidence_markers(self, *, final=False):
        require_dispatch_unfrozen(getattr(self, 'profile', None))
        if getattr(self, 'stop_path', STOP).exists():
            raise RuntimeError('APPLICATION_DIAGNOSTIC_OR_HARD_STOP')
        self.check_framework_markers(final=final)

    def check_framework_markers(self, *, final=False):
        """Cleanup observes new shared faults without replaying an existing stop."""
        try:
            profile = getattr(self, 'profile', None)
            root = getattr(self, 'stop_path', STOP).parent
            check_framework_failure(self.directory, budget_directory=root, final=final,
                                    grant_required=getattr(self, 'action', None) == 'scratch-tests',
                                    **({'profile': profile} if profile is not None else {}))
        except BaseException:
            failure = framework_failure_facts(getattr(self, 'stop_path', STOP).parent)
            self._freeze(failure)
            try:
                self._stop(failure['reason'], pid=self.process.pid, primary_event_id=failure['event_id'],
                     root_event_id=failure['root_event_id'])
            except BaseException as secondary:
                keep_primary(self.directory, secondary, stage='framework_stop_persistence')
            raise

    def check(self, *, allow_starting=False):
        self.budget.check_storage()
        selected = getattr(getattr(self, 'profile', None), 'message_id', None)
        maximum = 1200 if selected in MAIN_A_PROFILES or selected == CURRENT_PLAN else 1800
        if time.monotonic() - self.started > maximum:
            self._stop('OWNED_SERVICE_WINDOW_EXHAUSTED', pid=self.process.pid)
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
                self._stop('NATIVE_CRASH', pid=self.process.pid, signal=-self.process.returncode)
            raise RuntimeError('APPLICATION_EXITED')

    def wait_ready(self, timeout=60):
        # Odoo binds its socket before registry loading emits run.start. A
        # listening socket alone cannot authorize HTTP/browser dispatch.
        if type(timeout) not in (int, float) or timeout <= 0:
            raise ValueError('INVALID_OWNED_HTTP_START_TIMEOUT')
        deadline = min(time.monotonic() + timeout, self.started + 60)
        while True:
            if time.monotonic() >= deadline:
                raise TimeoutError('OWNED_HTTP_START_TIMEOUT')
            self.check(allow_starting=True)
            try:
                with socket.create_connection(('127.0.0.1', self.marker['port']), timeout=.5):
                    if self.event_guard.state.started:
                        self.assert_observed_logging_levels()
                        return
            except OSError:
                pass
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
        privacy = None
        if getattr(getattr(self, 'profile', None), 'message_id', None) in MAIN_A_PRIVATE_LOG_PROFILES | {CURRENT_PLAN}:
            privacy = strict_loads((self.run / 'diagnostics' / (
                'native-privacy-' + str(self.process.pid) + '.json')).read_bytes())
            if (privacy.get('pid') != self.process.pid
                    or privacy.get('task_message_id') != self.profile.message_id
                    or privacy.get('logger') != 'odoo.addons.base.models.res_device'
                    or type(privacy.get('effective_level')) is not int
                    or privacy['effective_level'] != 30
                    or privacy.get('config_sha256') != hashlib.sha256(self.log_config.read_bytes()).hexdigest()
                    or privacy.get('record_payload_retained') is not False):
                raise RuntimeError('ACTUAL_DEVICE_LOG_PRIVACY_LEVEL_NOT_ATTESTED')
        save_once(self.directory / 'actual-log-levels.json', {
            'pid': self.process.pid, 'event_id': starts[0]['event_id'],
            'native_http_log_level': 50, 'diagnostic_log_level': 20,
            'transport_access_error_detail_retained': False,
            'native_device_privacy': privacy})

    def wait(self, timeout):
        if getattr(getattr(self, 'profile', None), 'message_id', None) in MAIN_A_PROFILES:
            timeout = min(timeout, 1200)
        try:
            while self.process.poll() is None:
                self.budget.check_storage()
                self.check_evidence_markers()
                self.observe_events(allow_starting=time.monotonic() - self.started < 60)
                if time.monotonic() - self.started > timeout:
                    self._stop('APPLICATION_TIMEOUT_OUTCOME_NOT_OBSERVED', pid=self.process.pid)
                    raise TimeoutError('APPLICATION_WINDOW_EXHAUSTED')
                time.sleep(.2)
            returncode = self.process.returncode
            try:
                native_exit = returncode in (-4, -6, -7, -8, -11)
                if not native_exit:
                    self.check_evidence_markers(final=True)
                self.observe_events(final=True)
                if native_exit:
                    # Preserve the independently observed signal and the old
                    # diagnostic-first order. New framework uncertainty is secondary.
                    self.observe_native_exit(returncode)
                    try:
                        self.check_framework_markers(final=True)
                    except BaseException as secondary:
                        keep_primary(self.directory, secondary, stage='framework_after_native_exit')
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
                self._stop('OWNED_PROCESS_CLEANUP_UNCONFIRMED')
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
            if self.process is not None:
                try:
                    self.check_framework_markers(final=True)
                except BaseException as secondary:
                    retain(secondary, 'application_final_framework_guard')
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
        native_exit = self.process is not None and self.process.returncode in (-4, -6, -7, -8, -11)
        if cleanup_error is not None and primary is None and not native_exit:
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
