"""One approved framework RPC reservation; no Odoo, network or process imports."""
from datetime import datetime, timezone
import fcntl
import hashlib
import os
from pathlib import Path
import re
import stat
import time

from s10_lc2_evidence import AUTHORIZATION_EPOCH, Budget, CLUSTER, CORE, LIMITS, RAW_LIMIT, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_process_guard import ProcessLogGuard


ROOT = Path(__file__).resolve().parents[1]
EXEC_ROOT = ROOT / '.local/s10-lc2-r12-20261017'
LEGACY_EXEC_ROOT = ROOT / '.local/s10-lc2-exec-20261017'
RUN_ROOT = ROOT / '.local/s10-lc2/20261017-lc2-exec01'
PURPOSE = 'TestLogCloseoutHTTP.test_actual_rpc_preserves_native_access_error_name_and_arguments'
RPC_PATH = '/web/dataset/call_kw/ydental.access.audit.write'
GRANT_ENV = 'YDENTAL_LC2_FRAMEWORK_GRANT'
GRANT_NAME = 'framework-http-grant.json'
PENDING_NAME = 'framework-http-pending.json'
RESERVED_NAME = 'framework-http-reserved.json'
FAILURE_NAME = 'framework-http-failure.json'
FROZEN_FILES = frozenset({
    'scripts/s10_lc2_framework_caller.py', 'scripts/s10_lc2_evidence.py',
    'scripts/s10_lc2_launch.py', 'scripts/s10_lc2_targets.py',
    'scripts/s10_lc2_process_guard.py', 'scripts/s10_lc2_logging.py', 'scripts/s10_lc2_supervisor.py',
    'ydental_settlement_test/tests/test_log_closeout.py',
})
_FAILURE = None


def _private_directory(path):
    path = Path(path)
    info = path.lstat()
    if (not path.is_absolute() or path.resolve() != path or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700):
        raise RuntimeError('FRAMEWORK_DIRECTORY_NOT_PRIVATE')


def _read(path, limit=128 * 1024):
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as stream:
        info = os.fstat(stream.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > limit):
            raise RuntimeError('FRAMEWORK_FILE_NOT_PRIVATE_OR_BOUNDED')
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise RuntimeError('FRAMEWORK_FILE_BOUND')
    return raw


def _ledger(directory):
    _private_directory(directory)
    value = strict_loads(_read(Path(directory) / 'budget.json'))
    _read(Path(directory) / 'budget.lock')
    if (type(value) is not dict or set(value) != {'started_epoch', 'counts'}
            or value['started_epoch'] != AUTHORIZATION_EPOCH or type(value['counts']) is not dict
            or any(kind not in LIMITS or type(count) is not int or not 0 <= count <= LIMITS[kind]
                   for kind, count in value['counts'].items())):
        raise RuntimeError('FRAMEWORK_BUDGET_INVALID')
    return value


def _file_sha(path):
    return hashlib.sha256(_read(path)).hexdigest()


def _failure_facts(value):
    if (type(value) is not dict or type(value.get('reason')) is not str
            or not re.fullmatch(r'[A-Z0-9_]{1,96}', value['reason'])):
        raise ValueError('FRAMEWORK_FAILURE_FACTS_INVALID')
    facts = {'reason': value['reason']}
    for key in ('event_id', 'root_event_id'):
        reference = value.get(key)
        if reference is not None and (type(reference) is not str
                or not re.fullmatch(r'[A-Za-z0-9_.:/-]{1,160}', reference)):
            raise ValueError('FRAMEWORK_FAILURE_REFERENCE_INVALID')
        facts[key] = reference
    return facts


def framework_failure_facts(budget_directory):
    path = Path(budget_directory) / FAILURE_NAME
    if not path.exists():
        return {'reason': 'FRAMEWORK_CALLER_FAILURE', 'event_id': None, 'root_event_id': None}
    try:
        return _failure_facts(strict_loads(_read(path)))
    except BaseException:
        return {'reason': 'FRAMEWORK_FAILURE_RECORD_UNREADABLE', 'event_id': None, 'root_event_id': None}


