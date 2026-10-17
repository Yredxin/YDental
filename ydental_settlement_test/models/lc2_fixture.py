"""Private LC2 test fixtures; no routes, RPC methods, schema or business bypass.

Caller owns one new-target cursor and initializes its FIRST Environment as the
actual ordinary manager/actor. Helpers never commit or change default_env.
Credentials and limited tokens are RAM-only objects with hidden representations;
send them through the caller's anonymous pipe, never stdout or evidence JSON.
"""
from contextlib import closing
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat

from odoo.exceptions import AccessError
from odoo.tools.misc import limited_field_access_token, verify_limited_field_access_token


_CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
_CLUSTER = '7694897083368259627'
_PROTECTED = frozenset({'ydental_s10_test_20261017050000_21b0cafe',
                        'ydental_s10_test_20261017080710_2494c102'})
_TARGETS = {
    'ydental.settlement.source': ('ydental_settlement_source', 'ydental_original_amount'),
    'ydental.settlement.payment': ('ydental_settlement_payment', 'ydental_amount'),
    'ydental.access.audit': ('ydental_access_audit', 'ydental_reason'),
}


@dataclass(frozen=True)
class ReaderFixture:
    user_id: int
    manager_uid: int
    store_ids: tuple
    initial_levels: tuple
    login: str = field(repr=False)
    password: str = field(repr=False)
    owner: str = field(repr=False)


@dataclass(frozen=True)
class LimitedToken:
    original_id: int
    attachment_id: int
    verified: bool
    value: str = field(repr=False)


def _guard(env, run_directory, config_path=None):
    """Recheck only this existing connection; never connects to an old database."""
    directory = Path(run_directory)
    config = Path(config_path) if config_path is not None else directory / 'odoo.conf'
    database = env.cr.dbname
    if (database in _PROTECTED or not re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', database)
            or not directory.is_absolute() or directory.resolve() != directory
            or directory.name != database or config != directory / 'odoo.conf'
            or os.environ.get('YDENTAL_S10_RUN_DIR') != str(directory)):
        raise RuntimeError('LC2_FIXTURE_TARGET_NOT_OWNED')
    info = directory.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) != 0o700):
        raise RuntimeError('LC2_FIXTURE_DIRECTORY_NOT_PRIVATE')
    marker_path = directory / 'database.json'
    for path in (marker_path, config):
        info = path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600):
            raise RuntimeError('LC2_FIXTURE_FILE_NOT_PRIVATE')

    def pairs(items):
        result = {}
        for name, value in items:
            if name in result:
                raise ValueError('LC2_DUPLICATE_MARKER_KEY')
            result[name] = value
        return result

    def constant(value):
        raise ValueError('LC2_NONFINITE_MARKER_NUMBER')

    marker = json.loads(marker_path.read_bytes(), object_pairs_hook=pairs, parse_constant=constant)
    if (marker.get('database') != database or marker.get('cluster') != _CLUSTER
            or marker.get('core') != _CORE
            or marker.get('config_sha256') != hashlib.sha256(config.read_bytes()).hexdigest()):
        raise RuntimeError('LC2_FIXTURE_MARKER_DRIFT')
    env.cr.execute("SELECT current_database(), (SELECT oid FROM pg_database WHERE datname=current_database()), "
                   "(SELECT system_identifier::text FROM pg_control_system())")
    identity = env.cr.fetchone()
    if tuple(identity) != (database, marker.get('oid'), _CLUSTER):
        raise RuntimeError('LC2_FIXTURE_DATABASE_IDENTITY_DRIFT')
    return {'database': database, 'oid': identity[1], 'cluster': _CLUSTER, 'core': _CORE}


def _ordinary_actor(env, uid):
    default = env.transaction.default_env
    if (type(uid) is not int or uid <= 1 or env.uid != uid or env.su
            or default is None or default.uid != uid or default.su):
        raise RuntimeError('LC2_REAL_ACTOR_ENVIRONMENT_REQUIRED')
    if (not env.user.active or not env.user._is_internal()
            or not env.user.has_group('ydental_base.ydental_base_group_user')):
        raise RuntimeError('LC2_ACTIVE_INTERNAL_APPLICATION_ACTOR_REQUIRED')


def _actor_access(env):
    # A fresh fixture-only bound scope; never reuses a browser/session token.
    access = env['ydental.access.service']
    return access._bind(access._session_for_key(secrets.token_hex(24)))


