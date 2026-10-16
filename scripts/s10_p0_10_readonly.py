"""P0-10: five fixed synthetic sources, SELECT/SHOW only, rollback and close.

Offline mode never connects. SQL mode requires an API-verbatim checkpoint binding
this exact script and preflight bytes. No Odoo import, registry, browser or POST.
"""
import argparse
import ast
import base64
import configparser
import hashlib
import json
from pathlib import Path
import subprocess
import time

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/evidence/s10-p0-10'
BASE = '22d4762c8ddc0b8254b3492fe3ccc75664b5cf47'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
CLUSTER = '7694897083368259627'
AUTH = 6208516504
SOURCES = {
    'P009': ('ydental_s10_test_20261016_p009_9e51b7c2', 2100324, BASE),
    'R3': ('ydental_s10_test_20261014020300_8b6c1d4e', 2056451, 'f24b0302569aefaa394391da6b696d915e3f0616'),
    'W3': ('ydental_s10_test_20261015060000_b6c7d8e9', 2100285, '71a554667157cdd917c0062db5e4ddf1693f6410'),
    'W4': ('ydental_s10_test_20261015064000_d41e7b62', 2100301, '79417da9043478501ffae586f93eebc1e5d7105d'),
    'W5': ('ydental_s10_test_20261015073500_e50f4a71', 2100310, '287881a824e9a18dd637522c570f74df139078f9'),
}
# Explicitly projected IDs, synthetic amounts, states, dates and immutable hashes.
# Names, medical text, addresses, credentials, keys and session tokens never leave memory.
FIELDS = frozenset('''id company_id currency_id partner_id product_id product_uom_id
move_id move_type state amount_total amount_residual payment_state journal_id account_id
debit credit balance quantity price_unit price_subtotal lot_id location_id location_dest_id
payment_type partner_type amount debit_move_id credit_move_id origin_payment_id invoice_date date
settlement_payment_id invoice_id active create_uid write_uid create_date write_date
payment_id quantity_product_uom
'''.split())
YD_FIELDS = frozenset(('ydental_' + name) for name in '''
store_id patient_id actor_id author_id responsible_id doctor_id pharmacist_id cashier_id user_id
execution_id document_id document_version order_id order_line_id parent_id kind catalog_id
medicine_link_id product_id quantity uom_id actual_at business_date station_id already_performed
price_snapshot_id price_review_id event_id unit_price currency_id amount price_id snapshot_id
invoice_id line_id original_amount discount source_business_date source_actual_at price_version
payment_id native_payment_id credit_note_id approver_id requester_id state entered_at
recorded_at confirmed_at confirmed_by_id unlocked_at unlocked_by_id channel old_channel new_channel
move_id refund_business_date refund_channel cycle gross refunded pending revision version
number document_id previous_id result_id line_id lot_id batch_id stock_move_id stock_move_line_id
source_location_id target_location_id source_id source_store_id target_store_id target_lot_id
source_lot_id source_event_id inventory_event_id consumption_id segment_id mapping_id task_id
source_digest pdf_digest template expires_at inventory_operation_id operation event result
model record_id target_id target_model session_id returned_quantity requested_quantity dispensed_quantity
valid_from valid_to valid_until effective_from effective_to start_at end_at price
'''.split())
HASH_FIELDS = ('ydental_reason', 'ydental_unlock_reason', 'ydental_content', 'ydental_payload',
               'ydental_source', 'ydental_versions', 'ydental_request_key', 'ydental_fingerprint')
