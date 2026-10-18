"""Bounded independent RO evidence and explicit runtime-budget gates."""
import fcntl
from decimal import Decimal
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid

from s10_lc2_logging import strict_loads
from s10_lc2_supervisor import append_plain, private_file, safe_plain, save_primary
from s10_lc2_task_profile import CURRENT_PLAN, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI, TaskProfile

CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
CLUSTER = '7694897083368259627'
ACCIDENT = 'ydental_s10_test_20261017080710_2494c102'
PROTECTED = {'ydental_s10_test_20261017050000_21b0cafe': 0, ACCIDENT: 2}
LIMITS = {'accident_ro': 2, 'target_ro': 48, 'maintenance': 1, 'create': 2,
          'odoo_start': 12, 'http': 600, 'original_get': 12, 'firefox': 3}
AUTHORIZATION_EPOCH = 1792238721.801  # R1.2 direct authorization; cumulative counts preserved.
RAW_LIMIT = 1024 ** 3


def save_once(path, value):
    path = Path(path)
    raw = json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False).encode('utf-8') + b'\n'
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise
    if path.read_bytes() != raw:
        raise ValueError('SAVED_BYTES_READBACK_MISMATCH')
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


class Budget:
    """One budget owner, durable before dispatch; a failed call still consumes its intent."""

    def __init__(self, directory, *, started_epoch=None, create=True, profile=None):
        self.profile = profile
        if profile is not None:
            if type(profile) is not TaskProfile or Path(directory) != profile.root or create:
                raise ValueError('FRAMEWORK6_REQUIRES_EXISTING_TASK_BUDGET')
            profile.verify()
        self.directory = Path(directory)
        self.path = self.directory / 'budget.json'
        self.lock_path = self.directory / 'budget.lock'
        self.create = create
        if type(create) is not bool or not create and started_epoch is not None:
            raise ValueError('INVALID_BUDGET_OPEN_MODE')
        if create:
            self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        elif not self.directory.is_dir() or not self.path.is_file() or not self.lock_path.is_file():
            raise RuntimeError('EXISTING_BUDGET_REQUIRED')
        if not create:
            return  # Never initialize from the child path, even after a deletion race.
        if not self.path.exists():
            save_once(self.path, {'started_epoch': started_epoch if started_epoch is not None else AUTHORIZATION_EPOCH, 'counts': {}})

    def check_storage(self):
        size = sum(path.stat().st_size for path in self.directory.rglob('*') if path.is_file())
        if size >= RAW_LIMIT * .9:
            raise RuntimeError('RAW_STORAGE_PAUSE_AT_90_PERCENT')
        if size >= RAW_LIMIT * .8:
            safe_plain(self.directory / 'storage-warning.tsv', [time.time_ns(), '80_PERCENT', size])
        return size

    def consume(self, kind, *, before_reserve=None, after_reserve=None, firefox_purpose=None):
        if kind not in LIMITS:
            raise ValueError('UNAPPROVED_RESOURCE')
        engineering = self.profile is not None and self.profile.message_id in {MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI}
        original_ui = self.profile is not None and self.profile.message_id == MAIN_A_ORIGINAL_UI
        if (original_ui and kind == 'firefox' and firefox_purpose != 'ui'
                or engineering and kind == 'firefox' and firefox_purpose not in {'diagnostic', 'ui'}
                or firefox_purpose is not None and (not engineering or kind != 'firefox')):
            raise ValueError('FIREFOX_PURPOSE_REQUIRED_ONLY_FOR_ENGINEERING')
        self.check_storage()
        flags = os.O_RDWR | os.O_NOFOLLOW | (os.O_CREAT if self.create else 0)
        with os.fdopen(os.open(self.lock_path, flags, 0o600), 'a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if before_reserve is not None:
                before_reserve()
            value = strict_loads(self.path.read_bytes())
            if self.profile is not None:
                self.profile.validate_ledger(value)
                if kind not in self.profile.local_limits or value['task_counts'].get(kind, 0) >= self.profile.local_limits[kind]:
                    raise RuntimeError('FRAMEWORK6_RESOURCE_EXHAUSTED:' + kind)
            elif time.time() - value['started_epoch'] > 8 * 3600:
                raise RuntimeError('RUN_WINDOW_EXHAUSTED')
            if engineering and kind == 'firefox':
                if value['task_firefox_counts'][firefox_purpose] >= (3 if original_ui else 2):
                    raise RuntimeError('FIREFOX_PURPOSE_RESOURCE_EXHAUSTED:' + firefox_purpose)
                value['task_firefox_counts'][firefox_purpose] += 1
            count = value['counts'].get(kind, 0) + 1
            maximum = (self.profile.baseline[kind] + self.profile.local_limits[kind]
                       if self.profile is not None and self.profile.message_id == CURRENT_PLAN
                       else (8 if original_ui else 5) if engineering and kind == 'firefox' else LIMITS[kind])
            if count > maximum:
                raise RuntimeError('RESOURCE_EXHAUSTED:' + kind)
            value['counts'][kind] = count
            if self.profile is not None:
                value['task_counts'][kind] = value['task_counts'].get(kind, 0) + 1
            temporary = self.path.with_suffix('.next')
            save_once(temporary, value)
            temporary.replace(self.path)
            append_plain(self.directory / 'budget-intents.tsv', [time.time_ns(), kind, count])
            if after_reserve is not None:
                after_reserve(count)
        return count


def runtime_gate(approval_path, *, product_commit, test_commit, profile=None):
    value = strict_loads(Path(approval_path).read_bytes())
    expected_message = profile.message_id if profile is not None else 'YD-S10-LC2-EXEC-20261017-02'
    if profile is not None:
        profile.verify()
        if (value.get('authority_sha256') != profile.authority_sha256
                or set(value.get('allowed_target_names', [])) != {profile.database}
                or set(value.get('allowed_actions', [])) != profile.allowed_actions):
            raise RuntimeError('FRAMEWORK6_DISPATCH_SCOPE_INVALID')
    current = profile is not None and profile.message_id == CURRENT_PLAN
    if current:
        scope = profile.current_scope()
        if (value.get('plan_id') != CURRENT_PLAN or value.get('version') != '1.0'
                or value.get('execution_owner') != scope['execution_owner']):
            raise RuntimeError('CURRENT_PLAN_DISPATCH_OWNER_OR_SCOPE_INVALID')
    if (value.get('message_id') != expected_message
            or not current and value.get('start_api_exact_readback') is not True
            or value.get('runtime_dispatched') is not True
            or value.get('product_commit') != product_commit
            or value.get('test_commit') != test_commit
            or value.get('core_commit') != CORE):
        raise RuntimeError('RUNTIME_NOT_DISPATCHED_FOR_FIXED_CANDIDATE')
    root = Path(__file__).resolve().parents[1]
    head = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    core_head = subprocess.check_output(['git', '-C', str(root.parent), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'diff', '--name-only'], text=True).strip()
    core_dirty = subprocess.check_output(['git', '-C', str(root.parent), 'diff', '--name-only'], text=True).strip()
    if head != test_commit or core_head != CORE or dirty or core_dirty:
        raise RuntimeError('FROZEN_CANDIDATE_OR_CORE_DRIFT')
    for relative, expected_sha in value.get('frozen_files', {}).items():
        path = root / relative
        if not path.resolve().is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha:
            raise RuntimeError('FROZEN_FILE_DRIFT')
    return value


def target_guard(database, directory, *, allowed_names, config_path):
    directory, config_path = Path(directory), Path(config_path)
    if (database not in allowed_names or database in PROTECTED
            or not re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', database)
            or directory.is_symlink() or directory.name != database
            or config_path.is_symlink()):
        raise RuntimeError('TARGET_NOT_OWNED')
    marker = strict_loads((directory / 'database.json').read_bytes())
    if (marker.get('database') != database or marker.get('cluster') != CLUSTER
            or marker.get('core') != CORE
            or marker.get('config_sha256') != hashlib.sha256(config_path.read_bytes()).hexdigest()):
        raise RuntimeError('TARGET_MARKER_DRIFT')
    return marker


def collect_selection(connect, connection_args, *, database, expected_oid, selections,
                      directory, budget, allowed_target_names=(),
                      target_directory=None, config_path=None,
                      collect_metadata=False,
                      max_bytes=32 * 1024 * 1024, max_rows=200000):
    """One RO/RR transaction; close connection before decoding/hash/sealing large files.

    selections is an already frozen list of table names, optional id tuples, and
    explicitly named order columns. No raw SQL, credential or caller domain is logged.
    """
    if database in PROTECTED and database != ACCIDENT:
        raise RuntimeError('P021_CONNECTION_FORBIDDEN')
    if database != ACCIDENT and database not in allowed_target_names:
        raise RuntimeError('DATABASE_NOT_IN_APPROVED_TARGETS')
    if getattr(budget, 'profile', None) is not None:
        budget.profile.validate_target(database, expected_oid)
        budget.profile.require_action('target-ro')
        if set(allowed_target_names) != {budget.profile.database}:
            raise RuntimeError('LC2_TASK_RO_TARGET_SET_DRIFT')
    if database != ACCIDENT:
        if target_directory is None or config_path is None:
            raise RuntimeError('TARGET_MARKER_REQUIRED')
        marker = target_guard(database, target_directory, allowed_names=allowed_target_names, config_path=config_path)
        if marker['oid'] != expected_oid:
            raise RuntimeError('TARGET_OID_DRIFT')
    if not selections:
        raise ValueError('EMPTY_SELECTION')
    if type(collect_metadata) is not bool:
        raise ValueError('INVALID_METADATA_SELECTION')
    if (connection_args.get('host') != '127.0.0.1' or str(connection_args.get('port')) != '5432'
            or connection_args.get('user') != 'odoo'
            or set(connection_args) - {'host', 'port', 'user', 'password', 'sslmode', 'application_name'}):
        raise ValueError('UNAPPROVED_CONNECTION_ARGUMENT')
    for selection in selections:
        if any(key in selection for key in ('columns', 'null_columns', 'equals', 'row_digest')):
            for key in ('columns', 'null_columns'):
                if key in selection and (type(selection[key]) is not list
                        or key == 'columns' and not selection[key]
                        or any(type(name) is not str for name in selection[key])
                        or len(selection[key]) != len(set(selection[key]))):
                    raise ValueError('INVALID_SELECTION_PROJECTION')
            if ('columns' not in selection or type(selection.get('row_digest', False)) is not bool
                    or type(selection.get('equals', {})) is not dict
                    or any(type(value) is not int for value in selection.get('equals', {}).values())):
                raise ValueError('INVALID_SELECTION_PROJECTION')
        if 'xmlids' in selection and (selection['table'] != 'ir_model_data'
                or type(selection['xmlids']) is not list or not selection['xmlids']
                or any(type(value) is not str or not re.fullmatch(r'[a-z_][a-z0-9_]*\.[a-z_][a-z0-9_]*', value)
                       for value in selection['xmlids'])):
            raise ValueError('INVALID_SELECTION_XMLIDS')
        for name in [selection['table'], *selection.get('order', ['id']),
                     *selection.get('columns', []), *selection.get('null_columns', []),
                     *selection.get('equals', {})]:
            if not re.fullmatch(r'[a-z_][a-z0-9_]*', name):
                raise ValueError('UNSAFE_SELECTION_IDENTIFIER')
    budget.consume('accident_ro' if database == ACCIDENT else 'target_ro')
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    started = time.monotonic()
    connection = None
    files, total_bytes, total_rows = [], 0, 0
    cleanup_failure = False
    primary = None

    def remaining_ms():
        # Reserve two seconds of the total60s window for rollback/close.
        remaining = int((58 - (time.monotonic() - started)) * 1000)
        if remaining <= 0:
            raise TimeoutError('OBSERVER_WINDOW_EXHAUSTED')
        return min(30000, remaining)

    try:
        connection = connect(dbname=database, connect_timeout=10, **connection_args)
        connection.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)
        with connection.cursor() as cursor:
            cursor.execute("SELECT set_config('statement_timeout', %s, true)", [str(remaining_ms())])
            cursor.execute("SET LOCAL lock_timeout='3s'")
            cursor.execute("SET LOCAL timezone='UTC'")
            cursor.execute("SELECT current_database(), (SELECT oid FROM pg_database WHERE datname=current_database()), (SELECT system_identifier::text FROM pg_control_system()), pg_backend_pid(), current_setting('transaction_read_only'), current_setting('transaction_isolation'), current_user, inet_server_addr()::text, inet_server_port(), current_setting('TimeZone')")
            identity = cursor.fetchone()
            if tuple(identity[:3]) != (database, expected_oid, CLUSTER) or tuple(identity[4:6]) != ('on', 'repeatable read'):
                raise RuntimeError('DATABASE_IDENTITY_OR_ISOLATION_DRIFT')
            if connection_args.get('user') and identity[6] != connection_args['user']:
                raise RuntimeError('DATABASE_USER_DRIFT')
            save_once(directory / 'identity.json', dict(zip(
                ['database', 'oid', 'cluster', 'backend_pid', 'read_only', 'isolation',
                 'current_user', 'server_addr', 'server_port', 'timezone'], identity)) |
                      {'requested_host': connection_args.get('host'), 'requested_port': connection_args.get('port')})
            if database == ACCIDENT:
                cursor.execute("SELECT pid, state, backend_type, application_name FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid() ORDER BY pid")
                others = cursor.fetchall()
                save_once(directory / 'other-connections.json', {'connections': [
                    dict(zip(['pid', 'state', 'backend_type', 'application_name'], row)) for row in others]})
            if database == ACCIDENT or collect_metadata:
                cursor.execute("SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum LIMIT 50001")
                catalog = cursor.fetchall()
                if len(catalog) >= 50001:
                    raise RuntimeError('SCHEMA_INVENTORY_BOUND_EXCEEDED')
                schema = {}
                for table, column, column_type in catalog:
                    schema.setdefault(table, []).append({'column': column, 'type': column_type})
                save_once(directory / 'schema.json', schema)
                for label, query, parameters in [
                    ('installed-modules', "SELECT to_jsonb(t)::text FROM ir_module_module t WHERE state='installed' ORDER BY id", None),
                    ('native-access', 'SELECT to_jsonb(t)::text FROM ir_access t ORDER BY id', None),
                    ('queue-settings', 'SELECT key,value FROM ir_config_parameter WHERE key=ANY(%s) ORDER BY key',
                     [['ydental_queue.heartbeat_seconds', 'ydental_queue.timeout_seconds']]),
                ]:
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", [str(remaining_ms())])
                    cursor.execute(query, parameters)
                    metadata = cursor.fetchall()
                    save_once(directory / (label + '.json'), {'observed_rows': metadata})
            for selection in selections:
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", [str(remaining_ms())])
                # Quoting is safe after the strict identifier allowlist; values use bind parameters.
                table = '"' + selection['table'] + '"'
                order = ','.join('"' + name + '"' for name in selection.get('order', ['id'])) or 'to_jsonb(t)::text'
                ids = selection.get('ids')
                where = ' WHERE t.id = ANY(%s)' if ids is not None else ''
                parameters = [list(ids)] if ids is not None else []
                for name, value in selection.get('equals', {}).items():
                    if type(value) is not int:
                        raise ValueError('UNSAFE_SELECTION_VALUE')
                    where += (' AND ' if where else ' WHERE ') + 't."' + name + '"=%s'
                    parameters.append(value)
                if selection.get('xmlids'):
                    where += (' AND ' if where else ' WHERE ') + '(' + ' OR '.join(
                        '(t.module=%s AND t.name=%s)' for _ in selection['xmlids']) + ')'
                    parameters += [part for value in selection['xmlids'] for part in value.split('.')]
                projected = 'to_jsonb(t)'
                if 'columns' in selection:
                    pairs = ["'%s',t.\"%s\"" % (name, name) for name in selection['columns']]
                    pairs += ["'%s_is_null',t.\"%s\" IS NULL" % (name, name)
                              for name in selection.get('null_columns', [])]
                    if selection.get('row_digest'):
                        pairs.append("'__row_sha256',encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex')")
                    projected = 'jsonb_build_object(' + ','.join(pairs) + ')'
                path = directory / (selection['table'] + '.rows.jsonl')
                acquired_digest, acquired_rows, acquired_bytes = hashlib.sha256(), 0, 0
                # A named server cursor prevents libpq from buffering the full selection.
                with connection.cursor(name='lc2_' + selection['table']) as row_cursor, private_file(path) as stream:
                    row_cursor.itersize = 8
                    row_cursor.execute("SELECT t.tableoid::regclass::text,t.tableoid," + projected + "::text,encode(sha256(convert_to(" + projected + "::text,'UTF8')),'hex') FROM public." + table + ' t' + where + ' ORDER BY ' + order + ' LIMIT ' + str(max_rows + 1),
                                       parameters or None)
                    while True:
                        cursor.execute("SELECT set_config('statement_timeout', %s, true)", [str(remaining_ms())])
                        rows = row_cursor.fetchmany(8)
                        if not rows:
                            break
                        for physical, physical_oid, text, server_digest in rows:
                            raw = json.dumps({'physical_table': physical, 'physical_oid': physical_oid,
                                              'server_json_text': text, 'server_sha256': server_digest},
                                             ensure_ascii=True, separators=(',', ':')).encode('utf-8') + b'\n'
                            total_bytes += len(raw)
                            total_rows += 1
                            if total_bytes > max_bytes or total_rows > max_rows or time.monotonic() - started >= 60:
                                raise RuntimeError('EVIDENCE_BOUND_EXCEEDED')
                            stream.write(raw)
                            acquired_digest.update(raw)
                            acquired_rows += 1
                            acquired_bytes += len(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
                files.append((path, acquired_digest.hexdigest(), acquired_rows, acquired_bytes))
        connection.rollback()
        cleanup_failure = not safe_plain(directory / 'observer-exit.tsv', ['ROLLBACK_RETURNED', time.time_ns()])
    except BaseException as error:
        primary = save_primary(directory, error, stage='independent_observer')
        safe_plain(directory / 'observer-exit.tsv', ['INCOMPLETE', time.time_ns()])
        if connection is not None:
            try:
                connection.rollback()
            except BaseException as secondary:
                save_primary(directory, secondary, stage='observer_rollback', root_event_id=primary['event_id'])
        raise
    finally:
        if connection is not None:
            try:
                connection.close()
                cleanup_failure |= not safe_plain(directory / 'observer-exit.tsv', ['CLOSED', time.time_ns()])
            except BaseException as secondary:
                save_primary(directory, secondary, stage='observer_close',
                             root_event_id=primary['event_id'] if primary else None)
                cleanup_failure = True
    if cleanup_failure:
        raise RuntimeError('OBSERVER_CLEANUP_EVIDENCE_INCOMPLETE')
    if time.monotonic() - started > 60:
        raise TimeoutError('OBSERVER_TOTAL_WINDOW_EXHAUSTED')
    # Heavy validation and hashing occur after the protected connection is closed.
    index = []
    for path, acquired_sha, acquired_count, acquired_length in files:
        digest, count, length = hashlib.sha256(), 0, 0
        canonical_rows = []
        with path.open('rb') as stream:
            for raw in stream:
                if not raw.endswith(b'\n'):
                    raise ValueError('TRUNCATED_EVIDENCE')
                wrapper = strict_loads(raw)
                text = wrapper['server_json_text']
                if hashlib.sha256(text.encode('utf-8')).hexdigest() != wrapper['server_sha256']:
                    raise ValueError('SERVER_CLIENT_ROW_BYTES_MISMATCH')
                value = strict_loads(text, parse_float=Decimal)
                canonical_rows.append(value | {'__physical_table__': wrapper['physical_table'],
                                               '__physical_oid__': wrapper['physical_oid']})
                digest.update(raw)
                length += len(raw)
                count += 1
        if (digest.hexdigest(), count, length) != (acquired_sha, acquired_count, acquired_length):
            raise ValueError('ACQUIRED_FILE_READBACK_MISMATCH')
        canonical = json.dumps(canonical_rows, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str).encode('utf-8')
        index.append({'path': path.name, 'rows': count, 'bytes': length, 'sha256': digest.hexdigest(),
                      'acquired_file_readback_exact': True, 'server_client_row_bytes_exact': True,
                      'legacy_canonical_sha256': hashlib.sha256(canonical).hexdigest()})
    save_once(directory / 'sealed-index.json', {'files': index, 'total_rows': total_rows,
                                              'total_bytes': total_bytes, 'independent_measurement': True})
    return index


def b_source_binding(value):
    """Fixed non-secret source identity shared by B's existing evidence tools."""
    keys = {'run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit', 'identity'}
    if (type(value) is not dict or set(value) != keys
            or any(type(value[key]) is not str or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,96}', value[key])
                   for key in ('run_id', 'task_id'))
            or any(type(value[key]) is not str or not re.fullmatch(r'[0-9a-f]{40}', value[key])
                   for key in ('product_commit', 'test_commit', 'core_commit'))
            or value['core_commit'] != CORE
            or value['identity'] != {'database': 'ydental_s10_test_20261017105432_810a7d9c',
                                     'oid': 2144129, 'cluster': CLUSTER}):
        raise ValueError('B_SOURCE_BINDING_INVALID')
    return value


