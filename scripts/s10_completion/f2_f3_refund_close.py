import json,os
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.exceptions import AccessError,UserError
from odoo.addons.ydental_treatment_test.tests.common import key,bind
run=Path(os.environ['YDENTAL_S10_RUN_DIR'])
assert run.name==env.cr.dbname
with env.registry.cursor() as cr:
 root=api.Environment(cr,1,{})
 f1=json.loads((run/'f1.json').read_text())
 f5=json.loads((run/'f5.json').read_text())
 pay740=root['ydental.settlement.payment'].browse(f1['payment500_id'])
 pay300=root['ydental.settlement.payment'].browse(f5['payment_id'])
 assert pay740.ydental_amount==500 and pay300.ydental_amount==300
 store=pay740.ydental_store_id
 manager=pay740.ydental_cashier_id
 members=root['ydental.access.membership'].search([('ydental_store_id','=',store.id)])
 reviewer=members.ydental_user_id.filtered(lambda user:'frontdesk' in user.name.lower())[:1]
 assert reviewer and reviewer!=manager
 f=SimpleNamespace(root=root,stores=[store])
 ms=bind(f,manager).env['ydental.settlement.service']
 rs=bind(f,reviewer).env['ydental.settlement.service']
 request=ms._operate('refund_request',{'payment_id':pay740.id,'amount':100,'reason':'Synthetic actual return','request_key':key()},key())
 try:
  ms._operate('refund_approve',{'refund_id':request['refund_id'],'reason':'Own approval invalid'},key())
 except AccessError: pass
 else: raise AssertionError('Self approval was accepted')
 approve=rs._operate('refund_approve',{'refund_id':request['refund_id'],'reason':'Second reviewer accepted'},key())
 assert approve['actually_refunded']==0
 done=ms._operate('refund_execute',{'refund_id':request['refund_id'],'actual_utc':datetime.now(timezone.utc).isoformat(),'proof':'Synthetic actual offline return 100'},key())
 assert done['actually_refunded']==100
 payment2=root['ydental.settlement.payment'].browse(f1['payment240_id'])
 req2=ms._operate('refund_request',{'payment_id':payment2.id,'amount':50,'reason':'Synthetic rejected request','request_key':key()},key())
 rejected=rs._operate('refund_reject',{'refund_id':req2['refund_id'],'reason':'No physical return evidence'},key())
 assert rejected['actually_refunded']==0
 req3=ms._operate('refund_request',{'payment_id':payment2.id,'amount':80,'reason':'Synthetic uncertain transfer','request_key':key()},key())
 rs._operate('refund_approve',{'refund_id':req3['refund_id'],'reason':'Reviewed transfer request'},key())
 uncertain=ms._operate('refund_uncertain',{'refund_id':req3['refund_id'],'outcome':'unknown','reason':'External status unknown'},key())
 assert uncertain['actually_refunded']==0
 before=ms._refund_capacity(payment2)
 cancel=rs._operate('refund_cancel',{'refund_id':req3['refund_id'],'verified_not_paid':True,'evidence':'Synthetic bank/cash review found no transfer','reason':'Verified no actual refund'},key())
 assert before==160 and cancel['available']==240 and cancel['released']==80
 pdfs={}
 for kind,id in [('bill',f1['invoice_id']),('receipt',pay740.id),('refund',request['refund_id'])]:
  raw,digest=ms._pdf(kind,id)
  target=run/(kind+'-f2.pdf')
  if target.exists():
   target=run/(kind+'-f2-retry.pdf')
  with target.open('xb') as output:output.write(raw)
  pdfs[kind]={'sha256':digest,'bytes':len(raw)}
 print('S10_F2_REFUND',json.dumps({'request':request,'approved':approve,'done':done,'rejected':rejected,'uncertain':uncertain,'cancel':cancel,'pdfs':pdfs},ensure_ascii=False),flush=True)
 store300=pay300.ydental_store_id
 manager300=pay300.ydental_cashier_id
 f2=SimpleNamespace(root=root,stores=[store300])
 ms2=bind(f2,manager300).env['ydental.settlement.service']
 members2=root['ydental.access.membership'].search([('ydental_store_id','=',store300.id)])
 reviewer2=members2.ydental_user_id.filtered(lambda user:'frontdesk' in user.name.lower())[:1]
 rs2=bind(f2,reviewer2).env['ydental.settlement.service']
 close=ms2._operate('close',{'business_date':str(pay300.ydental_business_date),'channel':'cash'},key())
 try:
  ms2._operate('reclassify',{'payment_id':pay300.id,'new_channel':'wechat','reason':'Actual recorded channel correction'},key())
 except UserError: pass
 else: raise AssertionError('Day close failed to lock correction')
 unlocked=rs2._operate('unlock',{'close_id':close['close_id'],'reason':'Reviewed source cash proof'},key())
 correction=ms2._operate('reclassify',{'payment_id':pay300.id,'new_channel':'wechat','reason':'Reviewed actual WeChat proof'},key())
 reclosing=ms2._operate('close',{'business_date':str(pay300.ydental_business_date),'channel':'wechat'},key())
 assert close['gross']==550 and reclosing['gross']==300 and correction['actual_cash_refunded']==0
 print('S10_F3_DAYCLOSE',json.dumps({'close':close,'unlock':unlocked,'correction':correction,'reclose':reclosing},ensure_ascii=False),flush=True)
 cr.commit()
