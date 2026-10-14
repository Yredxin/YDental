"""Prepare one protected refund for two different finance approvers."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import AccessError
from odoo.addons.ydental_treatment_test.tests.common import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    fixture = json.loads((run / 'f1.json').read_text())
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    frontdesk = root['res.users'].browse(fixture['frontdesk_id'])
    doctor = root['res.users'].browse(fixture['doctor_id'])
    holder = SimpleNamespace(root=root, stores=[store])
    manager_access = bind(holder, manager).env['ydental.access.service']
    manager_access._grant(doctor.id, store.id, {
        'settlement': 'write', 'finance_approval': 'write'})
    service = bind(holder, manager).env['ydental.settlement.service']
    payment = root['ydental.settlement.payment'].browse(fixture['payment240_id'])
    requested = service._operate('refund_request', {'payment_id': payment.id,
        'amount': 10, 'reason': 'One request reviewed by two real people',
        'request_key': key()}, key())
    try:
        service._operate('refund_approve', {'refund_id': requested['refund_id'],
            'reason': 'Forbidden self approval'}, key())
    except AccessError:
        pass
    else:
        raise AssertionError('Requester self-approved')
    sessions = []
    for user in (frontdesk, doctor):
        access = root['ydental.access.service'].with_user(user)
        session = access._session_for_key(key())
        access._bind(session)._switch(store.id)
        sessions.append(session.id)
    assert not root['ydental.settlement.refund'].browse(
        requested['refund_id']).ydental_native_payment_id
    cr.commit()
    data = {'store_id': store.id, 'manager_id': manager.id,
        'approver_ids': [frontdesk.id, doctor.id], 'session_ids': sessions,
        'refund_id': requested['refund_id'], 'payment_id': payment.id}
    (run / 'approval-race-fixture.json').write_text(json.dumps(data) + '\n')
    print('S10_APPROVAL_RACE_PREPARED', json.dumps(data), flush=True)
