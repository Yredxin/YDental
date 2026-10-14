"""Read-only, scoped SQL verification of the one FC1 synthetic database."""

import configparser
import hashlib
import json
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ydental_s10_test_20261014145000_fc1a84d7'
RUN = ROOT / '.local' / NAME
marker = json.loads((RUN / 'database.json').read_text())
assert marker['database'] == NAME and marker['oid'] == 2100197
assert marker['auth'] == 6170892559
cfg = configparser.ConfigParser(interpolation=None)
assert cfg.read(ROOT.parent / 'odoo.conf')
opts = cfg['options']
assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')

connection = psycopg2.connect(dbname=NAME, host='127.0.0.1', port=5432,
                              user='odoo', password=opts['db_password'], connect_timeout=5)
connection.set_session(readonly=True)


def one(cursor, query, params=()):
    cursor.execute(query, params)
    return cursor.fetchone()[0]


with connection.cursor() as cursor:
    assert one(cursor, 'SELECT oid FROM pg_database WHERE datname=%s', (NAME,)) == marker['oid']
    assert one(cursor, 'SELECT system_identifier::text FROM pg_control_system()') == marker['cluster']
    modules = one(cursor, "SELECT count(*) FROM ir_module_module WHERE state='installed'")
    assert modules == 92
    group_ids = [row[0] for row in (cursor.execute(
        'SELECT hid FROM res_groups_implied_rel WHERE gid=1 AND hid IN (22,44,45) ORDER BY hid') or cursor.fetchall())]
    assert group_ids == [22, 44, 45]
    price = cursor.execute('SELECT state,ydental_unit_price,ydental_version FROM ydental_intake_price') or cursor.fetchall()
    assert len(price) == 1 and price[0][0] == 'published' and price[0][1] == 100
    snapshots = one(cursor, 'SELECT count(*) FROM ydental_intake_snapshot')
    assert snapshots == 3
    warehouses = one(cursor, 'SELECT count(*) FROM stock_warehouse')
    assert warehouses == 2
    cursor.execute('SELECT move_type,state,count(*),sum(amount_total) FROM account_move GROUP BY move_type,state ORDER BY move_type')
    moves = [(kind, state, count, float(total)) for kind, state, count, total in cursor.fetchall()]
    assert moves == [('entry', 'posted', 6, 455.0), ('out_invoice', 'posted', 3, 300.0),
                     ('out_refund', 'posted', 2, 55.0)]
    unbalanced = one(cursor, '''SELECT count(*) FROM (
        SELECT m.id FROM account_move m JOIN account_move_line l ON l.move_id=m.id
        GROUP BY m.id HAVING abs(sum(l.balance)) > 0.000001) bad''')
    assert unbalanced == 0
    cursor.execute('''SELECT p.payment_type,p.state,p.date,j.code,count(*),sum(p.amount),
        bool_and(m.state='posted') FROM account_payment p
        JOIN account_move m ON m.id=p.move_id JOIN account_journal j ON j.id=p.journal_id
        GROUP BY p.payment_type,p.state,p.date,j.code ORDER BY p.payment_type,p.date,j.code''')
    payments = [dict(type=typ, state=state, date=str(date), journal=journal,
                     count=count, amount=float(amount), posted=posted)
                for typ, state, date, journal, count, amount, posted in cursor.fetchall()]
    assert sum(row['amount'] for row in payments if row['type'] == 'inbound') == 300
    assert sum(row['amount'] for row in payments if row['type'] == 'outbound') == 55
    assert all(row['posted'] for row in payments)
    cursor.execute('SELECT amount FROM account_partial_reconcile ORDER BY id')
    partials = [float(row[0]) for row in cursor.fetchall()]
    assert sorted(partials) == [25, 30, 100, 100, 100]
    cursor.execute('''SELECT r.ydental_state,r.ydental_amount,r.ydental_refund_business_date,
        r.ydental_refund_channel,p.amount,p.payment_type,j.code,m.state
        FROM ydental_settlement_refund r
        LEFT JOIN account_payment p ON p.id=r.ydental_native_payment_id
        LEFT JOIN account_journal j ON j.id=p.journal_id
        LEFT JOIN account_move m ON m.id=p.move_id ORDER BY r.id''')
    refunds = [dict(state=state, amount=float(amount), actual_day=str(day) if day else None,
                    channel=channel, native_amount=float(native) if native else 0,
                    native_type=typ, journal=journal, move_state=move)
               for state, amount, day, channel, native, typ, journal, move in cursor.fetchall()]
    assert [row['state'] for row in refunds] == ['approved', 'done', 'done']
    assert [row['native_amount'] for row in refunds] == [0, 25, 30]
    assert all(row['journal'] == 'X41' and row['move_state'] == 'posted' for row in refunds[1:])
    cursor.execute('''SELECT ydental_channel,ydental_state,ydental_business_date,ydental_cycle,
        ydental_gross,ydental_refunded,ydental_pending FROM ydental_settlement_close ORDER BY id''')
    closes = [dict(channel=channel, state=state, day=str(day), cycle=cycle,
                   gross=float(gross), refunded=float(refunded), pending=float(pending))
              for channel, state, day, cycle, gross, refunded, pending in cursor.fetchall()]
    assert [(row['channel'], row['state'], row['gross'], row['refunded'], row['pending']) for row in closes] == [
        ('card', 'confirmed', 0, 0, 30), ('cash', 'unlocked', 100, 0, 0),
        ('wechat', 'confirmed', 100, 0, 0)]
    assert closes[1]['day'] < closes[0]['day']
    cursor.execute('SELECT ydental_old_channel,ydental_new_channel,m.state FROM ydental_settlement_correction c JOIN account_move m ON m.id=c.ydental_move_id')
    corrections = cursor.fetchall()
    assert corrections == [('cash', 'wechat', 'posted')]
    cursor.execute('''SELECT l.debit,l.credit,l.account_id FROM ydental_settlement_correction c
        JOIN account_move_line l ON l.move_id=c.ydental_move_id ORDER BY l.id''')
    correction_lines = [(float(debit), float(credit), account) for debit, credit, account in cursor.fetchall()]
    assert len(correction_lines) == 2 and correction_lines[0][:2] == (100, 0)
    assert correction_lines[1][:2] == (0, 100) and correction_lines[0][2] != correction_lines[1][2]
    cursor.execute("SELECT ydental_event,count(*) FROM ydental_access_audit WHERE ydental_event LIKE 'settlement.%' GROUP BY ydental_event ORDER BY ydental_event")
    audit = dict(cursor.fetchall())
    assert audit['settlement.refund.approve'] == 3 and audit['settlement.refund.execute'] == 2
    assert audit['settlement.reclassify'] == 1 and audit['settlement.unlock'] == 1
    cursor.execute("SELECT ydental_event,ydental_user_id,ydental_store_id,count(*) FROM ydental_access_audit WHERE ydental_event LIKE 'settlement.%' GROUP BY 1,2,3 ORDER BY 1,2")
    audit_actor_rows = cursor.fetchall()
    assert len({store for _event, _actor, store, _count in audit_actor_rows}) == 1
    assert len({actor for _event, actor, _store, _count in audit_actor_rows}) == 2
    mail = one(cursor, 'SELECT count(*) FROM mail_mail')
    bus = one(cursor, 'SELECT count(*) FROM bus_bus')
    deadlocks = one(cursor, 'SELECT deadlocks FROM pg_stat_database WHERE datname=current_database()')
    assert mail == 0 and deadlocks == 0
