"""Read-only native ledger and persisted-business upgrade audit for one guarded DB."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re

import psycopg2
from psycopg2 import sql

root = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
parser.add_argument('--phase', choices=('before', 'after'), required=True)
args = parser.parse_args()
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', args.db)
run = root / '.local' / args.db
marker = json.loads((run / 'database.json').read_text())
assert marker['database'] == args.db and marker['cluster'] == '7694897083368259627'
assert not list(run.glob('crash-*.json'))
config = configparser.ConfigParser(interpolation=None)
assert config.read(run / 'odoo.conf') and config['options']['db_name'] == args.db
assert hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest() == marker['config_sha256']
tables = ('ydental_treatment_event', 'ydental_treatment_fee', 'ydental_settlement_source',
    'ydental_settlement_payment', 'ydental_settlement_refund', 'ydental_settlement_close',
    'ydental_settlement_correction', 'ydental_settlement_trade', 'account_move',
    'account_payment', 'account_partial_reconcile', 'stock_move', 'stock_move_line',
    'stock_quant', 'sale_order', 'purchase_order')
f1 = json.loads((run / 'f1.json').read_text())
f5 = json.loads((run / 'f5.json').read_text())

with psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
        password=config['options']['db_password'], dbname=args.db) as conn:
    conn.set_session(readonly=True)
    with conn.cursor() as cursor:
        cursor.execute('SELECT oid FROM pg_database WHERE datname=%s', (args.db,))
        assert cursor.fetchone()[0] == marker['oid']
        table_hashes = {}
        for table in tables:
            cursor.execute(sql.SQL('SELECT to_jsonb(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
            rows = [line[0] for line in cursor]
            digest = hashlib.sha256(('\n'.join(rows) + '\n').encode()).hexdigest()
            table_hashes[table] = {'count': len(rows), 'sha256': digest}
        cursor.execute("SELECT state, count(*) FROM ir_module_module WHERE name IN "
                       "('ydental_settlement','ydental_settlement_test') GROUP BY state")
        modules = dict(cursor.fetchall())
        cursor.execute("SELECT count(*) FROM ydental_settlement_source s LEFT JOIN account_move m "
                       "ON m.id=s.ydental_invoice_id WHERE m.id IS NULL OR m.state!='posted' "
                       "OR m.company_id!=(SELECT company_id FROM ydental_access_store WHERE id=s.ydental_store_id)")
        bad_source = cursor.fetchone()[0]
        cursor.execute('SELECT count(*) FROM (SELECT ydental_fee_id FROM ydental_settlement_source '
                       'GROUP BY ydental_fee_id HAVING count(*)>1) x')
        duplicate_source = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM ydental_settlement_trade t JOIN account_move a "
                       "ON a.id=t.ydental_sale_invoice_id JOIN account_move b "
                       "ON b.id=t.ydental_purchase_bill_id JOIN stock_move o "
                       "ON o.id=t.ydental_out_move_id JOIN stock_move i "
                       "ON i.id=t.ydental_in_move_id WHERE a.state='posted' AND b.state='posted' "
                       "AND o.state='done' AND i.state='done' AND a.company_id!=b.company_id")
        valid_trades = cursor.fetchone()[0]
        cursor.execute("SELECT ydental_state,count(*),coalesce(sum(ydental_amount),0) "
                       "FROM ydental_settlement_refund GROUP BY ydental_state ORDER BY ydental_state")
        refunds = {state: {'count': count, 'amount': float(amount)} for state, count, amount in cursor.fetchall()}
        cursor.execute("SELECT count(*) FROM ydental_settlement_refund r LEFT JOIN account_payment p "
                       "ON p.id=r.ydental_native_payment_id WHERE r.ydental_state='done' "
                       "AND (p.id IS NULL OR p.state NOT IN ('paid','reconciled'))")
        bad_done = cursor.fetchone()[0]
        cursor.execute("SELECT count(*) FROM ydental_settlement_refund r WHERE r.ydental_state IN "
                       "('requested','approved','failed','unknown','rejected','cancelled') "
                       "AND r.ydental_native_payment_id IS NOT NULL")
        bad_not_done = cursor.fetchone()[0]
        cursor.execute("SELECT count(*),coalesce(sum(amount),0) FROM account_partial_reconcile")
        native_partials = cursor.fetchone()
        cursor.execute('SELECT deadlocks FROM pg_stat_database WHERE datname=%s', (args.db,))
        deadlocks = cursor.fetchone()[0]
        def allocations(payment_id):
            cursor.execute("SELECT invoice.id, partial.amount, partial.id "
                "FROM ydental_settlement_payment source "
                "JOIN account_payment payment ON payment.id=source.ydental_payment_id "
                "JOIN account_move_line paid ON paid.move_id=payment.move_id "
                "JOIN account_partial_reconcile partial ON partial.credit_move_id=paid.id "
                "JOIN account_move_line due ON due.id=partial.debit_move_id "
                "JOIN account_move invoice ON invoice.id=due.move_id "
                "WHERE source.id=%s ORDER BY invoice.invoice_date,invoice.id", (payment_id,))
            return [{'invoice_id': invoice, 'amount': float(amount), 'partial_id': partial}
                for invoice, amount, partial in cursor.fetchall()]
        f1_500 = allocations(f1['payment500_id'])
        f1_240 = allocations(f1['payment240_id'])
        f5_300 = allocations(f5['payment_id'])
        only_new = allocations(f5['only_new_payment_id'])
        cursor.execute('SELECT amount_residual FROM account_move WHERE id=%s', (f1['invoice_id'],))
        f1_residual = float(cursor.fetchone()[0])
        audit = {'database': args.db, 'oid': marker['oid'], 'source_commit': marker['source_commit'],
            'phase': args.phase, 'modules': modules, 'tables': table_hashes,
            'bad_source': bad_source, 'duplicate_source': duplicate_source,
            'valid_trades': valid_trades, 'refunds': refunds,
            'bad_done_refund': bad_done, 'bad_not_done_refund': bad_not_done,
            'native_partials': {'count': native_partials[0], 'amount': float(native_partials[1])},
            'deadlocks': deadlocks, 'f1': {'payment500': f1_500, 'payment240': f1_240,
                'residual': f1_residual},
            'f5': {'selected300': f5_300, 'only_new': only_new}}
assert modules == {'installed': 2}, modules
assert not (bad_source or duplicate_source or bad_done or bad_not_done or deadlocks)
assert valid_trades >= 1
assert [row['amount'] for row in f1_500] == [500]
assert [row['amount'] for row in f1_240] == [240]
assert f1_residual == 0
assert [row['amount'] for row in f5_300] == [270, 30], f5_300
assert len(only_new) == 1 and only_new[0]['invoice_id'] in f5['new_invoice_ids']
target = run / ('audit-' + args.phase + '.json')
with target.open('x') as stream:
    json.dump(audit, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
if args.phase == 'after':
    before = json.loads((run / 'audit-before.json').read_text())
    assert audit['tables'] == before['tables'], 'Persisted business rows changed during upgrade'
print('S10_NATIVE_SQL_AUDIT', json.dumps({'phase': args.phase, 'database': args.db,
    'oid': marker['oid'], 'tables': len(tables), 'valid_trades': valid_trades,
    'f1_500_240': [f1_500, f1_240], 'f5_270_30': f5_300,
    'refunds': refunds, 'deadlocks': deadlocks}), flush=True)
