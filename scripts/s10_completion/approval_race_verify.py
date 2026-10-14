"""Verify one approval, then actual payout and lost-response replay."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_treatment_test.tests.common import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
fixture = json.loads((run / 'approval-race-fixture.json').read_text())
actors = [json.loads((run / ('approval-actor-' + actor + '.json')).read_text())
          for actor in ('a', 'b')]
assert sorted(row['outcome'] for row in actors) == ['accepted', 'rejected']
assert actors[0]['backend_pid'] != actors[1]['backend_pid']
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    service = bind(SimpleNamespace(root=root, stores=[store]), manager).env[
        'ydental.settlement.service']
    refund = root['ydental.settlement.refund'].browse(fixture['refund_id'])
    assert refund.ydental_state == 'approved'
    assert refund.ydental_approver_id.id in fixture['approver_ids']
    assert not refund.ydental_native_payment_id and not refund.ydental_credit_note_ids
    before = root['account.payment'].search_count([])
    payload = {'refund_id': refund.id, 'actual_utc': datetime.now(timezone.utc).isoformat(),
               'proof': 'Synthetic real offline transfer with lost HTTP response'}
    request_key = key()
    done = service._operate('refund_execute', payload, request_key)
    replay = service._operate('refund_execute', payload, request_key)
    assert done['state'] == 'done' and replay['result'] == 'already_accepted'
    assert done['native_payment_id'] == replay['native_payment_id']
    assert root['account.payment'].search_count([]) == before + 1
    for operation, argument in (
        ('refund_execute', payload),
        ('refund_cancel', {'refund_id': refund.id, 'verified_not_paid': True,
            'evidence': 'Forbidden cancellation after actual transfer',
            'reason': 'Forbidden'}),
        ('refund_uncertain', {'refund_id': refund.id, 'outcome': 'unknown',
            'reason': 'Forbidden state regression'}),
    ):
        with cr.savepoint():
            try:
                service._operate(operation, argument, key())
            except (AccessError, UserError):
                pass
            else:
                raise AssertionError(operation + ' accepted after actual refund')
    assert root['account.payment'].search_count([]) == before + 1
    assert refund.ydental_native_payment_id.move_id.state == 'posted'
    print('S10_APPROVAL_RACE_VERIFIED', json.dumps({'refund_id': refund.id,
        'approver_id': refund.ydental_approver_id.id, 'native_payment_id': done['native_payment_id'],
        'first_backend_ids': [row['backend_pid'] for row in actors],
        'replay': replay['result'], 'native_payment_delta': 1}), flush=True)
    cr.commit()
