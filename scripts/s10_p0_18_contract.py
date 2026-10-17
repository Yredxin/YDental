"""P0-18 file contract and exact snapshot comparators; no connections on import."""
import ast
import configparser
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
from copy import deepcopy
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
CORE_ROOT = ROOT.parent
BASE = '68c9096246464f9ab1c3ec9c014fe7dc1be6d04b'
CORE = 'f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
AUTH = 6227951775
BRANCH = 'codex/s10-settlement-finance-r1-20261013'
SOURCE = 'ydental_s10_test_20261015073500_e50f4a71'
SOURCE_OID = 2100310
CLUSTER = '7694897083368259627'
NAME = 'ydental_s10_p018_20261017020000_8e21bc49'
PORT = 18318
PRIVATE = ROOT / '.local/s10-p0-18'
OUT = ROOT / 'docs/evidence/s10-p0-18'
RUN = ROOT / '.local' / NAME
SOURCE_RUN = ROOT / '.local' / SOURCE
PYTHON = CORE_ROOT / '.venv/bin/python'
XML = 'ydental_settlement/views/ydental_settlement_templates.xml'
IDS = {'ydental_settlement_action': ('ir.actions.act_url', 'ir_act_url', 571, 51384),
       'ydental_settlement_menu': ('ir.ui.menu', 'ir_ui_menu', 320, 51385),
       'ydental_settlement_tokens': ('ir.ui.view', 'ir_ui_view', 1597, 51386),
       'ydental_settlement_page_links': ('ir.ui.view', 'ir_ui_view', 1598, 51387),
       'ydental_settlement_page': ('ir.ui.view', 'ir_ui_view', 1599, 51388)}
VIEWS = {1597, 1598, 1599}
VIEW_FIELDS = {'arch_db', 'arch_prev', 'arch_fs', 'arch_updated', 'write_uid', 'write_date'}
TECH_FIELDS = {'write_uid', 'write_date'}
IDENTITY = {'res_users': 5, 'res_partner': 6, 'hr_employee': 1,
            'hr_version': 1, 'resource_resource': 1}
ASSETS = {'web.assets_frontend_minimal.min.js': 'application/javascript',
          'web.assets_frontend_lazy.min.js': 'application/javascript',
          'web.assets_frontend.min.css': 'text/css',
          'web.odoo_ui_icons.min.woff2': 'font/woff2',
          'web.material_symbols_outlined.min.woff2': 'font/woff2'}
OPTIONS = '-c default_transaction_read_only=on -c statement_timeout=15000 -c lock_timeout=3000 -c idle_in_transaction_session_timeout=15000 -c timezone=UTC'
ZERO = ['ECONOMIC_OR_CLINICAL_WRITE','HISTORICAL_REPLAY','PRODUCT_CHANGE','BUSINESS_POST',
        'DIRECT_BUSINESS_ORM','ODOO_SHELL_INSTALL_UPGRADE_INIT_TEST','EXECUTOR_SUDO',
        'OS_PG_DOCKER_NETWORK_SPECIAL','ISSUE_PROJECT_STATE_CHANGE','MERGE_DEPLOY_P019_S11']
BUDGET = dict(SOURCE_BEFORE=1,SOURCE_AFTER=1,MAINTENANCE=1,CREATE=1,
              TARGET_BEFORE=1,TARGET_METADATA_AFTER=1,TARGET_AFTER=1,
              METADATA_PROCESS=1,XML_IMPORT=1,METADATA_COMMIT=1,HTTP_PROCESS=1,
              FIREFOX_CONTEXT=1,LOGIN_GET=1,LOGIN_POST=1,STORE_SWITCH_POST=0,
              WORKBENCH_GET=2,PDF_GET=1,PDF_RENDER=1,DOWNLOAD=1,
              TRANSLATIONS_GET=1,STATIC_RESOURCE_GET=100,WKHTML_RESOURCE_GET=0,
              NEW_ASSET_ATTACHMENT=5,NATIVE_METADATA_CONNECTION=4,NATIVE_WEB_CONNECTION=4,LOGIN_AUDIT=1,LOGIN_SCOPE_AUDIT=1,
              STORE_SWITCH_AUDIT=1,INVOICE_VIEW_AUDIT=2,REPORT_DOWNLOAD_AUDIT=1)
BUDGET.update(dict.fromkeys(ZERO, 0))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def read(p):
    return json.loads(Path(p).read_text())

def save(p, x):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('x') as f:
        json.dump(x, f, ensure_ascii=False, indent=2, sort_keys=True, default=str)
        f.write('\n')

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', '-C', str(cwd), *args])