def _row_sha(env, table, record_id):
    # Table identifiers come only from the literal mapping above, not caller SQL.
    if table not in {item[0] for item in _TARGETS.values()}:
        raise ValueError('LC2_UNAPPROVED_PROBE_TABLE')
    env.cr.execute("SELECT encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') "
                   'FROM public."' + table + '" t WHERE id=%s', [record_id])
    row = env.cr.fetchone()
    if row is None:
        raise RuntimeError('LC2_PROBE_TARGET_MISSING')
    return row[0]


def _model_denials(env, *, uid, targets, run_directory, config_path=None):
    """Exactly six real MODEL negatives; all attempts roll back independently."""
    identity = _guard(env, run_directory, config_path)
    _ordinary_actor(env, uid)
    if (type(targets) is not list or len(targets) != 3
            or {item.get('model') for item in targets} != set(_TARGETS)):
        raise ValueError('LC2_EXACT_THREE_PROBE_TARGETS_REQUIRED')
    results = []
    for target in targets:
        model = target['model']
        table, column = _TARGETS[model]
        record_id, values = target.get('id'), target.get('values')
        if (type(record_id) is not int or record_id <= 0 or type(values) is not dict
                or set(values) != {column}
                or (column == 'ydental_reason' and values[column] != 'LC2 denied tampering')
                or (column != 'ydental_reason' and (type(values[column]) not in (int, float) or values[column] != 1))):
            raise ValueError('LC2_PROBE_VALUES_NOT_APPROVED')
        for operation in ('write', 'unlink'):
            before = _row_sha(env, table, record_id)
            denied, exception_name = False, None
            with closing(env.cr.savepoint()):
                # Native flushing savepoint + restore_state, no default_env patch.
                ordinary = env[model].browse(record_id).with_user(uid)
                if ordinary.env.uid != uid or ordinary.env.su:
                    raise RuntimeError('LC2_PROBE_NOT_ORDINARY')
                try:
                    if operation == 'write':
                        ordinary.write(values)
                    else:
                        ordinary.unlink()
                except AccessError as error:
                    denied = True
                    exception_name = type(error).__module__ + '.' + type(error).__name__
            after = _row_sha(env, table, record_id)
            if before != after:
                raise RuntimeError('LC2_PROBE_TARGET_STORAGE_CHANGED')
            results.append({'layer': 'MODEL', 'model': model, 'id': record_id,
                            'operation': operation, 'actor_id': uid, 'effective_uid': uid,
                            'su_flag': False, 'denied': denied, 'exception_name': exception_name,
                            'existing_target_sha256': before, 'after_sha256': after,
                            'rollback_observed': True})
    return {'identity': identity, 'checks': results, 'six_denied': all(item['denied'] for item in results),
            'rpc_claimed': False}


def _levels(levels):
    if (type(levels) is not dict or set(levels) != {'settlement', 'export'}
            or levels['settlement'] not in {'none', 'read'}
            or levels['export'] not in {'none', 'read', 'write'}):
        raise ValueError('LC2_READER_LEVELS_INVALID')
    return dict(levels)


def _reader_owner(identity, run_directory):
    # Accidental cross-run protection, not an authentication credential.
    return hashlib.sha256(('%s:%s:%s' % (identity['database'], identity['oid'], run_directory)).encode()).hexdigest()


def _check_reader(env, fixture, identity, run_directory):
    if (type(fixture) is not ReaderFixture or fixture.owner != _reader_owner(identity, run_directory)
            or type(fixture.user_id) is not int or fixture.user_id <= 1):
        raise ValueError('LC2_READER_OWNERSHIP_REQUIRED')
    user = env['res.users'].browse(fixture.user_id).exists()
    if (not user or user.login != fixture.login or not fixture.login.startswith('lc2_c_')
            or user.name != 'LC2 synthetic C reader' or user.create_uid.id != fixture.manager_uid):
        raise RuntimeError('LC2_READER_IDENTITY_CHANGED')
    return user


