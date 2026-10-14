import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from odoo import api
from odoo.exceptions import UserError
from psycopg2.errors import SerializationFailure
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
actor = os.environ['YDENTAL_S10_ACTOR']
assert actor in ('a', 'b')
fixture = json.loads((run / 'close-race-fixture.json').read_text())
request_key = key()
for attempt in range(1, 4):
    try:
        with env.registry.cursor() as cr:
            root = api.Environment(cr, 1, {})
            user = root['res.users'].browse(fixture['manager_id'])
            session = root['ydental.access.session'].sudo().browse(
                fixture['session_ids'][0 if actor == 'a' else 1])
            service = root['ydental.access.service'].with_user(user)._bind(session).env[
                'ydental.settlement.service']
            cr.execute('SELECT pg_backend_pid()')
            backend = cr.fetchone()[0]
            if attempt == 1:
                marker = run / ('close-race-barrier-' + actor + '.json')
                marker.write_text(json.dumps({'backend_pid': backend}) + '\n')
                other = run / ('close-race-barrier-' + ('b' if actor == 'a' else 'a') + '.json')
                for _ in range(2400):
                    if other.is_file():
                        break
                    time.sleep(.05)
                else:
                    raise AssertionError('Second PostgreSQL backend did not reach close barrier')
            try:
                if actor == 'a':
                    result = service._operate('close', {'business_date': fixture['business_date'],
                        'channel': 'card'}, request_key)
                else:
                    result = service._operate('pay', {'invoice_ids': [fixture['invoice_id']],
                        'amount': 1, 'channel': 'card',
                        'actual_utc': datetime.now(timezone.utc).isoformat(),
                        'proof': 'Actual synthetic contested card payment'}, request_key)
                outcome = 'accepted'
            except UserError as error:
                outcome = 'rejected'
                result = {'code': str(error).split(':')[0]}
            cr.commit()
        break
    except SerializationFailure:
        assert attempt < 3, 'Bounded close serialization retry exhausted'
evidence = {'actor': actor, 'backend_pid': backend, 'attempt': attempt,
    'outcome': outcome, 'result': result}
(run / ('close-race-actor-' + actor + '.json')).write_text(json.dumps(evidence) + '\n')
print('S10_CLOSE_RACE', json.dumps(evidence), flush=True)
