import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from odoo import api, Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_treatment_test.tests.common import (
    key, price, bind, handover_args, qualify, arrive_report, serving, save_args, make_slot,
)
from odoo.addons.ydental_treatment_test.tests.treatment_common import (
    setup, receive, opened_actual, execute_args, pharmacy_start,
)

run = Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname
with env.registry.cursor() as cr:
    f = SimpleNamespace(env=api.Environment(cr, 1, {}))
    old_clock = fields.Datetime.now() - timedelta(days=1)
    with patch.object(fields.Datetime, 'now', return_value=old_clock):
        setup(f)
        company = f.stores[0].company_id
        f.admin._grant(f.users['manager'].id, f.stores[0].id, {
            'settlement': 'write', 'finance_approval': 'write', 'export': 'write'})
        f.admin._grant(f.users['frontdesk'].id, f.stores[0].id, {
            'settlement': 'write', 'finance_approval': 'write', 'export': 'write'})
        f.admin._grant(f.users['manager'].id, f.stores[1].id, {'settlement': 'write'})
        root = f.root['base'].with_company(company).env
        income = root['account.account'].search([('account_type', '=', 'income'),
            ('company_ids', 'in', company.id)], limit=1)
        sales = root['account.journal'].search([('type', '=', 'sale'), ('company_id', '=', company.id)], limit=1)
        misc = root['account.journal'].search([('type', '=', 'general'), ('company_id', '=', company.id)], limit=1)
        assert income and sales and misc
        vals = {'ydental_store_id': f.stores[0].id, 'company_id': company.id,
            'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': sales.id,
            'ydental_income_account_id': income.id, 'ydental_adjustment_journal_id': misc.id}
        for index, channel in enumerate(('cash', 'wechat', 'alipay', 'card'), 1):
            account = root['account.account'].create({'name': 'Synthetic dated offline ' + channel,
                'code': 'D' + str(f.stores[0].id).zfill(3) + str(index),
                'account_type': 'asset_current', 'company_ids': [Command.link(company.id)]})
            journal = root['account.journal'].create({'name': 'Synthetic dated offline ' + channel,
                'code': 'D' + str(index) + str(f.stores[0].id), 'type': 'bank', 'company_id': company.id})
            for line in journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids:
                if line.payment_method_id.code == 'manual':
                    line.write({'payment_account_id': account.id})
            vals['ydental_' + channel + '_journal_id'] = journal.id
        root['ydental.settlement.config']._new(vals)
        receive(f, 8)
        receive(f, 25, 'medicine')
        price(f, 200)
        price(f, 27, catalog=f.drug_catalog)
        treatment, clinical, queue, lease, execution, document, args = opened_actual(f)
        patient_id = execution.ydental_patient_id.id
        line = {'mapping_id': f.drug_mapping.id, 'quantity': 20, 'uom_id': f.uom.id,
            'product_id': f.products['medicine'], 'specification': 'Synthetic dated issue',
            'usage': 'Synthetic', 'frequency': 'Synthetic', 'course': 'Synthetic'}
        draft = treatment._operate('order', args | {'kind': 'prescription',
            'purpose': 'Two old receivables', 'lines': [line]}, key())
        issued = treatment._operate('issue', args | {
            'order_id': draft['order_id'], 'version': draft['version']}, key())
        clinical._operate('handover', handover_args(document, lease))
        pharmacy, pa = pharmacy_start(f, issued)
        old_a = pharmacy._operate('dispense', pa | {'line_id': issued['line_ids'][0],
            'lot_id': f.lots['medicine'], 'quantity': 10, 'source': key(),
            'reason': 'Actual prior-day ten units A', 'policy': 'demo_confirmation'}, key())
        next_task = pharmacy._operate('finish', pa | {'reason': 'Old ten units A complete'}, key())['next_task_id']
        pharmacy, pa = pharmacy_start(f, issued, next_task)
        old_b = pharmacy._operate('dispense', pa | {'line_id': issued['line_ids'][0],
            'lot_id': f.lots['medicine'], 'quantity': 10, 'source': key(),
            'reason': 'Actual prior-day ten units B', 'policy': 'demo_confirmation'}, key())
        pharmacy._operate('finish', pa | {'reason': 'Old twenty units complete'}, key())
        assert old_a['amount'] == old_b['amount'] == 270
        manager = bind(f, f.users['manager']).env['ydental.settlement.service']
        prior_a = manager._operate('bill', {'fee_ids': [old_a['fee_id']], 'discount': 0, 'reason': ''}, key())
        prior_b = manager._operate('bill', {'fee_ids': [old_b['fee_id']], 'discount': 0, 'reason': ''}, key())

    f.group = bind(f, f.users['manager'])
    f.front = bind(f, f.users['frontdesk'])
    manager = bind(f, f.users['manager']).env['ydental.settlement.service']
    f.start = fields.Datetime.now().replace(microsecond=0) + timedelta(minutes=5)
    f.end = f.start + timedelta(minutes=5)
    f.group.env['ydental.supply.service']._operate('business', {
        'area_id': f.areas[0][0].id, 'state': 'open', 'reason': 'Current business date'}, key())
    make_slot(f, f.group, f.stations[0][0], f.start, f.end)
    qualification = qualify(f, patient_id=patient_id, start=f.start, end=f.end)
    arrive_report(f, qualification)
    task = root['ydental.intake.task'].browse(qualification['task_id'])
    queue, lease, execution = serving(f, task=task)
    clinical = queue.env['ydental.clinical.service']
    document = clinical._operate('open', {'execution_id': execution.id,
        'lease_id': lease['lease_id'], 'lease_token': lease['token']})
    document.update(clinical._operate('save', save_args(document)))
    args = {'execution_id': execution.id, 'lease_id': lease['lease_id'],
        'lease_token': lease['token'], 'document_id': document['document_id'],
        'document_version': document['version']}
    treatment = queue.env['ydental.treatment.service']
    new_fees = []
    for _ in range(4):
        result = treatment._operate('execute', execute_args(f, args), key())
        assert result['amount'] == 200
        new_fees.append(result['fee_id'])
    new_bills = [manager._operate('bill', {'fee_ids': [fee_id],
        'discount': 0, 'reason': ''}, key()) for fee_id in new_fees]
    old_date = root['account.move'].browse(prior_a['invoice_id']).invoice_date
    new_dates = [root['account.move'].browse(row['invoice_id']).invoice_date for row in new_bills]
    assert all(old_date < date for date in new_dates)
    assert len(set(new_dates)) == 1 and len({row['invoice_id'] for row in new_bills}) == 4
    now = datetime.now(timezone.utc).isoformat()
    only_new = manager._operate('pay', {'invoice_ids': [new_bills[1]['invoice_id']],
        'amount': 200, 'channel': 'cash', 'actual_utc': now,
        'proof': 'Actual offline new-only payment'}, key())
    assert root['account.move'].browse(prior_b['invoice_id']).amount_residual == 270
    assert root['account.move'].browse(new_bills[1]['invoice_id']).amount_residual == 0
    selected = manager._operate('pay', {'invoice_ids': [new_bills[0]['invoice_id'], prior_a['invoice_id']],
        'amount': 300, 'channel': 'cash', 'actual_utc': now,
        'proof': 'Actual offline old-and-new 300'}, key())
    assert [(row['invoice_id'], row['amount']) for row in selected['allocations']] == [
        (prior_a['invoice_id'], 270), (new_bills[0]['invoice_id'], 30)]
    assert root['account.move'].browse(prior_a['invoice_id']).amount_residual == 0
    assert root['account.move'].browse(new_bills[0]['invoice_id']).amount_residual == 170
    same_day = manager._operate('pay', {'invoice_ids': [new_bills[3]['invoice_id'], new_bills[2]['invoice_id']],
        'amount': 50, 'channel': 'cash', 'actual_utc': now,
        'proof': 'Actual offline same-day ID order'}, key())
    assert [(row['invoice_id'], row['amount']) for row in same_day['allocations']] == [
        (new_bills[2]['invoice_id'], 50)]
    assert root['account.move'].browse(new_bills[3]['invoice_id']).amount_residual == 200
    with cr.savepoint():
        try:
            manager._operate('pay', {'invoice_ids': [new_bills[1]['invoice_id']],
                'amount': 1, 'channel': 'cash', 'actual_utc': now,
                'proof': 'Invalid overpayment'}, key())
        except UserError:
            pass
        else:
            raise AssertionError('Overpayment accepted')
    (run / 'f5.json').write_text(json.dumps({'patient_id': patient_id,
        'store_id': f.stores[0].id, 'other_store_id': f.stores[1].id,
        'manager_id': f.users['manager'].id,
        'frontdesk_id': f.users['frontdesk'].id,
        'old_invoice_id': prior_a['invoice_id'], 'new_invoice_id': new_bills[0]['invoice_id'],
        'payment_id': selected['payment_id'],
        'old_invoice_ids': [prior_a['invoice_id'], prior_b['invoice_id']],
        'new_invoice_ids': [row['invoice_id'] for row in new_bills],
        'only_new_payment_id': only_new['payment_id'], 'selected_payment_id': selected['payment_id'],
        'same_day_payment_id': same_day['payment_id'], 'old_date': str(old_date),
        'new_date': str(new_dates[0])}, indent=2) + '\n')
    print('S10_F5_DATED', json.dumps({'only_new': only_new, 'selected': selected,
        'same_day': same_day, 'old_date': str(old_date), 'new_date': str(new_dates[0])}), flush=True)
    cr.commit()