def freeze_framework_http(error, *, observed_failure=None):
    global _FAILURE
    if _FAILURE is None:
        try:
            facts = _failure_facts(observed_failure) if observed_failure else {
                'reason': 'CALLER_ADMISSION_OR_RESERVATION_FAILED', 'event_id': None, 'root_event_id': None}
        except BaseException:
            facts = {'reason': 'FRAMEWORK_FAILURE_FACTS_INVALID', 'event_id': None, 'root_event_id': None}
        _FAILURE = facts['reason']
        value = {**facts, 'pid': os.getpid(), 'purpose': PURPOSE,
                 'exception_type': type(error).__name__,
                 'ts_utc': datetime.now(timezone.utc).isoformat()}
        for name in (FAILURE_NAME, 'HARD-STOP.json'):
            try:
                save_once(EXEC_ROOT / name, value)
            except BaseException:
                # A local latch still blocks this interpreter. No claim of
                # instantaneous cross-process delivery when all writes fail.
                pass


def issue_framework_grant(path, *, marker, environment, child_pid, frozen_files):
    """Parent calls only after its ordinary launch/identity/candidate gates."""
    path = Path(path)
    _private_directory(EXEC_ROOT)
    _private_directory(path.parent)
    if (path.name != GRANT_NAME or path.parent.parent != EXEC_ROOT
            or not re.fullmatch(r'application-scratch-tests-[a-f0-9]{8}', path.parent.name)
            or marker.get('role') != 'scratch' or marker.get('lc2_role') != 'scratch'
            or type(marker.get('database')) is not str
            or not re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', marker['database'])
            or marker.get('port') != 18411
            or type(child_pid) is not int or child_pid <= 0
            or not FROZEN_FILES.issubset(frozen_files)):
        raise RuntimeError('FRAMEWORK_GRANT_ISSUER_SCOPE_INVALID')
    run = RUN_ROOT / marker['database']
    _private_directory(run)
    ledger = _ledger(EXEC_ROOT)
    issued = time.time()
    value = {'schema_version': '1.0', 'purpose': PURPOSE, 'action': 'scratch-tests', 'role': 'scratch',
             'parent_pid': os.getpid(), 'child_pid': child_pid, 'issued_epoch': issued,
             'deadline_epoch': min(issued + 1200, ledger['started_epoch'] + 8 * 3600),
             'database': marker['database'], 'oid': marker['oid'], 'port': marker['port'],
             'run_directory': str(run), 'budget_directory': str(EXEC_ROOT),
             'budget_started_epoch': ledger['started_epoch'],
             'run_id': environment['YDENTAL_RUN_ID'], 'task_id': environment['YDENTAL_TASK_ID'],
             'product_commit': environment['YDENTAL_PRODUCT_COMMIT'],
             'test_commit': environment['YDENTAL_TEST_COMMIT'], 'core_commit': CORE,
             'config_sha256': _file_sha(run / 'odoo.conf'), 'marker_sha256': _file_sha(run / 'database.json'),
             'identity_probe_sha256': _file_sha(path.parent / 'identity-probe.json'),
             'identity_probe_exit_sha256': _file_sha(path.parent / 'identity-probe-exit.tsv'),
             'frozen_files': {name: frozen_files[name] for name in sorted(FROZEN_FILES)}}
    save_once(path, value)
    return value


