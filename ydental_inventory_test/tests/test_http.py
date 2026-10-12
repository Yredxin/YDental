import json
import re

from odoo.tests import HttpCase, tagged

from .common import key, receive, setup


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

    def test_http_t07_stock_manager_native_bypass(self):
        receive(self); self.select('stock2')
        self.assertEqual(self.rpc('stock.quant','search_count',[[]]).get('result'),0)
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
