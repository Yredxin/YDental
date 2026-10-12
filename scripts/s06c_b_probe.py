"""A's 21 races followed by B independent PostgreSQL RR competitions."""
import runpy
runpy.run_path(str(__import__('pathlib').Path(__file__).with_name('s06c_a_probe.py')), init_globals={'env': env})
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
result = {'scope': 'S06-B hold, restore, handover, continuation and append concurrency',
          'database': env.cr.dbname, 'started_utc': datetime.now(timezone.utc).isoformat(), 'races': []}


attempt_path = Path(__file__).resolve().parents[1] / 'docs/evidence/s06c/b-regression/probe-attempts' / (env.cr.dbname + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
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


from odoo.addons.ydental_queue_test.models.return_adapter import ReturnSource
from odoo.addons.ydental_queue_test.tests.return_common import close, appender


counter = 0


def case(q, mode='hold'):
    global counter
    counter += 1
    root = q.env['base'].sudo().env
    front = service(q.env.cr, 'frontdesk').env['ydental.intake.service']
    store = root['ydental.access.store'].browse(store_id)
    caps = root['ydental.intake.mapping'].browse(maps).ydental_catalog_id.ydental_capability_id
    admin = q.env['ydental.access.service']
    roles = []
    chairs = []
    for category, template_id in (('medical', stations[0]), ('exam', fixture.stations[0][2].id)):
        role = 'b' + str(counter) + category
        user = new_test_user(root, name='S06C synthetic ' + role, login='s06c_' + key(),
                             password='s06c-synthetic-only', groups='ydental_base.ydental_base_group_user')
        admin._join(user.id, store_id)
        admin._grant(user.id, store_id, {category: 'write'})
        user.write({'ydental_capability_ids': [fields.Command.set(caps.ids)]})
        users[role] = user.id
        intake = bind(SimpleNamespace(root=root, stores=store), user)
        sessions[role] = [intake.env['ydental.access.service']._scope().id]
        connections[role] = [key() + key()]
        template = root['ydental.space.station'].browse(template_id)
        chair = root['ydental.space.station'].create({'name': 'S06C ' + role + ' chair',
            'ydental_store_id': store_id, 'ydental_floor_id': template.ydental_floor_id.id,
            'ydental_area_id': template.ydental_area_id.id, 'ydental_kind': template.ydental_kind,
            'ydental_add_capability_ids': [fields.Command.set(template.ydental_capability_ids.ids)]})
        roles.append(role); chairs.append(chair.id)
    # This is an input fixture, not C's day-close or draining transition.
    business = q.env['ydental.supply.service']._business_record(store, root['ydental.intake.mapping'].browse(maps[0]).ydental_area_id.id)
    business._save({'state': 'open'})
    root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '600')
    claim = front._operate('reserve', {'patient_id': front.env['ydental.patient.service']._operate('create',
        {'values': {'name': 'S06C synthetic concurrency person'}}, key())['id'], 'mapping_id': maps[0], 'start': start, 'end': end}, key())
    task = root['ydental.intake.task'].browse(claim['task_id'])
    front._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
    dr = service(q.env.cr, roles[0]); ex = service(q.env.cr, roles[1])
    lease = dr._operate('enter', {'station_id': chairs[0]})
    other = ex._operate('enter', {'station_id': chairs[1]})
    c = {'doctor': roles[0], 'exam': roles[1], 'lease': lease, 'other': other, 'task': task.id, 'patient': task.ydental_patient_id.id}
    if mode == 'append':
        front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        business._save({'state': 'closed'})
        root['res.users'].browse(users['frontdesk']).write({'group_ids': [(4, root.ref('ydental_queue.ydental_group_append').id)]})
        return c
    front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
    call = dr._operate('call', args(lease))
    actual = dr._operate('start', dict(args(lease), entry_id=call['entry_id']))
    execution = root['ydental.queue.execution'].browse(actual['execution_id'])
    c['execution'] = execution.id
    target = front._new('task', store, dict(front._identity(task.ydental_patient_id), name='S06C synthetic external target',
        ydental_mapping_id=maps[2], ydental_parent_task_id=task.id, ydental_source_kind='derived'))
    dr._test_return_source(ReturnSource(execution.id, target.id, mode != 'failure'))
    c['target'] = target.id
    if mode in ('hold', 'calling'):
        c['hold'] = dr._operate('reserve', dict(args(lease), execution_id=execution.id, target_task_id=target.id))['hold_id']
        front._operate('report', {'task_id': target.id, 'version': target.ydental_version}, key())
        if mode == 'hold':
            c['call'] = ex._operate('call', args(other))['entry_id']
    return c


