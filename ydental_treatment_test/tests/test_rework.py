"""Real service regressions for GPT-REVIEW 6135903692, before product fixes."""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from .common import handover_args, key, price
from .treatment_common import opened_actual, pharmacy_start, receive, setup


@tagged('post_install', '-at_install')
class TestReworkBoundaries(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def chairside(self, args, rows, quantity=2, actual=False):
        return args | {'catalog_id': self.drug_catalog.id, 'quantity': quantity,
            'source': key(), 'reason': 'Explicit synthetic chairside fact',
            'materials': rows, 'teeth': [], 'already_performed': actual, 'policy': 'demo_confirmation'}

    def line(self, **values):
        return dict(mapping_id=self.drug_mapping.id, quantity=6, uom_id=self.uom.id,
            product_id=self.products['medicine'], specification='Synthetic specification',
            usage='Synthetic usage', frequency='Synthetic frequency', course='Synthetic course', **values)

    def test_rework_chairside_empty_batch_must_not_confirm_fee(self):
        price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        with self.assertRaises(UserError):
            s._operate('execute', self.chairside(a, []), key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id', '=', e.id)]))

    def test_rework_chairside_quantity_mismatch_must_not_confirm_fee(self):
        receive(self, 20, 'medicine'); price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        row = {'lot_id': self.lots['medicine'], 'quantity': 1, 'uom_id': self.uom.id, 'kind': 'chairside'}
        with self.assertRaises(UserError):
            s._operate('execute', self.chairside(a, [row], quantity=2), key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id', '=', e.id)]))

    def test_rework_incomplete_rx_draft_allowed_but_issue_rejected(self):
        s,c,q,l,e,d,a = opened_actual(self)
        line = self.line(); line.update(specification='', usage='  ', frequency='', course='')
        draft = s._operate('order', a | {'kind': 'prescription', 'purpose': 'Incomplete synthetic draft', 'lines': [line]}, key())
        with self.assertRaises(UserError):
            s._operate('issue', a | {'order_id': draft['order_id'], 'version': draft['version']}, key())
        self.assertEqual(s._model('order').browse(draft['order_id']).state, 'draft')
        self.assertFalse(s._model('segment').search_count([('ydental_order_id', '=', draft['order_id'])]))

    def test_rework_second_sku_cannot_borrow_generic_service_price(self):
        product = self.stock._operate('product', {'code': 'R-' + key(), 'name': 'Distinct synthetic medicine B',
            'kind': 'medicine', 'stock_uom_id': self.uom.id, 'issue_uom_id': self.uom.id, 'step': 1,
            'specification': 'Distinct SKU specification'}, key())['id']
        lot = self.stock._operate('lot', {'product_id': product, 'name': 'R-' + key(),
            'expiration': str(fields.Datetime.now() + timedelta(days=45))}, key())['id']
        self.stock._operate('receive', {'lot_id': lot, 'quantity': 20, 'uom_id': self.uom.id,
            'source_key': key(), 'reason': 'Physical synthetic medicine B'}, key())
        price(self, catalog=self.drug_catalog, amount=10)
        s,c,q,l,e,d,a = opened_actual(self)
        line = self.line(); line['product_id'] = product
        draft = s._operate('order', a | {'kind': 'prescription', 'purpose': 'Unproven SKU fee source', 'lines': [line]}, key())
        issued = s._operate('issue', a | {'order_id': draft['order_id'], 'version': draft['version']}, key())
        c._operate('handover', handover_args(d,l))
        p,args = pharmacy_start(self, issued)
        with self.assertRaises(UserError):
            p._operate('dispense', args | {'line_id': issued['line_ids'][0], 'lot_id': lot,
                'quantity': 4, 'source': key(), 'reason': 'No authorized SKU price link', 'policy': 'demo_confirmation'}, key())
        self.assertEqual(p._remaining(p._model('line').browse(issued['line_ids'][0])), 6)

    def test_rework_source_only_company_can_initiate_controlled_cross_legal_referral(self):
        s,c,q,l,e,d,a = opened_actual(self)
        from .treatment_common import cross_legal_target
        store,mapping,slot=cross_legal_target(self)
        company=store.company_id
        self.assertNotIn(company, self.users['doctor'].company_ids)
        result = s._operate('refer', a | {'mode': 'untimed', 'mapping_id': mapping.id,
            'reason': 'S05 trusted source, no arbitrary target write', 'valid_until': str(fields.Datetime.now() + timedelta(days=1)), 'source': key()}, key())
        self.assertEqual(result['target_qualification'], 'not_acquired')
        self.assertEqual(e.state, 'serving')

    def second_medicine(self, publish=True):
        product = self.stock._operate('product', {'code': 'R-' + key(), 'name': 'Distinct synthetic medicine B',
            'kind': 'medicine', 'stock_uom_id': self.uom.id, 'issue_uom_id': self.uom.id, 'step': 1,
            'specification': 'Synthetic B specification'}, key())['id']
        lot = self.stock._operate('lot', {'product_id': product, 'name': 'R-' + key(),
            'expiration': str(fields.Datetime.now() + timedelta(days=45))}, key())['id']
        self.stock._operate('receive', {'lot_id': lot, 'quantity': 20, 'uom_id': self.uom.id,
            'source_key': key(), 'reason': 'Synthetic B physical receipt'}, key())
        catalog = self.group._operate('catalog', {'code': 'R-' + key(), 'name': 'Medicine B exact fee catalog',
            'kind': 'medicine', 'capability_id': self.capabilities[0].id, 'uom_id': self.uom.id}, key())['id']
        catalog = self.root['ydental.intake.catalog'].browse(catalog)
        self.group._operate('mapping', {'catalog_id': catalog.id, 'area_id': self.pharmacy_area.id,
            'execution_area_id': self.pharmacy_area.id}, key())
        price(self, catalog=catalog, amount=27)
        if publish:
            self.publish_link(product, catalog)
        return product, lot, catalog

    def publish_link(self, product, catalog):
        from .common import bind
        service = bind(self,self.users['price']).env['ydental.queue.service']._bind_connection(key()+key()).env['ydental.treatment.service']
        return service._operate('publish_medicine', {'catalog_id': catalog.id, 'product_id': product,
            'uom_id': self.uom.id, 'evidence': 'Explicit synthetic SKU and service price review', 'policy': 'demo_confirmation'}, key())

    def test_rework_chairside_wrong_sku_and_unit_and_shortage_rejected_without_sources(self):
        receive(self, 1, 'medicine');price(self,catalog=self.drug_catalog,amount=10)
        product,lot,catalog=self.second_medicine()
        s,c,q,l,e,d,a=opened_actual(self)
        row={'lot_id':lot,'quantity':2,'uom_id':self.uom.id,'kind':'chairside'}
        with self.assertRaises(UserError):s._operate('execute',self.chairside(a,[row]),key())
        row['lot_id']=self.lots['medicine']
        with self.assertRaises(UserError):s._operate('execute',self.chairside(a,[row]),key())
        row['quantity']=1;row['uom_id']=self.root.ref('uom.product_uom_dozen').id
        with self.assertRaises(UserError):s._operate('execute',self.chairside(a,[row],quantity=1),key())
        self.assertFalse(s._model('event').search_count([('ydental_execution_id','=',e.id)]))

    def test_rework_historical_empty_batches_preserve_fact_then_evidenced_recovery_once(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        s,c,q,l,e,d,a=opened_actual(self)
        r=s._operate('execute',self.chairside(a,[],actual=True),key())
        event=s._model('event').browse(r['event_id']);before=(event.ydental_actor_id.id,event.ydental_actual_at,event.ydental_station_id.id,event.ydental_price_snapshot_id.id)
        self.assertEqual(r['pending_reason'],'medicine_evidence_missing');self.assertFalse(r['fee_id']);self.assertFalse(r['move_ids'])
        self.assertEqual(event.ydental_reported_materials,{'rows':[],'catalog_id':self.drug_catalog.id})
        rows=[{'lot_id':self.lots['medicine'],'quantity':2,'uom_id':self.uom.id,'kind':'chairside'}]
        verified=s._operate('verify_medicine',{'event_id':event.id,'materials':rows,'evidence':'Original actual batch independently verified'},key())
        self.assertEqual((verified['event_id'],verified['amount']),(event.id,20));self.assertEqual(len(verified['move_ids']),1)
        self.assertEqual(before,(event.ydental_actor_id.id,event.ydental_actual_at,event.ydental_station_id.id,event.ydental_price_snapshot_id.id))
        same=s._operate('reconcile',{'event_id':event.id,'reason':'Recheck original'},key());self.assertEqual(same['fee_id'],verified['fee_id'])

    def test_rework_issue_rechecks_each_field_and_legacy_incomplete_line(self):
        s,c,q,l,e,d,a=opened_actual(self)
        for field in ('specification','usage','frequency','course'):
            for value in ('', '   ', None):
                row=self.line();row[field]=value
                draft=s._operate('order',a|{'kind':'prescription','purpose':'Incomplete draft field','lines':[row]},key())
                with self.assertRaises(UserError):s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
                self.assertEqual(s._model('order').browse(draft['order_id']).state,'draft')
                self.assertFalse(s._model('segment').search_count([('ydental_order_id','=',draft['order_id'])]))
        draft=s._operate('order',a|{'kind':'prescription','purpose':'Legacy row issue validation','lines':[self.line()]},key())
        line=s._model('line').search([('ydental_order_id','=',draft['order_id'])]);line._save({'ydental_usage':False})
        with self.assertRaises(UserError):s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())
        line._save({'ydental_usage':'Explicitly completed usage'})
        self.assertTrue(s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key())['task_ids'])

    def test_rework_two_skus_same_pharmacy_direction_separate_prices_and_snapshots(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        product,lot,catalog=self.second_medicine()
        s,c,q,l,e,d,a=opened_actual(self)
        b=self.line();b['product_id']=product;b['quantity']=2
        draft=s._operate('order',a|{'kind':'prescription','purpose':'Two actual SKUs one pharmacy direction','lines':[self.line(),b]},key())
        issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key());c._operate('handover',handover_args(d,l))
        p,args=pharmacy_start(self,issued)
        amounts=[]
        for line_id,batch,qty,sku,amount in ((issued['line_ids'][0],self.lots['medicine'],4,self.products['medicine'],40),(issued['line_ids'][1],lot,2,product,54)):
            r=p._operate('dispense',args|{'line_id':line_id,'lot_id':batch,'quantity':qty,'source':key(),'reason':'Exact SKU actual dispense','policy':'demo_confirmation'},key())
            event=p._model('event').browse(r['event_id']);fee=p._model('fee').browse(r['fee_id']);move=self.root['stock.move'].browse(r['move_ids'])
            self.assertEqual((fee.ydental_product_id.id,move.product_id.id,event.ydental_medicine_link_id.ydental_product_id.id),(sku,sku,sku))
            self.assertEqual(r['amount'],amount);self.assertEqual(fee.ydental_currency_id,self.currency)
            self.assertEqual(event.ydental_price_snapshot_id.ydental_catalog_id,event.ydental_medicine_link_id.ydental_catalog_id)
            amounts.append((event.id,fee.ydental_price_snapshot_id.id,fee.ydental_amount))
        old=self.root['ydental.intake.price'].search([('ydental_store_id','=',self.stores[0].id),('ydental_catalog_id','=',catalog.id),('state','=','published')])
        price(self,catalog=catalog,amount=99,start=fields.Datetime.now()+timedelta(seconds=10),replace=old)
        for event_id,snapshot,amount in amounts:
            fee=p._model('fee').search([('ydental_event_id','=',event_id)])
            self.assertEqual((fee.ydental_price_snapshot_id.id,fee.ydental_amount),(snapshot,amount))

    def test_rework_publish_link_requires_price_authority_and_forbids_generic_shared_catalog(self):
        from odoo.exceptions import AccessError
        price(self,catalog=self.drug_catalog,amount=10)
        product,lot,catalog=self.second_medicine(publish=False)
        s,c,q,l,e,d,a=opened_actual(self)
        payload={'catalog_id':catalog.id,'product_id':product,'uom_id':self.uom.id,'evidence':'Cannot publish as doctor','policy':'demo_confirmation'}
        with self.assertRaises(AccessError):s._operate('publish_medicine',payload,key())
        with self.assertRaises(UserError):self.publish_link(product,self.drug_catalog)
        link=self.publish_link(product,catalog)
        with self.assertRaises(AccessError):s.env['ydental.treatment.medicine.link'].browse(link['link_id']).write({'ydental_product_id':self.products['medicine']})

    def test_rework_actual_unlinked_second_sku_pending_no_wrong_price_then_evidenced_review(self):
        receive(self,20,'medicine');price(self,catalog=self.drug_catalog,amount=10)
        product,lot,catalog=self.second_medicine(publish=False)
        s,c,q,l,e,d,a=opened_actual(self);row=self.line();row['product_id']=product
        draft=s._operate('order',a|{'kind':'prescription','purpose':'Historical unlinked SKU','lines':[row]},key())
        issued=s._operate('issue',a|{'order_id':draft['order_id'],'version':draft['version']},key());c._operate('handover',handover_args(d,l));p,args=pharmacy_start(self,issued)
        r=p._operate('dispense',args|{'line_id':issued['line_ids'][0],'lot_id':lot,'quantity':4,'source':key(),'reason':'Physical B issue, price link unavailable','policy':'demo_confirmation','already_performed':True},key())
        event=p._model('event').browse(r['event_id']);self.assertEqual(r['remaining'],2);self.assertFalse(r['fee_id']);self.assertFalse(r['move_ids']);self.assertFalse(event.ydental_price_snapshot_id)
        original=(event.ydental_actor_id.id,event.ydental_actual_at,event.ydental_quantity)
        self.publish_link(product,catalog)
        r=p._operate('verify_medicine',{'event_id':event.id,'materials':[{'lot_id':lot,'quantity':4,'uom_id':self.uom.id,'kind':'prescription'}],'evidence':'Verified original B SKU and original published price'},key())
        self.assertEqual(r['amount'],108);self.assertEqual(original,(event.ydental_actor_id.id,event.ydental_actual_at,event.ydental_quantity))
        self.assertEqual(p._remaining(p._model('line').browse(issued['line_ids'][0])),2)

    def test_rework_cross_legal_timed_untimed_capacity_closed_invalid_and_no_arbitrary_write(self):
        from .treatment_common import cross_legal_target
        from .common import bind,qualify
        from odoo.exceptions import AccessError
        store,mapping,slot=cross_legal_target(self)
        s,c,q,l,e,d,a=opened_actual(self)
        self.assertNotIn(store.company_id,self.users['doctor'].company_ids)
        before=self.root['ydental.supply.claim'].search_count([])
        timed=a|{'mode':'timed','mapping_id':mapping.id,'start':str(self.start),'end':str(self.end),'source':key(),'reason':'Real cross-legal timed source'}
        result=s._operate('refer',timed,key());self.assertTrue(result['task_id'])
        self.assertEqual(s._operate('refer',timed,key())['task_id'],result['task_id'])
        self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before+1)
        untimed=a|{'mode':'untimed','mapping_id':mapping.id,'valid_until':str(fields.Datetime.now()+timedelta(days=1)),'source':key(),'reason':'Real cross-legal untimed source'}
        referral=s._operate('refer',untimed,key());self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before+1)
        target=bind(self,self.users['frontdesk'],store)
        self.assertTrue(target._operate('accept_referral',{'record_id':referral['id'],'version':referral['version'],'start':str(self.start),'end':str(self.end)},key())['task_id'])
        self.assertEqual(self.root['ydental.supply.claim'].search_count([]),before+2)
        for i in range(3):qualify(self,mapping=mapping,service=target)
        with self.assertRaises(UserError):s._operate('refer',timed|{'source':key()},key())
        with self.assertRaises(AccessError):s.env['ydental.intake.mapping'].browse(mapping.id).write({'name':'Forbidden B mutation'})
        with self.assertRaises(AccessError):bind(self,self.users['doctor'],store)
        manager=bind(self,self.users['manager'],store);supply=manager.env['ydental.supply.service']
        supply._operate('business',{'area_id':mapping.ydental_area_id.id,'version':supply._business_record(store,mapping.ydental_area_id.id).ydental_version,'state':'draining','reason':'Stop target intake'},key())
        count=self.root['ydental.intake.referral'].search_count([])
        with self.assertRaises(UserError):s._operate('refer',untimed|{'source':key()},key())
        self.assertEqual(self.root['ydental.intake.referral'].search_count([]),count)
        mapping._save({'active':False})
        with self.assertRaises(UserError):s._operate('refer',untimed|{'source':key()},key())
        self.assertEqual(e.state,'serving')
