"""Independent PostgreSQL connections, controlled races, and synthetic UI fixtures."""
import atexit
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import runpy
import secrets
from threading import Barrier, Event
from types import SimpleNamespace
from unittest.mock import patch

import psycopg2
from odoo import api, fields
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_inventory_test.tests.common import setup, bind, key
from odoo.addons.ydental_inventory_test.models.adapter import SyntheticSource

run=Path(os.environ['YDENTAL_S07_RUN_DIR'])
assert re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}',env.cr.dbname) and run.name==env.cr.dbname
registry=env.registry
result={'scope':'S07 real native inventory with isolated synthetic sources','database':env.cr.dbname,'races':[],
    'started_utc':datetime.now(timezone.utc).isoformat(),'tested_commit':__import__('subprocess').check_output(['git','-C',str(Path(__file__).resolve().parents[1]),'rev-parse','HEAD'],text=True).strip()}
attempt=Path(__file__).resolve().parents[1]/'docs/evidence/s07-rework/probe-attempts'/(env.cr.dbname+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
attempt.parent.mkdir(parents=True,exist_ok=True)
def save():
    result.setdefault('result','FAIL_OR_INTERRUPTED');attempt.write_text(json.dumps(result,indent=2)+'\n')
atexit.register(save)
with registry.cursor() as cr:
    f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
    users={k:u.id for k,u in f.users.items()};store_ids=f.stores.ids;lots=dict(f.lots);products=dict(f.products);unit=f.uom.id;pack=f.pack.id
    sessions={role:[] for role in users}
    for role,uid in users.items():
        for n in range(2):sessions[role].append(bind(f,f.users[role]).env['ydental.access.service']._scope().id)
    # Random local-only preview passwords never enter public evidence.
    credentials={}
    for role,u in f.users.items():
        password=secrets.token_urlsafe(24);u.write({'password':password,'lang':'zh_CN'})
        credentials[role]={'login':u.login,'password':password}
    cr.commit() # Script owns this isolated fixture cursor.


def service(cr,role='stock',n=0):
    e=api.Environment(cr,users[role],{})
    return e['ydental.access.service']._bind(e['ydental.access.session'].sudo().browse(sessions[role][n])).env['ydental.inventory.service']
def fresh(fn,role='stock'):
    with registry.cursor() as cr:
        value=fn(service(cr,role));cr.commit();return value # Own cursor.
def action(s,op,payload,k=None):return s._operate(op,payload,k or key())
def newlot(s,kind='medicine'):
    return action(s,'lot',{'product_id':products[kind],'name':'S07-RACE-'+key(),'expiration':fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=45))})['id']
def receipt(s,lot,qty):return action(s,'receive',{'lot_id':lot,'quantity':qty,'uom_id':unit,'source_key':key(),'reason':'S07 synthetic actual receipt evidence'})
def issue(s,lot,qty=1,source=None,k=None):return action(s,'issue',{'lot_id':lot,'quantity':qty,'uom_id':unit,'source_key':source or key(),'reason':'S07 concurrent actual issue'},k)
def stock(s,lot,quarantine=False):
    store=s._access();l=s._lot(lot,store);c=s._config(store)
    return s._quantity(l,c.ydental_quarantine_id if quarantine else s._location(c,l.product_id))
def fixture(qty=1,kind='medicine'):
    lot=fresh(lambda s:newlot(s,kind));fresh(lambda s:receipt(s,lot,qty));return lot


