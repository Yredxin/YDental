import json
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from odoo import api, Command, fields
from s10_p0_20_fixture import key, price, bind, queue_bind, lease_args, handover_args
from s10_p0_20_fixture import setup, receive, opened_actual, execute_args, prescription, pharmacy_start, publish_medicine_link
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
 original_price=price(f)
 price(f,80,catalog=f.catalogs[2])
 price(f,10,catalog=f.drug_catalog)
 reviewer=f.group.env['ydental.exam.service']
 for catalog,code,family in ((f.catalogs[2],'panorama-demo-1','panorama'),):
  reviewer._operate('review_capability',{'capability_id':catalog.ydental_capability_id.id,'family':family,'reason':'Synthetic capability review'},key())
  reviewer._operate('bind_template',{'catalog_id':catalog.id,'code':code,'reason':'Synthetic approved template'},key())
 treatment,clinical,queue,lease,medical,document,args=opened_actual(f)
 actual=treatment._operate('execute',execute_args(f,args),key())
 assert actual['amount']==600
 row={'mapping_id':f.mappings[0][2].id,'quantity':1,'uom_id':f.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''}
 draft=treatment._operate('order',args|{'kind':'exam','purpose':'Synthetic full-flow examination','lines':[row]},key())
 exam_order=treatment._operate('issue',args|{'order_id':draft['order_id'],'version':draft['version']},key())
 med_order=prescription(f,treatment,args)
 clinical._operate('handover',handover_args(document,lease))
 task=root['ydental.intake.task'].browse(exam_order['task_ids'][0])
 f.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
 examiner=queue_bind(f,f.second)
 exam_lease=examiner._operate('enter',{'station_id':f.stations[0][2].id})
 called=examiner._operate('call',lease_args(exam_lease))
 started=examiner._operate('start',lease_args(exam_lease)|{'entry_id':called['entry_id']})
 ea={'line_id':exam_order['line_ids'][0],'execution_id':started['execution_id'],'lease_id':exam_lease['lease_id'],'lease_token':exam_lease['token'],'inline':False}
 es=examiner.env['ydental.exam.service']
 exam_draft=es._operate('draft',ea|{'version':0,'findings':'合成检查所见','measurements':{},'conclusion':''},key())
 exam_actual=es._operate('perform',ea|{'reason':'Actual synthetic examination','materials':[]},key())
 assert exam_actual['amount']==80
 es._operate('confirm',{'line_id':ea['line_id'],'version':exam_draft['version'],'reason':'Synthetic result review'},key())
 es._operate('finish',ea|{'reason':'Synthetic exam done'},key())
 ps,pa=pharmacy_start(f,med_order)
 first=ps._operate('dispense',pa|{'line_id':med_order['line_ids'][0],'lot_id':f.lots['medicine'],'quantity':4,'source':key(),'reason':'Actual synthetic four unit dispense','policy':'demo_confirmation'},key())
 assert (first['amount'],first['remaining'])==(40,2)
 first_end=ps._operate('finish',pa|{'reason':'Four units physically dispensed; two await a new arrival'},key())
 assert first_end['next_task_id'] and first_end['next_task_id']!=med_order['task_ids'][0]
 assert not root['ydental.queue.entry'].search_count([('ydental_task_id','=',first_end['next_task_id'])])
 ps,pa=pharmacy_start(f,med_order,first_end['next_task_id'])
 second_drug=ps._operate('dispense',pa|{'line_id':med_order['line_ids'][0],'lot_id':f.lots['medicine'],'quantity':2,'source':key(),'reason':'Actual synthetic remaining two unit dispense','policy':'demo_confirmation'},key())
 assert (second_drug['amount'],second_drug['remaining'])==(20,0)
 second_end=ps._operate('finish',pa|{'reason':'All six units physically dispensed'},key())
 assert not second_end['next_task_id'] and second_end['order_state']=='done'
 fee_ids=[actual['fee_id'],exam_actual['fee_id'],first['fee_id'],second_drug['fee_id']]
 drug_events=root['ydental.treatment.event'].browse([first['event_id'],second_drug['event_id']])
 assert len(set(drug_events.ids))==2 and all(event.state=='confirmed' for event in drug_events)
 moves=root['ydental.inventory.event'].browse(first['inventory_event_ids']+second_drug['inventory_event_ids'])
 assert len(moves)==2 and sum(moves.mapped('ydental_quantity'))==6 and all(row.ydental_move_id.state=='done' for row in moves)
 price(f,620,start=fields.Datetime.now(),replace=root['ydental.intake.price'].browse(original_price['id']))
 service=bind(f,f.users['manager']).env['ydental.settlement.service']
 bill=service._operate('bill',{'fee_ids':fee_ids,'discount':0,'reason':''},key())
 assert bill['amount']==740
 pay=service._operate('pay',{'invoice_ids':[bill['invoice_id']],'amount':350,'channel':'wechat','actual_utc':datetime.now(timezone.utc).isoformat(),'proof':'Synthetic actual offline 350'},key())
 invoice=root['account.move'].browse(bill['invoice_id'])
 assert invoice.amount_residual==390
 second=service._operate('pay',{'invoice_ids':[invoice.id],'amount':390,'channel':'wechat','actual_utc':datetime.now(timezone.utc).isoformat(),'proof':'Synthetic actual offline 390'},key())
 assert invoice.amount_residual==0
 (run/'b-chain.json').write_text(json.dumps({'store_id':f.stores[0].id,'manager_id':f.users['manager'].id,'frontdesk_id':f.users['frontdesk'].id,'none_id':f.users['none'].id,'doctor_id':f.users['doctor'].id,'reader_id':f.users['reader'].id,'price_id':f.users['price'].id,'exam_id':f.second.id,'pharmacist_id':f.pharmacist.id,'invoice_id':invoice.id,'payment_first_id':pay['payment_id'],'payment_second_id':second['payment_id'],'fee_ids':fee_ids,'drug_event_ids':drug_events.ids,'drug_move_ids':moves.mapped('ydental_move_id').ids},ensure_ascii=False,indent=2)+'\n')
 print('S10_F1_740',json.dumps({'fees':fee_ids,'drug_events':drug_events.ids,'native_moves':moves.mapped('ydental_move_id').ids,'bill':bill,'pay350':pay,'pay390':second,'residual':invoice.amount_residual,'partials':root['account.partial.reconcile'].search_count([('debit_move_id.move_id','=',invoice.id)])},ensure_ascii=False),flush=True)
 # Complete and correct this same original medical document after actual chain and payment.
 economic_models=['ydental.treatment.fee','ydental.treatment.event','ydental.inventory.event','stock.move','stock.quant','account.move','account.move.line','account.payment','account.partial.reconcile','ydental.settlement.source','ydental.settlement.payment','ydental.settlement.refund']
 def signature():
  import hashlib
  return {m:hashlib.sha256(json.dumps(root[m].search([]).read(),sort_keys=True,default=str).encode()).hexdigest() for m in economic_models}
 before_text=signature()
 owner=queue_bind(f,f.users['doctor']).env['ydental.clinical.service']
 held=owner._operate('acquire',{'document_id':document['document_id']})
 confirmed=owner._operate('confirm',{'document_id':held['document_id'],'editor_token':held['editor_token'],'expected_version':held['version'],'content':held['content'],'key':key()})
 text=dict(confirmed['content'],chief_complaint='P020 synthetic administrative wording correction only')
 corrected=owner._operate('correct',{'document_id':held['document_id'],'editor_token':held['editor_token'],'expected_version':confirmed['version'],'content':text,'key':key(),'reason':'P020 synthetic text correction; no medical conclusion'})
 owner._operate('release',{'document_id':held['document_id'],'editor_token':held['editor_token']})
 assert signature()==before_text,'TEXT_CHANGED_ECONOMIC_FACTS'
 raw,digest=service._pdf('bill',invoice.id)
 (run/'b-current-internal-bill.pdf').write_bytes(raw)
 assert signature()==before_text,'PDF_CHANGED_ECONOMIC_FACTS'
 print('P020_SAME_SOURCE_TEXT_PRICE_PDF',json.dumps({'patient':execution.ydental_patient_id.id,'document':document['document_id'],'confirmed_version':confirmed['version'],'corrected_version':corrected['version'],'old_price':600,'new_price':620,'invoice_amount':invoice.amount_total,'residual':invoice.amount_residual,'economic_signatures':before_text,'pdf_sha256':digest,'historical_original':False}),flush=True)
 cr.commit()
