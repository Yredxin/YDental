import json
import re
from unittest.mock import patch

from odoo.tests import HttpCase, tagged

from .common import setup, key, accepted


@tagged('post_install', '-at_install')
class TestClinicalHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass();setup(cls)
        cls.admin._grant(cls.users['reader'].id,cls.stores[0].id,{'medical':'read'})

    def select(self,role='doctor'):
        self.authenticate(self.users[role].login,'s05-test-password')
        page=self.url_open('/ydental/access');self.csrf=re.search(r'name="csrf_token" value="([^"]+)"',page.text).group(1)
        revision=int(re.search(r'name="revision" value="([0-9]+)"',page.text).group(1))
        r=self.url_open('/ydental/access/action',data={'csrf_token':self.csrf,'revision':revision,'operation':'switch','payload':json.dumps({'store_id':self.stores[0].id}),'output':'json'})
        self.assertEqual(r.status_code,200,r.text);self.revision=r.json()['revision'];self.connection=key()+key()

    def action(self,op,payload,queue=False):
        return self.url_open('/ydental/queue/action' if queue else '/ydental/clinical/action',data={'csrf_token':self.csrf,'revision':self.revision,'connection':self.connection,'operation':op,'payload':json.dumps(payload)})

    def rpc(self,model,method,args,context=None):
        return self.url_open('/web/dataset/call_kw/'+model+'/'+method,data=json.dumps({'jsonrpc':'2.0','id':1,'method':'call','params':{'model':model,'method':method,'args':args,'kwargs':{'context':context or {}}}}),headers={'Content-Type':'application/json'}).json()

    def begin_reception(self):
        task=accepted(self);self.select()
        r=self.action('enter',{'station_id':self.stations[0][0].id},True);self.assertEqual(r.status_code,200,r.text);self.lease=r.json()
        a={'lease_id':self.lease['lease_id'],'token':self.lease['token']}
        call=self.action('call',a,True);self.assertEqual(call.status_code,200,call.text)
        start=self.action('start',a|{'entry_id':call.json()['entry_id']},True);self.assertEqual(start.status_code,200,start.text)
        r=self.action('open',{'execution_id':start.json()['execution_id'],'lease_id':self.lease['lease_id'],'lease_token':self.lease['token']});self.assertEqual(r.status_code,200,r.text)
        self.doc=r.json();return self.doc

    def args(self):
        d=self.doc
        return {'document_id':d['document_id'],'editor_token':d['editor_token'],'expected_version':d['version'],'key':key(),'content':dict(d['content'],chief_complaint='Synthetic HTTP content')}

    def test_real_workbench_open_autosave_cas_handover(self):
        self.begin_reception()
        for i in range(3):
            r=self.action('save',self.args());self.assertEqual(r.status_code,200,r.text);self.doc.update(r.json())
        page=self.url_open('/ydental/clinical?document_id='+str(self.doc['document_id']));self.assertEqual(page.status_code,200,page.text);self.assertIn('data-tooth="85"',page.text)
        stale=self.args();stale['expected_version']=0;self.assertEqual(self.action('save',stale).status_code,409)
        a=self.args()|{'lease_id':self.lease['lease_id'],'lease_token':self.lease['token']}
        r=self.action('handover',a);self.assertEqual(r.status_code,200,r.text)
        page=self.url_open('/ydental/clinical?document_id='+str(self.doc['document_id']));self.assertIn('pending',page.text)

    def test_connection_expired_http_result_and_telemetry(self):
        self.select()
        service = self.env['ydental.clinical.service']
        with patch.object(type(service), '_operate', return_value={
                'result': 'connection_expired', 'verification_required': True,
        }), patch('odoo.addons.ydental_clinical.controllers.clinical.emit_event') as emit:
            response = self.action('complete', {})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['result'], 'connection_expired')
        returned = [call for call in emit.call_args_list if call.args[0] == 'business.returned']
        self.assertEqual(len(returned), 1)
        self.assertEqual(returned[0].kwargs['outcome'], 'connection_expired')

    def test_rpc_private_and_mutation_forgery(self):
        self.begin_reception()
        self.assertIn('error',self.rpc('ydental.clinical.service','_operate',['save',self.args()]))
        self.assertIn('error',self.rpc('ydental.clinical.document','write',[[self.doc['document_id']],{'state':'confirmed'}],{'ydental_clinical_mutation':True}))
        self.assertIn('error',self.rpc('ydental.clinical.version','create',[{'ydental_number':999}]))
        self.assertIn('error',self.rpc('ydental.clinical.document','read',[[self.doc['document_id']],['ydental_editor_hash']]))

    def test_readonly_and_no_access_denials(self):
        self.select('reader');self.assertEqual(self.url_open('/ydental/clinical').status_code,200)
        self.assertEqual(self.action('open',{'execution_id':1,'lease_id':1,'lease_token':'invalid'}).status_code,403)
        self.select('none');self.assertEqual(self.url_open('/ydental/clinical').status_code,403)
        self.assertIn('error',self.rpc('ydental.clinical.document','search_read',[[]]))

    def test_csrf_unknown_and_fdi_backend(self):
        self.begin_reception();a=self.args();a['content']['teeth']=[{'tooth':99,'state':'present','surfaces':['M']}]
        self.assertEqual(self.action('save',a).status_code,409)
        self.assertEqual(self.action('invented',{}).status_code,409)
        r=self.url_open('/ydental/clinical/action',data={'operation':'save','revision':self.revision,'connection':self.connection,'payload':'{}'})
        self.assertEqual(r.status_code,400)

    def test_old_connection_and_shared_token_rejected(self):
        self.begin_reception();a=self.args();self.connection=key()+key();self.assertEqual(self.action('save',a).status_code,403)

    def test_attachments_and_export_cannot_bypass_scope(self):
        self.begin_reception()
        self.assertIn('error',self.rpc('ir.attachment','create',[{'name':'Forgery','res_model':'ydental.clinical.document','res_id':self.doc['document_id'],'datas':'YQ=='}]))
        self.assertIn('error',self.rpc('ydental.clinical.document','export_data',[[self.doc['document_id']],['ydental_content']]))

    def test_stored_clinical_text_is_escaped_in_workbench_and_history(self):
        self.begin_reception();a=self.args();a['content']['chief_complaint']='<script>window.ydentalInjected=true</script>'
        self.assertEqual(self.action('save',a).status_code,200)
        page=self.url_open('/ydental/clinical?document_id='+str(self.doc['document_id']))
        self.assertEqual(page.status_code,200);self.assertIn('&lt;script&gt;',page.text)
        self.assertNotIn('<script>window.ydentalInjected',page.text)
        self.doc['version']=1
        confirmed=self.action('confirm',self.args());self.assertEqual(confirmed.status_code,200)
        self.doc['version']=2
        denied=self.action('confirm',self.args());self.assertEqual(denied.status_code,409)
        self.assertIn('correction_required',denied.text)
