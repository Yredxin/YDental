"""Real independent PostgreSQL print races and committed Chinese demo PDFs."""
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import threading
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import psycopg2
from odoo import api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.ydental_treatment_test.tests.common import bind, key, save_args, handover_args, lease_args, serving
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual, prescription, receive, pharmacy_start, price, distinct_medicine
from odoo.addons.ydental_clinical.models.ydental_clinical_service import TEETH

run=Path(os.environ['YDENTAL_S08C_RUN_DIR']);root=Path(__file__).resolve().parents[1]
assert run.name==env.cr.dbname and re.fullmatch('ydental_s08c_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
folder=root/'docs/evidence/s08c/probe-attempts'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f');folder.mkdir(parents=True)
result={'database':env.cr.dbname,'tested_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'races':[],'deadlocks':0,'artifacts':[]}

def fixtures(cr):
 f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
 for user in (f.users['doctor'],f.second):f.admin._grant(user.id,f.stores[0].id,{'export':'write'})
 f.admin._grant(f.pharmacist.id,f.stores[0].id,{'export':'write'})
 s,c,q,l,e,d,a=opened_actual(f);p=c.env['ydental.print.service'].with_context(lang='zh_CN')
 return f,s,c,q,l,e,d,a,p

def economy(cr):
 names=['ydental_treatment_event','ydental_treatment_fee','ydental_treatment_consumption','ydental_treatment_order','ydental_treatment_line','ydental_inventory_event','stock_move','stock_move_line','stock_quant','ydental_intake_snapshot']
 signatures={}
 for table in names:
  cr.execute('SELECT COALESCE(jsonb_agg(to_jsonb(t) ORDER BY id),\'[]\'::jsonb)::text FROM '+table+' t')
  signatures[table]=hashlib.sha256(cr.fetchone()[0].encode()).hexdigest()
 return signatures

def pdf(p,selection,name):
 p.env.flush_all();before=economy(p.env.cr);preview=p._operate('preview',selection)
 job=p._operate('generate',selection|{'expected_digest':preview['source_digest'],'key':key()})
 binary,signature=p._operate('download',{'job_id':job['job_id']})
 p._operate('pdf_view',{'job_id':job['job_id']});p._operate('print_request',{'job_id':job['job_id']})
 assert binary.startswith(b'%PDF-') and hashlib.sha256(binary).hexdigest()==signature
 assert economy(p.env.cr)==before,'PDF changed economic source tables'
 path=folder/(name+'.pdf');path.write_bytes(binary)
 payload=p._source(**selection)[3]
 result['artifacts'].append({'path':str(path.relative_to(root)),'sha256':signature,'job_id':job['job_id'],'source':selection,'versions':job['versions'],'source_digest':job['source_digest'],'fields':payload,'economic_signatures':before})
 return job

def race(kind):
 with env.registry.cursor() as cr:
  f,s,c,q,l,e,d,a,p=fixtures(cr);sel={'kind':'clinical','source_id':d['document_id'],'version':d['version']}
  preview=p._operate('preview',sel);args=sel|{'expected_digest':preview['source_digest'],'key':key()}
  context=dict(p.env.context);uid=p.env.uid;admin_context=dict(f.admin.env.context);admin_uid=f.admin.env.uid
  save=save_args(d,'并发来源新版本正文');docid=d['document_id'];oldversion=d['version'];f.env.flush_all();before=economy(cr)
  if kind=='repeated_print':
   generated=p._operate('generate',args);args={'job_id':generated['job_id']}
  cr.commit()
 barrier=threading.Barrier(2,timeout=20);render_enter=threading.Event();writer_commit=threading.Event()
 traces=[[],[]];record={'case':kind,'trace':traces};result['races'].append(record)
 original=type(env['ir.actions.report'])._run_wkhtmltopdf
 def render(reports,arguments):
  if kind=='generate_during_source_save' and not render_enter.is_set():
   render_enter.set();assert writer_commit.wait(20),'source writer did not commit during render'
  return original(reports,arguments)
 def worker(index):
  initial=None;retries=[]
  for attempt in range(6):
   try:
    with env.registry.cursor() as cr:
     cr.execute('SET LOCAL lock_timeout=\'15s\'');cr.execute('SELECT pg_backend_pid()');pid=cr.fetchone()[0]
     if initial is None:initial=pid
     traces[index].append({'event':'connected','attempt':attempt,'pid':pid,'time_ns':time.monotonic_ns()})
     if attempt==0:
      traces[index].append({'event':'barrier_enter','time_ns':time.monotonic_ns()});barrier.wait();traces[index].append({'event':'barrier_exit','time_ns':time.monotonic_ns()})
     service=api.Environment(cr,uid,context)['ydental.print.service']
     try:
      if kind=='generate_during_source_save' and index==1:
       assert render_enter.wait(20),'generation did not enter native render'
       value=service.env['ydental.clinical.service']._operate('save',save)
      elif kind=='generate_vs_revoke' and index==1:
       admin=api.Environment(cr,admin_uid,admin_context)['ydental.access.service'];admin._grant(uid,f.stores[0].id,{'export':'none'});value={}
      elif kind=='preview_vs_handover' and index==1:
       value=service.env['ydental.clinical.service']._operate('handover',handover_args(d,l))
      elif kind=='repeated_print':
       binary,signature=service._operate('print_request',args);value={'pdf_digest':signature,'size':len(binary)}
      else:
       value=service._operate('preview' if kind=='preview_vs_handover' else 'generate',args if kind!='preview_vs_handover' else sel)
       value.pop('html',None)
      cr.commit();traces[index].append({'event':'commit','time_ns':time.monotonic_ns()})
      if kind=='generate_during_source_save' and index==1:writer_commit.set()
      return {'result':'accepted','initial_backend_pid':initial,'final_backend_pid':pid,'retries':retries,'data':value}
     except (AccessError,UserError,ValidationError) as error:
      cr.rollback();return {'result':'rejected','initial_backend_pid':initial,'final_backend_pid':pid,'retries':retries,'code':str(error).split(':')[0]}
   except psycopg2.errors.SerializationFailure:
    retries.append('serialization_retry');traces[index].append({'event':'serialization_retry','time_ns':time.monotonic_ns()});time.sleep(.01*(attempt+1))
   except psycopg2.errors.DeadlockDetected:
    result['deadlocks']+=1;raise
  raise AssertionError('bounded retries exhausted')
 with patch.object(type(env['ir.actions.report']),'_run_wkhtmltopdf',render),ThreadPoolExecutor(max_workers=2) as pool:
  tasks=[pool.submit(worker,i) for i in range(2)];outcomes=[t.result(timeout=65) for t in tasks]
 record['outcomes']=outcomes
 assert outcomes[0]['initial_backend_pid']!=outcomes[1]['initial_backend_pid']
 states=[o['result'] for o in outcomes]
 if kind in ('generate_same_key','repeated_print','generate_during_source_save'):assert states==['accepted','accepted'],outcomes
 if kind=='generate_same_key':assert outcomes[0]['data']['job_id']==outcomes[1]['data']['job_id']
 if kind=='generate_vs_revoke':assert states[1]=='accepted' and states[0] in ('accepted','rejected')
 if kind=='preview_vs_handover':assert states==['accepted','accepted']
 with env.registry.cursor() as cr:
  assert economy(cr)==before,'read/PDF race changed economic tables'
  r=api.Environment(cr,1,{})
  if kind=='generate_during_source_save':
   assert r['ydental.clinical.document'].browse(docid).ydental_version==oldversion+1
   job=r['ydental.print.job'].browse(outcomes[0]['data']['job_id']);assert job.ydental_versions['document'][1]==oldversion
   try:api.Environment(cr,uid,context)['ydental.print.service']._operate('download',{'job_id':job.id})
   except UserError:pass
   else:raise AssertionError('changed source job was delivered')
 record['result']='PASS'

try:
 for name in ('generate_same_key','generate_during_source_save','generate_vs_revoke','preview_vs_handover','repeated_print'):race(name)
 with env.registry.cursor() as cr:
  f,s,c,q,l,e,d,a,p=fixtures(cr)
  f.stores[0].write({'name':'S08-C PDF 合成门店甲'})
  e.ydental_patient_id._save({'name':'S08-C 合成患者（非真人）'})
  f.users['doctor'].write({'name':'合成医师甲 D1'});f.second.write({'name':'合成医师乙 D2'})
  payload=save_args(d,'D1合成主诉：独立原始作者与待完善责任。')
  payload['content']['history']='合成长病史段落，中文换页核对；不代表真实医学结论。'*320
  payload['content']['teeth']=[{'tooth':t,'state':'unknown' if t==51 else 'missing' if t==48 else 'present','surfaces':['O'] if t==16 else []} for t in TEETH]+[{'tooth':0,'state':'not_applicable','surfaces':[]}]
  d.update(c._operate('save',payload));a['document_version']=d['version']
  sel={'kind':'clinical','source_id':d['document_id'],'version':d['version']};pdf(p,sel,'clinical-d1-long-draft')
  pdf(p,sel|{'kind':'consent'},'consent-unsigned-unreviewed')
  # Incomplete prescriptions stay honest drafts, never issue without real fields.
  draft=s._operate('order',a|{'kind':'prescription','purpose':'合成不完整草稿','lines':[{'mapping_id':f.drug_mapping.id,'quantity':6,'uom_id':f.uom.id,'product_id':f.products['medicine'],'specification':'','usage':'','frequency':'','course':''}]},key())
  rx={'kind':'prescription','source_id':draft['order_id'],'version':draft['version']};pdf(p,rx,'prescription-incomplete-draft')
  receive(f,20,'medicine');price(f,catalog=f.drug_catalog,amount=10)
  order=prescription(f,s,a);rx={'kind':'prescription','source_id':order['order_id'],'version':order['version']};pdf(p,rx,'prescription-six-uncollected')
  hand=c._operate('handover',handover_args(d,l));d.update(hand);sel['version']=d['version'];pdf(p,sel,'clinical-d1-pending')
  q._operate('exit',lease_args(l))
  pharm,pa=pharmacy_start(f,order)
  dose=pa|{'line_id':order['line_ids'][0],'lot_id':f.lots['medicine'],'quantity':4,'source':key(),'reason':'合成四份真实发放','policy':'demo_confirmation'}
  pharm._operate('dispense',dose,key());pdf(p,rx,'prescription-four-dispensed-two-left')
  finished=pharm._operate('finish',pa|{'reason':'合成第一段结束'},key())
  pharm,pa2=pharmacy_start(f,order,finished['next_task_id']);pharm._operate('dispense',dose|pa2|{'quantity':2,'source':key()},key());pharm._operate('finish',pa2|{'reason':'合成第二段结束'},key());pdf(p,rx,'prescription-six-dispensed-zero-left')
  # Real continuation creates an independent D2; do not merge or substitute D1.
  task=f.root['ydental.intake.task'].browse(hand['continuation_task_id']);f.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
  q2,l2,e2=serving(f,user=f.second,station=f.other_station,task=task);c2=q2.env['ydental.clinical.service']
  d2=c2._operate('open',{'execution_id':e2.id,'lease_id':l2['lease_id'],'lease_token':l2['token']});d2.update(c2._operate('confirm',save_args(d2,'D2独立确认内容，仅属于合成医师乙。')))
  p2=c2.env['ydental.print.service'].with_context(lang='zh_CN');pdf(p2,{'kind':'clinical','source_id':d2['document_id'],'version':d2['version']},'clinical-d2-confirmed-independent')
  old=d2['version'];d2.update(c2._operate('correct',save_args(d2,'D2附原因更正后内容。')|{'reason':'合成文字核对更正'}))
  pdf(p2,{'kind':'clinical','source_id':d2['document_id'],'version':old},'clinical-d2-historical-confirmed')
  pdf(p2,{'kind':'clinical','source_id':d2['document_id'],'version':d2['version']},'clinical-d2-corrected')
  # Credentials only in the private run, never in evidence.
  creds={}
  for role,user in [('doctor',f.users['doctor']),('doctor2',f.second),('pharmacy',f.pharmacist),('reader',f.users['reader']),('manager',f.users['manager'])]:
   password=secrets.token_urlsafe(24);user.write({'password':password,'lang':'zh_CN'});creds[role]={'login':user.login,'password':password}
  ui={'store':f.stores[0].id,'other_store':f.stores[1].id,'clinical':{'kind':'clinical','source_id':d['document_id'],'version':d['version']},'d2':{'kind':'clinical','source_id':d2['document_id'],'version':d2['version']},'prescription':rx,'consent':sel|{'kind':'consent'},'doctor':f.users['doctor'].id}
  cr.commit()
  for filename,value in [('print-access.json',creds),('print-preview.json',ui)]:
   with os.fdopen(os.open(run/filename,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as handle:json.dump(value,handle)
 result['result']='PASS'
except Exception as error:
 result['result']='FAIL';result['failure']={'type':type(error).__name__,'detail':str(error)[:1500],'trace':traceback.format_exc()}
finally:
 (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'result':result['result'],'races':len(result['races']),'artifacts':len(result['artifacts']),'deadlocks':result['deadlocks']}))
assert result['result']=='PASS',result.get('failure')
