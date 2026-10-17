"""Owned LC2 target creation and launch preparation; all mutations require dispatch."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time

from s10_lc2_evidence import ACCIDENT, CLUSTER, CORE, RAW_LIMIT, save_once
from s10_lc2_logging import strict_loads
from s10_lc2_supervisor import safe_plain, save_primary

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}\Z')


def _identifier(name):
    if not NAME.fullmatch(name):
        raise ValueError('UNAPPROVED_NEW_DATABASE_NAME')
    return '"' + name + '"'


def _private_parents(path):
    missing = []
    current = Path(path)
    while not current.exists():
        missing.append(current)
        current = current.parent
    for candidate in reversed(missing):
        candidate.mkdir(mode=0o700)
    if Path(path).is_symlink():
        raise RuntimeError('PRIVATE_TARGET_DIRECTORY_SYMLINK')


def source_filestore_inventory():
    """Read only, validate every current source byte against a valid retained index."""
    source_run = ROOT / '.local' / ACCIDENT
    source_marker = strict_loads((source_run / 'database.json').read_bytes())
    config_path = source_run / 'odoo.conf'
    if (config_path.is_symlink() or source_marker.get('database') != ACCIDENT
            or source_marker.get('oid') != 2144127 or source_marker.get('core') != CORE
            or source_marker.get('config_sha256') != hashlib.sha256(config_path.read_bytes()).hexdigest()):
        raise RuntimeError('SOURCE_CONFIG_OR_MARKER_DRIFT')
    config = configparser.ConfigParser(interpolation=None)
    config.read(config_path)
    source = Path(config['options']['data_dir']) / 'filestore' / ACCIDENT
    reference_path = ROOT / 'docs/evidence/s10-closeout-v1/source-before-filestore.json'
    expected = strict_loads(reference_path.read_bytes())
    actual = {}
    for path in sorted(source.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('SOURCE_FILESTORE_SYMLINK_FORBIDDEN')
        if not path.is_file():
            continue
        relative = str(path.relative_to(source))
        content_address = bool(re.fullmatch(r'[0-9a-f]{2}/[0-9a-f]{40}', relative))
        checklist_marker = bool(re.fullmatch(r'checklist/[0-9a-f]{2}/[0-9a-f]{40}', relative))
        if not content_address and not checklist_marker:
            raise RuntimeError('SOURCE_FILESTORE_UNEXPECTED_CONTENT_ADDRESS')
        sha256, sha1 = hashlib.sha256(), hashlib.sha1()
        length = 0
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(65536), b''):
                length += len(chunk)
                sha256.update(chunk)
                sha1.update(chunk)
        if content_address and sha1.hexdigest() != path.name:
            raise RuntimeError('SOURCE_FILESTORE_CONTENT_ADDRESS_MISMATCH')
        if checklist_marker and length != 0:
            raise RuntimeError('SOURCE_FILESTORE_CHECKLIST_MARKER_NOT_EMPTY')
        actual[relative] = {'bytes': length, 'sha256': sha256.hexdigest()}
    if actual != expected:
        raise RuntimeError('SOURCE_FILESTORE_VALID_REFERENCE_DRIFT')
    return {'source': str(source), 'reference': str(reference_path.relative_to(ROOT)), 'files': actual}


def create_targets(connect, connection_args, *, targets, directory, budget, main_admission):
    """One autocommit/IDLE maintenance connection, at most two CREATE statements.

    targets consists of role/name pairs. The main source is fixed; scratch uses
    template0. This function never drops, retries, kills connections or changes roles.
    """
    if (not targets or len(targets) > 2 or len({item['database'] for item in targets}) != len(targets)
            or any(item['role'] not in {'main', 'scratch'} for item in targets)
            or len({item['role'] for item in targets}) != len(targets)):
        raise ValueError('INVALID_TARGET_PLAN')
    for item in targets:
        _identifier(item['database'])
    if any(item['role'] == 'main' for item in targets) and main_admission.get('copy_admission') is not True:
        raise RuntimeError('MAIN_COPY_NOT_ADMITTED')
    if (connection_args.get('host'), str(connection_args.get('port')), connection_args.get('user')) != ('127.0.0.1', '5432', 'odoo'):
        raise RuntimeError('MAINTENANCE_ENDPOINT_NOT_APPROVED')
    directory = Path(directory)
    directory.mkdir(mode=0o700, parents=True, exist_ok=False)
    started = time.monotonic()
    created, connection, primary = [], None, None
    budget.consume('maintenance')
    try:
        connection = connect(dbname='postgres', connect_timeout=10, **connection_args)
        # Set autocommit before the first statement, without connection context manager.
        connection.autocommit = True
        if connection.get_transaction_status() != 0:
            raise RuntimeError('CREATE_REQUIRES_IDLE_AUTOCOMMIT')
        with connection.cursor() as cursor:
            def execute(query, params=None):
                remaining = int((178 - (time.monotonic() - started)) * 1000)
                if remaining <= 0:
                    raise TimeoutError('MAINTENANCE_WINDOW_EXHAUSTED')
                cursor.execute('SET statement_timeout=' + str(remaining))
                cursor.execute(query, params)

            execute('SET lock_timeout=3000')
            execute('SELECT system_identifier::text,current_user FROM pg_control_system()')
            if tuple(cursor.fetchone()) != (CLUSTER, 'odoo'):
                raise RuntimeError('MAINTENANCE_CLUSTER_OR_USER_DRIFT')
            execute('SELECT datname FROM pg_database WHERE datname=ANY(%s)', [[item['database'] for item in targets]])
            if cursor.fetchall():
                raise RuntimeError('NEW_TARGET_ALREADY_EXISTS')
            if any(item['role'] == 'main' for item in targets):
                execute('SELECT oid FROM pg_database WHERE datname=%s', [ACCIDENT])
                if cursor.fetchone()[0] != 2144127:
                    raise RuntimeError('COPY_SOURCE_OID_DRIFT')
                execute('SELECT pid,state FROM pg_stat_activity WHERE datname=%s ORDER BY pid', [ACCIDENT])
                active = cursor.fetchall()
                save_once(directory / 'source-connections.json', {'other_connections': active})
                if active:
                    raise RuntimeError('COPY_SOURCE_NOT_QUIESCENT')
            for item in targets:
                if connection.get_transaction_status() != 0 or not connection.autocommit:
                    raise RuntimeError('CREATE_REQUIRES_IDLE_AUTOCOMMIT')
                remaining = int((178 - (time.monotonic() - started)) * 1000)
                if remaining <= 0:
                    raise TimeoutError('MAINTENANCE_WINDOW_EXHAUSTED')
                budget.consume('create')
                if not safe_plain(directory / 'create-intents.tsv', [time.time_ns(), item['role'], item['database']]):
                    raise RuntimeError('CREATE_INTENT_NOT_PERSISTED')
                template = _identifier(ACCIDENT) if item['role'] == 'main' else 'template0'
                execute('CREATE DATABASE ' + _identifier(item['database']) + ' TEMPLATE ' + template + " ENCODING 'UTF8'")
                execute('SELECT oid FROM pg_database WHERE datname=%s', [item['database']])
                oid = cursor.fetchone()[0]
                created.append(item | {'oid': oid, 'cluster': CLUSTER, 'core': CORE})
                save_once(directory / (item['role'] + '-created.json'), created[-1])
    except BaseException as error:
        primary = save_primary(directory, error, stage='CREATE_WINDOW_STOP_NO_RETRY')
        raise
    finally:
        if connection is not None:
            try:
                connection.close()
                safe_plain(directory / 'maintenance-exit.tsv', ['CLOSED', time.time_ns()])
            except BaseException as secondary:
                save_primary(directory, secondary, stage='maintenance_close',
                             root_event_id=primary['event_id'] if primary else None)
                if primary is None:
                    raise
    if time.monotonic() - started > 180:
        raise TimeoutError('MAINTENANCE_TOTAL_WINDOW_EXHAUSTED')
    save_once(directory / 'created-databases.json', {'databases': created})
    return created


def prepare_target(item, *, run_root, port, product_commit, test_commit, budget):
    """New private target config and byte-copied main filestore, no application start."""
    database = item['database']
    _identifier(database)
    if port not in range(18410, 18420):
        raise ValueError('TARGET_PORT_NOT_APPROVED')
    run = Path(run_root).resolve() / database
    _private_parents(run.parent)
    run.mkdir(mode=0o700, parents=True, exist_ok=False)
    diagnostics = run / 'diagnostics'
    diagnostics.mkdir(mode=0o700)
    source_config = ROOT / '.local' / ACCIDENT / 'odoo.conf'
    source = configparser.ConfigParser(interpolation=None)
    source.read(source_config)
    options = source['options']
    config = configparser.ConfigParser(interpolation=None)
    config['options'] = {key: options[key] for key in ('db_host', 'db_port', 'db_user', 'db_password')}
    config['options'].update({
        'addons_path': str(ROOT.parent / 'addons') + ',' + str(ROOT),
        'db_name': database, 'dbfilter': '^' + database + '$', 'list_db': 'False',
        'http_interface': '127.0.0.1', 'http_port': str(port),
        'workers': '0', 'max_cron_threads': '0', 'db_maxconn': '4',
        'data_dir': str(run / 'data'), 'logfile': str(run / 'odoo-native.log'),
        'log_config': str(ROOT / 'config/logging-s10.example.json'),
        'log_level': 'info', 'without_demo': 'all',
    })
    config_path = run / 'odoo.conf'
    fd = os.open(config_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        config.write(stream)
        stream.flush()
        os.fsync(stream.fileno())
    marker = item | {'config_sha256': hashlib.sha256(config_path.read_bytes()).hexdigest(),
                     'product_commit': product_commit, 'test_commit': test_commit,
                     'lc2_role': item['role'], 'port': port}
    save_once(run / 'database.json', marker)
    if item['role'] == 'main':
        source_filestore = Path(options['data_dir']) / 'filestore' / ACCIDENT
        target_filestore = run / 'data' / 'filestore' / database
        files = []
        for path in sorted(source_filestore.rglob('*')):
            if path.is_symlink():
                raise RuntimeError('SOURCE_FILESTORE_SYMLINK_FORBIDDEN')
            if not path.is_file():
                continue
            relative = path.relative_to(source_filestore)
            target = target_filestore / relative
            _private_parents(target.parent)
            if budget.check_storage() + path.stat().st_size >= RAW_LIMIT * .9:
                raise RuntimeError('FILESTORE_COPY_WOULD_CROSS_RAW_STORAGE_PAUSE')
            with path.open('rb') as source_stream:
                target_fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(target_fd, 'wb') as target_stream:
                    shutil.copyfileobj(source_stream, target_stream, length=65536)
                    target_stream.flush()
                    os.fsync(target_stream.fileno())
            if path.stat().st_ino == target.stat().st_ino:
                raise RuntimeError('FILESTORE_HARDLINK_FORBIDDEN')
            original_sha = hashlib.sha256(path.read_bytes()).hexdigest()
            target_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            if original_sha != target_sha:
                raise RuntimeError('FILESTORE_COPY_BYTES_MISMATCH')
            files.append({'path': str(relative), 'bytes': target.stat().st_size, 'sha256': target_sha})
        save_once(run / 'initial-filestore-index.json', {'files': files, 'copied_not_hardlinked': True})
    return marker