def execute(role,n,fn,barrier=None,entered=None,release=None,rollback=False,started=None):
    pids=[]
    for tries in range(1,9):
        try:
            with registry.cursor() as cr:
                s=service(cr,role,n);cr.execute('SELECT pg_backend_pid(),ydental_revision FROM ydental_inventory_mutex');pid,_=cr.fetchone();pids.append(pid)
                if started:started.set()
                if tries==1 and barrier:barrier.wait(timeout=20)
                try:value=fn(s)
                except (AccessError,UserError) as error:value={'rejected':type(error).__name__,'code':str(error).split(':')[0]}
                if entered:entered.set()
                if release:assert release.wait(20)
                if rollback:cr.rollback();value={'rolled_back':True}
                else:cr.commit()
                return {'value':value,'backend_pid':pids[0],'retry_backend_pids':pids,'attempts':tries}
        except psycopg2.errors.SerializationFailure:
            continue
    raise RuntimeError('Bounded transaction retries exhausted')
def parallel(a,b):
    barrier=Barrier(2)
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(execute,*x,barrier) for x in (a,b)]
        return [x.result(timeout=60) for x in futures]
def ordered(a,b,rollback=False,started=None):
    entered,release,second_started=Event(),Event(),Event()
    with ThreadPoolExecutor(2) as pool:
        first=pool.submit(execute,*a,None,entered,release,rollback)
        assert entered.wait(20)
        second=pool.submit(execute,*b,None,None,None,False,second_started)
        assert second_started.wait(20)
        # The second connection has begun before release; lock visibility is
        # independently recorded by the returned backend/retry PIDs.
        release.set()
        return [first.result(timeout=60),second.result(timeout=60)]
def record(name,out,**checks):
    assert len({o['backend_pid'] for o in out})==2
    result['races'].append({'name':name,'status':'PASS','connections':2,'outputs':out,**checks})
def successes(out):return sum('rejected' not in o['value'] for o in out)

