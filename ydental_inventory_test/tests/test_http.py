import json
import re

from odoo.tests import HttpCase, tagged

from .common import bind, key, quantity, receive, setup
from ..models.adapter import SyntheticSource


@tagged('post_install', '-at_install')
class TestInventoryHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)

    def select(self, role='stock'):
        self.authenticate(self.users[role].login, 's07-test-password')
        page = self.url_open('/ydental/access')
        self.csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = int(re.search(r'name="revision" value="([0-9]+)"', page.text).group(1))
        r = self.url_open('/ydental/access/action', data={'csrf_token': self.csrf, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(r.status_code, 200, r.text); self.revision = r.json()['revision']

    def action(self, op, args, request_key=None, revision=None):
        return self.url_open('/ydental/inventory/action', data={'csrf_token': self.csrf, 'revision': self.revision if revision is None else revision,
            'key': request_key or key(), 'operation': op, 'payload': json.dumps(args), 'output': 'json'})

    def rpc(self, model, method, args, context=None):
        return self.url_open('/web/dataset/call_kw/' + model + '/' + method, data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'call',
            'params': {'model': model, 'method': method, 'args': args, 'kwargs': {'context': context or {}}}}), headers={'Content-Type': 'application/json'}).json()

    def test_http_t01_issue_and_retry(self):
        receive(self); self.select(); k=key()
        args={'lot_id': self.lots['medicine'], 'quantity':3, 'uom_id':self.uom.id, 'source_key':key(), 'reason':'HTTP actual issue evidence'}
        first=self.action('issue',args,k); self.assertEqual(first.status_code,200,first.text)
        retry=self.action('issue',args,k); self.assertEqual(first.json()['id'],retry.json()['id'])
        page=self.url_open('/ydental/inventory'); self.assertEqual(page.status_code,200,page.text); self.assertIn('7.0',page.text)

    def test_http_t07_reader_and_native_rpc(self):
        receive(self); self.select('reader')
        page=self.url_open('/ydental/inventory'); self.assertEqual(page.status_code,200,page.text)
        self.assertNotIn('data-inventory-form="issue"',page.text)
        self.assertEqual(self.action('issue',{}).status_code,403)
        self.assertIn('error',self.rpc('stock.lot','read',[[self.lots['medicine']],['product_qty','quant_ids']]))
        self.assertIn('error',self.rpc('ydental.inventory.event','write',[[1],{'state':'done'}],{'ydental_inventory_mutation':True}))

    def test_http_purchase_type_is_bound_to_warehouse_store(self):
        self.select('stock')
        warehouse = self.root['stock.warehouse'].search([('ydental_store_id', '=', self.stores[0].id)], limit=1)
        self.assertTrue(warehouse)
        response = self.url_open('/ydental/inventory/purchase-type?revision=%s' % self.revision)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'store_id': self.stores[0].id,
            'company_id': self.stores[0].company_id.id, 'picking_type_id': warehouse.in_type_id.id})

        self.select('reader')
        denied = self.url_open('/ydental/inventory/purchase-type?revision=%s' % self.revision)
        self.assertEqual(denied.status_code, 403, denied.text)

    def test_http_t07_stock_manager_native_bypass(self):
        receive(self); self.select('stock2')
        self.assertIn('error',self.rpc('stock.quant','search_count',[[]]))
        self.assertIn('error',self.rpc('stock.quant','create',[{'quantity':999,'product_id':self.products['medicine']}]))
        self.assertIn('error',self.rpc('stock.lot','export_data',[[self.lots['medicine']],['name']]))
        self.assertIn('error',self.rpc('product.product','read',[[self.products['medicine']],['qty_available']]))

    def test_http_t03_cross_store_and_batch_forgery(self):
        self.select(); other=self.lots['medicine']
        r=self.url_open('/ydental/access/action',data={'csrf_token':self.csrf,'revision':self.revision,'operation':'switch','payload':json.dumps({'store_id':self.stores[1].id}),'output':'json'})
        old=self.revision;self.revision=r.json()['revision']
        self.assertEqual(self.action('issue',{},revision=old).status_code,409)
        self.assertEqual(self.action('issue',{'lot_id':other,'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'Forged cross store'}).status_code,403)

    def test_http_t09_csrf_hook_and_scan_failclosed(self):
        self.select()
        self.assertEqual(self.url_open('/ydental/inventory/action',data={'operation':'setup','revision':self.revision,'key':key(),'payload':'{}'}).status_code,400)
        self.assertIn('error',self.rpc('ydental.inventory.service','_source_action',[{}]))
        scan=self.url_open('/ydental/inventory/scan',data={'csrf_token':self.csrf,'revision':self.revision,'code':'UNKNOWN'})
        self.assertEqual(scan.json()['result'],'unsupported_source');self.assertFalse(scan.json()['received'])

    def test_http_t09_catalog_does_not_read_stock(self):
        receive(self);self.select('catalog')
        page=self.url_open('/ydental/inventory/catalog');self.assertEqual(page.status_code,200,page.text)
        self.assertNotIn('data-lot=',page.text);self.assertNotIn('data-event=',page.text)
        self.assertEqual(self.url_open('/ydental/inventory').status_code,403)

    def test_http_t07_none_patient_attachment_and_export(self):
        self.select('none')
        self.assertEqual(self.url_open('/ydental/inventory').status_code,403)
        self.assertIn('error',self.rpc('ydental.inventory.event','search_read',[[]]))
        self.assertIn('error',self.rpc('ydental.patient','search_read',[[]]))

    def test_http_t05_return_verification(self):
        receive(self);self.select()
        issued=self.action('issue',{'lot_id':self.lots['medicine'],'quantity':3,'uom_id':self.uom.id,'source_key':key(),'reason':'Issue'}).json()
        returned=self.action('return',{'event_id':issued['id'],'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'Physical return'});self.assertEqual(returned.status_code,200,returned.text)
        verified=self.action('verify',{'event_id':returned.json()['id'],'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'Inspected real return','disposition':'release'})
        self.assertEqual(verified.status_code,200,verified.text)

    def test_http_t03_expired_and_disabled_lot_ids_refused(self):
        from datetime import timedelta
        from odoo import fields
        self.select()
        expired=self.action('lot',{'product_id':self.products['medicine'],'name':'S07-expired-'+key(),'expiration':fields.Datetime.to_string(fields.Datetime.now()-timedelta(days=1))})
        self.assertEqual(expired.status_code,200,expired.text)
        args={'lot_id':expired.json()['id'],'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'Actual expired batch receipt'}
        self.assertEqual(self.action('receive',args).status_code,200)
        args['source_key']=key();r=self.action('issue',args);self.assertEqual(r.status_code,409);self.assertIn('lot_expired',r.text)
        self.assertEqual(self.action('lot_edit',{'lot_id':self.lots['medicine'],'enabled':False,'reason':'Stopped batch'}).status_code,200)
        args.update(lot_id=self.lots['medicine'],source_key=key());r=self.action('issue',args)
        self.assertEqual(r.status_code,409);self.assertIn('lot_disabled',r.text)

    def test_http_t07_permission_revocation_next_request(self):
        receive(self);self.select()
        self.admin._grant(self.users['stock'].id,self.stores[0].id,{'warehouse':'none'})
        self.assertEqual(self.url_open('/ydental/inventory').status_code,403)
        self.assertEqual(self.action('issue',{}).status_code,403)
        self.assertIn('error',self.rpc('ydental.inventory.event','search_read',[[]]))

    def test_http_t06_recovery_rejects_observed_count(self):
        receive(self,2);self.select()
        count=self.action('inventory',{'lot_id':self.lots['medicine'],'counted':2,'uom_id':self.uom.id,'source_key':key(),'reason':'Actual count agrees with ledger'})
        self.assertEqual(count.status_code,200,count.text);self.assertEqual(count.json()['state'],'observed')
        rejected=self.action('recover',{'event_id':count.json()['id'],'reason':'Only pending execution may recover'})
        self.assertEqual(rejected.status_code,409,rejected.text)
        event=self.env['ydental.inventory.event'].sudo().browse(count.json()['id'])
        self.assertEqual(event.state,'observed');self.assertFalse(event.ydental_move_id)

    def test_http_rework_category_via_trusted_server_bridge_and_rpc_refusal(self):
        from unittest.mock import patch
        self.admin._grant(self.users['stock'].id, self.stores[0].id,
            {'warehouse': 'write', 'pharmacy': 'write', 'medical': 'write'})
        self.select()
        for kind in ('prescription', 'chairside', 'treatment'):
            categories = ('material', 'prosthesis') if kind != 'treatment' else ('medicine', 'prosthesis')
            for category in categories:
                lot = self.lots[category]; receive(self, 3, lot)
                source = SyntheticSource(self.users['stock'].id, self.stores[0].id, key(), kind, lot, 1, self.uom.id)
                # Temporary private server bridge only during this HttpCase;
                # no installed route, RPC method or dictionary authorization.
                def bridge(service, store, **kwargs):
                    return service._source_action(source)
                before = tuple(self.env[m].sudo().search_count([]) for m in ('ydental.inventory.event', 'stock.move', 'stock.quant'))
                with patch.object(type(self.stock), '_issue', bridge):
                    rejected = self.action('issue', {})
                self.assertEqual(rejected.status_code, 409, rejected.text)
                self.assertIn('source_category_mismatch', rejected.text)
                after = tuple(self.env[m].sudo().search_count([]) for m in ('ydental.inventory.event', 'stock.move', 'stock.quant'))
                self.assertEqual(after, before)
                self.assertIn('error', self.rpc('ydental.inventory.service', '_source_action', [{'kind':kind,'lot_id':lot}]))

    def test_http_rework_expired_pending_recovery_and_new_execution_refusal(self):
        self._http_rework_pending(True)

    def test_http_rework_disabled_pending_recovery_and_new_execution_refusal(self):
        self._http_rework_pending(False)

    def _http_rework_pending(self, expired):
        from datetime import timedelta
        from unittest.mock import patch
        from odoo import fields
        lot = self.lots['material']; doctor = bind(self, self.users['doctor'])
        original = doctor._source_action(SyntheticSource(self.users['doctor'].id, self.stores[0].id, key(), 'treatment', lot, 2, self.uom.id, already_performed=True))
        self.select()
        if not expired:
            self.assertEqual(self.action('lot_edit', {'lot_id':lot,'enabled':False,'reason':'Stopped after execution'}).status_code, 200)
        future = fields.Datetime.now() + timedelta(days=46) if expired else fields.Datetime.now()
        with patch.object(type(self.stock), '_now', return_value=future):
            args = {'event_id':original['id'],'reason':'Verified original performed event'}
            self.assertEqual(self.action('recover', args).status_code, 409)
            receipt = self.action('receive', {'lot_id':lot,'quantity':5,'uom_id':self.uom.id,'source_key':key(),'reason':'Actual incoming stock evidence'})
            self.assertEqual(receipt.status_code,200,receipt.text)
            first = self.action('recover',args); retry = self.action('recover',args)
            self.assertEqual(first.status_code,200,first.text);self.assertEqual(first.json()['move_id'],retry.json()['move_id'])
            denied = self.action('issue', {'lot_id':lot,'quantity':1,'uom_id':self.uom.id,'source_key':key(),'reason':'New execution must refuse'})
            self.assertEqual(denied.status_code,409,denied.text)
            self.assertIn('lot_expired' if expired else 'lot_disabled',denied.text)
        event = self.env['ydental.inventory.event'].sudo().browse(original['id'])
        self.assertEqual(event.ydental_correction_id.id,receipt.json()['id']);self.assertEqual(event.ydental_price_snapshot['unit_price'],20)
        self.assertEqual(quantity(self,lot),3)
        self.select('reader');self.assertEqual(self.action('recover',args).status_code,403)
        self.assertIn('error',self.rpc('ydental.inventory.event','write',[[original['id']],{'state':'pending','ydental_correction_id':False}]))
