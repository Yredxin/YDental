"""Committed real B sources and overlapping initial PostgreSQL backends."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import threading
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import psycopg2
from odoo import api, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.ydental_treatment_test.tests.common import key, price, handover_args, bind, qualify, queue_bind, lease_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args, prescription, pharmacy_start

run=Path(os.environ['YDENTAL_S08B_RUN_DIR'])
assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s08b_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
root=Path(__file__).resolve().parents[1]
result={'database':env.cr.dbname,'tested_commit':subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip(),'races':[],'deadlocks':0,'failures':[]}

def job(service,operation,args,request=None):
    return {'uid':service.env.uid,'context':dict(service.env.context),'model':service._name,'operation':operation,'payload':args,'key':request or key()}

def fixture(kind):
    with env.registry.cursor() as cr:
        f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
        s,c,q,l,e,d,a=opened_actual(f)
        info={'patient_id':e.ydental_patient_id.id,'execution_id':e.id,'store_id':e.ydental_store_id.id,'kind':kind,'sources':[]}
        if kind.startswith('dispense') or kind.startswith('finish') or kind in ('restore_vs_pharmacy_start','two_pharmacy_stations_call'):
            receive(f,20,'medicine');price(f,catalog=f.drug_catalog,amount=10)
            issued=prescription(f,s,a);info.update(order_id=issued['order_id'],line_id=issued['line_ids'][0])
            if kind=='two_pharmacy_stations_call':
                from odoo.tests import new_test_user
                c._operate('handover',handover_args(d,l))
                task=f.root['ydental.intake.task'].browse(issued['task_ids'][0]);f.front._operate('arrive',{'patient_id':task.ydental_patient_id.id},key());f.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
                second=new_test_user(f.root,name='Synthetic second pharmacist',login='s08b_second_pharm_'+key(),groups='ydental_base.ydental_base_group_user')
                f.admin._join(second.id,f.stores[0].id);f.admin._grant(second.id,f.stores[0].id,{'pharmacy':'write'})
                second.write({'ydental_capability_ids':[fields.Command.set(f.capabilities[0].ids)]})
                station=f.pharmacy_station.copy({'name':'Synthetic second pharmacy station'})
                one=queue_bind(f,f.pharmacist);one_lease=one._operate('enter',{'station_id':f.pharmacy_station.id})
                two=queue_bind(f,second);two_lease=two._operate('enter',{'station_id':station.id})
                jobs=[job(one,'call',lease_args(one_lease)),job(two,'call',lease_args(two_lease))]
            elif kind=='restore_vs_pharmacy_start':
                hold=q._operate('reserve',lease_args(l)|{'execution_id':e.id,'target_task_id':issued['task_ids'][0]})
                task=f.root['ydental.intake.task'].browse(issued['task_ids'][0]);f.front._operate('arrive',{'patient_id':task.ydental_patient_id.id},key());f.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
                pq=queue_bind(f,f.pharmacist);pl=pq._operate('enter',{'station_id':f.pharmacy_station.id});called=pq._operate('call',lease_args(pl))
                jobs=[job(q,'restore',lease_args(l)|{'hold_id':hold['hold_id'],'confirmed':True}),job(pq,'start',lease_args(pl)|{'entry_id':called['entry_id']})]
            else:
                c._operate('handover',handover_args(d,l));p,pa=pharmacy_start(f,issued)
                dose=pa|{'line_id':issued['line_ids'][0],'lot_id':f.lots['medicine'],'quantity':4,'source':key(),'reason':'Synthetic competing actual issue','policy':'demo_confirmation'}
                if kind.startswith('finish'):
                    p._operate('dispense',dose,key());finish=pa|{'reason':'Actual dispensing segment ended'}
                    k=key();jobs=[job(p,'finish',finish,k),job(p,'finish',finish,k if kind=='finish_same_key' else None)]
                else:
                    second=dict(dose)
                    if kind=='dispense_distinct_four':second['source']=key()
                    jobs=[job(p,'dispense',dose),job(p,'dispense',second)];info['sources']=[dose['source'],second['source']]
        elif kind.startswith('referral') or kind=='timed_last_capacity' or kind=='untimed_accept':
            target=f.mappings[1][0]
            args=a|{'mode':'timed','mapping_id':target.id,'reason':'Synthetic real clinical referral',
                'start':fields.Datetime.to_string(f.start),'end':fields.Datetime.to_string(f.end),'source':key()}
            if kind=='timed_last_capacity':
                front=bind(f,f.users['frontdesk'],f.stores[1])
                for i in range(3):qualify(f,mapping=target,service=front)
                second=dict(args,source=key());jobs=[job(s,'refer',args),job(s,'refer',second)]
            elif kind=='untimed_accept':
                args={k:v for k,v in args.items() if k not in ('start','end')};args.update(mode='untimed',valid_until=fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=1)))
                referral=s._operate('refer',args,key());front=bind(f,f.users['frontdesk'],f.stores[1])
                accept={'record_id':referral['id'],'version':referral['version'],'start':fields.Datetime.to_string(f.start),'end':fields.Datetime.to_string(f.end)}
                jobs=[job(front,'accept_referral',accept),job(front,'accept_referral',accept)]
            else:jobs=[job(s,'refer',args),job(s,'refer',args)]
            info['target_mapping_id']=target.id
        elif kind=='exam_cancel_vs_report':
            lines=[{'mapping_id':f.mappings[0][2].id,'quantity':1,'uom_id':f.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''}]
            draft=s._operate('order',a|{'kind':'exam','purpose':'Synthetic examination race','lines':lines},key());issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
            task=f.root['ydental.intake.task'].browse(issued['task_ids'][0]);args=a|{'line_id':issued['line_ids'][0],'order_version':issued['version'],'reason':'Declined before actual examination'}
            jobs=[job(s,'cancel_exam',args),job(f.front,'report',{'task_id':task.id,'version':task.ydental_version})];info['line_id']=issued['line_ids'][0]
        else:
            if kind!='missing_price_fact':price(f)
            if kind!='shortage_last_unit':receive(f)
            else:receive(f,1)
            args=execute_args(f,a,actual=kind in ('missing_price_fact','recover_original'))
            if kind=='recover_original':
                # Consume fixture stock without inventing an incoming correction.
                args['materials'][0]['quantity']=25
                pending=s._operate('execute',args,key());receive(f,30)
                f.stock._operate('recover',{'event_id':pending['inventory_event_ids'][0],'reason':'Evidenced correction of original pending fact'},key())
                rec={'event_id':pending['event_id'],'reason':'Concurrent recheck original clinical fact'}
                jobs=[job(s,'reconcile',rec),job(s,'reconcile',rec)];info['event_id']=pending['event_id']
            elif kind=='price_publish_vs_execute':
                old=f.root['ydental.intake.price'].search([('ydental_store_id','=',f.stores[0].id),('ydental_catalog_id','=',f.catalogs[0].id),('state','=','published')],limit=1)
                revised_at=fields.Datetime.now()+timedelta(seconds=20);info['clock_utc']=str(revised_at)
                revised=f.group._operate('price',{'catalog_id':f.catalogs[0].id,'currency_id':f.currency.id,'unit_price':999,'start':fields.Datetime.to_string(revised_at),'end':fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=30)),'reason':'Synthetic revised published quote'},key())
                revised=f.group._operate('review',{'record_id':revised['id'],'version':revised['version'],'reason':'Reviewed next quote'},key())
                jobs=[job(s,'execute',args),job(f.group,'publish',{'record_id':revised['id'],'version':revised['version'],'replace_id':old.id,'replace_version':old.ydental_version,'reason':'Publish changed price concurrently'})];info['sources']=[args['source']]
            elif kind=='revocation_vs_execute':
                jobs=[job(s,'execute',args),job(f.admin,'grant',{'user_id':f.users['doctor'].id,'store_id':f.stores[0].id,'levels':{'medical':'read'}})];info['sources']=[args['source']]
            else:
                second=dict(args)
                if kind in ('execute_changed','shortage_last_unit'):second['source']=key() if kind=='shortage_last_unit' else args['source'];second['quantity']=2 if kind=='execute_changed' else 1
                if kind=='old_lease':second['lease_token']='invalid'
                jobs=[job(s,'execute',args),job(s,'execute',second)];info['sources']=[args['source'],second['source']]
        cr.commit() # This function owns the fixture cursor; product actions never commit.
        return jobs,info

def race(kind,round_number):
    jobs,info=fixture(kind);record={'case':kind,'round':round_number,'result':'RUNNING','trace':[[],[]],'identities':info};result['races'].append(record)
    barrier=threading.Barrier(2,timeout=25)
    def worker(index):
        trace=record['trace'][index];initial=None;attempts=[]
        for attempt in range(6):
            try:
                with env.registry.cursor() as cr:
                    cr.execute('SET LOCAL lock_timeout=%s',['15s']);cr.execute('SELECT pg_backend_pid()');pid=cr.fetchone()[0]
                    if initial is None:initial=pid
                    trace.append({'event':'connected','attempt':attempt,'pid':pid,'time_ns':time.monotonic_ns()})
                    if attempt==0:
                        trace.append({'event':'barrier_enter','time_ns':time.monotonic_ns()});barrier.wait();trace.append({'event':'barrier_exit','time_ns':time.monotonic_ns()})
                    j=jobs[index];service=api.Environment(cr,j['uid'],j['context'])[j['model']]
                    try:
                        if kind=='revocation_vs_execute' and index==1:data=service._grant(**j['payload']) or {}
                        elif j['model']=='ydental.queue.service':data=service._operate(j['operation'],j['payload'])
                        else:data=service._operate(j['operation'],j['payload'],j['key'])
                        cr.commit();trace.append({'event':'commit','time_ns':time.monotonic_ns()})
                        return {'result':'accepted','initial_backend_pid':initial,'final_backend_pid':pid,'attempts':attempts,'data':data if isinstance(data,dict) else {}}
                    except psycopg2.errors.SerializationFailure:
                        cr.rollback();attempts.append('serialization_retry');trace.append({'event':'serialization_retry','time_ns':time.monotonic_ns()})
                    except (AccessError,UserError,ValidationError) as error:
                        cr.rollback();return {'result':'rejected','initial_backend_pid':initial,'final_backend_pid':pid,'attempts':attempts,'code':str(error).split(':')[0]}
            except psycopg2.errors.DeadlockDetected:
                result['deadlocks']+=1
                raise
            time.sleep(0.01*(attempt+1))
        raise AssertionError('Bounded serialization retries exhausted')
    if kind=='native_move_failure':
        original=type(env['ydental.inventory.service'])._move
        def fail(service,event):
            original(service,event);raise UserError('native_move_failure: Injected after completed native move')
        context=patch.object(type(env['ydental.inventory.service']),'_move',fail)
    elif kind=='price_publish_vs_execute':
        context=patch.object(fields.Datetime,'now',return_value=fields.Datetime.to_datetime(info['clock_utc']))
    else:
        from contextlib import nullcontext
        context=nullcontext()
    with context,ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker,i) for i in range(2)];outcomes=[]
        for future in futures:
            try:outcomes.append(future.result(timeout=100))
            except Exception as error:
                outcomes.append({'result':'unexpected','type':type(error).__name__,'detail':str(error)[:500],
                    'trace':[{'file':Path(f.filename).name,'line':f.lineno,'method':f.name} for f in traceback.extract_tb(error.__traceback__)]})
    record['outcomes']=outcomes
    assert all('initial_backend_pid' in o for o in outcomes),outcomes
    assert outcomes[0]['initial_backend_pid']!=outcomes[1]['initial_backend_pid'],outcomes
    states=sorted(o['result'] for o in outcomes)
    both=('execute_same','missing_price_fact','recover_original','dispense_same_source','finish_same_key','referral_same_source','price_publish_vs_execute')
    if kind=='revocation_vs_execute':assert states in (['accepted','accepted'],['accepted','rejected']),outcomes
    else:assert states==(['accepted','accepted'] if kind in both else ['rejected','rejected'] if kind=='native_move_failure' else ['accepted','rejected']),(kind,states,outcomes)
    with env.registry.cursor() as cr:
        r=api.Environment(cr,1,{})
        unresolved=r['ydental.queue.execution'].search_count([('ydental_patient_id','=',info['patient_id']),('state','in',('serving','verify'))]);assert unresolved<=1
        if info['sources'] and not kind.startswith('dispense'):
            events=r['ydental.treatment.event'].search([('ydental_store_id','=',info['store_id']),('ydental_source','in',info['sources'])])
            assert len(events)==(0 if kind=='native_move_failure' or kind=='revocation_vs_execute' and outcomes[0]['result']=='rejected' else 1),(kind,events.ids)
            for event in events:
                fees=r['ydental.treatment.fee'].search([('ydental_event_id','=',event.id)])
                assert len(fees)==(0 if kind=='missing_price_fact' else 1)
                if kind=='price_publish_vs_execute':assert fees.ydental_unit_price in (600,999)
        if 'order_id' in info:
            segment=r['ydental.treatment.segment'].search([('ydental_order_id','=',info['order_id']),('state','in',('pending','active'))]);assert len(segment)<=1
            events=r['ydental.treatment.event'].search([('ydental_order_line_id','=',info['line_id'])]);assert sum(events.mapped('ydental_quantity'))<=6
            if kind.startswith('dispense'):assert sum(events.mapped('ydental_quantity'))==4 and len(events)==1
            if kind.startswith('finish'):
                assert len(segment)==1 and segment.ydental_task_id.state=='pending'
                assert not r['ydental.queue.entry'].search_count([('ydental_task_id','=',segment.ydental_task_id.id)])
        if kind=='exam_cancel_vs_report':assert r['ydental.treatment.line'].browse(info['line_id']).state=='cancelled'
        if kind=='untimed_accept':
            accepted=[o['data'] for o in outcomes if o['result']=='accepted'];assert accepted[0]['task_id']
    record['result']='PASS'

try:
    for kind in ('execute_same','execute_changed','old_lease','shortage_last_unit','missing_price_fact','recover_original',
        'native_move_failure','dispense_distinct_four','dispense_same_source','finish_same_key','finish_distinct_keys',
        'restore_vs_pharmacy_start','exam_cancel_vs_report','timed_last_capacity','untimed_accept','referral_same_source','price_publish_vs_execute','revocation_vs_execute','two_pharmacy_stations_call'):
        race(kind,1)
    result['result']='PASS'
except Exception as error:
    result['result']='FAIL';result['failures'].append({'type':type(error).__name__,'detail':str(error)[:1500],
        'trace':[{'file':Path(f.filename).name,'line':f.lineno,'method':f.name} for f in traceback.extract_tb(error.__traceback__)]})
finally:
    directory=root/'docs/evidence/s08b/probe-attempts';directory.mkdir(parents=True,exist_ok=True)
    (directory/(run.name+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'races':len(result['races']),'deadlocks':result['deadlocks']}))
assert result['result']=='PASS',result['failures']
