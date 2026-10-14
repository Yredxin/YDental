"""Render actual Chinese refund PDFs for all material states."""
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
fixture = json.loads((run / 'f1.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    holder = SimpleNamespace(root=root, stores=[store])
    manager = bind(holder, root['res.users'].browse(fixture['manager_id'])).env[
        'ydental.settlement.service'].with_context(lang='zh_CN')
    reviewer = bind(holder, root['res.users'].browse(fixture['frontdesk_id'])).env[
        'ydental.settlement.service']
    payment = root['ydental.settlement.payment'].browse(fixture['payment240_id'])
    approved = manager._operate('refund_request', {'payment_id': payment.id,
        'amount': 5, 'reason': 'Synthetic approved evidence PDF',
        'request_key': key()}, key())
    reviewer._operate('refund_approve', {'refund_id': approved['refund_id'],
        'reason': 'Distinct finance decision'}, key())
    unknown = manager._operate('refund_request', {'payment_id': payment.id,
        'amount': 5, 'reason': 'Synthetic unknown evidence PDF',
        'request_key': key()}, key())
    reviewer._operate('refund_approve', {'refund_id': unknown['refund_id'],
        'reason': 'Distinct finance decision'}, key())
    manager._operate('refund_uncertain', {'refund_id': unknown['refund_id'],
        'outcome': 'unknown', 'reason': 'External result unconfirmed'}, key())
    rejected = manager._operate('refund_request', {'payment_id': payment.id,
        'amount': 5, 'reason': 'Synthetic rejected evidence PDF',
        'request_key': key()}, key())
    reviewer._operate('refund_reject', {'refund_id': rejected['refund_id'],
        'reason': 'No legal return evidence'}, key())
    done = root['ydental.settlement.refund'].search([
        ('ydental_payment_id.ydental_store_id', '=', store.id),
        ('ydental_state', '=', 'done')], limit=1)
    assert done
    rows = {'approved': approved['refund_id'], 'unknown': unknown['refund_id'],
            'rejected': rejected['refund_id'], 'done': done.id}
    result = {}
    for state, refund_id in rows.items():
        refund = root['ydental.settlement.refund'].browse(refund_id)
        assert refund.ydental_state == state
        _, payload = manager._report_payload('refund', refund_id)
        assert payload['state'] == state
        assert payload['pending'] == (refund.ydental_amount if state in ('approved', 'unknown') else 0)
        assert payload['refunded'] == (refund.ydental_amount if state == 'done' else 0)
        raw, digest = manager._pdf('refund', refund_id)
        assert raw.startswith(b'%PDF-') and hashlib.sha256(raw).hexdigest() == digest
        target = run / ('refund-' + state + '.pdf')
        with target.open('xb') as output:
            output.write(raw)
        result[state] = {'refund_id': refund_id, 'amount': refund.ydental_amount,
            'pending': payload['pending'], 'refunded': payload['refunded'],
            'sha256': digest, 'bytes': len(raw)}
    cr.commit()
    print('S10_REFUND_PDF_STATES', json.dumps(result, ensure_ascii=False), flush=True)
