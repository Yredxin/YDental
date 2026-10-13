import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import UserError
from odoo.addons.ydental_treatment_test.tests.common import key, bind

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
actor = os.environ['YDENTAL_S10_ACTOR']
assert actor in ('a', 'b')
fixture = json.loads((run / 'f1.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    service = bind(SimpleNamespace(root=root, stores=[store]), manager).env['ydental.settlement.service']
    cr.execute('SELECT pg_backend_pid()')
    backend = cr.fetchone()[0]
    payment = root['ydental.settlement.payment'].browse(fixture['payment500_id'])
    assert payment.ydental_amount == 500
    marker = run / ('refund-race-barrier-' + actor + '.json')
    marker.write_text(json.dumps({'backend_pid': backend}) + '\n')
    other = run / ('refund-race-barrier-' + ('b' if actor == 'a' else 'a') + '.json')
    for _ in range(2400):
        if other.is_file():
            break
        time.sleep(.05)
    else:
        raise AssertionError('Second PostgreSQL backend did not reach refund barrier')
    try:
        result = service._operate('refund_request', {
            'payment_id': payment.id, 'amount': 300, 'reason': 'Competing protected request',
            'request_key': key()}, key())
        outcome = 'accepted'
    except UserError as error:
        result = {'code': str(error).split(':')[0]}
        outcome = 'rejected'
    cr.commit()
    evidence = {'actor': actor, 'backend_pid': backend, 'outcome': outcome, 'result': result}
    (run / ('refund-race-actor-' + actor + '.json')).write_text(json.dumps(evidence) + '\n')
    print('S10_REFUND_RACE', json.dumps(evidence), flush=True)
