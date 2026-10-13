"""Committed synthetic examination queue races on independent PostgreSQL backends."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import patch
import json
import os
import re
import time

import psycopg2
from odoo import api, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.addons.ydental_treatment_test.tests.common import (
    key, handover_args, lease_args, make_slot, queue_bind, price, save_args, serving,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual

run = Path(os.environ['YDENTAL_S09_RUN_DIR'])
assert run.name == env.cr.dbname and re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname)
record = {'database': env.cr.dbname, 'cases': [], 'deadlocks': 0}


def job(service, operation, payload):
    return {'uid': service.env.uid, 'context': dict(service.env.context),
            'model': service._name, 'operation': operation, 'payload': payload, 'key': key()}


def race(name, jobs):
    barrier = Barrier(2, timeout=20)
    trace = [[], []]

    def worker(index):
        first_pid = None
        for attempt in range(5):
            try:
                with env.registry.cursor() as cr:
                    cr.execute('SET LOCAL lock_timeout = %s', ['12s'])
                    cr.execute('SELECT pg_backend_pid()')
                    pid = cr.fetchone()[0]
                    if first_pid is None:
                        first_pid = pid
                    trace[index].append({'attempt': attempt, 'pid': pid, 'phase': 'connected',
                                         'time_ns': time.monotonic_ns()})
                    if attempt == 0:
                        barrier.wait()
                        trace[index].append({'attempt': attempt, 'pid': pid, 'phase': 'barrier_released',
                                             'time_ns': time.monotonic_ns()})
                    request = jobs[index]
                    service = api.Environment(cr, request['uid'], request['context'])[request['model']]
                    try:
                        answer = service._operate(request['operation'], request['payload'], request['key']) if (
                            request['model'] != 'ydental.queue.service') else service._operate(
                                request['operation'], request['payload'])
                        cr.commit()
                        return {'result': 'accepted', 'first_pid': first_pid, 'pid': pid,
                                'answer': answer}
                    except psycopg2.errors.SerializationFailure:
                        cr.rollback()
                        trace[index].append({'attempt': attempt, 'pid': pid, 'phase': 'serialization_retry',
                                             'time_ns': time.monotonic_ns()})
                    except (AccessError, UserError, ValidationError) as error:
                        cr.rollback()
                        return {'result': 'rejected', 'first_pid': first_pid, 'pid': pid,
                                'code': str(error).split(':')[0]}
            except psycopg2.errors.DeadlockDetected:
                record['deadlocks'] += 1
                raise
        raise AssertionError('Bounded serialization retries exhausted')

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(worker, index) for index in range(2)]
        outcomes = [future.result(timeout=80) for future in futures]
    first_pids = [row['first_pid'] for row in outcomes]
    assert len(set(first_pids)) == 2, (name, first_pids)
    result = {'case': name, 'initial_backend_pids': first_pids,
              'outcomes': outcomes, 'trace': trace}
    record['cases'].append(result)
    return result


with env.registry.cursor() as cr:
    fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(fixture)
    fixture.admin._grant(fixture.users['manager'].id, fixture.stores[0].id, {'exam': 'write'})
    original = fixture.stations[0][2]
    twin = fixture.root['ydental.space.station'].create({
        'name': 'S09 synthetic second panorama station',
        'ydental_store_id': fixture.stores[0].id,
        'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': original.ydental_area_id.id,
        'ydental_kind': 'exam',
        'ydental_add_capability_ids': [fields.Command.set(fixture.capabilities[2].ids)],
    })
    make_slot(fixture, fixture.group, twin, fixture.start, fixture.end)
    with patch.object(type(fixture.group.env['ydental.supply.service']),
                      '_allow_demo_supply', return_value=True):
        treatment, clinical, doctor_queue, doctor_lease, medical, document, args = opened_actual(fixture)
    line = {'mapping_id': fixture.mappings[0][2].id, 'quantity': 1,
            'uom_id': fixture.uom.id, 'product_id': False, 'specification': '',
            'usage': '', 'frequency': '', 'course': ''}
    order = treatment._operate('order', args | {'kind': 'exam',
        'purpose': 'Synthetic competing panorama stations', 'lines': [line]}, key())
    issued = treatment._operate('issue', args | {'order_id': order['order_id'],
        'version': order['version']}, key())
    clinical._operate('handover', handover_args(document, doctor_lease))
    task = fixture.root['ydental.intake.task'].browse(issued['task_ids'][0])
    record['patient_id'] = medical.ydental_patient_id.id
    fixture.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
    queue_a = queue_bind(fixture, fixture.second)
    queue_b = queue_bind(fixture, fixture.users['manager'])
    lease_a = queue_a._operate('enter', {'station_id': original.id})
    lease_b = queue_b._operate('enter', {'station_id': twin.id})
    call_jobs = [job(queue_a, 'call', lease_args(lease_a)),
                 job(queue_b, 'call', lease_args(lease_b))]
    cr.commit()

called = race('T01_two_panorama_stations_one_task', call_jobs)
accepted = [row for row in called['outcomes'] if row['result'] == 'accepted']
assert len(accepted) == 1, called
winner = called['outcomes'].index(accepted[0])
entry_id = accepted[0]['answer']['entry_id']
start_payload = call_jobs[winner]['payload'] | {'entry_id': entry_id}
started = race('T01_same_called_entry_two_backends', [
    dict(call_jobs[winner], operation='start', payload=start_payload),
    dict(call_jobs[winner], operation='start', payload=start_payload),
])
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    executions = root['ydental.queue.execution'].search([('ydental_task_id', '=', task.id)])
    assert len(executions) == 1 and executions.state == 'serving', executions.ids
    assert root['ydental.treatment.line'].browse(issued['line_ids'][0]).state == 'started'
    record['execution_ids'] = executions.ids
    record['line_id'] = issued['line_ids'][0]

with env.registry.cursor() as cr:
    fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(fixture)
    with patch.object(type(fixture.group.env['ydental.supply.service']),
                      '_allow_demo_supply', return_value=True):
        treatment, clinical, doctor_queue, doctor_lease, medical, document, args = opened_actual(fixture)
    line = {'mapping_id': fixture.mappings[0][2].id, 'quantity': 1,
            'uom_id': fixture.uom.id, 'product_id': False, 'specification': '',
            'usage': '', 'frequency': '', 'course': ''}
    order = treatment._operate('order', args | {'kind': 'exam',
        'purpose': 'Synthetic restore versus real examination start', 'lines': [line]}, key())
    issued = treatment._operate('issue', args | {'order_id': order['order_id'],
        'version': order['version']}, key())
    held = doctor_queue._operate('reserve', lease_args(doctor_lease) | {
        'execution_id': medical.id, 'target_task_id': issued['task_ids'][0]})
    task_id = issued['task_ids'][0]
    task = fixture.root['ydental.intake.task'].browse(task_id)
    fixture.front._operate('report', {'task_id': task_id, 'version': task.ydental_version}, key())
    examiner = queue_bind(fixture, fixture.second)
    exam_lease = examiner._operate('enter', {'station_id': fixture.stations[0][2].id})
    called = examiner._operate('call', lease_args(exam_lease))
    assert called['task_id'] == task_id
    restore_job = job(doctor_queue, 'restore', lease_args(doctor_lease) | {
        'hold_id': held['hold_id'], 'confirmed': True})
    start_job = job(examiner, 'start', lease_args(exam_lease) | {'entry_id': called['entry_id']})
    record['T07_patient_id'] = medical.ydental_patient_id.id
    cr.commit()

restored = race('T07_restore_versus_exam_start', [restore_job, start_job])
assert sum(row['result'] == 'accepted' for row in restored['outcomes']) == 1, restored
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    active = root['ydental.queue.execution'].search([
        ('ydental_patient_id', '=', record['T07_patient_id']),
        ('state', 'in', ('serving', 'verify'))])
    assert len(active) == 1, active.ids
    record['T07_active_execution'] = active.ids

with env.registry.cursor() as cr:
    fixture = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(fixture)
    original = fixture.stations[0][0]
    chair = fixture.root['ydental.space.station'].create({
        'name': 'Synthetic inline cancel-start race chair',
        'ydental_store_id': fixture.stores[0].id,
        'ydental_floor_id': original.ydental_floor_id.id,
        'ydental_area_id': original.ydental_area_id.id, 'ydental_kind': 'care',
        'ydental_add_capability_ids': [fields.Command.set(
            fixture.capabilities[0].ids + fixture.capabilities[2].ids)],
    })
    make_slot(fixture, fixture.group, chair, fixture.start, fixture.end)
    price(fixture, 80, catalog=fixture.catalogs[2])
    with patch.object(type(fixture.group.env['ydental.supply.service']),
                      '_allow_demo_supply', return_value=True):
        doctor_queue, lease, medical = serving(fixture, station=chair)
    clinical = doctor_queue.env['ydental.clinical.service']
    document = clinical._operate('open', {'execution_id': medical.id,
        'lease_id': lease['lease_id'], 'lease_token': lease['token']})
    document.update(clinical._operate('save', save_args(document)))
    treatment = doctor_queue.env['ydental.treatment.service']
    args = {'execution_id': medical.id, 'lease_id': lease['lease_id'],
        'lease_token': lease['token'], 'document_id': document['document_id'],
        'document_version': document['version']}
    line = {'mapping_id': fixture.mappings[0][2].id, 'quantity': 1,
            'uom_id': fixture.uom.id, 'product_id': False, 'specification': '',
            'usage': '', 'frequency': '', 'course': ''}
    order = treatment._operate('order', args | {'kind': 'exam',
        'purpose': 'Synthetic unperformed cancel versus actual inline exam', 'lines': [line]}, key())
    issued = treatment._operate('issue', args | {'order_id': order['order_id'],
        'version': order['version']}, key())
    exam = doctor_queue.env['ydental.exam.service']
    exam._operate('bind_template', {'catalog_id': fixture.catalogs[2].id,
        'code': 'panorama-demo-1', 'reason': 'Explicit synthetic reviewed template'}, key())
    line_id = issued['line_ids'][0]
    assert exam._actual(fixture.root['ydental.treatment.line'].browse(line_id), medical.id,
                        lease['lease_id'], lease['token'], True).id == medical.id
    record['T05_before_race'] = 'both_actions_eligible'
    perform_job = job(exam, 'perform', {'line_id': line_id, 'execution_id': medical.id,
        'lease_id': lease['lease_id'], 'lease_token': lease['token'], 'inline': True,
        'reason': 'Actual synthetic inline examination', 'materials': []})
    cancel_job = job(treatment, 'cancel_exam', args | {'line_id': line_id,
        'order_version': issued['version'], 'reason': 'Cancel only if still unperformed'})
    cr.commit()

cancelled = race('T05_unperformed_cancel_versus_inline_actual', [perform_job, cancel_job])
assert sum(row['result'] == 'accepted' for row in cancelled['outcomes']) == 1, cancelled
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    line = root['ydental.treatment.line'].browse(line_id)
    events = root['ydental.treatment.event'].search([('ydental_order_line_id', '=', line_id)])
    fees = root['ydental.treatment.fee'].search([('ydental_event_id', 'in', events.ids)])
    assert (line.state == 'cancelled' and not events and not fees) or (
        line.state == 'done' and len(events) == 1 and len(fees) == 1)
    record['T05_final_line_state'] = line.state
    record['T05_event_ids'] = events.ids
    record['T05_fee_ids'] = fees.ids

run.joinpath('race-result-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.json').write_text(
    json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print('S09_RACE_RESULT', json.dumps(record, ensure_ascii=False))
