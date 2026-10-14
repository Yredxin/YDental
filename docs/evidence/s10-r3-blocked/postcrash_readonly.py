"""Read-only, credential-redacted SQL/incident snapshot after S10 SIGSEGV."""
import configparser
import hashlib
import json
from pathlib import Path
import re

import psycopg2
from psycopg2 import sql
from PyPDF2 import PdfReader

root = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
name = 'ydental_s10_test_20261014020300_8b6c1d4e'
run = root / '.local' / name
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[0-9a-f]{8}', name)
marker = json.loads((run / 'database.json').read_text())
assert marker['database'] == name and marker['oid'] == 2056451
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == marker['config_sha256']
cfg = configparser.ConfigParser()
assert cfg.read(run / 'odoo.conf') and cfg['options']['db_name'] == name
f1 = json.loads((run / 'f1.json').read_text())
f5 = json.loads((run / 'f5.json').read_text())
actions = [json.loads(line) for line in (run / 'actions.jsonl').read_text().splitlines()]
races = [json.loads(line) for line in (run / 'race-actions.jsonl').read_text().splitlines()]
crash = json.loads((run / 'crash-2383730.json').read_text())
assert crash['signal'] == 11 and any(row['signal'] == 11 for row in races)
tables = ('ydental_treatment_event', 'ydental_treatment_fee',
          'ydental_settlement_source', 'ydental_settlement_payment',
          'ydental_settlement_refund', 'ydental_settlement_close',
          'ydental_settlement_trade', 'account_move', 'account_payment',
          'account_partial_reconcile', 'stock_move', 'stock_move_line',
          'stock_quant', 'sale_order', 'purchase_order')

def rows(cursor, query, args=()):
    cursor.execute(query, args)
    return cursor.fetchall()

def alloc(cursor, payment_id):
    return rows(cursor, "SELECT invoice.id,partial.amount,partial.id FROM "
        "ydental_settlement_payment p JOIN account_payment native ON "
        "native.id=p.ydental_payment_id JOIN account_move_line paid ON "
        "paid.move_id=native.move_id JOIN account_partial_reconcile partial ON "
        "partial.credit_move_id=paid.id JOIN account_move_line due ON "
        "due.id=partial.debit_move_id JOIN account_move invoice ON "
        "invoice.id=due.move_id WHERE p.id=%s ORDER BY invoice.invoice_date,invoice.id",
        (payment_id,))

with psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
                      password=cfg['options']['db_password'], dbname=name) as db:
    db.set_session(readonly=True)
    with db.cursor() as cursor:
        assert rows(cursor, 'SELECT oid FROM pg_database WHERE datname=%s', (name,))[0][0] == marker['oid']
        counts = {}
        for table in tables:
            cursor.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table)))
            counts[table] = cursor.fetchone()[0]
        invoices = rows(cursor, 'SELECT id,amount_total,amount_residual,state,move_type '
                        'FROM account_move WHERE id IN %s ORDER BY id',
                        (tuple([f1['invoice_id'], f5['old_invoice_id'], f5['new_invoice_id']]),))
        native = {
            'f1_500': alloc(cursor, f1['payment500_id']),
            'f1_240': alloc(cursor, f1['payment240_id']),
            'f5_300': alloc(cursor, f5['payment_id']),
            'f5_only_new': alloc(cursor, f5['only_new_payment_id']),
            'invoices': invoices,
            'refund_states': rows(cursor, 'SELECT ydental_state,count(*),coalesce(sum(ydental_amount),0) '
                                  'FROM ydental_settlement_refund GROUP BY ydental_state ORDER BY ydental_state'),
            'done_refund_native_journals': rows(cursor, "SELECT r.id,r.ydental_refund_business_date,"
                "r.ydental_refund_channel,r.ydental_executor_id,p.journal_id,p.state "
                "FROM ydental_settlement_refund r JOIN account_payment p ON "
                "p.id=r.ydental_native_payment_id WHERE r.ydental_state='done' ORDER BY r.id"),
            'source_bad_posted_or_company': rows(cursor, "SELECT count(*) FROM ydental_settlement_source s "
                "LEFT JOIN account_move m ON m.id=s.ydental_invoice_id WHERE m.id IS NULL "
                "OR m.state!='posted' OR m.company_id!=(SELECT company_id FROM "
                "ydental_access_store WHERE id=s.ydental_store_id)")[0][0],
            'source_duplicate_fee': rows(cursor, 'SELECT count(*) FROM (SELECT ydental_fee_id FROM '
                'ydental_settlement_source GROUP BY ydental_fee_id HAVING count(*)>1) x')[0][0],
            'native_partial_total': rows(cursor, 'SELECT count(*),coalesce(sum(amount),0) '
                'FROM account_partial_reconcile')[0],
            'native_done_stock_moves': rows(cursor, "SELECT count(*) FROM stock_move WHERE state='done'")[0][0],
            'cross_company_trade': rows(cursor, "SELECT t.id,a.id,a.state,a.company_id,b.id,b.state,"
                "b.company_id,o.state,i.state FROM ydental_settlement_trade t JOIN account_move a "
                "ON a.id=t.ydental_sale_invoice_id JOIN account_move b ON b.id=t.ydental_purchase_bill_id "
                "JOIN stock_move o ON o.id=t.ydental_out_move_id JOIN stock_move i "
                "ON i.id=t.ydental_in_move_id ORDER BY t.id"),
            'deadlocks': rows(cursor, 'SELECT deadlocks FROM pg_stat_database WHERE datname=%s', (name,))[0][0],
            'modules': rows(cursor, "SELECT name,state FROM ir_module_module WHERE name IN "
                "('ydental_settlement','ydental_settlement_test') ORDER BY name"),
        }

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

logs = {}
for path in sorted(run.glob('*.log')):
    logs[path.name] = {'sha256': digest(path), 'bytes': path.stat().st_size}
pdfs = {}
for path in sorted(run.glob('*.pdf')):
    pages = PdfReader(str(path)).pages
    text = [(page.extract_text() or '') for page in pages]
    pdfs[path.name] = {'sha256': digest(path), 'bytes': path.stat().st_size,
                       'pages': len(pages),
                       'extracted_chinese_characters': sum(len(re.findall(r'[\u4e00-\u9fff]', part))
                                                           for part in text)}

evidence = {
    'authorization': 'https://github.com/Yredxin/YDental/issues/34#issuecomment-6158230350',
    'status': 'BLOCKED_NEW_NATIVE_SIGSEGV',
    'database': {k: marker[k] for k in ('database', 'oid', 'cluster', 'port', 'core',
                                        'source_commit', 'config_sha256')},
    'fixed_product_sha': '4b168a84254882a2e1e3e5037c372ab57fc3dfdd',
    'fixed_test_sha': '255b48f54495eb99638af8ffc824771b9a5af3e7',
    'actions': actions,
    'parallel_processes': races,
    'crash': crash,
    'sql': {'table_counts': counts, **native},
    'log_files': logs,
    'pdf_files': pdfs,
    'core_pattern': '|/usr/share/apport/apport -p%p -s%s -c%c -d%d -P%P -u%u -g%g -F%F -- %E',
    'core_visible': False,
    'post_crash_odoo_or_firefox_runs': 0,
}
target = root / 'docs/evidence/s10-r3-blocked/incident.json'
target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, default=str) + '\n')
print(json.dumps({'database': name, 'oid': marker['oid'],
                  'sequential_exit_codes': [row['exit_code'] for row in actions],
                  'parallel_exit_codes': [row['exit_code'] for row in races],
                  'table_counts': counts, 'deadlocks': native['deadlocks']}, ensure_ascii=False))
