"""Fixed-commit full C validation, fresh installation and retained business upgrade."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1];PYTHON=ROOT.parent/'.venv/bin/python'
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--db',required=True);parser.add_argument('--port',type=int,required=True);args=parser.parse_args()
assert re.fullmatch(r'ydental_s08c_test_[0-9]{14}_[a-f0-9]{8}',args.db)
assert 18000<=args.port<=18999
run=ROOT/'.local'/args.db;assert not run.exists(),'full validation requires a new isolated C database'
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
evidence=ROOT/'docs/evidence/s08c';evidence.mkdir(parents=True,exist_ok=True)
record={'database':args.db,'port':args.port,'tested_commit':commit,'started_utc':datetime.now(timezone.utc).isoformat(),'commands':[],'preview_stops':[],'result':'RUNNING'}
target=evidence/('validation-'+args.db+'.json')

def save():target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
def command(script,*arguments):
 assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()==commit,'fixed test SHA changed'
 cmd=[str(PYTHON),str(ROOT/'scripts'/script),*map(str,arguments)];start=datetime.now(timezone.utc).isoformat()
 if run.exists():
  log=run/('validation-'+script.removesuffix('.py')+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.log')
  with log.open('x') as handle:status=subprocess.run(cmd,cwd=ROOT,stdout=handle,stderr=subprocess.STDOUT,start_new_session=True).returncode
  item={'command':['../.venv/bin/python','scripts/'+script,*map(str,arguments)],'exit_code':status,'started_utc':start,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),'log':log.name}
 else:
  status=subprocess.run(cmd,cwd=ROOT,start_new_session=True).returncode
  item={'command':['../.venv/bin/python','scripts/'+script,*map(str,arguments)],'exit_code':status,'started_utc':start}
 record['commands'].append(item);save();print(json.dumps({'step':script,'arguments':list(map(str,arguments)),'exit_code':status}),flush=True)
 assert status==0,item

def action(name):
 command('s08c.py',name,'--db',args.db,'--port',args.port)
 if name in ('install','upgrade'):
  entry=json.loads((run/'actions.jsonl').read_text().splitlines()[-1]);assert entry['tests']==[0,0,102 if name=='install' else 100],entry

def audit(name):
 action('audit');path=sorted((evidence/'audit-attempts').glob(args.db+'-*.json'))[-1];value=json.loads(path.read_text())
 (evidence/(name+'-'+args.db+'.json')).write_text(json.dumps(value,indent=2)+'\n');return value

def browser(phase):
 if phase!='C':action('preview')
 before=audit('before-browser-'+phase)
 proc=subprocess.Popen([str(PYTHON),str(ROOT/'scripts/s08c.py'),'serve','--db',args.db,'--port',str(args.port)],cwd=ROOT,start_new_session=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(120):
   assert proc.poll() is None,'dedicated preview exited before ready'
   try:urllib.request.urlopen('http://127.0.0.1:'+str(args.port)+'/web/login',timeout=1).close();break
   except (OSError,TimeoutError):time.sleep(.25)
  else:raise AssertionError('dedicated preview readiness timeout')
  name={'A':'s08c_a_browser.py','B':'s08c_browser.py','R':'s08c_rework_browser.py','C':'s08c_print_browser.py'}[phase]
  parameters=['--db',args.db,'--port',args.port]
  if phase=='A':parameters+=['--terminal-races']
  command(name,*parameters)
 finally:
  metadata=json.loads((run/'database.json').read_text());conf=(run/'odoo.conf').resolve()
  assert hashlib.sha256(conf.read_bytes()).hexdigest()==metadata['config_sha256']
  stop={'phase':phase,'config_sha256':metadata['config_sha256']}
  if proc.poll() is None:
   pid=int((run/'serve.pid').read_text());assert str(conf).encode() in Path('/proc/'+str(pid)+'/cmdline').read_bytes().split(b'\0')
   os.kill(pid,signal.SIGTERM);stop['pid']=pid;stop['exit_code']=proc.wait(timeout=30)
  else:stop['exit_code']=proc.returncode;stop['unexpected_early_exit']=True
  record['preview_stops'].append(stop);save();assert stop['exit_code']==0 and not stop.get('unexpected_early_exit'),stop
 after=audit('after-browser-'+phase)
 if phase in ('A','C'):
  tables=list(before['signatures'])
  if phase=='A':
   tables=[t for t in tables if t not in ('ydental_clinical_document','ydental_clinical_version','ydental_queue_execution','ydental_intake_task','ydental_queue_entry','ydental_queue_lease','ydental_queue_outbox','bus_bus')]
  else:tables.remove('ydental_print_job')
  assert all(before['signatures'][t]==after['signatures'][t] for t in tables),(phase,'economic or source mutation')
  assert before['capacity_totals']==after['capacity_totals']
  record['pure_'+phase+'_signatures']={'result':'PASS','tables':tables,'before':'before-browser-'+phase+'-'+args.db+'.json','after':'after-browser-'+phase+'-'+args.db+'.json'};save()
 return after

try:
 action('install');action('upgrade');command('test_s08c_guard.py')
 action('probe_a');action('probe');action('probe_c')
 probe_file=sorted((evidence/'probe-attempts').glob('*/result.json'))[-1];probe=json.loads(probe_file.read_text());assert probe['database']==args.db and probe['result']=='PASS' and len(probe['races'])==5 and len(probe['artifacts'])==15
 command('s08c_render_pages.py',probe_file.relative_to(ROOT))
 action('export');command('s08c_translation.py','--db',args.db)
 for phase in ('A','B','R','C'):last=browser(phase)
 before=audit('before-business-upgrade');action('upgrade');after=audit('after-business-upgrade')
 assert before['signatures']==after['signatures'] and before['capacity_totals']==after['capacity_totals'],'committed business upgrade changed source signatures'
 record['business_upgrade']={'result':'PASS','tables':list(after['signatures']),'all_equal':True}
 record['result']='PASS'
except Exception as error:
 import traceback
 record['result']='FAIL';record['failure']={'type':type(error).__name__,'detail':str(error)[:1000],'trace':traceback.format_exc()}
finally:
 record['finished_utc']=datetime.now(timezone.utc).isoformat();save();print(json.dumps({'result':record['result'],'database':args.db,'commands':len(record['commands'])}),flush=True)
assert record['result']=='PASS',record.get('failure')