def check_framework_failure(directory, *, budget_directory=None, final=False, grant_required=False):
    """Parent checks under the ledger lock, so an active reservation is not a fault."""
    directory = Path(directory)
    budget_directory = Path(budget_directory) if budget_directory is not None else EXEC_ROOT
    if (budget_directory / FAILURE_NAME).exists():
        raise RuntimeError('FRAMEWORK_CALLER_FAILURE_PERSISTED')
    if grant_required and not (directory / GRANT_NAME).is_file():
        raise RuntimeError('FRAMEWORK_EXPECTED_GRANT_MISSING')
    pending, reserved = directory / PENDING_NAME, directory / RESERVED_NAME
    if not pending.exists():
        if final and (grant_required or (directory / GRANT_NAME).exists()):
            raise RuntimeError('FRAMEWORK_HTTP_RESERVATION_NOT_OBSERVED')
        return
    with os.fdopen(os.open(budget_directory / 'budget.lock', os.O_RDWR | os.O_NOFOLLOW), 'a+b') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if pending.exists() and not reserved.exists():
            raise RuntimeError('FRAMEWORK_RESERVATION_INCOMPLETE')
        before, after = strict_loads(_read(pending)), strict_loads(_read(reserved))
        grant_hash = _file_sha(directory / GRANT_NAME)
        if (before.get('grant_sha256') != grant_hash or after.get('grant_sha256') != grant_hash
                or before.get('purpose') != PURPOSE or after.get('purpose') != PURPOSE
                or before.get('pid') != after.get('pid')
                or before.get('resource') != 'http' or after.get('resource') != 'http'
                or type(after.get('count')) is not int or after['count'] < 1
                or _ledger(budget_directory)['counts'].get('http', 0) < after['count']):
            raise RuntimeError('FRAMEWORK_RESERVATION_EVIDENCE_INVALID')


class _FrameworkBudget(Budget):
    def check_storage(self):
        size = sum(path.stat().st_size for base in (LEGACY_EXEC_ROOT, EXEC_ROOT, RUN_ROOT) if base.exists()
                   for path in base.rglob('*') if path.is_file() and not path.is_symlink())
        if size >= RAW_LIMIT * .9:
            raise RuntimeError('FRAMEWORK_RAW_STORAGE_BOUND')
        return size


