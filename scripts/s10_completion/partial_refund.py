import json,os
from datetime import datetime,timezone
from pathlib import Path
from types import SimpleNamespace
from odoo import api
from odoo.addons.ydental_treatment_test.tests.common import key,bind
run=Path(os.environ['YDENTAL_S10_RUN_DIR']);assert run.name==env.cr.dbname
f5=json.loads((run/'f5.json').read_text())
with env.registry.cursor() as cr:
 root=api.Environment(cr,1,{})
 payment=root['ydental.settlement.payment'].browse(f5['payment_id'])
 store=payment.ydental_store_id
 manager=root['res.users'].browse(f5['manager_id'])
 reviewer=root['res.users'].browse(f5['frontdesk_id'])
 fixture=SimpleNamespace(root=root,stores=[store])
 service=bind(fixture,manager).env['ydental.settlement.service']
 review=bind(fixture,reviewer).env['ydental.settlement.service']
 close=root['ydental.settlement.close'].search([('ydental_store_id','=',store.id),
     ('ydental_cashier_id','=',manager.id),
     ('ydental_business_date','=',payment.ydental_business_date),
     ('ydental_channel','=',service._effective_channel(payment)),
     ('ydental_state','=','confirmed')],order='id desc',limit=1)
 if close:review._operate('unlock',{'close_id':close.id,'reason':'Reviewed further actual refund evidence'},key())
 invoice=root['account.move'].browse(f5['new_invoice_id'])
 initial=invoice.amount_residual
 req=service._operate('refund_request',{'payment_id':payment.id,'amount':20,'reason':'Synthetic partially paid invoice return','request_key':key()},key())
 review._operate('refund_approve',{'refund_id':req['refund_id'],'reason':'Distinct finance review'},key())
 done=service._operate('refund_execute',{'refund_id':req['refund_id'],'actual_utc':datetime.now(timezone.utc).isoformat(),'proof':'Actual synthetic offline 20 returned'},key())
 assert done['actually_refunded']==20 and invoice.amount_residual==initial
 credit=root['account.move'].browse(done['credit_note_ids'])
 outbound=root['account.payment'].browse(done['native_payment_id'])
 assert credit.state=='posted' and outbound.move_id.state=='posted'
 partials=root['account.partial.reconcile'].search([('debit_move_id.move_id','=',outbound.move_id.id),('credit_move_id.move_id','in',credit.ids)])
 assert sum(partials.mapped('amount'))==20
 print('S10_PARTIAL_REFUND',json.dumps({'invoice_id':invoice.id,'residual_before':initial,'residual_after':invoice.amount_residual,'credit_note_ids':credit.ids,'outbound_payment':outbound.id,'partials':partials.ids}),flush=True)
 cr.commit()