def restore(q, c):
    return q._operate('restore', dict(args(c['lease']), hold_id=c['hold'], confirmed=True))


def start_exam(q, c):
    return q._operate('start', dict(args(c['other']), entry_id=c['call']))


def handover(q, c):
    return q._operate('handover', dict(args(c['lease']), execution_id=c['execution']))


def assert_patient(c):
    def read(q):
        rows = q._model('execution').search([('ydental_patient_id', '=', c['patient']), ('state', 'in', ('serving', 'verify'))])
        assert len(rows) <= 1
        return [r.ydental_task_id.id for r in rows]
    return fresh(read)


for first_name in ('restore', 'exam_start'):
    c = fresh(lambda q: case(q))
    actions = [(c['doctor'], 0, lambda q: restore(q, c)), (c['exam'], 0, lambda q: start_exam(q, c))]
    if first_name == 'exam_start':
        actions.reverse()
    output = ordered(*actions)
    assert 'rejected' not in output[0]['value'] and 'rejected' in output[1]['value']
    assert assert_patient(c) == [c['task'] if first_name == 'restore' else c['target']]
    record('T07_' + first_name + '_commits_first', output, one_actual_execution=True, atomic_withdraw=True)

c = fresh(lambda q: case(q, 'calling'))
output = parallel([(c['doctor'], 0, lambda q: restore(q, c)), (c['exam'], 0, lambda q: q._operate('call', args(c['other'])))])
assert assert_patient(c) == [c['task']]
assert fresh(lambda q: q._model('entry').search([('ydental_task_id', '=', c['target'])]).state) == 'void'
record('T07_restore_vs_external_call', output, other_call_released=True)

c = fresh(lambda q: case(q, 'handover'))
output = parallel([(c['doctor'], 0, lambda q: handover(q, c)), (c['doctor'], 0, lambda q: handover(q, c))])
assert output[0]['value']['continuation_task_id'] == output[1]['value']['continuation_task_id']
assert not assert_patient(c)
record('T08_duplicate_handover', output, one_continuation=True, lease_retained=True)

c = fresh(lambda q: case(q, 'failure'))
def retry_save(q):
    q._locks()
    q._test_return_source(ReturnSource(c['execution'], c['target'], True))
    return handover(q, c)
output = ordered((c['doctor'], 0, lambda q: handover(q, c)), (c['doctor'], 0, retry_save))
assert 'rejected' in output[0]['value'] and 'continuation_task_id' in output[1]['value']
assert not assert_patient(c)
record('T08_save_failure_vs_trusted_retry', output, no_half_handover=True, one_successful_save=True)

def result_notification(q):
    # A future fixed S09 result source calls this under the same complete locks.
    # A result cannot authorize handover or save a draft itself.
    q._locks()
    execution = q._model('execution').browse(c['execution'])
    assert execution.state == 'handover'
    task = q._continuation(execution)
    return {'task_id': task.id}
output = parallel([('frontdesk', 0, result_notification), ('frontdesk', 1, result_notification)])
assert output[0]['value']['task_id'] == output[1]['value']['task_id']
record('T08_two_result_notifications_reuse_continuation', output, one_pending_continuation=True)

c = fresh(lambda q: case(q, 'append'))
output = parallel([('frontdesk', 0, lambda q: q._operate('append', {'task_id': c['task'], 'reason': 'explicit concurrent append'})),
                   ('frontdesk', 1, lambda q: q._operate('append', {'task_id': c['task'], 'reason': 'explicit concurrent append'}))])
assert output[0]['value']['permit_id'] == output[1]['value']['permit_id']
fresh(lambda q: q._operate('revoke', {'permit_id': output[0]['value']['permit_id'], 'reason': 'retire synthetic permit'}), 'frontdesk')
record('T09_duplicate_append_same_task', output, one_active_permit=True, no_capacity_added=True)

