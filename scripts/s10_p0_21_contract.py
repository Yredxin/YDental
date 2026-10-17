"""P0-21 pure file contract, exact stored facts and pre-decision evidence."""
from collections import Counter,defaultdict
import configparser
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
CORE_ROOT=ROOT.parent
BASE='7a4bdb93cb4a2d625f01df7eb0ac41d76c5e0e46'
CORE='f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb'
AUTH=6229311739
BRANCH='codex/s10-settlement-finance-r1-20261013'
NAME='ydental_s10_test_20261017050000_21b0cafe'
PORT=18322
CLUSTER='7694897083368259627'
PRIVATE=ROOT/'.local/s10-p0-21'
OUT=ROOT/'docs/evidence/s10-p0-21'
RUN=ROOT/'.local'/NAME
PYTHON=CORE_ROOT/'.venv/bin/python'
PROTECTED=[2100310,2100325,2100326,2100327,2100330,2100333,2100336]
OPTIONS='-c statement_timeout=15000 -c lock_timeout=3000 -c idle_in_transaction_session_timeout=15000 -c timezone=UTC'
CATALOG="SELECT c.relname,a.attname,format_type(a.atttypid,a.atttypmod) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace JOIN pg_attribute a ON a.attrelid=c.oid WHERE n.nspname='public' AND c.relkind='r' AND a.attnum>0 AND NOT a.attisdropped ORDER BY c.relname,a.attnum"
IDENTITY='SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(SELECT system_identifier::text FROM pg_control_system()),pg_backend_pid()'
# Stored computed amounts/residuals and every physical relation row remain included.
ECON_PREFIX=('account_','stock_','ydental_inventory_','ydental_treatment_','ydental_settlement_')
ECON_EXTRA={'ydental_intake_snapshot','ydental_intake_price','product_pricelist','product_pricelist_item','res_currency','res_currency_rate','uom_uom'}
NON_ECON={'ydental_settlement_bill_original','ydental_settlement_mutex','ydental_settlement_receipt'}

def canonical(x):return json.dumps(x,sort_keys=True,ensure_ascii=False,default=str,separators=(',',':'))
def sha(x):return hashlib.sha256(x).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,sort_keys=True,default=str);f.write('\n');f.flush();os.fsync(f.fileno())
def event(name,**facts):
    OUT.mkdir(parents=True,exist_ok=True)
    with (OUT/'transaction-events.jsonl').open('a') as f:f.write(canonical({'event':name,**facts})+'\n');f.flush();os.fsync(f.fileno())
def git(*args,cwd=ROOT):return subprocess.check_output(['git','-C',str(cwd),*args],text=True).strip()
def credentials():
    p=configparser.ConfigParser(interpolation=None);p.read(CORE_ROOT/'odoo.conf');o=p['options'];assert (o['db_host'],o['db_port'],o['db_user'])==('127.0.0.1','5432','odoo')
    return dict(host='127.0.0.1',port=5432,user='odoo',password=o['db_password'])
def gate():
    assert git('branch','--show-current')==BRANCH and git('remote','get-url','origin')=='https://github.com/Yredxin/YDental.git'
    assert git('rev-parse','HEAD',cwd=CORE_ROOT)==CORE and not git('status','--porcelain','--untracked-files=no',cwd=CORE_ROOT)
    plan=read(PRIVATE/'active-plan.json');freeze=read(ROOT/plan['freeze_path'])
    raw=read(PRIVATE/plan['api_raw']);assert raw['body']==(PRIVATE/plan['body_path']).read_text() and raw['id']==plan['comment_id']
    assert sha((ROOT/plan['freeze_path']).read_bytes())==plan['freeze_sha256']
    assert git('rev-parse','HEAD')==freeze['execution_commit']
    for p,h in freeze['file_sha256'].items():assert sha((ROOT/p).read_bytes())==h,('FROZEN_DRIFT',p)
    return freeze

def economic(t):return t not in NON_ECON and (t.startswith(ECON_PREFIX) or t in ECON_EXTRA)
def capture(cur,full=True):
    cur.execute(IDENTITY);name,oid,cluster,pid=cur.fetchone();m=read(RUN/'database.json');assert (name,oid,cluster)==(NAME,m['oid'],CLUSTER) and oid not in PROTECTED
    cur.execute(CATALOG);schema={}
    for table,col,typ in cur.fetchall():schema.setdefault(table,[]).append({'column':col,'type':typ})
    tables={}
    for t,cols in sorted(schema.items()):
        if not full and not (economic(t) or t in NON_ECON or t.startswith(('ydental_clinical_','ydental_patient','ydental_access_','ydental_queue_','hr_','resource_','res_users','res_groups')) or t in {'res_company','res_partner','ir_attachment','ir_model_data'}):continue
        order='"id"' if any(c['column']=='id' for c in cols) else 'to_jsonb(t)::text'
        cur.execute('SELECT t.tableoid::regclass::text,t.tableoid,to_jsonb(t)::text FROM public."'+t+'" t ORDER BY '+order)
        # Numeric text remains exact; no epsilon, rounding-away, or omitted stored compute.
        tables[t]=[json.loads(raw,parse_float=Decimal)|{'__physical_table__':physical,'__physical_oid__':physical_oid} for physical,physical_oid,raw in cur.fetchall()]
    return {'database':name,'oid':oid,'cluster':cluster,'backend_pid':pid,'schema':schema,'tables':tables,'capture_scope':'full_catalog_all_physical_tables' if full else 'complete_economic_plus_document_identity_audit_attachment_source_rows'}

