"""Verify the single FC2 synthetic database with read-only SQL and redacted output."""

import configparser
import hashlib
import json
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
NAME = 'ydental_s10_test_20261014152000_fc2a7d31'
RUN = ROOT / '.local' / NAME
marker = json.loads((RUN / 'database.json').read_text())
assert marker['database'] == NAME and marker['oid'] == 2100212
assert marker['auth'] == 6171419484 and marker['source_oid'] == 2100080
cfg = configparser.ConfigParser(interpolation=None)
assert cfg.read(ROOT.parent / 'odoo.conf')
opts = cfg['options']
assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
endpoint = dict(host='127.0.0.1', port=5432, user='odoo', password=opts['db_password'], connect_timeout=5)


def one(cursor, query, params=()):
    cursor.execute(query, params)
    return cursor.fetchone()[0]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


connection = psycopg2.connect(dbname=NAME, **endpoint)
connection.set_session(readonly=True)
with connection.cursor() as cur:
    assert one(cur, 'SELECT oid FROM pg_database WHERE datname=%s', (NAME,)) == 2100212
    assert one(cur, 'SELECT system_identifier::text FROM pg_control_system()') == marker['cluster']
    assert one(cur, "SELECT count(*) FROM ir_module_module WHERE state='installed'") == 92
    cur.execute('SELECT hid FROM res_groups_implied_rel WHERE gid=1 AND hid IN (22,44,45) ORDER BY hid')
    assert [row[0] for row in cur.fetchall()] == [22, 44, 45]
    cur.execute('SELECT state,ydental_unit_price FROM ydental_intake_price')
    assert cur.fetchall() == [('published', 100)]
    assert one(cur, 'SELECT count(*) FROM ydental_intake_snapshot') == 3
    assert one(cur, 'SELECT count(*) FROM stock_warehouse') == 2
    cur.execute('SELECT move_type,state,count(*),sum(amount_total) FROM account_move GROUP BY 1,2 ORDER BY 1')
    moves = [(typ, state, count, float(total)) for typ, state, count, total in cur.fetchall()]
    assert moves == [('entry', 'posted', 7, 495), ('out_invoice', 'posted', 3, 300),
                     ('out_refund', 'posted', 3, 95)]
    assert one(cur, '''SELECT count(*) FROM (SELECT m.id FROM account_move m
        JOIN account_move_line l ON l.move_id=m.id GROUP BY m.id
        HAVING abs(sum(l.balance)) > 0.000001) unbalanced''') == 0
    cur.execute('''SELECT p.payment_type,p.state,p.date,j.code,count(*),sum(p.amount),
        bool_and(m.state='posted') FROM account_payment p
        JOIN account_move m ON m.id=p.move_id JOIN account_journal j ON j.id=p.journal_id
        GROUP BY 1,2,3,4 ORDER BY 1,3,4''')
    payments = [dict(type=typ, state=state, day=str(day), journal=journal,
                     count=count, amount=float(amount), move_posted=posted)
                for typ, state, day, journal, count, amount, posted in cur.fetchall()]
    assert sum(row['amount'] for row in payments if row['type'] == 'inbound') == 300
    assert sum(row['amount'] for row in payments if row['type'] == 'outbound') == 95
    assert all(row['move_posted'] for row in payments)
    assert [row['amount'] for row in payments if row['type'] == 'outbound' and row['journal'] == 'Y11'] == []
    assert [row['amount'] for row in payments if row['type'] == 'outbound' and row['journal'] == 'Y21'] == [40]
    cur.execute('SELECT amount FROM account_partial_reconcile ORDER BY id')
    partials = [float(row[0]) for row in cur.fetchall()]
    assert partials == [100, 100, 100, 25, 30, 40]
    cur.execute('''SELECT r.ydental_state,r.ydental_amount,r.ydental_refund_business_date,
        r.ydental_refund_channel,p.amount,j.code,m.state,
        r.ydental_requester_id,r.ydental_approver_id,r.ydental_executor_id
        FROM ydental_settlement_refund r
        LEFT JOIN account_payment p ON p.id=r.ydental_native_payment_id
        LEFT JOIN account_journal j ON j.id=p.journal_id
        LEFT JOIN account_move m ON m.id=p.move_id ORDER BY r.id''')
    raw_refunds = cur.fetchall()
    assert [row[0] for row in raw_refunds] == ['cancelled', 'done', 'cancelled',
                                               'cancelled', 'done', 'done']
    assert [float(row[4] or 0) for row in raw_refunds] == [0, 25, 0, 0, 30, 40]
    assert all(row[7] != row[8] for row in raw_refunds)
    assert raw_refunds[4][9] == 6 and raw_refunds[4][3] == 'card'
    assert raw_refunds[5][9] == 5 and raw_refunds[5][3] == 'wechat'
    refunds = [dict(state=state, amount=float(amount), actual_day=str(day) if day else None,
                    channel=channel, native_amount=float(native or 0), journal=journal,
                    move_state=move, requester_different_approver=requester != approver,
                    executor_role='frontdesk' if executor == 6 else 'manager' if executor == 5 else None)
               for state, amount, day, channel, native, journal, move, requester, approver, executor in raw_refunds]
    cur.execute('''SELECT ydental_channel,ydental_state,ydental_business_date,
        ydental_gross,ydental_refunded,ydental_pending,ydental_cashier_id
        FROM ydental_settlement_close ORDER BY id''')
    closes = [dict(channel=channel, state=state, day=str(day), gross=float(gross),
                   refunded=float(refunded), pending=float(pending),
                   cashier_role='frontdesk' if cashier == 6 else 'manager')
              for channel, state, day, gross, refunded, pending, cashier in cur.fetchall()]
    assert [(x['channel'], x['state'], x['gross'], x['refunded'], x['pending']) for x in closes] == [
        ('card', 'confirmed', 100, 0, 0), ('card', 'confirmed', 0, 30, 0),
        ('cash', 'unlocked', 100, 0, 0), ('wechat', 'confirmed', 100, 0, 0),
        ('wechat', 'confirmed', 0, 40, 0)]
    assert closes[0]['day'] < closes[1]['day'] and closes[2]['day'] < closes[4]['day']
    cur.execute('''SELECT c.ydental_old_channel,c.ydental_new_channel,c.ydental_recorded_at,
        m.state,p.ydental_channel,p.ydental_actual_at
        FROM ydental_settlement_correction c
        JOIN account_move m ON m.id=c.ydental_move_id
        JOIN ydental_settlement_payment p ON p.id=c.ydental_payment_id''')
    correction = cur.fetchone()
    assert correction[0:2] == ('cash', 'wechat') and correction[3] == 'posted'
    assert correction[4] == 'cash' and correction[5].date() < correction[2].date()
    cur.execute('''SELECT r.ydental_actual_at,c.ydental_recorded_at
        FROM ydental_settlement_refund r JOIN ydental_settlement_correction c
        ON c.ydental_payment_id=r.ydental_payment_id
        WHERE r.ydental_refund_channel='wechat' ''')
    actual_after_correction = cur.fetchone()
    assert actual_after_correction and actual_after_correction[0] > actual_after_correction[1]
    cur.execute('''SELECT l.debit,l.credit,l.account_id FROM ydental_settlement_correction c
        JOIN account_move_line l ON l.move_id=c.ydental_move_id ORDER BY l.id''')
    adjustment_lines = [(float(debit), float(credit), account) for debit, credit, account in cur.fetchall()]
    assert len(adjustment_lines) == 2 and adjustment_lines[0][:2] == (100, 0)
    assert adjustment_lines[1][:2] == (0, 100) and adjustment_lines[0][2] != adjustment_lines[1][2]
    cur.execute("SELECT ydental_event,count(*) FROM ydental_access_audit WHERE ydental_event LIKE 'settlement.%' GROUP BY 1 ORDER BY 1")
    audit = dict(cur.fetchall())
    assert audit['settlement.refund.cancel'] == 3 and audit['settlement.refund.execute'] == 3
    assert audit['settlement.refund.unknown'] == audit['settlement.refund.failed'] == 1
    assert audit['settlement.refund.recover'] == 2 and audit['settlement.close'] == 5
    assert audit['settlement.reclassify'] == audit['settlement.unlock'] == 1
    cur.execute("SELECT count(distinct ydental_store_id) FROM ydental_access_audit WHERE ydental_event LIKE 'settlement.%'")
    assert cur.fetchone()[0] == 1
    cur.execute('''SELECT m.ydental_user_id,m.ydental_store_id,g.ydental_category,g.ydental_level
        FROM ydental_access_membership m JOIN ydental_access_grant g
        ON g.ydental_membership_id=m.id
        WHERE m.ydental_user_id IN (5,6,7)
        AND g.ydental_category IN ('settlement','finance_approval')
        ORDER BY 1,2,3''')
    rights = cur.fetchall()
    assert rights == [(5, 1, 'finance_approval', 'write'), (5, 1, 'settlement', 'write'),
                      (6, 1, 'finance_approval', 'write'), (6, 1, 'settlement', 'write'),
                      (7, 1, 'settlement', 'write')]
    cur.execute('SELECT DISTINCT company_id FROM account_move')
    assert cur.fetchall() == [(1,)]
    mail = one(cur, 'SELECT count(*) FROM mail_mail')
    bus = one(cur, 'SELECT count(*) FROM bus_bus')
    messages = one(cur, 'SELECT count(*) FROM mail_message')
    deadlocks = one(cur, 'SELECT deadlocks FROM pg_stat_database WHERE datname=current_database()')
    assert (mail, bus, messages, deadlocks) == (0, 30, 937, 0)
