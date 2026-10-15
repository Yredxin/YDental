"""Read-only post-STOP audit of the single W3 attempt; write sanitized evidence."""

from decimal import Decimal
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import sys

import psycopg2
from psycopg2 import sql

from s10_e2e_w3_control import NAME, PORT, ROOT, RUN, SOURCE, endpoint

OUT = ROOT / 'docs/evidence/s10-e2e-w3/verification.json'
TABLES = {
    'ydental_treatment_event': ('id','ydental_kind','state','ydental_patient_id','ydental_store_id',
        'ydental_actor_id','ydental_execution_id','ydental_order_line_id','ydental_price_snapshot_id',
        'ydental_quantity','ydental_business_date'),
    'ydental_treatment_fee': ('id','ydental_event_id','ydental_patient_id','ydental_price_snapshot_id',
        'ydental_unit_price','ydental_amount'),
    'ydental_intake_snapshot': ('id','ydental_price_id','ydental_unit_price','ydental_quantity','ydental_amount'),
    'ydental_exam_result': ('id','ydental_line_id','ydental_event_id','state','ydental_version'),
    'ydental_treatment_order': ('id','ydental_kind','state','ydental_version','ydental_patient_id','ydental_store_id'),
    'ydental_treatment_segment': ('id','ydental_order_id','ydental_task_id','ydental_sequence','state','ydental_execution_id'),
    'ydental_intake_task': ('id','ydental_patient_id','ydental_store_id','ydental_mapping_id',
        'ydental_parent_task_id','ydental_source_kind','state'),
    'ydental_queue_execution': ('id','ydental_category','ydental_task_id','state'),
    'ydental_queue_lease': ('id','ydental_active','ydental_release_reason'),
    'ydental_settlement_source': ('id','ydental_fee_id','ydental_invoice_id','ydental_line_id',
        'ydental_original_amount','ydental_patient_id'),
    'ydental_settlement_receipt': ('id','ydental_operation','ydental_result'),
    'ydental_settlement_payment': ('id','ydental_payment_id','ydental_amount','ydental_channel'),
    'account_payment': ('id','state','amount','move_id'),
    'account_partial_reconcile': ('id','amount','debit_move_id','credit_move_id'),
}
ECONOMIC_TABLES = ('ydental_treatment_event','ydental_treatment_fee','ydental_inventory_event',
    'stock_move','ydental_settlement_source','ydental_settlement_receipt','ydental_settlement_payment',
    'account_move','account_payment','account_partial_reconcile')
PRIVATE_FILES = ('database.json','odoo.conf','fixture.json','odoo-prepare.log','odoo-http.log',
    'browser.log','browser-actions.jsonl','browser-events.jsonl','browser-attempt.json',
    'browser-launch.json.result','prepare-attempt.json.result','http.result.json')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def connect(database):
    connection = psycopg2.connect(dbname=database, **endpoint())
    connection.set_session(readonly=True)
    with connection.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        assert cursor.fetchone()[0] == 'on'
    return connection


