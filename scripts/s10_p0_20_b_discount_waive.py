import json,os
from pathlib import Path
from types import SimpleNamespace
from odoo import api,Command
from odoo.exceptions import UserError,ValidationError
from s10_p0_20_fixture import key, price, bind
from s10_p0_20_fixture import setup, receive, opened_actual, execute_args
run=Path(os.environ['YDENTAL_S10_RUN_DIR']);assert run.name==env.cr.dbname
with env.registry.cursor() as cr:
 f=SimpleNamespace(env=api.Environment(cr,1,{}));setup(f)
 company=f.stores[0].company_id
 f.admin._grant(f.users['manager'].id,f.stores[0].id,{'settlement':'write'})
 root=f.root['base'].with_company(company).env
 income=root['account.account'].search([('account_type','=','income'),('company_ids','in',company.id)],limit=1)
 sales=root['account.journal'].search([('type','=','sale'),('company_id','=',company.id)],limit=1)
 misc=root['account.journal'].search([('type','=','general'),('company_id','=',company.id)],limit=1)
 vals={'ydental_store_id':f.stores[0].id,'company_id':company.id,'ydental_policy':'demo_confirmation','ydental_sales_journal_id':sales.id,'ydental_income_account_id':income.id,'ydental_adjustment_journal_id':misc.id}
 for i,ch in enumerate(('cash','wechat','alipay','card'),1):
  acc=root['account.account'].create({'name':'Synthetic discount '+ch,'code':'W'+str(f.stores[0].id).zfill(3)+str(i),'account_type':'asset_current','company_ids':[Command.link(company.id)]})
  journal=root['account.journal'].create({'name':'Synthetic discount '+ch,'code':'W'+str(i)+str(f.stores[0].id),'type':'bank','company_id':company.id})
  for line in journal.inbound_payment_method_line_ids|journal.outbound_payment_method_line_ids:
   if line.payment_method_id.code=='manual':line.write({'payment_account_id':acc.id})
  vals['ydental_'+ch+'_journal_id']=journal.id
 root['ydental.settlement.config']._new(vals)
 receive(f);price(f,100)
 service,clinical,queue,lease,execution,doc,args=opened_actual(f)
 actual=service._operate('execute',execute_args(f,args),key())
 billing=bind(f,f.users['manager']).env['ydental.settlement.service']
 for bad in (-1,101):
  try:billing._operate('bill',{'fee_ids':[actual['fee_id']],'discount':bad,'reason':'Synthetic invalid'},key())
  except (UserError,ValidationError):pass
  else:raise AssertionError('Invalid discount accepted')
 bill=billing._operate('bill',{'fee_ids':[actual['fee_id']],'discount':20,'reason':'Synthetic explicit discount'},key())
 assert bill['amount']==80
 waiver=billing._operate('waive',{'invoice_id':bill['invoice_id'],'amount':80,'reason':'Synthetic documented unpaid waiver'},key())
 invoice=root['account.move'].browse(bill['invoice_id'])
 assert invoice.amount_residual==0 and waiver['actually_refunded']==0
 zero_source=service._operate('execute',execute_args(f,args),key())
 assert zero_source['amount']==100
 zero_bill=billing._operate('bill',{'fee_ids':[zero_source['fee_id']],
  'discount':100,'reason':'Synthetic documented full fee discount'},key())
 zero_invoice=root['account.move'].browse(zero_bill['invoice_id'])
 assert zero_invoice.state=='posted' and zero_invoice.amount_total==0
 assert zero_invoice.amount_residual==0 and zero_bill['amount']==0
 assert root['ydental.settlement.source'].search_count([
  ('ydental_fee_id','=',zero_source['fee_id']),('ydental_invoice_id','=',zero_invoice.id)])==1
 assert not root['account.payment'].search([('partner_id','=',invoice.partner_id.id)])
 print('S10_T03_T06',json.dumps({'fee':actual['fee_id'],'bill':bill,'waive':waiver,
  'native_invoice':invoice.id,'zero_fee':zero_source['fee_id'],
  'zero_native_invoice':zero_invoice.id,'zero_amount':zero_invoice.amount_total,
  'native_payments_for_patient':0}),flush=True)
 cr.commit()
