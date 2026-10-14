"""Reconcile contested close against the actual posted native outcome."""
import json
import os
from pathlib import Path

from odoo import api

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
mode = os.environ['YDENTAL_S10_RACE_MODE']
assert mode in ('refund', 'reclassify')
fixture = json.loads((run / 'finance-race-fixture.json').read_text())
actors = [json.loads((run / ('finance-' + mode + '-actor-' + actor + '.json')).read_text())
          for actor in ('a', 'b')]
assert actors[0]['backend_pid'] != actors[1]['backend_pid']
with env.registry.cursor() as cr:
    root = api.Environment(cr, 1, {})
    store = root['ydental.access.store'].browse(fixture['store_id'])
    close = root['ydental.settlement.close'].search([('ydental_store_id', '=', store.id),
        ('ydental_business_date', '=', fixture['business_date']),
        ('ydental_channel', '=', 'card' if mode == 'refund' else 'cash')], limit=1)
    assert bool(close) == (actors[0]['outcome'] == 'accepted')
    if mode == 'refund':
        refund = root['ydental.settlement.refund'].browse(fixture['refund_id'])
        assert (refund.ydental_state == 'done') == (actors[1]['outcome'] == 'accepted')
        if refund.ydental_state == 'done':
            assert refund.ydental_native_payment_id.move_id.state == 'posted'
            assert close.ydental_refunded == 50
        else:
            assert refund.ydental_state == 'approved' and not refund.ydental_native_payment_id
            assert close.ydental_pending == 50 and close.ydental_refunded == 0
    else:
        payment = root['ydental.settlement.payment'].browse(fixture['cash_payment_id'])
        correction = root['ydental.settlement.correction'].search([
            ('ydental_payment_id', '=', payment.id)])
        assert bool(correction) == (actors[1]['outcome'] == 'accepted')
        if correction:
            assert correction.ydental_move_id.state == 'posted'
            assert close.ydental_gross == 0
        else:
            assert close.ydental_gross == 100
    cr.execute('SELECT deadlocks FROM pg_stat_database WHERE datname=%s', (env.cr.dbname,))
    deadlocks = cr.fetchone()[0]
    assert deadlocks == 0
    print('S10_FINANCE_RACE_VERIFIED', json.dumps({'mode': mode,
        'backends': [row['backend_pid'] for row in actors],
        'outcomes': [row['outcome'] for row in actors],
        'close_id': close.id, 'gross': close.ydental_gross,
        'refunded': close.ydental_refunded, 'pending': close.ydental_pending,
        'deadlocks': deadlocks}), flush=True)
