from .common import accepted, arrive_report, bind, key, lease_args, qualify, queue_bind
from ..models.return_adapter import ReturnSource


def serving(cls, user=None, station=None, task=None):
    task = task if task is not None else accepted(cls)
    queue = queue_bind(cls, user=user)
    lease = queue._operate('enter', {'station_id': (station or cls.stations[0][0]).id})
    call = queue._operate('call', lease_args(lease))
    assert call['task_id'] == task.id
    execution = queue._operate('start', dict(lease_args(lease), entry_id=call['entry_id']))
    return queue, lease, cls.root['ydental.queue.execution'].browse(execution['execution_id'])


def external(cls, execution, mapping=None, independent=False):
    intake = cls.front
    if independent:
        q = qualify(cls, patient_id=execution.ydental_patient_id.id, mapping=mapping or cls.mappings[0][2])
        task = cls.root['ydental.intake.task'].browse(q['task_id'])
    else:
        target = mapping or cls.mappings[0][2]
        task = intake._new('task', cls.stores[0], dict(intake._identity(execution.ydental_patient_id),
            name='S06B synthetic external order task', ydental_mapping_id=target.id,
            ydental_parent_task_id=execution.ydental_task_id.id, ydental_source_kind='derived'))
    return task


def source(queue, execution, task=None, save_ok=True, document_key=''):
    return queue._test_return_source(ReturnSource(execution.id, task.id if task is not None else 0, save_ok, document_key))


def reserve(cls, queue, lease, execution, task=None):
    task = task if task is not None else external(cls, execution)
    source(queue, execution, task)
    result = queue._operate('reserve', dict(lease_args(lease), execution_id=execution.id, target_task_id=task.id))
    return cls.root['ydental.queue.hold'].browse(result['hold_id']), task


def report(cls, task):
    return cls.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())


def close(cls, area=None):
    # B consumes an existing S03 closed state. It does not test or implement C's
    # draining/clear transition, whose lower hook remains fail-closed.
    from ..models.adapter import guard
    guard(cls.root)
    supply = cls.group.env['ydental.supply.service']
    record = supply._business_record(cls.stores[0], (area or cls.areas[0][0]).id)
    record._save({'state': 'closed', 'ydental_reason': 'Guarded synthetic B closed input'})


def appender(cls):
    cls.users['frontdesk'].write({'group_ids': [(4, cls.root.ref('ydental_queue.ydental_group_append').id)]})
    return cls.front.env['ydental.queue.service']
