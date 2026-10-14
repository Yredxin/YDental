"""First-barrier race of close against real refund or native reclassification."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from psycopg2.errors import SerializationFailure
from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
actor = os.environ['YDENTAL_S10_ACTOR']
mode = os.environ['YDENTAL_S10_RACE_MODE']
assert actor in ('a', 'b') and mode in ('refund', 'reclassify')
fixture = json.loads((run / 'finance-race-fixture.json').read_text())
request_key = key()
for attempt in range(1, 4):
    try:
        with env.registry.cursor() as cr:
            root = api.Environment(cr, 1, {})
            manager = root['res.users'].browse(fixture['manager_id'])
            session = root['ydental.access.session'].sudo().browse(
                fixture['session_ids'][0 if actor == 'a' else 1])
            service = root['ydental.access.service'].with_user(manager)._bind(session).env[
                'ydental.settlement.service']
            cr.execute('SELECT pg_backend_pid()')
            backend = cr.fetchone()[0]
            if attempt == 1:
                marker = run / ('finance-' + mode + '-barrier-' + actor + '.json')
                marker.write_text(json.dumps({'backend_pid': backend}) + '\n')
                other = run / ('finance-' + mode + '-barrier-' + ('b' if actor == 'a' else 'a') + '.json')
                for _ in range(1200):
                    if other.exists():
                        break
                    time.sleep(0.05)
                else:
                    raise AssertionError('Second PostgreSQL backend did not reach barrier')
            try:
                if actor == 'a':
                    result = service._operate('close', {'business_date': fixture['business_date'],
                        'channel': 'card' if mode == 'refund' else 'cash'}, request_key)
                elif mode == 'refund':
                    result = service._operate('refund_execute', {
                        'refund_id': fixture['refund_id'],
                        'actual_utc': datetime.now(timezone.utc).isoformat(),
                        'proof': 'Actual synthetic contested card refund'}, request_key)
                else:
                    result = service._operate('reclassify', {
                        'payment_id': fixture['cash_payment_id'], 'new_channel': 'wechat',
                        'reason': 'Actual synthetic cash label was WeChat'}, request_key)
                outcome = 'accepted'
            except (AccessError, UserError) as error:
                result = {'code': str(error).split(':')[0]}
                outcome = 'rejected'
            cr.commit()
        break
    except SerializationFailure:
        assert attempt < 3, 'Bounded native serialization retry exhausted'
evidence = {'mode': mode, 'actor': actor, 'backend_pid': backend,
    'attempt': attempt, 'outcome': outcome, 'result': result}
(run / ('finance-' + mode + '-actor-' + actor + '.json')).write_text(json.dumps(evidence) + '\n')
print('S10_FINANCE_RACE', json.dumps(evidence), flush=True)
