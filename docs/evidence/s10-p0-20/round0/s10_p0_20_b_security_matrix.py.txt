"""Real role and source gates against the committed F1 native documents."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import AccessError
from s10_p0_20_fixture import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'b-chain.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    holder = SimpleNamespace(root=root, stores=[store])
    manager = bind(holder, root['res.users'].browse(fixture['manager_id'])).env['ydental.settlement.service']
    frontdesk = bind(holder, root['res.users'].browse(fixture['frontdesk_id'])).env['ydental.settlement.service']
    assert manager._workbench()['store'].id == store.id
    assert frontdesk._workbench()['store'].id == store.id
    before = root['account.payment'].search_count([])
    denied = {}
    for role in ('none', 'doctor', 'reader', 'price', 'exam', 'pharmacist'):
        user_id = fixture.get(role + '_id')
        if not user_id and role in ('doctor', 'reader', 'price'):
            members = root['ydental.access.membership'].search([
                ('ydental_store_id', '=', store.id),
                ('ydental_user_id.login', '=like', 's06a_' + role + '_%')])
            assert len(members) == 1, (role, members.ids)
            user_id = members.ydental_user_id.id
        if not user_id:
            continue  # Only pre-fixed diagnostic fixtures lack the two later IDs.
        service = bind(holder, root['res.users'].browse(user_id)).env['ydental.settlement.service']
        blocked = []
        for label, call in (
            ('board', lambda: service._workbench()),
            ('bill_pdf', lambda: service._pdf('bill', fixture['invoice_id'])),
            ('pay', lambda: service._operate('pay', {'invoice_ids': [fixture['invoice_id']],
                'amount': 1, 'channel': 'cash', 'actual_utc': datetime.now(timezone.utc).isoformat(),
                'proof': 'Forbidden synthetic role payment'}, key())),
        ):
            with cr.savepoint():
                try:
                    call()
                except AccessError:
                    blocked.append(label)
                else:
                    raise AssertionError(f'{role} unexpectedly accepted {label}')
        assert blocked == ['board', 'bill_pdf', 'pay']
        denied[role] = blocked
    if all(role + '_id' in fixture for role in ('exam', 'pharmacist')):
        assert len(denied) == 6
    assert root['account.payment'].search_count([]) == before
    print('S10_SECURITY_MATRIX', json.dumps({'allowed': ['manager', 'frontdesk'],
        'denied': denied, 'native_payment_delta': 0}), flush=True)
