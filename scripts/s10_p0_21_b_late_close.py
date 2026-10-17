from s10_p0_21_runtime import observed
from s10_p0_21_runtime import pending, checkpoint, step
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.exceptions import UserError
from s10_p0_21_fixture import key, bind
run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'b-multi.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    reviewer = root['res.users'].browse(fixture['frontdesk_id'])
    holder = SimpleNamespace(root=root, stores=[store])
    service = bind(holder, manager).env['ydental.settlement.service']
    review = bind(holder, reviewer).env['ydental.settlement.service']
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    invoice_id = fixture['old_invoice_ids'][1]
    residual_before = root['account.move'].browse(invoice_id).amount_residual
    payment = observed(service.env, 's10_p0_21_b_late_close-pay-1', lambda: service._operate('pay', {'invoice_ids': [invoice_id], 'amount': 10, 'channel': 'cash', 'actual_utc': yesterday, 'proof': 'Actual prior-day cash confirmed and entered next day'}, key()))
    source = root['ydental.settlement.payment'].browse(payment['payment_id'])
    assert source.ydental_actual_at < source.ydental_entered_at
    assert source.ydental_business_date < source.ydental_entered_at.date()
    close = observed(service.env, 's10_p0_21_b_late_close-close-2', lambda: service._operate('close', {'business_date': str(source.ydental_business_date), 'channel': 'cash'}, key()))
    assert close['gross'] == 10
    with cr.savepoint():
        try:
            observed(service.env, 's10_p0_21_b_late_close-pay-3', lambda: service._operate('pay', {'invoice_ids': [invoice_id], 'amount': 1, 'channel': 'cash', 'actual_utc': yesterday, 'proof': 'Forbidden late posting after close'}, key()))
        except UserError as error:
            assert 'day_closed:' in str(error)
        else:
            raise AssertionError('Late payment bypassed locked close')
    observed(review.env, 's10_p0_21_b_late_close-unlock-4', lambda: review._operate('unlock', {'close_id': close['close_id'], 'reason': 'Independent finance review of prior-day evidence'}, key()))
    supplement = observed(service.env, 's10_p0_21_b_late_close-pay-5', lambda: service._operate('pay', {'invoice_ids': [invoice_id], 'amount': 1, 'channel': 'cash', 'actual_utc': yesterday, 'proof': 'Actual prior-day one unit confirmed after finance unlock'}, key()))
    second = observed(service.env, 's10_p0_21_b_late_close-close-6', lambda: service._operate('close', {'business_date': str(source.ydental_business_date), 'channel': 'cash'}, key()))
    assert second['gross'] == 11
    assert root['account.move'].browse(invoice_id).amount_residual == residual_before - 11
    print('S10_LATE_CLOSE', json.dumps({'first_payment': payment['payment_id'], 'actual_at': str(source.ydental_actual_at), 'entered_at': str(source.ydental_entered_at), 'close': close, 'supplement': supplement, 'reclose': second}), flush=True)
    checkpoint(cr, root, 'scenario-late_close', pending)