connection.rollback()
connection.close()

admin = psycopg2.connect(dbname='postgres', **endpoint)
admin.set_session(readonly=True)
with admin.cursor() as cur:
    cur.execute('SELECT datname,oid FROM pg_database WHERE datname=ANY(%s)', ([
        'ydental_s10_test_20261014020300_8b6c1d4e',
        'ydental_s10_test_20261014044700_4f6a8d2c',
        'ydental_odoo_c1_20261014132000_a84d2c91',
        'ydental_odoo_c1r1_20261014134200_6d3e9f20',
        'ydental_odoo_c1r2_20261014140600_7a19d24e',
        'ydental_s10_test_20261014145000_fc1a84d7', NAME],))
    oids = dict(cur.fetchall())
    assert oids == {
        'ydental_s10_test_20261014020300_8b6c1d4e': 2056451,
        'ydental_s10_test_20261014044700_4f6a8d2c': 2100080,
        'ydental_odoo_c1_20261014132000_a84d2c91': 2100125,
        'ydental_odoo_c1r1_20261014134200_6d3e9f20': 2100126,
        'ydental_odoo_c1r2_20261014140600_7a19d24e': 2100176,
        'ydental_s10_test_20261014145000_fc1a84d7': 2100197,
        NAME: 2100212,
    }
