"""Committed synthetic examination queue races on independent PostgreSQL backends."""
from concurrent.futures import ThreadPoolExecutor
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
    key, handover_args, lease_args, make_slot, queue_bind,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual

run = Path(os.environ['YDENTAL_S09_RUN_DIR'])
assert run.name == env.cr.dbname and re.fullmatch(r'ydental_s09_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname)
record = {'database': env.cr.dbname, 'cases': [], 'deadlocks': 0}


def job(service, operation, payload):
    return {'uid': service.env.uid, 'context': dict(service.env.context),
            'operation': operation, 'payload': payload}


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
                    service = api.Environment(cr, request['uid'], request['context'])['ydental.queue.service']
                    try:
                        answer = service._operate(request['operation'], request['payload'])
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
run.joinpath('race-result.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print('S09_RACE_RESULT', json.dumps(record, ensure_ascii=False))
