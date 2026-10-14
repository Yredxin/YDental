"""Find and act on older refunds/closing cycles after large synthetic history.

Run only after a guarded S10 synthetic database has recorded F1/F5 fixtures.
The counts are intentionally generated through authorized service operations.
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
    f1 = json.loads((run / 'f1.json').read_text())
    f5 = json.loads((run / 'f5.json').read_text())
    s1 = root['ydental.access.store'].browse(f1['store_id'])
    user1 = root['res.users'].browse(f1['manager_id'])
    reviewer1 = root['res.users'].browse(f1['frontdesk_id'])
    context1 = SimpleNamespace(root=root, stores=[s1])
    service1 = bind(context1, user1).env['ydental.settlement.service']
    review1 = bind(context1, reviewer1).env['ydental.settlement.service']
    receipt = root['ydental.settlement.payment'].browse(f1['payment500_id'])
    oldest_request = None
    for index in range(55):
        new = service1._operate('refund_request', {
            'payment_id': receipt.id, 'amount': 1,
            'reason': 'Synthetic historical nonpaid refund request %d' % index,
            'request_key': key(),
        }, key())
        if oldest_request is None:
            oldest_request = new['refund_id']
    listing = service1._workbench(pages={'refunds': 2})
    assert listing['page_counts']['refunds'] >= 55
    assert oldest_request in listing['refunds'].ids
    released = service1._operate('refund_cancel', {
        'refund_id': oldest_request, 'verified_not_paid': True,
        'evidence': 'Synthetic no outbound payment found',
        'reason': 'Old request reached safely through page 2',
    }, key())
    assert released['state'] == 'cancelled' and released['released'] == 1

    now = datetime.now(timezone.utc)
    close_ids = []
    for offset in range(95, 40, -1):
        day = service1._local_date(s1, now - timedelta(days=offset))
        closed = service1._operate('close', {
            'business_date': str(day), 'channel': 'card',
        }, key())
        close_ids.append(closed['close_id'])
    closings = service1._workbench(pages={'closes': 2})
    assert closings['page_counts']['closes'] >= 55
    assert close_ids[0] in closings['closes'].ids
    old = root['ydental.settlement.close'].browse(close_ids[0])
    reopened = review1._operate('unlock', {
        'close_id': old.id, 'reason': 'Authorized older-day close correction',
    }, key())
    assert reopened['state'] == 'unlocked'

    s5 = root['ydental.access.store'].browse(f5['store_id'])
    user5 = root['res.users'].browse(f5['manager_id'])
    ctx5 = SimpleNamespace(root=root, stores=[s5])
    service5 = bind(ctx5, user5).env['ydental.settlement.service']
    invoice = root['account.move'].browse(f5['new_invoice_ids'][-1])
    assert invoice.amount_residual >= 55
    first_payment = None
    for index in range(55):
        received = service5._operate('pay', {
            'invoice_ids': [invoice.id], 'amount': 1, 'channel': 'alipay',
            'actual_utc': datetime.now(timezone.utc).isoformat(),
            'proof': 'Synthetic older payment in navigation %d' % index,
        }, key())
        if first_payment is None:
            first_payment = received['payment_id']
    payments = service5._workbench(pages={'payments': 2})
    assert payments['page_counts']['payments'] >= 55
    assert first_payment in payments['payments'].ids
    assert root['account.payment'].browse(received['native_payment_id']).move_id.state == 'posted'

    result = {
        'refunds_total': listing['page_counts']['refunds'],
        'older_refund_id': oldest_request,
        'closes_total': closings['page_counts']['closes'],
        'older_close_id': close_ids[0],
        'payments_total': payments['page_counts']['payments'],
        'older_payment_id': first_payment,
    }
    print('S10_PAGED_FINANCE_HISTORY', json.dumps(result, ensure_ascii=False), flush=True)
    cr.commit()
