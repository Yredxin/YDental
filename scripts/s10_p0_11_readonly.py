"""P0-11 W5 preflight: offline seals, then one API-gated read-only snapshot.

No Odoo import, HTTP service, browser, DDL, DML, business ORM or CREATE path.
Full raw rows stay in the private directory. Only hashes leave that directory.
"""
import argparse
import ast
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import time

import psycopg2
from psycopg2 import sql


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-11'
PRIVATE = ROOT / '.local/s10-p0-11-6209310360'
BASE = '0c972e1949191d62d84536f987a40f26dba57e03'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6209310360
NAME = 'ydental_s10_test_20261015073500_e50f4a71'
OID = 2100310
CLUSTER = '7694897083368259627'
FOLDER = ROOT / '.local' / NAME
CONFIG_SHA = '867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7'
MARKER_SHA = '1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa'
MANIFEST_SHA = 'bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283'
P010_SQL_SHA = '3bbc7130ed4fa3575a1f4ee8e5ca527781c366bbddcaf6de0eb3d8853e0f65ea'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write('\n')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


def repository_gate():
    assert git('rev-parse', 'HEAD') == BASE
    assert git('branch', '--show-current') == BRANCH
    assert git('remote', 'get-url', 'origin') == 'https://github.com/Yredxin/YDental.git'
    assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == BASE
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent) == CORE
    assert not git('status', '--porcelain', '--untracked-files=no', cwd=ROOT.parent)
    for line in git('status', '--porcelain').splitlines():
        assert line[:2] == '??' and line[3:].startswith((
            'scripts/s10_p0_11_', 'docs/s10-p0-11-', 'docs/evidence/s10-p0-11/'))


