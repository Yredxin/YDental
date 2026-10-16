"""P0-14 frozen source seals and strictly read-only snapshots.

No Odoo imports or business write path. Source snapshots are separate connections.
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
OUT = ROOT / 'docs/evidence/s10-p0-14'
PRIVATE = ROOT / '.local/s10-p0-14'
BASE = '6c64403f9c015c669e50e750aff6e0e7a2eab3c0'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6212000008
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
    assert read(PRIVATE / 'remote-ref.json')['object']['sha'] == BASE
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent) == CORE
    assert not git('status', '--porcelain', '--untracked-files=no', cwd=ROOT.parent)
    for line in git('status', '--porcelain').splitlines():
        assert line[:2] == '??' and line[3:].startswith((
            'scripts/s10_p0_14_', 'docs/s10-p0-14-', 'docs/evidence/s10-p0-14/'))


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



IDENTITY_SQL = ('SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),'
                '(SELECT system_identifier::text FROM pg_control_system()),CURRENT_TIMESTAMP')
CONNECTION_SQL = 'SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()'
CATALOG_SQL = ("SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
               "JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' "
               "AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
TARGET_NAME_SQL = 'SELECT oid,datname FROM pg_database WHERE datname=%s'
TEMPLATE_CONNECTION_SQL = 'SELECT pid FROM pg_stat_activity WHERE datname=%s'


def credentials():
    conf = configparser.ConfigParser(interpolation=None)
    conf.read(FOLDER / 'odoo.conf')
    opts = conf['options']
    assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
    return dict(host='127.0.0.1', port=5432, user='odoo', password=opts['db_password'])


class ReadAudit:
    """One physical connection; fresh strictly read-only transaction per capture.

    The target-before connection remains open across the browser gates. Every
    capture rolls back its repeatable-read snapshot before the next request.
    Sources use separate objects and are closed before CREATE / after the run.
    """
    def __init__(self, name, label, expected_oid=None):
        self.name, self.label, self.expected_oid = name, label, expected_oid
        self.conn = None
        self.captures = 0
        save(PRIVATE / (label + '-connection-intent.json'), {'database': name, 'label': label,
             'utc_epoch': time.time(), 'attempt': 1, 'readonly': True})
        self.conn = psycopg2.connect(dbname=name, connect_timeout=5,
            options='-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=3000', **credentials())
        self.conn.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)

    def capture(self, tables=None):
        try:
            assert self.conn and not self.conn.closed
            assert self.conn.info.transaction_status == psycopg2.extensions.TRANSACTION_STATUS_IDLE
            self.captures += 1
            with self.conn.cursor() as cur:
                # This SHOW is the first statement after psycopg's explicit
                # BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY.
                cur.execute('SHOW transaction_read_only')
                assert cur.fetchone()[0] == 'on'
                cur.execute('SHOW transaction_isolation')
                assert cur.fetchone()[0] == 'repeatable read'
                cur.execute(IDENTITY_SQL)
                db, oid, cluster, now = cur.fetchone()
                assert db == self.name and cluster == CLUSTER
                if self.expected_oid is not None:
                    assert oid == self.expected_oid
                if self.name == NAME:
                    assert oid == OID
                    cur.execute(CONNECTION_SQL)
                    assert not cur.fetchall(), 'SOURCE_HAS_OTHER_CONNECTIONS'
                cur.execute(CATALOG_SQL)
                catalog = {}
                for table, column in cur.fetchall():
                    catalog.setdefault(table, []).append(column)
                expected = read(ROOT / 'docs/evidence/s10-p0-11/read-only-sql.json')['columns']
                assert catalog == expected and len(catalog) == 643, 'CATALOG_DRIFT'
                raw, signatures = {}, {}
                assert tables is None or self.name != NAME
                selected = sorted(catalog) if tables is None else sorted(tables)
                assert set(selected) <= set(catalog)
                for table in selected:
                    order = sql.Identifier('id') if 'id' in catalog[table] else sql.SQL('to_jsonb(t)::text')
                    query = sql.SQL('SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {}').format(sql.Identifier(table), order)
                    cur.execute(query)
                    values = [r[0] for r in cur.fetchall()]
                    raw[table] = values
                    signatures[table] = {'rows': len(values), 'sha256': sha(('\n'.join(values) + '\n').encode())}
                return {'database': db, 'oid': oid, 'cluster': cluster, 'database_time': now.isoformat(),
                        'columns': catalog, 'tables': raw, 'signatures': signatures,
                        'transaction': 'READ ONLY / REPEATABLE READ', 'backend_pid': self.conn.get_backend_pid(),
                        'connection_label': self.label, 'snapshot_number': self.captures,
                        'capture_scope': 'full643' if tables is None else 'minimal', 'captured_tables': selected}
        finally:
            if self.conn and not self.conn.closed:
                self.conn.rollback()

    def close(self):
        if self.conn is not None:
            try:
                self.conn.rollback()
            finally:
                self.conn.close()
                save(PRIVATE / (self.label + '-connection-closed.json'), {'database': self.name,
                     'closed': bool(self.conn.closed), 'rolled_back': True, 'captures': self.captures, 'utc_epoch': time.time()})


def verify_pointers(snap):
    seal, files = files_gate()
    pointers = [(r['store_fname'], r['checksum']) for r in map(json.loads, snap['tables']['ir_attachment']) if r.get('store_fname')]
    assert len(pointers) == 164
    for filename, checksum in pointers:
        assert filename in files
        assert hashlib.sha1((FOLDER / 'data/filestore' / NAME / filename).read_bytes()).hexdigest() == checksum
    old = read(ROOT / 'docs/evidence/s10-p0-10/read-only-sql.json')['sources']['W5']
    pointer_sha = sha(json.dumps(pointers).encode())
    assert pointer_sha == old['attachment_pointers_sha256']
    return {'seal': seal, 'attachment_pointer_count': len(pointers), 'attachment_pointer_sha256': pointer_sha}


def source_capture(label):
    audit = None
    try:
        files_gate()
        audit = ReadAudit(NAME, label, OID)
        snap = audit.capture()
        refs = read(ROOT / 'docs/evidence/s10-p0-13/source-after.json')['all_table_signatures']
        assert snap['signatures'] == refs, 'SOURCE_FULL643_HISTORICAL_DRIFT'
        protected = read(ROOT / 'docs/evidence/s10-p0-10/read-only-sql.json')['sources']['W5']['table_signatures']
        stable = read(ROOT / 'docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json')['target']['stable_31_sha256']
        assert len(protected) == 47 and len(stable) == 31
        assert all(snap['signatures'][t] == sig for t, sig in (protected | stable).items()), 'PROTECTED_OR_STABLE_DRIFT'
        pointers = verify_pointers(snap)
        filename = 'w5-private-rows.json' if label == 'source-before' else 'w5-after-private-rows.json'
        save(PRIVATE / filename, snap)
        result = {'status': 'SOURCE_SNAPSHOT_MATCH_ELIGIBILITY_PENDING_OFFLINE_REVIEW',
                  'authorization': AUTH, 'database': NAME, 'oid': OID, 'cluster': CLUSTER,
                  'database_time': snap['database_time'], 'backend_pid': snap['backend_pid'],
                  'all_table_signatures': snap['signatures'], 'public_table_count': len(snap['columns']),
                  'private_snapshot_sha256': sha((PRIVATE / filename).read_bytes()),
                  'baseline_mismatches': {}, 'historical_full643_match': True,
                  'protected47_match': True, 'stable31_match': True, **pointers}
        if label == 'source-after':
            before = read(PRIVATE / 'w5-private-rows.json')
            assert snap['tables'] == before['tables'], 'SOURCE_AFTER_DRIFT'
            result['source_before_after643_exact'] = True
            result['distinct_source_backend'] = snap['backend_pid'] != before['backend_pid']
        return snap, result
    finally:
        if audit:
            audit.close()
