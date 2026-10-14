import json
import os
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'f5.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    invoice = root['account.move'].browse(fixture['new_invoice_ids'][3])
    assert invoice.amount_residual >= 1
    business_date = datetime.now(timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()
    assert not root['ydental.settlement.close'].search_count([
        ('ydental_store_id', '=', store.id), ('ydental_business_date', '=', business_date),
        ('ydental_channel', '=', 'card'), ('ydental_state', '=', 'confirmed')])
    access = root['ydental.access.service'].with_user(manager)
    sessions = []
    for _ in range(2):
        session = access._session_for_key(key())
        access._bind(session)._switch(store.id)
        sessions.append(session.id)
    cr.commit()
    (run / 'close-race-fixture.json').write_text(json.dumps({'store_id': store.id,
        'manager_id': manager.id, 'invoice_id': invoice.id,
        'business_date': str(business_date), 'session_ids': sessions}) + '\n')
    print('S10_CLOSE_RACE_PREPARED', sessions, flush=True)
