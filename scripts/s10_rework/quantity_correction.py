import json,os
from pathlib import Path
from types import SimpleNamespace
from odoo import api,Command,fields
from odoo.exceptions import UserError,ValidationError
from odoo.addons.ydental_treatment_test.tests.common import key,price,bind
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup,receive,opened_actual,execute_args
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
 receive(f)
 first=price(f,600)
 treatment,clinical,queue,lease,execution,doc,args=opened_actual(f)
 actual=treatment._operate('execute',execute_args(f,args),key())
 assert actual['amount']==600
 original=root['ydental.intake.price'].browse(first['id'])
 price(f,620,start=fields.Datetime.now(),replace=original)
 billing=bind(f,f.users['manager']).env['ydental.settlement.service']
 bill=billing._operate('bill',{'fee_ids':[actual['fee_id']],'discount':0,'reason':''},key())
 assert bill['amount']==600
 corrected=treatment._operate('correct',args|{'event_id':actual['event_id'],'delta':-1,'source':key(),'reason':'Synthetic verified quantity correction','materials':[]},key())
 assert corrected['amount']==-600
 credit=billing._operate('bill',{'fee_ids':[corrected['fee_id']],'discount':0,'reason':''},key())
 invoice=root['account.move'].browse(bill['invoice_id'])
 note=root['account.move'].browse(credit['credit_note_id'])
 assert invoice.amount_residual==0 and note.state=='posted' and credit['unpaid_reduced']==600
 assert not root['account.payment'].search([('partner_id','=',invoice.partner_id.id)])
 print('S10_T08_T15',json.dumps({'original_fee':actual['fee_id'],'frozen_amount':600,'new_price':620,'invoice':invoice.id,'correction_fee':corrected['fee_id'],'credit_note':note.id,'residual':invoice.amount_residual,'actual_refunded':0}),flush=True)
 cr.commit()
