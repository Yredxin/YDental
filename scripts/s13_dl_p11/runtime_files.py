"""Runtime native READ ONLY inventory of protected attachment references and files.
No runtime/guard/target change, no authentication-column reads, no business write.
"""
import argparse,datetime as dt,hashlib,importlib.util,json,os,subprocess
from pathlib import Path,PurePosixPath
ROOT=Path.cwd(); OUT=ROOT/'.local/dl-p11/verification'
p=argparse.ArgumentParser();p.add_argument('--candidate',required=True);p.add_argument('--label',required=True);a=p.parse_args()
assert a.label.replace('-','').isalnum() and len(a.label)<50
source=ROOT/'scripts/s13_dl_p11/protected_snapshot.py'
spec=importlib.util.spec_from_file_location('p11_runtime_file_scope',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==a.candidate
assert subprocess.check_output(['git','branch','--show-current'],text=True).strip()=='codex/s13-dl-p11-report-source-detail-r1'
assert subprocess.check_output(['git','-C',str(ROOT.parent),'rev-parse','HEAD'],text=True).strip()==m.CORE
cfg=m.private_json(m.PRIVATE/'runtime.json')['database'];assert(cfg['name'],cfg['expected_oid'],str(cfg['expected_cluster_ref']),cfg['user'])==(m.TARGET,m.OID,m.CLUSTER,m.TARGET)
started=dt.datetime.now(dt.timezone.utc).isoformat();c=m.psycopg2.connect(dbname=cfg['name'],host=cfg['host'],port=cfg['port'],user=cfg['user'],password=cfg['password'],connect_timeout=5,options='-c default_transaction_read_only=on -c statement_timeout=15000 -c TimeZone=UTC');c.set_session(readonly=True,isolation_level='REPEATABLE READ')
pid=c.get_backend_pid(); refs=[]; paths={}
try:
 with c.cursor() as q:
  q.execute("SELECT current_database(),(SELECT oid FROM pg_database WHERE datname=current_database()),(pg_control_system()).system_identifier::text,current_user,current_setting('transaction_read_only'),current_setting('transaction_isolation')");identity=q.fetchone();assert identity==(m.TARGET,m.OID,m.CLUSTER,m.TARGET,'on','repeatable read')
  q.execute("SELECT id,store_fname FROM ir_attachment WHERE (res_model LIKE 'ydental.%' OR res_model IN ('account.move','purchase.order')) AND store_fname IS NOT NULL ORDER BY id")
  fs=(ROOT/'.local/s11/new-target-data/filestore'/m.TARGET).resolve()
  for ident,name in q.fetchall():
   rel=PurePosixPath(name);assert not rel.is_absolute() and not any(v in ('..','.') for v in rel.parts)
   path=fs.joinpath(*rel.parts);assert path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(fs)
   b=path.read_bytes();item={'attachment_id':ident,'file_path_sha256':hashlib.sha256(name.encode()).hexdigest(),'file_size':len(b),'file_sha256':hashlib.sha256(b).hexdigest()};refs.append(item)
   if name in paths:assert paths[name]==(len(b),item['file_sha256'])
   paths[name]=(len(b),item['file_sha256'])
finally:
 c.rollback();rollback_idle=c.get_transaction_status()==m.psycopg2.extensions.TRANSACTION_STATUS_IDLE;c.close();closed=bool(c.closed)
assert rollback_idle and closed
v={'status':'RUNTIME_NATIVE_PROTECTED_REFERENCE_FILE_INVENTORY_COMPLETE','candidate_commit':a.candidate,'reviewer':'/root/runtime_p11 (runtime adapter implementer; independent acceptance separate)','started_at_utc':started,'finished_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'actual_new_physical_pid':pid,'identity':identity,'rollback_idle':rollback_idle,'connection_closed':closed,'protected_attachment_reference_count':len(refs),'unique_physical_path_count':len(paths),'distinct_file_sha256_count':len(set(v[1] for v in paths.values())),'shared_reference_excess':len(refs)-len(paths),'all_reference_files_really_opened_and_hashed':True,'references':refs,'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'projection_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'business_write_or_service_start':False}
b=(json.dumps(v,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode();out=OUT/(a.label+'-reference-file-inventory.json');fd=os.open(out,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'wb') as f:f.write(b)
print(json.dumps({'status':v['status'],'path':str(out.relative_to(ROOT)),'sha256':hashlib.sha256(b).hexdigest(),'new_physical_pid':pid,'references':len(refs),'unique_paths':len(paths),'distinct_sha256':v['distinct_file_sha256_count']}))
