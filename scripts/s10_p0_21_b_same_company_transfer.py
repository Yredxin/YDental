from s10_p0_21_runtime import observed
from s10_p0_21_runtime import pending, checkpoint, step
import json, os
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from s10_p0_21_fixture import key, bind
from s10_p0_21_fixture import setup, receive
run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(f)
    source, target = f.stores
    f.admin._grant(f.users['manager'].id, target.id, {'warehouse': 'write'})
    target_service = bind(f, f.users['manager'], target).env['ydental.inventory.service']
    target_service._operate('setup', {'code': 'T' + str(target.id)}, key())
    receive(f, quantity=20)
    stock = f.stock
    before = stock._quantity(f.root['stock.lot'].browse(f.lots['material']), stock._location(stock._config(source), f.root['product.product'].browse(f.products['material'])))
    transfer = observed(stock.env, 's10_p0_21_b_same_company_transfer-transfer-1', lambda: stock._operate('transfer', {'lot_id': f.lots['material'], 'quantity': 5, 'uom_id': f.uom.id, 'target_store_id': target.id, 'source_key': key(), 'reason': 'Synthetic actual same-company transfer'}, key()))
    event = f.root['ydental.inventory.event'].browse(transfer['id'])
    move = f.root['stock.move'].browse(transfer['move_id'])
    assert before == 20 and move.state == 'done' and (event.state == 'done')
    assert move.location_id.ydental_store_id == source and move.location_dest_id.ydental_store_id == target
    print('S10_T09_SAME_COMPANY', json.dumps({'source_store': source.id, 'target_store': target.id, 'event': event.id, 'native_move': move.id, 'quantity': 5, 'company': source.company_id.id}), flush=True)
    checkpoint(cr, f.root, 'scenario-same_company_transfer', pending)