admin.rollback()
admin.close()

evidence = [json.loads(line) for line in (RUN / 'fc2-evidence.jsonl').read_text().splitlines()]
ledger = [json.loads(line) for line in (RUN / 'fc2-commit-ledger.jsonl').read_text().splitlines()]
commits = [row for row in ledger if row['status'] == 'COMMITTED']
assert len(commits) == 11 and [row['attempt'] for row in commits] == list(range(1, 12))
races = {}
for case in ('A', 'C'):
    overlap = next(row for row in evidence if row['case'] == case and row['stage'] == 'overlap')
    result = next(row for row in evidence if row['case'] == case and row['stage'] == 'race_result')
    assert overlap['first_backend'] != overlap['second_backend']
    assert overlap['second_waiting'] and result['second']['sqlstate'] == '40001'
    races[case] = {'first_backend': overlap['first_backend'],
                   'second_backend': overlap['second_backend'],
                   'second_start_utc': overlap['second_start_utc'],
                   'second_waiting_before_commit': True,
                   'first': result['first'], 'second': result['second']['status'],
                   'exception': result['second']['exception'], 'sqlstate': result['second']['sqlstate']}
phases = {}
for row in evidence:
    if row['stage'] == 'fresh_cursor_review':
        phases[row['case']] = {key: row['counts'][key] for key in (
            'mail.message', 'mail.mail', 'bus.bus', 'ydental.access.audit',
            'account.move', 'account.payment', 'account.partial.reconcile',
            'ydental.settlement.close')}
