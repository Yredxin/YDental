"""RO1: inspect immutable W5 evidence, then optionally open one read-only SQL window.

Never invokes Odoo or the old W5 execution/browser/final-audit entry points.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
import time

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_e2e_w5_snapshot as old

W5 = ROOT / 'docs/evidence/s10-e2e-w5/verification.json'
PREFLIGHT = ROOT / 'docs/evidence/s10-e2e-w5-ro1/preflight.json'
LIVE = ROOT / 'docs/evidence/s10-e2e-w5-ro1/read-only-sql.json'
EXPECTED = {
    'scripts/s10_e2e_w5_browser.py': 'a3db4471714888a142a47d0067572fe83d9ba92362e2384a26d4144d4509efbc',
    'scripts/s10_e2e_w5_cli_offline.py': '01af42a51d0014548423f7ba26918ccb0a80625d57a9efda51bc1585658149a0',
    'scripts/s10_e2e_w5_control.py': '032db39bfbf99d28ee7f4100bf33169e5e2952129eec233b500a433bb9f284f5',
    'scripts/s10_e2e_w5_offline.py': 'f74f1f1e57e66fa320c1ff1309b772b911f31d344b2f39a2b17a8175c5ecf49b',
    'scripts/s10_e2e_w5_preflight.py': 'a5cdf152c9a4d70843fa808b1f7f2f0624362216b561bbc59f42a4a7c8ed38da',
    'scripts/s10_e2e_w5_snapshot.py': '019d2ddf23a07cb6344bfdfc56b9129fa20aa69a18f17e9d1f1efc87f05d7de7',
    'docs/s10-e2e-w5-blocked-report.md': '9ad2b32f82ad128939c25c5d430369b87a1107d8e30c6a0312a6d3de66c5fa35',
    'docs/evidence/s10-e2e-w5/preflight.json': 'bb26dea5188ae9147aa11b85f45a530e6124487141f326c0b99238eed93479b4',
    'docs/evidence/s10-e2e-w5/verification.json': '5cd6896404b3b2789692a783269d55c6dde4c70c5824225bbeadd123feea4265',
}


def require(condition, label):
    if not condition:
        raise AssertionError(label)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_file(path):
    return json.loads(path.read_text())


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, default=str)
        stream.write('\n')


def money_check(m, baseline):
    """Independent complete-pair contract; a state string alone never passes."""
    invoice = m['invoices']
    require(len(invoice) == 1 and invoice[0]['id'] == 1, 'unique_invoice')
    require(invoice[0]['type'] == 'out_invoice' and invoice[0]['state'] == 'posted', 'posted_invoice')
    require(Decimal(invoice[0]['total']) == 740 and Decimal(invoice[0]['residual']) == 0, 'invoice_740_to_zero')
    require(invoice[0]['payment_state'] == 'paid', 'invoice_paid')
    require(m['sources'] == baseline['sources'], 'unchanged_sources')
    require(m['cash_configs'] == baseline['cash_configs'] == [{'store': 1, 'company': 1, 'journal': 8}], 'cash_config')
    require(len(m['native_moves']) == 3 and m['native_moves'][0] == baseline['native_moves'][0], 'unique_posted_moves')
    require(len(m['payments']) == len(m['partials']) == len(m['settlement_payments']) == len(m['payment_invoices']) == 2, 'unique_payment_pair')
    require(len(m['receipts']) == 3 and m['receipts'][0] == baseline['receipts'][0], 'receipt_count')
    require(m['invoice_lines'][:4] == baseline['invoice_lines'][:4], 'invoice_source_lines')
    require(m['invoice_lines'][4]['id'] == 5 and Decimal(m['invoice_lines'][4]['residual']) == 0, 'invoice_ar_line')
    for index, amount in enumerate((500, 240), 1):
        payment = m['payments'][index-1]
        move = m['native_moves'][index]
        part = m['partials'][index-1]
        internal = m['settlement_payments'][index-1]
        relation = m['payment_invoices'][index-1]
        require(payment['id'] == index and payment['state'] == 'reconciled', f'payment_state_{index}')
        require(payment['payment_type'] == 'inbound' and payment['partner_type'] == 'customer', f'payment_direction_{index}')
        require(payment['company'] == 1 and payment['journal'] == 8 and payment['move'] == index+1, f'payment_journal_move_{index}')
        require(payment['move_state'] == move['state'] == 'posted' and move['id'] == index+1 and move['type'] == 'entry', f'posted_move_{index}')
        require(Decimal(payment['amount']) == Decimal(amount), f'payment_amount_{index}')
        require(part['id'] == index and part['debit'] == 5 and part['company'] == 1 and Decimal(part['amount']) == amount, f'partial_invoice_ar_{index}')
        credit = [line for line in m['payment_lines'] if line['id'] == part['credit'] and line['move'] == move['id']]
        require(len(credit) == 1 and Decimal(credit[0]['credit']) == amount, f'partial_payment_ar_{index}')
        lines = [line for line in m['payment_lines'] if line['move'] == move['id']]
        require(len(lines) == 2 and sum((Decimal(line['balance']) for line in lines), Decimal()) == 0, f'balanced_move_{index}')
        require(internal['id'] == index and internal['payment'] == index and Decimal(internal['amount']) == amount, f's10_native_link_{index}')
        require(internal['channel'] == 'cash' and internal['store'] == internal['patient'] == 1, f's10_scope_{index}')
        require(relation == {'settlement_payment': index, 'invoice': 1}, f's10_invoice_link_{index}')
        receipt = m['receipts'][index]
        require(receipt['id'] == index+1 and receipt['operation'] == 'pay', f'receipt_{index}')
        result = receipt['result']
        require(result['native_payment_id'] == result['payment_id'] == index and Decimal(str(result['amount'])) == amount, f'receipt_native_link_{index}')
        require(result['allocations'] == [{'invoice_id': 1, 'partial_id': index, 'amount': float(amount)}], f'receipt_allocation_{index}')
    pay_audits = [a for a in m['audits'] if a['event'] == 'settlement.pay']
    require(len(pay_audits) == 2 and all(a['result'] == 'accepted' and a['user'] == 5 and a['store'] == 1 for a in pay_audits), 's01_two_accepted')
    require(not [a for a in baseline['audits'] if a['event'] == 'settlement.pay'], 'prepayment_pay_audit_zero')
    return {'invoice_id': 1, 'amounts': [500, 240], 'payment_ids': [1, 2],
            'move_ids': [2, 3], 'partial_ids': [1, 2], 'receipt_ids': [2, 3],
            'audit_ids': [a['id'] for a in pay_audits]}


def simulations(before, after):
    require(money_check(after, before), 'positive_reconciled')
    cases = {
        'unposted_move': lambda m: m['payments'][0].update(move_state='draft'),
        'wrong_journal': lambda m: m['payments'][0].update(journal=1),
        'wrong_partial_amount': lambda m: m['partials'][0].update(amount='499'),
        'wrong_partial_ar': lambda m: m['partials'][1].update(debit=4),
        'wrong_payment_line': lambda m: m['partials'][1].update(credit=7),
        'duplicate_payment': lambda m: m['payments'].append(deepcopy(m['payments'][1])),
        'wrong_amount': lambda m: m['payments'][1].update(amount='241'),
        'wrong_invoice': lambda m: m['payment_invoices'][1].update(invoice=2),
        'unreconciled_state': lambda m: m['payments'][0].update(state='draft'),
        'unbalanced_move': lambda m: m['payment_lines'][-1].update(balance='-239'),
        'missing_receipt': lambda m: m['receipts'].pop(),
        'missing_s01_audit': lambda m: m['audits'].pop(next(i for i, a in enumerate(m['audits']) if a['event'] == 'settlement.pay')),
    }
    for name, mutate in cases.items():
        bad = deepcopy(after)
        mutate(bad)
        try:
            money_check(bad, before)
        except AssertionError:
            continue
        raise AssertionError(f'negative_case_accepted_{name}')
    return {'status': 'SIMULATED_PASS', 'reconciled_positive': 1, 'negative_cases': list(cases)}


def offline():
    v = json_file(W5)
    require(v['target']['oid'] == 2100310 and v['source']['oid'] == 2100301, 'w5_report_identity')
    for name, expected in EXPECTED.items():
        require(sha(ROOT / name) == expected, f'fixed_file_{name}')
    require(v['hashes']['scripts_sha256'] == {k: x for k, x in EXPECTED.items() if k.startswith('scripts/')}, 'fixed_script_index')
    private = old.RUN
    for name, expected in v['hashes']['private_files_sha256'].items():
        require(sha(private / name) == expected, f'private_{name}')
    require(sha(private / 'database.json') == v['target']['marker_sha256'], 'target_marker')
    require(sha(private / 'odoo.conf') == v['target']['config_sha256'], 'target_config')
    require(sha(old.SOURCE_RUN / 'database.json') == v['source']['marker_sha256'], 'source_marker')
    require(sha(old.SOURCE_RUN / 'odoo.conf') == v['source']['config_sha256'], 'source_config')
    before = json_file(private / 'before-web.json')
    one = json_file(private / 'pay-1-observed.json')
    two = json_file(private / 'pay-2-observed.json')
    stop = json_file(private / 'post-stop-readonly.json')
    require(before['oid'] == stop['target_oid'] == 2100310 and stop['source_oid'] == 2100301, 'private_oid')
    require(Decimal(one['money']['invoices'][0]['residual']) == 240, 'first_residual')
    require(one['money']['payments'][0]['state'] == 'paid', 'first_state')
    require(two['money']['payments'][0]['state'] == two['money']['payments'][1]['state'] == 'reconciled', 'second_state')
    require(two['response']['http_status'] == one['response']['http_status'] == 303, 'historical_303')
    for i, amount in ((1, 500), (2, 240)):
        intent, sent, response, observed = [json_file(private / f'pay-{i}-{suffix}.json') for suffix in ('intent', 'sent', 'response', 'observed')]
        require(intent['one_shot'] and intent['amount'] == observed['amount'] == amount and intent['invoice'] == 1, f'intent_{i}')
        require(sent['method'] == 'POST' and sent['path'] == '/ydental/settlement/action', f'sent_{i}')
        require(response['http_status'] == 303 and observed['response']['http_status'] == 303, f'response_{i}')
        require(datetime.fromisoformat(intent['utc']) < datetime.fromisoformat(observed['utc']), f'chronology_{i}')
    require(datetime.fromisoformat(one['utc']) < datetime.fromisoformat(json_file(private / 'pay-2-intent.json')['utc']), 'payment_order')
    require(stop['target_stable_tables_unchanged'] and stop['source_business_38_and_money_unchanged'], 'historical_stability')
    require(v['failure']['final_audit'] == 'NOT_RUN' and v['resources']['browser_result']['exit_code'] == 1, 'historical_block')
    require(not (private / 'browser-complete.json').exists() and not (private / 'final-audit.json').exists(), 'no_fabricated_completion')
    simulation = simulations(before['money'], two['money'])
    return {'status': 'PREFLIGHT_PASS_SQL0', 'authorization': 6187934504,
            'fixed_head': '287881a824e9a18dd637522c570f74df139078f9',
            'fixed_file_sha256': EXPECTED, 'private_file_sha256': v['hashes']['private_files_sha256'],
            'source': {'database': old.SOURCE, 'oid': 2100301, 'marker_sha256': v['source']['marker_sha256'], 'config_sha256': v['source']['config_sha256']},
            'target': {'database': old.NAME, 'oid': 2100310, 'marker_sha256': v['target']['marker_sha256'], 'config_sha256': v['target']['config_sha256']},
            'historical': {'first_observed_utc': one['utc'], 'second_observed_utc': two['utc'],
                           'web_post_amounts': [500, 240], 'response_codes': [303, 303],
                           'browser_exit': 1, 'final_audit': 'NOT_RUN',
                           'post_stop_sha256': v['hashes']['post_stop_readonly_sha256']},
            'simulation': simulation, 'sql_budget': {'windows': 1, 'seconds_max': 300,
                'connections_per_database_max': 1, 'read_only': True, 'odoo_processes': 0,
                'create': 0, 'writes': 0}}


def connection(database):
    conn = psycopg2.connect(dbname=database, options='-c statement_timeout=30000', **old.endpoint())
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
    with conn.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        require(cursor.fetchone()[0] == 'on', 'transaction_not_readonly')
    return conn


def inspect_database(database, expected_oid):
    conn = connection(database)
    try:
        with conn.cursor() as cursor:
            cursor.execute('SELECT oid FROM pg_database WHERE datname=current_database()')
            oid = cursor.fetchone()[0]
            require(oid == expected_oid, f'{database}_oid')
            cursor.execute('SELECT system_identifier::text FROM pg_control_system()')
            cluster = cursor.fetchone()[0]
            require(cluster == old.CLUSTER, f'{database}_cluster')
            cursor.execute("SELECT name,state,latest_version,write_date FROM ir_module_module ORDER BY name")
            module_meta = {name: {'state': state, 'version': version, 'write_date': stamp.isoformat() if stamp else None}
                           for name, state, version, stamp in cursor.fetchall()}
            cursor.execute('SELECT to_jsonb(t)::text FROM ydental_access_audit t ORDER BY id')
            audit_rows = [r[0] for r in cursor.fetchall()]
            cursor.execute('SELECT id,ydental_cashier_id,ydental_store_id,ydental_patient_id,ydental_channel,ydental_amount,ydental_business_date,ydental_actual_utc FROM ydental_settlement_payment ORDER BY id')
            cashier = [list(map(str, row)) for row in cursor.fetchall()]
            cursor.execute('SELECT id,ydental_operation,ydental_result FROM ydental_settlement_receipt ORDER BY id')
            receipts = [{'id': i, 'operation': op, 'result': result} for i, op, result in cursor.fetchall()]
            cursor.execute("SELECT id,ydental_event,ydental_result,ydental_user_id,ydental_store_id FROM ydental_access_audit WHERE ydental_event='settlement.pay' ORDER BY id")
            pay_audits = [list(row) for row in cursor.fetchall()]
            cursor.execute("SELECT id,state FROM stock_move ORDER BY id")
            stock = [list(row) for row in cursor.fetchall()]
            cursor.execute("SELECT id,ydental_amount,ydental_price_snapshot_id FROM ydental_treatment_fee ORDER BY id")
            fees = [list(map(str, row)) for row in cursor.fetchall()]
        exact = old.exact_signature(conn)
        money = json.loads(old.canonical(old.money(conn)))
        views = old.views(conn)
        files = old.filestore(database, conn)
        modules = sorted(name for name, row in module_meta.items() if row['state'] == 'installed')
        module_hash = hashlib.sha256(old.canonical(module_meta).encode()).hexdigest()
        return {'oid': oid, 'cluster': cluster, 'exact': exact, 'money': money,
                'views': views, 'module_count': len(modules), 'module_meta_sha256': module_hash,
                'filestore': {k: v for k, v in files.items() if k != 'files'},
                'audit_rows': audit_rows, 'cashier': cashier, 'receipts': receipts,
                'pay_audits': pay_audits, 'stock': stock, 'fees': fees}
    finally:
        conn.close()


def live():
    start = time.monotonic()
    pre = json_file(PREFLIGHT)
    require(pre['status'] == 'PREFLIGHT_PASS_SQL0' and pre['authorization'] == 6187934504, 'preflight_required')
    require(sha(Path(__file__)) == pre['ro1_script_sha256'], 'script_drift_after_checkpoint')
    v = json_file(W5)
    before = json_file(old.RUN / 'before-web.json')
    historical = json_file(old.RUN / 'pay-2-observed.json')
    source = inspect_database(old.SOURCE, 2100301)
    require(time.monotonic() - start < 300, 'sql_window_timeout_source')
    target = inspect_database(old.NAME, 2100310)
    require(time.monotonic() - start < 300, 'sql_window_timeout_target')
    require(source['exact'] == json_file(ROOT / 'docs/evidence/s10-e2e-w5/preflight.json')['source']['exact_signatures'], 'w4_38_table_drift')
    require(source['module_count'] == target['module_count'] == 92, 'module_count_drift')
    require(source['module_meta_sha256'] == target['module_meta_sha256'] == before['module_meta_sha256'], 'module_meta_drift')
    require(source['views'] == target['views'] == before['views'], 'installed_view_drift')
    require(source['filestore'] == target['filestore'], 'filestore_drift')
    require(source['filestore']['manifest_sha256'] == before['filestore_manifest_sha256'], 'filestore_baseline_drift')
    require(source['money'] == before['money'], 'w4_finance_drift')
    require(source['fees'] == [['1', '600.00', '1'], ['2', '80.00', '2'], ['3', '40.00', '3'], ['4', '20.00', '4']], 'source_fees')
    require(target['fees'] == source['fees'] and target['stock'] == source['stock'], 'fee_stock_drift')
    stable = {table: target['exact'][table] for table in old.STABLE_AFTER_PAYMENT}
    require(stable == {table: before['exact'][table] for table in old.STABLE_AFTER_PAYMENT}, 'target_31_table_drift')
    require(target['audit_rows'][:len(source['audit_rows'])] == source['audit_rows'], 'w4_audit_history_drift')
    check = money_check(target['money'], before['money'])
    require(old.canonical(target['money']) == old.canonical(historical['money']), 'historical_final_money_drift')
    require(target['cashier'] == [['1', '5', '1', '1', 'cash', '500.00', '2026-10-15', '2026-10-15 07:52:02.559463'],
                                  ['2', '5', '1', '1', 'cash', '240.00', '2026-10-15', '2026-10-15 07:52:03.952418']], 'cashier_scope_date')
    require(len(target['audit_rows']) >= len(source['audit_rows']) + 2, 'new_audits_missing')
    require(len(target['pay_audits']) == 2 and [a[0] for a in target['pay_audits']] == check['audit_ids'], 'audit_ids')
    require(all(a[1:] == ['settlement.pay', 'accepted', 5, 1] for a in target['pay_audits']), 'audit_actor_scope')
    require(len(target['receipts']) == 3, 'receipt_count_live')
    duration = time.monotonic() - start
    require(duration <= 300, 'sql_window_exceeded')
    return {'status': 'NEW_READONLY_SQL_PASS', 'window_seconds': round(duration, 3),
            'connections': {'source': 1, 'target': 1}, 'transaction_read_only': True,
            'source': {'database': old.SOURCE, 'oid': source['oid'], 'cluster': source['cluster'],
                'business_38_sha256': source['exact'], 'module_count': source['module_count'],
                'module_meta_sha256': source['module_meta_sha256'], 'views': source['views'],
                'filestore': source['filestore'], 'invoice': source['money']['invoices'],
                'payment_count': len(source['money']['payments']), 'partial_count': len(source['money']['partials']),
                'audit_row_count': len(source['audit_rows'])},
            'target': {'database': old.NAME, 'oid': target['oid'], 'cluster': target['cluster'],
                'stable_31_sha256': stable, 'module_count': target['module_count'],
                'module_meta_sha256': target['module_meta_sha256'], 'views': target['views'],
                'filestore': target['filestore'], 'invoice': target['money']['invoices'],
                'payments': target['money']['payments'], 'moves': target['money']['native_moves'],
                'partials': target['money']['partials'], 'invoice_ar_line': target['money']['invoice_lines'][4],
                'payment_lines': target['money']['payment_lines'],
                's10_payments': target['money']['settlement_payments'],
                'payment_invoice_rel': target['money']['payment_invoices'],
                'cashier': target['cashier'], 'receipts': target['receipts'],
                'pay_audits': target['pay_audits'], 'audit_row_count': len(target['audit_rows']),
                'stock': target['stock'], 'fees': target['fees'],
                'refund_count': target['exact']['ydental_settlement_refund']['rows'],
                'close_count': target['exact']['ydental_settlement_close']['rows']},
            'checks': check, 'historical_private_sha256': v['hashes']['private_files_sha256'],
            'not_run': ['Odoo HTTP/CLI/shell', 'Firefox/Playwright', 'CREATE', 'payment POST',
                'module install/upgrade', 'W5 browser-complete', 'W5 final_audit']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preflight', 'live'))
    args = parser.parse_args()
    if args.mode == 'preflight':
        data = offline()
        data['ro1_script_sha256'] = sha(Path(__file__))
        write_new(PREFLIGHT, data)
        print('PREFLIGHT_PASS_SQL0', data['ro1_script_sha256'])
    else:
        write_new(LIVE, live())
        print('NEW_READONLY_SQL_PASS', LIVE)
