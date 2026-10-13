import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key, price, bind, handover_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(f)
    f.admin._grant(f.users['manager'].id, f.stores[0].id, {'settlement': 'write'})
    receive(f, quantity=215)
    price(f)
    treatment, clinical, queue, lease, execution, document, args = opened_actual(f)
    old_patient = execution.ydental_patient_id.id
    old_ready = treatment._operate('execute', execute_args(f, args), key())
    old_billed = treatment._operate('execute', execute_args(f, args), key())
    clinical._operate('handover', handover_args(document, lease))
    manager = bind(f, f.users['manager']).env['ydental.settlement.service']
    invoice = manager._operate('bill', {'fee_ids': [old_billed['fee_id']], 'discount': 0, 'reason': ''}, key())
    treatment, clinical, queue, lease, execution, document, args = opened_actual(f)
    for _ in range(205):
        result = treatment._operate('execute', execute_args(f, args), key())
        assert result['state'] == 'confirmed' and result['fee_id'] and len(result['move_ids']) == 1
    board = manager._workbench(old_patient)
    assert old_ready['fee_id'] in (board['today'] | board['history']).ids
    assert invoice['invoice_id'] in board['invoices'].ids
    assert old_billed['fee_id'] not in (board['today'] | board['history']).ids
    all_first = manager._workbench()
    assert all_first['page_counts']['today'] + all_first['page_counts']['history'] >= 206
    all_fifth = manager._workbench(pages={'today': 5, 'history': 5})
    assert old_ready['fee_id'] in (all_fifth['today'] | all_fifth['history']).ids
    assert invoice['invoice_id'] in all_first['invoices'].ids
    assert all_first['today'].ids != all_fifth['today'].ids
    print('S10_HISTORY_205', json.dumps({'old_patient': old_patient, 'old_ready_fee': old_ready['fee_id'],
        'old_invoice': invoice['invoice_id'], 'count': all_first['page_counts'],
        'fifth_page_ids': (all_fifth['today'] | all_fifth['history']).ids}, ensure_ascii=False), flush=True)
    cr.commit()
