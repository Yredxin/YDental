"""Read-only, full-row P0-08 and historical database snapshots. No Odoo registry."""

import configparser
import hashlib
import json
from pathlib import Path

import psycopg2
from psycopg2 import sql

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT.parent
SOURCE = 'ydental_s10_test_20261016_p007_7c92b4a6'
SOURCE_OID = 2100322
CLUSTER = '7694897083368259627'
SOURCE_CONFIG = '9ab06779590e31bd372e6880cc406ffd6fe08ed78b41f1786700530fb7bb3db7'
SOURCE_MARKER = '065e25e24b5786a60963330943f1b4db2c8a983101e0ab5fab9d3bf4e81522d8'
SOURCE_MANIFEST = '27174fa6aa277611a62f4feaf8deb65701d5bbd0d38f91b7966a9b90f0901372'
TOKEN_OLD = 'f454d4e36da804a2ff87a7519c680d59c33ff38e92e40ef296e2be6e1e49db3d'
SOURCE_RUN = ROOT / '.local' / SOURCE
TARGET = 'ydental_s10_test_20261016_p008_8d43a1e5'
TARGET_RUN = ROOT / '.local' / TARGET
PORT = 18291
HEAD = '4f40f11f51ca4f73070c117b88770e31d1354e9c'
CORE_HEAD = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
ALLOWED_VIEWS = frozenset({
    'ydental_settlement.ydental_queue_page',
    'ydental_settlement.ydental_settlement_page',
    'ydental_settlement.ydental_settlement_page_links',
    'ydental_settlement.ydental_settlement_pdf',
    'ydental_settlement.ydental_settlement_tokens',
})
PREFIXES = ('ydental_', 'account_', 'stock_')
EXTRA_TABLES = frozenset({
    'ir_module_module', 'ir_model_data', 'ir_ui_view', 'ir_attachment',
    'ir_model', 'ir_model_fields', 'ir_model_access', 'ir_rule',
    'res_users', 'res_groups', 'res_partner', 'res_company',
    'product_product', 'product_template', 'product_pricelist',
    'product_pricelist_item', 'mail_message', 'mail_followers',
})
# View/metadata are compared field by field; audit and session may grow in Web.
UPGRADE_EXCEPTIONS = frozenset({'ir_module_module', 'ir_ui_view'})
MONEY_TABLES = frozenset({'account_move', 'account_move_line', 'account_payment',
    'account_partial_reconcile', 'account_full_reconcile',
    'ydental_settlement_payment',
    'ydental_settlement_source', 'ydental_settlement_correction',
    'ydental_settlement_trade', 'stock_move', 'stock_move_line', 'stock_quant',
    'ydental_inventory_event', 'ydental_treatment_fee'})


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def credentials():
    conf = configparser.ConfigParser(interpolation=None)
    assert conf.read(SOURCE_RUN / 'odoo.conf')
    opts = conf['options']
    assert (opts['db_host'], opts['db_port'], opts['db_user']) == ('127.0.0.1', '5432', 'odoo')
    return {'host': '127.0.0.1', 'port': 5432, 'user': 'odoo',
            'password': opts['db_password'], 'connect_timeout': 5}


class ReadOnlyConnection(psycopg2.extensions.connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def connect(name):
    conn = psycopg2.connect(dbname=name, connection_factory=ReadOnlyConnection, **credentials())
    conn.set_session(readonly=True, isolation_level="REPEATABLE READ")
    with conn.cursor() as cur:
        cur.execute('SHOW transaction_read_only')
        assert cur.fetchone()[0] == 'on'
    return conn


def identity():
    with connect('postgres') as conn, conn.cursor() as cur:
        cur.execute('SELECT system_identifier::text FROM pg_control_system()')
        assert cur.fetchone()[0] == CLUSTER
        cur.execute('SELECT datname,oid FROM pg_database WHERE datname IN (%s,%s)', (SOURCE, TARGET))
        rows = dict(cur.fetchall())
        assert rows.get(SOURCE) == SOURCE_OID
        cur.execute('SELECT datname,pid,state FROM pg_stat_activity WHERE datname IN (%s,%s)',
                    (SOURCE, TARGET))
        active = cur.fetchall()
        return rows, active


def table_inventory(cur):
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' "
                "AND table_type='BASE TABLE' ORDER BY table_name")
    return [name for (name,) in cur.fetchall() if name.startswith(PREFIXES) or name in EXTRA_TABLES]


