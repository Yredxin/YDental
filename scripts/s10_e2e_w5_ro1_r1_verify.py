"""RO1-R1: inspect the complete SQL contract before one read-only W4/W5 window.

Never invokes Odoo or an old W5/RO1 execution, browser or final-audit entry point.
"""

import argparse
import ast
from copy import deepcopy
from datetime import datetime
from decimal import Decimal
import hashlib
import inspect
import json
from pathlib import Path
import re
import signal
import sys
import time
import textwrap

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_e2e_w5_snapshot as old

W5 = ROOT / 'docs/evidence/s10-e2e-w5/verification.json'
RO1 = ROOT / 'docs/evidence/s10-e2e-w5-ro1'
R1 = ROOT / 'docs/evidence/s10-e2e-w5-ro1-r1'
PREFLIGHT = R1 / 'preflight.json'
CHECKPOINT = R1 / 'checkpoint.json'
LIVE = R1 / 'read-only-sql.json'
BASE = '877b94653e89234ba06c9086d0cb472458188ba1'
AUTH = 6188802614
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
RO1_EXPECTED = {
    'scripts/s10_e2e_w5_ro1_verify.py': 'e1326cf1e24b5ff712281ebe398ace447e58b8873dad88203a331201b972062d',
    'docs/evidence/s10-e2e-w5-ro1/preflight.json': '6142e41d421025e83a40cb19de8d0da2c8f9f841edd48926199d00a8b010ff45',
    'docs/evidence/s10-e2e-w5-ro1/blocked.json': 'd4213acca5e74bd87e90bd7379175b5c1dabf5be4c174d6e8c0ad5eba3a750b6',
    'docs/s10-e2e-w5-ro1-blocked-report.md': 'd35f3fc2e360e9bcd496d53fab8d369791ac110e58f6b97e739f11efc6f4f433',
}

# All projected business columns in inspect_database(), plus the actual SQL
# executed by W5's fixed exact_signature(), money(), views() and filestore().
# Each of the 38 exact tables also needs its ORM primary key for ORDER BY id.
REQUIRED_COLUMNS = {table: {'id'} for table in old.EXACT_TABLES}
for table, columns in {
    'ir_module_module': 'name state latest_version write_date',
    'ir_ui_view': 'key arch_db',
    'ir_attachment': 'id store_fname checksum',
    'ydental_access_audit': 'id ydental_event ydental_result ydental_user_id ydental_store_id',
    'ydental_settlement_payment': 'id ydental_payment_id ydental_amount ydental_channel ydental_store_id ydental_patient_id ydental_cashier_id ydental_business_date ydental_actual_at',
    'ydental_settlement_payment_invoice_rel': 'settlement_payment_id invoice_id',
    'ydental_settlement_receipt': 'id ydental_store_id ydental_actor_id ydental_operation ydental_result',
    'ydental_settlement_config': 'id ydental_store_id company_id ydental_cash_journal_id',
    'ydental_settlement_source': 'id ydental_fee_id ydental_invoice_id ydental_line_id ydental_original_amount',
    'ydental_treatment_fee': 'id ydental_amount ydental_price_snapshot_id',
    'stock_move': 'id state quantity',
    'ydental_treatment_event': 'id state',
    'ydental_exam_result': 'id state',
    'account_move': 'id move_type state amount_total amount_residual payment_state company_id journal_id',
    'account_move_line': 'id move_id account_id debit credit amount_residual balance',
    'account_payment': 'id state payment_type partner_type amount company_id journal_id move_id',
    'account_partial_reconcile': 'id amount debit_move_id credit_move_id company_id',
}.items():
    REQUIRED_COLUMNS.setdefault(table, set()).update(columns.split())


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


