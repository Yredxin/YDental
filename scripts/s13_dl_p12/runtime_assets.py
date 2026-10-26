"""Read native derived web-asset metadata and actual files separately from business originals."""
import argparse,datetime as dt,hashlib,json,os,re,subprocess,sys
from pathlib import Path
root=Path.cwd();sys.path.insert(0,str(root/'scripts/s13_dl_p12'))
from admission_probe import TARGET,OID,CORE,CLUSTER,BRANCH,read_provider,write_receipt
import psycopg2
from protected_snapshot import canonical
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--label',required=True);a=p.parse_args()
assert re.fullmatch('[A-Za-z0-9_-]{1,60}',a.label)
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.candidate
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()==BRANCH
assert subprocess.check_output(['git','-C',str(root.parent),'rev-parse','HEAD'],text=True).strip()==CORE
assert not (root/'.local/dl-p12/active.json').exists()
cfg=read_provider(root/'.local/dl-p12/runtime.json')
v={'status':'INCOMPLETE_NATIVE_DERIVED_ASSET_SNAPSHOT','candidate_commit':a.candidate,'observer':'/root/runtime_p12 (runtime author; independent acceptance separate)','layer':'NEW_PHYSICAL_READ_ONLY_REPEATABLE_READ','started_at_utc':dt.datetime.now(dt.UTC).isoformat(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'business_write_or_service_action':False,'protected_business_original_scope_unchanged':True,'assets':[]}
c=None
try:
 c=psycopg2.connect(dbname=cfg['name'],host=cfg['host'],port=cfg['port'],user=cfg['user'],password=cfg['password'],connect_timeout=5,options='-c default_transaction_read_only=on -c statement_timeout=15000 -c TimeZone=UTC');c.set_session(readonly=True,isolation_level='REPEATABLE READ')
 with c.cursor() as q:
  q.execute("SELECT pg_backend_pid(),current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')")
  identity=q.fetchone();assert identity[1:]==(TARGET,OID,CLUSTER,TARGET,'on','repeatable read');v['identity']=identity
  q.execute("SELECT id,name,type,mimetype,url,public,res_model,res_id,store_fname,file_size,checksum,create_date,write_date FROM ir_attachment WHERE url LIKE '/web/assets/%' ORDER BY id")
  columns=['id','name','type','mimetype','url','public','res_model','res_id','store_fname','file_size','checksum','create_date','write_date']
  fs=(root/'.local/s11/new-target-data/filestore'/TARGET).resolve()
  for values in q.fetchall():
   row=dict(zip(columns,values));stored=row.pop('store_fname');row['native_derived_web_asset_not_protected_business_original']=True
   if stored:
    rel=Path(stored);assert not rel.is_absolute() and '..' not in rel.parts
    path=fs/rel;assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(fs)
    raw=path.read_bytes();assert row['file_size']==len(raw)
    row.update(file_path_sha256=hashlib.sha256(stored.encode()).hexdigest(),actual_size=len(raw),actual_sha256=hashlib.sha256(raw).hexdigest(),contains_P12_settlement_lookup_marker=b'settlement-lookup' in raw)
   v['assets'].append(row)
 v['status']='READONLY_NATIVE_DERIVED_WEB_ASSET_METADATA_AND_FILE_HASHES_COMPLETE'
finally:
 if c:c.rollback();v['rollback_idle']=c.get_transaction_status()==psycopg2.extensions.TRANSACTION_STATUS_IDLE;c.close();v['connection_closed']=bool(c.closed)
 v['finished_at_utc']=dt.datetime.now(dt.UTC).isoformat()
assert v['rollback_idle'] and v['connection_closed']
out=root/'.local/dl-p12/verification'/('derived-assets-'+a.label+'.json');sha=write_receipt(out,canonical(v))
print(json.dumps({'status':v['status'],'path':str(out.relative_to(root)),'sha256':sha,'physical_pid':v['identity'][0],'asset_count':len(v['assets'])}))