def repo_gate():
    assert git('rev-parse','HEAD').decode().strip() == BASE
    assert git('branch','--show-current').decode().strip() == BRANCH
    assert git('remote','get-url','origin').decode().strip() == 'https://github.com/Yredxin/YDental.git'
    assert git('rev-parse','HEAD',cwd=CORE_ROOT).decode().strip() == CORE
    assert not git('status','--porcelain','--untracked-files=no',cwd=CORE_ROOT).strip()
    for line in git('status','--porcelain','--untracked-files=all').decode().splitlines():
        assert line[:2] in ('??','A '), ('OLD_FILE_CHANGE',line)
        assert line[3:].startswith(('scripts/s10_p0_18_','docs/s10-p0-18-','docs/evidence/s10-p0-18/'))

def seal():
    expected = {'odoo.conf':'867f761771ecc20931f69103388df699b094b748e6a9d392e15ebe3d406e43c7',
                'database.json':'1a7f4a2a95e8aa0ea3d6da17abf6033976d2e39754185fa38e441a497351a5fa'}
    for p,h in expected.items():
        assert sha((SOURCE_RUN/p).read_bytes()) == h, 'SOURCE_FILE_SEAL'
    m = read(SOURCE_RUN/'database.json')
    assert (m['database'],m['oid'],m['cluster'],m['core']) == (SOURCE,SOURCE_OID,CLUSTER,CORE)
    files = filestore(SOURCE_RUN,SOURCE)
    digest = sha(''.join(k+'\t'+v+'\n' for k,v in files.items()).encode())
    assert len(files) == 152 and digest == 'bd0b0fbad15868bbabb836fa7016a91187bb31c6b9b6d934b2a7a0fe035c4283'
    return expected | {'filestore_files':len(files),'filestore_manifest':digest}

def filestore(folder, name):
    root = folder/'data/filestore'/name
    assert root.is_dir() and not root.is_symlink()
    files = {}
    for p in sorted(root.rglob('*')):
        assert not p.is_symlink()
        if p.is_file(): files[str(p.relative_to(root))] = sha(p.read_bytes())
    return files

def credentials():
    p = configparser.ConfigParser(interpolation=None)
    p.read(SOURCE_RUN/'odoo.conf')
    o = p['options']
    assert (o['db_host'],o['db_port'],o['db_user'],o['db_name']) == ('127.0.0.1','5432','odoo',SOURCE)
    return dict(host='127.0.0.1',port=5432,user='odoo',password=o['db_password'])

def schema():
    return read(ROOT/'docs/evidence/s10-p0-11/read-only-sql.json')['columns']

def norm(node):
    return [node.tag,dict(node.attrib),(node.text or '').strip(),
            [norm(n) for n in node if isinstance(n.tag,str)],(node.tail or '').strip()]

def template(name, old=False):
    n = etree.fromstring((ROOT/XML).read_bytes()).xpath("template[@id='%s']" % name)[0]
    n.tag='t';n.attrib.pop('id');n.set('t-name','ydental_settlement.'+name)
    if old:
        for child in n.xpath(".//section[@name='settled-bills']"):
            child.getparent().remove(child)
    return n

def old_metadata():
    # Saved W5 metadata only; never a connection to a protected clone.
    old = read(ROOT/'.local/s10-p0-14/w5-private-rows.json')['tables']
    result = {}
    for name,(_model,table,ident,xid) in IDS.items():
        row = next(json.loads(r) for r in old[table] if json.loads(r)['id']==ident)
        data = next(json.loads(r) for r in old['ir_model_data'] if json.loads(r)['id']==xid)
        assert (data['name'],data['module'],data['model'],data['res_id'],data['noupdate']) == (name,'ydental_settlement',_model,ident,False)
        if table == 'ir_ui_view':
            assert set(row['arch_db']) in ({'en_US'},{'en_US','zh_CN'})
            if ident==1599:assert set(row['arch_db'])=={'en_US','zh_CN'}
            assert all(norm(etree.fromstring(v.encode())) == norm(template(name,old=True)) for v in row['arch_db'].values())
        result[name] = {'record':row,'xmlid':data}
    return result

IDENTITY_SQL = 'SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),pg_backend_pid()'
ACTIVE_SQL = 'SELECT pid FROM pg_stat_activity WHERE datname=current_database() AND pid<>pg_backend_pid()'
CATALOG_SQL = "SELECT c.relname,a.attname FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum"

def table_sql():
    return {t:'SELECT to_jsonb(t)::text FROM public."'+t+'" t ORDER BY '+('"id"' if 'id' in cols else 'to_jsonb(t)::text') for t,cols in sorted(schema().items())}