def sql_plan():
    """List the exact SELECT/SHOW templates reachable from the new live path."""
    functions = (connection, validate_schema, inspect_database,
                 old.full_rows, old.exact_signature, old.money, old.views, old.filestore)
    plan = []
    for function in functions:
        tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == 'execute'):
                continue
            first = node.args[0]
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                query = first.value
            elif (isinstance(first, ast.Call) and isinstance(first.func, ast.Attribute)
                  and first.func.attr == 'format' and isinstance(first.func.value, ast.Call)
                  and isinstance(first.func.value.func, ast.Attribute)
                  and first.func.value.func.attr == 'SQL'):
                query = ast.literal_eval(first.func.value.args[0])
            else:
                raise AssertionError(f'unlisted_SQL_{function.__name__}_{node.lineno}')
            normalized = ' '.join(query.split())
            require(normalized.upper().startswith(('SELECT ', 'SHOW ')), f'nonread_sql_{function.__name__}')
            require(not re.search(r'\b(FOR UPDATE|INSERT|DELETE|UPDATE|ALTER|DROP|CREATE|TRUNCATE|SET)\b', normalized, re.I), 'nonread_sql_token')
            plan.append({'function': function.__name__, 'sql': normalized,
                         'sha256': hashlib.sha256(query.encode()).hexdigest()})
    require(any('ydental_actual_at FROM ydental_settlement_payment' in row['sql'] for row in plan), 'actual_at_projection_missing')
    require(not any('ydental_actual_utc' in row['sql'] for row in plan), 'old_error_branch_reachable')
    require(any('to_jsonb(t)::text' in row['sql'] for row in plan), 'exact_signature_query_missing')
    return plan


def model_proofs():
    """Bind every named table/column to source declarations or ORM keys."""
    core = ROOT.parent
    paths = (list(ROOT.glob('ydental_*/models/*.py'))
             + list((core / 'addons/account/models').glob('*.py'))
             + list((core / 'addons/stock/models').glob('*.py'))
             + list((core / 'odoo/addons/base/models').glob('*.py')))
    sources = {str(path): path.read_text() for path in paths}
    output = {}
    for table, columns in sorted(REQUIRED_COLUMNS.items()):
        if table == 'ydental_settlement_payment_invoice_rel':
            path = ROOT / 'ydental_settlement/models/ydental_settlement_payment.py'
            body = path.read_text()
            require("relation='ydental_settlement_payment_invoice_rel'" in body
                    and "column1='settlement_payment_id'" in body
                    and "column2='invoice_id'" in body, 'relation_source')
            output[table] = {'model': 'Many2many relation', 'source': str(path.relative_to(ROOT)),
                             'columns': {name: 'Many2many relation declaration' for name in sorted(columns)}}
            continue
        model = table.replace('_', '.')
        candidates = [path for path, body in sources.items()
                      if re.search(r"^\s*_name\s*=\s*['\"]" + re.escape(model) + r"['\"]", body, re.M)]
        require(bool(candidates), f'model_source_missing_{table}')
        model_path = min(candidates, key=len)
        parent_dir = str(Path(model_path).parent)
        column_proofs = {}
        for column in sorted(columns):
            if column in ('id', 'write_date'):
                column_proofs[column] = 'Odoo ORM implicit model field'
                continue
            declaration = re.compile(r'^\s*' + re.escape(column) + r'\s*=\s*fields\.', re.M)
            matches = [path for path, body in sources.items()
                       if (path == model_path or str(Path(path).parent) == parent_dir)
                       and declaration.search(body)]
            require(bool(matches), f'model_field_missing_{table}.{column}')
            proof = model_path if declaration.search(sources[model_path]) else min(matches, key=len)
            column_proofs[column] = str(Path(proof).relative_to(ROOT if proof.startswith(str(ROOT)) else core))
        output[table] = {'model': model, 'source': str(Path(model_path).relative_to(ROOT if model_path.startswith(str(ROOT)) else core)),
                         'columns': column_proofs}
    return output