rejections = [dict(case=row['case'], reason=row['reason'], operation=row['operation'],
                   exception=row['exception'], code=row['code']) for row in evidence
              if row['stage'] == 'EXPECTED_REJECT']
intents = [dict(case=row['case'], types=row['kinds'], total=row['total']) for row in evidence
           if row['stage'] == 'precommit_bus_intents']
assert len(intents) == 11 and all(row['total'] == 0 for row in intents)
assert len(rejections) == 13

output = {
    'scope': 'S10-FC2 one synthetic Odoo shell; read-only SQL verification',
    'authorization_comment': 6171419484, 'checkpoint_comment': 6171566556,
    'start_head': '7ee2c5e091fa1d29bd01e493b07902d2827f4a35',
    'database': {'name': NAME, 'oid': marker['oid'], 'source_oid': marker['source_oid'],
                 'cluster': marker['cluster'], 'config_sha256': marker['config_sha256'],
                 'marker_sha256': sha(RUN / 'database.json'), 'modules': 92,
                 'warehouses': 2, 'old_oid_sentinels_unchanged': True},
    'run': {**json.loads((RUN / 'run-result.json').read_text()),
            'commit_count': len(commits), 'commit_purposes': [row['purpose'] for row in commits]},
    'concurrency': races, 'negative_actions': rejections,
    'finance': {'moves': moves, 'unbalanced_moves': 0, 'payments': payments,
                'partial_amounts': partials, 'refunds': refunds, 'closes': closes,
                'correction': {'from': correction[0], 'to': correction[1],
                               'recorded_utc': str(correction[2]), 'posted': True,
                               'original_inbound_label': correction[4],
                               'actual_refund_after_correction': True},
                'correction_lines': [{'debit': debit, 'credit': credit} for debit, credit, _account in adjustment_lines],
                'audit_events': audit, 'phase_counts': phases,
                'rights': {'manager': ['settlement:write', 'finance_approval:write'],
                           'frontdesk': ['settlement:write', 'finance_approval:write'],
                           'doctor': ['settlement:write'], 'one_store_and_one_company': True},
                'mail_message': messages, 'mail_mail': mail, 'bus_bus': bus,
                'observed_precommit_bus_intents': intents, 'deadlocks': deadlocks,
                'published_price': 100, 'snapshots': 3,
                'global_group_xmlids_enabled': ['product.group_product_pricelist',
                    'stock.group_stock_multi_locations', 'stock.group_stock_multi_warehouses']},
    'private_sha256': {'ledger': sha(RUN / 'fc2-commit-ledger.jsonl'),
                       'timeline': sha(RUN / 'fc2-evidence.jsonl'),
                       'odoo_log': sha(RUN / 'odoo-fc2.log')},
    'limits': {'reverse_40001_then_retry': 'only fresh-cursor legal close, no automatic retry',
               'bus_intent_scope': 'only checked precommit bus.bus.values slot at 11 COMMIT points',
               'external_offline_transfer': 'synthetic proof only, no bank or WeChat API',
               'full_S10_T01_T16': 'NOT_RUN'},
}
target = ROOT / 'docs/evidence/s10-fc2/verification.json'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': 'READ_ONLY_PASS', 'evidence': str(target),
                  'commits': len(commits), 'races': len(races), 'rejections': len(rejections)}))