def capture_cursor(cur, name, oid, source=False):
    started=time.monotonic()
    cur.execute(IDENTITY_SQL)
    db,actual,cluster,pid = cur.fetchone()
    assert (db,actual,cluster) == (name,oid,CLUSTER), 'DATABASE_IDENTITY'
    if source:
        cur.execute(ACTIVE_SQL); assert not cur.fetchall(), 'SOURCE_ACTIVE_CONNECTIONS'
    cur.execute(CATALOG_SQL)
    cols = {}
    for t,c in cur.fetchall(): cols.setdefault(t,[]).append(c)
    assert cols == schema() and len(cols)==643, 'CATALOG_DRIFT'
    tables, sig = {}, {}
    for t,q in table_sql().items():
        assert time.monotonic()-started<150,'SNAPSHOT_WALL_BUDGET'
        cur.execute(q)
        raw = [r[0] for r in cur.fetchall()]
        tables[t] = [json.loads(r) for r in raw]
        sig[t] = {'rows':len(raw),'sha256':sha(('\n'.join(raw)+'\n').encode())}
    return {'database':db,'oid':actual,'cluster':cluster,'backend_pid':pid,'tables':tables,'signatures':sig}

def row_map(rows):
    return {r['id']:r for r in rows}

def fields_changed(a,b):
    return {k for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}

def append_only(a,b,cap):
    old,new=row_map(a),row_map(b)
    assert old.keys()<=new.keys() and all(new[i]==r for i,r in old.items()), 'OLD_ROWS_CHANGED'
    rows=[r for i,r in new.items() if i not in old]
    assert len(rows)<=cap, 'APPEND_BUDGET'
    return rows

def metadata_gate(a,b):
    assert a.keys()==b.keys(),'METADATA_TABLE_SET'
    diff=[]
    for t in a:
        if a[t]==b[t]:continue
        assert t in {'ir_ui_view','ir_ui_menu','ir_act_url','ir_model_data'}, ('METADATA_TABLE',t)
        old,new=row_map(a[t]),row_map(b[t]);assert old.keys()==new.keys(), ('METADATA_ROWS',t)
        allowed_ids = ({1597,1598,1599} if t=='ir_ui_view' else {320} if t=='ir_ui_menu' else {571} if t=='ir_act_url' else {v[3] for v in IDS.values()})
        for i,r in old.items():
            f=fields_changed(r,new[i])
            if not f:continue
            assert i in allowed_ids
            assert f<=(VIEW_FIELDS if t=='ir_ui_view' else TECH_FIELDS), ('METADATA_COLUMN',t,i,sorted(f))
            assert new[i]['write_uid']==1 and new[i]['write_date'], 'METADATA_ACTOR'
            if t=='ir_ui_view':
                name=next(n for n,v in IDS.items() if v[2]==i and v[1]==t)
                assert set(new[i]['arch_db'])==set(r['arch_db'])
                assert all(norm(etree.fromstring(v.encode()))==norm(template(name)) for v in new[i]['arch_db'].values()), ('VIEW_ARCH',i)
                assert new[i]['arch_prev']==r['arch_db']['en_US'], ('ARCH_PREV',i)
                assert new[i]['arch_fs']==XML and new[i]['arch_updated'] is False
            diff.append({'table':t,'id':i,'fields':sorted(f),'before_sha256':sha(json.dumps(r,sort_keys=True).encode()),'after_sha256':sha(json.dumps(new[i],sort_keys=True).encode())})
    assert row_map(b['ir_ui_view'])[1599]['arch_db'] != row_map(a['ir_ui_view'])[1599]['arch_db'], 'MAIN_ARCH_NOT_UPDATED'
    return diff

def audit_expected(event, target_model, target_id, store=None, after=None, before=None, category='settlement', source='confirmed_offline_transaction'):
    return dict(ydental_event=event,ydental_user_id=5,ydental_store_id=store,
                ydental_category=category,ydental_target_model=target_model,ydental_target_id=target_id,
                ydental_source=source,ydental_result='accepted',ydental_before=before,ydental_after=after)