lot=fixture();out=parallel(('stock',0,lambda s:issue(s,lot)),('stock2',0,lambda s:issue(s,lot)))
assert successes(out)==1 and fresh(lambda s:stock(s,lot))==0;record('T02 final one unit; one actual issue; loser no half movement',out,final_quantity=0)
lot=fixture(10);source,k=key(),key();out=parallel(('stock',0,lambda s:issue(s,lot,3,source,k)),('stock2',0,lambda s:issue(s,lot,3,source,k)))
assert successes(out)==2 and out[0]['value']['id']==out[1]['value']['id'] and fresh(lambda s:stock(s,lot))==7
record('T01 identical request retry on distinct actor connections',out,final_quantity=7)
lot=fixture(10);source=key();out=parallel(('stock',0,lambda s:issue(s,lot,3,source)),('stock2',0,lambda s:issue(s,lot,3,source)))
assert out[0]['value']['id']==out[1]['value']['id'] and fresh(lambda s:stock(s,lot))==7;record('T01 source event uniqueness with different request keys',out)
lot=fixture(1);issued=fresh(lambda s:issue(s,lot))
def returned(s,source=None):return action(s,'return',{'event_id':issued['id'],'quantity':1,'uom_id':unit,'source_key':source or key(),'reason':'Real physical return'})
out=parallel(('stock',0,returned),('stock2',0,returned));assert successes(out)==1 and fresh(lambda s:stock(s,lot,True))==1
record('T05 two returns against one issued unit',out)
ret=next(o['value']['id'] for o in out if 'id' in o['value'])
def verify(s):return action(s,'verify',{'event_id':ret,'quantity':1,'uom_id':unit,'disposition':'release','source_key':key(),'reason':'Verified physical return'})
out=parallel(('stock',0,verify),('stock2',0,verify));assert successes(out)==1 and fresh(lambda s:stock(s,lot))==1
record('T05 two verifications cannot release the same return twice',out)
lot=fresh(lambda s:newlot(s,'material'));source=SyntheticSource(users['doctor'],store_ids[0],key(),'treatment',lot,2,unit,already_performed=True)
out=parallel(('doctor',0,lambda s:s._source_action(source)),('doctor',1,lambda s:s._source_action(source)))
assert out[0]['value']['id']==out[1]['value']['id'] and all(o['value']['state']=='pending' for o in out);record('T06 identical already-performed shortage source creates one pending fact',out)
pending=out[0]['value']['id'];fresh(lambda s:receipt(s,lot,5))
def recover(s):return action(s,'recover',{'event_id':pending,'reason':'Corrected real receipt; restore original event'})
out=parallel(('stock',0,recover),('stock2',0,recover));assert successes(out)==2 and out[0]['value']['move_id']==out[1]['value']['move_id']
assert fresh(lambda s:stock(s,lot))==3;record('T06 concurrent recovery yields one original native movement',out)
lot=fixture()
def transfer(s):return action(s,'transfer',{'lot_id':lot,'quantity':1,'uom_id':unit,'target_store_id':store_ids[1],'source_key':key(),'reason':'Same-company actual transfer'})
out=parallel(('stock',0,transfer),('stock2',0,lambda s:issue(s,lot)));assert successes(out)==1 and fresh(lambda s:stock(s,lot))==0
record('T08 transfer versus issue of final one',out)
lot=fixture()
def disable(s):return action(s,'lot_edit',{'lot_id':lot,'enabled':False,'reason':'Actual store batch disabled'})
out=ordered(('stock',0,disable),('stock2',0,lambda s:issue(s,lot)));assert 'rejected' in out[1]['value'] and fresh(lambda s:stock(s,lot))==1
record('T03 disable commits before issue; next execution refused',out)
lot=fixture();out=ordered(('stock',0,lambda s:issue(s,lot)),('stock2',0,disable));assert successes(out)==2 and fresh(lambda s:stock(s,lot))==0
record('T03 issue commits before disable; actual history retained',out)
lot=fresh(newlot)
def count(s):return action(s,'inventory',{'lot_id':lot,'counted':1,'uom_id':unit,'source_key':key(),'reason':'Actual physical inventory count one'})
out=ordered(('stock',0,count),('stock2',0,lambda s:issue(s,lot)));assert successes(out)==2 and fresh(lambda s:stock(s,lot))==0
record('T08 actual count commits before previously unavailable issue',out)
lot=fixture();out=ordered(('stock',0,lambda s:issue(s,lot)),('stock2',0,lambda s:issue(s,lot)),rollback=True)
assert successes(out)==2 and fresh(lambda s:stock(s,lot))==0;record('T02 full transaction rollback does not consume final unit',out)
# Native movement failure after modifying real quants must rollback completely.
lot=fixture(3)
with registry.cursor() as cr:
    s=service(cr);before=stock(s,lot);moves=s._native('stock.move').search_count([]);audits=s.env['ydental.access.audit'].sudo().search_count([])
    native=type(s._native('stock.move'));original=native._action_done
    def fail_after_move(m,*args,**kwargs):
        original(m,*args,**kwargs);raise UserError('S07 injected failure after actual native movement')
    with patch.object(native,'_action_done',fail_after_move):
        try:issue(s,lot);raise AssertionError('Injected failure missing')
        except UserError:pass
    assert stock(s,lot)==before and s._native('stock.move').search_count([])==moves and s.env['ydental.access.audit'].sudo().search_count([])==audits
    cr.commit()
result['native_rollback']={'status':'PASS','quantity_before':before,'quantity_after':before,'no_half_native_moves':True,'no_half_audit':True}
# Rework: category negatives on distinct live database connections.
def facts(s):
    return {m:s.env[m].sudo().search_count([]) for m in
        ('ydental.inventory.event','stock.move','stock.move.line','stock.quant','ydental.access.audit')}
for kind,role,categories in [('prescription','pharmacy',('material','prosthesis')),
        ('chairside','doctor',('material','prosthesis')),('treatment','doctor',('medicine','prosthesis'))]:
    for category in categories:
        lot=fixture(3,category);before=fresh(facts)
        def mismatch(s):
            return s._source_action(SyntheticSource(users[role],store_ids[0],key(),kind,lot,1,unit))
        out=parallel((role,0,mismatch),(role,1,mismatch))
        assert successes(out)==0 and fresh(facts)==before and fresh(lambda s:stock(s,lot))==3
        record('REWORK category '+kind+' rejects '+category+' without event/move/quant/audit changes',out)
