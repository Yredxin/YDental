"""Two posted receipts for independent close/refund and close/reclassify races."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from odoo import Command, api
from odoo.addons.ydental_treatment_test.tests.common import bind, key, price
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    setup, receive, opened_actual, execute_args,
)

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname and (run / 'database.json').is_file()
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(f)
    store = f.stores[0]
    company = store.company_id
    f.admin._grant(f.users['manager'].id, store.id, {
        'settlement': 'write', 'finance_approval': 'write'})
    f.admin._grant(f.users['frontdesk'].id, store.id, {
        'settlement': 'write', 'finance_approval': 'write'})
    root = f.root['base'].with_company(company).env
    income = root['account.account'].search([('account_type', '=', 'income'),
        ('company_ids', 'in', company.id)], limit=1)
    sales = root['account.journal'].search([('type', '=', 'sale'),
        ('company_id', '=', company.id)], limit=1)
    general = root['account.journal'].search([('type', '=', 'general'),
        ('company_id', '=', company.id)], limit=1)
    config = {'ydental_store_id': store.id, 'company_id': company.id,
        'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id,
        'ydental_income_account_id': income.id,
        'ydental_adjustment_journal_id': general.id}
    for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
        account = root['account.account'].create({'name': 'Synthetic race ' + channel,
            'code': 'R' + str(store.id).zfill(3) + str(index),
            'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
        journal = root['account.journal'].create({'name': 'Synthetic race ' + channel,
            'code': 'R' + str(index) + str(store.id), 'type': 'bank',
            'company_id': company.id})
        for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
            if line.payment_method_id.code == 'manual':
                line.write({'payment_account_id': account.id})
        config['ydental_' + channel + '_journal_id'] = journal.id
    root['ydental.settlement.config']._new(config)
    receive(f)
    price(f, 100)
    treatment, clinical, queue, lease, execution, document, args = opened_actual(f)
    manager = bind(f, f.users['manager']).env['ydental.settlement.service']
    invoices = []
    for _ in range(2):
        actual = treatment._operate('execute', execute_args(f, args), key())
        invoice = manager._operate('bill', {'fee_ids': [actual['fee_id']],
            'discount': 0, 'reason': ''}, key())
        invoices.append(invoice['invoice_id'])
    receipts = {}
    for channel, invoice_id in zip(('card', 'cash'), invoices):
        receipts[channel] = manager._operate('pay', {'invoice_ids': [invoice_id],
            'amount': 100, 'channel': channel,
            'actual_utc': datetime.now(timezone.utc).isoformat(),
            'proof': 'Actual synthetic ' + channel + ' receipt'}, key())['payment_id']
    request = manager._operate('refund_request', {'payment_id': receipts['card'],
        'amount': 50, 'reason': 'Actual synthetic pending card refund',
        'request_key': key()}, key())
    reviewer = bind(f, f.users['frontdesk']).env['ydental.settlement.service']
    reviewer._operate('refund_approve', {'refund_id': request['refund_id'],
        'reason': 'Independent finance approval'}, key())
    sessions = []
    for _ in range(2):
        access = root['ydental.access.service'].with_user(f.users['manager'])
        session = access._session_for_key(key())
        access._bind(session)._switch(store.id)
        sessions.append(session.id)
    data = {'store_id': store.id, 'manager_id': f.users['manager'].id,
        'session_ids': sessions, 'business_date': str(root['ydental.settlement.payment'].browse(
            receipts['card']).ydental_business_date), 'card_payment_id': receipts['card'],
        'cash_payment_id': receipts['cash'], 'refund_id': request['refund_id'],
        'card_invoice_id': invoices[0], 'cash_invoice_id': invoices[1]}
    cr.commit()
    (run / 'finance-race-fixture.json').write_text(json.dumps(data) + '\n')
    print('S10_FINANCE_RACE_PREPARED', json.dumps(data), flush=True)
