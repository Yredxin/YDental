"""Read-only W4 source, W5 clone and native payment invariants."""

import configparser
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261015064000_d41e7b62'
SOURCE_OID = 2100301
NAME = 'ydental_s10_test_20261015073500_e50f4a71'
PORT = 18280
BASE = '79417da9043478501ffae586f93eebc1e5d7105d'
CORE_HEAD = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
CLUSTER = '7694897083368259627'
SOURCE_CONFIG_SHA = '464f29204afd03c63d1450db442f4d42454e1d164243ca6bb1dbe8eb787b10ba'
SOURCE_MARKER_SHA = '82aaa9c49144987eaa2bf08268db145b62bb55f3ebd5fb373d94dfbd4e101b4a'
RUN = ROOT / '.local' / NAME
SOURCE_RUN = ROOT / '.local' / SOURCE
EXPECTED_TOKEN_SHA = 'f454d4e36da804a2ff87a7519c680d59c33ff38e92e40ef296e2be6e1e49db3d'
AUTH = 6186596167
PREFLIGHT_COMMENT = None  # Replaced by immutable private checkpoint file before CREATE.

# Strict full-row comparison across the clone. Payment changes only the
# explicitly excluded native finance and audit tables after the first POST.
EXACT_TABLES = (
    'ydental_access_store', 'ydental_access_membership', 'ydental_access_grant',
    'ydental_access_audit', 'ydental_patient', 'ydental_patient_relation',
    'ydental_intake_price', 'ydental_intake_snapshot', 'ydental_intake_task',
    'ydental_queue_entry', 'ydental_queue_execution', 'ydental_queue_lease',
    'ydental_clinical_document', 'ydental_clinical_version',
    'ydental_treatment_order', 'ydental_treatment_line', 'ydental_treatment_segment',
    'ydental_treatment_event', 'ydental_treatment_fee', 'ydental_treatment_consumption',
    'ydental_exam_result', 'ydental_exam_version', 'ydental_inventory_event',
    'ydental_inventory_batch', 'stock_move', 'stock_move_line',
    'account_move', 'account_move_line', 'account_payment', 'account_partial_reconcile',
    'ydental_settlement_source', 'ydental_settlement_receipt',
    'ydental_settlement_payment', 'ydental_settlement_refund', 'ydental_settlement_close',
    'ydental_settlement_config', 'account_account', 'account_journal',
)
STABLE_AFTER_PAYMENT = tuple(table for table in EXACT_TABLES if table not in (
    'ydental_access_audit', 'account_move', 'account_move_line', 'account_payment',
    'account_partial_reconcile', 'ydental_settlement_receipt', 'ydental_settlement_payment'))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def endpoint():
    config = configparser.ConfigParser(interpolation=None)
    assert config.read(CORE / 'odoo.conf')
    options = config['options']
    assert (options['db_host'], options['db_port'], options['db_user']) == ('127.0.0.1', '5432', 'odoo')
    return {'host': '127.0.0.1', 'port': 5432, 'user': 'odoo',
            'password': options['db_password'], 'connect_timeout': 5}


def connect(database):
    connection = psycopg2.connect(dbname=database, **endpoint())
    connection.set_session(readonly=True)
    with connection.cursor() as cursor:
        cursor.execute('SHOW transaction_read_only')
        assert cursor.fetchone()[0] == 'on'
    return connection


def database_identity():
    connection = connect('postgres')
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT system_identifier::text FROM pg_control_system()')
            assert cursor.fetchone()[0] == CLUSTER
            cursor.execute('SELECT datname,oid FROM pg_database WHERE datname IN (%s,%s)', (SOURCE, NAME))
            rows = dict(cursor.fetchall())
            assert rows.get(SOURCE) == SOURCE_OID
            cursor.execute('SELECT datname,pid,state FROM pg_stat_activity WHERE datname IN (%s,%s)', (SOURCE, NAME))
            activity = cursor.fetchall()
            return rows, activity
    finally:
        connection.close()


