"""P0-16 immutable offline contract; importing this module never connects."""
import ast
import configparser
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
BASE = '82a435e90b2aaba6437322700ad2ac0be4e7e328'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
AUTH = 6214616229
NAME = 'ydental_s10_test_20261015073500_e50f4a71'
OID = 2100310
CLUSTER = '7694897083368259627'
CONFIG_SHA = '867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7'
MARKER_SHA = '1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa'
MANIFEST_SHA = 'bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283'
FOLDER = ROOT / '.local' / NAME
PRIVATE = ROOT / '.local/s10-p0-16'
OUT = ROOT / 'docs/evidence/s10-p0-16'
SCRIPTS = ['scripts/s10_p0_16_contract.py', 'scripts/s10_p0_16_readonly.py', 'scripts/s10_p0_16_offline.py']
BASELINE = 'docs/evidence/s10-p0-14/source-after.json'
SCHEMA = 'docs/evidence/s10-p0-11/read-only-sql.json'
ZERO = dict.fromkeys(('OTHER_DB_CONNECTION', 'MAINTENANCE_CONNECTION', 'CREATE', 'ODOO_HTTP',
    'FIREFOX', 'BUSINESS_GET_POST', 'PDF_GENERATION', 'FUNDS_FEE_STOCK_ATTACHMENT_WRITE',
    'ODOO_SHELL_UPGRADE_INSTALL_INIT_TEST', 'DIRECT_BUSINESS_ORM', 'SUDO',
    'OS_PG_DOCKER_FIREWALL_IPV6_SPECIAL', 'ISSUE_PROJECT_MUTATION', 'MERGE_DEPLOY_S11'), 0)
OPTIONS = '-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=3000 -c idle_in_transaction_session_timeout=15000 -c timezone=UTC'
SOURCE_FILES = [
 'ydental_access/models/ydental_access_service.py', 'ydental_access/models/constants.py',
 'ydental_access/models/ydental_access_membership.py', 'ydental_access/models/ydental_access_grant.py',
 'ydental_settlement/models/ydental_settlement_service.py', 'ydental_settlement/controllers/settlement.py',
 'ydental_settlement/models/report_ydental_settlement_pdf.py', 'ydental_settlement/models/__init__.py',
 'ydental_settlement/__manifest__.py', 'ydental_settlement/report/ydental_settlement_reports.xml',
 'ydental_settlement/report/ydental_settlement_templates.xml',
 'ydental_settlement/views/ydental_settlement_templates.xml',
 'ydental_print/__manifest__.py', 'ydental_print/report/ydental_print_reports.xml',
 'ydental_patient/models/ydental_patient_service.py',
]
CORE_FILES = ['odoo/tools/convert.py', 'odoo/addons/base/models/res_users.py',
              'odoo/addons/base/models/ir_actions_report.py']


