from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import json
import atexit
import os
from pathlib import Path
import re
import secrets
from threading import Barrier, Event
from types import SimpleNamespace

import psycopg2

from odoo import api, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import new_test_user
from odoo.addons.ydental_queue_test.tests.common import setup, key, bind, accepted, qualify, arrive_report
from odoo.addons.ydental_queue_test.models.adapter import Clock
from odoo.addons.ydental_queue_test.tests.rework_common import mixed_fixture


run = Path(os.environ['YDENTAL_S06C_RUN_DIR'])
assert re.fullmatch(r'ydental_s06c_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) and run.name == env.cr.dbname
registry = env.registry
result = {'scope': 'S06-C business day, push and credential concurrency',
          'database': env.cr.dbname, 'started_utc': datetime.now(timezone.utc).isoformat(), 'races': []}


attempt_path = Path(__file__).resolve().parents[1] / 'docs/evidence/s06c/probe-attempts' / (env.cr.dbname + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
attempt_path.parent.mkdir(parents=True, exist_ok=True)

def save_attempt():
    result.setdefault('result', 'FAIL_OR_INTERRUPTED')
    attempt_path.write_text(json.dumps(result, indent=2) + '\n')

atexit.register(save_attempt)


def private(path, value):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
        json.dump(value, handle, indent=2)


with registry.cursor() as cr:
    fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(fixture)
    root = fixture.root
    for slots in fixture.slots:
        for slot in slots:
            manager = bind(fixture, fixture.users['manager'], slot.ydental_store_id)
            manager.env['ydental.supply.service']._operate('resize', {'id': slot.id, 'version': slot.ydental_version,
                'total': 180, 'reason': 'Synthetic S06-B race capacity'}, key())
    users = {role: u.id for role, u in fixture.users.items()} | {'second': fixture.second.id}
    sessions = {}
    connections = {}
    for role, uid in users.items():
        sessions[role] = []
        connections[role] = []
        for n in range(2):
            service = bind(fixture, root['res.users'].browse(uid))
            sessions[role].append(service.env['ydental.access.service']._scope().id)
            connections[role].append(key() + key())
    stations = [fixture.stations[0][0].id, fixture.other_station.id]
    maps = [m.id for m in fixture.mappings[0]]
    start, end = fields.Datetime.to_string(fixture.start), fields.Datetime.to_string(fixture.end)
    store_id = fixture.stores[0].id
    root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '7200')
    root['res.users'].browse(users['frontdesk']).write({'group_ids': [(4, root.ref('ydental_queue.ydental_group_append').id)]})
    cr.commit()  # This script owns this new fixture cursor.


def service(cr, role='doctor', n=0):
    e = api.Environment(cr, users[role], {})
    access = e['ydental.access.service']
    scope = e['ydental.access.session'].sudo().browse(sessions[role][n])
    return access._bind(scope).env['ydental.queue.service']._bind_connection(connections[role][n])


def fresh(callback, role='manager'):
    with registry.cursor() as cr:
        q = service(cr, role)
        value = callback(q)
        cr.commit()  # Only the script's own cursor, never a business method.
        return value


def execute(callback, role, n, barrier=None, hold=None, ready=None):
    backend_pids = []
    for attempt in range(1, 13):
        try:
            with registry.cursor() as cr:
                q = service(cr, role, n)
                cr.execute('SELECT pg_backend_pid(), ydental_revision FROM ydental_queue_mutex')
                pid, revision = cr.fetchone()  # Establish independent RR snapshots.
                backend_pids.append(pid)
                if attempt == 1 and ready:
                    ready.set()
                if attempt == 1 and barrier:
                    barrier.wait(timeout=20)
                try:
                    value = callback(q)
                except (UserError, AccessError) as error:
                    value = {'rejected': str(error)}
                if attempt == 1 and hold:
                    hold[0].set()
                    assert hold[1].wait(timeout=20)
                cr.commit()
                return {'value': value, 'attempts': attempt, 'pid': pid, 'initial_pid': backend_pids[0], 'attempt_pids': backend_pids}
        except psycopg2.errors.SerializationFailure:
            if attempt == 12:
                raise


def parallel(calls):
    barrier = Barrier(len(calls))
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        fs = [pool.submit(execute, fn, role, n, barrier) for role, n, fn in calls]
        return [f.result(timeout=90) for f in fs]


def ordered(first, second):
    held, release, ready = Event(), Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(execute, first[2], first[0], first[1], None, (held, release))
        assert held.wait(timeout=20)
        b = pool.submit(execute, second[2], second[0], second[1], None, None, ready)
        assert ready.wait(timeout=20)
        release.set()
        return [a.result(timeout=90), b.result(timeout=90)]


def record(name, output, **checks):
    assert len({v['initial_pid'] for v in output}) == 2
    result['races'].append({'name': name, 'result': 'PASS', 'connections': 2,
        'backend_pids': [v['initial_pid'] for v in output], 'retry_backend_pids': [v['attempt_pids'] for v in output], 'attempts': [v['attempts'] for v in output],
        'outcomes': ['rejected' if 'rejected' in v['value'] else v['value'].get('result', 'accepted') for v in output], **checks})


def args(lease):
    return {'lease_id': lease['lease_id'], 'token': lease['token']}


def enter(q, station=0):
    return q._operate('enter', {'station_id': stations[station]})


from odoo.addons.ydental_queue_test.tests.test_day import at
from odoo.addons.ydental_queue_test.models.return_adapter import ReturnSource
from odoo.addons.ydental_queue_test.models.day_adapter import DaySource

base_now=datetime.now().replace(microsecond=0)
late=base_now.replace(hour=23,minute=55,second=0)
midnight=late.replace(hour=0,minute=0)+timedelta(days=1)


def task(q, reported=False, derived=False):
    front=service(q.env.cr,'frontdesk').env['ydental.intake.service']
    pid=front.env['ydental.patient.service']._operate('create',{'values':{'name':'张合成患者'}},key())['id']
    r=front._operate('reserve',{'patient_id':pid,'mapping_id':maps[0],'start':start,'end':end},key())
    t=q.env['ydental.intake.task'].sudo().browse(r['task_id'])
    if derived:
        t=front._new('task',t.ydental_store_id,dict(front._identity(t.ydental_patient_id),name='C synthetic derived source',
            ydental_mapping_id=maps[0],ydental_parent_task_id=t.id,ydental_source_kind='derived'))
    front._operate('arrive',{'patient_id':pid},key())
    if reported:front._operate('report',{'task_id':t.id,'version':t.ydental_version},key())
    return {'task':t.id,'patient':pid}


def report_task(q,c):
    t=q.env['ydental.intake.task'].sudo().browse(c['task'])
    return q.env['ydental.intake.service']._operate('report',{'task_id':t.id,'version':t.ydental_version},key())


def business(q,state,instant=None):
    q=at(q,instant) if instant else q
    supply=q.env['ydental.supply.service'];store=q.env['ydental.access.store'].sudo().browse(store_id)
    area=q.env['ydental.intake.mapping'].sudo().browse(maps[0]).ydental_area_id
    b=supply._business_record(store,area.id)
    return supply._operate('business',dict(area_id=area.id,state=state,reason='C real concurrent business action',
        **({'version':b.ydental_version} if b else {})),key())


def reset(q):
    front=service(q.env.cr,'frontdesk').env['ydental.intake.service']
    for row in q._model('entry').search([('ydental_store_id','=',store_id),('state','in',('waiting','calling'))]):
        front._withdraw(row.ydental_task_id,'C prepare independent next race')
    return business(q,'open')


def cleanup(q,date=None):
    return at(q,midnight+timedelta(minutes=30))._cleanup_day(q.env['ydental.access.store'].sudo().browse(store_id),date or late.date())


def state(c):
    return fresh(lambda q: {'entries':[(r.id,r.state,str(r.ydental_business_date)) for r in q._model('entry').search([('ydental_task_id','=',c['task'])])],
        'task':q.env['ydental.intake.task'].sudo().browse(c['task']).state})


def finish(q,c,lease):
    e=q._model('execution').browse(c['execution_id'])
    q._test_return_source(ReturnSource(e.id,save_ok=True))
    return q._operate('handover',dict(args(lease),execution_id=e.id))

c=fresh(lambda q:task(q));out=ordered(('frontdesk',0,lambda q:report_task(q,c)),('manager',0,lambda q:business(q,'draining')))
assert all('rejected' not in v['value'] for v in out);assert state(c)['task']=='accepted'
record('report commits before draining; accepted waiting retained',out,waiting_retained=True)
fresh(reset);c=fresh(lambda q:task(q));out=ordered(('manager',0,lambda q:business(q,'draining')),('frontdesk',0,lambda q:report_task(q,c)))
assert 'rejected' in out[1]['value'];assert not state(c)['entries'];record('draining commits before report; no half position',out,no_half_position=True)
fresh(reset);c=fresh(lambda q:task(q,True));lease=fresh(lambda q:enter(at(q,late)), 'doctor');fresh(lambda q:business(q,'draining'))
out=ordered(('manager',0,lambda q:business(q,'closed')),('doctor',0,lambda q:q._operate('call',args(lease))))
assert 'rejected' in out[0]['value'] and 'entry_id' in out[1]['value'];record('close sees waiting; draining call continues',out,close_refused=True)
call=out[1]['value'];out=ordered(('doctor',0,lambda q:at(q,late)._operate('start',dict(args(lease),entry_id=call['entry_id']))),('manager',0,lambda q:business(q,'closed')))
assert all('rejected' not in v['value'] for v in out);record('draining start clears last calling before close',out,serving_survives_closed=True)
fresh(lambda q:finish(at(q,late),out[0]['value'],lease),'doctor');fresh(lambda q:q._operate('exit',args(lease)),'doctor')
fresh(reset);c=fresh(lambda q:task(q));fresh(lambda q:business(q,'draining'))
out=parallel([('manager',0,lambda q:business(q,'closed')),('frontdesk',0,lambda q:report_task(q,c))])
assert 'rejected' in out[1]['value'] and not state(c)['entries'];record('close versus concurrent ordinary report',out,ordinary_report_refused=True)
c=fresh(lambda q:task(q));ordinary=fresh(lambda q:task(q))
fresh(lambda q:q._operate('append',{'task_id':c['task'],'reason':'C closed permit'}),'frontdesk')
out=parallel([('frontdesk',0,lambda q:report_task(q,c)),('frontdesk',1,lambda q:report_task(q,ordinary))])
assert 'rejected' not in out[0]['value'] and 'rejected' in out[1]['value']
lease=fresh(enter,'doctor');fresh(lambda q:q._operate('call',args(lease)),'doctor');record('closed append report and call versus ordinary report',out,area_stays_closed=True)
fresh(reset);fresh(lambda q:q._operate('exit',args(lease)),'doctor')
# Cleanup and old-day call/start interleave on independent live RR connections.
c=fresh(lambda q:task(q,True));lease=fresh(lambda q:enter(at(q,late)),'doctor')
out=ordered(('manager',0,cleanup),('doctor',0,lambda q:at(q,midnight+timedelta(minutes=9))._operate('call',args(lease))))
assert 'rejected' in out[1]['value'];record('cleanup commits before old-day call',out,terminal_not_called=True)
# New independent store/day prevents reusing a completed watermark to hide rows.
# A prior-day cleanup watermark forbids inserting backdated fixtures in production;
# move forward one day for each subsequent synthetic old-day race.
late+=timedelta(days=1);midnight+=timedelta(days=1)

def next_day_task(q,reported=True):
    front=at(service(q.env.cr,'frontdesk').env['ydental.intake.service'],late)
    c=task(q,False,True);t=q.env['ydental.intake.task'].sudo().browse(c['task'])
    front._operate('arrive',{'patient_id':c['patient']},key())
    business(q,'open',late)
    if reported:report_task(at(service(q.env.cr,'frontdesk'),late),c)
    return c

fresh(lambda q:q._operate('exit',args(lease)),'doctor')
c=fresh(next_day_task);lease=fresh(lambda q:enter(at(q,late)),'doctor')
call=fresh(lambda q:at(q,late)._operate('call',args(lease)),'doctor')
out=ordered(('manager',0,cleanup),('doctor',0,lambda q:at(q,midnight+timedelta(minutes=9,seconds=59))._operate('start',dict(args(lease),entry_id=call['entry_id']))))
assert 'rejected' in out[1]['value'];record('cleanup commits before old-day start',out,claim_not_consumed=True)
fresh(lambda q:q._operate('exit',args(lease)),'doctor')
late+=timedelta(days=1);midnight+=timedelta(days=1)
c=fresh(next_day_task);lease=fresh(lambda q:enter(at(q,late)),'doctor');call=fresh(lambda q:at(q,late)._operate('call',args(lease)),'doctor')
out=ordered(('doctor',0,lambda q:at(q,midnight+timedelta(minutes=9,seconds=59))._operate('start',dict(args(lease),entry_id=call['entry_id']))),('manager',0,cleanup))
assert state(c)['entries'][-1][1]=='serving';record('old-day start commits before cleanup; actual survives',out,serving_preserved=True)
fresh(lambda q:finish(at(q,midnight+timedelta(minutes=30)),out[0]['value'],lease),'doctor');fresh(lambda q:q._operate('exit',args(lease)),'doctor')
late+=timedelta(days=1);midnight+=timedelta(days=1);c=fresh(next_day_task)
out=parallel([('manager',0,cleanup),('manager',1,cleanup)])
assert out[0]['value']['watermark_id']==out[1]['value']['watermark_id'];record('two cleanup workers; one final watermark',out,one_watermark=True)
late+=timedelta(days=1);midnight+=timedelta(days=1);old=fresh(next_day_task);today=fresh(lambda q:next_day_task(q,False))
fresh(lambda q:business(q,'open',midnight+timedelta(minutes=30)))
fresh(lambda q:at(q,midnight+timedelta(minutes=30)).env['ydental.intake.service']._operate('arrive',{'patient_id':today['patient']},key()),'frontdesk')
out=parallel([('manager',0,cleanup),('frontdesk',0,lambda q:report_task(at(q,midnight+timedelta(minutes=30)),today))])
assert state(old)['entries'][-1][1]=='day_closed' and state(today)['entries'][-1][1]=='waiting';record('delayed cleanup versus today new report',out,today_untouched=True)
out=parallel([('manager',0,lambda q:business(q,'open',midnight+timedelta(minutes=30))),('manager',1,cleanup)])
assert state(old)['entries'][-1][1]=='day_closed';record('today open versus yesterday terminal history',out,no_resurrection=True)
# Actual native bus rows are inspected across commit and full rollback.
area_id=fixture.areas[0][0].id

def publish(q,rollback=False):
    q._locks();store=q.env['ydental.access.store'].sudo().browse(store_id);area=q.env['ydental.space.area'].sudo().browse(area_id)
    if rollback:
        try:
            with q.env.cr.savepoint(flush=False):
                q._publish_scope(store,area);q.env.flush_all();raise RuntimeError('synthetic savepoint failure')
        except RuntimeError:pass
        q.env.invalidate_all()
    else:q._publish_scope(store,area)
    return {'version':q._scope_record(store,area).ydental_version}

out=parallel([('manager',0,lambda q:publish(q)),('manager',1,lambda q:publish(q,True))]);record('native bus commit versus rolled-back version',out,rollback_no_success=True)
created=fresh(lambda q:q._operate('screen_create',{'area_id':area_id}))
# Never include credentials/payload outcomes in public evidence.
out=ordered(('manager',0,lambda q:q._operate('screen_revoke',{'credential_id':created['credential_id']})),('reader',0,lambda q:q._screen_snapshot(created['token'])))
assert 'rejected' in out[1]['value'];record('screen credential revoke before next snapshot',out,next_request_denied=True)
fresh(reset);c=fresh(lambda q:task(q,True));lease=fresh(enter,'doctor');fresh(lambda q:q._operate('call',args(lease)),'doctor')
created=fresh(lambda q:q._operate('screen_create',{'area_id':area_id}));before=fresh(lambda q:q._screen_snapshot(created['token']))
out=ordered(('frontdesk',0,lambda q:q.env['ydental.intake.service']._operate('void',{'task_id':c['task'],'version':q.env['ydental.intake.task'].sudo().browse(c['task']).ydental_version,'reason':'C retract call'},key())),('reader',0,lambda q:q._screen_snapshot(created['token'])))
assert not any(r['state']=='calling' for r in out[1]['value']['rows']);assert out[1]['value']['version']>before['version'];record('retracted calling versus stale client version snapshot',out,no_replay=True)
# Native bus messages contain only scope/version, and every version has a committed outbox fact.
def bus_check(q):
    import json
    scope=q._scope_record(q.env['ydental.access.store'].sudo().browse(store_id),q.env['ydental.space.area'].sudo().browse(area_id))
    notifications=q.env['bus.bus']._poll([(q.env.cr.dbname,scope.ydental_channel)],0)
    versions=[]
    for r in notifications:
        p=r['message']['payload'];assert set(p)=={'store','area','version'};versions.append(p['version'])
    committed=q._model('outbox').search([('ydental_scope_id','=',scope.id)]).mapped('ydental_scope_version')
    assert versions and set(versions)==set(committed)
    return {'messages':len(versions),'minimal_payload':True,'outbox_exact':True}
result['bus']=fresh(bus_check)
result.update(result='PASS',deadlocks=0);save_attempt();print(json.dumps({'result':'PASS','races':len(result['races']),'deadlocks':0}))
