"""Committed fixtures and real two-backend races in the guarded S08-B database."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import threading
import time
import traceback
from types import SimpleNamespace

import psycopg2
from odoo import api
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.ydental_treatment_test.tests.common import setup, opened, save_args, handover_args, key, accepted, queue_bind, lease_args

run=Path(os.environ['YDENTAL_S08B_RUN_DIR'])
assert run.name==env.cr.dbname and re.fullmatch(r'ydental_s08b_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname)
result={'database':env.cr.dbname,'races':[],'failures':[],'deadlocks':0}
env.cr.execute('SELECT name,setting FROM pg_settings WHERE name=ANY(%s)', [
    ['max_parallel_workers_per_gather','max_parallel_maintenance_workers','maintenance_work_mem']])
result['session_settings']=dict(env.cr.fetchall())
assert result['session_settings']=={'max_parallel_workers_per_gather':'0','max_parallel_maintenance_workers':'0','maintenance_work_mem':'16384'}

root=Path(__file__).resolve().parents[1]
import subprocess
result['tested_commit']=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()

def legacy_final_pid_assertion(outcomes):
    # Re-execute only the old diagnostic predicate (1bec52a script line 79).
    # Its failure is evidence of an invalid pool-identity check, not permission
    # to ignore any business invariant or the initial two-backend barrier.
    assert outcomes[0]['backend_pid']!=outcomes[1]['backend_pid']

def fixture(kind):
    with env.registry.cursor() as cr:
        f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
        # Explicit synthetic values only; long enough for thread/barrier orchestration.
        f.root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds','600')
        if kind=='queue_start':
            task=accepted(f);q=queue_bind(f);l=q._operate('enter',{'station_id':f.stations[0][0].id})
            called=q._operate('call',lease_args(l));a=lease_args(l)|{'entry_id':called['entry_id']}
            cr.commit()
            return q.env.uid,[dict(q.env.context)]*2,[('start',a)]*2,0,task.id
        s,q,l,e,d=opened(f)
        if kind in ('editors','transfer'):
            r=s._operate('handover',handover_args(d,l));d.update(version=r['version'])
        contexts=[dict(s.env.context),dict(s.env.context)];uid=s.env.uid
        if kind=='editors':
            contexts[1]=dict(q._bind_connection(key()+key()).env.context)
            jobs=[('acquire',{'document_id':d['document_id']})]*2
        elif kind=='versions':
            jobs=[('save',save_args(d,'Synthetic racer A')),('save',save_args(d,'Synthetic racer B'))]
        elif kind=='handover_save':
            jobs=[('handover',handover_args(d,l)),('save',save_args(d,'Concurrent save'))]
        elif kind=='continuation':
            a=handover_args(d,l);jobs=[('handover',a),('handover',a)]
        elif kind=='old_new_editor':
            s._operate('release',{'document_id':d['document_id'],'editor_token':d['editor_token']})
            jobs=[('save',save_args(d)),('acquire',{'document_id':d['document_id'],'lease_id':l['lease_id'],'lease_token':l['token']})]
        elif kind=='rollback':
            jobs=[('handover',handover_args(d,l)|{'mapping_id':f.mappings[0][2].id}),('save',save_args(d,'Survives failed handover'))]
        elif kind=='transfer':
            a={'document_id':d['document_id'],'expected_version':d['version'],'user_id':f.second.id,'reason':'Synthetic responsibility race'}
            jobs=[('transfer',a),('transfer',a)]
        cr.commit() # Dedicated fixture cursor, never a business transaction.
        return uid,contexts,jobs,d['document_id'],e.id

def race(kind,round_number):
    record={'case':kind,'round':round_number,'result':'RUNNING','worker_traces':[[],[]]}
    result['races'].append(record) # Preserve the failed case, not only completed races.
    uid,contexts,jobs,doc_id,execution_id=fixture(kind)
    record.update(document_id=doc_id,execution_id=execution_id)
    barrier=threading.Barrier(2,timeout=20)
    # Reproduce the legal LIFO pool reuse after the original eighth race.
    # Initial business requests still overlap on two independent backends.
    reuse_probe=kind=='continuation' and round_number==2
    loser_released=threading.Event();winner_released=threading.Event()
    record['controlled_retry_pool_reuse']=reuse_probe
    def worker(index):
        attempts=[];pid=None;initial_pid=None;backend_trace=[]
        def trace(event):
            record['worker_traces'][index].append({'event':event,'attempt':attempt,'backend_pid':pid,'monotonic_ns':time.monotonic_ns()})
        for attempt in range(6):
            accepted_attempt=False;retry_attempt=False
            try:
                with env.registry.cursor() as cr:
                    cr.execute('SET LOCAL lock_timeout = %s',['12s']);cr.execute('SELECT pg_backend_pid()');pid=cr.fetchone()[0]
                    backend_trace.append(pid)
                    if attempt==0:initial_pid=pid
                    trace('backend_connected')
                    try:
                        if attempt==0:
                            trace('barrier_enter');barrier.wait();trace('barrier_exit')
                        s=api.Environment(cr,uid,contexts[index])['ydental.queue.service' if kind=='queue_start' else 'ydental.clinical.service']
                        trace('operate_begin')
                        data=s._operate(*jobs[index]);cr.commit()
                        trace('accepted_commit')
                        accepted_attempt=True
                        if reuse_probe:
                            assert loser_released.wait(20),'Loser cursor did not release'
                        return {'result':'accepted','backend_pid':pid,'initial_backend_pid':initial_pid,'backend_pid_trace':backend_trace,'attempts':attempts,'version':data.get('version')}
                    except psycopg2.errors.SerializationFailure:
                        trace('serialization_retry')
                        retry_attempt=True
                        attempts.append('serialization_retry');cr.rollback()
                        time.sleep(0.01*(attempt+1))
                    except psycopg2.errors.DeadlockDetected:
                        trace('deadlock')
                        result['deadlocks']+=1
                        return {'result':'deadlock','backend_pid':pid,'initial_backend_pid':initial_pid,'backend_pid_trace':backend_trace,'attempts':attempts}
                    except (AccessError,UserError,ValidationError) as error:
                        trace('business_rejected')
                        cr.rollback();return {'result':'rejected','backend_pid':pid,'initial_backend_pid':initial_pid,'backend_pid_trace':backend_trace,'attempts':attempts,'code':str(error).split(':')[0]}
            finally:
                trace('cursor_released')
                if reuse_probe and accepted_attempt:
                    winner_released.set()
                elif reuse_probe and retry_attempt:
                    loser_released.set()
                    assert winner_released.wait(20),'Winner cursor did not release'
        return {'result':'retry_exhausted','backend_pid':pid,'initial_backend_pid':initial_pid,'backend_pid_trace':backend_trace,'attempts':attempts}
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(worker,i) for i in range(2)]; outcomes=[f.result(timeout=100) for f in futures]
    record['outcomes']=outcomes
    record['legacy_final_pid_distinct']=outcomes[0]['backend_pid']!=outcomes[1]['backend_pid']
    if reuse_probe:
        assert not record['legacy_final_pid_distinct'],('Controlled reuse was not reproduced',outcomes)
        assert any('serialization_retry' in x['attempts'] for x in outcomes),outcomes
    try:
        legacy_final_pid_assertion(outcomes)
        record['legacy_predicate_diagnostic']={'result':'PASS'}
    except AssertionError as error:
        record['legacy_predicate_diagnostic']={'result':'FAIL_REPRODUCED',
            'original_predicate':'1bec52a:scripts/s08b_probe.py:79',
            'trace':[{'file':Path(frame.filename).name,'line':frame.lineno,'method':frame.name}
                     for frame in traceback.extract_tb(error.__traceback__)]}
    # The first cursors overlap at the barrier. A retry may legitimately borrow
    # the winner's now-idle pooled backend; comparing final PIDs is insufficient.
    assert outcomes[0]['initial_backend_pid']!=outcomes[1]['initial_backend_pid'],(kind,outcomes)
    assert sorted(x['result'] for x in outcomes)==['accepted','rejected'],(kind,outcomes)
    with env.registry.cursor() as cr:
        r=api.Environment(cr,1,{})
        if kind=='queue_start':
            assert r['ydental.queue.execution'].search_count([('ydental_task_id','=',execution_id)])==1
            record['result']='PASS'
            return
        doc=r['ydental.clinical.document'].browse(doc_id);e=r['ydental.queue.execution'].browse(execution_id)
        versions=r['ydental.clinical.version'].search([('ydental_document_id','=',doc_id)])
        successors=r['ydental.intake.task'].search_count([('ydental_source_execution_id','=',execution_id)])
        assert successors<=1
        assert len(versions)==doc.ydental_version
        if kind=='rollback':assert e.state=='serving' and successors==0 and doc.ydental_content['chief_complaint']=='Survives failed handover'
        if kind=='continuation':assert successors==1 and e.state=='handover' and not doc.ydental_editor_id
        if kind=='versions':assert doc.ydental_version==1
        if kind=='transfer':assert doc.ydental_responsible_id.id!=uid
    record.update(result='PASS',single_continuation=successors)

try:
    for kind in ('versions','editors','handover_save','continuation','old_new_editor','rollback','transfer','queue_start'):
        for round_number in range(2):race(kind,round_number+1)
    result['result']='PASS'
except Exception as error:
    result['result']='FAIL';result['failures'].append({'type':type(error).__name__,'detail':str(error)[:1000],'trace':[{'file':Path(frame.filename).name,'line':frame.lineno,'method':frame.name} for frame in traceback.extract_tb(error.__traceback__)]})
finally:
    target=root/'docs/evidence/s08b/probe-attempts';target.mkdir(parents=True,exist_ok=True)
    (target/(run.name+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'result':result['result'],'races':len(result['races']),'deadlocks':result['deadlocks']}))
assert result['result']=='PASS',result['failures']
