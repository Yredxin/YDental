"""S05 real PostgreSQL races on a recorded isolated database.

Each manual commit owns a newly opened fixture/worker cursor. Business services
never commit. Raw logs and access secrets stay in the private run directory.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
from threading import Barrier, Event
from types import SimpleNamespace

import psycopg2

from odoo import api, fields
from odoo.exceptions import UserError
from odoo.addons.ydental_intake_test.tests.common import setup, bind, key, patient, qualify, arrive_report, make_slot, price


run = Path(os.environ['YDENTAL_S05_RUN_DIR'])
assert re.fullmatch(r'ydental_s05_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) and run.name == env.cr.dbname
registry = env.registry
result = {'scope': 'S05 real multi-connection database races, S03/S04 real integration, queue synthetic only',
    'database': env.cr.dbname, 'started_utc': datetime.now(timezone.utc).isoformat(), 'races': []}


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
                'total': 90, 'reason': 'Synthetic race capacity'}, key())
    users = {role: u.id for role, u in fixture.users.items()}
    sessions = {}
    for role in ('manager', 'frontdesk', 'doctor'):
        sessions[role] = []
        for i in range(2):
            service = bind(fixture, fixture.users[role])
            sessions[role].append(service.env['ydental.access.service']._scope().id)
    maps = [[m.id for m in mappings] for mappings in fixture.mappings]
    areas = [[a.id for a in group] for group in fixture.areas]
    stations = [[s.id for s in group] for group in fixture.stations]
    stores = fixture.stores.ids
    start, end = fields.Datetime.to_string(fixture.start), fields.Datetime.to_string(fixture.end)
    catalog_id, currency_id = fixture.catalogs[0].id, fixture.currency.id
    browser_person = patient(fixture)
    browser_q = qualify(fixture, browser_person)
    browser_other = qualify(fixture, browser_person, fixture.mappings[0][1])
    initial_price = price(fixture)
    preview = {'stores': stores, 'patient_id': browser_person, 'qualification': browser_q, 'other': browser_other,
        'catalog_id': catalog_id, 'currency_id': currency_id, 'mappings': maps, 'start': start, 'end': end,
        'price_id': initial_price['id']}
    access = {}
    for role, user in fixture.users.items():
        password = secrets.token_urlsafe(24)
        user.write({'password': password, 'lang': 'en_US'})
        access[role] = {'id': user.id, 'login': user.login, 'password': password}
    cr.commit()  # This probe owns its fresh fixture cursor.
private(run / 'access.json', access)
private(run / 'preview.json', preview)


def service_for(cr, role='frontdesk', n=0):
    root = api.Environment(cr, users[role], {})
    access = root['ydental.access.service']
    session = root['ydental.access.session'].sudo().browse(sessions[role][n])
    return access._bind(session).env['ydental.intake.service']


def fresh(callback, role='manager'):
    with registry.cursor() as cr:
        service = service_for(cr, role)
        value = callback(service)
        cr.commit()  # Own cursor, only isolated synthetic state.
        return value


def execute(callback, role='frontdesk', n=0, barrier=None, hold=None, ready=None):
    for attempt in range(1, 13):
        try:
            with registry.cursor() as cr:
                service = service_for(cr, role, n)
                cr.execute('SELECT ydental_revision FROM ydental_patient_mutex')
                cr.fetchone()  # Establish independent RR snapshots before locks.
                if attempt == 1 and ready:
                    ready.set()
                if attempt == 1 and barrier:
                    barrier.wait(timeout=20)
                try:
                    value = callback(service)
                except UserError as error:
                    value = {'rejected': str(error)}
                if attempt == 1 and hold:
                    hold[0].set()
                    assert hold[1].wait(timeout=20)
                cr.commit()  # Worker owns this cursor. No business method commits.
                return {'value': value, 'attempts': attempt}
        except psycopg2.errors.SerializationFailure:
            if attempt == 12:
                raise
    # DeadlockDetected is deliberately not retried/hidden.


def parallel(calls):
    barrier = Barrier(len(calls))
    with ThreadPoolExecutor(max_workers=len(calls)) as pool:
        futures = [pool.submit(execute, cb, role, i, barrier) for i, (role, cb) in enumerate(calls)]
        return [future.result(timeout=90) for future in futures]


def ordered(first, second):
    entered, release, ready = Event(), Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(execute, first[1], first[0], 0, None, (entered, release))
        assert entered.wait(timeout=30)
        b = pool.submit(execute, second[1], second[0], 1, None, None, ready)
        assert ready.wait(timeout=20)
        release.set()
        return [a.result(timeout=90), b.result(timeout=90)]


def record(name, output, **checks):
    result['races'].append({'name': name, 'result': 'PASS', 'connections': len(output),
        'attempts': [r['attempts'] for r in output], 'outcomes': ['rejected' if 'rejected' in r['value'] else r['value'].get('result', 'accepted') for r in output], **checks})


def new_patient(service):
    return service.env['ydental.patient.service']._operate('create', {'values': {'name': 'S05 Race Synthetic Person'}}, key())['id']


def new_q(service, pid, mapping_id=None, channel='reservation', slot_start=None, slot_end=None):
    return service._operate('reserve' if channel == 'reservation' else 'register', {'patient_id': pid,
        'mapping_id': mapping_id or maps[0][0], 'start': slot_start or start, 'end': slot_end or end}, key())


def prepare_pair(service):
    pid = new_patient(service)
    a, b = new_q(service, pid), new_q(service, pid, maps[0][1])
    service._operate('arrive', {'patient_id': pid}, key())
    return pid, a, b


pid, a, b = fresh(prepare_pair)
output = parallel([('frontdesk', lambda s, q=q: s._operate('report', {'task_id': q['task_id'], 'version': q['task_version']}, key())) for q in (a, b)])
def check_position(s):
    root = s.env['base'].sudo().env
    assert root['ydental.intake.position'].search_count([('ydental_patient_id', '=', pid), ('ydental_active', '=', True)]) == 1
    assert root['ydental.intake.test.queue'].search_count([('ydental_patient_id', '=', pid), ('ydental_active', '=', True)]) == 1
fresh(check_position)
record('T04_same_patient_different_areas', output, one_position=True, one_synthetic_waiting=True)

for first_kind in ('report', 'stop'):
    pid, a, _ = fresh(prepare_pair)
    def reporting(s, q=a):
        return s._operate('report', {'task_id': q['task_id'], 'version': q['task_version']}, key())
    def stop(s):
        supply = s.env['ydental.supply.service']
        business = supply._business_record(s.env['ydental.access.service']._scope().ydental_store_id, areas[0][0])
        return supply._operate('business', {'area_id': areas[0][0], 'version': business.ydental_version,
            'state': 'draining', 'reason': 'Synthetic stop race'}, key())
    output = ordered(('frontdesk', reporting), ('manager', stop)) if first_kind == 'report' else ordered(('manager', stop), ('frontdesk', reporting))
    assert ('rejected' not in output[0]['value'] and 'rejected' not in output[1]['value']) if first_kind == 'report' else 'rejected' in output[1]['value']
    def verify(s, kind=first_kind, pid=pid):
        positions = s.env['ydental.intake.position'].sudo().search([('ydental_patient_id', '=', pid), ('ydental_active', '=', True)])
        assert len(positions) == (1 if kind == 'report' else 0)
        if positions:
            t = positions.ydental_task_id
            s._operate('void', {'task_id': t.id, 'version': t.ydental_version, 'reason': 'Synthetic queue drain'}, key())
        supply = s.env['ydental.supply.service']
        store = s.env['ydental.access.service']._scope().ydental_store_id
        business = supply._business_record(store, areas[0][0])
        supply._operate('business', {'area_id': areas[0][0], 'version': business.ydental_version,
            'state': 'open', 'reason': 'Synthetic reopen'}, key())
    fresh(verify)
    record('T05_' + first_kind + '_before_' + ('stop' if first_kind == 'report' else 'report'), output, no_half_intake=True)

q = fresh(lambda s: new_q(s, new_patient(s)))
args = {'record_id': q['id'], 'version': q['version'], 'reason': 'Synthetic concurrent cancellation'}
output = parallel([('frontdesk', lambda s: s._operate('cancel', args, key())) for _ in range(2)])
assert sum('rejected' in r['value'] for r in output) == 1
fresh(lambda s: (s.env['ydental.intake.entitlement'].sudo().browse(q['id']).state == 'cancelled') or (_ for _ in ()).throw(AssertionError()))
record('T06_duplicate_cancel_competition', output, returned_once=True)

for first_kind in ('cancel', 'consume'):
    def preparation(s):
        q = new_q(s, new_patient(s))
        s._operate('arrive', {'patient_id': q['patient_id']}, key())
        p = s._operate('report', {'task_id': q['task_id'], 'version': q['task_version']}, key())
        return q, p
    q, p = fresh(preparation)
    cancel = ('manager', lambda s, q=q: s._operate('cancel', {'record_id': q['id'], 'version': q['version'], 'reason': 'Cancel versus consume'}, key()))
    consume = ('manager', lambda s, q=q, p=p: s._downstream_action('start', {'task_id': q['task_id'], 'version': p['version']}, key()))
    output = ordered(cancel, consume) if first_kind == 'cancel' else ordered(consume, cancel)
    assert 'rejected' not in output[0]['value'] and 'rejected' in output[1]['value']
    def check_claim(s, q=q, kind=first_kind):
        e = s.env['ydental.intake.entitlement'].sudo().browse(q['id'])
        assert (e.state, e.ydental_claim_id.state) == (('cancelled', 'cancelled') if kind == 'cancel' else ('started', 'consumed'))
        assert s.env['ydental.supply.event'].sudo().search_count([('ydental_claim_id', '=', e.ydental_claim_id.id), ('ydental_operation', '=', 'cancel')]) == (1 if kind == 'cancel' else 0)
    fresh(check_claim)
    record('T06_' + first_kind + '_before_' + ('consume' if first_kind == 'cancel' else 'cancel'), output, no_double_return=True)

# A real target last-sale wins before the concurrent reschedule snapshot retries.
def prepare_full(s):
    pid = new_patient(s)
    q = new_q(s, pid)
    s._operate('arrive', {'patient_id': pid}, key())
    p = s._operate('report', {'task_id': q['task_id'], 'version': q['task_version']}, key())
    station = s.env['ydental.space.station'].sudo().browse(stations[0][0])
    begin = fields.Datetime.to_datetime(start) + timedelta(hours=3)
    endtime = fields.Datetime.to_datetime(end) + timedelta(hours=3)
    box = SimpleNamespace(root=s.env['base'].sudo().env, users={'manager': s.env.user})
    slot = make_slot(box, s, station, begin, endtime, total=3)
    return q, p, fields.Datetime.to_string(begin), fields.Datetime.to_string(endtime), new_patient(s)
q, p, ts, te, otherpid = fresh(prepare_full)
output = ordered(('frontdesk', lambda s: new_q(s, otherpid, slot_start=ts, slot_end=te)),
    ('frontdesk', lambda s: s._operate('reschedule', {'record_id': q['id'], 'version': q['version'],
        'mapping_id': maps[0][0], 'start': ts, 'end': te, 'reason': 'Concurrent full target'}, key())))
assert 'rejected' in output[1]['value']
def preserved(s):
    e = s.env['ydental.intake.entitlement'].sudo().browse(q['id'])
    assert e.ydental_claim_id.id == q['claim_id'] and e.ydental_version == q['version']
    assert s.env['ydental.intake.position'].sudo().browse(p['id']).ydental_active
fresh(preserved)
record('T06_reschedule_vs_target_last_sale', output, original_claim_and_position_preserved=True)

# Two real source clinicians compete for one target reservation.
def prepare_referral(s):
    q = new_q(s, new_patient(s))
    target = s.env['ydental.intake.mapping'].sudo().browse(maps[1][0])
    station = s.env['ydental.space.station'].sudo().browse(stations[1][0])
    manager_b = bind(SimpleNamespace(root=s.env['base'].sudo().env), s.env.user, target.ydental_store_id)
    box = SimpleNamespace(root=s.env['base'].sudo().env, users={'manager': s.env.user})
    begin, ending = fields.Datetime.to_datetime(start) + timedelta(hours=4), fields.Datetime.to_datetime(end) + timedelta(hours=4)
    slot = make_slot(box, manager_b, station, begin, ending, total=3)
    return q, fields.Datetime.to_string(begin), fields.Datetime.to_string(ending), slot.id
q, ts, te, target_slot = fresh(prepare_referral)
args = {'source_task_id': q['task_id'], 'version': q['task_version'], 'mapping_id': maps[1][0],
    'start': ts, 'end': te, 'reason': 'Synthetic cross-store target last capacity'}
output = parallel([('doctor', lambda s: s._operate('refer_timed', args, key())) for _ in range(2)])
assert sum('rejected' in r['value'] for r in output) == 1
def check_referral(s):
    root = s.env['base'].sudo().env
    assert root['ydental.intake.entitlement'].search_count([('ydental_source_task_id', '=', q['task_id'])]) == 1
    assert root['ydental.supply.slot'].browse(target_slot).ydental_reservation_free == 0
fresh(check_referral)
record('T11_timed_referral_target_last_capacity', output, one_target_claim=True, no_half_referral=True)

for channel in ('reservation', 'walkin'):
    for first_kind in ('business', 'merge'):
        def prepare_merge(s):
            source, target = new_patient(s), new_patient(s)
            q = new_q(s, source)
            request = s.env['ydental.patient.service']._operate('request_merge', {'source_id': source, 'target_id': target,
                'reason': 'S05 real activity identity conflict'}, key())
            return source, target, q, request
        source, target, q, request = fresh(prepare_merge)
        business = ('frontdesk', lambda s, pid=target, c=channel: new_q(s, pid, channel=c))
        confirmation = ('manager', lambda s, r=request: s.env['ydental.patient.service']._operate('confirm',
            {'request_id': r['id'], 'version': r['version'], 'reason': 'S05 concurrent verified merge'}, key()))
        output = ordered(business, confirmation) if first_kind == 'business' else ordered(confirmation, business)
        if first_kind == 'business':
            assert output[1]['value']['result'] == 'conflict_requires_resolution'
        else:
            assert output[0]['value']['result'] == 'accepted' and 'rejected' not in output[1]['value']
        def check_merge(s, source=source, target=target, q=q, kind=first_kind):
            root = s.env['base'].sudo().env
            original = root['ydental.intake.task'].browse(q['task_id'])
            assert original.ydental_origin_patient_id.id == source
            assert original.ydental_patient_id.id == (source if kind == 'business' else target)
            assert bool(root['ydental.patient'].browse(source).ydental_merged_into_id) == (kind == 'merge')
        fresh(check_merge)
        record('T09_' + first_kind + '_before_' + channel + '_merge_race', output, real_s05_objects=True, canonical_references=True)

# Publication and snapshot are serialized together, including native rule updates.
def prepare_price(s):
    begin = fields.Datetime.now() + timedelta(minutes=1)
    p = s._operate('price', {'catalog_id': catalog_id, 'currency_id': currency_id, 'unit_price': 620,
        'start': fields.Datetime.to_string(begin), 'end': fields.Datetime.to_string(begin + timedelta(days=30)),
        'reason': 'Synthetic concurrent new price'}, key())
    reviewed = s._operate('review', {'record_id': p['id'], 'version': p['version'], 'reason': 'Synthetic review'}, key())
    old = s.env['ydental.intake.price'].sudo().browse(initial_price['id'])
    return reviewed, old.ydental_version, fields.Datetime.to_string(begin)
new_price, old_version, price_start = fresh(prepare_price)
publication = ('manager', lambda s: s._operate('publish', {'record_id': new_price['id'], 'version': new_price['version'],
    'replace_id': initial_price['id'], 'replace_version': old_version, 'reason': 'Synthetic price publication race'}, key()))
snapshot_args = {'catalog_id': catalog_id, 'currency_id': currency_id, 'quantity': 1,
    'source': 'race-original-snapshot', 'policy': 'demo_confirmation'}
output = parallel([publication, ('manager', lambda s: s._operate('snapshot', snapshot_args, key()))])
assert all('rejected' not in r['value'] for r in output) and output[1]['value']['amount'] == 600
recovered = fresh(lambda s: s._operate('snapshot', snapshot_args, key()))
assert recovered['amount'] == 600 and recovered['price_id'] == initial_price['id']
record('T13_price_publication_vs_snapshot_and_recovery', output, frozen_version=initial_price['id'], amount=600)

with registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    slots = root['ydental.supply.slot'].search([])
    for slot in slots:
        held = root['ydental.supply.claim'].search_count([('ydental_slot_id', '=', slot.id), ('state', 'in', ['held', 'consumed'])])
        assert slot.ydental_reservation_free + slot.ydental_walkin_free + slot.ydental_unavailable + held == slot.ydental_total
    positions = root['ydental.intake.position'].search([('ydental_active', '=', True)])
    assert len(positions.ydental_patient_id) == len(positions)
    tasks = root['ydental.intake.task'].search([('state', 'in', ['pending', 'accepted', 'started'])])
    assert all(not task.ydental_patient_id.ydental_merged_into_id for task in tasks)
    result['invariants'] = {'single_position': True, 's03_capacity_conservation': True,
        'live_tasks_canonical': True, 'deadlocks': 0, 'real_queue_and_clinical_execution': 'NOT_RUN'}
result['finished_utc'] = datetime.now(timezone.utc).isoformat()
result['tested_commit'] = __import__('subprocess').check_output(['git', '-C', str(run.parents[1]), 'rev-parse', 'HEAD'], text=True).strip()
target = run.parents[1] / 'docs/evidence/s05/probe-attempts' / (run.name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'probe': 'PASS', 'races': len(result['races']), 'evidence': str(target)}))