def schema(cur, tables):
    cur.execute("SELECT table_name,column_name,ordinal_position,data_type,udt_name,is_nullable,"
                "column_default FROM information_schema.columns WHERE table_schema='public' "
                "AND table_name=ANY(%s) ORDER BY table_name,ordinal_position", (tables,))
    columns = cur.fetchall()
    cur.execute("SELECT c.relname,con.conname,pg_get_constraintdef(con.oid) "
                "FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND c.relname=ANY(%s) ORDER BY 1,2", (tables,))
    constraints = cur.fetchall()
    cur.execute("SELECT tablename,indexname,indexdef FROM pg_indexes WHERE schemaname='public' "
                "AND tablename=ANY(%s) ORDER BY tablename,indexname", (tables,))
    indexes = cur.fetchall()
    data = json.dumps({'columns':columns,'constraints':constraints,'indexes':indexes},
                      default=str,ensure_ascii=False,separators=(',', ':')).encode()
    return {'columns':len(columns),'constraints':len(constraints),'indexes':len(indexes),
            'sha256':sha(data)}


def full_rows(cur, name, exclude_id=None):
    # JSONB canonicalizes field order. Sorting the row text handles relation tables without id.
    statement = sql.SQL('SELECT to_jsonb(t)::text FROM {} t').format(sql.Identifier(name))
    if exclude_id is not None:
        statement += sql.SQL(' WHERE id <> %s')
    statement += sql.SQL(' ORDER BY to_jsonb(t)::text')
    cur.execute(statement, (exclude_id,) if exclude_id is not None else ())
    digest = hashlib.sha256()
    count = 0
    for (row,) in cur:
        digest.update(row.encode() + b'\n')
        count += 1
    return {'rows': count, 'sha256': digest.hexdigest()}


def manifest(run, name):
    folder = run / 'data' / 'filestore' / name
    assert folder.is_dir() and not folder.is_symlink()
    files = {}
    for path in folder.rglob('*'):
        assert not path.is_symlink(), path
        if path.is_file():
            files[str(path.relative_to(folder))] = file_sha(path)
    old_style = sha(b''.join((key + ' ' + files[key] + '\n').encode() for key in sorted(files)))
    return {'files': files, 'count': len(files), 'sha256': old_style}


def source_business(cur):
    cur.execute('SELECT count(*) FROM ydental_settlement_refund r JOIN ydental_settlement_payment p '
                'ON p.id=r.ydental_payment_id WHERE p.ydental_store_id=1')
    refunds_count = cur.fetchone()[0]
    cur.execute('SELECT id FROM ydental_settlement_refund WHERE ydental_payment_id IN '
                '(SELECT id FROM ydental_settlement_payment WHERE ydental_store_id=1) '
                'ORDER BY id DESC OFFSET 50 LIMIT 50')
    refunds_page = [row[0] for row in cur.fetchall()]
    cur.execute('SELECT count(*) FROM ydental_settlement_close WHERE ydental_store_id=1')
    closes_count = cur.fetchone()[0]
    cur.execute('SELECT id FROM ydental_settlement_close WHERE ydental_store_id=1 '
                'ORDER BY id DESC OFFSET 50 LIMIT 50')
    closes_page = [row[0] for row in cur.fetchall()]
    cur.execute('SELECT r.ydental_state,r.ydental_requester_id,p.ydental_store_id,'
                'r.ydental_amount,r.ydental_native_payment_id,r.ydental_credit_note_id '
                'FROM ydental_settlement_refund r JOIN ydental_settlement_payment p '
                'ON p.id=r.ydental_payment_id WHERE r.id=14')
    refund = cur.fetchone()
    cur.execute('SELECT ydental_state,ydental_store_id,ydental_cashier_id,ydental_business_date,'
                'ydental_channel,ydental_cycle,ydental_gross,ydental_refunded,ydental_pending '
                'FROM ydental_settlement_close WHERE id=9')
    close = cur.fetchone()
    cur.execute('SELECT id FROM ydental_settlement_close WHERE ydental_store_id=1 '
                'AND ydental_cashier_id=%s AND ydental_business_date=%s AND ydental_channel=%s '
                'ORDER BY ydental_cycle DESC LIMIT 1', (close[2], close[3], close[4]))
    latest = cur.fetchone()[0]
    cur.execute("SELECT m.ydental_user_id,m.ydental_store_id,g.ydental_category,g.ydental_level "
                "FROM ydental_access_grant g JOIN ydental_access_membership m "
                "ON m.id=g.ydental_membership_id WHERE m.active AND "
                "m.ydental_user_id IN (5,6,10,14) AND "
                "g.ydental_category IN ('settlement','finance_approval') ORDER BY 1,2,3")
    grants = cur.fetchall()
    assert refunds_count == 63 and closes_count == 55
    assert 14 in refunds_page and 9 in closes_page
    assert refund[:3] == ('rejected', 5, 1) and str(refund[3]) == '1.00'
    assert refund[4:] == (None, None)
    assert close[0] in ('confirmed','unlocked') and close[1] == 1 and latest == 9
    assert (6,1,'settlement','write') in grants
    assert (6,1,'finance_approval','write') in grants
    assert not any(row[0] == 10 and row[1] == 1 for row in grants)
    return {'refunds_count': refunds_count, 'closes_count': closes_count,
        'refund_page2_ids': refunds_page, 'close_page2_ids': closes_page,
        'refund14': [str(x) if x is not None else None for x in refund],
        'close9': [str(x) if x is not None else None for x in close],
        'close9_latest': latest, 'grants': grants}


