"""Run two guarded Odoo shells against distinct PostgreSQL backends at one barrier."""
import argparse,configparser,hashlib,json,os,re,subprocess,sys
from pathlib import Path
import psycopg2
root=Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons');core=root.parent
p=argparse.ArgumentParser();p.add_argument('--db',required=True);p.add_argument('--sha',required=True);args=p.parse_args()
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}',args.db)
assert re.fullmatch(r'[a-f0-9]{40}',args.sha)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==args.sha
run=root/'.local'/args.db;marker=json.loads((run/'database.json').read_text())
assert marker['database']==args.db and marker['cluster']=='7694897083368259627'
assert hashlib.sha256((run/'odoo.conf').read_bytes()).hexdigest()==marker['config_sha256']
assert not list(run.glob('crash-*.json'))
actions=[json.loads(x) for x in (run/'actions.jsonl').read_text().splitlines()]
assert all(x['signal'] is None for x in actions)
fixture=json.loads((run/'concurrency-fixture.json').read_text());assert fixture['fee_id']>0
assert not list(run.glob('barrier-*.json'))
config=configparser.ConfigParser(interpolation=None);config.read(run/'odoo.conf')
assert config['options']['db_name']==args.db
script=(root/'scripts/s10_completion/concurrency_actor.py').read_text()
script_sha=hashlib.sha256(script.encode()).hexdigest()
base_env=os.environ.copy();deps=root/'.local/s00-b-deps'
base_env.update({'PATH':str(deps/'wkhtmltox/usr/local/bin')+os.pathsep+os.environ.get('PATH',''),
    'PYTHONPATH':str(run/'network-policy')+os.pathsep+str(root/'.local/s04-deps'),
    'YDENTAL_S10_RUN_DIR':str(run),'YDENTAL_S08C_HTTP_PORT':str(marker['port']),
    'PYTHONFAULTHANDLER':'1','PYTHONDONTWRITEBYTECODE':'1',
    'PGOPTIONS':'-c max_parallel_workers_per_gather=0 -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=16384'})
children=[]
for actor in ('a','b'):
 cmd=[str(core/'.venv/bin/python'),str(core/'odoo-bin'),'shell','-c',str(run/'odoo.conf'),'--no-http']
 log=run/('concurrent-'+actor+'.log');stream=log.open('x')
 proc=subprocess.Popen(cmd,cwd=core,env=base_env|{'YDENTAL_S10_ACTOR':actor},stdin=subprocess.PIPE,stdout=stream,stderr=subprocess.STDOUT,text=True)
 children.append((actor,proc,stream,log,cmd))
for _actor,proc,_stream,_log,_cmd in children:
 proc.stdin.write(script)
 proc.stdin.close()
for actor,proc,stream,log,cmd in children:
 try:proc.wait(timeout=180)
 except subprocess.TimeoutExpired:
  proc.terminate();proc.wait(timeout=15)
 stream.close()
 record={'actor':actor,'pid':proc.pid,'exit_code':proc.returncode,'signal':-proc.returncode if proc.returncode<0 else None,
  'command':cmd,'script_sha256':script_sha,'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest(),
  'database':args.db,'oid':marker['oid']}
 with (run/'concurrent-actions.jsonl').open('a') as out:out.write(json.dumps(record)+'\n')
 if proc.returncode<0 or proc.returncode==139:(run/('crash-'+str(proc.pid)+'.json')).write_text(json.dumps(record)+'\n')
 print(json.dumps(record),flush=True)
assert all(proc.returncode==0 for _,proc,*_ in children)
a=json.loads((run/'concurrent-a.json').read_text());b=json.loads((run/'concurrent-b.json').read_text())
assert a['backend_pid']!=b['backend_pid']
assert all(x['outcome'] in ('accepted','conflict') for x in (a,b))
accepted=next(x for x in (a,b) if x['outcome']=='accepted')
assert accepted['amount']==100
for x in (a,b):
 if x['outcome']=='accepted':assert x['invoice_id']==accepted['invoice_id'] and x['amount']==100
with psycopg2.connect(host='127.0.0.1',port=5432,user='odoo',password=config['options']['db_password'],dbname=args.db) as conn:
 conn.set_session(readonly=True)
 with conn.cursor() as cr:
  cr.execute('select count(*) from ydental_settlement_source where ydental_fee_id=%s',(fixture['fee_id'],));assert cr.fetchone()[0]==1
  cr.execute('select deadlocks from pg_stat_database where datname=%s',(args.db,));assert cr.fetchone()[0]==0
print('S10_TWO_BACKEND_BILL_PASS',json.dumps({'backend_pids':[a['backend_pid'],b['backend_pid']],'invoice_id':accepted['invoice_id'],'fee_id':fixture['fee_id'],'source_count':1,'outcomes':[a['outcome'],b['outcome']]}),flush=True)
