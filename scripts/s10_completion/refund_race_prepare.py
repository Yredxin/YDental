import json
import os
from pathlib import Path

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'f1.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    manager = root['res.users'].browse(fixture['manager_id'])
    access = root['ydental.access.service'].with_user(manager)
    sessions = []
    for _ in range(2):
        session = access._session_for_key(key())
        access._bind(session)._switch(fixture['store_id'])
        sessions.append(session.id)
    cr.commit()
    assert sessions[0] != sessions[1]
    (run / 'refund-race-fixture.json').write_text(json.dumps({
        'payment_id': fixture['payment500_id'], 'store_id': fixture['store_id'],
        'manager_id': manager.id, 'session_ids': sessions}) + '\n')
    print('S10_REFUND_RACE_PREPARED', sessions, flush=True)