def sha(b):
    return hashlib.sha256(b).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def default(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def save(path, value, exclusive=True):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x' if exclusive else 'w') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, indent=2, default=default)
        stream.write('\n')


def git(*args, cwd=ROOT):
    assert args[0] in ('rev-parse','branch','remote','status','show','ls-files','ls-tree','diff')
    return subprocess.check_output(['git', *args], cwd=cwd)


def fixed(path, core=False):
    root = ROOT.parent if core else ROOT
    b = (root / path).read_bytes()
    assert git('show', (CORE if core else BASE) + ':' + path, cwd=root) == b, 'FIXED_SOURCE_DRIFT:' + path
    return b


def repo_gate(execution=True):
    head = git('rev-parse','HEAD').decode().strip()
    assert head == BASE if execution else (head == BASE or git('rev-parse','HEAD^').decode().strip() == BASE)
    assert git('branch','--show-current').decode().strip() == BRANCH
    assert git('remote','get-url','origin').decode().strip() == 'https://github.com/Yredxin/YDental.git'
    assert git('rev-parse','HEAD',cwd=ROOT.parent).decode().strip() == CORE
    assert not git('status','--porcelain','--untracked-files=no',cwd=ROOT.parent).strip()
    for line in git('status','--porcelain','--untracked-files=all').decode().splitlines():
        assert line[:2] in ('??','A ')
        assert line[3:].startswith(('scripts/s10_p0_16_','docs/s10-p0-16-','docs/evidence/s10-p0-16/'))


def files_gate():
    assert sha((FOLDER / 'database.json').read_bytes()) == MARKER_SHA
    assert sha((FOLDER / 'odoo.conf').read_bytes()) == CONFIG_SHA
    marker = read(FOLDER / 'database.json')
    assert (marker['database'],marker['oid'],marker['cluster'],marker['core']) == (NAME,OID,CLUSTER,CORE)
    assert marker['source_oid'] == 2100301 and marker['config_sha256'] == CONFIG_SHA
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(FOLDER / 'odoo.conf')
    opt = parser['options']
    assert (opt['db_host'],opt['db_port'],opt['db_user']) == ('127.0.0.1','5432','odoo')
    files, sha1s = {}, {}
    base = FOLDER / 'data/filestore' / NAME
    assert base.is_dir() and not base.is_symlink()
    for path in sorted(base.rglob('*')):
        assert not path.is_symlink()
        if path.is_file():
            b = path.read_bytes()
            key = str(path.relative_to(base))
            files[key] = sha(b)
            sha1s[key] = hashlib.sha1(b).hexdigest()
    manifest = sha(''.join(k + '\t' + files[k] + '\n' for k in sorted(files)).encode())
    assert len(files) == 152 and manifest == MANIFEST_SHA
    return {'database':NAME,'oid':OID,'cluster':CLUSTER,'config_sha256':CONFIG_SHA,
        'marker_sha256':MARKER_SHA,'filestore_files':152,'filestore_manifest_sha256':manifest,
        'parent_oid':2100301}, sha1s


def credentials():
    # Parse the sealed config in memory only. Never log or return it to artifacts.
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(FOLDER / 'odoo.conf')
    return dict(host='127.0.0.1',port=5432,user='odoo',password=parser['options']['db_password'])


def xml_tree(element):
    return [element.tag, sorted(element.attrib.items()), (element.text or '').strip(),
        [[xml_tree(child), (child.tail or '').strip()] for child in element]]


def expected_template(path, template_id):
    tree = ET.fromstring(fixed(path))
    node = next(x for x in tree.findall('template') if x.get('id') == template_id)
    node.tag = 't'
    del node.attrib['id']
    node.set('t-name', 'ydental_settlement.' + template_id)
    return xml_tree(node)


def rank_contract():
    tree = ast.parse(fixed('ydental_access/models/constants.py'))
    rank = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id == 'RANK' for t in n.targets))
    assert rank == {'none':0,'read':1,'write':2}
    return rank


