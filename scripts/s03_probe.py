"""Seed only a recorded fresh S03 database and verify actual two-connection races."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from datetime import timedelta
import json
import os
from pathlib import Path
import re
import secrets
import threading
from unittest.mock import patch

import psycopg2

from odoo import api, fields
from odoo.exceptions import UserError
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from s03_fixtures import setup_supply, slot, acquire, acquire_args, new_test_user


run = Path(os.environ['YDENTAL_S03_RUN_DIR'])
metadata = json.loads((run / 'database.json').read_text())
assert re.fullmatch(r'ydental_s03_test_[0-9]{14}_[a-f0-9]{8}', metadata['database'])
assert env.cr.dbname == metadata['database']
assert not (run / 'access.json').exists(), 'Preview already seeded'
registry = env.registry


class Fixture:
    pass


with registry.cursor() as cr:
    fixture = Fixture()
    fixture.env = api.Environment(cr, api.SUPERUSER_ID, {})
    setup_supply(fixture)
    f = fixture
    access = {}
    for role in ('writer', 'reader', 'staff'):
        user = f.root['res.users'].browse(f.__dict__[role].id)
        login = 's03_' + secrets.token_hex(6) + '@example.invalid'
        password = secrets.token_urlsafe(24)
        user.write({'login': login, 'password': password, 'email': login, 'lang': 'zh_CN'})
        access[role] = {'id': user.id, 'login': login, 'password': password}
    sessions = []
    for key in ('race-one', 'race-two'):
        service = f.root['ydental.access.service'].with_user(f.writer)
        session = service._session_for_key(key + '-' + f.suffix)
        service._bind(session)._switch(f.stores[0].id)
        sessions.append(session.id)
    scenarios = []
    for index, name in enumerate(('last_capacity', 'reservation_first', 'conversion_first', 'cancel_start', 'repeat_cancel', 'source_move')):
        record = slot(f, start=f.start + timedelta(days=index), end=f.end + timedelta(days=index), total=3, key=name)
        if name in ('cancel_start', 'repeat_cancel'):
            claim = acquire(f, record, key=name)
            pair = [('cancel', {'id': claim.id, 'reason': 'Synthetic concurrent cancellation'}),
                    ('consume' if name == 'cancel_start' else 'cancel', {'id': claim.id} if name == 'cancel_start' else {'id': claim.id, 'reason': 'Synthetic duplicate cancellation'})]
        elif name == 'source_move':
            old = slot(f, station=f.stations[0], start=record.ydental_start, end=record.ydental_end, total=3, key='move-old')
            claim = acquire(f, old, key='move-original')
            pair = [('reassign', {'id': claim.id, 'slot_id': record.id, 'reason': 'Concurrent source move'}),
                    ('acquire', acquire_args(f, record, 'race-fill', capability=f.capabilities[1]))]
        elif name in ('reservation_first', 'conversion_first'):
            pair = [('acquire', acquire_args(f, record, 'race-reservation')), ('convert', {'id': record.id})]
        else:
            pair = [('acquire', acquire_args(f, record, name + '-clean')),
                    ('acquire', acquire_args(f, record, name + '-fill', capability=f.capabilities[1]))]
        if name in ('reservation_first', 'conversion_first'):
            with patch.object(type(f.service), '_now', return_value=record.ydental_start - timedelta(seconds=1)):
                f.service._operate('business', {'area_id': f.area.id, 'state': 'open', 'reason': 'Synthetic boundary business day'}, 'boundary-open-' + name)
        scenarios.append({'name': name, 'slot_id': record.id, 'start': fields.Datetime.to_string(record.ydental_start), 'actions': pair})
    now = fields.Datetime.now()
    today = f.service._operate('assign', {'user_id': f.staff.id, 'station_id': f.stations[0].id,
        'start': fields.Datetime.to_string(now - timedelta(minutes=5)), 'end': fields.Datetime.to_string(now + timedelta(hours=2))}, 'preview-today')
    previous_week = now - timedelta(days=7)
    f.service._operate('assign', {'user_id': f.replacement.id, 'area_id': f.area.id,
        'start': fields.Datetime.to_string(previous_week), 'end': fields.Datetime.to_string(previous_week + timedelta(hours=1))}, 'preview-previous-week')
    user_id, store_id, area_id = f.writer.id, f.stores[0].id, f.area.id
    summary = {'database': cr.dbname, 'stores': f.stores.ids, 'station_ids': f.stations.ids,
        'area_id': area_id, 'capability_ids': f.capabilities.ids, 'today_assignment_id': today['id'],
        'staff_id': f.staff.id, 'replacement_id': f.replacement.id, 'synthetic_only': True}
    cr.commit()  # Own cursor; guarded fresh S03 fixtures only.


results = []
for scenario in scenarios:
    barrier = threading.Barrier(2)
    first_acquired = threading.Event()
    second_waiting = threading.Event()
    local = threading.local()
    Supply = type(env['ydental.supply.service'])
    original_lock, original_now = Supply._lock, Supply._now
    ordered = scenario['name'] in ('reservation_first', 'conversion_first')
    first_index = 0 if scenario['name'] == 'reservation_first' else 1

    def ordered_lock(service):
        if local.index != first_index:
            assert first_acquired.wait(timeout=20)
            second_waiting.set()
        original_lock(service)
        if local.index == first_index:
            first_acquired.set()
            assert second_waiting.wait(timeout=20)

    def server_clock(service):
        if not ordered:
            return original_now(service)
        boundary = fields.Datetime.to_datetime(scenario['start'])
        return boundary - timedelta(seconds=1) if local.index == 0 else boundary

    def worker(index):
        local.index = index
        operation, payload = scenario['actions'][index]
        attempts = []
        for attempt in range(5):
            try:
                with registry.cursor() as cr:
                    current = api.Environment(cr, user_id, {})
                    current['ydental.access.service']._require_internal()
                    session = current['ydental.access.session'].sudo().browse(sessions[index])
                    service = current['ydental.access.service']._bind(session).env['ydental.supply.service']
                    cr.execute('SELECT pg_backend_pid(), current_setting(%s)', ['transaction_isolation'])
                    pid, isolation = cr.fetchone()
                    attempts.append({'pid': pid, 'isolation': isolation, 'attempt': attempt + 1})
                    if attempt == 0:
                        barrier.wait(timeout=20)
                    result = service._operate(operation, payload, scenario['name'] + str(index)) if operation == 'convert' else service._capacity_action(operation, payload, scenario['name'] + str(index))
                    cr.commit()  # Own independent connection, actual transaction.
                    return {'action': operation, 'result': 'accepted', 'receipt': result, 'attempts': attempts}
            except psycopg2.errors.SerializationFailure:
                attempts[-1]['result'] = 'serialization_retry'
                continue
            except UserError as error:
                # Only stable public error categories, no raw exception/log upload.
                return {'action': operation, 'result': 'rejected', 'reason': 'insufficient_balance' if 'insufficient_balance:' in str(error) else 'state_conflict', 'attempts': attempts}
        raise AssertionError('Bounded transaction retries exhausted')

    lock_patch = patch.object(Supply, '_lock', ordered_lock) if ordered else nullcontext()
    with lock_patch, patch.object(Supply, '_now', server_clock), ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(worker, (0, 1)))
    with registry.cursor() as cr:
        root = api.Environment(cr, api.SUPERUSER_ID, {})
        record = root['ydental.supply.slot'].browse(scenario['slot_id'])
        claims = root['ydental.supply.claim'].search([('ydental_slot_id', '=', record.id)])
        held = len(claims.filtered(lambda r: r.state in ('held', 'consumed')))
        counters = {'total': record.ydental_total, 'reservation': record.ydental_reservation_free,
            'walkin': record.ydental_walkin_free, 'unavailable': record.ydental_unavailable, 'used': held,
            'claim_states': claims.mapped('state')}
        progress = {'scenario': scenario['name'], 'outcomes': outcomes, 'after': counters}
        (run / ('concurrency-progress-' + scenario['name'] + '-' + f.suffix + '.json')).write_text(json.dumps(progress, indent=2) + '\n')
        assert counters['total'] == sum(counters[k] for k in ('reservation', 'walkin', 'unavailable', 'used'))
        assert len({o['attempts'][0]['pid'] for o in outcomes}) == 2
        if scenario['name'] in ('last_capacity', 'source_move', 'cancel_start'):
            assert sum(o['result'] == 'accepted' for o in outcomes) == 1
        if scenario['name'] == 'repeat_cancel':
            assert all(o['result'] == 'accepted' for o in outcomes)
            assert root['ydental.supply.event'].search_count([('ydental_slot_id', '=', record.id), ('ydental_operation', '=', 'cancel')]) == 1
        if scenario['name'] == 'conversion_first':
            assert outcomes[0]['result'] == 'rejected' and outcomes[1]['result'] == 'accepted'
            assert counters['reservation'] == 0 and counters['walkin'] == 3
        if scenario['name'] == 'reservation_first':
            assert all(o['result'] == 'accepted' for o in outcomes)
            assert counters['reservation'] == 0 and counters['walkin'] == 2 and counters['used'] == 1
        results.append({'scenario': scenario['name'], 'result': 'PASS', 'outcomes': outcomes, 'after': counters})

# Extra fixtures for the three directed rework boundaries. They are seeded only
# after all six unchanged capacity races have completed.
with registry.cursor() as cr:
    root = api.Environment(cr, api.SUPERUSER_ID, {})
    store = root['ydental.access.store'].browse(store_id)
    store.write({'ydental_timezone': 'America/New_York'})
    service = root['ydental.access.service'].with_user(user_id)._bind(
        root['ydental.access.session'].browse(sessions[0])).env['ydental.supply.service']
    login, password = 's03_' + secrets.token_hex(6) + '@example.invalid', secrets.token_urlsafe(24)
    partial = new_test_user(root, name='S03 Synthetic Partial Staff', login=login, password=password,
        groups='ydental_base.ydental_base_group_user')
    admin = root['ydental.access.service'].with_user(f.manager.id)
    admin._bind(admin._session_for_key('rework-preview-admin-' + f.suffix))._join(partial.id, store.id)
    partial.write({'login': login, 'email': login, 'password': password, 'lang': 'zh_CN',
        'ydental_capability_ids': [fields.Command.set(summary['capability_ids'][:1])]})
    access['partial_staff'] = {'id': partial.id, 'login': login, 'password': password}
    now = fields.Datetime.now()
    common = {'user_id': partial.id, 'start': fields.Datetime.to_string(now),
        'end': fields.Datetime.to_string(now + timedelta(hours=1))}
    area_assignment = service._operate('assign', dict(common, area_id=area_id), 'rework-preview-area')
    direct_assignment = service._operate('assign', {'user_id': partial.id, 'station_id': summary['station_ids'][1],
        'start': fields.Datetime.to_string(now + timedelta(hours=1)),
        'end': fields.Datetime.to_string(now + timedelta(hours=2))}, 'rework-preview-direct')
    future = now + timedelta(days=10)
    handling = service._operate('assign', {'user_id': user_id, 'station_id': summary['station_ids'][0],
        'start': fields.Datetime.to_string(future), 'end': fields.Datetime.to_string(future + timedelta(hours=1))}, 'rework-preview-handling')
    assignment = root['ydental.supply.assignment'].browse(handling['id'])
    root['resource.calendar.leaves'].create({'name': 'Synthetic rework absence without a capacity slot',
        'resource_id': assignment.ydental_employee_id.resource_id.id,
        'date_from': assignment.ydental_start, 'date_to': assignment.ydental_end})
    disposition = root['ydental.supply.disposition'].search([
        ('ydental_assignment_id', '=', assignment.id), ('ydental_slot_id', '=', False), ('state', '=', 'pending')])
    assert len(disposition) == 1
    source_ids = []
    for index, wall in enumerate(('2026-10-25T23:30', '2026-10-26T00:30', '2026-11-01T23:30')):
        instant = service._local_to_utc(store, wall)
        source = service._operate('assign', {'user_id': user_id, 'area_id': area_id,
            'start': fields.Datetime.to_string(instant), 'end': fields.Datetime.to_string(instant + timedelta(minutes=15))}, 'rework-preview-dst-' + str(index))
        source_ids.append(source['id'])
    summary['rework'] = {'timezone': store.ydental_timezone, 'area_assignment_id': area_assignment['id'],
        'direct_assignment_id': direct_assignment['id'], 'handling_assignment_id': assignment.id,
        'handling_disposition_id': disposition.id, 'dst_source_ids': source_ids[1:], 'dst_excluded_id': source_ids[0]}
    cr.commit()  # Own cursor, guarded new S03 synthetic preview only.

# Preserve credentials privately. Evidence contains synthetic object IDs only.
with os.fdopen(os.open(run / 'access.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as handle:
    json.dump(access, handle)
(run / 'preview.json').write_text(json.dumps(summary, indent=2) + '\n')
(run / 'concurrency.json').write_text(json.dumps({'database': metadata['database'], 'scenarios': results}, indent=2) + '\n')
print(json.dumps({'synthetic_preview': summary, 'concurrency': results}))
