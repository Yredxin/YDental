import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import UserError
from s10_p0_20_fixture import key, bind

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
f1 = json.loads((run / 'b-chain.json').read_text())
f5 = json.loads((run / 'b-multi.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(f1['store_id'])
    manager = root['res.users'].browse(f1['manager_id'])
    service = bind(SimpleNamespace(root=root, stores=[store]), manager).env['ydental.settlement.service']
    source_count = root['ydental.settlement.source'].search_count([('ydental_fee_id', 'in', f1['fee_ids'])])
    replay_bill = service._operate('bill', {'fee_ids': f1['fee_ids'],
        'discount': 0, 'reason': ''}, key())
    assert replay_bill['invoice_id'] == f1['invoice_id'] and source_count == 4
    assert root['ydental.settlement.source'].search_count([('ydental_fee_id', 'in', f1['fee_ids'])]) == 4
    other_store = root['ydental.access.store'].browse(f5['store_id'])
    other_manager = root['res.users'].browse(f5['manager_id'])
    other = bind(SimpleNamespace(root=root, stores=[other_store]), other_manager).env['ydental.settlement.service']
    invoice_id = f5['new_invoice_ids'][0]
    payment_count = root['account.payment'].search_count([])
    request_key = key()
    payload = {'invoice_ids': [invoice_id], 'amount': 5, 'channel': 'card',
        'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'Actual offline idempotent five'}
    first = other._operate('pay', payload, request_key)
    again = other._operate('pay', payload, request_key)
    assert first['payment_id'] == again['payment_id'] and again['result'] == 'already_accepted'
    assert root['account.payment'].search_count([]) == payment_count + 1
    with cr.savepoint():
        try:
            other._operate('pay', payload | {'amount': 6}, request_key)
        except UserError as error:
            assert 'version_conflict:' in str(error)
        else:
            raise AssertionError('Changed payload reused a payment key')
    print('S10_IDEMPOTENCY', json.dumps({'bill_replay': replay_bill,
        'payment_first': first, 'payment_replay': again,
        'source_count': source_count, 'native_payment_delta': 1}), flush=True)
    cr.commit()
