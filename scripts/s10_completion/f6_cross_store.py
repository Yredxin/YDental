import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.exceptions import AccessError
from odoo.addons.ydental_treatment_test.tests.common import key, bind

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'f5.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    source = root['ydental.access.store'].browse(fixture['store_id'])
    target = root['ydental.access.store'].browse(fixture['other_store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    frontdesk = root['res.users'].browse(fixture['frontdesk_id'])
    holder = SimpleNamespace(root=root, stores=[source])
    patient_id = fixture['patient_id']
    bind(holder, frontdesk, target).env['ydental.patient.service']._operate(
        'relation', {'patient_id': patient_id}, key())
    other = bind(holder, manager, target).env['ydental.settlement.service']
    summary = other._other_store_summary(patient_id)
    assert len(summary) == 1 and summary[0]['store_id'] == source.id
    invoices = root['account.move'].browse(fixture['old_invoice_ids'] + fixture['new_invoice_ids'])
    expected = source.company_id.currency_id.round(sum(invoices.mapped('amount_residual')))
    assert summary[0]['residual'] == expected
    assert set(summary[0]) == {'store', 'store_id', 'company', 'currency', 'residual'}
    before = root['account.payment'].search_count([])
    try:
        other._operate('pay', {'invoice_ids': [fixture['old_invoice_ids'][1]],
            'amount': 10, 'channel': 'cash', 'actual_utc': '2026-10-13T00:00:00+00:00',
            'proof': 'Forbidden cross-store receipt'}, key())
    except AccessError:
        pass
    else:
        raise AssertionError('Cross-store payment accepted')
    assert root['account.payment'].search_count([]) == before
    local = bind(holder, manager, source).env['ydental.settlement.service']
    board = local._workbench(patient_id)
    assert fixture['old_invoice_ids'][1] in board['invoices'].ids
    print('S10_F6_CROSS_STORE', json.dumps({'source_store': source.id,
        'other_store': target.id, 'summary': summary, 'local_invoice_ids': board['invoices'].ids,
        'cross_store_payment_delta': root['account.payment'].search_count([]) - before}), flush=True)
    cr.commit()