# Temporal transition is simulated only by the private service clock, never by
# editing expiry or enabling a stopped lot. Separate live connections still
# perform all actual native movements and commits.
for expired in (True,False):
    lot=fresh(lambda s:newlot(s,'material'))
    source=SyntheticSource(users['doctor'],store_ids[0],key(),'treatment',lot,2,unit,already_performed=True)
    pending=fresh(lambda s:s._source_action(source),'doctor')['id']
    if not expired:fresh(lambda s:action(s,'lot_edit',{'lot_id':lot,'enabled':False,'reason':'Stopped after actual event'}))
    future=fields.Datetime.now()+timedelta(days=46) if expired else fields.Datetime.now()
    with patch.object(type(env['ydental.inventory.service']),'_now',return_value=future):
        correction=fresh(lambda s:receipt(s,lot,5))
        before=fresh(lambda s:s._model('event').browse(pending).read(['ydental_source_key','ydental_lot_id','ydental_quantity','ydental_actual_at','ydental_responsible_id','ydental_price_snapshot']))
        def recover_history(s):return action(s,'recover',{'event_id':pending,'reason':'Verified original fact plus evidenced stock correction'})
        out=parallel(('stock',0,recover_history),('stock2',0,recover_history))
        assert successes(out)==2 and out[0]['value']['move_id']==out[1]['value']['move_id'] and fresh(lambda s:stock(s,lot))==3
        after=fresh(lambda s:s._model('event').browse(pending).read(list(before[0].keys()-{'id'})))
        assert before==after
        assert fresh(lambda s:s._model('event').browse(pending).ydental_correction_id.id)==correction['id']
        record('REWORK '+('expired' if expired else 'disabled')+' original pending concurrent reconciliation one move frozen snapshot',out,correction_event=correction['id'])
        def new_clinical(s):return s._source_action(replace(source,source_key=key(),already_performed=False))
        negative_before=fresh(facts)
        out=parallel(('stock',0,lambda s:issue(s,lot)),('doctor',0,new_clinical))
        assert successes(out)==0 and fresh(facts)==negative_before and fresh(lambda s:stock(s,lot))==3
        record('REWORK '+('expired' if expired else 'disabled')+' new ordinary and clinical requests both refuse after historical recovery',out)
# Browser fixtures are isolated from races and contain no real patient/order.
ui_lot=fixture(10);ui_material=fresh(lambda s:newlot(s,'material'));ui_pending= fresh(lambda s:s._source_action(SyntheticSource(users['doctor'],store_ids[0],key(),'treatment',ui_material,2,unit,already_performed=True)),'doctor')
ui_prosthesis=fresh(lambda s:newlot(s,'prosthesis'));fresh(lambda s:receipt(s,ui_prosthesis,1))
fresh(lambda s:action(s,'policy',{'near_days':60,'wait_days':0,'low_quantity':3,'reason':'S07 synthetic UI thresholds only'}))
preview={'store':store_ids[0],'other_store':store_ids[1],'legal_store':store_ids[2],'lot':ui_lot,'material':ui_material,'pending':ui_pending['id'],
    'prosthesis':ui_prosthesis,'unit':unit,'pack':pack,'products':products}
for name,data in [('access.json',credentials),('preview.json',preview)]:
    with os.fdopen(os.open(run/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as f:json.dump(data,f,indent=2)
audit_result=runpy.run_path(str(Path(__file__).with_name('s07_audit.py')),init_globals={'env':env})['audit_result']
result['invariants']=audit_result
result.update(result='PASS',deadlocks=0)
print(json.dumps({'result':'PASS','races':len(result['races']),'deadlocks':0}))
save()
