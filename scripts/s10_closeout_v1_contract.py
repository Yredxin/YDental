"""CLOSEOUT frozen source/copy boundary and full physical-row evidence, no business DML."""
from collections import Counter, defaultdict
import configparser
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = ROOT.parent
BASE = '7d52d9e342d49837f3b81a7da3b6e7794a5cde01'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
SOURCE = 'ydental_s10_test_20261017050000_21b0cafe'
SOURCE_OID = 2122140
NAME = 'ydental_s10_test_20261017080710_2494c102'
PORT = 18325
CLUSTER = '7694897083368259627'
AUTH = 'USER_DIRECT_S10_CLOSEOUT_PLAN_v1.1'
PRIVATE = ROOT / '.local/s10-closeout-v1'
OUT = ROOT / 'docs/evidence/s10-closeout-v1'
RUN = ROOT / '.local' / NAME
SOURCE_RUN = ROOT / '.local' / SOURCE
PYTHON = CORE_ROOT / '.venv/bin/python'
OPTIONS = '-c statement_timeout=15000 -c lock_timeout=3000 -c timezone=UTC'
IDENTITY = 'SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),pg_backend_pid()'
CATALOG = "SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), default=str)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY:' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, sort_keys=True, ensure_ascii=False, indent=2, default=str)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    reopened = read(path)
    assert canonical(reopened) == canonical(value), ('SERIALIZED_READBACK_MISMATCH', str(path))


