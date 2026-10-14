"""Cross-company duplicate, authorization, stock and native rollback checks."""
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from odoo import api
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_treatment_test.tests.common import bind, key

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
fixture = json.loads((run / 'trade.json').read_text())
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    source = root['ydental.access.store'].browse(fixture['source_store_id'])
    manager = root['res.users'].browse(fixture['manager_id'])
    frontdesk = root['res.users'].browse(fixture['frontdesk_id'])
    holder = SimpleNamespace(root=root, stores=[source])
    service = bind(holder, manager).env['ydental.settlement.service']
    unprivileged = bind(holder, frontdesk).env['ydental.settlement.service']
    payload = {'target_store_id': fixture['target_store_id'],
        'source_lot_id': fixture['source_lot_id'], 'target_lot_id': fixture['target_lot_id'],
        'quantity': 1, 'uom_id': fixture['uom_id'], 'unit_price': 80,
        'source_key': fixture['source_key'], 'reason': 'Synthetic intercompany actual movement'}
    models = ('sale.order', 'purchase.order', 'stock.move', 'account.move', 'ydental.settlement.trade')
    def counts():
        return {model: root[model].search_count([]) for model in models}
    before = counts()
    replay = service._operate('trade', payload, key())
    assert replay['trade_id'] == fixture['trade_id'] and counts() == before
    cases = [
        (service, payload | {'unit_price': 90}, UserError, 'changed_source'),
        (service, payload | {'source_key': key(), 'quantity': 1000000}, UserError, 'no_stock'),
        (service, payload | {'source_key': key(), 'target_lot_id': fixture['source_lot_id']},
            (AccessError, UserError), 'wrong_company_lot'),
        (unprivileged, payload | {'source_key': key()}, AccessError, 'no_target_approval'),
    ]
    denied = []
    for actor, values, error_type, label in cases:
        with cr.savepoint():
            try:
                actor._operate('trade', values, key())
            except error_type:
                denied.append(label)
            else:
                raise AssertionError(f'{label} unexpectedly accepted')
        assert counts() == before, label
    with patch.object(type(service), '_trade_finish_move',
                      side_effect=UserError('Synthetic native stock failure after both orders')):
        with cr.savepoint():
            try:
                service._operate('trade', payload | {'source_key': key()}, key())
            except UserError as error:
                assert 'Synthetic native stock failure' in str(error)
                denied.append('native_stock_failure_rollback')
            else:
                raise AssertionError('Injected native stock failure unexpectedly accepted')
    assert counts() == before
    print('S10_T09_NEGATIVE', json.dumps({'replayed_trade': replay['trade_id'],
        'denied': denied, 'native_counts_unchanged': before}), flush=True)
