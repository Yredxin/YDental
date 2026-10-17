"""P024 single-field read-only contract. No database connection at import time."""
import configparser
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / '.local/s10-p0-24'
OUT = ROOT / 'docs/evidence/s10-p0-24'
DATABASE = 'ydental_s10_test_20261017060000_22b0cafe'
OID = 2144126
CLUSTER = '7694897083368259627'
KEY = 'account.portal_my_journal_mail_notifications'
BASELINE_SHA = '776c4257a3567c92aa3e46aa5dc2c4e5a714989be88ab59714452dfeb4042664'
OPTIONS = '-c default_transaction_read_only=on -c statement_timeout=5000 -c lock_timeout=5000 -c timezone=UTC -c client_encoding=UTF8'
MAX_RETURN = 65536
BEGIN = 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;'
SHOW_RO = 'SHOW transaction_read_only;'
SHOW_ISO = 'SHOW transaction_isolation;'
ROLLBACK = 'ROLLBACK;'
IDENTITY = """SELECT pg_catalog.jsonb_build_object(
 'kind','identity', 'database',pg_catalog.current_database(),
 'database_oid',(SELECT oid::bigint FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()),
 'cluster',(SELECT system_identifier::text FROM pg_catalog.pg_control_system()),
 'backend_pid',pg_catalog.pg_backend_pid(), 'server_time',pg_catalog.clock_timestamp(),
 'transaction_start',pg_catalog.transaction_timestamp(), 'snapshot',pg_catalog.pg_current_snapshot()::text,
 'read_only',pg_catalog.current_setting('transaction_read_only'),
 'isolation',pg_catalog.current_setting('transaction_isolation'),
 'server_encoding',pg_catalog.getdatabaseencoding(), 'client_encoding',pg_catalog.current_setting('client_encoding'),
 'server_version',pg_catalog.current_setting('server_version'),
 'server_version_num',pg_catalog.current_setting('server_version_num')
)::text;"""
TARGET = """SELECT pg_catalog.jsonb_build_object(
 'kind','target', 'id',v.id, 'key',v.key,
 'table_oid',v.tableoid::bigint, 'physical_table',v.tableoid::regclass::text,
 'arch_prev_type',pg_catalog.pg_typeof(v.arch_prev)::text, 'arch_prev_is_null',v.arch_prev IS NULL,
 'arch_prev_text',v.arch_prev, 'arch_prev_characters',pg_catalog.char_length(v.arch_prev),
 'arch_prev_UTF8_bytes',pg_catalog.octet_length(pg_catalog.convert_to(v.arch_prev,'UTF8')),
 'arch_prev_UTF8_hex',pg_catalog.encode(pg_catalog.convert_to(v.arch_prev,'UTF8'),'hex'),
 'arch_prev_server_sha256',pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(v.arch_prev,'UTF8')),'hex'),
 'arch_db_type',pg_catalog.pg_typeof(v.arch_db)::text, 'arch_db_is_null',v.arch_db IS NULL,
 'arch_db_server_sha256',pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(v.arch_db::text,'UTF8')),'hex'),
 'write_uid',v.write_uid, 'write_date',v.write_date,
 'server_time',pg_catalog.clock_timestamp(), 'backend_pid',pg_catalog.pg_backend_pid(),
 'transaction_start',pg_catalog.transaction_timestamp(), 'snapshot',pg_catalog.pg_current_snapshot()::text,
 'server_encoding',pg_catalog.getdatabaseencoding(), 'client_encoding',pg_catalog.current_setting('client_encoding')
)::text FROM public.ir_ui_view AS v
WHERE v.id=929 AND v.key='account.portal_my_journal_mail_notifications';"""
STATEMENTS = [('begin', BEGIN), ('show-readonly', SHOW_RO), ('show-isolation', SHOW_ISO),
              ('identity', IDENTITY), ('target', TARGET), ('rollback', ROLLBACK)]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def parse(raw):
    def pairs(items):
        obj = {}
        for key, value in items:
            if key in obj:
                raise ValueError('DUPLICATE_JSON_KEY')
            obj[key] = value
        return obj
    def nonfinite(value):
        raise ValueError('NONFINITE_JSON_NUMBER')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=nonfinite)


def write(path, raw):
    """New files only. Persist first, then reopen and record byte-level equality."""
    path = Path(path)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    readback = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'intended_bytes': len(raw), 'intended_sha256': sha(raw),
            'readback_bytes': len(readback), 'readback_sha256': sha(readback), 'bytes_equal': raw == readback}


def save(path, value):
    return write(path, encode(value))


def gate():
    proof = parse((PRIVATE / 'preflight-api-readback.json').read_bytes())
    assert proof['body_exact'] is True
    assert sha((OUT / 'freeze.json').read_bytes()) == proof['freeze_sha256']
    freeze = parse((OUT / 'freeze.json').read_bytes())
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == freeze['execution_commit']
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip() == 'codex/s10-settlement-finance-r1-20261013'
    assert subprocess.check_output(['git', 'remote', 'get-url', 'origin'], cwd=ROOT, text=True).strip() == 'https://github.com/Yredxin/YDental.git'
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT.parent, text=True).strip() == 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
    api = parse((PRIVATE / 'preflight-api-raw.json').read_bytes())
    assert api['id'] == proof['comment_id'] and api['body'] == (PRIVATE / 'preflight-body.txt').read_text()
    for name, digest in freeze['files'].items():
        assert sha((ROOT / name).read_bytes()) == digest, ('FROZEN_INPUT_DRIFT', name)
    return freeze


