"""Finite native module dependency metadata, sole target READ ONLY/RR."""
import argparse,datetime as dt,hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'scripts/s13_dl_p9'))
from admission_probe import PLAN,BRANCH,TARGET,OID,CORE,CLUSTER,read_provider,write_receipt
import psycopg2
from psycopg2 import sql
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--label',required=True);p.add_argument('--phase',choices=('pre','post'),required=True);a=p.parse_args()
assert re.fullmatch('[A-Za-z0-9_-]{1,60}',a.label)
private=root/'.local/dl-p9';runtime_path=private/'runtime.json';runtime=json.loads(runtime_path.read_text());cfg=read_provider(runtime_path)
assert runtime['plan_id']==PLAN and runtime['branch']==BRANCH
candidate=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();assert runtime['candidate_commit']==candidate
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==BRANCH
assert subprocess.check_output(['git','-C',str(root.parent),'rev-parse','HEAD'],text=True).strip()==CORE
for stage in ('dl-p1','dl-p2','dl-p3','dl-p4','dl-p5','dl-p6','dl-p7','dl-p8','dl-p9','s12','s13'):
 assert not (root/'.local'/stage/'active.json').exists(),'Stop the exact active service before dependency pre/post'
assert not (root/'.local/s11/new-target-active.json').exists()
v={'status':'INCOMPLETE_NATIVE_DEPENDENCY_METADATA','phase':a.phase,'candidate_commit':candidate,'plan_id':PLAN,'started_at_utc':dt.datetime.now(dt.UTC).isoformat(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'runtime_sha256':hashlib.sha256(runtime_path.read_bytes()).hexdigest(),'database_write_performed':False,'secrets_or_authentication_hashes_selected':False,'table':'ir_module_module_dependency','module':'ydental_print'}
c=None
try:
 c=psycopg2.connect(dbname=cfg['name'],host=cfg['host'],port=cfg['port'],user=cfg['user'],password=cfg['password'],connect_timeout=5,options='-c default_transaction_read_only=on -c statement_timeout=15000 -c TimeZone=UTC');c.set_session(readonly=True,isolation_level='REPEATABLE READ')
 with c.cursor() as q:
  q.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
  identity=q.fetchone();assert identity[1:]==(TARGET,OID,CLUSTER,TARGET,'on','repeatable read');v['identity']=identity
  q.execute("SELECT column_name,data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='ir_module_module_dependency' ORDER BY ordinal_position")
  cols=q.fetchall();assert cols and {'id','name','module_id'}<=set(k for k,_ in cols)
  assert all(not re.search('password|secret|token|session|credential',name,re.I) for name,_ in cols)
  v['columns']=cols
  q.execute('SELECT id,name,state FROM ir_module_module WHERE name=%s',('ydental_print',));module=q.fetchone();assert module and module[1:] == ('ydental_print','installed');v['module_record']=module
  q.execute(sql.SQL('SELECT {} FROM ir_module_module_dependency WHERE module_id=%s ORDER BY id').format(sql.SQL(',').join(sql.Identifier(k) for k,_ in cols)),(module[0],))
  v['rows']=[dict(zip([k for k,_ in cols],row)) for row in q.fetchall()]
  v['status']='READONLY_NATIVE_DEPENDENCY_METADATA_COMPLETE'
finally:
 if c:c.rollback();v['rollback_idle']=c.get_transaction_status()==psycopg2.extensions.TRANSACTION_STATUS_IDLE;c.close();v['connection_closed']=bool(c.closed)
 v['finished_at_utc']=dt.datetime.now(dt.UTC).isoformat()
out=private/'verification'/('dependencies-'+a.label+'-'+a.phase+'.json');sha=write_receipt(out,v)
print(json.dumps({'status':v['status'],'phase':a.phase,'physical_pid':v['identity'][0],'row_count':len(v['rows']),'dependency_names':[r['name'] for r in v['rows']],'sha256':sha,'path':str(out.relative_to(root))}))