def plan():
    schema = read(ROOT / SCHEMA)['columns']
    assert len(schema) == 643
    entries = []
    def add(label, sql, params=()):
        entries.append({'label':label,'sql':sql,'params':list(params)})
    add('read_only','SHOW transaction_read_only')
    add('isolation','SHOW transaction_isolation')
    add('identity', 'SELECT pg_catalog.current_database() AS database,(SELECT oid FROM pg_catalog.pg_database WHERE datname=pg_catalog.current_database()) AS oid,(SELECT system_identifier::text FROM pg_catalog.pg_control_system()) AS cluster,pg_catalog.pg_backend_pid() AS backend_pid,CURRENT_TIMESTAMP AS database_time')
    add('other_connections','SELECT pid FROM pg_catalog.pg_stat_activity WHERE datname=pg_catalog.current_database() AND pid<>pg_catalog.pg_backend_pid() ORDER BY pid')
    add('catalog', "SELECT c.relname,a.attname,pg_catalog.format_type(a.atttypid,a.atttypmod) AS data_type FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace JOIN pg_catalog.pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum")
    for table, columns in sorted(schema.items()):
        assert table.replace('_','').isalnum()
        order = 't."id"' if 'id' in columns else 'pg_catalog.to_jsonb(t)::text'
        # Same PG JSONB text, order and trailing LF as P0-14. Built-in SHA
        # returns only count/hash; clinical/password rows never reach the client.
        query = 'SELECT pg_catalog.count(*)::bigint AS rows,pg_catalog.encode(pg_catalog.sha256(pg_catalog.convert_to(COALESCE(pg_catalog.string_agg(pg_catalog.to_jsonb(t)::text,E\'\\n\' ORDER BY ' + order + '),\'\')||E\'\\n\',\'UTF8\')),\'hex\') AS sha256 FROM public."' + table + '" t'
        add('hash:' + table,query)
    add('user','SELECT id,active,share,company_id,partner_id FROM public.res_users WHERE id=%s',(5,))
    add('companies','SELECT cid,user_id FROM public.res_company_users_rel WHERE user_id=%s ORDER BY cid',(5,))
    add('store','SELECT s.id,s.active,s.company_id,c.active AS company_active,c.currency_id FROM public.ydental_access_store s JOIN public.res_company c ON c.id=s.company_id WHERE s.id=%s',(1,))
    add('memberships','SELECT m.id,m.ydental_user_id,m.ydental_store_id,m.ydental_employee_id,m.active,m.ydental_is_manager,e.id AS employee_id,e.active AS employee_active,e.user_id AS employee_user_id,e.company_id AS employee_company_id,e.resource_id,r.active AS resource_active,r.user_id AS resource_user_id,r.company_id AS resource_company_id FROM public.ydental_access_membership m JOIN public.hr_employee e ON e.id=m.ydental_employee_id JOIN public.resource_resource r ON r.id=e.resource_id WHERE m.ydental_user_id=%s AND m.ydental_store_id=%s ORDER BY m.id',(5,1))
    add('grants','SELECT g.id,g.ydental_membership_id,g.ydental_category,g.ydental_level FROM public.ydental_access_grant g JOIN public.ydental_access_membership m ON m.id=g.ydental_membership_id WHERE m.ydental_user_id=%s AND m.ydental_store_id=%s AND m.active ORDER BY g.id',(5,1))
    add('group_xmlids',"SELECT module,name,model,res_id FROM public.ir_model_data WHERE (module=%s AND name=%s) OR (module=%s AND name=%s) ORDER BY module,name",('base','group_user','ydental_base','ydental_base_group_user'))
    add('user_groups','SELECT gid,uid FROM public.res_groups_users_rel WHERE uid=%s ORDER BY gid',(5,))
    add('implied_groups','SELECT gid,hid FROM public.res_groups_implied_rel ORDER BY gid,hid')
    add('invoice','SELECT id,company_id,currency_id,partner_id,journal_id,state,move_type,payment_state,amount_total,amount_residual,invoice_date,date FROM public.account_move WHERE id=%s',(1,))
    add('sources','SELECT id,ydental_fee_id,ydental_store_id,ydental_patient_id,ydental_invoice_id,ydental_line_id,ydental_currency_id,ydental_original_amount,ydental_discount,ydental_price_version FROM public.ydental_settlement_source WHERE ydental_invoice_id=%s ORDER BY id',(1,))
    add('fees','SELECT id,ydental_store_id,ydental_patient_id,ydental_event_id,ydental_parent_id,ydental_price_snapshot_id,ydental_price_review_id,ydental_currency_id,ydental_quantity,ydental_unit_price,ydental_amount FROM public.ydental_treatment_fee WHERE id IN (%s,%s,%s,%s) ORDER BY id',(1,2,3,4))
    add('snapshots','SELECT id,ydental_store_id,ydental_price_id,ydental_currency_id,ydental_quantity,ydental_unit_price,ydental_version FROM public.ydental_intake_snapshot WHERE id IN (%s,%s,%s,%s) ORDER BY id',(1,2,3,4))
    add('invoice_lines','SELECT id,move_id,company_id,currency_id,account_id,quantity,price_unit,price_subtotal,balance,amount_residual,display_type FROM public.account_move_line WHERE move_id=%s ORDER BY id',(1,))
    add('payments','SELECT p.id,p.company_id,p.currency_id,p.partner_id,p.move_id,p.payment_type,p.partner_type,p.amount,p.state,m.state AS move_state,m.origin_payment_id FROM public.account_payment p JOIN public.account_move m ON m.id=p.move_id WHERE p.id IN (%s,%s) ORDER BY p.id',(1,2))
    add('partials','SELECT p.id,p.company_id,p.amount,p.debit_move_id,p.credit_move_id,d.move_id AS debit_invoice,c.move_id AS credit_move,m.origin_payment_id FROM public.account_partial_reconcile p JOIN public.account_move_line d ON d.id=p.debit_move_id JOIN public.account_move_line c ON c.id=p.credit_move_id JOIN public.account_move m ON m.id=c.move_id WHERE d.move_id=%s ORDER BY p.id',(1,))
    add('settlement_payments','SELECT id,ydental_store_id,ydental_patient_id,ydental_payment_id,ydental_cashier_id,ydental_currency_id,ydental_channel,ydental_amount FROM public.ydental_settlement_payment WHERE ydental_store_id=%s AND ydental_patient_id=%s ORDER BY id',(1,1))
    add('patient','SELECT id,active,ydental_store_id,ydental_partner_id,ydental_merged_into_id FROM public.ydental_patient WHERE id=%s',(1,))
    add('patient_relation','SELECT id,ydental_patient_id,ydental_store_id,ydental_superseded_by_id FROM public.ydental_patient_relation WHERE ydental_patient_id=%s AND ydental_store_id=%s ORDER BY id',(1,1))
    add('modules',"SELECT name,state,latest_version FROM public.ir_module_module WHERE state='installed' ORDER BY name")
    add('report_xmlids',"SELECT module,name,model,res_id,noupdate FROM public.ir_model_data WHERE (module=%s AND name IN (%s,%s,%s)) OR (module=%s AND name=%s) ORDER BY module,name",('ydental_settlement','ydental_settlement_pdf_report','ydental_settlement_pdf','ydental_settlement_page','ydental_print','ydental_pdf_a4'))
    add('report_action','SELECT id,model,report_type,report_name,paperformat_id,attachment,attachment_use,save_as_attachment FROM public.ir_act_report_xml WHERE report_name=%s ORDER BY id',('ydental_settlement.ydental_settlement_pdf',))
    add('report_groups','SELECT g.uid AS report_id,g.gid FROM public.res_groups_report_rel g JOIN public.ir_act_report_xml r ON r.id=g.uid WHERE r.report_name=%s ORDER BY g.uid,g.gid',('ydental_settlement.ydental_settlement_pdf',))
    add('report_views','SELECT id,key,type,active,inherit_id,arch_db FROM public.ir_ui_view WHERE key IN (%s,%s) ORDER BY key,id',('ydental_settlement.ydental_settlement_pdf','ydental_settlement.ydental_settlement_page'))
    add('paperformat',"SELECT p.id,p.format,p.orientation,p.margin_top,p.margin_bottom,p.margin_left,p.margin_right,p.dpi,p.disable_shrinking FROM public.report_paperformat p JOIN public.ir_model_data d ON d.model='report.paperformat' AND d.res_id=p.id WHERE d.module=%s AND d.name=%s ORDER BY p.id",('ydental_print','ydental_pdf_a4'))
    add('languages','SELECT id,code,active FROM public.res_lang WHERE code IN (%s,%s) ORDER BY code',('en_US','zh_CN'))
    add('attachment_pointers','SELECT store_fname,checksum FROM public.ir_attachment WHERE store_fname IS NOT NULL ORDER BY id')
    return {'base':BASE,'authorization':AUTH,'database':NAME,'schema':schema,
        'schema_source':SCHEMA,'schema_source_sha256':sha(fixed(SCHEMA)),
        'reference_source':BASELINE,'reference_sha256':sha(fixed(BASELINE)),
        'queries':entries,'maximum_statements':len(entries),
        'endpoint':{'host':'127.0.0.1','port':5432,'user':'odoo','dbname':NAME,'connect_timeout':5,'options':OPTIONS},
        'transaction':'READ ONLY / REPEATABLE READ; driver BEGIN before first SHOW; ROLLBACK/CLOSE finally',
        'maximum_connections':1,'maximum_seconds':150,'maximum_statement_ms':15000,
        'zero_budget':ZERO,'rank':rank_contract(),
        'hash_algorithm':'SHA256(UTF8(join PG to_jsonb(t)::text ordered by id else JSONB text with LF + trailing LF)); empty table hashes one LF',
        'permission_scope':'actual store1 grant only; no admin exemption; existing medical grant not expanded or used',
        'report_ids':{'action_xmlid':'ydental_settlement.ydental_settlement_pdf_report','report_name_and_template_xmlid':'ydental_settlement.ydental_settlement_pdf'},
        'paid_invoice_UI_limitation':'_workbench filters residual>0; existing bill link only inside unpaid invoice loop; no claim invoice1 button visible',
        'private_rows_policy':'643 table signatures computed by side-effect-free pg_catalog built-ins; no clinical/password content leaves server; only minimal identity/grant/account/report metadata projected'}