def filestore(database, connection):
    folder = (SOURCE_RUN if database == SOURCE else RUN) / 'data/filestore' / database
    assert folder.is_dir() and not folder.is_symlink()
    files = {}
    for path in folder.rglob('*'):
        assert not path.is_symlink(), path
        if path.is_file():
            files[str(path.relative_to(folder))] = digest(path)
    assert files
    with connection.cursor() as cursor:
        cursor.execute('SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
        pointers = cursor.fetchall()
    for relative, checksum in pointers:
        assert relative in files
        assert hashlib.sha1((folder / relative).read_bytes()).hexdigest() == checksum
    manifest = '\n'.join(f'{name}\t{value}' for name, value in sorted(files.items())) + '\n'
    return {'file_count': len(files), 'pointer_count': len(pointers),
            'manifest_sha256': hashlib.sha256(manifest.encode()).hexdigest(), 'files': files,
            'attachment_pointers_sha256': hashlib.sha256(json.dumps(pointers).encode()).hexdigest()}


def full_rows(cursor, table):
    cursor.execute(sql.SQL('SELECT to_jsonb(t)::text FROM {} t ORDER BY id').format(sql.Identifier(table)))
    return [row[0] for row in cursor.fetchall()]


def exact_signature(connection, tables=EXACT_TABLES):
    with connection.cursor() as cursor:
        result = {}
        for table in tables:
            rows = full_rows(cursor, table)
            data = ('\n'.join(rows) + '\n').encode()
            result[table] = {'rows': len(rows), 'sha256': hashlib.sha256(data).hexdigest()}
        return result


def views(connection):
    with connection.cursor() as cursor:
        cursor.execute("SELECT key,arch_db FROM ir_ui_view WHERE key IN "
                       "('ydental_settlement.ydental_settlement_tokens',"
                       "'ydental_settlement.ydental_settlement_page') ORDER BY key")
        rows = cursor.fetchall()
    assert len(rows) == 2
    result = {}
    for key, translations in rows:
        assert isinstance(translations, dict) and 'en_US' in translations
        result[key] = {language: {'sha256': hashlib.sha256(arch.encode()).hexdigest(),
                                  'has_output_html': 'name="output" value="html"' in arch}
                       for language, arch in translations.items()}
    return result


def money(connection):
    with connection.cursor() as cursor:
        cursor.execute('SELECT ydental_store_id,company_id,ydental_cash_journal_id '
                       'FROM ydental_settlement_config ORDER BY id')
        cash_configs = [dict(zip(('store','company','journal'), row)) for row in cursor.fetchall()]
        cursor.execute("SELECT id,move_type,state,amount_total,amount_residual,payment_state,"
                       "company_id,journal_id FROM account_move WHERE move_type='out_invoice' ORDER BY id")
        invoices = [dict(zip(('id','type','state','total','residual','payment_state','company','journal'), row))
                    for row in cursor.fetchall()]
        cursor.execute('SELECT id,move_type,state,amount_total,company_id,journal_id '
                       'FROM account_move ORDER BY id')
        native_moves = [dict(zip(('id','type','state','total','company','journal'), row))
                        for row in cursor.fetchall()]
        cursor.execute('SELECT id,ydental_fee_id,ydental_invoice_id,ydental_line_id,ydental_original_amount '
                       'FROM ydental_settlement_source ORDER BY id')
        sources = [dict(zip(('id','fee','invoice','line','amount'), row)) for row in cursor.fetchall()]
        cursor.execute('SELECT id,ydental_operation,ydental_result FROM ydental_settlement_receipt ORDER BY id')
        receipts = [dict(zip(('id','operation','result'), row)) for row in cursor.fetchall()]
        cursor.execute('SELECT p.id,p.state,p.payment_type,p.partner_type,p.amount,p.company_id,'
                       'p.journal_id,p.move_id,m.state FROM account_payment p '
                       'LEFT JOIN account_move m ON m.id=p.move_id ORDER BY p.id')
        payments = [dict(zip(('id','state','payment_type','partner_type','amount','company','journal','move','move_state'), row))
                    for row in cursor.fetchall()]
        cursor.execute('SELECT id,amount,debit_move_id,credit_move_id,company_id '
                       'FROM account_partial_reconcile ORDER BY id')
        partials = [dict(zip(('id','amount','debit','credit','company'), row)) for row in cursor.fetchall()]
        cursor.execute('SELECT id,ydental_payment_id,ydental_amount,ydental_channel,ydental_store_id,ydental_patient_id '
                       'FROM ydental_settlement_payment ORDER BY id')
        settlement_payments = [dict(zip(('id','payment','amount','channel','store','patient'), row))
                               for row in cursor.fetchall()]
        cursor.execute('SELECT settlement_payment_id,invoice_id FROM ydental_settlement_payment_invoice_rel '
                       'ORDER BY settlement_payment_id,invoice_id')
        payment_invoices = [dict(zip(('settlement_payment','invoice'), row)) for row in cursor.fetchall()]
        cursor.execute("SELECT id,move_id,account_id,debit,credit,amount_residual "
                       "FROM account_move_line WHERE move_id IN "
                       "(SELECT id FROM account_move WHERE move_type='out_invoice') ORDER BY id")
        invoice_lines = [dict(zip(('id','move','account','debit','credit','residual'), row))
                         for row in cursor.fetchall()]
        cursor.execute('SELECT l.id,l.move_id,l.account_id,l.debit,l.credit,l.balance '
                       'FROM account_move_line l JOIN account_payment p ON p.move_id=l.move_id ORDER BY l.id')
        payment_lines = [dict(zip(('id','move','account','debit','credit','balance'), row))
                         for row in cursor.fetchall()]
        cursor.execute("SELECT id,ydental_event,ydental_result,ydental_user_id,ydental_store_id "
                       "FROM ydental_access_audit WHERE ydental_event IN "
                       "('settlement.pay','settlement.bill','settlement.invoice_view','login.scope') ORDER BY id")
        audits = [dict(zip(('id','event','result','user','store'), row)) for row in cursor.fetchall()]
    return {'cash_configs': cash_configs, 'invoices': invoices, 'native_moves': native_moves,
        'sources': sources, 'receipts': receipts,
            'payments': payments, 'partials': partials, 'settlement_payments': settlement_payments,
            'invoice_lines': invoice_lines, 'payment_invoices': payment_invoices,
            'payment_lines': payment_lines, 'audits': audits}


def assert_w4_economic(connection):
    with connection.cursor() as cursor:
        cursor.execute('SELECT id,ydental_amount,ydental_price_snapshot_id FROM ydental_treatment_fee ORDER BY id')
        assert cursor.fetchall() == [(1, Decimal('600'), 1), (2, Decimal('80'), 2),
                                     (3, Decimal('40'), 3), (4, Decimal('20'), 4)]
    values = money(connection)
    assert len(values['invoices']) == 1
    invoice = values['invoices'][0]
    assert invoice['id'] == 1 and invoice['type'] == 'out_invoice' and invoice['state'] == 'posted'
    assert invoice['total'] == invoice['residual'] == Decimal('740')
    assert [row['amount'] for row in values['sources']] == [Decimal('20'), Decimal('40'), Decimal('80'), Decimal('600')]
    assert len(values['receipts']) == 1 and values['receipts'][0]['operation'] == 'bill'
    assert not values['payments'] and not values['partials'] and not values['settlement_payments']
    with connection.cursor() as cursor:
        cursor.execute('SELECT id,state FROM ydental_treatment_event ORDER BY id')
        assert cursor.fetchall() == [(i, 'confirmed') for i in range(1, 5)]
        cursor.execute('SELECT id,state,quantity FROM stock_move ORDER BY id')
        stock = cursor.fetchall()
        assert len(stock) == 5 and all(state == 'done' for _, state, _ in stock)
        assert [qty for _, _, qty in stock[2:]] == [Decimal('1'), Decimal('4'), Decimal('2')]
        cursor.execute('SELECT id,state FROM ydental_exam_result ORDER BY id')
        assert cursor.fetchall() == [(1, 'confirmed')]
        cursor.execute("SELECT count(*) FROM ydental_access_grant g JOIN ydental_access_membership m "
                       "ON m.id=g.ydental_membership_id WHERE m.ydental_user_id=5 "
                       "AND m.ydental_store_id=1 AND g.ydental_category='settlement' "
                       "AND g.ydental_level='write' AND m.active")
        assert cursor.fetchone()[0] == 1
    return values


def source_audit():
    assert digest(SOURCE_RUN / 'database.json') == SOURCE_MARKER_SHA
    assert digest(SOURCE_RUN / 'odoo.conf') == SOURCE_CONFIG_SHA
    rows, activity = database_identity()
    assert NAME not in rows and activity == []
    connection = connect(SOURCE)
    try:
        assert_w4_economic(connection)
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM ir_module_module WHERE state='installed' ORDER BY name")
            modules = [row[0] for row in cursor.fetchall()]
            assert len(modules) == 92 and 'ydental_settlement' in modules
        installed = views(connection)
        token = installed['ydental_settlement.ydental_settlement_tokens']['en_US']
        assert token['sha256'] == EXPECTED_TOKEN_SHA and token['has_output_html'] is True
        assert all(language['has_output_html'] for language in installed['ydental_settlement.ydental_settlement_tokens'].values())
        storage = filestore(SOURCE, connection)
        return {'source_oid': SOURCE_OID, 'module_count': len(modules),
                'modules_sha256': hashlib.sha256(('\n'.join(modules) + '\n').encode()).hexdigest(),
                'view': installed, 'filestore': {key: value for key, value in storage.items() if key != 'files'},
                'exact': exact_signature(connection), 'money': money(connection)}
    finally:
        connection.close()


def state(database):
    connection = connect(database)
    try:
        assert_w4_economic(connection) if database == SOURCE else None
        with connection.cursor() as cursor:
            cursor.execute("SELECT name,state,latest_version,write_date FROM ir_module_module ORDER BY name")
            module_meta = {name: {'state': status, 'version': version,
                'write_date': stamp.isoformat() if stamp else None}
                for name, status, version, stamp in cursor.fetchall()}
            modules = sorted(name for name, details in module_meta.items()
                             if details['state'] == 'installed')
        storage = filestore(database, connection)
        return {'database': database, 'exact': exact_signature(connection),
                'money': money(connection), 'views': views(connection),
                'modules': modules, 'module_meta': module_meta, 'filestore': storage}
    finally:
        connection.close()


def simple(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, default=simple, ensure_ascii=False, sort_keys=True)
