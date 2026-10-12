import json

from odoo.tests import HttpCase, tagged

from .test_http import TestClinicalHTTP
from .common import key, price
from .treatment_common import setup, receive


@tagged('post_install', '-at_install')
class TestTreatmentHTTP(TestClinicalHTTP):
    @classmethod
    def setUpClass(cls):
        HttpCase.setUpClass.__func__(cls)
        setup(cls)
        cls.admin._grant(cls.users['reader'].id,cls.stores[0].id,{'medical':'read'})

    def t_action(self, operation, payload, request_key=None):
        return self.url_open('/ydental/treatment/action',data={'csrf_token':self.csrf,'revision':self.revision,
            'connection':self.connection,'operation':operation,'payload':json.dumps(payload),'key':request_key or key()})

    def medical(self):
        self.begin_reception();saved=self.action('save',self.args());self.assertEqual(saved.status_code,200,saved.text);self.doc.update(saved.json())
        doc=self.root['ydental.clinical.document'].browse(self.doc['document_id'])
        return {'execution_id':doc.ydental_current_execution_id.id,'lease_id':self.lease['lease_id'],'lease_token':self.lease['token'],
            'document_id':doc.id,'document_version':self.doc['version']}

    def dose(self,args):
        return args|{'catalog_id':self.catalogs[0].id,'quantity':1,'source':key(),'reason':'Synthetic real HTTP project',
            'materials':[{'lot_id':self.lots['material'],'quantity':1,'uom_id':self.uom.id,'kind':'treatment'}],
            'teeth':[],'already_performed':False,'policy':'demo_confirmation'}

    def test_http_real_project_receipt_fee_stock_and_workbench(self):
        receive(self);price(self);args=self.medical();dose=self.dose(args);request=key()
        r=self.t_action('execute',dose,request);self.assertEqual(r.status_code,200,r.text);result=r.json();self.assertEqual(result['amount'],600);self.assertEqual(len(result['move_ids']),1)
        same=self.t_action('execute',dose,request);self.assertEqual(same.status_code,200);self.assertEqual(same.json()['event_id'],result['event_id'])
        page=self.url_open('/ydental/treatment');self.assertEqual(page.status_code,200,page.text);self.assertIn('data-event="'+str(result['event_id'])+'"',page.text)

    def test_http_rpc_attachment_export_and_readonly_boundaries(self):
        receive(self);price(self);args=self.medical();r=self.t_action('execute',self.dose(args));self.assertEqual(r.status_code,200,r.text);event=r.json()['event_id']
        self.assertIn('error',self.rpc('ydental.treatment.service','_operate',['execute',{},key()]))
        self.assertIn('error',self.rpc('ydental.treatment.event','write',[[event],{'ydental_quantity':99}],{'ydental_treatment_mutation':True}))
        self.assertIn('error',self.rpc('ydental.treatment.event','export_data',[[event],['ydental_quantity']]))
        self.assertIn('error',self.rpc('ir.attachment','create',[{'name':'blocked','res_model':'ydental.treatment.event','res_id':event,'datas':'YQ=='}]))
        self.select('reader');self.assertEqual(self.url_open('/ydental/treatment').status_code,200);self.assertEqual(self.t_action('execute',self.dose(args)).status_code,403)
        self.select('none');self.assertEqual(self.url_open('/ydental/treatment').status_code,403)

    def test_http_csrf_unknown_arguments_oldtab_and_no_price(self):
        args=self.medical();self.assertEqual(self.t_action('execute',self.dose(args)).status_code,409)
        self.assertEqual(self.t_action('execute',self.dose(args)|{'unit_price':0}).status_code,409)
        self.assertEqual(self.t_action('invented',{}).status_code,409)
        r=self.url_open('/ydental/treatment/action',data={'operation':'execute','revision':self.revision,'connection':self.connection,'payload':'{}','key':key()});self.assertEqual(r.status_code,400)
        self.connection=key()+key();self.assertEqual(self.t_action('execute',self.dose(args)).status_code,403)