def diff(a,b):
    full=[];redacted=[]
    for table in sorted(a['tables'].keys()|b['tables'].keys()):
        x,y=a['tables'].get(table,[]),b['tables'].get(table,[])
        if canonical(x)==canonical(y):continue
        ga=defaultdict(list);gb=defaultdict(list)
        for r in x:ga[(r.get('__physical_table__',table),r.get('id',canonical(r)))].append(r)
        for r in y:gb[(r.get('__physical_table__',table),r.get('id',canonical(r)))].append(r)
        for key in sorted(ga.keys()|gb.keys(),key=str):
            u,v=ga.get(key,[]),gb.get(key,[])
            if Counter(map(canonical,u))==Counter(map(canonical,v)):continue
            cols=sorted(set().union(*(r.keys() for r in u+v)))
            if len(u)==len(v)==1:cols=[c for c in cols if canonical(u[0].get(c))!=canonical(v[0].get(c))]
            item={'table':table,'physical_key':['public',key[0],key[1]],'columns':cols,'before_count':len(u),'after_count':len(v),'economic':economic(table),'before_sha256':sha(canonical(u).encode()),'after_sha256':sha(canonical(v).encode()),'duplicate_ID_preserved':len(u)>1 or len(v)>1}
            full.append(item|{'before':u,'after':v});redacted.append(item)
    return full,redacted

def persist(label,before,after,decision):
    save(PRIVATE/(label+'-before.json'),before);save(PRIVATE/(label+'-after.json'),after)
    raw,index=diff(before,after);save(PRIVATE/(label+'-full-diff.json'),raw)
    save(OUT/(label+'-diff-index.json'),{'changes':index,'schema_changed':before['schema']!=after['schema'],'full_values_saved_before_gate':True})
    assert read(OUT/(label+'-diff-index.json'))['changes']==index
    try:result=decision(before,after,index)
    except BaseException as e:
        save(OUT/(label+'-decision.json'),{'PASS':False,'error_type':type(e).__name__,'detail_sha256':sha(str(e).encode()),'full_evidence_before_assertion':True});raise
    save(OUT/(label+'-decision.json'),{'PASS':True,'detail':result,'full_evidence_before_assertion':True});return result

def unchanged_economics(a,b,index):
    allowed={'ydental_clinical_document','ydental_clinical_version','ydental_access_audit','ydental_queue_mutex','ydental_settlement_bill_original','ir_attachment'}
    unexpected=[r for r in index if not r['economic'] and r['table'] not in allowed and not r['table'].startswith('orm_signaling_')]
    assert not unexpected,('UNEXPECTED_DOCUMENT_ORIGINAL_SIDE_EFFECT',[(r['table'],r['columns']) for r in unexpected])
    for change in index:
        if change['table'] in {'ydental_settlement_bill_original','ir_attachment','ydental_clinical_version','ydental_access_audit'}:
            assert change['before_count']==0 and change['after_count']==1,('IMMUTABLE_OLD_ROW_CHANGED',change['table'],change['physical_key'])
    bad=[r for r in index if r['economic']];assert not bad,('UNEXPLAINED_STORED_ECONOMIC_CHANGE',[(r['table'],r['columns']) for r in bad]);return {'economic_storage_exact':True,'all_stored_amounts_balances_relations_included':True}

def readonly(label):
    import psycopg2
    event('readonly_intent',label=label,database=NAME)
    conn=psycopg2.connect(dbname=NAME,connect_timeout=5,options='-c default_transaction_read_only=on '+OPTIONS,**credentials())
    try:
        conn.set_session(readonly=True,isolation_level='REPEATABLE READ')
        with conn.cursor() as cur:
            cur.execute('SHOW transaction_read_only');assert cur.fetchone()[0]=='on'
            cur.execute('SHOW transaction_isolation');assert cur.fetchone()[0]=='repeatable read'
            snap=capture(cur)
        save(PRIVATE/(label+'-RO-rows.json'),snap);save(OUT/(label+'-RO-signatures.json'),{k:v for k,v in snap.items() if k not in ('tables','schema')}|{'READ_ONLY':True,'REPEATABLE_READ':True,'tables':{t:{'rows':len(r),'sha256':sha(canonical(r).encode())} for t,r in snap['tables'].items()}})
        return snap
    finally:conn.rollback();conn.close();event('readonly_closed',label=label,rollback=True)