TABLES = tuple('''ydental_access_store ydental_access_membership ydental_access_grant
 ydental_patient ydental_patient_relation ydental_intake_price ydental_intake_snapshot ydental_intake_task
 ydental_queue_entry ydental_queue_execution ydental_queue_lease ydental_clinical_document
 ydental_clinical_version ydental_treatment_order ydental_treatment_line ydental_treatment_segment
 ydental_treatment_event ydental_treatment_fee ydental_treatment_consumption ydental_exam_result
 ydental_exam_version ydental_inventory_event ydental_inventory_batch stock_move stock_move_line
 stock_quant stock_lot account_move account_move_line account_payment account_partial_reconcile
 ydental_settlement_source ydental_settlement_receipt ydental_settlement_payment
 ydental_settlement_payment_invoice_rel ydental_settlement_refund ydental_settlement_close
 ydental_settlement_correction ydental_settlement_mutex ydental_print_job ydental_exam_receipt
 ydental_treatment_receipt ydental_settlement_config ydental_access_audit ydental_access_session
'''.split())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads((ROOT / path).read_text())


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + '\n')


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args], text=True).strip()


def identities():
    v = load('docs/evidence/s10-p0-09/verification.json')
    w4 = load('docs/evidence/s10-e2e-w4/verification.json')
    w5 = load('docs/evidence/s10-e2e-w5/verification.json')
    r3 = v['histories_after'][SOURCES['R3'][0]]
    return {'P009': v['target'], 'R3': r3, 'W3': w4['source'],
            'W4': w5['source'], 'W5': w5['target']}


def files_gate(key, expected):
    name, oid, commit = SOURCES[key]
    folder = ROOT / '.local' / name
    assert folder.is_dir() and not folder.is_symlink()
    paths = [folder / 'database.json', folder / 'odoo.conf']
    assert all(p.is_file() and not p.is_symlink() for p in paths)
    marker = json.loads(paths[0].read_text())
    hashes = {'marker_sha256': sha(paths[0].read_bytes()), 'config_sha256': sha(paths[1].read_bytes())}
    assert all(hashes[k] == expected[k] for k in hashes), 'seal_hash_mismatch'
    assert marker['database'] == name and marker['oid'] == oid
    assert marker['cluster'] == CLUSTER and marker['core'] == CORE
    assert marker['config_sha256'] == hashes['config_sha256']
    return {'database': name, 'oid': oid, 'fixed_commit': commit, **hashes,
            'marker_source': marker.get('source'), 'marker_source_oid': marker.get('source_oid'),
            'marker_source_marker_sha256': marker.get('source_marker_sha256'),
            'marker_source_config_sha256': marker.get('source_config_sha256')}