def event(name, **facts):
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'events.jsonl').open('a') as stream:
        stream.write(canonical({'event': name, **facts}) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


def current_freeze():
    return read(ROOT / read(PRIVATE / 'active-plan.json')['freeze_path'])


def stopped():
    if (PRIVATE / 'STOP-r1.json').exists():
        return True
    if not (PRIVATE / 'STOP.json').exists():
        return False
    freeze = current_freeze()
    if freeze['round'] != 1:
        return True
    permit = PRIVATE / 'repair-r1-approved.json'
    if not permit.exists():
        return True
    proof = read(permit)
    return not (proof['same_clone_only'] and proof['source_extra_final_RO_explicitly_approved']
                and proof['preserved_R0_STOP_sha256'] == sha((PRIVATE / 'STOP.json').read_bytes())
                and read(OUT / 'R1-offline-repair-check.json')['independent_tail_equals_pre_acquire'])


def gate(business=False):
    assert git('branch', '--show-current') == BRANCH
    assert git('remote', 'get-url', 'origin') == 'https://github.com/Yredxin/YDental.git'
    assert git('rev-parse', 'HEAD', cwd=CORE_ROOT) == CORE
    assert not git('status', '--porcelain', '--untracked-files=no', cwd=CORE_ROOT)
    approval = read(PRIVATE / 'user-approval.json')
    assert approval['selection'] == 'full_implementation'
    assert approval['user_execution_message_verbatim'] == 'Implement the plan.'
    plan = read(PRIVATE / 'active-plan.json')
    freeze = read(ROOT / plan['freeze_path'])
    sync = read(PRIVATE / plan.get('github_sync_path', 'github-preflight-sync.json'))
    assert sync['state'] in {'SYNCED_EXACT_READBACK', 'UNSYNCED'}
    if sync['state'] == 'SYNCED_EXACT_READBACK':
        raw = read(PRIVATE / sync['api_raw'])
        assert raw['id'] == sync['comment_id'] and raw['body'] == (PRIVATE / sync['body_path']).read_text()
    assert not sync.get('safety_refusal'), 'TOOL_SAFETY_REFUSAL_NO_BYPASS'
    assert sha((ROOT / plan['freeze_path']).read_bytes()) == plan['freeze_sha256']
    assert git('rev-parse', 'HEAD') == freeze['execution_commit']
    for path, digest in freeze['file_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == digest, ('FROZEN_DRIFT', path)
    if business:
        assert not stopped()
    return freeze


def credentials():
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(CORE_ROOT / 'odoo.conf')
    opt = parser['options']
    assert (opt['db_host'], opt['db_port'], opt['db_user']) == ('127.0.0.1', '5432', 'odoo')
    return dict(host='127.0.0.1', port=5432, user='odoo', password=opt['db_password'])


def economic(table):
    return table not in {'ydental_settlement_bill_original', 'ydental_settlement_mutex', 'ydental_settlement_receipt'} and (
        table.startswith(('account_', 'stock_', 'ydental_inventory_', 'ydental_treatment_', 'ydental_settlement_'))
        or table in {'ydental_intake_price', 'ydental_intake_snapshot', 'product_pricelist', 'product_pricelist_item', 'res_currency', 'res_currency_rate', 'uom_uom'})


def selected_table(table):
    return table.startswith(('ydental_', 'account_', 'stock_', 'hr_', 'resource_',
                             'res_users', 'res_groups', 'res_company', 'res_partner')) or table in {
        'ir_attachment', 'res_currency', 'res_currency_rate', 'uom_uom', 'product_product',
        'product_template', 'product_pricelist', 'product_pricelist_item'}


def capture(cur, database=NAME, full=False):
    cur.execute(IDENTITY)
    db, oid, cluster, pid = cur.fetchone()
    event('snapshot_identity', database=db, oid=oid, cluster=cluster, backend_pid=pid)
    expected = SOURCE_OID if database == SOURCE else read(RUN / 'database.json')['oid']
    assert db == database and oid == expected and cluster == CLUSTER
    cur.execute(CATALOG)
    schema = {}
    for table, column, kind in cur.fetchall():
        schema.setdefault(table, []).append({'column': column, 'type': kind})
    tables = {}
    capture_no = sum(1 for line in (OUT / 'events.jsonl').read_text().splitlines()
                     if json.loads(line)['event'] == 'snapshot_identity')
    raw_path = PRIVATE / ('capture-%04d-server-rows.jsonl' % capture_no)
    raw_stream = raw_path.open('x')
    complete = False
    try:
        for table, columns in sorted(schema.items()):
            if not full and not selected_table(table):
                continue
            # Identifiers come exclusively from this verified actual catalog.
            from psycopg2 import sql
            order = sql.Identifier('id') if any(c['column'] == 'id' for c in columns) else sql.SQL('to_jsonb(t)::text')
            query = sql.SQL("SELECT t.tableoid::regclass::text,t.tableoid,to_jsonb(t)::text,pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(to_jsonb(t)::text,'UTF8')),'hex') FROM public.{} t ORDER BY {}").format(sql.Identifier(table), order)
            cur.execute(query)
            tables[table] = []
            for physical, physical_oid, raw, server_digest in cur.fetchall():
                raw_stream.write(canonical({'requested_table': table, 'physical_table': physical,
                    'physical_oid': physical_oid, 'server_json_text': raw, 'server_sha256': server_digest}) + '\n')
                raw_stream.flush()
                assert sha(raw.encode('utf8')) == server_digest, ('SERVER_CLIENT_ROW_BYTES_MISMATCH', table)
                value = json.loads(raw, parse_float=Decimal)
                tables[table].append(value | {'__physical_table__': physical, '__physical_oid__': physical_oid})
        complete = True
    finally:
        raw_stream.flush(); os.fsync(raw_stream.fileno()); raw_stream.close()
        if not complete:
            save(OUT / ('capture-%04d-partial-layer.json' % capture_no), {'private_raw_file': str(raw_path.relative_to(ROOT)),
                'bytes': raw_path.stat().st_size, 'sha256': sha(raw_path.read_bytes()),
                'status': 'INCOMPLETE_NO_SNAPSHOT_PASS', 'tables_started': sorted(tables)})
    save(OUT / ('capture-%04d-layer.json' % capture_no), {'private_raw_file': str(raw_path.relative_to(ROOT)),
        'bytes': raw_path.stat().st_size, 'sha256': sha(raw_path.read_bytes()),
        'server_and_client_row_digests_equal': True, 'full': full, 'tables': len(tables)})
    return {'database': db, 'oid': oid, 'cluster': cluster, 'backend_pid': pid,
            'schema': schema, 'tables': tables, 'capture_scope': 'all_actual_physical_tables' if full else 'all_stored_business_identity_permission_original_attachment_facts'}


def diff(before, after):
    raw, index = [], []
    for table in sorted(before['tables'].keys() | after['tables'].keys()):
        left, right = defaultdict(list), defaultdict(list)
        for rows, dest in [(before['tables'].get(table, []), left), (after['tables'].get(table, []), right)]:
            for row in rows:
                dest[(row.get('__physical_table__', table), row.get('id', canonical(row)))].append(row)
        for key in sorted(left.keys() | right.keys(), key=str):
            a, b = left.get(key, []), right.get(key, [])
            if Counter(map(canonical, a)) == Counter(map(canonical, b)):
                continue
            columns = sorted(set().union(*(row.keys() for row in a + b)))
            if len(a) == len(b) == 1:
                columns = [col for col in columns if canonical(a[0].get(col)) != canonical(b[0].get(col))]
            item = {'table': table, 'physical_key': ['public', key[0], key[1]], 'columns': columns,
                    'before_count': len(a), 'after_count': len(b), 'economic': economic(table),
                    'before_sha256': sha(canonical(a).encode()), 'after_sha256': sha(canonical(b).encode()),
                    'duplicate_key_preserved': len(a) > 1 or len(b) > 1}
            raw.append(item | {'before': a, 'after': b})
            index.append(item)
    return raw, index


def persist(label, before, after, assertion):
    save(PRIVATE / (label + '-before.json'), before)
    save(PRIVATE / (label + '-after.json'), after)
    raw, index = diff(before, after)
    save(PRIVATE / (label + '-full-diff.json'), raw)
    save(OUT / (label + '-diff-index.json'), {'changes': index, 'schema_changed': before['schema'] != after['schema'],
                                           'all_values_saved_before_assertion': True})
    try:
        result = assertion(before, after, raw)
    except BaseException as error:
        save(OUT / (label + '-decision.json'), {'PASS': False, 'error_type': type(error).__name__,
                                              'detail_sha256': sha(str(error).encode()), 'evidence_first': True})
        raise
    save(OUT / (label + '-decision.json'), {'PASS': True, 'result': result, 'evidence_first': True})
    return result


def exact(before, after, changes):
    assert before['schema'] == after['schema'], 'SCHEMA_DRIFT'
    assert not changes, [(row['table'], row['physical_key'], row['columns']) for row in changes]
    return {'all_stored_rows_exact': True}


def readonly(label, source=False, full=False):
    import psycopg2
    database = SOURCE if source else NAME
    events = [json.loads(line) for line in (OUT / 'events.jsonl').read_text().splitlines()] if (OUT / 'events.jsonl').exists() else []
    assert sum(e['event'] == 'RO_intent' for e in events) < 28
    if source:
        cap = 2
        if (PRIVATE / 'source-budget-approval.json').exists():
            approval = read(PRIVATE / 'source-budget-approval.json')
            assert approval['additional_final_source_RO'] == 1 and approval['explicit_user_approval']
            assert approval['source'] == SOURCE and approval['oid'] == SOURCE_OID and approval['cluster'] == CLUSTER
            assert approval['source_cap'] == 3 and approval['total_explicit_RO_cap'] == 28 and approval['terminal_only']
            cap = 3
        assert label in {'source-before', 'source-final', 'source-final-r1'}
        assert sum(e['event'] == 'RO_intent' and e.get('database') == SOURCE for e in events) < cap
    event('RO_intent', label=label, database=database)
    conn = psycopg2.connect(dbname=database, connect_timeout=5, options='-c default_transaction_read_only=on ' + OPTIONS, **credentials())
    try:
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only'); assert cur.fetchone()[0] == 'on'
            cur.execute('SHOW transaction_isolation'); assert cur.fetchone()[0] == 'repeatable read'
            snapshot = capture(cur, database, full=source or full)
            if source:
                cur.execute('SELECT pid,state,application_name FROM pg_stat_activity WHERE datid=%s AND pid<>pg_backend_pid() ORDER BY pid', (SOURCE_OID,))
                snapshot['other_source_connections'] = cur.fetchall()
        save(PRIVATE / (label + '-RO.json'), snapshot)
        save(OUT / (label + '-RO-signatures.json'), {k: v for k, v in snapshot.items() if k not in {'tables', 'schema'}} | {
            'READ_ONLY': True, 'REPEATABLE_READ': True,
            'tables': {t: {'rows': len(rows), 'sha256': sha(canonical(rows).encode())} for t, rows in snapshot['tables'].items()}})
        return snapshot
    finally:
        conn.rollback(); conn.close(); event('RO_closed', label=label, database=database, rollback=True)


def filetree(root):
    root = Path(root)
    result = {}
    for path in sorted(root.rglob('*')):
        assert not path.is_symlink(), 'FILESTORE_SYMLINK'
        if path.is_file():
            result[str(path.relative_to(root))] = {'bytes': path.stat().st_size, 'sha256': sha(path.read_bytes())}
    return result


def stop(reason):
    path = PRIVATE / ('STOP-r1.json' if current_freeze()['round'] else 'STOP.json')
    if not path.exists():
        save(path, {'reason': reason, 'no_new_business': True})
    event('STOP', reason=reason)
