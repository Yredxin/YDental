import json
import os
from pathlib import Path
from types import SimpleNamespace

from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key, bind

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'f1.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    user = root['res.users'].browse(fixture['pharmacist_id'])
    service = bind(SimpleNamespace(root=root, stores=[store]), user).env[
        'ydental.queue.service']._bind_connection(key() + key()).env['ydental.treatment.service']
    event = root['ydental.treatment.event'].browse(fixture['drug_event_ids'][0])
    consumption = root['ydental.treatment.consumption'].search([('ydental_event_id', '=', event.id)])
    assert len(consumption) == 1 and consumption.ydental_inventory_event_id.state == 'done'
    line = event.ydental_order_line_id
    assert service._remaining(line) == 0
    before = (root['ydental.treatment.fee'].search_count([]),
              root['ydental.settlement.refund'].search_count([]))
    returned = service._operate('return_material', {'event_id': event.id,
        'inventory_event_id': consumption.ydental_inventory_event_id.id,
        'quantity': 1, 'uom_id': event.ydental_uom_id.id, 'source': key(),
        'reason': 'Actual medicine returned to controlled quarantine'}, key())
    movement = root['ydental.inventory.event'].browse(returned['id'])
    native = root['stock.move'].browse(returned['move_id'])
    assert movement.ydental_kind == 'return' and movement.ydental_parent_id == consumption.ydental_inventory_event_id
    assert native.state == 'done' and returned['state'] == 'quarantine'
    assert service._remaining(line) == 0
    assert before == (root['ydental.treatment.fee'].search_count([]),
                      root['ydental.settlement.refund'].search_count([]))
    print('S10_DRUG_RETURN', json.dumps({'original_event': event.id,
        'original_stock_event': consumption.ydental_inventory_event_id.id,
        'return_event': movement.id, 'native_move': native.id,
        'remaining_prescription': service._remaining(line), 'fee_refund_delta': [0, 0]}), flush=True)
    cr.commit()