def offline():
    assert git('rev-parse', 'HEAD') == BASE
    assert git('branch', '--show-current') == BRANCH
    assert git('remote', 'get-url', 'origin') == 'https://github.com/Yredxin/YDental.git'
    assert git('rev-parse', 'HEAD', cwd=ROOT.parent) == CORE
    assert not git('status', '--porcelain', '--untracked-files=no', cwd=ROOT.parent)
    assert git('ls-remote', 'origin', 'refs/heads/' + BRANCH).split()[0] == BASE
    for line in git('status', '--porcelain').splitlines():
        assert line[:2] == '??' and allowed(line[3:]), ('unexpected_change', line)
    # Historical inputs are read at their fixed commit, then byte-compared locally.
    gap = load('docs/evidence/s10-gap-01/coverage.json')
    paths = [(BASE, p) for p in ['docs/s10-gap-01-evidence-matrix.md',
             'docs/s10-gap-01-next-batch-proposals.md', 'docs/evidence/s10-gap-01/coverage.json']]
    for e in gap['source_evidence'].values():
        paths.extend((e['commit'], e[k]) for k in ('report', 'machine_index'))
    for n in range(2, 10):
        report = next(ROOT.glob(f'docs/s10-p0-{n:02d}-*report.md'))
        commit = git('log', '-1', '--format=%H', '--', str(report.relative_to(ROOT)))
        paths.extend((commit, str(p.relative_to(ROOT))) for p in sorted((ROOT/f'docs/evidence/s10-p0-{n:02d}').glob('*.json')))
        paths.append((commit, str(report.relative_to(ROOT))))
    records = []
    for commit, path in paths:
        raw = subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{commit}:{path}'])
        assert raw == (ROOT / path).read_bytes(), ('historical_file_drift', path)
        records.append({'commit': commit, 'path': path, 'sha256': sha(raw), 'bytes': len(raw)})
    assert sha((ROOT/'docs/evidence/s10-p0-09/verification.json').read_bytes()) == '3c3c49dbec6c93ec89ce766fea93ff8926691bf28a8e8a8939a671302db994a5'
    assert sha((ROOT/'docs/evidence/s10-p0-09/business-before-after.json').read_bytes()) == '97a9cd9e394e73e4a5acaa9595930474d1bf3961fe79a88fb79536e017bf4378'
    seals = {}
    for key, expected in identities().items():
        try:
            seals[key] = {'status': 'STATIC_FILE_IDENTITY_MATCH', **files_gate(key, expected)}
        except (AssertionError, OSError, KeyError, ValueError) as error:
            seals[key] = {'status': 'UNAVAILABLE_OR_DRIFT', 'error_type': type(error).__name__, 'sql': 'NOT_RUN'}
    # Freeze every literal SQL query, including composable identifier-only statements.
    tree = ast.parse(Path(__file__).read_text())
    queries = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)
               and n.value.lstrip().upper().startswith(('SELECT ', 'SHOW '))]
    assert queries and all('FOR UPDATE' not in q.upper() and 'ADVISORY' not in q.upper() for q in queries)
    result = {'authorization': AUTH, 'base': BASE, 'branch': BRANCH, 'core': CORE,
              'script_sha256': sha(Path(__file__).read_bytes()), 'sources': seals,
              'historical_inputs': records, 'sql_literals': queries,
              'transaction': {'read_only': True, 'isolation': 'REPEATABLE READ',
                              'finalization': 'explicit rollback in finally, close in finally',
                              'connection_limit': 5, 'other_database_connections': 0},
              'budget': dict.fromkeys(['CREATE', 'ODOO_HTTP', 'BROWSER', 'BUSINESS_POST',
                                     'SQL_ORM_WRITE', 'ODOO_CLI', 'SUDO'], 0),
              'source_check_before_sql': True, 'sql_run': 'NOT_RUN',
              'schema_contract': 'catalog first; SELECT to_jsonb on base tables; optional fields explicit missing',
              'path_gate': True, 'fixed_files_match': True}
    save('preflight.json', result)
    print(json.dumps({'offline': 'PASS', 'fixed_files': len(records),
                      'seals': {k:v['status'] for k,v in seals.items()}}))


def allowed(path):
    return path.startswith(('scripts/s10_p0_10_', 'docs/s10-p0-10-', 'docs/evidence/s10-p0-10/'))


def redacted(row):
    result = {}
    for key, value in row.items():
        if key in FIELDS or key in YD_FIELDS:
            if isinstance(value, (dict, list)):
                result[key + '_sha256'] = sha(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())
            else:
                result[key] = value
        elif key in HASH_FIELDS:
            result[key + '_present'] = value is not None and value != ''
            result[key + '_sha256'] = sha(json.dumps(value, sort_keys=True, ensure_ascii=False).encode())
    return result


