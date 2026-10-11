"""Private S04 shell probe: synthetic fixtures and real multi-cursor races.

The guarded runner supplies env only for its recorded fresh S04 database.
Every manual commit below owns a newly opened cursor; no business service
commits. Public evidence contains synthetic identifiers and aggregate results.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
from threading import Barrier, Event
from types import SimpleNamespace

import psycopg2

from odoo import api
from odoo.exceptions import UserError
from odoo.addons.ydental_patient_test.tests.common import setup_patient, bind, create, merge, clinical


run = Path(os.environ['YDENTAL_S04_RUN_DIR'])
assert re.fullmatch(r'ydental_s04_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname)
assert run.name == env.cr.dbname
registry = env.registry
result = {'scope': 'S04 real database concurrency with synthetic identities and active-reference adapter',
          'database': env.cr.dbname, 'started_utc': datetime.now(timezone.utc).isoformat(), 'races': []}


def private(path, data):
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as f:
        json.dump(data, f, indent=2)


with registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    fixture = SimpleNamespace(env=root)
    setup_patient(fixture)
    user_id = fixture.users['frontdesk'].id
    group_id = fixture.manager.id
    store_id = fixture.stores[0].id
    sessions = []
    for i in range(8):
        service = bind(fixture, fixture.users['frontdesk'], 'race-' + str(i))
        sessions.append(service.env['ydental.access.service']._scope().id)
    group_sessions = []
    for i in range(2):
        service = bind(fixture, fixture.manager, 'group-race-' + str(i))
        group_sessions.append(service.env['ydental.access.service']._scope().id)
    original = create(fixture, name='S04 Browser Original', phone='+1 202 555 0100')
    same_phone = create(fixture, name='S04 Browser Shared Phone', phone='2025550100', phone_region='US')
    clinical_id = clinical(fixture, original['id'], fixture.stores[2], 'S04 SYNTHETIC CROSS STORE BACKGROUND')['id']
    b_service = bind(fixture, fixture.manager, 'browser-b-only', fixture.stores[1])
    b_only = create(fixture, service=b_service, name='S04 Browser B Only')
    b_history = clinical(fixture, b_only['id'], fixture.stores[1], 'S04 SYNTHETIC B ONLY HISTORY')['id']
    guardian = fixture.service._operate('contact', {'patient_id': original['id'], 'name': 'S04 Browser Protected Guardian',
        'relation': 'guardian', 'relationship': 'Declared guardian, synthetic'}, 'browser-protected-guardian')
    primary_partner = root['ydental.patient'].browse(original['id']).ydental_partner_id
    guardian_partner = root['ydental.patient.contact'].browse(guardian['id']).ydental_partner_id
    ordinary_partner = root['res.partner'].create({'name': 'S04 Browser Ordinary Contact'})
    credential_values = {}
    for role, user in fixture.users.items():
        password = secrets.token_urlsafe(24)
        user.write({'password': password, 'lang': 'zh_CN' if role != 'reader' else 'en_US'})
        credential_values[role] = {'id': user.id, 'login': user.login, 'password': password}
    preview = {'stores': fixture.stores.ids, 'original': original, 'same_phone': same_phone,
               'clinical_id': clinical_id, 'suffix': fixture.suffix, 'b_only': b_only, 'b_history': b_history,
               'protected_partners': (primary_partner | guardian_partner).ids, 'ordinary_partner': ordinary_partner.id,
               'contacts_action': root.ref('base.action_partner_form').id}
    cr.commit()  # New private fixture cursor, persist only this synthetic run.
private(run / 'access.json', credential_values)
private(run / 'preview.json', preview)


def service_for(cr, actor, session_id):
    root = api.Environment(cr, actor, {})
    access = root['ydental.access.service']
    session = root['ydental.access.session'].sudo().browse(session_id)
    return access._bind(session).env['ydental.patient.service']


def execute(actor, session_id, callback, barrier=None, started=None, hold=None, ready=None):
    attempts = 0
    while True:
        attempts += 1
        try:
            with registry.cursor() as cr:
                service = service_for(cr, actor, session_id)
                # Establish independent RR snapshots before contending.
                cr.execute('SELECT ydental_revision FROM ydental_patient_mutex')
                cr.fetchone()
                if attempts == 1 and ready:
                    ready.set()
                if attempts == 1 and barrier:
                    barrier.wait(timeout=20)
                if attempts == 1 and started:
                    started.wait(timeout=20)
                try:
                    value = callback(service)
                except UserError as error:
                    value = {'rejected': str(error)}
                if attempts == 1 and hold:
                    hold[0].set()
                    assert hold[1].wait(timeout=20)
                cr.commit()  # This worker owns its new cursor and transaction.
                return {'value': value, 'attempts': attempts}
        except (psycopg2.errors.SerializationFailure, psycopg2.errors.DeadlockDetected):
            if attempts >= 12:
                raise


def run_parallel(callbacks):
    barrier = Barrier(len(callbacks))
    with ThreadPoolExecutor(max_workers=len(callbacks)) as pool:
        futures = [pool.submit(execute, actor, session, callback, barrier) for actor, session, callback in callbacks]
        return [future.result(timeout=90) for future in futures]


numbers = run_parallel([(user_id, session, lambda service, i=i: service._operate('create',
    {'values': {'name': 'S04 Concurrent Number ' + str(i)}}, 'number-race-' + str(i))) for i, session in enumerate(sessions)])
assert len({r['value']['number'] for r in numbers}) == 8
assert all(r['value']['result'] == 'accepted' for r in numbers)
result['races'].append({'name': 'eight_concurrent_patient_numbers', 'result': 'PASS', 'connections': 8,
                        'unique_numbers': 8, 'attempts': [r['attempts'] for r in numbers]})

retry = run_parallel([(user_id, session, lambda service: service._operate('create',
    {'values': {'name': 'S04 Retry Identity'}}, 'same-create-key')) for session in sessions[:2]])
assert len({r['value']['id'] for r in retry}) == 1
assert sorted(r['value']['result'] for r in retry) == ['accepted', 'already_accepted']
result['races'].append({'name': 'same_creation_idempotency_key', 'result': 'PASS', 'connections': 2,
                        'single_identity': True, 'attempts': [r['attempts'] for r in retry]})


def pair(label, source_active=False):
    with registry.cursor() as cr:
        service = service_for(cr, user_id, sessions[0])
        source = service._operate('create', {'values': {'name': label + ' Source'}}, label + '-source')
        target = service._operate('create', {'values': {'name': label + ' Target'}}, label + '-target')
        activity = service._synthetic_start(source['id']) if source_active else None
        request = service._operate('request_merge', {'source_id': source['id'], 'target_id': target['id'],
            'reason': 'Synthetic concurrency verification'}, label + '-request')
        cr.commit()  # Own fixture cursor.
        return source, target, request, activity.id if activity else None


source, target, request, _ = pair('same-merge')
args = {'request_id': request['id'], 'version': request['version'], 'reason': 'Synthetic verified identity'}
merged = run_parallel([(group_id, session, lambda service: service._operate('confirm', args, 'same-merge-confirm'))
                       for session in group_sessions])
assert sorted(r['value']['result'] for r in merged) == ['accepted', 'already_accepted']
result['races'].append({'name': 'same_merge_idempotency_key', 'result': 'PASS', 'connections': 2,
                        'single_merge': True, 'attempts': [r['attempts'] for r in merged]})

source, target, request, _ = pair('different-merge-keys')
distinct = run_parallel([(group_id, session, lambda service, i=i: service._operate('confirm',
    {'request_id': request['id'], 'version': 1, 'reason': 'Synthetic distinct confirmations'},
    'different-confirm-' + str(i))) for i, session in enumerate(group_sessions)])
assert sum('rejected' in r['value'] for r in distinct) == 1
result['races'].append({'name': 'same_request_distinct_keys_version_protection', 'result': 'PASS',
                        'connections': 2, 'accepted': 1, 'rejected': 1, 'attempts': [r['attempts'] for r in distinct]})


def ordered(label, first, second):
    entered, release, ready = Event(), Event(), Event()
    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(execute, *first[:2], first[2], None, None, (entered, release))
        assert entered.wait(timeout=30)
        b = pool.submit(execute, *second[:2], second[2], None, entered, None, ready)
        assert ready.wait(timeout=20)
        release.set()
        output = [a.result(timeout=90), b.result(timeout=90)]
    return output


for first_kind in ('business', 'merge'):
    source, target, request, activity_id = pair(first_kind + '-first', source_active=True)
    args = {'request_id': request['id'], 'version': 1, 'reason': 'Synthetic concurrent identity verification'}
    business = (user_id, sessions[1], lambda service, pid=target['id']: {'id': service._synthetic_start(pid).id})
    confirmation = (group_id, group_sessions[0], lambda service, a=args: service._operate('confirm', a, first_kind + '-confirmation'))
    output = ordered(first_kind, business if first_kind == 'business' else confirmation,
                     confirmation if first_kind == 'business' else business)
    if first_kind == 'business':
        assert output[1]['value']['result'] == 'conflict_requires_resolution'
    else:
        assert output[0]['value']['result'] == 'accepted'
        assert 'rejected' in output[1]['value']
    with registry.cursor() as cr:
        check = api.Environment(cr, 1, {})
        identities = [source['id'], target['id']]
        active = check['ydental.patient.test.activity'].search([
            ('ydental_patient_id', 'in', identities), ('ydental_active', '=', True)])
        if first_kind == 'business':
            assert len(active) == 2 and not check['ydental.patient'].browse(source['id']).ydental_merged_into_id
        else:
            assert len(active) == 1 and active.ydental_patient_id.id == target['id']
    result['races'].append({'name': first_kind + '_before_merge' if first_kind == 'business' else 'merge_before_new_business',
        'result': 'PASS', 'connections': 2, 'outcomes': ['rejected' if 'rejected' in r['value'] else r['value'].get('result', 'accepted') for r in output],
        'attempts': [r['attempts'] for r in output]})

source, target, request, _ = pair('opposite')
with registry.cursor() as cr:
    service = service_for(cr, user_id, sessions[0])
    opposite = service._operate('request_merge', {'source_id': target['id'], 'target_id': source['id'],
        'reason': 'Synthetic opposing merge'}, 'reverse-opposite-request')
    cr.commit()  # Own fixture cursor.
opposed = run_parallel([(group_id, group_sessions[i], lambda service, request=request, i=i: service._operate('confirm',
    {'request_id': request['id'], 'version': 1, 'reason': 'Synthetic opposing verification'}, 'opposed-' + str(i)))
    for i, request in enumerate((request, opposite))])
assert sum('rejected' in r['value'] for r in opposed) == 1
result['races'].append({'name': 'opposing_merges_no_cycle', 'result': 'PASS', 'connections': 2,
                        'accepted': 1, 'rejected': 1, 'attempts': [r['attempts'] for r in opposed]})

with registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    numbers = root['ydental.patient.number'].search([])
    assert len(numbers.mapped('name')) == len(set(numbers.mapped('name')))
    assert all(not n.ydental_patient_id.ydental_merged_into_id for n in numbers)
    patients = root['ydental.patient'].with_context(active_test=False).search([])
    result['invariants'] = {'patient_numbers_unique': True, 'number_mappings_canonical': True,
        'patient_identities': len(patients), 'number_mappings': len(numbers),
        'no_patient_accounts': not any(p.ydental_partner_id.user_ids for p in patients)}
    result['fixture'] = {'user_id': user_id, 'group_id': group_id, 'store_id': store_id}
    result['merge_samples'] = [{
        'request_id': r.id, 'state': r.state, 'source_id': r.ydental_source_id.id,
        'target_id': r.ydental_target_id.id, 'counts': r.ydental_reference_counts,
        'conflicts': r.ydental_conflicts,
    } for r in root['ydental.patient.merge'].search([])]
    result['schema'] = {}
    for model_name in ('ydental.patient', 'ydental.patient.number', 'ydental.patient.relation',
                       'ydental.patient.contact', 'ydental.patient.clinical', 'ydental.patient.policy',
                       'ydental.patient.merge', 'ydental.patient.operation', 'ydental.patient.mutex'):
        model = root[model_name]
        described = model.fields_get()
        result['schema'][model_name] = [{
            'name': name, 'label': details['string'], 'type': details['type'],
            'required': details.get('required', False), 'readonly': details.get('readonly', False),
            'relation': details.get('relation'), 'selection': details.get('selection'),
            'groups': details.get('groups'), 'index': str(model._fields[name].index),
            'ondelete': model._fields[name].ondelete if details['type'] == 'many2one' else None,
            'has_default': bool(model._fields[name].default),
        } for name, details in described.items() if name.startswith('ydental_') or name in ('name', 'active', 'state')]
    result['ended_utc'] = datetime.now(timezone.utc).isoformat()
path = run / ('probe-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json')
private(path, result)
print(json.dumps({'probe': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'races': len(result['races']), 'result': 'PASS'}))
