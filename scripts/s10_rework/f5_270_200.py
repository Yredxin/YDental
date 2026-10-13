import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from odoo import api, Command
from odoo.addons.ydental_treatment_test.tests.common import key, price, bind, queue_bind, lease_args, handover_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args, prescription, pharmacy_start, publish_medicine_link
run=Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name==env.cr.dbname
with env.registry.cursor() as cr:
 f=SimpleNamespace(env=api.Environment(cr,1,{}))
 setup(f)
 company=f.stores[0].company_id
 f.admin._grant(f.users['manager'].id,f.stores[0].id,{'settlement':'write','finance_approval':'write','export':'write','exam':'write'})
 f.admin._grant(f.users['frontdesk'].id,f.stores[0].id,{'settlement':'write','finance_approval':'write','export':'write'})
 root=f.root['base'].with_company(company).env
 income=root['account.account'].search([('account_type','=','income'),('company_ids','in',company.id)],limit=1)
 sales=root['account.journal'].search([('type','=','sale'),('company_id','=',company.id)],limit=1)
 misc=root['account.journal'].search([('type','=','general'),('company_id','=',company.id)],limit=1)
 assert income and sales and misc
 vals={'ydental_store_id':f.stores[0].id,'company_id':company.id,'ydental_policy':'demo_confirmation','ydental_sales_journal_id':sales.id,'ydental_income_account_id':income.id,'ydental_adjustment_journal_id':misc.id}
 for index,channel in enumerate(('cash','wechat','alipay','card'),1):
  account=root['account.account'].create({'name':'Synthetic 740 offline '+channel+' outstanding','code':'F'+str(f.stores[0].id).zfill(3)+str(index),'account_type':'asset_current','company_ids':[Command.link(company.id)]})
  journal=root['account.journal'].create({'name':'Synthetic 740 offline '+channel,'code':'F'+str(index)+str(f.stores[0].id),'type':'bank','company_id':company.id})
  for line in journal.inbound_payment_method_line_ids|journal.outbound_payment_method_line_ids:
   if line.payment_method_id.code=='manual':line.write({'payment_account_id':account.id})
  vals['ydental_'+channel+'_journal_id']=journal.id
 root['ydental.settlement.config']._new(vals)
 receive(f)
 receive(f,kind='medicine')
 price(f,200)
 price(f,27,catalog=f.drug_catalog)
 treatment,clinical,queue,lease,medical,document,args=opened_actual(f)
 actual=treatment._operate('execute',execute_args(f,args),key())
 assert actual['amount']==200
 line={'mapping_id':f.drug_mapping.id,'quantity':10,'uom_id':f.uom.id,'product_id':f.products['medicine'],'specification':'Synthetic specification','usage':'Synthetic usage','frequency':'Synthetic frequency','course':'Synthetic course'}
 draft=treatment._operate('order',args|{'kind':'prescription','purpose':'Synthetic old account medicine','lines':[line]},key())
 issued=treatment._operate('issue',args|{'order_id':draft['order_id'],'version':draft['version']},key())
 clinical._operate('handover',handover_args(document,lease))
 ps,pa=pharmacy_start(f,issued)
 drug=ps._operate('dispense',pa|{'line_id':issued['line_ids'][0],'lot_id':f.lots['medicine'],'quantity':10,'source':key(),'reason':'Actual synthetic 10 unit dispense','policy':'demo_confirmation'},key())
 assert drug['amount']==270
 service=bind(f,f.users['manager']).env['ydental.settlement.service']
 old=service._operate('bill',{'fee_ids':[drug['fee_id']],'discount':0,'reason':''},key())
 new=service._operate('bill',{'fee_ids':[actual['fee_id']],'discount':0,'reason':''},key())
 assert old['amount']==270 and new['amount']==200
 payment=service._operate('pay',{'invoice_ids':[old['invoice_id'],new['invoice_id']],'amount':300,'channel':'cash','actual_utc':datetime.now(timezone.utc).isoformat(),'proof':'Synthetic actual offline 300'},key())
 old_invoice=root['account.move'].browse(old['invoice_id'])
 new_invoice=root['account.move'].browse(new['invoice_id'])
 assert old_invoice.amount_residual==0 and new_invoice.amount_residual==170
 assert [x['amount'] for x in payment['allocations']]==[270,30]
 (run/'f5.json').write_text(json.dumps({'store_id':f.stores[0].id,'manager_id':f.users['manager'].id,'frontdesk_id':f.users['frontdesk'].id,'old_invoice_id':old_invoice.id,'new_invoice_id':new_invoice.id,'payment_id':payment['payment_id'],'old_fee_id':drug['fee_id'],'new_fee_id':actual['fee_id']},ensure_ascii=False,indent=2)+'\n')
 print('S10_F5_270_200',json.dumps({'old':old,'new':new,'payment':payment,'old_residual':old_invoice.amount_residual,'new_residual':new_invoice.amount_residual},ensure_ascii=False),flush=True)
 cr.commit()