def _b_file(path, limit=32 * 1024 * 1024):
    path = Path(path)
    if not path.is_absolute() or path.resolve() != path or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('B_SOURCE_FILE_INVALID')
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError('B_SOURCE_FILE_BOUND')
    return raw


def _b_file_ref(path):
    raw = _b_file(Path(path).absolute())
    return {'path': str(Path(path).absolute()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


_B_PROJECTIONS = {
    'res_users': ('id active company_id', False),
    'res_groups_users_rel': ('uid gid', False),
    'res_groups_implied_rel': ('gid hid', False),
    'ir_model_data': ('id module name model res_id', False),
    'ydental_access_store': ('id name active company_id', False),
    'ydental_access_membership': ('id active ydental_user_id ydental_store_id ydental_employee_id', False),
    'hr_employee': ('id active user_id company_id', False),
    'ydental_access_session': ('ydental_user_id ydental_store_id ydental_revision', False),
    'ydental_settlement_source': ('id ydental_store_id ydental_patient_id ydental_invoice_id ydental_line_id', True),
    'ydental_settlement_payment': ('id ydental_store_id ydental_patient_id ydental_payment_id', True),
    'ydental_settlement_payment_invoice_rel': ('settlement_payment_id invoice_id', True),
    'ydental_access_audit': ('id ydental_user_id ydental_store_id ydental_target_model ydental_target_id', True),
    'ydental_patient': ('id ydental_partner_id', False),
    'account_move': ('id company_id partner_id', True),
    'account_move_line': ('id move_id', True),
    'account_payment': ('id company_id', True),
    'ydental_clinical_document': ('id state ydental_version ydental_author_id ydental_responsible_id ydental_editor_id ydental_session_id ydental_session_revision ydental_editor_expires ydental_editor_lease_id', True),
    'ydental_clinical_version': ('id', True),
}


def _b_projection_guard(selections):
    if type(selections) is not list or not selections or any(type(item) is not dict for item in selections):
        raise ValueError('B_SOURCE_SAFE_PROJECTION_REQUIRED')
    if len({item.get('table') for item in selections}) != len(selections):
        raise ValueError('B_SOURCE_DUPLICATE_SELECTION')
    for item in selections:
        spec = _B_PROJECTIONS.get(item.get('table'))
        if (spec is None or item.get('columns') != spec[0].split()
                or item.get('row_digest') is not spec[1]
                or item.get('null_columns', []) != (['ydental_connection_hash', 'ydental_editor_hash']
                    if item['table'] == 'ydental_clinical_document' else [])
                or set(item) - {'table', 'columns', 'row_digest', 'null_columns', 'ids', 'equals', 'order', 'xmlids'}
                or 'ids' in item and (type(item['ids']) is not list or any(type(value) is not int or value <= 0 for value in item['ids']))):
            raise ValueError('B_SOURCE_SAFE_PROJECTION_REQUIRED')
        if item['table'] == 'ir_model_data' and item.get('xmlids') != [
                'base.group_user', 'base.group_system', 'base.group_erp_manager', 'ydental_base.ydental_base_group_user']:
            raise ValueError('B_SOURCE_SAFE_XMLIDS_REQUIRED')


def collect_b_source(connect, connection_args, *, binding, point, check_id, phase, selections,
                     directory, budget, target_directory, config_path):
    """Existing RO collector plus a check-bound receipt AFTER rollback/close.

    All I/O is explicit. There is no credential loader, target discovery or
    admission shortcut here. Callers must have the existing execution grant.
    """
    b_source_binding(binding)
    if (point not in {'manifest', 'before', 'after', 'terminal'}
            or any(type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_-]{1,40}', value)
                   for value in (check_id, phase))):
        raise ValueError('B_SOURCE_POINT_INVALID')
    _b_projection_guard(selections)
    marker = target_guard(binding['identity']['database'], target_directory,
        allowed_names=[binding['identity']['database']], config_path=config_path)
    if (any(marker.get(key) != value for key, value in binding['identity'].items())
            or any(marker.get(key) != binding[key] for key in ('product_commit', 'test_commit'))
            or marker.get('core') != binding['core_commit']):
        raise ValueError('B_SOURCE_MARKER_CANDIDATE_DRIFT')
    target_ref = _b_file_ref(Path(target_directory) / 'database.json')
    started = datetime.now(timezone.utc).isoformat()
    collect_selection(connect, connection_args, database=binding['identity']['database'],
        expected_oid=binding['identity']['oid'], selections=selections, directory=directory, budget=budget,
        allowed_target_names=[binding['identity']['database']], target_directory=target_directory,
        config_path=config_path, max_rows=2048, max_bytes=8 * 1024 * 1024)
    directory = Path(directory).absolute()
    paths = ['identity.json', 'observer-exit.tsv', 'sealed-index.json'] + [item['table'] + '.rows.jsonl' for item in selections]
    receipt = {'schema': 'LC2_B_SOURCE_1', 'binding': binding, 'measurement_id': uuid.uuid4().hex,
        'point': point, 'check_id': check_id, 'phase': phase, 'started_utc': started,
        'captured_utc': datetime.now(timezone.utc).isoformat(), 'selections': selections,
        'target_ref': target_ref,
        'files': {name: _b_file_ref(directory / name) for name in paths}}
    save_once(directory / 'b-source.json', receipt)
    return _b_file_ref(directory / 'b-source.json')


def read_b_source(reference, *, binding, used=None):
    """Resolve and verify exact bytes; never trust a pre-filled VERIFIED flag."""
    b_source_binding(binding)
    raw = _b_file(reference['path'])
    if len(raw) != reference.get('bytes') or hashlib.sha256(raw).hexdigest() != reference.get('sha256'):
        raise ValueError('B_SOURCE_REFERENCE_DRIFT')
    source = strict_loads(raw)
    if source.get('schema') != 'LC2_B_SOURCE_1' or source.get('binding') != binding:
        raise ValueError('B_SOURCE_CANDIDATE_OR_TARGET_DRIFT')
    target = source['target_ref']
    target_raw = _b_file(target['path'])
    marker = strict_loads(target_raw)
    if (Path(target['path']).name != 'database.json' or Path(target['path']).parent.name != binding['identity']['database']
            or len(target_raw) != target['bytes'] or hashlib.sha256(target_raw).hexdigest() != target['sha256']
            or any(marker.get(key) != value for key, value in binding['identity'].items())
            or any(marker.get(key) != binding[key] for key in ('product_commit', 'test_commit'))
            or marker.get('core') != binding['core_commit']):
        raise ValueError('B_SOURCE_MARKER_REFERENCE_DRIFT')
    measurement = source.get('measurement_id')
    if type(measurement) is not str or not re.fullmatch(r'[a-f0-9]{32}', measurement) or used is not None and measurement in used:
        raise ValueError('B_SOURCE_MEASUREMENT_REUSED')
    for field in ('started_utc', 'captured_utc'):
        stamp = datetime.fromisoformat(source[field])
        if stamp.tzinfo is None:
            raise ValueError('B_SOURCE_TIMEZONE_REQUIRED')
    if not 0 <= (datetime.fromisoformat(source['captured_utc']) - datetime.fromisoformat(source['started_utc'])).total_seconds() <= 60:
        raise ValueError('B_SOURCE_TIME_INVALID')
    directory = Path(reference['path']).parent
    files = source['files']
    contents = {}
    expected_names = {'identity.json', 'observer-exit.tsv', 'sealed-index.json'} | {
        item['table'] + '.rows.jsonl' for item in source['selections']}
    if set(files) != expected_names:
        raise ValueError('B_SOURCE_FILE_SET_DRIFT')
    for name, item in files.items():
        if Path(name).name != name or item['path'] != str(directory / name):
            raise ValueError('B_SOURCE_REFERENCE_OUTSIDE_CAPTURE')
        contents[name] = _b_file(item['path'])
        if len(contents[name]) != item['bytes'] or hashlib.sha256(contents[name]).hexdigest() != item['sha256']:
            raise ValueError('B_SOURCE_SEALED_BYTES_DRIFT')
    identity = strict_loads(contents['identity.json'])
    if (any(identity.get(key) != value for key, value in binding['identity'].items())
            or identity.get('read_only') != 'on' or identity.get('isolation') != 'repeatable read'):
        raise ValueError('B_SOURCE_RO_IDENTITY_DRIFT')
    exits = [line.split('\t')[0] for line in contents['observer-exit.tsv'].decode('ascii').splitlines()]
    if exits != ['ROLLBACK_RETURNED', 'CLOSED']:
        raise ValueError('B_SOURCE_TRANSACTION_NOT_CLOSED')
    index = strict_loads(contents['sealed-index.json'])
    if index.get('independent_measurement') is not True:
        raise ValueError('B_SOURCE_INDEX_INVALID')
    rows = {}
    if {item['path'] for item in index['files']} != expected_names - {'identity.json', 'observer-exit.tsv', 'sealed-index.json'}:
        raise ValueError('B_SOURCE_SELECTION_DRIFT')
    for entry in index['files']:
        body = contents[entry['path']]
        if len(body) != entry['bytes'] or hashlib.sha256(body).hexdigest() != entry['sha256'] or not body.endswith(b'\n') and body:
            raise ValueError('B_SOURCE_INDEX_BYTES_DRIFT')
        table_rows = []
        for line in body.splitlines():
            wrapped = strict_loads(line)
            text = wrapped['server_json_text']
            if hashlib.sha256(text.encode()).hexdigest() != wrapped['server_sha256']:
                raise ValueError('B_SOURCE_SERVER_ROW_DRIFT')
            if wrapped['physical_table'].removeprefix('public.') != entry['path'].removesuffix('.rows.jsonl'):
                raise ValueError('B_SOURCE_PHYSICAL_TABLE_DRIFT')
            table_rows.append(strict_loads(text))
        if len(table_rows) != entry['rows']:
            raise ValueError('B_SOURCE_ROW_COUNT_DRIFT')
        rows[entry['path'].removesuffix('.rows.jsonl')] = table_rows
    if used is not None:
        used.add(measurement)
    return source | {'rows': rows, 'reference': reference,
                     'connection_ref': 'ro:' + str(identity['backend_pid']) + ':' + measurement}


def parse_b_server_events(*, binding, app_directory, target_directory, pid, final=False):
    """Parse the actual logger contract, binding its missing target via launch.

    Live observations validate a bounded immutable prefix, not a final seal.
    The caller must verify these prefixes against final sealed logs at terminal.
    """
    from s10_lc2_logging import validate_jsonl
    from s10_lc2_process_guard import ProcessLogGuard

    b_source_binding(binding)
    app_directory, target_directory = Path(app_directory).absolute(), Path(target_directory).absolute()
    launch_path = app_directory / 'launch-intent.json'
    probe_path = app_directory / 'identity-probe.json'
    launch, probe = (strict_loads(_b_file(path)) for path in (launch_path, probe_path))
    marker = target_guard(binding['identity']['database'], target_directory,
        allowed_names=[binding['identity']['database']], config_path=target_directory / 'odoo.conf')
    if (any(launch.get(key) != binding[key] for key in ('product_commit', 'test_commit', 'core_commit'))
            or any(launch.get(key) != binding['identity'][key] for key in ('database', 'oid'))
            or launch.get('effective_db_system') != binding['identity']['database']
            or any(probe.get(key) != value for key, value in binding['identity'].items())
            or any(marker.get(key) != value for key, value in binding['identity'].items())
            or probe.get('read_only') != 'on' or probe.get('rollback_returned') is not True
            or any(marker.get(key) != binding[key] for key in ('product_commit', 'test_commit', 'core_commit') if key != 'core_commit')
            or marker.get('core') != binding['core_commit']):
        raise ValueError('B_LOG_LAUNCH_CANDIDATE_OR_TARGET_DRIFT')
    probe_exit = _b_file(app_directory / 'identity-probe-exit.tsv').decode('ascii').splitlines()
    if len(probe_exit) != 1 or probe_exit[0].split('\t')[0] != 'CLOSED':
        raise ValueError('B_LOG_LAUNCH_PROBE_NOT_CLOSED')
    parent_path = app_directory / 'parent-exit.tsv'
    parent = [line.split('\t') for line in _b_file(parent_path).decode('ascii').splitlines()]
    starts = [row for row in parent if row[0] == 'child.start']
    ends = [row for row in parent if row[0] == 'parent.end']
    if (len(starts) != 1 or len(starts[0]) != 3 or starts[0][2] != str(pid)
            or final and (len(ends) != 1 or len(ends[0]) != 6 or ends[0][2] != str(pid)
                          or ends[0][3] not in {'0', '-2'})):
        raise ValueError('B_LOG_OWNED_PID_OR_EXIT_DRIFT')
    started_epoch = int(starts[0][1]) / 1e9
    guard = ProcessLogGuard(target_directory / 'diagnostics', pid, binding['run_id'])
    guard.observe(final=final)
    paths = sorted((target_directory / 'diagnostics').glob('events-%s-*.jsonl' % pid))
    validation = validate_jsonl(paths, require_end=final)
    if validation['status'] != 'VALID':
        raise ValueError('B_LOG_INTEGRITY_INVALID')
    events, locations = [], {}
    for item in validation['records']:
        row = item['record']
        if any(row.get(key) != binding[key] for key in ('run_id', 'task_id', 'product_commit', 'test_commit', 'core_commit')):
            raise ValueError('B_LOG_PRODUCER_CANDIDATE_DRIFT')
        stamp = datetime.fromisoformat(row['ts_utc'])
        if stamp.tzinfo is None or stamp.timestamp() < started_epoch - 1:
            raise ValueError('B_LOG_OLD_PROCESS_OBSERVATION')
        if row['event'] == 'request.received' and row.get('case_id') == 'B-RPC-6':
            # Singular evidence_ref is an adapter reference, not a producer key.
            ref = 'b-log:' + hashlib.sha256(json.dumps(item['location'], sort_keys=True).encode()).hexdigest()
            locations[ref] = item['location']
            events.append(row | {'evidence_ref': ref})
    return {'events': events, 'prefixes': [_b_file_ref(path) for path in paths],
            'binding': binding, 'final': final, 'locations': locations,
            'launch_refs': [_b_file_ref(path) for path in (launch_path, probe_path, parent_path, target_directory / 'database.json')]}


def verify_b_log_prefixes(live, final):
    """An appended live segment is valid; replacement of any observed byte is not."""
    if final.get('final') is not True or any(item.get('binding') != final['binding'] for item in live):
        raise ValueError('B_LOG_FINAL_SOURCE_MISSING')
    final_paths = {item['path'] for item in final['prefixes']}
    for observation in live:
        for prefix in observation['prefixes']:
            if prefix['path'] not in final_paths:
                raise ValueError('B_LOG_PREFIX_SEGMENT_MISSING')
            raw = _b_file(prefix['path'])[:prefix['bytes']]
            if len(raw) != prefix['bytes'] or hashlib.sha256(raw).hexdigest() != prefix['sha256']:
                raise ValueError('B_LOG_LIVE_PREFIX_CHANGED')
    return True
