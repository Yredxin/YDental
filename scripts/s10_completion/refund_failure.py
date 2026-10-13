import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from odoo import api
from odoo.exceptions import UserError
from odoo.addons.ydental_treatment_test.tests.common import key, bind

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'f1.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    reviewer = root['res.users'].browse(fixture['frontdesk_id'])
    holder = SimpleNamespace(root=root, stores=[store])
    service = bind(holder, manager).env['ydental.settlement.service']
    review = bind(holder, reviewer).env['ydental.settlement.service']
    payment = root['ydental.settlement.payment'].browse(fixture['payment240_id'])
    requested = service._operate('refund_request', {'payment_id': payment.id, 'amount': 60,
        'reason': 'Actual offline refund subject to a native posting failure',
        'request_key': key()}, key())
    review._operate('refund_approve', {'refund_id': requested['refund_id'],
        'reason': 'Independent synthetic approval'}, key())
    before = root['account.payment'].search_count([])
    with patch.object(type(root['account.payment']), 'action_post', side_effect=UserError('synthetic_native_post_failure')):
        try:
            service._operate('refund_execute', {'refund_id': requested['refund_id'],
                'actual_utc': datetime.now(timezone.utc).isoformat(),
                'proof': 'No actual transfer: native post failed'}, key())
        except UserError as error:
            assert 'synthetic_native_post_failure' in str(error)
        else:
            raise AssertionError('Injected native posting failure was ignored')
    root.invalidate_all()
    refund = root['ydental.settlement.refund'].browse(requested['refund_id'])
    assert refund.ydental_state == 'approved' and not refund.ydental_native_payment_id
    assert root['account.payment'].search_count([]) == before
    failed = service._operate('refund_uncertain', {'refund_id': refund.id,
        'outcome': 'failed', 'reason': 'Actual native posting failed with no transfer'}, key())
    assert failed['actually_refunded'] == 0 and service._refund_capacity(payment) == 180
    recovered = review._operate('refund_recover', {'refund_id': refund.id,
        'verified_not_paid': True, 'reason': 'Verified no actual transfer and no native payment'}, key())
    assert recovered['state'] == 'approved'
    done = service._operate('refund_execute', {'refund_id': refund.id,
        'actual_utc': datetime.now(timezone.utc).isoformat(),
        'proof': 'Actual synthetic offline 60 returned after recovery'}, key())
    assert done['actually_refunded'] == 60 and root['account.payment'].search_count([]) == before + 1
    assert refund.ydental_state == 'done' and refund.ydental_native_payment_id.move_id.state == 'posted'
    print('S10_REFUND_FAILURE', json.dumps({'refund_id': refund.id, 'failed': failed,
        'recovered': recovered, 'executed': done, 'native_payment_delta': 1}), flush=True)
    cr.commit()
