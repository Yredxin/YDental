import json
import os
import time
from pathlib import Path
from odoo import api
from odoo.exceptions import UserError
from psycopg2.errors import SerializationFailure
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
actor = os.environ['YDENTAL_S10_ACTOR']
assert actor in ('a', 'b')
fixture = json.loads((run / 'refund-race-fixture.json').read_text())
session_id = fixture['session_ids'][0 if actor == 'a' else 1]
request_key = key()
for attempt in range(1, 4):
    try:
        with env.registry.cursor() as cr:
            root = api.Environment(cr, 1, {})
            manager = root['res.users'].browse(fixture['manager_id'])
            session = root['ydental.access.session'].sudo().browse(session_id)
            service = root['ydental.access.service'].with_user(manager)._bind(session).env['ydental.settlement.service']
            cr.execute('SELECT pg_backend_pid()')
            backend = cr.fetchone()[0]
            payment = root['ydental.settlement.payment'].browse(fixture['payment_id'])
            assert payment.ydental_amount == 500
            if attempt == 1:
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
                    'request_key': request_key}, request_key)
                outcome = 'accepted'
            except UserError as error:
                result = {'code': str(error).split(':')[0]}
                outcome = 'rejected'
            cr.commit()
        break
    except SerializationFailure:
        assert attempt < 3, 'Bounded refund serialization retry exhausted'
else:
    raise AssertionError('Bounded refund serialization retry exhausted')
evidence = {'actor': actor, 'backend_pid': backend, 'attempt': attempt,
    'outcome': outcome, 'result': result}
(run / ('refund-race-actor-' + actor + '.json')).write_text(json.dumps(evidence) + '\n')
print('S10_REFUND_RACE', json.dumps(evidence), flush=True)