connection.rollback()
connection.close()

evidence = [json.loads(line) for line in (RUN / 'fc1-evidence.jsonl').read_text().splitlines()]
ledger = [json.loads(line) for line in (RUN / 'fc1-commit-ledger.jsonl').read_text().splitlines()]
commits = [row for row in ledger if row['status'] == 'COMMITTED']
assert len(commits) == 7 and [row['attempt'] for row in commits] == list(range(1, 8))
races = {}
for case in ('A', 'B', 'C_refund', 'C_reclass'):
    overlap = next(row for row in evidence if row['case'] == case and row['stage'] == 'overlap')
    result = next(row for row in evidence if row['case'] == case and row['stage'] == 'race_result')
    assert overlap['first_backend'] != overlap['second_backend']
    assert overlap['second_waiting'] and result['second']['sqlstate'] == '40001'
    races[case] = {'first_backend': overlap['first_backend'], 'second_backend': overlap['second_backend'],
                   'second_start_utc': overlap['second_start_utc'], 'second_waiting_before_commit': True,
                   'first': result['first'], 'second': result['second']['status'],
                   'exception': result['second']['exception'], 'sqlstate': result['second']['sqlstate']}
phases = {}
for row in evidence:
    if row['stage'] == 'fresh_cursor_review':
        phases[row['case']] = {name: row['counts'][name] for name in (
            'mail.message', 'mail.mail', 'bus.bus', 'ydental.access.audit',
            'account.move', 'account.payment', 'account.partial.reconcile')}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


