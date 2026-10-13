from unittest.mock import patch
from datetime import timedelta
from odoo import fields

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from .common import key, price, handover_args, bind
from .treatment_common import setup, receive, opened_actual, execute_args, prescription, pharmacy_start


@tagged('post_install', '-at_install')
class TestActualTreatment(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def test_f1_actual_event_price_native_stock_exactly_once(self):
        receive(self); price(self)
        s,c,q,l,e,d,a = opened_actual(self)
        args = execute_args(self,a); request = key()
        result = s._operate('execute',args,request)
        self.assertEqual(result['state'],'confirmed');self.assertEqual(result['amount'],600)
        self.assertEqual(len(result['move_ids']),1)
        self.assertEqual(s._operate('execute',args,request)['event_id'],result['event_id'])
        self.assertEqual(s._operate('execute',args,key())['event_id'],result['event_id'])
        move=self.root['stock.move'].browse(result['move_ids']);self.assertEqual(move.state,'done');self.assertEqual(move.quantity,1)
        self.assertEqual(s._model('fee').search_count([('ydental_event_id','=',result['event_id'])]),1)

    def test_missing_price_before_execution_rolls_back(self):
        receive(self);s,c,q,l,e,d,a=opened_actual(self)
        with self.assertRaises(UserError):s._operate('execute',execute_args(self,a),key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id','=',e.id)]))

    def test_shortage_before_execution_no_fact_or_fee(self):
        price(self);s,c,q,l,e,d,a=opened_actual(self)
        with self.assertRaises(UserError):s._operate('execute',execute_args(self,a),key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id','=',e.id)]))

    def test_f4_already_performed_shortage_original_pending_recovery(self):
        price(self);s,c,q,l,e,d,a=opened_actual(self)
        result=s._operate('execute',execute_args(self,a,actual=True),key())
        self.assertEqual(result['state'],'pending');self.assertFalse(result['fee_id']);self.assertFalse(result['move_ids'])
        stock_event=self.root['ydental.inventory.event'].browse(result['inventory_event_ids']);self.assertEqual(stock_event.state,'pending')
        original_price=self.root['ydental.intake.price'].search([('ydental_store_id','=',self.stores[0].id),('ydental_catalog_id','=',self.catalogs[0].id),('state','=','published')],limit=1)
        revised_at=fields.Datetime.now()+timedelta(seconds=10)
        price(self,amount=999,start=revised_at,replace=original_price)
        with patch.object(fields.Datetime,'now',return_value=revised_at+timedelta(seconds=1)):
            self.assertEqual(self.group._quote(self.stores[0],self.catalogs[0].id,self.currency.id,1)[1]['ydental_unit_price'],999)
            receive(self)
            self.stock._operate('recover',{'event_id':stock_event.id,'reason':'S08B physical correction verified'},key())
            result=s._operate('reconcile',{'event_id':result['event_id'],'reason':'Original event reconciliation'},key())
        self.assertEqual(result['state'],'confirmed');self.assertEqual(result['amount'],600)
        self.assertEqual(len(result['move_ids']),1)

    def test_unpriced_fact_manual_review_no_later_price_substitution(self):
        receive(self);s,c,q,l,e,d,a=opened_actual(self)
        result=s._operate('execute',execute_args(self,a,actual=True),key());self.assertEqual(result['pending_reason'],'missing_price')
        price(self,amount=999)
        result=s._operate('reconcile',{'event_id':result['event_id'],'reason':'Do not silently reprice'},key());self.assertEqual(result['pending_reason'],'missing_price')
        pricer=bind(self,self.users['price']).env['ydental.queue.service']._bind_connection(key()+key()).env[s._name]
        pricer._operate('review_price',{'event_id':result['event_id'],'unit_price':600,'currency_id':self.currency.id,'evidence':'Verified synthetic original quote'},key())
        result=s._operate('reconcile',{'event_id':result['event_id'],'reason':'Use reviewed original quote'},key());self.assertEqual(result['amount'],600)

    def test_quantity_correction_is_linked_delta_not_overwrite(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        r=s._operate('execute',execute_args(self,a),key())
        correction=s._operate('correct',a|{'event_id':r['event_id'],'delta':-1,'source':key(),'reason':'Verified quantity correction','materials':[]},key())
        self.assertEqual(correction['amount'],-600)
        original=s._model('event').browse(r['event_id']);self.assertEqual(original.ydental_quantity,1)
        self.assertEqual(s._model('event').browse(correction['event_id']).ydental_parent_id,original)
        with self.assertRaises(ValidationError):s._operate('correct',a|{'event_id':r['event_id'],'delta':-1,'source':key(),'reason':'Cannot overreverse','materials':[]},key())

    def test_stock_failure_after_native_move_rolls_back_every_source(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        original=type(self.stock)._move
        def fail(service,event):
            original(service,event)
            raise UserError('Injected after native completed move')
        with patch.object(type(self.stock),'_move',fail):
            with self.assertRaises(UserError):s._operate('execute',execute_args(self,a),key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id','=',e.id)]))
        self.assertFalse(self.root['ydental.inventory.event'].search_count([('ydental_source_namespace','=','s08b-clinical'),('ydental_store_id','=',self.stores[0].id)]))

    def test_rpc_context_cannot_forge_clinical_inventory_or_referral(self):
        with self.assertRaises(AccessError):self.stock._source_action({'actor_id':self.users['doctor'].id})
        with self.assertRaises(AccessError):self.doctor._referral_action('refer_untimed',{},key(),permit={'actor_id':self.users['doctor'].id})
        with self.assertRaises(AccessError):self.doctor.env['ydental.treatment.event'].with_context(ydental_treatment_mutation=True).create({'name':'forged'})

    def test_old_document_version_and_lease_rejected(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        with self.assertRaises(UserError):s._operate('execute',execute_args(self,a|{'document_version':0}),key())
        with self.assertRaises(AccessError):s._operate('execute',execute_args(self,a|{'lease_token':'invalid'}),key())
        self.admin._grant(self.users['doctor'].id,self.stores[0].id,{'medical':'read'})
        with self.assertRaises(AccessError):s._operate('execute',execute_args(self,a),key())

    def test_f3_prescription_six_dispense_four_then_two_real_finish(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self);issued=prescription(self,s,a)
        self.assertFalse(self.root['ydental.queue.entry'].search_count([('ydental_task_id','in',issued['task_ids'])]))
        c._operate('handover',handover_args(d,l))
        p,args=pharmacy_start(self,issued)
        r=p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,'source':key(),'reason':'Synthetic actual four','policy':'demo_confirmation'},key())
        self.assertEqual((r['amount'],r['remaining']),(40,2))
        end=p._operate('finish',args|{'reason':'End actual four-unit dispensing segment'},key())
        self.assertTrue(end['next_task_id']);self.assertNotEqual(end['next_task_id'],issued['task_ids'][0])
        self.assertFalse(self.root['ydental.queue.execution'].search_count([('ydental_patient_id','=',e.ydental_patient_id.id),('state','in',('serving','verify'))]))
        self.assertFalse(self.root['ydental.queue.entry'].search_count([('ydental_task_id','=',end['next_task_id'])]))
        p,args=pharmacy_start(self,issued,end['next_task_id'])
        last=p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':2,'source':key(),'reason':'Synthetic actual two','policy':'demo_confirmation'},key())
        self.assertEqual((last['amount'],last['remaining']),(20,0))
        with self.assertRaises(UserError):p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':1,'source':key(),'reason':'No seventh unit','policy':'demo_confirmation'},key())
        end=p._operate('finish',args|{'reason':'Prescription fully dispensed'},key());self.assertFalse(end['next_task_id']);self.assertEqual(end['order_state'],'done')
        member=self.root['ydental.access.membership'].search([('ydental_user_id','=',self.pharmacist.id),('ydental_store_id','=',self.stores[0].id)])
        levels=self.admin._levels(member);self.assertEqual(levels['pharmacy'],'write')
        for category in ('warehouse','price','settlement'):self.assertEqual(levels[category],'none')

    def test_frozen_exam_cancel_unperformed_and_new_order(self):
        s,c,q,l,e,d,a=opened_actual(self)
        lines=[{'mapping_id':self.mappings[0][i].id,'quantity':1,'uom_id':self.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''} for i in (2,3)]
        draft=s._operate('order',a|{'kind':'exam','purpose':'Synthetic panorama and CBCT','lines':lines},key())
        issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
        cancelled=s._operate('cancel_exam',a|{'line_id':issued['line_ids'][1],'order_version':issued['version'],'reason':'Patient declined unperformed synthetic CBCT'},key())
        self.assertEqual(cancelled['state'],'cancelled')
        with self.assertRaises(UserError):s._operate('edit_order',a|{'order_id':draft['order_id'],'version':cancelled['order_version'],'purpose':'Cannot append','lines':lines},key())
        new=s._operate('order',a|{'kind':'exam','purpose':'Separate additional examination','lines':lines[:1]},key());self.assertNotEqual(new['order_id'],draft['order_id'])

    def test_multi_material_shortage_does_not_post_partial_consumption(self):
        price(self);receive(self,1)
        second=self.stock._operate('lot',{'product_id':self.products['material'],'name':'S08B-empty-'+key(),
            'expiration':fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=10))},key())['id']
        s,c,q,l,e,d,a=opened_actual(self);args=execute_args(self,a,actual=True)
        args['materials'].append({'lot_id':second,'quantity':1,'uom_id':self.uom.id,'kind':'treatment'})
        r=s._operate('execute',args,key());self.assertEqual(r['state'],'pending');self.assertFalse(r['move_ids']);self.assertFalse(r['fee_id'])
        self.assertEqual(len(r['inventory_event_ids']),1)

    def test_d1_handover_d2_real_project_d1_text_no_second_fee(self):
        from .common import arrive_report, serving, save_args
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        first=s._operate('execute',execute_args(self,a),key())
        exam_lines=[{'mapping_id':self.mappings[0][2].id,'quantity':1,'uom_id':self.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''}]
        exam=s._operate('order',a|{'kind':'exam','purpose':'F2 unperformed panorama retained across D1/D2','lines':exam_lines},key())
        exam=s._operate('issue',a|{'order_id':exam['order_id'],'version':exam['version']},key())
        hand=c._operate('handover',handover_args(d,l))
        arrive_report(self,{'task_id':hand['continuation_task_id']})
        task=self.root['ydental.intake.task'].browse(hand['continuation_task_id'])
        q2,l2,e2=serving(self,user=self.second,station=self.other_station,task=task)
        c2=q2.env['ydental.clinical.service'];d2=c2._operate('open',{'execution_id':e2.id,'lease_id':l2['lease_id'],'lease_token':l2['token']})
        d2.update(c2._operate('save',save_args(d2,'Synthetic D2 project document')))
        a2={'execution_id':e2.id,'lease_id':l2['lease_id'],'lease_token':l2['token'],'document_id':d2['document_id'],'document_version':d2['version']}
        second=q2.env[s._name]._operate('execute',execute_args(self,a2),key())
        self.assertNotEqual(first['event_id'],second['event_id']);self.assertEqual(second['amount'],600)
        before=self.root['ydental.treatment.fee'].search_count([])
        pending=c._operate('acquire',{'document_id':d['document_id']})
        c._operate('confirm',save_args(pending,'Synthetic D1 completion without a new project'))
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([]),before)
        self.assertEqual(self.root['ydental.clinical.document'].browse(d['document_id']).ydental_author_id,self.users['doctor'])
        self.assertEqual(s._model('line').browse(exam['line_ids']).state,'issued')
        self.assertEqual(self.root['ydental.intake.task'].browse(exam['task_ids']).state,'pending')
        self.assertFalse(self.root['ydental.queue.execution'].search_count([('ydental_task_id','in',exam['task_ids'])]))

    def test_real_source_referrals_timed_untimed_and_retry(self):
        from odoo import fields
        from datetime import timedelta
        s,c,q,l,e,d,a=opened_actual(self)
        timed=a|{'mode':'timed','mapping_id':self.mappings[1][0].id,'reason':'Synthetic clinician timed referral',
            'start':fields.Datetime.to_string(self.start),'end':fields.Datetime.to_string(self.end),'source':key()}
        r=s._operate('refer',timed,key());self.assertTrue(r['task_id']);self.assertEqual(e.state,'serving')
        same=s._operate('refer',timed,key());self.assertEqual(r['task_id'],same['task_id'])
        untimed=a|{'mode':'untimed','mapping_id':self.mappings[1][0].id,'reason':'Synthetic untimed referral',
            'valid_until':fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=1)),'source':key()}
        before=self.root['ydental.supply.claim'].search_count([])
        r=s._operate('refer',untimed,key());self.assertEqual(r['target_qualification'],'not_acquired');self.assertEqual(before,self.root['ydental.supply.claim'].search_count([]))
        target=bind(self,self.users['frontdesk'],self.stores[1]);ref=self.root['ydental.intake.referral'].browse(r['id'])
        accepted=target._operate('accept_referral',{'record_id':ref.id,'version':ref.ydental_version,
            'start':fields.Datetime.to_string(self.start),'end':fields.Datetime.to_string(self.end)},key())
        self.assertTrue(accepted['task_id']);self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before+1)
        with self.assertRaises(AccessError):s.env['ydental.clinical.document'].create({'name':'arbitrary target write','ydental_store_id':self.stores[1].id})

    def test_prescription_duplicate_source_return_does_not_reopen_allowance(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self);issued=prescription(self,s,a);c._operate('handover',handover_args(d,l))
        p,args=pharmacy_start(self,issued)
        dose=args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,'source':key(),'reason':'Synthetic actual four','policy':'demo_confirmation'}
        r=p._operate('dispense',dose,key());same=p._operate('dispense',dose,key());self.assertEqual(r['event_id'],same['event_id']);self.assertEqual(same['remaining'],2)
        returned=p._operate('return_material',{'event_id':r['event_id'],'inventory_event_id':r['inventory_event_ids'][0],
            'quantity':1,'uom_id':self.uom.id,'source':key(),'reason':'Actual physical return, quarantine'},key())
        self.assertTrue(returned['id']);self.assertEqual(p._remaining(p._model('line').browse(issued['line_ids'][0])),2)
        with self.assertRaises(AccessError):p.env['ydental.inventory.service']._operate('issue',{'lot_id':self.lots['medicine'],'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'No warehouse authority'},key())

    def test_closed_pharmacy_needs_fresh_task_specific_append(self):
        from odoo import fields
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        self.users['frontdesk'].write({'group_ids':[fields.Command.link(self.root.ref('ydental_queue.ydental_group_append').id)]})
        s,c,q,l,e,d,a=opened_actual(self);issued=prescription(self,s,a);c._operate('handover',handover_args(d,l))
        supply=self.group.env['ydental.supply.service']
        for state in ('draining','closed'):
            supply._operate('business',{'area_id':self.pharmacy_area.id,'version':supply._business_record(self.stores[0],self.pharmacy_area.id).ydental_version,'state':state,'reason':'Synthetic pharmacy stop ordinary admissions'},key())
        task=self.root['ydental.intake.task'].browse(issued['task_ids'][0]);self.front._operate('arrive',{'patient_id':task.ydental_patient_id.id},key())
        with self.assertRaises(UserError):self.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
        append=self.front.env['ydental.queue.service']._bind_connection(key()+key())._operate('append',{'task_id':task.id,'reason':'Explicit actual closed pharmacy intake'})
        p,args=pharmacy_start(self,issued)
        p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,'source':key(),'reason':'Synthetic closed actual four','policy':'demo_confirmation'},key())
        finished=p._operate('finish',args|{'reason':'Finish first closed segment'},key())
        next_task=self.root['ydental.intake.task'].browse(finished['next_task_id'])
        with self.assertRaises(UserError):self.front._operate('report',{'task_id':next_task.id,'version':next_task.ydental_version},key())
        permits=self.root['ydental.queue.append.permit'].search([('ydental_task_id','=',task.id)]);self.assertEqual(permits.state,'ended')
        self.assertFalse(self.root['ydental.queue.append.permit'].search_count([('ydental_task_id','=',next_task.id)]))

    def test_exam_actual_start_remains_fail_closed_until_s09(self):
        from .common import queue_bind, lease_args, arrive_report
        s,c,q,l,e,d,a=opened_actual(self)
        lines=[{'mapping_id':self.mappings[0][2].id,'quantity':1,'uom_id':self.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''}]
        draft=s._operate('order',a|{'kind':'exam','purpose':'Synthetic examination source','lines':lines},key())
        issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
        c._operate('handover',handover_args(d,l))
        arrive_report(self,{'task_id':issued['task_ids'][0]})
        exam=queue_bind(self,user=self.second);lease=exam._operate('enter',{'station_id':self.stations[0][2].id})
        called=exam._operate('call',lease_args(lease))
        with self.assertRaises(AccessError):exam._operate('start',lease_args(lease)|{'entry_id':called['entry_id']})
        self.assertFalse(self.root['ydental.queue.execution'].search_count([('ydental_task_id','=',issued['task_ids'][0])]))

    def test_material_only_delta_retains_original_quantity_and_price(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        original=s._operate('execute',execute_args(self,a),key())
        extra=s._operate('correct',a|{'event_id':original['event_id'],'delta':0,'source':key(),
            'reason':'Verified additional physical material only','materials':execute_args(self,a)['materials']},key())
        self.assertEqual(extra['amount'],0);self.assertEqual(len(extra['move_ids']),1)
        self.assertEqual(s._model('event').browse(original['event_id']).ydental_quantity,1)
        self.assertEqual(s._model('fee').browse(extra['fee_id']).ydental_unit_price,600)

    def test_historical_recovery_inventory_preserves_original_actual_time(self):
        receive(self);s,c,q,l,e,d,a=opened_actual(self)
        result=s._operate('execute',execute_args(self,a,actual=True),key())
        actual=s._model('event').browse(result['event_id']).ydental_actual_at
        pricer=bind(self,self.users['price']).env['ydental.queue.service']._bind_connection(key()+key()).env[s._name]
        pricer._operate('review_price',{'event_id':result['event_id'],'unit_price':600,'currency_id':self.currency.id,'evidence':'Original historical quote'},key())
        with patch.object(fields.Datetime,'now',return_value=actual+timedelta(minutes=2)):
            result=s._operate('reconcile',{'event_id':result['event_id'],'reason':'Later bookkeeping keeps original actual time'},key())
        inventory=self.root['ydental.inventory.event'].browse(result['inventory_event_ids'])
        self.assertEqual(inventory.ydental_actual_at,actual)

    def test_next_day_remaining_requires_new_arrival_report_and_holder(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self);issued=prescription(self,s,a);c._operate('handover',handover_args(d,l))
        p,args=pharmacy_start(self,issued)
        p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,'source':key(),'reason':'Actual first-day four','policy':'demo_confirmation'},key())
        ended=p._operate('finish',args|{'reason':'End first-day dispensing'},key())
        tomorrow=fields.Datetime.now()+timedelta(days=1)
        with patch.object(fields.Datetime,'now',return_value=tomorrow):
            with self.assertRaises((AccessError,UserError)):
                p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':2,'source':key(),'reason':'Old holder cannot serve next day','policy':'demo_confirmation'},key())
            supply=self.group.env['ydental.supply.service']
            supply._operate('business',{'area_id':self.pharmacy_area.id,'state':'open','reason':'Explicit next-day pharmacy opening'},key())
            p,args=pharmacy_start(self,issued,ended['next_task_id'])
            last=p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':2,'source':key(),'reason':'Actual next-day two','policy':'demo_confirmation'},key())
            self.assertEqual(last['remaining'],0)
            self.assertEqual(p._operate('finish',args|{'reason':'End second-day dispensing'},key())['order_state'],'done')

    def test_referral_target_closed_and_expiry_preserve_source_without_capacity(self):
        s,c,q,l,e,d,a=opened_actual(self)
        target=bind(self,self.users['manager'],self.stores[1]);supply=target.env['ydental.supply.service']
        for state in ('draining','closed'):
            supply._operate('business',{'area_id':self.areas[1][0].id,'version':supply._business_record(self.stores[1],self.areas[1][0].id).ydental_version,'state':state,'reason':'Target explicitly stopped intake'},key())
        before=self.root['ydental.supply.claim'].search_count([])
        with self.assertRaises(UserError):s._operate('refer',a|{'mode':'timed','mapping_id':self.mappings[1][0].id,'reason':'Closed target must fail','start':str(self.start),'end':str(self.end),'source':key()},key())
        self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before);self.assertEqual(e.state,'serving')
        with self.assertRaises(UserError):s._operate('refer',a|{'mode':'untimed','mapping_id':self.mappings[1][0].id,'reason':'Expired target must fail','valid_until':str(fields.Datetime.now()-timedelta(minutes=1)),'source':key()},key())
        self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before)

    def test_cross_legal_entity_referral_uses_trusted_source_without_target_account_authority(self):
        s,c,q,l,e,d,a=opened_actual(self)
        from .treatment_common import cross_legal_target
        store,mapping,slot=cross_legal_target(self)
        result=s._operate('refer',a|{'mode':'untimed','mapping_id':mapping.id,'reason':'Trusted S05 source authority only','valid_until':str(fields.Datetime.now()+timedelta(days=1)),'source':key()},key())
        self.assertTrue(result['id'])
        with self.assertRaises(AccessError):s.env['ydental.intake.mapping'].browse(mapping.id).write({'name':'Arbitrary target mutation'})

    def test_actual_chairside_medicine_has_no_takeaway_task(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self)
        result=s._operate('execute',a|{'catalog_id':self.drug_catalog.id,'quantity':2,'source':key(),'reason':'Verified actual chairside medicine',
            'materials':[{'lot_id':self.lots['medicine'],'quantity':2,'uom_id':self.uom.id,'kind':'chairside'}],
            'teeth':[],'already_performed':False,'policy':'demo_confirmation'},key())
        self.assertEqual(result['amount'],20);self.assertEqual(self.root['stock.move'].browse(result['move_ids']).quantity,2)
        self.assertFalse(self.root['ydental.treatment.segment'].search_count([('ydental_patient_id','=',e.ydental_patient_id.id)]))

    def test_actual_time_is_frozen_in_current_service_and_rejects_future(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        args=execute_args(self,a)
        with self.assertRaises(ValidationError):s._operate('execute',args|{'actual_at':str(e.ydental_started_at-timedelta(seconds=1))},key())
        with self.assertRaises(ValidationError):s._operate('execute',args|{'actual_at':str(fields.Datetime.now()+timedelta(minutes=1))},key())
        original=e.ydental_started_at+timedelta(seconds=1)
        with patch.object(fields.Datetime,'now',return_value=original+timedelta(seconds=10)):
            result=s._operate('execute',args|{'actual_at':str(original)},key())
        self.assertEqual(s._model('event').browse(result['event_id']).ydental_actual_at,original)
        self.assertEqual(self.root['ydental.inventory.event'].browse(result['inventory_event_ids']).ydental_actual_at,original)

    def test_already_performed_native_business_failure_retains_fact_zero_half_bookkeeping(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        original=type(self.stock)._move
        def fail(service,event):
            original(service,event);raise UserError('native_failure: Actual physical project needs bookkeeping review')
        with patch.object(type(self.stock),'_move',fail):
            result=s._operate('execute',execute_args(self,a,actual=True),key())
        self.assertEqual(result['state'],'pending');self.assertEqual(result['pending_reason'],'bookkeeping_failed')
        self.assertFalse(result['move_ids']);self.assertFalse(result['fee_id']);self.assertFalse(result['inventory_event_ids'])
        event=result['event_id'];result=s._operate('reconcile',{'event_id':event,'reason':'Original physical source, native bookkeeping recovered'},key())
        self.assertEqual(result['event_id'],event);self.assertEqual(result['amount'],600);self.assertEqual(len(result['move_ids']),1)

    def test_actual_pharmacy_shortage_preserves_allowance_and_prevents_early_finish(self):
        price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self);issued=prescription(self,s,a);c._operate('handover',handover_args(d,l))
        p,args=pharmacy_start(self,issued)
        result=p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,'source':key(),
            'reason':'Verified physically dispensed; stock ledger requires correction','policy':'demo_confirmation','already_performed':True},key())
        self.assertEqual((result['state'],result['remaining']),('pending',2));self.assertFalse(result['fee_id'])
        with self.assertRaises(UserError):p._operate('finish',args|{'reason':'Do not finish half bookkeeping'},key())
        receive(self,10,'medicine');self.stock._operate('recover',{'event_id':result['inventory_event_ids'][0],'reason':'Original actual dispensing physical receipt evidence'},key())
        result=p._operate('reconcile',{'event_id':result['event_id'],'reason':'Finish original dispensing bookkeeping'},key());self.assertEqual(result['amount'],40)
        self.assertTrue(p._operate('finish',args|{'reason':'Original four confirmed'},key())['next_task_id'])


    def test_disabled_batch_new_execution_rejected_original_fact_recovery_no_fake_activation(self):
        receive(self);price(self);s,c,q,l,e,d,a=opened_actual(self)
        self.stock._operate('lot_edit',{'lot_id':self.lots['material'],'enabled':False,'reason':'Disable new use'},key())
        with self.assertRaises(UserError):s._operate('execute',execute_args(self,a),key())
        result=s._operate('execute',execute_args(self,a,actual=True),key());self.assertEqual(result['state'],'pending')
        receive(self,1)
        self.stock._operate('recover',{'event_id':result['inventory_event_ids'][0],'reason':'Evidenced original historical accounting only'},key())
        result=s._operate('reconcile',{'event_id':result['event_id'],'reason':'Original disabled batch actual fact'},key())
        self.assertEqual(result['amount'],600)
        self.assertFalse(self.stock._batch(self.root['stock.lot'].browse(self.lots['material']),self.stores[0]).ydental_enabled)

    def test_other_operator_cannot_reconcile_original_responsibility(self):
        price(self);s,c,q,l,e,d,a=opened_actual(self)
        result=s._operate('execute',execute_args(self,a,actual=True),key())
        other=bind(self,self.second).env['ydental.queue.service']._bind_connection(key()+key()).env[s._name]
        with self.assertRaises(AccessError):other._operate('reconcile',{'event_id':result['event_id'],'reason':'Cannot impersonate original actor'},key())