for first_name in ('revoke', 'start'):
    c = fresh(lambda q: case(q, 'append'))
    permit = fresh(lambda q: q._operate('append', {'task_id': c['task'], 'reason': 'explicit concurrency append'}), 'frontdesk')
    call = fresh(lambda q: q._operate('call', args(c['lease'])), c['doctor'])
    actions = [('frontdesk', 0, lambda q: q._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'atomic revoke'})),
               (c['doctor'], 0, lambda q: q._operate('start', dict(args(c['lease']), entry_id=call['entry_id'])))]
    if first_name == 'start':
        actions.reverse()
    output = ordered(*actions)
    assert 'rejected' not in output[0]['value'] and 'rejected' in output[1]['value']
    assert assert_patient(c) == ([c['task']] if first_name == 'start' else [])
    record('T10_' + first_name + '_commits_first', output, no_capacity_returned=True, no_started_fact_erased=True)

for first_name in ('timeout', 'restore'):
    c = fresh(lambda q: case(q))
    def timeout_hold(q):
        q._locks()
        q._model('lease').browse(c['lease']['lease_id'])._save({'ydental_expires_at': q._now() - timedelta(seconds=1)})
        return {'expired': q._expire()}
    actions = [('manager', 0, timeout_hold), (c['doctor'], 0, lambda q: restore(q, c))]
    if first_name == 'restore':
        actions.reverse()
    output = ordered(*actions)
    if first_name == 'timeout':
        assert 'rejected' in output[1]['value'] and not assert_patient(c)
        assert fresh(lambda q: q._model('hold').browse(c['hold']).state) == 'verify'
    else:
        assert assert_patient(c) == [c['task']]
        assert fresh(lambda q: q._unresolved_execution(c['patient']).state) == 'verify'
    record('T06_hold_' + first_name + '_commits_first', output, no_automatic_completion=True)

c = fresh(lambda q: case(q))
output = parallel([(c['doctor'], 0, lambda q: q._operate('call', args(c['lease']))), (c['exam'], 0, lambda q: start_exam(q, c))])
assert 'rejected' in output[0]['value'] and assert_patient(c) == [c['target']]
record('T06_holding_doctor_call_vs_external_start', output, holding_doctor_cannot_call=True, external_serving_allowed=True)


# Rework additions: original A21/B12 above are retained intact.
for held in (False, True):
    c = fresh(lambda q: case(q, 'calling' if held else 'handover'))
    def expire_source(q):
        q._locks()
        q._model('lease').browse(c['lease']['lease_id'])._save({'ydental_expires_at': q._now() - timedelta(seconds=1)})
        q._expire()
    fresh(expire_source)
    def resolver_employee(q):
        root = q.env['base'].sudo().env
        user = new_test_user(root, name='S06C onsite resolver', login='s06c_' + key(),
                             password='s06c-synthetic-only', groups='ydental_base.ydental_base_group_user')
        q.env['ydental.access.service']._join(user.id, store_id)
        q.env['ydental.access.service']._grant(user.id, store_id, {'medical': 'write'})
        user.write({'ydental_capability_ids': [fields.Command.set(root['ydental.intake.mapping'].browse(maps).ydental_catalog_id.ydental_capability_id.ids)]})
        role = 'onsite_' + key()
        users[role] = user.id
        intake = bind(SimpleNamespace(root=root, stores=root['ydental.access.store'].browse(store_id)), user)
        sessions[role] = [intake.env['ydental.access.service']._scope().id]
        connections[role] = [key() + key()]
        return role
    resolver = fresh(resolver_employee)
    operation = 'handover_verify_hold' if held else 'takeover_verify'
    payload = {'execution_id': c['execution'], 'confirmed': True, 'reason': 'Two qualified people physically inspecting original station'}
    # The original actor and a distinct qualified employee both attempt the
    # same original station, with different server sessions/connections.
    output = parallel([(c['doctor'], 0, lambda q: q._operate(operation, payload)),
                       (resolver, 0, lambda q: q._operate(operation, payload))])
    winners = [v['value'] for v in output if 'rejected' not in v['value']]
    assert len(winners) == 1
    new_lease = winners[0]['lease_id']
    assert new_lease != c['lease']['lease_id']
    assert fresh(lambda q: q._model('execution').browse(c['execution']).state) == ('handover' if held else 'interrupted')
    if held:
        assert fresh(lambda q: q._model('hold').browse(c['hold']).ydental_resolution_lease_id.id) == new_lease
        assert not assert_patient(c)
    else:
        assert assert_patient(c) == [c['task']]
    record('B_REWORK_verify_' + ('hold' if held else 'execution') + '_two_people', output,
           exactly_one_success=True, new_bound_lease=True, old_identity_preserved=True, no_treatment_completion=True)

