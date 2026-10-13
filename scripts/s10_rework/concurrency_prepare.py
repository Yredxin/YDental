import json,os
from pathlib import Path
from types import SimpleNamespace
from odoo import api,Command
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
 receive(f);price(f,100)
 service,clinical,queue,lease,execution,doc,args=opened_actual(f)
 actual=service._operate('execute',execute_args(f,args),key())
 billing=bind(f,f.users['manager']).env['ydental.settlement.service']
 (run/'concurrency-fixture.json').write_text(json.dumps({'store_id':f.stores[0].id,'manager_id':f.users['manager'].id,'fee_id':actual['fee_id']},indent=2)+'\n')
 print('S10_CONCURRENCY_READY',actual['fee_id'],flush=True)
 cr.commit()
