from s10_p0_21_runtime import observed
from s10_p0_21_runtime import pending, checkpoint, step
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from odoo import api, Command, fields
from datetime import timedelta
from odoo.addons.ydental_inventory.models.ydental_inventory_record import MUTATION
from odoo.addons.ydental_intake.models.ydental_intake_record import MUTATION as INTAKE_MUTATION
from s10_p0_21_fixture import key, price, bind
from s10_p0_21_fixture import setup, receive, opened_actual, execute_args
run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    setup(f)
    company = f.stores[0].company_id
    admin = f.admin
    admin._grant(f.users['manager'].id, f.stores[0].id, {'settlement': 'write', 'finance_approval': 'write', 'export': 'write'})
    admin._grant(f.users['frontdesk'].id, f.stores[0].id, {'settlement': 'write', 'export': 'write'})
    root = f.root['base'].with_company(company).env
    income = root['account.account'].search([('account_type', '=', 'income'), ('company_ids', 'in', company.id)], limit=1)
    sales = root['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    misc = root['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
    assert income and sales and misc
    vals = {'ydental_store_id': f.stores[0].id, 'company_id': company.id, 'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id, 'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': misc.id}
    for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
        account = root['account.account'].create({'name': 'Synthetic offline ' + channel + ' outstanding', 'code': 'D7' + str(f.stores[0].id).zfill(3) + str(index), 'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
        journal = root['account.journal'].create({'name': 'Synthetic offline ' + channel, 'code': 'S' + str(index) + str(f.stores[0].id), 'type': 'bank', 'company_id': company.id})
        for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
            if line.payment_method_id.code == 'manual':
                line.write({'payment_account_id': account.id})
        vals['ydental_' + channel + '_journal_id'] = journal.id
    config = root['ydental.settlement.config']._new(vals)
    receive(f)
    source = f.stores[0]
    source_config = config
    manager_user = f.users['manager']
    company = root['res.company'].create({'name': 'S10 synthetic legal B ' + key(), 'currency_id': source.company_id.currency_id.id})
    print('TRADE_COMPANY', company.id, company.chart_template, flush=True)
    if not company.chart_template:
        root['account.chart.template'].with_context(ydental_inventory_mutation=MUTATION, ydental_intake_mutation=INTAKE_MUTATION).try_loading('generic_coa', company)
    print('TRADE_CHART', company.chart_template, flush=True)
    target = root['ydental.access.store'].create({'name': 'S10 synthetic B store ' + key(), 'company_id': company.id, 'ydental_timezone': source.ydental_timezone})
    manager_user.write({'company_ids': [Command.link(company.id)]})
    f.admin._join(manager_user.id, target.id)
    f.admin._grant(manager_user.id, target.id, {'warehouse': 'write', 'finance_approval': 'write', 'settlement': 'write'})
    f.admin._grant(manager_user.id, source.id, {'warehouse': 'write', 'finance_approval': 'write', 'settlement': 'write'})
    target_stock = bind(f, manager_user, target).env['ydental.inventory.service']
    target_stock._operate('setup', {'code': 'X' + str(target.id)}, key())
    source_lot = root['stock.lot'].browse(f.lots['material'])
    product = root['product.product'].browse(f.products['material'])
    lot = target_stock._operate('lot', {'product_id': product.id, 'name': source_lot.name, 'expiration': fields.Datetime.to_string(fields.Datetime.now() + timedelta(days=45))}, key())
    income = source_config.ydental_income_account_id
    expense = root['account.account'].with_company(company).search([('account_type', 'in', ('expense', 'expense_direct_cost')), ('company_ids', 'in', company.id)], limit=1)
    sales = root['account.journal'].with_company(company).search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
    purchase = root['account.journal'].with_company(company).search([('type', '=', 'purchase'), ('company_id', '=', company.id)], limit=1)
    misc = root['account.journal'].with_company(company).search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
    print('TRADE_ACCOUNTS', expense.id, sales.id, purchase.id, misc.id, flush=True)
    assert expense and sales and purchase and misc
    product.with_company(source.company_id).with_context(ydental_inventory_mutation=MUTATION, ydental_intake_mutation=INTAKE_MUTATION).write({'property_account_income_id': income.id})
    product.with_company(company).with_context(ydental_inventory_mutation=MUTATION, ydental_intake_mutation=INTAKE_MUTATION).write({'property_account_expense_id': expense.id})
    vals = {'ydental_store_id': target.id, 'company_id': company.id, 'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id, 'ydental_purchase_journal_id': purchase.id, 'ydental_expense_account_id': expense.id, 'ydental_income_account_id': root['account.account'].search([('account_type', '=', 'income'), ('company_ids', 'in', company.id)], limit=1).id, 'ydental_adjustment_journal_id': misc.id}
    for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
        account = root['account.account'].with_company(company).create({'name': 'Synthetic B offline ' + channel, 'code': 'B' + str(target.id).zfill(3) + str(index), 'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
        journal = root['account.journal'].with_company(company).create({'name': 'Synthetic B offline ' + channel, 'code': 'B' + str(index) + str(target.id), 'type': 'bank', 'company_id': company.id})
        for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
            if line.payment_method_id.code == 'manual':
                line.write({'payment_account_id': account.id})
        vals['ydental_' + channel + '_journal_id'] = journal.id
    root['ydental.settlement.config']._new(vals)
    service = bind(f, manager_user, source).env['ydental.settlement.service']
    trade_key = key()
    result = observed(service.env, 's10_p0_21_b_t09_trade-trade-1', lambda: service._operate('trade', {'target_store_id': target.id, 'source_lot_id': source_lot.id, 'target_lot_id': lot['id'], 'quantity': 1, 'uom_id': product.uom_id.id, 'unit_price': 80, 'source_key': trade_key, 'reason': 'Synthetic intercompany actual movement'}, key()))
    from odoo.exceptions import AccessError
    try:
        observed(bind(f, f.users['frontdesk'], source).env['ydental.settlement.service'].env, 's10_p0_21_b_t09_trade-trade-2', lambda: bind(f, f.users['frontdesk'], source).env['ydental.settlement.service']._operate('trade', {'target_store_id': target.id, 'source_lot_id': source_lot.id, 'target_lot_id': lot['id'], 'quantity': 1, 'uom_id': product.uom_id.id, 'unit_price': 80, 'source_key': key(), 'reason': 'Unauthorized cross-company attempt'}, key()))
    except AccessError:
        pass
    else:
        raise AssertionError('Unauthorized cross-company trade was accepted')
    pending['trade.json'] = {'source_store_id': source.id, 'target_store_id': target.id, 'manager_id': manager_user.id, 'frontdesk_id': f.users['frontdesk'].id, 'source_lot_id': source_lot.id, 'target_lot_id': lot['id'], 'uom_id': product.uom_id.id, 'source_key': trade_key, 'trade_id': result['trade_id'], 'sale_order_id': result['sale_order_id'], 'purchase_order_id': result['purchase_order_id']}
    print('TRADE_RESULT', result, flush=True)
    checkpoint(cr, root, 'scenario-t09_trade', pending)
