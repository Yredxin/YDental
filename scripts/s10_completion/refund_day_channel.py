"""S10 negative-to-positive canary: refund cash flow belongs to its real day.

Run only in a freshly guarded S10 synthetic DB after f5_270_200.py has committed.
This script does not modify the clock, old databases, or the original paid receipt.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    fixture = json.loads((run / 'f5.json').read_text())
    store = root['ydental.access.store'].browse(fixture['store_id'])
    actor = root['res.users'].browse(fixture['manager_id'])
    approver = root['res.users'].browse(fixture['frontdesk_id'])
    ctx = SimpleNamespace(root=root, stores=[store])
    service = bind(ctx, actor).env['ydental.settlement.service']
    reviewer = bind(ctx, approver).env['ydental.settlement.service']
    invoice = root['account.move'].browse(fixture['old_invoice_ids'][1])
    assert invoice.amount_residual >= 100 and invoice.state == 'posted'
    earlier = datetime.now(timezone.utc) - timedelta(days=1)
    earlier_day = service._local_date(store, earlier)
    current_day = service._local_date(store, datetime.now(timezone.utc))
    assert earlier_day < current_day
    payment = service._operate('pay', {
        'invoice_ids': [invoice.id], 'amount': 100, 'channel': 'cash',
        'actual_utc': earlier.isoformat(),
        'proof': 'Synthetic older-day cash label later verified as WeChat',
    }, key())
    receipt = root['ydental.settlement.payment'].browse(payment['payment_id'])
    close1 = service._operate('close', {'business_date': str(earlier_day), 'channel': 'cash'}, key())
    initial = root['ydental.settlement.close'].browse(close1['close_id'])
    assert initial.ydental_gross >= 100 and initial.ydental_refunded == 0
    reviewer._operate('unlock', {'close_id': initial.id, 'reason': 'Correct source proof'}, key())
    correction = service._operate('reclassify', {
        'payment_id': receipt.id, 'new_channel': 'wechat',
        'reason': 'Actual confirmed cash-label error; no reverse payment',
    }, key())
    native_classification = root['account.move'].browse(correction['move_id'])
    assert native_classification.state == 'posted'
    close1_corrected = service._operate('close', {
        'business_date': str(earlier_day), 'channel': 'wechat',
    }, key())
    before = root['ydental.settlement.close'].browse(close1_corrected['close_id'])
    assert before.ydental_gross >= 100 and before.ydental_refunded == 0

    request = service._operate('refund_request', {
        'payment_id': receipt.id, 'amount': 100, 'reason': 'Later real offline refund',
        'request_key': key(),
    }, key())
    approved = reviewer._operate('refund_approve', {
        'refund_id': request['refund_id'], 'reason': 'Other person reviewed evidence',
    }, key())
    assert approved['actually_refunded'] == 0
    pending = service._operate('close', {
        'business_date': str(current_day), 'channel': 'wechat',
    }, key())
    pending_snapshot = root['ydental.settlement.close'].browse(pending['close_id'])
    assert pending_snapshot.ydental_pending >= 100 and pending_snapshot.ydental_refunded == 0
    reviewer._operate('unlock', {
        'close_id': pending_snapshot.id, 'reason': 'Perform documented later-day refund',
    }, key())
    done = service._operate('refund_execute', {
        'refund_id': request['refund_id'],
        'actual_utc': datetime.now(timezone.utc).isoformat(),
        'proof': 'Synthetic verified actual WeChat refund',
    }, key())
    assert done['actually_refunded'] == 100
    refund = root['ydental.settlement.refund'].browse(request['refund_id'])
    assert refund.ydental_refund_business_date == current_day
    assert refund.ydental_refund_channel == 'wechat'
    assert refund.ydental_executor_id == actor
    assert refund.ydental_native_payment_id.journal_id == service._config(store).ydental_wechat_journal_id
    close2 = service._operate('close', {
        'business_date': str(current_day), 'channel': 'wechat',
    }, key())
    today = root['ydental.settlement.close'].browse(close2['close_id'])
    assert today.ydental_refunded >= 100 and today.ydental_pending == 0
    assert before.ydental_refunded == 0 and initial.ydental_refunded == 0
    assert pending_snapshot.ydental_pending >= 100  # immutable prior cycle
    result = {
        'store': store.id, 'source_payment': receipt.id,
        'source_day': str(earlier_day), 'refund_day': str(current_day),
        'prior_close': before.id, 'pending_close': pending_snapshot.id,
        'refund_close': today.id, 'native_refund_payment': refund.ydental_native_payment_id.id,
        'actual_channel': refund.ydental_refund_channel, 'actual_amount': refund.ydental_amount,
        'prior_refunded': before.ydental_refunded, 'today_refunded': today.ydental_refunded,
    }
    print('S10_REFUND_DATE_CHANNEL', json.dumps(result, ensure_ascii=False), flush=True)
    cr.commit()