def storage(folder, name):
    base = folder / 'data/filestore' / name
    assert base.is_dir() and not base.is_symlink()
    files = {}
    for path in sorted(base.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            files[str(path.relative_to(base))] = sha(path.read_bytes())
    p0 = ''.join(k + ' ' + files[k] + '\n' for k in sorted(files))
    w = ''.join(k + '\t' + files[k] + '\n' for k in sorted(files))
    return {'count': len(files), 'p0_manifest_sha256': sha(p0.encode()),
            'w_manifest_sha256': sha(w.encode())}, files


def baseline(key):
    if key == 'P009':
        b = load('docs/evidence/s10-p0-09/business-before-after.json')
        return b['after_all_643_table_signatures'], 'canonical_text', b
    if key == 'R3':
        b = identities()[key]['managed']
        return b['tables'], 'canonical_text', b
    b = load('docs/evidence/s10-e2e-w4/verification.json')['source']['exact_signatures']
    if key == 'W5':
        b = load('docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json')['target']['stable_31_sha256']
    return b, 'id_with_empty_newline', None


def query(cur, statement, params=()):
    # Only fixed SELECT/SHOW and Identifier-composed base-table SELECTs reach here.
    cur.execute(statement, params)
    return cur.fetchall()


def schema_hash(cur, tables):
    columns = query(cur, "SELECT table_name,column_name,ordinal_position,data_type,udt_name,is_nullable,"
        "column_default FROM information_schema.columns WHERE table_schema='public' "
        "AND table_name=ANY(%s) ORDER BY table_name,ordinal_position", (tables,))
    constraints = query(cur, "SELECT c.relname,con.conname,pg_get_constraintdef(con.oid) "
        "FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' "
        "AND c.relname=ANY(%s) ORDER BY 1,2", (tables,))
    indexes = query(cur, "SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' "
        "AND tablename=ANY(%s) ORDER BY tablename,indexname", (tables,))
    data = json.dumps({'columns': columns, 'constraints': constraints, 'indexes': indexes},
        default=str, ensure_ascii=False, separators=(',', ':')).encode()
    return {'columns': len(columns), 'constraints': len(constraints),
            'indexes': len(indexes), 'sha256': sha(data)}


def w5_money_gate(objects):
    # Compare exact known finance projections with the fixed RO1-R1 evidence.
    old = load('docs/evidence/s10-e2e-w5-ro1-r1/read-only-sql.json')['target']
    mappings = {
        'account_move': ('moves', {'id':'id','type':'move_type','state':'state',
            'total':'amount_total','company':'company_id','journal':'journal_id'}),
        'account_payment': ('payments', {'id':'id','state':'state','amount':'amount',
            'company':'company_id','journal':'journal_id','move':'move_id',
            'payment_type':'payment_type','partner_type':'partner_type'}),
        'account_partial_reconcile': ('partials', {'id':'id','amount':'amount',
            'debit':'debit_move_id','credit':'credit_move_id','company':'company_id'}),
        'ydental_settlement_payment': ('s10_payments', {'id':'id','payment':'ydental_payment_id',
            'amount':'ydental_amount','channel':'ydental_channel','store':'ydental_store_id','patient':'ydental_patient_id'}),
    }
    from decimal import Decimal
    for table, (old_key, mapping) in mappings.items():
        actual = sorted(objects[table], key=lambda r: r['id'])
        expected = sorted(old[old_key], key=lambda r: r['id'])
        assert len(actual)==len(expected), ('w5_row_count',table)
        for a,b in zip(actual,expected):
            for alias,field in mapping.items():
                if alias in ('amount','total'):
                    assert Decimal(str(a[field]))==Decimal(str(b[alias])), ('w5_money',table)
                else:
                    assert a[field]==b[alias], ('w5_identity',table,field)
    invoice = next(r for r in objects['account_move'] if r['id']==1)
    assert Decimal(str(invoice['amount_residual']))==0 and invoice['payment_state']=='paid'
    assert len(objects['ydental_settlement_receipt'])==3
    assert not objects['ydental_settlement_refund'] and not objects['ydental_settlement_close']
    assert {r['id'] for r in objects['ydental_access_audit'] if r.get('ydental_event')=='settlement.pay'}=={327,330}
    return 'FIXED_RO1_R1_MONEY_PROJECTIONS_MATCH'


def capture(key, seal):
    name, oid, commit = SOURCES[key]
    files_gate(key, identities()[key])
    folder = ROOT / '.local' / name
    conf = configparser.ConfigParser(interpolation=None)
    assert conf.read(folder / 'odoo.conf')
    opts = conf['options']
    assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
    manifest, files = storage(folder, name)
    expected, algorithm, old = baseline(key)
    conn = None
    result = {'database': name, 'oid_expected': oid, 'fixed_commit': commit,
              'evidence_layer': 'READONLY_SOURCE', 'seal': seal}
    started = time.time()
    try:
        conn = psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
                               password=opts['db_password'], dbname=name, connect_timeout=5)
        conn.set_session(readonly=True, isolation_level='REPEATABLE READ', autocommit=False)
        with conn.cursor() as cur:
            ro = query(cur, 'SHOW transaction_read_only')[0][0]
            iso = query(cur, 'SHOW transaction_isolation')[0][0]
            assert ro == 'on' and iso == 'repeatable read'
            actual_name, actual_oid, cluster = query(cur,
                'SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),'
                '(SELECT system_identifier::text FROM pg_control_system())')[0]
            assert (actual_name, actual_oid, cluster) == (name, oid, CLUSTER), 'database_identity_drift'
            result.update({'oid': actual_oid, 'cluster': cluster, 'transaction_read_only': ro,
                           'transaction_isolation': iso, 'backend_pid': conn.get_backend_pid()})
            # Passive observation only; never acquire advisory or row business locks.
            others = query(cur, 'SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()')
            assert not others, 'source_has_other_connections'
            columns = query(cur, "SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                "JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' "
                "AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
            catalog = {}
            for table, field in columns:
                catalog.setdefault(table, []).append(field)
            assert set(expected).issubset(catalog), 'required_table_missing'
            if key == 'P009':
                assert set(expected) == set(catalog), 'p009_public_table_set_drift'
            signatures = {}
            observations = {}
            # Hash full rows privately. Publish only SHA and explicit field projections.
            for table in sorted(set(expected) | (set(TABLES) & set(catalog))):
                order = sql.SQL('to_jsonb(t)::text') if algorithm == 'canonical_text' or 'id' not in catalog[table] else sql.Identifier('id')
                rows = query(cur, sql.SQL('SELECT to_jsonb(t)::text FROM public.{} t ORDER BY {}').format(sql.Identifier(table), order))
                raw = [r[0] for r in rows]
                payload = ''.join(x + '\n' for x in raw)
                if algorithm == 'id_with_empty_newline' and not raw:
                    payload = '\n'
                signatures[table] = {'rows': len(raw), 'sha256': sha(payload.encode())}
                if table in TABLES:
                    parsed = [json.loads(x) for x in raw]
                    if table == 'ydental_access_session':
                        parsed = [r for r in parsed if key == 'P009' and r['id'] in (185,186)]
                    if table == 'ydental_access_audit':
                        parsed = [r for r in parsed if str(r.get('ydental_event','')).startswith(
                            ('settlement.', 'treatment.', 'clinical.', 'exam.', 'inventory.')) or
                            key == 'P009' and 2693 <= r['id'] <= 2702]
                    observations[table] = [redacted(r) for r in parsed]
            mismatches = {t: {'expected': expected[t], 'actual': signatures[t]} for t in expected if expected[t] != signatures[t]}
            result.update({'table_signatures': signatures, 'baseline_table_count': len(expected),
                           'baseline_algorithm': algorithm, 'baseline_mismatches': mismatches})
            if mismatches:
                result['status'] = 'UNAVAILABLE_OR_DRIFT'
                return result
            pointers = query(cur, 'SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
            for filename, checksum in pointers:
                assert filename in files
                assert hashlib.sha1((folder/'data/filestore'/name/filename).read_bytes()).hexdigest() == checksum
            result['filestore'] = manifest
            result['attachment_pointers'] = len(pointers)
            result['attachment_pointers_sha256'] = sha(json.dumps(pointers).encode())
            if key == 'P009':
                assert manifest['p0_manifest_sha256'] == old['after_filestore']['sha256'] and manifest['count'] == old['after_filestore']['count']
                assert len(pointers) == old['after_attachment_pointers']
                assert len(signatures) >= 643
            elif key == 'R3':
                assert manifest['p0_manifest_sha256'] == old['filestore']['sha256']
                assert len(pointers) == old['attachment_pointers']
            else:
                assert manifest['w_manifest_sha256'] == 'bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283'
                assert (manifest['count'],len(pointers)) == (152,164)
            # Catalog-based projection records missing fields rather than inventing column names.
            result['observed_columns'] = {t: catalog[t] for t in observations}
            result['objects'] = observations
            if key == 'W5':
                result['native_money_gate'] = w5_money_gate(observations)
            if key in ('P009','R3'):
                tables = list(old['after_265_managed_table_signatures']) if key=='P009' else list(old['tables'])
                result['schema'] = schema_hash(cur,tables)
                expected_schema = old['after_schema'] if key=='P009' else old['schema']
                assert result['schema'] == expected_schema, 'schema_drift'
            result['missing_optional_tables'] = sorted(set(TABLES)-set(catalog))
            # Existing clinical print bytes only. No rendering or business/API call.
            pdfs = []
            if 'ydental_print_job' in catalog and 'ydental_pdf' in catalog['ydental_print_job']:
                for ident, value, digest in query(cur, 'SELECT id,ydental_pdf,ydental_pdf_digest FROM ydental_print_job ORDER BY id'):
                    data = bytes(value) if value is not None else b''
                    if data and not data.startswith(b'%PDF-'):
                        data = base64.b64decode(data, validate=True)
                    pdfs.append({'job_id': ident, 'bytes': len(data), 'pdf_magic': data.startswith(b'%PDF-'),
                                 'sha256': sha(data), 'stored_digest': digest, 'digest_matches': sha(data)==digest})
            result['existing_clinical_pdf_bytes'] = pdfs
            result['status'] = 'READONLY_SOURCE_MATCH'
    except (AssertionError, psycopg2.Error, OSError, ValueError) as error:
        result['status'] = 'UNAVAILABLE_OR_DRIFT'
        # Never publish raw DB exceptions, parameters or DSNs.
        result['error_type'] = type(error).__name__
        result['sqlstate'] = getattr(error, 'pgcode', None)
    finally:
        if conn is not None:
            try:
                conn.rollback()
                result['rolled_back'] = True
            finally:
                conn.close()
                result['closed'] = bool(conn.closed)
        result['seconds'] = round(time.time()-started, 3)
    return result


def run_sql(checkpoint_path):
    assert not (OUT/'read-only-sql.json').exists(), 'single_window_already_recorded'
    p = load('docs/evidence/s10-p0-10/preflight.json')
    assert p['script_sha256'] == sha(Path(__file__).read_bytes())
    check = json.loads(Path(checkpoint_path).read_text())
    assert check['verbatim_equal'] is True and check['authorization'] == AUTH
    assert check['script_sha256'] == p['script_sha256']
    assert check['preflight_sha256'] == sha((OUT/'preflight.json').read_bytes())
    assert git('rev-parse','HEAD') == BASE and git('ls-remote','origin','refs/heads/'+BRANCH).split()[0] == BASE
    results = {}
    for key in SOURCES:
        seal = p['sources'][key]
        results[key] = capture(key, seal) if seal['status']=='STATIC_FILE_IDENTITY_MATCH' else seal
        # Persist after each source; never retry a failed/missing source.
        save('read-only-sql.json', {'authorization': AUTH, 'checkpoint_id': check['comment_id'],
             'script_sha256': p['script_sha256'], 'sources': results,
             'budget': p['budget'], 'source_attempts': len(results)})
        print(key, results[key]['status'], flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['offline', 'sql'])
    parser.add_argument('--checkpoint')
    args = parser.parse_args()
    if args.mode == 'offline':
        offline()
    else:
        assert args.checkpoint
        run_sql(args.checkpoint)