def snapshot(name, *, business=False):
    run = ROOT / '.local' / name
    storage = manifest(run, name)
    with connect(name) as conn, conn.cursor() as cur:
        cur.execute('SELECT (SELECT oid FROM pg_database WHERE datname=current_database()),'
                    '(SELECT system_identifier::text FROM pg_control_system())')
        oid, cluster = cur.fetchone()
        assert cluster == CLUSTER and (name != SOURCE or oid == SOURCE_OID)
        tables = table_inventory(cur)
        signatures = {table: full_rows(cur, table) for table in tables}
        protected_other_rows = {
            'ydental_settlement_refund_excluding_14':full_rows(cur,'ydental_settlement_refund',14),
            'ydental_settlement_close_excluding_9':full_rows(cur,'ydental_settlement_close',9)}
        shape = schema(cur, tables)
        cur.execute('SELECT to_jsonb(m)::text FROM ir_module_module m ORDER BY name')
        modules = {json.loads(row)['name']: json.loads(row) for (row,) in cur.fetchall()}
        cur.execute('SELECT key,arch_db,to_jsonb(v)::text FROM ir_ui_view v '
                    'WHERE key IS NOT NULL ORDER BY key')
        views = {key: {'row': json.loads(row), 'arch': arch,
            'languages': {lang: {'sha256': sha(value.encode()),
                'has_output_html': 'name="output" value="html"' in value}
                for lang, value in arch.items()}}
            for key, arch, row in cur.fetchall()}
        cur.execute('SELECT id,to_jsonb(v)::text FROM ir_ui_view v ORDER BY id')
        view_rows = {str(ident):json.loads(row) for ident,row in cur.fetchall()}
        cur.execute('SELECT store_fname,checksum FROM ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
        pointers = cur.fetchall()
        for filename, checksum in pointers:
            assert filename in storage['files']
            assert hashlib.sha1((run / 'data/filestore' / name / filename).read_bytes()).hexdigest() == checksum
        facts = source_business(cur) if business else None
    return {'database': name, 'oid': oid, 'cluster': cluster, 'tables': signatures,
        'schema': shape, 'modules': modules, 'views': views, 'view_rows': view_rows,
        'protected_other_rows':protected_other_rows,
        'filestore': storage, 'attachment_pointers': len(pointers),
        'business': facts}


def public(snapshot):
    return {'database': snapshot['database'], 'oid': snapshot['oid'],
        'table_count': len(snapshot['tables']), 'schema': snapshot['schema'],
        'tables': snapshot['tables'], 'protected_other_rows':snapshot['protected_other_rows'],
        'module_count': len(snapshot['modules']),
        'installed_count': sum(row['state']=='installed' for row in snapshot['modules'].values()),
        'filestore': {k: snapshot['filestore'][k] for k in ('count','sha256')},
        'attachment_pointers': snapshot['attachment_pointers'],
        'views': {key: {'languages': value['languages']} for key,value in snapshot['views'].items()
                  if key in ALLOWED_VIEWS}, 'business': snapshot['business']}