c = fresh(lambda q: case(q, 'calling'))
def care_target(q):
    front = service(q.env.cr, 'frontdesk').env['ydental.intake.service']
    task = front._model('task').browse(c['task'])
    return front._new('task', task.ydental_store_id, dict(front._identity(task.ydental_patient_id),
        name='Unrelated synthetic Care task', ydental_mapping_id=maps[0], ydental_parent_task_id=task.id,
        ydental_source_kind='derived')).id
care_id = fresh(care_target)
def report_task(q, task_id):
    intake = q.env['ydental.intake.service']
    task = intake._model('task').browse(task_id)
    return intake._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
output = parallel([('frontdesk', 0, lambda q: report_task(q, care_id)),
                   ('frontdesk', 1, lambda q: report_task(q, c['target']))])
assert 'rejected' in output[0]['value'] and 'rejected' not in output[1]['value']
record('B_REWORK_hold_unrelated_care_vs_trusted_external_report', output, care_denied=True, trusted_exam_allowed=True)

c = fresh(lambda q: case(q, 'append'))
permit = fresh(lambda q: q._operate('append', {'task_id': c['task'], 'reason': 'Rework reopen qualification'}), 'frontdesk')
call = fresh(lambda q: q._operate('call', args(c['lease'])), c['doctor'])
fresh(lambda q: q._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'Rework revoke stopped exception'}), 'frontdesk')
def reopen(q):
    q._locks()
    store = q.env['ydental.access.store'].sudo().browse(store_id)
    business = q.env['ydental.supply.service']._business_record(store, q.env['ydental.intake.mapping'].sudo().browse(maps[0]).ydental_area_id.id)
    business._save({'state': 'open'})  # guarded synthetic S03 input, not C
    return {'result': 'open'}
output = ordered(('manager', 0, reopen), ('frontdesk', 0, lambda q: report_task(q, c['task'])))
assert all('rejected' not in v['value'] for v in output)
call = fresh(lambda q: q._operate('call', args(c['lease'])), c['doctor'])
fresh(lambda q: q._operate('start', dict(args(c['lease']), entry_id=call['entry_id'])), c['doctor'])
assert assert_patient(c) == [c['task']]
assert fresh(lambda q: q._model('append.permit').browse(permit['permit_id']).state) == 'revoked'
record('B_REWORK_revoked_reopen_vs_ordinary_report_then_start', output, same_task=True, historical_revoke_retained=True, no_new_permit=True)


def invariants(q):
    q.env.flush_all()
    for table, field, predicate in (
        ('ydental_queue_execution', 'ydental_patient_id', "state IN ('serving', 'verify')"),
        ('ydental_queue_execution', 'ydental_lease_id', "state IN ('serving', 'verify')"),
        ('ydental_queue_execution', 'ydental_entry_id', 'ydental_entry_id IS NOT NULL'),
        ('ydental_queue_hold', 'ydental_patient_id', "state IN ('active', 'verify')"),
        ('ydental_queue_append_permit', 'ydental_task_id', "state IN ('active', 'started')")):
        from odoo.tools import SQL
        q.env.cr.execute(SQL('SELECT %s FROM %s WHERE %s GROUP BY %s HAVING count(*)>1',
            SQL.identifier(field), SQL.identifier(table), SQL(predicate), SQL.identifier(field)))
        assert not q.env.cr.fetchall()
    return {'one_actual_execution': True, 'one_entry_start': True, 'one_hold': True, 'one_permit': True}


result['invariants'] = fresh(invariants)