def validate_schema(cursor):
    """First business-independent SELECT in the same read-only transaction."""
    cursor.execute("SELECT c.relname,a.attname FROM pg_catalog.pg_class c "
                   "JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace "
                   "JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid "
                   "WHERE n.nspname='public' AND c.relkind IN ('r','p') "
                   "AND a.attnum>0 AND NOT a.attisdropped AND c.relname=ANY(%s) "
                   "ORDER BY c.relname,a.attname", (sorted(REQUIRED_COLUMNS),))
    actual = {}
    for table, column in cursor.fetchall():
        actual.setdefault(table, set()).add(column)
    missing = {table: sorted(columns - actual.get(table, set()))
               for table, columns in REQUIRED_COLUMNS.items()
               if columns - actual.get(table, set())}
    require(not missing, f'actual_schema_mismatch_{missing}')
    return {'table_count': len(actual), 'required_table_count': len(REQUIRED_COLUMNS),
            'checked_column_count': sum(map(len, REQUIRED_COLUMNS.values())),
            'schema_projection_sha256': hashlib.sha256(json.dumps(
                {table: sorted(actual[table] & REQUIRED_COLUMNS[table]) for table in sorted(REQUIRED_COLUMNS)},
                sort_keys=True).encode()).hexdigest()}


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
    require({k: v for k, v in m['invoice_lines'][4].items() if k != 'residual'} ==
            {k: v for k, v in baseline['invoice_lines'][4].items() if k != 'residual'}, 'invoice_ar_original')
    for index, amount in enumerate((500, 240), 1):
        payment = m['payments'][index-1]
        move = m['native_moves'][index]
        part = m['partials'][index-1]
        internal = m['settlement_payments'][index-1]
        relation = m['payment_invoices'][index-1]
        require(payment['id'] == index and payment['state'] == 'reconciled', f'payment_state_{index}')
        require(payment['payment_type'] == 'inbound' and payment['partner_type'] == 'customer', f'payment_direction_{index}')
        require(payment['company'] == 1 and payment['journal'] == 8 and payment['move'] == index+1, f'payment_journal_move_{index}')
        require(payment['move_state'] == move['state'] == 'posted' and move['id'] == index+1
                and move['type'] == 'entry' and move['company'] == 1
                and move['journal'] == 8, f'posted_move_{index}')
        require(Decimal(payment['amount']) == Decimal(amount), f'payment_amount_{index}')
        require(part['id'] == index and part['debit'] == 5 and part['company'] == 1 and Decimal(part['amount']) == amount, f'partial_invoice_ar_{index}')
        credit = [line for line in m['payment_lines'] if line['id'] == part['credit'] and line['move'] == move['id']]
        require(len(credit) == 1 and Decimal(credit[0]['credit']) == amount
                and credit[0]['account'] == m['invoice_lines'][4]['account'], f'partial_payment_ar_{index}')
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
        require(result['residuals'] == {'1': float(240 if index == 1 else 0)}, f'receipt_residual_{index}')
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
        'wrong_move_company': lambda m: m['native_moves'][1].update(company=2),
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
        'wrong_account': lambda m: m['payment_lines'][-1].update(account=99),
        'wrong_business_date_receipt': lambda m: m['receipts'][-1]['result'].update(residuals={'1': 5}),
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


def gate_simulations():
    class CatalogCursor:
        def __init__(self, rows):
            self.rows = rows
        def execute(self, query, values):
            require(query.startswith('SELECT ') and set(values[0]) == set(REQUIRED_COLUMNS), 'catalog_query_contract')
        def fetchall(self):
            return self.rows

    rows = [(table, column) for table, columns in REQUIRED_COLUMNS.items() for column in columns]
    require(validate_schema(CatalogCursor(rows))['required_table_count'] == len(REQUIRED_COLUMNS), 'schema_positive')
    blocked = []
    for label, altered in (
        ('missing_column', [row for row in rows if row != ('ydental_settlement_payment', 'ydental_actual_at')]),
        ('missing_table', [row for row in rows if row[0] != 'account_partial_reconcile']),
    ):
        try:
            validate_schema(CatalogCursor(altered))
        except AssertionError:
            blocked.append(label)
        else:
            raise AssertionError(f'gate_did_not_block_{label}')
    calls = []
    def broken_source(database, oid):
        calls.append(database)
        raise RuntimeError('simulated read-only SQL interruption')
    try:
        ordered_read(broken_source)
    except RuntimeError:
        require(calls == [old.SOURCE], 'target_read_after_source_failure')
        blocked.append('mid_sql_source_error')
    else:
        raise AssertionError('mid_sql_error_not_propagated')
    calls.clear()
    def broken_target(database, oid):
        calls.append(database)
        if database == old.NAME:
            raise RuntimeError('simulated target SQL interruption')
        return {'oid': oid}
    try:
        ordered_read(broken_target)
    except RuntimeError:
        require(calls == [old.SOURCE, old.NAME], 'unexpected_target_retry')
        blocked.append('mid_sql_target_error')
    else:
        raise AssertionError('target_sql_error_not_propagated')
    try:
        require(sha(old.RUN / 'pay-2-observed.json') == '0' * 64, 'raw_hash_mismatch')
    except AssertionError:
        blocked.append('raw_evidence_hash_mismatch')
    else:
        raise AssertionError('raw_hash_mismatch_not_blocked')
    return {'status': 'SIMULATED_PASS', 'catalog_positive': 1, 'fail_closed': blocked}