output = {
    'scope': 'S10-FC1 single synthetic Odoo shell; SQL audit read-only',
    'authorization_comment': 6170892559,
    'checkpoint_comment': 6171084143,
    'start_head': 'ce21976f4bc448ff1aa3c2380ce6f959aed9dbde',
    'database': {'name': NAME, 'oid': marker['oid'], 'source_oid': marker['source_oid'],
                 'cluster': marker['cluster'], 'modules': modules, 'warehouses': warehouses,
                 'config_sha256': marker['config_sha256'], 'marker_sha256': sha(RUN / 'database.json')},
    'run': {**json.loads((RUN / 'run-result.json').read_text()),
            'commit_count': len(commits), 'planned_commit_purposes': [row['purpose'] for row in commits]},
    'races': races,
    'finance': {'move_summary': moves, 'unbalanced_moves': unbalanced, 'payments': payments,
                'partial_amounts': partials, 'refunds': refunds, 'closes': closes,
                'corrections': [{'from': old, 'to': new, 'state': state} for old, new, state in corrections],
                'correction_lines': [{'debit': debit, 'credit': credit} for debit, credit, _account in correction_lines],
                'audit_events': audit, 'mail_mail': mail, 'bus_bus': bus, 'deadlocks': deadlocks,
                'phase_counts': phases,
                'audit_actor_roles': {'distinct_business_actors': 2, 'one_store': True,
                                      'third_finance_reviewer_only_rollback': True},
                'published_price': 100, 'snapshots': snapshots, 'global_group_xmlids_enabled': [
                    'product.group_product_pricelist', 'stock.group_stock_multi_locations',
                    'stock.group_stock_multi_warehouses']},
    'private_sha256': {'ledger': sha(RUN / 'fc1-commit-ledger.jsonl'),
                       'timeline': sha(RUN / 'fc1-evidence.jsonl'),
                       'odoo_log': sha(RUN / 'odoo-fc1.log')},
    'limits': {'same_key_after_done_replay': 'NOT_RUN', 'unknown_recovery_race': 'NOT_RUN',
               'corrected_payment_wechat_refund': 'NOT_RUN',
               'date_escape_negative': 'NOT_RUN', 'cross_company_negative': 'NOT_RUN',
               'bus_precommit_intent_detail': 'NOT_CAPTURED',
               'full_S10_T01_T16': 'NOT_RUN'},
}
target = ROOT / 'docs/evidence/s10-fc1/verification.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(output, indent=2, ensure_ascii=False) + '\n')
print(json.dumps({'status': 'READ_ONLY_PASS', 'evidence': str(target),
                  'commits': len(commits), 'races': len(races)}))