# Independent browser fixtures, still synthetic and in this newly recorded DB.
from odoo.addons.ydental_queue_test.models.return_adapter import ReturnPlan
browser_access, browser_cases = {}, {}
with registry.cursor() as cr:
    for kind in ('hold', 'external_serving', 'save_failure', 'append_start', 'append_revoke', 'pharmacy'):
        f = SimpleNamespace(env=api.Environment(cr, 1, {}))
        setup(f)
        root = f.root
        if kind == 'pharmacy':
            f.catalogs[2]._save({'ydental_kind': 'medicine'})
            f.stations[0][2].write({'ydental_kind': 'pharmacy', 'ydental_version': f.stations[0][2].ydental_version})
            f.admin._grant(f.users['doctor'].id, f.stores[0].id, {'medical': 'none', 'exam': 'none', 'pharmacy': 'write'})
        task = accepted(f, mapping=f.mappings[0][2] if kind == 'pharmacy' else f.mappings[0][0])
        target = f.front._new('task', f.stores[0], dict(f.front._identity(task.ydental_patient_id),
            name='S06C synthetic examination task', ydental_mapping_id=f.mappings[0][2].id,
            ydental_parent_task_id=task.id, ydental_source_kind='derived')) if kind != 'pharmacy' else False
        f.front.env['ydental.queue.service']._test_return_plan(ReturnPlan(task.id, target.id if target else 0, kind != 'save_failure'))
        if kind.startswith('append'):
            close(f)
            f.admin._grant(f.users['price'].id, f.stores[0].id, {'frontdesk': 'write'})
            f.users['price'].write({'group_ids': [(4, root.ref('ydental_queue.ydental_group_append').id)]})
        next_task = accepted(f) if kind == 'hold' else False
        browser_cases[kind] = {'store': f.stores[0].id, 'station': f.stations[0][2].id if kind == 'pharmacy' else f.stations[0][0].id,
            'other_station': f.other_station.id, 'exam_station': f.stations[0][2].id, 'task': task.id,
            'target': target.id if target else 0, 'patient': task.ydental_patient_id.id, 'next_task': next_task.id if next_task else 0}
        for role in ('doctor', 'frontdesk', 'second', 'manager', 'price'):
            user = f.second if role == 'second' else f.users[role]
            browser_access[kind + '_' + role] = {'id': user.id, 'login': user.login, 'password': 's06c-ui-synthetic-only'}
            user.password = browser_access[kind + '_' + role]['password']
    root['ir.config_parameter'].set_str('ydental_queue.timeout_seconds', '20')
    cr.commit()
private(run / 'access-b.json', browser_access)
private(run / 'preview-b.json', browser_cases)
# Dedicated rework UI fixtures. Their source and time transitions are trusted
# synthetic setup, never an HTTP force-release or client source declaration.
from odoo.addons.ydental_queue_test.tests.return_common import serving as ui_serving, reserve as ui_reserve, source as ui_source, external as ui_external
rework_access, rework_cases = {}, {}
with registry.cursor() as cr:
    for kind in ('verify_execution', 'verify_hold', 'hold_targets', 'revoked_reopen'):
        f = SimpleNamespace(env=api.Environment(cr, 1, {}))
        setup(f)
        if kind == 'revoked_reopen':
            task = accepted(f)
            close(f)
            app = appender(f)
            permit = app._operate('append', {'task_id': task.id, 'reason': 'UI historical closed append'})
            app._operate('revoke', {'permit_id': permit['permit_id'], 'reason': 'UI exception revoked'})
            app.env['ydental.supply.service']._business_record(f.stores[0], f.areas[0][0].id)._save({'state': 'open'})
            c = {'task': task.id, 'permit': permit['permit_id']}
        else:
            q, lease, execution = ui_serving(f)
            ui_source(q, execution)
            c = {'task': execution.ydental_task_id.id, 'execution': execution.id}
            if kind != 'verify_execution':
                hold, target = ui_reserve(f, q, lease, execution)
                c.update(hold=hold.id, target=target.id)
                if kind == 'hold_targets':
                    care = ui_external(f, execution, f.mappings[0][0], independent=True)
                    extra = ui_external(f, execution)
                    untrusted = ui_external(f, execution)
                    ui_source(q, execution, extra)
                    c.update(care=care.id, extra=extra.id, untrusted=untrusted.id)
            if kind.startswith('verify'):
                execution.ydental_lease_id._save({'ydental_expires_at': q._now() - timedelta(seconds=1)})
                q._timeout()
        c.update(store=f.stores[0].id, station=f.stations[0][0].id, exam_station=f.stations[0][2].id)
        rework_cases[kind] = c
        for role in ('doctor', 'frontdesk', 'second'):
            user = f.second if role == 'second' else f.users[role]
            user.password = 's06c-ui-synthetic-only'
            rework_access[kind + '_' + role] = {'id': user.id, 'login': user.login, 'password': 's06c-ui-synthetic-only'}
    cr.commit()
private(run / 'access-rework.json', rework_access)
private(run / 'preview-rework.json', rework_cases)
result.update(result='PASS', deadlocks=0)
save_attempt()
print(json.dumps({'result': 'PASS', 'races': len(result['races']), 'a_regression_races': 21, 'deadlocks': 0}))