def _create_reader(env, *, manager_uid, store_ids, run_directory, config_path=None,
                   initial_levels=None):
    identity = _guard(env, run_directory, config_path)
    _ordinary_actor(env, manager_uid)
    if (type(store_ids) not in (list, tuple) or not 1 <= len(store_ids) <= 3
            or len(set(store_ids)) != len(store_ids) or any(type(item) is not int or item <= 0 for item in store_ids)):
        raise ValueError('LC2_READER_STORE_SET_INVALID')
    levels = _levels({'settlement': 'read', 'export': 'write'} if initial_levels is None else initial_levels)
    access = _actor_access(env)
    login = 'lc2_c_' + secrets.token_hex(16)
    if env['res.users'].search_count([('login', '=', login)]):
        raise RuntimeError('LC2_NEW_READER_LOGIN_COLLISION')
    result = access._create_account('LC2 synthetic C reader', login, store_ids[0])
    user_id = result['user_id']
    # Return a password only in RAM. Caller first commits the manager creation,
    # then initializes it with a NEW own cursor whose first env is this user.
    password = secrets.token_urlsafe(32)
    initial = []
    for store_id in store_ids:
        if store_id != store_ids[0]:
            access._join(user_id, store_id)
        access._grant(user_id, store_id, levels, source='lc2_new_reader_fixture')
        actual = access._levels(access._membership(user_id, store_id))
        initial.append((store_id, tuple(sorted(actual.items()))))
    access.env.flush_all()
    return ReaderFixture(user_id, manager_uid, tuple(store_ids), tuple(initial), login, password,
                         _reader_owner(identity, run_directory))


def _initialize_reader_password(env, fixture, *, run_directory, config_path=None):
    """New user's own-cursor initialization, with no mixed-UID dirty transaction."""
    identity = _guard(env, run_directory, config_path)
    _ordinary_actor(env, fixture.user_id)
    user = _check_reader(env, fixture, identity, run_directory)
    user.write({'password': fixture.password})
    env.flush_all()
    return {'user_id': fixture.user_id, 'own_password_initialized': True,
            'actor_id': env.uid, 'su_flag': env.su}


def _reader_permissions(env, fixture, *, levels=None, restore=False, store_id=None,
                        run_directory, config_path=None):
    identity = _guard(env, run_directory, config_path)
    _check_reader(env, fixture, identity, run_directory)
    _ordinary_actor(env, fixture.manager_uid)
    if type(restore) is not bool or restore == (levels is not None):
        raise ValueError('LC2_RESTORE_OR_EXPLICIT_LEVELS_REQUIRED')
    stores = fixture.store_ids if store_id is None else (store_id,)
    if not set(stores) <= set(fixture.store_ids):
        raise ValueError('LC2_READER_STORE_NOT_OWNED')
    access = _actor_access(env)
    result = []
    for current in stores:
        desired = dict(dict(fixture.initial_levels)[current]) if restore else _levels(levels)
        if restore:
            _levels({name: desired[name] for name in ('settlement', 'export')})
            if any(value != 'none' for name, value in desired.items() if name not in {'settlement', 'export'}):
                raise ValueError('LC2_RESTORE_CANNOT_EXPAND_READER_PRIVILEGES')
        access._grant(fixture.user_id, current, desired, source='lc2_new_reader_restore' if restore else 'lc2_new_reader_fixture')
        access.env.flush_all()
        actual = access._levels(access._membership(fixture.user_id, current))
        if any(actual[name] != value for name, value in desired.items()):
            raise RuntimeError('LC2_READER_LEVEL_VERIFICATION_FAILED')
        result.append({'store_id': current, 'levels': desired})
    return {'user_id': fixture.user_id, 'restored': restore, 'stores': result}


def _limited_token(env, *, original_id, run_directory, config_path=None):
    """Generate a genuine limited HMAC in RAM; never writes access_token."""
    _guard(env, run_directory, config_path)
    _ordinary_actor(env, env.uid)
    if type(original_id) is not int or original_id <= 0:
        raise ValueError('LC2_ORIGINAL_ID_INVALID')
    access = _actor_access(env)
    service = access.env['ydental.settlement.service']
    original = service._model('bill.original').browse(original_id).exists()
    if not original:
        raise AccessError('LC2 original unavailable')
    session = access._scope()
    access._switch(original.store_id.id)
    access = access._bind(session)
    service = access.env['ydental.settlement.service']
    invoice, sources, patient, store = service._original_invoice(original.invoice_id.id)
    if (original.store_id != store or original.company_id != store.company_id
            or original.patient_id.id not in service._patient_family_ids(patient)):
        raise AccessError('LC2 original outside the authorized source')
    attachment = original.attachment_id
    if (not attachment or attachment.res_model != original._name or attachment.res_id != original.id
            or attachment.company_id != store.company_id or attachment.public or attachment.access_token):
        raise AccessError('LC2 original attachment unavailable')
    value = limited_field_access_token(attachment, 'raw', scope='binary')
    verified = verify_limited_field_access_token(attachment, 'raw', value, scope='binary')
    if not verified:
        raise RuntimeError('LC2_LIMITED_TOKEN_VERIFICATION_FAILED')
    return LimitedToken(original.id, attachment.id, True, value)
