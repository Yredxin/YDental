from unittest.mock import patch

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
        self.assertFalse(self.root['ydental.inventory.event'].search_count([('ydental_source_namespace','=','s08b-clinical')]))

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
        for category in ('warehouse','price','billing'):self.assertEqual(levels[category],'none')

    def test_frozen_exam_cancel_unperformed_and_new_order(self):
        s,c,q,l,e,d,a=opened_actual(self)
        lines=[{'mapping_id':self.mappings[0][i].id,'quantity':1,'uom_id':self.uom.id,'product_id':False,'specification':'','usage':'','frequency':'','course':''} for i in (2,3)]
        draft=s._operate('order',a|{'kind':'exam','purpose':'Synthetic panorama and CBCT','lines':lines},key())
        issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
        cancelled=s._operate('cancel_exam',a|{'line_id':issued['line_ids'][1],'order_version':issued['version'],'reason':'Patient declined unperformed synthetic CBCT'},key())
        self.assertEqual(cancelled['state'],'cancelled')
        with self.assertRaises(UserError):s._operate('edit_order',a|{'order_id':draft['order_id'],'version':cancelled['order_version'],'purpose':'Cannot append','lines':lines},key())
        new=s._operate('order',a|{'kind':'exam','purpose':'Separate additional examination','lines':lines[:1]},key());self.assertNotEqual(new['order_id'],draft['order_id'])
