"""First-barrier native PostgreSQL race on the same refund approval."""
import json
import os
import time
from pathlib import Path

from psycopg2.errors import SerializationFailure
from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
actor = os.environ['YDENTAL_S10_ACTOR']
assert actor in ('a', 'b')
fixture = json.loads((run / 'approval-race-fixture.json').read_text())
request_key = key()
for attempt in range(1, 4):
    try:
        with env.registry.cursor() as cr:
            root = api.Environment(cr, 1, {})
            index = 0 if actor == 'a' else 1
            user = root['res.users'].browse(fixture['approver_ids'][index])
            session = root['ydental.access.session'].sudo().browse(
                fixture['session_ids'][index])
            service = root['ydental.access.service'].with_user(user)._bind(session).env[
                'ydental.settlement.service']
            cr.execute('SELECT pg_backend_pid()')
            backend = cr.fetchone()[0]
            if attempt == 1:
                marker = run / ('approval-barrier-' + actor + '.json')
                marker.write_text(json.dumps({'backend_pid': backend}) + '\n')
                other = run / ('approval-barrier-' + ('b' if actor == 'a' else 'a') + '.json')
                for _ in range(1200):
                    if other.exists():
                        break
                    time.sleep(0.05)
                else:
                    raise AssertionError('Second approver did not reach PostgreSQL barrier')
            try:
                result = service._operate('refund_approve', {
                    'refund_id': fixture['refund_id'],
                    'reason': 'Independent concurrent finance approval'}, request_key)
                outcome = 'accepted'
            except (AccessError, UserError) as error:
                outcome = 'rejected'
                result = {'code': str(error).split(':')[0]}
            cr.commit()
        break
    except SerializationFailure:
        assert attempt < 3, 'Bounded approval serialization retry exhausted'
evidence = {'actor': actor, 'user_id': user.id, 'backend_pid': backend,
    'attempt': attempt, 'outcome': outcome, 'result': result}
(run / ('approval-actor-' + actor + '.json')).write_text(json.dumps(evidence) + '\n')
print('S10_APPROVAL_RACE', json.dumps(evidence), flush=True)
