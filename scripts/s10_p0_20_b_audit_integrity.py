import json
import os
from pathlib import Path

from odoo import api
from odoo.exceptions import AccessError

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'b-chain.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    source = root['ydental.settlement.source'].search([('ydental_invoice_id', '=', fixture['invoice_id'])], limit=1)
    payment = root['ydental.settlement.payment'].browse(fixture['payment_first_id'])
    audit = root['ydental.access.audit'].search([('ydental_event', '=', 'settlement.pay')], limit=1)
    assert source and payment and audit
    checked = []
    for record, values in ((source, {'ydental_original_amount': 1}),
                           (payment, {'ydental_amount': 1}),
                           (audit, {'ydental_reason': 'forged'})):
        for action in ('write', 'unlink'):
            with cr.savepoint():
                try:
                    record.write(values) if action == 'write' else record.unlink()
                except AccessError:
                    checked.append(record._name + '.' + action)
                else:
                    raise AssertionError(record._name + '.' + action + ' was accepted')
    assert len(checked) == 6
    assert source.ydental_original_amount == 600 and payment.ydental_amount == 500
    print('S10_AUDIT_INTEGRITY', json.dumps({'refused': checked,
        'source_id': source.id, 'payment_id': payment.id, 'audit_id': audit.id}), flush=True)
    cr.commit()