def web_gate(a,b,context):
    assert a.keys()==b.keys(),'WEB_TABLE_SET'
    mutable=set(IDENTITY)|{'res_users_log','res_device_log','ydental_access_session','ydental_access_audit','ir_attachment','orm_signaling_default'}
    changed=[t for t in a if a[t]!=b[t]]
    assert set(changed)<=mutable, ('WEB_TABLE_DRIFT',sorted(set(changed)-mutable))
    for t,i in IDENTITY.items():
        old,new=row_map(a[t]),row_map(b[t]);assert old.keys()==new.keys()
        for ident,r in old.items():
            f=fields_changed(r,new[ident]); allowed=TECH_FIELDS | ({'last_modified_uid','last_modified_date'} if t=='hr_version' else set())
            assert not f or ident==i and f<=allowed, ('IDENTITY_DRIFT',t,ident,sorted(f))
            if f:
                assert new[ident]['write_uid']==5
                if 'last_modified_uid' in f:assert new[ident]['last_modified_uid']==5
    logs=append_only(a['res_users_log'],b['res_users_log'],1)
    devices=append_only(a['res_device_log'],b['res_device_log'],1)
    sessions=append_only(a['ydental_access_session'],b['ydental_access_session'],1)
    assert len(logs)==len(devices)==len(sessions)==1
    for r in logs:
        assert set(r)==set(a['res_users_log'][0]) and r['create_uid']==r['write_uid']==5 and r['create_date']==r['write_date']
    for r in devices:
        assert r['user_id']==5 and r['ip_address']=='127.0.0.1' and 'Firefox/' in r['user_agent'] and r['revoked'] is False
        assert sha(r['session_identifier'].encode())==sessions[0]['ydental_key_hash']
        assert r['country'] is None and r['city'] is None
        assert all(r[k] is None for k in ('create_uid','write_uid','create_date','write_date'))
    s=sessions[0]
    assert (s['ydental_user_id'],s['ydental_store_id'],s['ydental_revision'],s['create_uid'],s['write_uid'])==(5,1,1,5,5)
    audits=append_only(a['ydental_access_audit'],b['ydental_access_audit'],6)
    expected=[audit_expected('login','res.users',5,category='personnel',source='native_authenticated_login'),
              audit_expected('login.scope','ydental.access.session',s['id'],category='personnel',source='authenticated_session'),
              audit_expected('store.switch','ydental.access.session',s['id'],store=1,category='personnel',source='interactive',before={'store_id':False},after={'store_id':1})]
    expected += [audit_expected('settlement.invoice_view','account.move',1,store=1)]*2
    expected += [audit_expected('settlement.report_download','account.move',1,store=1,after={'kind':'bill','pdf_sha256':context['pdf_sha256']})]
    assert len(audits)==len(expected)
    actual=[]
    for r in audits:
        assert set(r)==set(a['ydental_access_audit'][0]) and r['create_uid']==r['write_uid']==5 and r['create_date']==r['write_date']
        assert not r['ydental_reason']
        actual.append({k:(r[k] or None) if k in ('ydental_before','ydental_after','ydental_store_id') else r[k] for k in expected[0]})
    key=lambda r:json.dumps(r,sort_keys=True)
    assert sorted(actual,key=key)==sorted(expected,key=key), ('AUDIT_EXACT',actual)
    newassets=append_only(a['ir_attachment'],b['ir_attachment'],5)
    for r in newassets:
        assert r['res_model']=='ir.ui.view' and not r['res_id'] and r['public'] is True and r['type']=='binary'
        assert r['create_uid']==r['write_uid']==1 and r['create_date']==r['write_date']
        assert r['url'].startswith('/web/assets/') and r['url'].split('/')[-1] in ASSETS
        assert r['mimetype']==ASSETS[r['url'].split('/')[-1]] and r['name']==r['url'].split('/')[-1]
        assert not any(r[k] for k in ('res_field','access_token','original_id','description','db_datas'))
        assert 0<r['file_size']<=5000000 and r['store_fname'] and r['checksum']
    for r in append_only(a['orm_signaling_default'],b['orm_signaling_default'],1):
        assert set(r)=={'id','date'} and r['date']
    return {'changed_tables':changed,'audits':actual,'new_asset_ids':[r['id'] for r in newassets],
            'economic_clinical_permission_old_attachment_facts_unchanged':True}

def checkpoint():
    repo_gate();seal()
    plan=read(OUT/'execution-freeze.json')
    for p,h in plan['file_sha256'].items():assert sha((ROOT/p).read_bytes())==h, ('FREEZE_DRIFT',p)
    ck=read(PRIVATE/'preflight-api-readback.json');raw=read(PRIVATE/'preflight-api-raw.json')
    assert raw['body']==(PRIVATE/'preflight-body.txt').read_text()
    assert ck['verbatim_equal'] and raw['id']==ck['comment_id']
    assert sha(raw['body'].encode())==ck['body_sha256']
    assert ck['freeze_sha256']==sha((OUT/'execution-freeze.json').read_bytes())
    assert read(PRIVATE/'execution-ready.json')['remote_sha']==BASE
    return ck