def files_gate():
    assert sha((FOLDER / 'database.json').read_bytes()) == MARKER_SHA
    assert sha((FOLDER / 'odoo.conf').read_bytes()) == CONFIG_SHA
    marker = read(FOLDER / 'database.json')
    assert (marker['database'], marker['oid'], marker['cluster'], marker['core']) == (NAME, OID, CLUSTER, CORE)
    assert marker['config_sha256'] == CONFIG_SHA
    assert marker['source'] == 'ydental_s10_test_20261015064000_d41e7b62'
    assert marker['source_oid'] == 2100301
    path = ROOT / 'docs/evidence/s10-p0-10/read-only-sql.json'
    assert sha(path.read_bytes()) == P010_SQL_SHA
    p010 = read(path)['sources']['W5']
    assert marker['source_marker_sha256'] == p010['seal']['marker_source_marker_sha256']
    assert marker['source_config_sha256'] == p010['seal']['marker_source_config_sha256']
    files = {}
    base = FOLDER / 'data/filestore' / NAME
    assert base.is_dir() and not base.is_symlink()
    for path in sorted(base.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            files[str(path.relative_to(base))] = sha(path.read_bytes())
    manifest = sha(''.join(k + '\t' + files[k] + '\n' for k in sorted(files)).encode())
    assert len(files) == 152 and manifest == MANIFEST_SHA
    return {'database': NAME, 'oid': OID, 'cluster': CLUSTER, 'marker_sha256': MARKER_SHA,
            'config_sha256': CONFIG_SHA, 'w_manifest_sha256': manifest, 'file_count': len(files),
            'source': marker['source'], 'source_oid': marker['source_oid'],
            'source_marker_sha256': marker['source_marker_sha256'],
            'source_config_sha256': marker['source_config_sha256']}, files


def offline():
    repository_gate()
    seal, _ = files_gate()
    literals = [n.value for n in ast.walk(ast.parse(Path(__file__).read_text()))
                if isinstance(n, ast.Constant) and isinstance(n.value, str)
                and n.value.lstrip().upper().startswith(('SELECT ', 'SHOW '))]
    assert literals and all('FOR UPDATE' not in q.upper() and 'ADVISORY' not in q.upper() for q in literals)
    save(OUT / 'preflight.json', {
        'authorization': AUTH, 'base': BASE, 'core': CORE, 'branch': BRANCH,
        'script_sha256': sha(Path(__file__).read_bytes()), 'seal': seal,
        'sql_literals': literals, 'sql_connections_max': 1,
        'transaction': 'READ ONLY / REPEATABLE READ; rollback and close in finally',
        'private_snapshot': '.local/s10-p0-11-6209310360/w5-private-rows.json',
        'public_projection': 'full-row hashes only; raw contents and credentials never published',
        'create_allowed_now': False,
        'later_gate': 'All personnel/content/execution/QWeb/source checks required; freeze execution scripts in API checkpoint before CREATE',
        'maximum_authorized_budget': {'CREATE': 1, 'ODOO_HTTP_LAUNCH': 1, 'FIREFOX_LAUNCH': 1,
            'NATIVE_LOGIN_POST': 1, 'OPTIONAL_STORE_SWITCH_POST': 1, 'CLINICAL_WORKBENCH_GET': 2,
            'CLINICAL_ACTION_POST': 3, 'CLINICAL_HEARTBEAT_POST': 0,
            'OTHER_BUSINESS_POST': 0, 'PDF': 0, 'FUNDS_STOCK_WRITE': 0,
            'ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST': 0, 'SUDO': 0},
    })
    print('OFFLINE_SEALS_MATCH; SQL/CREATE/HTTP/Firefox/POST=0')


def capture():
    assert not (OUT / 'read-only-sql.json').exists()
    assert not (PRIVATE / 'sql-intent.json').exists(), 'no_repeat_snapshot'
    repository_gate()
    pre = read(OUT / 'preflight.json')
    check = read(OUT / 'preflight-api-readback.json')
    assert pre['script_sha256'] == check['script_sha256'] == sha(Path(__file__).read_bytes())
    assert check['preflight_sha256'] == sha((OUT / 'preflight.json').read_bytes())
    assert check['verbatim_equal'] and check['authorization'] == AUTH
    live = json.loads(subprocess.check_output(['gh', 'api',
        f"repos/Yredxin/YDental/issues/comments/{check['comment_id']}"]))
    assert live['body'] == check['body'] and sha(live['body'].encode()) == check['body_sha256']
    seal, files = files_gate()
    save(PRIVATE / 'sql-intent.json', {'utc_epoch': time.time(), 'database': NAME,
                                      'checkpoint_id': check['comment_id'], 'attempt': 1})
    conf = configparser.ConfigParser(interpolation=None)
    conf.read(FOLDER / 'odoo.conf')
    opts = conf['options']
    assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
    result = {'authorization': AUTH, 'checkpoint_id': check['comment_id'], 'seal': seal,
              'status': 'BLOCKED_PREFLIGHT', 'script_sha256': pre['script_sha256'],
              'CREATE': 0, 'HTTP': 0, 'Firefox': 0, 'ALL_POST': 0, 'SQL_ORM_WRITE': 0}
    conn = None
    started = time.time()
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=5432, user='odoo', password=opts['db_password'],
            dbname=NAME, connect_timeout=5, options='-c statement_timeout=15000 -c lock_timeout=3000')
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only')
            result['transaction_read_only'] = cur.fetchone()[0]
            cur.execute('SHOW transaction_isolation')
            result['transaction_isolation'] = cur.fetchone()[0]
            assert result['transaction_read_only'] == 'on' and result['transaction_isolation'] == 'repeatable read'
            cur.execute('SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),'
                        '(SELECT system_identifier::text FROM pg_control_system()),CURRENT_TIMESTAMP')
            name, oid, cluster, now = cur.fetchone()
            assert (name, oid, cluster) == (NAME, OID, CLUSTER)
            result.update(database=name, oid=oid, cluster=cluster, database_time=now.isoformat(), backend_pid=conn.get_backend_pid())
            cur.execute('SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')
            assert not cur.fetchall(), 'source_has_other_connections'
            cur.execute("SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' "
                        "AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            catalog = {}
            for table, column in cur.fetchall():
                catalog.setdefault(table, []).append(column)
            signatures, canonical_signatures, raw_tables = {}, {}, {}
            for table in sorted(catalog):
                order = sql.Identifier('id') if 'id' in catalog[table] else sql.SQL('to_jsonb(t)::text')
                cur.execute(sql.SQL('SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {}').format(sql.Identifier(table), order))
                rows = [r[0] for r in cur.fetchall()]
                signatures[table] = {'rows': len(rows), 'sha256': sha(('\n'.join(rows) + '\n').encode())}
                canonical_signatures[table] = {'rows': len(rows), 'sha256': sha(''.join(r + '\n' for r in sorted(rows)).encode())}
                raw_tables[table] = rows
            save(PRIVATE / 'w5-private-rows.json', {'database_time': now.isoformat(), 'columns': catalog, 'tables': raw_tables})
            p010 = read(ROOT / 'docs/evidence/s10-p0-10/read-only-sql.json')['sources']['W5']
            stable = read(ROOT / 'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json')['target']['stable_31_sha256']
            old = p010['table_signatures']
            mismatch = {t: {'expected': sig, 'actual': signatures.get(t)} for t, sig in (old | stable).items() if signatures.get(t) != sig}
            result.update(all_table_signatures=signatures, all_canonical_signatures=canonical_signatures,
                          public_table_count=len(catalog), baseline_table_count=len(old | stable),
                          stable_31_match=all(signatures.get(t) == sig for t, sig in stable.items()),
                          baseline_mismatches=mismatch, columns=catalog,
                          private_snapshot_sha256=sha((PRIVATE / 'w5-private-rows.json').read_bytes()))
            assert not mismatch, 'sealed_table_drift'
            pointers = [json.loads(row) for row in raw_tables['ir_attachment']]
            pointers = [(r['store_fname'], r['checksum']) for r in pointers if r.get('store_fname')]
            assert len(pointers) == 164
            for filename, checksum in pointers:
                assert filename in files
                assert hashlib.sha1((FOLDER / 'data/filestore' / NAME / filename).read_bytes()).hexdigest() == checksum
            result.update(attachment_pointer_count=len(pointers),
                          attachment_pointer_sha256=sha(json.dumps(pointers).encode()))
            assert result['attachment_pointer_sha256'] == p010['attachment_pointers_sha256']
            result['status'] = 'SOURCE_SNAPSHOT_MATCH_ELIGIBILITY_PENDING_OFFLINE_REVIEW'
    except (AssertionError, psycopg2.Error, OSError, ValueError) as error:
        result.update(error_type=type(error).__name__, sqlstate=getattr(error, 'pgcode', None))
        if isinstance(error, AssertionError):
            result['gate_error'] = str(error)
    finally:
        if conn is not None:
            try:
                conn.rollback()
                result['rolled_back'] = True
            finally:
                conn.close()
                result['closed'] = bool(conn.closed)
        result['duration_seconds'] = round(time.time() - started, 3)
        save(OUT / 'read-only-sql.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('all_table_signatures', 'all_canonical_signatures', 'columns')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['offline', 'sql'])
    args = parser.parse_args()
    if args.mode == 'offline':
        offline()
    else:
        capture()