def records(cursor, table, columns):
    query = sql.SQL('SELECT {} FROM {} ORDER BY id').format(
        sql.SQL(',').join(map(sql.Identifier, columns)), sql.Identifier(table))
    cursor.execute(query)
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def main():
    fixture = json.loads((RUN / 'fixture.json').read_text())
    assert fixture['database'] == NAME and fixture['oid'] == 2100285
    target = connect(NAME)
    with target.cursor() as cursor:
        business = {table: records(cursor, table, columns) for table, columns in TABLES.items()}
        cursor.execute('SELECT i.id, i.ydental_lot_id, i.ydental_quantity, i.ydental_move_id, '
            'i.state, c.ydental_event_id, m.state, m.quantity FROM ydental_inventory_event i '
            'LEFT JOIN ydental_treatment_consumption c ON c.ydental_inventory_event_id=i.id '
            'LEFT JOIN stock_move m ON m.id=i.ydental_move_id ORDER BY i.id')
        business['inventory'] = [dict(zip(('id','lot','quantity','move','state','event',
            'native_state','native_quantity'), row)) for row in cursor.fetchall()]
        cursor.execute("SELECT id,state,move_type,amount_total,amount_residual,company_id "
            "FROM account_move WHERE move_type='out_invoice' ORDER BY id")
        business['invoices'] = [dict(zip(('id','state','move_type','total','residual','company'), row))
            for row in cursor.fetchall()]
        cursor.execute("SELECT ydental_event,ydental_result,count(*) FROM ydental_access_audit "
            "WHERE ydental_event IN ('treatment.actual_execution','treatment.actual_dispense',"
            "'treatment.order_issued','treatment.pharmacy_segment_finished','exam.actual_performed',"
            "'exam.confirm','settlement.bill','settlement.pay','inventory.movement') "
            "GROUP BY ydental_event,ydental_result ORDER BY ydental_event")
        business['audit_economic'] = [dict(zip(('event','result','count'), row)) for row in cursor.fetchall()]
        cursor.execute("SELECT arch_db FROM ir_ui_view WHERE key='ydental_settlement.ydental_settlement_tokens'")
        installed_arch = cursor.fetchone()[0]['en_US']
        cursor.execute('SELECT count(*) FROM mail_mail')
        business['mail_mail'] = cursor.fetchone()[0]
    target.close()
    source = connect(SOURCE)
    with source.cursor() as cursor:
        source_counts = {}
        for table in ECONOMIC_TABLES:
            cursor.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(table)))
            source_counts[table] = cursor.fetchone()[0]
        cursor.execute("SELECT arch_db FROM ir_ui_view WHERE key='ydental_settlement.ydental_settlement_tokens'")
        source_arch = cursor.fetchone()[0]['en_US']
    source.close()
    postgres = connect('postgres')
    with postgres.cursor() as cursor:
        cursor.execute('SELECT datname,oid FROM pg_database WHERE datname IN (%s,%s) ORDER BY datname', [SOURCE, NAME])
        database_oids = cursor.fetchall()
        cursor.execute('SELECT datname,count(*) FROM pg_stat_activity WHERE datname IN (%s,%s) GROUP BY datname', [SOURCE, NAME])
        active = cursor.fetchall()
    postgres.close()
    actions_path = RUN / 'browser-actions.jsonl'
    steps_path = RUN / 'browser-events.jsonl'
    actions = [json.loads(line) for line in actions_path.read_text().splitlines()]
    steps = [json.loads(line) for line in steps_path.read_text().splitlines()]
    screens = [{'file': str(path.relative_to(RUN)), 'sha256': digest(path), 'bytes': path.stat().st_size}
        for path in sorted((RUN / 'screenshots').glob('*.png'))]
    private = {name: {'sha256': digest(RUN / name), 'bytes': (RUN / name).stat().st_size}
        for name in PRIVATE_FILES if (RUN / name).is_file()}
    current_qweb = ROOT / 'ydental_settlement/views/ydental_settlement_templates.xml'
    assert 'name="output" value="html"' in current_qweb.read_text()
    assert 'name="output" value="html"' not in installed_arch and source_arch == installed_arch
    assert len(actions) == 34 and len(steps) == len(screens) == 20
    assert [row['name'] for row in steps][-1] == 'finish_final'
    assert [Decimal(str(row['ydental_amount'])) for row in business['ydental_treatment_fee']] == [600,80,40,20]
    assert [row['native_state'] for row in business['inventory']] == ['done'] * 5
    assert len(business['ydental_settlement_source']) == 4
    assert len(business['invoices']) == len(business['ydental_settlement_receipt']) == 1
    invoice = business['invoices'][0]
    assert invoice['state'] == 'posted' and Decimal(str(invoice['total'])) == Decimal('740')
    assert Decimal(str(invoice['residual'])) == Decimal('740')
    assert business['account_payment'] == business['ydental_settlement_payment'] == business['account_partial_reconcile'] == []
    assert all(value == 0 for value in source_counts.values()) and active == []
    result = {
        'status': 'BLOCKED_AFTER_WEB_BILL_COMMIT', 'authorization_comment': 6185309077,
        'preflight_comment': 6185552492, 'base_head': 'a17cf61fadd983aa83ed53c791e79713b83f0b58',
        'source': {'database': SOURCE, 'oid': 2100080, 'economic_counts': source_counts,
            'settlement_tokens_arch_sha256': hashlib.sha256(source_arch.encode()).hexdigest(),
            'contains_output_html': False},
        'target': {'database': NAME, 'oid': fixture['oid'], 'port': PORT,
            'database_oids': database_oids, 'active_connections_after_http_stop': active,
            'patient_id': fixture['patient'], 'store_id': fixture['store'], 'company_id': fixture['company']},
        'resources': {'create': 1, 'prepare_shell': 1, 'http': 1, 'firefox_playwright': 1,
            'module_install_upgrade': 0,
            'prepare_result': json.loads((RUN / 'prepare-attempt.json.result').read_text()),
            'http_result': json.loads((RUN / 'http.result.json').read_text()),
            'browser_result': json.loads((RUN / 'browser-launch.json.result').read_text())},
        'browser': {'completed_steps': [row['name'] for row in steps], 'logged_posts': len(actions),
            'last_logged_post': {'step': actions[-1]['step'], 'url': actions[-1]['response']['url'],
                'http_status': actions[-1]['response']['http_status']},
            'private_screenshots': [{'file': x['file'], 'sha256': x['sha256']} for x in screens],
            'bill_post_http_status_from_server_log': 200,
            'bill_harness_assertion': 'settlement_http_class expected 303, got 200',
            'bill_step_event_logged': False, 'pay_steps_run': False},
        'business': business,
        'qweb_drift': {'tracked_qweb_sha256': digest(current_qweb),
            'tracked_contains_output_html': True,
            'installed_token_arch_sha256': hashlib.sha256(installed_arch.encode()).hexdigest(),
            'installed_contains_output_html': False,
            'controller_sha256': digest(ROOT / 'ydental_settlement/controllers/settlement.py'),
            'controller_html_branch_requires_output_html': True},
        'private_files': private,
        'screenshots': {'count': len(screens),
            'aggregate_sha256': hashlib.sha256(('\n'.join(x['sha256'] for x in screens) + '\n').encode()).hexdigest()},
    }
    def encode(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, (date, datetime)):
            return value.isoformat()
        raise TypeError(type(value).__name__)
    assert not OUT.exists()
    OUT.write_text(json.dumps(result, default=encode, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'oid': fixture['oid'], 'steps': len(steps),
        'posts': len(actions), 'invoice_total': str(invoice['total']), 'payments': 0,
        'verification_sha256': digest(OUT)}))


if __name__ == '__main__':
    main()
