"""One source, one clone, bounded native processes. Never runs Odoo on source."""
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import s10_p0_22_contract as c

ACTIONS = ['A', 'B', 'C', 'prepare', 'T05-setup', 'T05-recover', 'revoke', 'upgrade']


def native_env(action):
    env = os.environ.copy()
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONFAULTHANDLER='1', PYTHONPATH=str(c.ROOT / '.local/s04-deps'),
               PGAPPNAME='s10-p0-22-' + action, PGOPTIONS=c.OPTIONS,
               YDENTAL_S10_RUN_DIR=str(c.RUN), YDENTAL_P022_ACTION=action,
               FONTCONFIG_FILE=str(c.ROOT / '.local/s00-b-deps/browser-fonts.conf'))
    return env


def create():
    import psycopg2
    from psycopg2 import sql
    c.gate(business=True)
    assert not c.RUN.exists()
    source = c.readonly('source-before', source=True)
    old = c.read(c.ROOT / '.local/s10-p0-21/final-RO-rows.json')
    c.persist('source-vs-accepted-P021-tail', old, source, c.exact)
    assert len(source['tables']) == 645 and not source['other_source_connections']
    source_files = c.filetree(c.SOURCE_RUN / 'data/filestore' / c.SOURCE)
    c.save(c.PRIVATE / 'source-before-files.json', source_files)
    c.save(c.OUT / 'source-before-filestore.json', source_files)
    prefix = '.local/' + c.SOURCE + '/data/filestore/' + c.SOURCE + '/'
    accepted_files = {row['path'][len(prefix):]: {'bytes': row['bytes'], 'sha256': row['sha256']}
                      for row in c.read(c.ROOT / 'docs/evidence/s10-p0-21/private-evidence-manifest.json')['files']
                      if row['path'].startswith(prefix)}
    assert source_files == accepted_files, 'SOURCE_FILESTORE_DRIFT_FROM_ACCEPTED_P021'
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', c.PORT))
    c.event('maintenance_intent', database='postgres')
    conn = psycopg2.connect(dbname='postgres', connect_timeout=5, options='-c statement_timeout=120000 -c lock_timeout=3000', **c.credentials())
    try:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute('SELECT oid,datname FROM pg_database ORDER BY oid')
            catalog = dict(cur.fetchall())
            assert c.NAME not in catalog.values() and catalog[c.SOURCE_OID] == c.SOURCE
            cur.execute('SELECT pid FROM pg_stat_activity WHERE datid=%s', (c.SOURCE_OID,))
            assert not cur.fetchall(), 'SOURCE_ACTIVE_CONNECTIONS_DO_NOT_TERMINATE'
            c.event('CREATE_intent', database=c.NAME, template=c.SOURCE)
            cur.execute(sql.SQL('CREATE DATABASE {} TEMPLATE {}').format(sql.Identifier(c.NAME), sql.Identifier(c.SOURCE)))
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s', (c.NAME,))
            oid = cur.fetchone()[0]
            assert oid not in catalog
    finally:
        conn.close()
        c.event('maintenance_closed')
    c.RUN.mkdir(mode=0o700)
    shutil.copyfile(c.PRIVATE / 'proposed-odoo.conf', c.RUN / 'odoo.conf')
    os.chmod(c.RUN / 'odoo.conf', 0o600)
    target = c.RUN / 'data/filestore' / c.NAME
    shutil.copytree(c.SOURCE_RUN / 'data/filestore' / c.SOURCE, target, copy_function=shutil.copy2)
    copied = c.filetree(target)
    assert source_files == copied
    for name in source_files:
        assert (target / name).stat().st_ino != (c.SOURCE_RUN / 'data/filestore' / c.SOURCE / name).stat().st_ino
    marker = {'database': c.NAME, 'oid': oid, 'cluster': c.CLUSTER, 'source_database': c.SOURCE,
              'source_oid': c.SOURCE_OID, 'authorization': c.AUTH, 'parent': c.BASE, 'core': c.CORE,
              'port': c.PORT, 'config_sha256': c.sha((c.RUN / 'odoo.conf').read_bytes())}
    c.save(c.RUN / 'database.json', marker)
    initial = c.readonly('clone-initial')
    c.persist('source-to-clone-initial', source, initial, c.exact)
    c.save(c.OUT / 'created-lineage.json', marker | {'all_initial_rows_exact': True, 'filestore_copied_no_hardlinks': True,
                                                  'filestore_file_count': len(copied)})
    c.event('CREATE_returned', database=c.NAME, oid=oid)


def run_native(action):
    freeze = c.gate(business=True)
    assert action in ACTIONS
    label = 'r%s-%s' % (freeze['round'], action)
    c.save(c.PRIVATE / (label + '-intent.json'), {'action': action, 'execution_HEAD': c.git('rev-parse', 'HEAD')})
    if action == 'upgrade':
        argv = [str(c.PYTHON), str(c.CORE_ROOT / 'odoo-bin'), '-c', str(c.RUN / 'odoo.conf'),
                '-u', 'ydental_settlement', '--without-demo=all', '--stop-after-init', '--no-http']
        timeout = 480
    else:
        argv = [str(c.PYTHON), str(c.ROOT / 'scripts/s10_p0_22_native.py'), action]
        timeout = 420
    log = c.RUN / (label + '.log')
    with log.open('xb') as stream:
        process = subprocess.Popen(argv, cwd=c.ROOT, env=native_env(label), stdin=subprocess.DEVNULL,
                                   stdout=stream, stderr=subprocess.STDOUT)
        try:
            code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.terminate(); process.wait(timeout=20)
            code = process.returncode
    raw = log.read_bytes()
    result = {'action': action, 'round': freeze['round'], 'pid': process.pid, 'exit_code': code,
              'SIGSEGV': code in {-11, 139} or b'Fatal Python error: Segmentation fault' in raw,
              'backend_creations': [int(n) for n in re.findall(rb'Create new connection backend PID (\d+)', raw)],
              'pool_max_observed': max([int(n) for n in re.findall(rb'ConnectionPool\([^)]*count=(\d+)', raw)] or [0]),
              'DSNs_observed': sorted({n.decode() for n in re.findall(rb'dbname=([^ ]+)', raw)}),
              'per_PID_DSN': 'UNKNOWN where native log omits it', 'log_sha256': c.sha(raw), 'log_bytes': len(raw)}
    c.save(c.OUT / (label + '-result.json'), result)
    if code:
        c.stop('NATIVE_PROCESS_FAILED:' + label)
    print(json.dumps(result))
    return code


def source_final():
    c.gate()
    source = c.readonly('source-final', source=True)
    before = c.read(c.PRIVATE / 'source-before-RO.json')
    c.persist('source-final-preservation', before, source, c.exact)
    files = c.filetree(c.SOURCE_RUN / 'data/filestore' / c.SOURCE)
    c.save(c.OUT / 'source-final-filestore.json', files)
    assert files == c.read(c.PRIVATE / 'source-before-files.json')
    c.save(c.OUT / 'source-final-preserved.json', {'all_645_tables_schema_rows_exact': True,
                                               'all_filestore_bytes_exact': True, 'source_connections': 2})


if __name__ == '__main__':
    os.umask(0o077)
    action = sys.argv[1]
    if action == 'create': create()
    elif action == 'source-final': source_final()
    elif action == 'final-tail': c.gate(); c.readonly('final-tail')
    else: sys.exit(run_native(action))