def reserve_framework_http(*, environment, database, http_port, url, purpose, allow_redirects=False):
    """Caller-local gate and one durable reservation before the native url_open."""
    if _FAILURE is not None:
        raise RuntimeError('FRAMEWORK_HTTP_FROZEN_' + _FAILURE)
    observed_failure = None
    try:
        _private_directory(EXEC_ROOT)
        if (EXEC_ROOT / 'HARD-STOP.json').exists() or (EXEC_ROOT / FAILURE_NAME).exists():
            raise RuntimeError('FRAMEWORK_EXISTING_STOP')
        pointer = environment.get(GRANT_ENV)
        if not pointer:
            raise RuntimeError('FRAMEWORK_GRANT_MISSING')
        path = Path(pointer)
        _private_directory(path.parent)
        if (path.name != GRANT_NAME or path.parent.parent != EXEC_ROOT
                or not re.fullmatch(r'application-scratch-tests-[a-f0-9]{8}', path.parent.name)):
            raise RuntimeError('FRAMEWORK_GRANT_PATH_INVALID')
        grant_raw = _read(path)
        grant = strict_loads(grant_raw)
        if (type(database) is not str
                or not re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', database)):
            raise RuntimeError('FRAMEWORK_DATABASE_NAME_INVALID')
        run = RUN_ROOT / database
        if run.parent != RUN_ROOT or run.resolve() != run:
            raise RuntimeError('FRAMEWORK_TARGET_PATH_INVALID')
        _private_directory(run)

        def gate():
            nonlocal observed_failure
            if (EXEC_ROOT / 'HARD-STOP.json').exists() or (EXEC_ROOT / FAILURE_NAME).exists():
                raise RuntimeError('FRAMEWORK_EXISTING_STOP')
            if _read(path) != grant_raw:
                raise RuntimeError('FRAMEWORK_GRANT_CHANGED')
            if (type(http_port) is not int or http_port != 18411
                    or url not in {RPC_PATH, 'http://127.0.0.1:%s%s' % (http_port, RPC_PATH)}
                    or allow_redirects is not False or purpose != PURPOSE
                    or grant.get('schema_version') != '1.0' or grant.get('purpose') != PURPOSE
                    or grant.get('action') != 'scratch-tests' or grant.get('role') != 'scratch'
                    or type(grant.get('parent_pid')) is not int or type(grant.get('child_pid')) is not int
                    or grant.get('parent_pid') != os.getppid() or grant.get('child_pid') != os.getpid()
                    or grant.get('database') != database or grant.get('port') != http_port
                    or grant.get('run_directory') != str(run) or grant.get('budget_directory') != str(EXEC_ROOT)
                    or grant.get('core_commit') != CORE
                    or grant.get('budget_started_epoch') != _ledger(EXEC_ROOT)['started_epoch']
                    or not grant['issued_epoch'] <= time.time() <= grant['deadline_epoch']
                    or grant['deadline_epoch'] > min(grant['issued_epoch'] + 1200, AUTHORIZATION_EPOCH + 8 * 3600)):
                raise RuntimeError('FRAMEWORK_CALLER_IDENTITY_OR_PURPOSE_INVALID')
            for field in ('run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit'):
                if environment.get('YDENTAL_' + field.upper()) != grant.get(field):
                    raise RuntimeError('FRAMEWORK_CANDIDATE_ENV_DRIFT')
            for field in ('product_commit', 'test_commit'):
                if not re.fullmatch(r'[a-f0-9]{40}', grant[field]):
                    raise RuntimeError('FRAMEWORK_CANDIDATE_INVALID')
            if (environment.get('YDENTAL_S10_RUN_DIR') != str(run)
                    or environment.get('YDENTAL_LC2_BUDGET_DIR') != str(EXEC_ROOT)
                    or _file_sha(run / 'database.json') != grant['marker_sha256']
                    or _file_sha(run / 'odoo.conf') != grant['config_sha256']
                    or _file_sha(path.parent / 'identity-probe.json') != grant['identity_probe_sha256']
                    or _file_sha(path.parent / 'identity-probe-exit.tsv') != grant['identity_probe_exit_sha256']):
                raise RuntimeError('FRAMEWORK_LOCAL_IDENTITY_DRIFT')
            marker = strict_loads(_read(run / 'database.json'))
            identity = strict_loads(_read(path.parent / 'identity-probe.json'))
            if (marker.get('database') != database or marker.get('oid') != grant['oid']
                    or marker.get('core') != CORE or marker.get('cluster') != CLUSTER
                    or marker.get('role') != 'scratch' or marker.get('lc2_role') != 'scratch'
                    or marker.get('port') != http_port or marker.get('config_sha256') != grant['config_sha256']
                    or marker.get('product_commit') != grant['product_commit']
                    or marker.get('test_commit') != grant['test_commit']
                    or identity.get('database') != database or identity.get('oid') != grant['oid']
                    or identity.get('cluster') != CLUSTER or identity.get('user') != 'odoo'
                    or identity.get('read_only') != 'on' or identity.get('isolation') != 'repeatable read'
                    or identity.get('rollback_returned') is not True
                    or not _read(path.parent / 'identity-probe-exit.tsv').startswith(b'CLOSED\t')):
                raise RuntimeError('FRAMEWORK_TARGET_OR_PROBE_DRIFT')
            if list((run / 'diagnostics').glob('diagnostics-failed-*.txt')):
                raise RuntimeError('FRAMEWORK_DIAGNOSTICS_FAILED')
            observer = ProcessLogGuard(run / 'diagnostics', os.getpid(), grant['run_id'])
            try:
                observer.observe()
            except BaseException:
                observed_failure = observer.state.failure
                raise
            if observer.state.ended:
                raise RuntimeError('FRAMEWORK_DIAGNOSTICS_ENDED')
            if set(grant['frozen_files']) != FROZEN_FILES or any(
                    (ROOT / relative).resolve() != ROOT / relative
                    or hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() != expected
                    for relative, expected in grant['frozen_files'].items()):
                raise RuntimeError('FRAMEWORK_FROZEN_SOURCE_DRIFT')
            save_once(path.parent / PENDING_NAME, {'grant_sha256': hashlib.sha256(grant_raw).hexdigest(),
                      'purpose': PURPOSE, 'pid': os.getpid(), 'resource': 'http'})

        def reserved(count):
            save_once(path.parent / RESERVED_NAME, {'resource': 'http', 'count': count,
                      'pid': os.getpid(), 'purpose': PURPOSE,
                      'grant_sha256': hashlib.sha256(grant_raw).hexdigest()})

        budget = _FrameworkBudget(EXEC_ROOT, create=False)
        return budget.consume('http', before_reserve=gate, after_reserve=reserved)
    except BaseException as primary:
        freeze_framework_http(primary, observed_failure=observed_failure)
        raise
