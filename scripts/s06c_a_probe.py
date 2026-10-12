"""Actual independent PostgreSQL transactions on the recorded S06-B database."""
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
from odoo.exceptions import UserError
from odoo.tests import new_test_user
from odoo.addons.ydental_queue_test.tests.common import setup, key, bind, accepted, qualify, arrive_report
from odoo.addons.ydental_queue_test.models.adapter import Clock
from odoo.addons.ydental_queue_test.tests.rework_common import mixed_fixture


run = Path(os.environ['YDENTAL_S06C_RUN_DIR'])
assert re.fullmatch(r'ydental_s06c_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) and run.name == env.cr.dbname
registry = env.registry
result = {'scope': 'S06-B real queue/leases/execution, independent PostgreSQL RR transactions',
          'database': env.cr.dbname, 'started_utc': datetime.now(timezone.utc).isoformat(), 'races': []}


attempt_path = Path(__file__).resolve().parents[1] / 'docs/evidence/s06c/b-regression/a-regression/probe-attempts' / (env.cr.dbname + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
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
                except UserError as error:
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


def clean(q):
    # Test teardown uses the actual fault path, preserving history and missed.
    q._locks()
    q._model('lease').search([('ydental_active', '=', True), ('ydental_store_id', '=', store_id)])._save({'ydental_expires_at': q._now() - timedelta(seconds=1)})
    q._expire()
    # Voiding queue numbers is a genuine reception action, not a test state reset.
    intake = q.env['ydental.intake.service']
    for row in q._model('entry').search([('state', 'in', ['waiting', 'calling']), ('ydental_store_id', '=', store_id)]):
        t = row.ydental_task_id
        intake._operate('void', {'task_id': t.id, 'version': t.ydental_version, 'reason': 'Synthetic race teardown'}, key())


def accepted_task(q):
    intake = q.env['ydental.intake.service']
    pid = q.env['ydental.patient.service']._operate('create', {'values': {'name': 'S06C Race Synthetic Person'}}, key())['id']
    qualification = intake._operate('reserve', {'patient_id': pid, 'mapping_id': maps[0], 'start': start, 'end': end}, key())
    intake._operate('arrive', {'patient_id': pid}, key())
    intake._operate('report', {'task_id': qualification['task_id'], 'version': qualification['task_version']}, key())
    return qualification['task_id']


output = parallel([('doctor', 0, lambda q: enter(q)), ('second', 0, lambda q: enter(q))])
assert sum('rejected' not in v['value'] for v in output) == 1
record('T01_two_people_one_station', output, one_holder=True)
fresh(clean)
output = parallel([('doctor', 0, lambda q: enter(q, 0)), ('doctor', 1, lambda q: enter(q, 1))])
assert sum('rejected' not in v['value'] for v in output) == 1
record('T01_one_account_two_stations', output, one_active_lease=True)
fresh(clean)

la = fresh(lambda q: enter(q), 'doctor')
output = parallel([('doctor', 0, lambda q: q._operate('switch', dict(args(la), station_id=stations[1]))),
                   ('second', 0, lambda q: enter(q, 1))])
assert sum('rejected' not in v['value'] for v in output) == 1
state = fresh(lambda q: [(l.ydental_actor_id.id, l.ydental_station_id.id) for l in q._model('lease').search([('ydental_active', '=', True)])])
if 'rejected' in output[0]['value']:
    assert (users['doctor'], stations[0]) in state
else:
    assert (users['doctor'], stations[1]) in state and (users['doctor'], stations[0]) not in state
record('T18_switch_vs_target_acquisition', output, target_atomic=True, failure_keeps_old_station=True)
fresh(clean)

for first in ('heartbeat', 'timeout'):
    la = fresh(lambda q: enter(q), 'doctor')
    point = fresh(lambda q: q._now() + timedelta(seconds=10))
    fresh(lambda q: q._model('lease').browse(la['lease_id'])._save({'ydental_expires_at': point - timedelta(seconds=1)}))
    heartbeat = ('doctor', 0, lambda q: q._operate('heartbeat', args(la)))
    def timeout_reclaim(q):
        clocked = q.with_context(ydental_queue_test_clock=Clock(point))
        expired = clocked._timeout()
        reclaimed = enter(clocked)
        return {'expired': expired, 'reclaimed_lease_id': reclaimed['lease_id']}
    timeout = ('manager', 0, timeout_reclaim)
    output = ordered(heartbeat, timeout) if first == 'heartbeat' else ordered(timeout, heartbeat)
    active = fresh(lambda q: q._model('lease').browse(la['lease_id']).ydental_active)
    assert active == (first == 'heartbeat')
    record('T05_' + first + '_before_' + ('timeout' if first == 'heartbeat' else 'heartbeat'), output,
           stale_token_never_revives=True)
    fresh(clean)

for first in ('grant', 'heartbeat'):
    fresh(lambda q: q.env['ydental.access.service']._grant(users['doctor'], store_id, {'medical': 'write'}))
    la = fresh(lambda q: enter(q), 'doctor')
    grant = ('manager', 0, lambda q: {'membership': q.env['ydental.access.service']._grant(users['doctor'], store_id, {'medical': 'none'})})
    heartbeat = ('doctor', 0, lambda q: q._operate('heartbeat', args(la)))
    output = ordered(grant, heartbeat) if first == 'grant' else ordered(heartbeat, grant)
    assert ('rejected' in output[1]['value']) if first == 'grant' else 'rejected' not in output[0]['value']
    record('T14_' + first + '_before_' + ('heartbeat' if first == 'grant' else 'grant'), output, live_grant_fence=True)
    fresh(clean)
fresh(lambda q: q.env['ydental.access.service']._grant(users['doctor'], store_id, {'medical': 'write'}))

tid = fresh(accepted_task)
la = fresh(lambda q: enter(q), 'doctor')
lb = fresh(lambda q: enter(q, 1), 'second')
output = parallel([('doctor', 0, lambda q: q._operate('call', args(la))), ('second', 0, lambda q: q._operate('call', args(lb)))])
assert sum('rejected' not in v['value'] for v in output) == 1
record('T02_two_equal_capability_stations_one_patient', output, one_calling=True)
fresh(clean)

for first in ('call', 'void'):
    tid = fresh(accepted_task)
    la = fresh(lambda q: enter(q), 'doctor')
    def void(q):
        intake = q.env['ydental.intake.service']
        task = intake._model('task').browse(tid)
        return intake._operate('void', {'task_id': tid, 'version': task.ydental_version, 'reason': 'Real call vs void'}, key())
    call = ('doctor', 0, lambda q: q._operate('call', args(la)))
    revoke = ('frontdesk', 0, void)
    output = ordered(call, revoke) if first == 'call' else ordered(revoke, call)
    assert ('rejected' in output[1]['value']) == (first == 'void')
    assert fresh(lambda q: q._model('entry').search([('ydental_task_id', '=', tid)]).state) == 'void'
    record('T02_' + first + '_before_' + ('void' if first == 'call' else 'call'), output, no_stale_call=True)
    fresh(clean)

# Before actual starts, exercise void winning and rejecting stale starts.
tid = fresh(accepted_task)
la = fresh(lambda q: enter(q), 'doctor')
call = fresh(lambda q: q._operate('call', args(la)), 'doctor')
output = ordered(('frontdesk', 0, void), ('doctor', 0, lambda q: q._operate('start', dict(args(la), entry_id=call['entry_id']))))
assert 'rejected' in output[1]['value']
record('T02_void_before_start', output, no_execution=True)
fresh(clean)

def rotate_stations(q):
    global stations
    original = q.env['ydental.space.station'].sudo().browse(stations[0])
    stations = q.env['ydental.space.station'].sudo().create([{
        'name': 'S06C Race New Chair ' + key()[:6], 'ydental_store_id': original.ydental_store_id.id,
        'ydental_floor_id': original.ydental_floor_id.id, 'ydental_area_id': original.ydental_area_id.id,
        'ydental_add_capability_ids': [fields.Command.set(original.ydental_capability_ids.ids)]} for _ in range(2)]).ids
    # Prior actors keep their unresolved executions. Subsequent independent
    # cases use a new qualified person instead of bypassing the new actor fence.
    root = q.env['base'].sudo().env
    doctor = new_test_user(root, name='S06C Race New Qualified Doctor', login='s06cr_' + key(),
        groups='ydental_base.ydental_base_group_user')
    access = q.env['ydental.access.service']
    access._join(doctor.id, store_id)
    access._grant(doctor.id, store_id, {'medical': 'write', 'exam': 'write'})
    doctor.write({'ydental_capability_ids': [fields.Command.set(fixture.capabilities.ids)]})
    users['doctor'] = doctor.id
    sessions['doctor'], connections['doctor'] = [], []
    for n in range(2):
        a = root['ydental.access.service'].with_user(doctor)
        session = a._session_for_key(key())
        a._bind(session)._switch(store_id)
        sessions['doctor'].append(session.id)
        connections['doctor'].append(key() + key())


for competitor in ('call', 'start'):
    tid = fresh(accepted_task)
    la = fresh(lambda q: enter(q), 'doctor')
    lb = fresh(lambda q: enter(q, 1), 'second')
    call = fresh(lambda q: q._operate('call', args(la)), 'doctor')
    def competing(q):
        return q._operate(competitor, args(lb) if competitor == 'call' else dict(args(lb), entry_id=call['entry_id']))
    output = parallel([('doctor', 0, lambda q: q._operate('start', dict(args(la), entry_id=call['entry_id']))),
                       ('second', 0, competing)])
    assert 'rejected' not in output[0]['value'] and 'rejected' in output[1]['value']
    record('T02_actual_start_vs_other_holder_' + competitor, output, one_execution=True, no_duplicate_call=True)
    fresh(clean)
    fresh(rotate_stations)


# Actual start winners remain unresolved. Use a separate legal station pair
# afterward; no synthetic completion endpoint is added to product code.
tid = fresh(accepted_task)
la = fresh(lambda q: enter(q), 'doctor')
lb = fresh(lambda q: enter(q, 1), 'second')
call = fresh(lambda q: q._operate('call', args(la)), 'doctor')
output = ordered(('doctor', 0, lambda q: q._operate('start', dict(args(la), entry_id=call['entry_id']))), ('frontdesk', 0, void))
assert 'rejected' not in output[0]['value'] and 'rejected' in output[1]['value']
record('T02_start_before_void', output, serving_cannot_be_erased=True)
output = parallel([('doctor', 0, lambda q: q._operate('start', dict(args(la), entry_id=call['entry_id']))),
                   ('second', 0, lambda q: q._operate('start', dict(args(lb), entry_id=call['entry_id'])))])
assert all('rejected' in v['value'] for v in output)
record('T02_repeat_start_vs_another_holder_start', output, one_actual_execution=True)
output = parallel([('doctor', 0, lambda q: q._operate('start', dict(args(la), entry_id=call['entry_id']))),
                   ('second', 0, lambda q: q._operate('call', args(lb)))])
assert all('rejected' in v['value'] for v in output)
record('T02_start_vs_another_station_call', output, serving_patient_not_callable=True)

# New B1 races retain the original successful execution and its original actor.
old_actor = users['doctor']
old_lease = la
old_station = stations[0]
fresh(lambda q: q._model('lease').browse(old_lease['lease_id'])._save({'ydental_expires_at': q._now() - timedelta(seconds=1)}))
target = fresh(lambda q: q.env['ydental.space.station'].sudo().create({
    'name': 'S06C Verify Actor Forbidden New Chair', 'ydental_store_id': store_id,
    'ydental_floor_id': q.env['ydental.space.station'].sudo().browse(old_station).ydental_floor_id.id,
    'ydental_area_id': q.env['ydental.space.station'].sudo().browse(old_station).ydental_area_id.id,
    'ydental_add_capability_ids': [fields.Command.set(fixture.capabilities[0].ids)]}).id)
for first in ('timeout', 'enter'):
    timeout = ('manager', 0, lambda q: {'expired': q._timeout()})
    admission = ('doctor', 0, lambda q: q._operate('enter', {'station_id': target}))
    output = ordered(timeout, admission) if first == 'timeout' else ordered(admission, timeout)
    rejected = output[1 if first == 'timeout' else 0]['value']
    assert 'rejected' in rejected
    assert fresh(lambda q: q._actor_execution(old_actor).state) == 'verify'
    assert fresh(lambda q: q._model('lease').search_count([('ydental_actor_id', '=', old_actor), ('ydental_active', '=', True)])) == 0
    status = fresh(lambda q: q._status(), 'doctor')
    assert status['state'] == 'verify' and status['station'] == fresh(lambda q: q.env['ydental.space.station'].sudo().browse(old_station).name)
    name = 'B1_serving_timeout_before_actor_enter' if first == 'timeout' else 'B1_existing_verify_actor_enter_vs_sweep'
    record(name, output, actor_still_fenced=True, old_position_verify=True)

store_b = fixture.stores[1].id
map_b = fixture.mappings[1][0].id
fresh(lambda q: q.env['ydental.access.service']._join(old_actor, store_b))
fresh(lambda q: q.env['ydental.access.service']._grant(old_actor, store_b, {'frontdesk': 'write', 'medical': 'write'}))
def cross_store_write(q):
    access = q.env['ydental.access.service']
    session = access._scope()
    access._switch(store_b)
    intake = access._bind(session).env['ydental.intake.service']
    assert intake.env['ydental.access.service']._get_execution_store_id() == store_id
    return intake._operate('reserve', {'patient_id': fresh_patient, 'mapping_id': map_b,
        'start': start, 'end': end, 'channel': 'reservation'}, key())
fresh_patient = fresh(lambda q: q.env['ydental.patient.service']._operate('create',
    {'values': {'name': 'S06C Cross Store Fence Synthetic'}}, key())['id'])
output = parallel([('manager', 0, lambda q: {'expired': q._timeout()}), ('doctor', 1, cross_store_write)])
assert 'rejected' in output[1]['value'] and 'another store' in output[1]['value']['rejected']
record('B1_execution_store_fence_vs_cross_store_write', output, unresolved_store_fence=True, no_cross_store_task=True)

# New B4: unrelated request and scheduler contend over the same expiration.
fresh(clean)
fresh(rotate_stations)
la = fresh(lambda q: enter(q), 'doctor')
fresh(lambda q: q._model('lease').browse(la['lease_id'])._save({'ydental_expires_at': q._now() - timedelta(seconds=1)}))
output = parallel([('second', 0, lambda q: enter(q, 1)), ('manager', 0, lambda q: {'expired': q._timeout()})])
def timeout_audit(q):
    rows = q.env['ydental.access.audit'].sudo().search([('ydental_event', '=', 'queue.connection_timeout'), ('ydental_target_id', '=', la['lease_id'])])
    assert len(rows) == 1 and rows.ydental_user_id == q.env.ref('base.user_root')
    assert rows.ydental_source == 'workstation_timeout_automation'
    assert rows.ydental_after['holder_user_id'] == users['doctor'] and rows.ydental_after['station_id'] == stations[0]
    return True
assert fresh(timeout_audit)
record('B4_unrelated_request_cleanup_vs_cron_timeout_audit', output, one_automation_event=True, holder_preserved=True)
fresh(clean)

# New B3: mixed-capability missed competes with a different capability call.
with registry.cursor() as cr:
    fixture.root = api.Environment(cr, 1, {})
    fixture.group = service(cr, 'manager').env['ydental.intake.service']
    fixture.stores = fixture.root['ydental.access.store'].browse([store_id, store_b])
    fixture.stations = [[fixture.root['ydental.space.station'].browse(stations[0])]]
    fixture.capabilities = fixture.root['ydental.access.capability'].browse(fixture.capabilities.ids)
    fixture.catalogs = [fixture.root['ydental.intake.catalog'].browse(c.id) for c in fixture.catalogs]
    fixture.users = {role: fixture.root['res.users'].browse(uid) for role, uid in users.items()}
    mixed = mixed_fixture(fixture)
    mixed_ids = {'area': mixed.area.id, 'stations': [s.id for s in mixed.stations], 'maps': [m.id for m in mixed.mappings]}
    cr.commit()
def mixed_accept(q, index):
    intake = q.env['ydental.intake.service']
    pid = q.env['ydental.patient.service']._operate('create', {'values': {'name': 'S06C Mixed Race Synthetic'}}, key())['id']
    value = intake._operate('reserve', {'patient_id': pid, 'mapping_id': mixed_ids['maps'][index], 'start': start, 'end': end}, key())
    intake._operate('arrive', {'patient_id': pid}, key())
    intake._operate('report', {'task_id': value['task_id'], 'version': value['task_version']}, key())
    return value['task_id']
mixed_tasks = [fresh(lambda q, i=i: mixed_accept(q, i)) for i in (0, 1, 2, 2, 2, 2)]
la = fresh(lambda q: q._operate('enter', {'station_id': mixed_ids['stations'][2]}), 'doctor')
lb = fresh(lambda q: q._operate('enter', {'station_id': mixed_ids['stations'][0]}), 'second')
called = fresh(lambda q: q._operate('call', args(la)), 'doctor')
assert called['task_id'] == mixed_tasks[2]
output = parallel([('doctor', 0, lambda q: q._operate('missed', dict(args(la), entry_id=called['entry_id']))),
                   ('second', 0, lambda q: q._operate('call', args(lb)))])
assert all('rejected' not in v['value'] for v in output)
actual_order = fresh(lambda q: q._ranked_area(mixed_ids['area']).ydental_task_id.ids)
assert actual_order == [mixed_tasks[i] for i in (0, 1, 3, 4, 2, 5)]
record('B3_mixed_capability_missed_vs_other_capability_call', output, call_rank_before=3,
       rank_after=5, never_promoted=True, unrelated_call_anchor_preserved=True)

# Global invariants over genuine committed records.
def invariants(q):
    e = q.env['base'].sudo().env
    for table, field, where in [('ydental_queue_lease', 'ydental_actor_id', 'ydental_active'),
        ('ydental_queue_lease', 'ydental_station_id', 'ydental_active'),
        ('ydental_queue_entry', 'ydental_patient_id', "state IN ('waiting','calling')"),
        ('ydental_queue_execution', 'ydental_patient_id', "state IN ('serving', 'verify')")]:
        # Identifiers and predicate are fixed literals above, never input values.
        from odoo.tools import SQL
        q.env.cr.execute(SQL('SELECT %s FROM %s WHERE %s GROUP BY %s HAVING count(*)>1',
            SQL.identifier(field), SQL.identifier(table), SQL(where), SQL.identifier(field)))
        assert not q.env.cr.fetchall()
    for slot in e['ydental.supply.slot'].search([]):
        claims = e['ydental.supply.claim'].search([('ydental_slot_id', '=', slot.id), ('state', 'in', ['held', 'consumed'])])
        assert slot.ydental_total == slot.ydental_reservation_free + slot.ydental_walkin_free + slot.ydental_unavailable + len(claims)
    return {'one_actor_station': True, 'one_waiting_calling': True, 'one_actual_execution': True, 's03_conservation': True}
result['invariants'] = fresh(invariants)
with registry.cursor() as cr:
    cr.execute('SELECT deadlocks FROM pg_stat_database WHERE datname=%s', [env.cr.dbname])
    result['deadlocks'] = cr.fetchone()[0]
assert result['deadlocks'] == 0

# Create an independent browser fixture so race serving rows are left intact.
with registry.cursor() as cr:
    browser_fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(browser_fixture)
    browser_task = accepted(browser_fixture)
    browser_mixed = mixed_fixture(browser_fixture)
    browser_mixed_task = accepted(browser_fixture, browser_mixed.mappings[2])
    browser_nzero_task = accepted(browser_fixture, browser_fixture.mappings[0][1])
    zero_area = browser_fixture.areas[0][1]
    zero_area.write({'ydental_version': zero_area.ydental_version, 'ydental_missed_limit': 0})
    preview = {'stores': browser_fixture.stores.ids, 'stations': [browser_fixture.stations[0][0].id, browser_fixture.other_station.id],
               'task_id': browser_task.id, 'task_version': browser_task.ydental_version,
               'wrong_execution_station': browser_mixed.wrong.id, 'mixed_task_id': browser_mixed_task.id,
               'nzero_station': browser_fixture.stations[0][1].id, 'nzero_task_id': browser_nzero_task.id}
    access = {}
    for role, user in (list(browser_fixture.users.items()) + [('second', browser_fixture.second)]):
        password = secrets.token_urlsafe(24)
        user.write({'password': password, 'lang': 'en_US'})
        access[role] = {'id': user.id, 'login': user.login, 'password': password}
    cr.commit()
private(run / 'access.json', access)
private(run / 'preview.json', preview)
result['result'] = 'PASS'
evidence = Path(__file__).resolve().parents[1] / 'docs/evidence/s06c/b-regression/a-regression/probe-attempts'
evidence.mkdir(parents=True, exist_ok=True)
path = attempt_path
path.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'result': 'PASS', 'races': len(result['races']), 'deadlocks': 0, 'evidence': str(path)}))