def ordered_read(reader):
    source = reader(old.SOURCE, 2100301)
    target = reader(old.NAME, 2100310)
    return source, target


def offline():
    v = json_file(W5)
    require(v['target']['oid'] == 2100310 and v['source']['oid'] == 2100301, 'w5_report_identity')
    for name, expected in {**EXPECTED, **RO1_EXPECTED}.items():
        require(sha(ROOT / name) == expected, f'fixed_file_{name}')
    require(json_file(RO1 / 'blocked.json')['status'] == 'BLOCKED_READONLY_SQL_QUERY_CONTRACT', 'ro1_blocked_history')
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
    gate = gate_simulations()
    full_flow = full_flow_simulations(before, two)
    query_inventory = sql_plan()
    proofs = model_proofs()
    return {'status': 'PREFLIGHT_PASS_SQL0', 'authorization': AUTH,
            'fixed_head': BASE, 'fixed_file_sha256': {**EXPECTED, **RO1_EXPECTED},
            'private_file_sha256': v['hashes']['private_files_sha256'],
            'source': {'database': old.SOURCE, 'oid': 2100301, 'marker_sha256': v['source']['marker_sha256'], 'config_sha256': v['source']['config_sha256']},
            'target': {'database': old.NAME, 'oid': 2100310, 'marker_sha256': v['target']['marker_sha256'], 'config_sha256': v['target']['config_sha256']},
            'historical': {'first_observed_utc': one['utc'], 'second_observed_utc': two['utc'],
                           'web_post_amounts': [500, 240], 'response_codes': [303, 303],
                           'browser_exit': 1, 'final_audit': 'NOT_RUN',
                           'post_stop_sha256': v['hashes']['post_stop_readonly_sha256']},
            'simulation': simulation, 'gate_simulation': gate,
            'full_flow_simulation': full_flow,
            'query_inventory': query_inventory, 'required_columns': {table: sorted(columns) for table, columns in sorted(REQUIRED_COLUMNS.items())},
            'source_model_proofs': proofs,
            'sql_budget': {'windows': 1, 'seconds_max': 300,
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
            schema = validate_schema(cursor)
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
            cursor.execute('SELECT id,ydental_cashier_id,ydental_store_id,ydental_patient_id,ydental_channel,ydental_amount,ydental_business_date,ydental_actual_at FROM ydental_settlement_payment ORDER BY id')
            cashier = [list(map(str, row)) for row in cursor.fetchall()]
            cursor.execute('SELECT id,ydental_store_id,ydental_actor_id,ydental_operation,ydental_result FROM ydental_settlement_receipt ORDER BY id')
            receipts = [{'id': i, 'store': store, 'actor': actor, 'operation': op, 'result': result}
                        for i, store, actor, op, result in cursor.fetchall()]
            cursor.execute("SELECT id,ydental_event,ydental_result,ydental_user_id,ydental_store_id FROM ydental_access_audit WHERE ydental_event='settlement.pay' ORDER BY id")
            pay_audits = [list(row) for row in cursor.fetchall()]
            cursor.execute("SELECT id,state,quantity FROM stock_move ORDER BY id")
            stock = [list(map(str, row)) for row in cursor.fetchall()]
            cursor.execute("SELECT id,ydental_amount,ydental_price_snapshot_id FROM ydental_treatment_fee ORDER BY id")
            fees = [list(map(str, row)) for row in cursor.fetchall()]
            cursor.execute("SELECT id,state FROM ydental_treatment_event ORDER BY id")
            treatment = [list(row) for row in cursor.fetchall()]
            cursor.execute("SELECT id,state FROM ydental_exam_result ORDER BY id")
            exam = [list(row) for row in cursor.fetchall()]
        exact = old.exact_signature(conn)
        money = json.loads(old.canonical(old.money(conn)))
        views = old.views(conn)
        files = old.filestore(database, conn)
        modules = sorted(name for name, row in module_meta.items() if row['state'] == 'installed')
        module_hash = hashlib.sha256(old.canonical(module_meta).encode()).hexdigest()
        return {'oid': oid, 'cluster': cluster, 'schema': schema, 'exact': exact, 'money': money,
                'views': views, 'module_count': len(modules), 'module_meta_sha256': module_hash,
                'filestore': {k: v for k, v in files.items() if k != 'files'},
                'audit_rows': audit_rows, 'cashier': cashier, 'receipts': receipts,
                'pay_audits': pay_audits, 'stock': stock, 'fees': fees,
                'treatment': treatment, 'exam': exam}
    finally:
        conn.close()


def assess_pair(source, target, before, historical):
    """The same complete source/target assertions used by live and offline."""
    require(source['oid'] == 2100301 and target['oid'] == 2100310, 'source_target_oid')
    require(source['cluster'] == target['cluster'] == old.CLUSTER, 'source_target_cluster')
    require(source['exact'] == json_file(ROOT / 'docs/evidence/s10-e2e-w5/preflight.json')['source']['exact_signatures'], 'w4_38_table_drift')
    require(source['module_count'] == target['module_count'] == 92, 'module_count_drift')
    require(source['module_meta_sha256'] == target['module_meta_sha256'] == before['module_meta_sha256'], 'module_meta_drift')
    require(source['views'] == target['views'] == before['views'], 'installed_view_drift')
    require(source['filestore'] == target['filestore'], 'filestore_drift')
    require(source['filestore']['manifest_sha256'] == before['filestore_manifest_sha256'], 'filestore_baseline_drift')
    require(source['money'] == before['money'], 'w4_finance_drift')
    require(len(source['money']['invoices']) == 1
            and source['money']['invoices'][0]['id'] == 1
            and source['money']['invoices'][0]['state'] == 'posted'
            and Decimal(source['money']['invoices'][0]['total']) == 740
            and Decimal(source['money']['invoices'][0]['residual']) == 740,
            'w4_posted_740_unpaid')
    require(len(before['money']['invoices']) == 1 and not before['money']['payments']
            and not before['money']['partials'] and not before['money']['settlement_payments'], 'w4_unpaid_invoice_baseline')
    require(len(source['money']['receipts']) == 1
            and source['money']['receipts'][0]['operation'] == 'bill', 'w4_bill_receipt_only')
    require(source['fees'] == [['1', '600.00', '1'], ['2', '80.00', '2'], ['3', '40.00', '3'], ['4', '20.00', '4']], 'source_fees')
    require(target['fees'] == source['fees'] and target['stock'] == source['stock'], 'fee_stock_drift')
    require(len(source['stock']) == 5 and all(row[1] == 'done' for row in source['stock']), 'five_done_stock_moves')
    require([Decimal(row[2]) for row in source['stock'][2:]] == [1, 4, 2], 'stock_1_4_2')
    require(source['treatment'] == target['treatment'] == [[i, 'confirmed'] for i in range(1, 5)], 'confirmed_treatment_source')
    require(source['exam'] == target['exam'] == [[1, 'confirmed']], 'confirmed_exam_source')
    stable = {table: target['exact'][table] for table in old.STABLE_AFTER_PAYMENT}
    require(stable == {table: before['exact'][table] for table in old.STABLE_AFTER_PAYMENT}, 'target_31_table_drift')
    require(target['audit_rows'][:len(source['audit_rows'])] == source['audit_rows'], 'w4_audit_history_drift')
    accounting = money_check(target['money'], before['money'])
    require(old.canonical(target['money']) == old.canonical(historical['money']), 'historical_final_money_drift')
    require(target['cashier'] == [['1', '5', '1', '1', 'cash', '500.00', '2026-10-15', '2026-10-15 07:52:02.559463'],
                                  ['2', '5', '1', '1', 'cash', '240.00', '2026-10-15', '2026-10-15 07:52:03.952418']], 'cashier_scope_date')
    require(len(target['audit_rows']) >= len(source['audit_rows']) + 2, 'new_audits_missing')
    require(len(target['pay_audits']) == 2 and [a[0] for a in target['pay_audits']] == accounting['audit_ids'], 'audit_ids')
    require(all(a[1:] == ['settlement.pay', 'accepted', 5, 1] for a in target['pay_audits']), 'audit_actor_scope')
    require(len(target['receipts']) == 3, 'receipt_count_live')
    require([(r['id'], r['store'], r['actor'], r['operation']) for r in target['receipts']]
            == [(1, 1, 5, 'bill'), (2, 1, 5, 'pay'), (3, 1, 5, 'pay')], 'receipt_actor_store')
    require([r['result'] for r in target['receipts']]
            == [r['result'] for r in target['money']['receipts']], 'receipt_json_link')
    require(target['exact']['ydental_settlement_refund']['rows'] == 0
            and target['exact']['ydental_settlement_close']['rows'] == 0, 'no_refund_close')
    return {'accounting': accounting, 'stable': stable}


def full_flow_simulations(before, historical):
    """Exercise the real pair assessor with fixed historical shapes in memory."""
    locked = json_file(ROOT / 'docs/evidence/s10-e2e-w5/preflight.json')['source']
    post_stop = json_file(old.RUN / 'post-stop-readonly.json')
    fees = [['1', '600.00', '1'], ['2', '80.00', '2'],
            ['3', '40.00', '3'], ['4', '20.00', '4']]
    stock = [[str(i), 'done', str(qty)] for i, qty in enumerate((1, 1, 1, 4, 2), 1)]
    treatment = [[i, 'confirmed'] for i in range(1, 5)]
    exam = [[1, 'confirmed']]
    prefix = list(range(1, locked['exact_signatures']['ydental_access_audit']['rows'] + 1))
    source = {'oid': 2100301, 'cluster': old.CLUSTER,
              'exact': locked['exact_signatures'], 'module_count': 92,
              'module_meta_sha256': before['module_meta_sha256'],
              'views': before['views'], 'filestore': locked['filestore'],
              'money': before['money'], 'fees': fees, 'stock': stock,
              'treatment': treatment, 'exam': exam,
              'audit_rows': prefix}
    target = {'oid': 2100310, 'cluster': old.CLUSTER,
              'exact': before['exact'], 'module_count': 92,
              'module_meta_sha256': before['module_meta_sha256'],
              'views': before['views'], 'filestore': locked['filestore'],
              'money': historical['money'], 'fees': fees, 'stock': stock,
              'treatment': treatment, 'exam': exam,
              'audit_rows': prefix + ['synthetic_new_audit_1', 'synthetic_new_audit_2'],
              'cashier': [[str(row[0]), str(row[2]), str(row[1]), '1',
                           str(row[3]), str(row[4]), str(row[5]), str(row[6])]
                          for row in post_stop['s10_cashier_rows']],
              'pay_audits': [[a['id'], a['event'], a['result'], a['user'], a['store']]
                             for a in historical['money']['audits'] if a['event'] == 'settlement.pay'],
              'receipts': [{'id': r[0], 'store': r[1], 'actor': r[2],
                            'operation': r[3], 'result': r[4]}
                           for r in post_stop['receipts']]}
    require(assess_pair(source, target, before, historical)['accounting']['amounts'] == [500, 240], 'complete_pair_positive')
    cases = {
        'source_oid_drift': lambda s, t: s.update(oid=0),
        'source_38_table_drift': lambda s, t: s['exact']['ydental_treatment_fee'].update(sha256='0' * 64),
        'target_31_table_drift': lambda s, t: t['exact']['stock_move'].update(sha256='0' * 64),
        'cashier_business_date': lambda s, t: t['cashier'][0].__setitem__(6, '2026-10-14'),
        'cashier_actual_time': lambda s, t: t['cashier'][1].__setitem__(7, '2026-10-15 00:00:00'),
        'audit_history_overwrite': lambda s, t: t['audit_rows'].__setitem__(0, 0),
        'target_third_payment': lambda s, t: t['money']['payments'].append(deepcopy(t['money']['payments'][1])),
        'target_refund': lambda s, t: t['exact']['ydental_settlement_refund'].update(rows=1),
        'wrong_stock_quantity': lambda s, t: t['stock'][-1].__setitem__(2, '3'),
        'wrong_receipt_actor': lambda s, t: t['receipts'][1].update(actor=6),
    }
    for label, mutate in cases.items():
        bad_source, bad_target = deepcopy(source), deepcopy(target)
        mutate(bad_source, bad_target)
        try:
            assess_pair(bad_source, bad_target, before, historical)
        except AssertionError:
            continue
        raise AssertionError(f'full_flow_negative_accepted_{label}')
    return {'status': 'SIMULATED_PASS', 'complete_pair_positive': 1,
            'negative_cases': list(cases)}


def live():
    start = time.monotonic()
    pre = json_file(PREFLIGHT)
    check = json_file(CHECKPOINT)
    require(pre['status'] == 'PREFLIGHT_PASS_SQL0' and pre['authorization'] == AUTH, 'preflight_required')
    require(check['authorization'] == AUTH and check['preflight_comment_id'] > AUTH, 'readback_checkpoint_required')
    require(check['script_sha256'] == pre['r1_script_sha256'] == sha(Path(__file__)), 'script_drift_after_checkpoint')
    require(check['preflight_sha256'] == sha(PREFLIGHT) and check['github_exact_readback'] is True, 'preflight_drift_after_checkpoint')
    require(check['fixed_head'] == BASE, 'checkpoint_head')
    for name, expected in pre['fixed_file_sha256'].items():
        require(sha(ROOT / name) == expected, f'history_drift_{name}')
    require(sha(old.RUN / 'database.json') == pre['target']['marker_sha256']
            and sha(old.RUN / 'odoo.conf') == pre['target']['config_sha256'], 'target_identity_drift')
    require(sha(old.SOURCE_RUN / 'database.json') == pre['source']['marker_sha256']
            and sha(old.SOURCE_RUN / 'odoo.conf') == pre['source']['config_sha256'], 'source_identity_drift')
    v = json_file(W5)
    before = json_file(old.RUN / 'before-web.json')
    historical = json_file(old.RUN / 'pay-2-observed.json')
    def timeout(_signum, _frame):
        raise TimeoutError('single_readonly_window_timeout')
    previous_handler = signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, 295)
    try:
        def bounded_reader(database, oid):
            require(time.monotonic() - start < 270, 'sql_window_no_time_for_next_database')
            return inspect_database(database, oid)
        source, target = ordered_read(bounded_reader)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
    require(time.monotonic() - start < 300, 'sql_window_timeout')
    assessment = assess_pair(source, target, before, historical)
    accounting, stable = assessment['accounting'], assessment['stable']
    duration = time.monotonic() - start
    require(duration <= 300, 'sql_window_exceeded')
    return {'status': 'NEW_READONLY_SQL_PASS', 'window_seconds': round(duration, 3),
            'connections': {'source': 1, 'target': 1}, 'transaction_read_only': True,
            'source': {'database': old.SOURCE, 'oid': source['oid'], 'cluster': source['cluster'],
                'schema': source['schema'],
                'business_38_sha256': source['exact'], 'module_count': source['module_count'],
                'module_meta_sha256': source['module_meta_sha256'], 'views': source['views'],
                'filestore': source['filestore'], 'invoice': source['money']['invoices'],
                'payment_count': len(source['money']['payments']), 'partial_count': len(source['money']['partials']),
                'audit_row_count': len(source['audit_rows']), 'fees': source['fees'],
                'stock': source['stock'], 'treatment': source['treatment'], 'exam': source['exam']},
            'target': {'database': old.NAME, 'oid': target['oid'], 'cluster': target['cluster'],
                'schema': target['schema'],
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
                'treatment': target['treatment'], 'exam': target['exam'],
                'refund_count': target['exact']['ydental_settlement_refund']['rows'],
                'close_count': target['exact']['ydental_settlement_close']['rows']},
            'checks': accounting, 'historical_private_sha256': v['hashes']['private_files_sha256'],
            'not_run': ['Odoo HTTP/CLI/shell', 'Firefox/Playwright', 'CREATE', 'payment POST',
                'module install/upgrade', 'W5 browser-complete', 'W5 final_audit']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('preflight', 'live'))
    args = parser.parse_args()
    if args.mode == 'preflight':
        data = offline()
        data['r1_script_sha256'] = sha(Path(__file__))
        write_new(PREFLIGHT, data)
        print('PREFLIGHT_PASS_SQL0', data['r1_script_sha256'])
    else:
        write_new(LIVE, live())
        print('NEW_READONLY_SQL_PASS', LIVE)
