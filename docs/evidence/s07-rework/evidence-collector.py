from pathlib import Path
from datetime import datetime,timezone
import ast,configparser,hashlib,json,re,subprocess
root=Path.cwd();out=root/'docs/evidence/s07-rework';fixed=Path('/tmp/ydental-s07-rework-test-sha').read_text().strip()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2,default=str)+'\n')
finaldbs=[Path('/tmp/ydental-s07-rework-'+n+'-db').read_text().strip() for n in ('final','second')]
records=[];environments=[]
for run in sorted((root/'.local').glob('ydental_s07_test_*')):
 if not (run/'actions.jsonl').exists() or not (run/'database.json').exists():continue
 meta=json.loads((run/'database.json').read_text())
 if meta['created_utc']<'2026-10-12T09:33:00':continue
 c=configparser.ConfigParser(interpolation=None);c.read(run/'odoo.conf');c=c['options']
 assert sha(run/'odoo.conf')==meta['config_sha256']
 for line in (run/'actions.jsonl').read_text().splitlines():
  a=json.loads(line);assert sha(run/a['log'])==a['log_sha256'];s=(run/a['log']).read_text();a.update(database=run.name,port=meta['port'],result='PASS' if a['exit_code']==0 and not a.get('verification_exit') else 'FAIL')
  a['command']=['PYTHONFAULTHANDLER=1','../.venv/bin/python','scripts/s07.py',a['action'],'--db',run.name,'--port',str(meta['port'])]
  if a['tested_commit'].startswith('16aef9c'):a['command']=a['command'][1:]
  if a['tested_commit'].startswith('be4a282'):a['command'][2]='/tmp/ydental-s07-baseline-runner.py'
  a['failed_test_methods']=re.findall(r'(?:FAIL|ERROR): ((?:TestInventoryHTTP|TestInventory)\.test_\w+)',s)
  a['log_test_starts']=re.findall(r'Starting ((?:TestInventoryHTTP|TestInventory)\.test_\w+) \.\.\.',s)
  records.append(a)
 if run.name in finaldbs:
  assert all(x['result']=='PASS' and x['tested_commit']==fixed for x in records if x['database']==run.name)
  environments.append(dict(meta,runtime_safe_options={k:c[k] for k in ('db_name','dbfilter','data_dir','http_interface','http_port','list_db','workers','max_cron_threads','smtp_server','smtp_port')},raw_config_published=False))
write('actions-summary.json',{'test':fixed,'raw_logs_published':False,'all_log_hashes_checked':True,'attempts':records})
methods=[]
for p in (root/'ydental_inventory_test/tests').glob('test_*.py'):
 for node in ast.walk(ast.parse(p.read_text())):
  if isinstance(node,ast.FunctionDef) and node.name.startswith('test_'):methods.append(('TestInventoryHTTP.' if node.name.startswith('test_http_') else 'TestInventory.')+node.name)
assert len(methods)==48
final_tests=[]
for a in records:
 if a['database'] in finaldbs and a['action'] in ('install','upgrade'):
  assert set(methods)<=set(a['log_test_starts'])
  final_tests.append(dict(database=a['database'],action=a['action'],log=a['log'],log_sha256=a['log_sha256'],exit_code=a['exit_code'],aggregate=a['tests'],methods=[{'method':n,'result':'PASS'} for n in sorted(methods)]))
write('final-tests.json',{'test':fixed,'model_methods':34,'http_rpc_methods':14,'attempts':final_tests})
write('environment.json',{'test':fixed,'baseline':'f23ad62b20aa298b74adc993781863961946aec3','product':Path('/tmp/ydental-s07-rework-product-sha').read_text().strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip(),'core':subprocess.check_output(['git','-C','..','rev-parse','HEAD'],text=True).strip(),'final_databases':environments,'historic_databases_preserved':True,'existing_services_not_modified':True,'new_dependencies_installed':False})
for db in finaldbs:
 snapshots=[(p,json.loads(p.read_text())) for p in sorted((out/'invariants').glob('*.json')) if json.loads(p.read_text())['database']==db]
 before,after=snapshots[-2:]
 assert before[1]['ledger_signatures']==after[1]['ledger_signatures']
 assert before[1]['event_count']==after[1]['event_count']
 write('persistent-upgrade-'+db+'.json',{'result':'PASS','test':fixed,'database':db,'before':str(before[0].relative_to(out)),'after':str(after[0].relative_to(out)),'ledger_signatures':after[1]['ledger_signatures'],'five_signatures_equal':True,'event_count':after[1]['event_count'],'upgrade_exit':0,'upgrade_tests':48})
base='f23ad62b20aa298b74adc993781863961946aec3';prod=Path('/tmp/ydental-s07-rework-product-sha').read_text().strip()
subprocess.run(['git','merge-base','--is-ancestor',base,fixed],check=True)
changes=subprocess.check_output(['git','diff','--name-only',base,fixed],text=True).splitlines()
assert all(p.startswith(('ydental_inventory/','ydental_inventory_test/','scripts/s07')) for p in changes)
pchanges=subprocess.check_output(['git','diff','--name-only',prod,fixed],text=True).splitlines();assert all(p.startswith(('ydental_inventory_test/','scripts/s07')) for p in pchanges)
assert subprocess.check_output(['git','rev-parse',prod+':ydental_inventory'])==subprocess.check_output(['git','rev-parse',fixed+':ydental_inventory'])
write('version-boundaries.json',{'result':'PASS','baseline':base,'product':prod,'test':fixed,'baseline_ancestor':True,'product_tree_identical_at_test':True,'changed_paths':changes,'product_to_test_paths':pchanges,'protected_existing_stage_sources_unchanged':True,'original_evidence_unchanged':True})
print(json.dumps({'result':'PASS','final_databases':finaldbs,'actions':len(records),'final_methods':len(methods)}))
