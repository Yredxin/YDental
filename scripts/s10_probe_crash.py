import json
import os
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from odoo import api, Command
from odoo.addons.ydental_treatment_test.tests.common import key, price, bind
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, receive, opened_actual, execute_args

run=Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name == env.cr.dbname == 'ydental_s10_test_20261013125916_2b3e556e'
with env.registry.cursor() as cr:
 f=SimpleNamespace(env=api.Environment(cr,1,{}))
 setup(f)
 company=f.stores[0].company_id
 admin=f.admin
 admin._grant(f.users['manager'].id,f.stores[0].id,{'settlement':'write','finance_approval':'write','export':'write'})
 admin._grant(f.users['frontdesk'].id,f.stores[0].id,{'settlement':'write','export':'write'})
 root=f.root['base'].with_company(company).env
 income=root['account.account'].search([('account_type','=','income'),('company_ids','in',company.id)],limit=1)
 sales=root['account.journal'].search([('type','=','sale'),('company_id','=',company.id)],limit=1)
 misc=root['account.journal'].search([('type','=','general'),('company_id','=',company.id)],limit=1)
 assert income and sales and misc
 vals={'ydental_store_id':f.stores[0].id,'company_id':company.id,'ydental_policy':'demo_confirmation','ydental_sales_journal_id':sales.id,'ydental_income_account_id':income.id,'ydental_adjustment_journal_id':misc.id}
 for index,channel in enumerate(('cash','wechat','alipay','card'),1):
  account=root['account.account'].create({'name':'Synthetic offline '+channel+' outstanding','code':'D7'+str(f.stores[0].id).zfill(3)+str(index),'account_type':'asset_current','company_ids':[Command.link(company.id)]})
  journal=root['account.journal'].create({'name':'Synthetic offline '+channel,'code':'S'+str(index)+str(f.stores[0].id),'type':'bank','company_id':company.id})
  for line in journal.inbound_payment_method_line_ids|journal.outbound_payment_method_line_ids:
   if line.payment_method_id.code=='manual':line.write({'payment_account_id':account.id})
  vals['ydental_'+channel+'_journal_id']=journal.id
 config=root['ydental.settlement.config']._new(vals)
 receive(f);price(f)
 with patch.object(type(f.group.env['ydental.supply.service']), '_allow_demo_supply', return_value=True):
  treatment,clinical,queue,lease,execution,doc,args=opened_actual(f)
 actual=treatment._operate('execute',execute_args(f,args),key())
 fee=root['ydental.treatment.fee'].browse(actual['fee_id'])
 assert fee.ydental_amount==600 and fee.ydental_event_id.state=='confirmed'
 service=bind(f,f.users['manager']).env['ydental.settlement.service']
 bill=service._operate('bill',{'fee_ids':[fee.id],'discount':0,'reason':''},key())
 now=datetime.now(timezone.utc).isoformat()
 pay=service._operate('pay',{'invoice_ids':[bill['invoice_id']],'amount':500,'channel':'wechat','actual_utc':now,'proof':'Synthetic offline WeChat confirmation'},key())
 invoice=root['account.move'].browse(bill['invoice_id'])
 native=root['account.payment'].browse(pay['native_payment_id'])
 assert invoice.state=='posted' and invoice.amount_residual==100 and native.move_id.state=='posted'
 assert len(root['account.partial.reconcile'].search([('credit_move_id.move_id','=',native.move_id.id)]))==1
 result={'store_id':f.stores[0].id,'patient_id':execution.ydental_patient_id.id,'fee_id':fee.id,'event_id':actual['event_id'],'stock_move_ids':actual['move_ids'],'config_id':config.id,'invoice':bill,'payment':pay,'invoice_residual':invoice.amount_residual,'native_payment_move_id':native.move_id.id,'manager_id':f.users['manager'].id,'frontdesk_id':f.users['frontdesk'].id}
 cr.commit()
 (run/'probe-600.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('S10_PROBE_600',json.dumps(result,ensure_ascii=False))