def credentials():
    path = ROOT.parent / 'odoo.conf'
    ref = parse((PRIVATE / 'credential-reference.json').read_bytes())
    assert sha(path.read_bytes()) == ref['config_sha256'], 'PRIVATE_CONFIG_DRIFT'
    config = configparser.ConfigParser(interpolation=None)
    config.read(path)
    v = config['options']
    assert (v['db_host'], v['db_port'], v['db_user']) == ('127.0.0.1', '5432', 'odoo')
    assert v['db_password']
    return {'host': '127.0.0.1', 'port': 5432, 'user': 'odoo', 'password': v['db_password']}


def identity_ok(row):
    return (row['database'] == DATABASE and row['database_oid'] == OID and row['cluster'] == CLUSTER
            and row['read_only'] == 'on' and row['isolation'] == 'repeatable read'
            and row['server_encoding'] == row['client_encoding'] == 'UTF8')


def target_ok(row):
    return (row.get('id') == 929 and row.get('key') == KEY and row.get('table_oid') == 2122563
            and row.get('physical_table') in ['ir_ui_view', 'public.ir_ui_view']
            and row.get('arch_prev_type') == 'text' and row.get('arch_prev_is_null') is False
            and isinstance(row.get('arch_prev_text'), str) and isinstance(row.get('arch_prev_UTF8_bytes'), int)
            and row['arch_prev_UTF8_bytes'] <= 8192)


def analyze(label):
    """After rollback/close: persist raw, parse, encode, fsync, reopen, compare."""
    base = PRIVATE / label
    raw = (base / 'target-return.utf8').read_bytes()
    if len(raw) > MAX_RETURN:
        save(base / 'analysis.json', {'completed': False, 'reason': 'TARGET_RETURN_EXCEEDS_65536', 'actual_bytes': len(raw)})
        return False
    try:
        row = parse(raw)
    except BaseException as error:
        save(base / 'analysis.json', {'completed': False, 'reason': 'STRICT_TARGET_JSON_PARSE_FAILED', 'error': type(error).__name__, 'raw_sha256': sha(raw)})
        return False
    save(base / 'parsed-server-envelope.json', row)
    if not isinstance(row, dict):
        save(base / 'analysis.json', {'completed': False, 'reason': 'SERVER_ENVELOPE_NOT_OBJECT'})
        return False
    value = row.get('arch_prev_text')
    if not isinstance(value, str):
        save(base / 'analysis.json', {'completed': False, 'reason': 'TEXT_MISSING_OR_NULL', 'server_result_preserved': True})
        return False
    field = value.encode('utf-8')
    field_io = write(base / 'parsed-field.utf8', field)
    serialized = encode(row)
    serialized_io = write(base / 'serialized.json', serialized)
    disk = (base / 'serialized.json').read_bytes()
    write(base / 'serialized-reopened.bin', disk)
    try:
        reparsed = parse(disk)
        semantics = reparsed == row
        parse_error = None
    except BaseException as error:
        semantics = False; parse_error = type(error).__name__
    comparisons = {'server_vs_client_characters': len(value) == row.get('arch_prev_characters'),
                   'server_vs_client_UTF8_bytes': len(field) == row.get('arch_prev_UTF8_bytes'),
                   'server_vs_client_UTF8_hex': field.hex() == row.get('arch_prev_UTF8_hex'),
                   'server_vs_client_sha256': sha(field) == row.get('arch_prev_server_sha256'),
                   'field_write_readback_bytes': field_io['bytes_equal'],
                   'serialized_write_readback_bytes': serialized_io['bytes_equal'] and serialized == disk,
                   'serialized_reparse_semantics': semantics}
    if (base / 'target-receive-write.json').exists():
        receipt = parse((base / 'target-receive-write.json').read_bytes())
        comparisons['raw_client_return_write_readback_bytes'] = receipt['bytes_equal']
    if (base / 'identity-parsed.json').exists():
        identity = parse((base / 'identity-parsed.json').read_bytes())
        for key in ['backend_pid', 'transaction_start', 'snapshot', 'server_encoding', 'client_encoding']:
            comparisons['same_transaction_' + key] = row.get(key) == identity.get(key)
    result = {'completed': True, 'label': label, 'target_identity_and_type_ok': target_ok(row),
              'server_sha256': row.get('arch_prev_server_sha256'), 'client_field_sha256': sha(field),
              'server_digest_source': "same target SELECT: encode(sha256(convert_to(v.arch_prev,'UTF8')),'hex')",
              'active_digest_source': "same SELECT: sha256(convert_to(v.arch_db::text,'UTF8')); active text NOT selected",
              'raw_envelope_sha256': sha(raw), 'raw_is_not_wire_protocol': True,
              'parsed_type': type(value).__name__, 'characters': len(value), 'UTF8_bytes': len(field),
              'historical_field_sha_match': sha(field) == BASELINE_SHA,
              'comparisons': comparisons, 'field_io': field_io, 'serialized_io': serialized_io,
              'reparse_error': parse_error, 'all_layer_comparisons_match': all(comparisons.values())}
    save(base / 'analysis.json', result)  # save all differences before deciding
    return result['target_identity_and_type_ok'] and result['all_layer_comparisons_match']
