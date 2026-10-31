import json

from lxml import html

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

    def test_current_medical_navigation_preserves_tab_and_checks_live_grant(self):
        self.select()
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertNotIn('Open the current clinical document', page.text)

        self.begin_reception()
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200, page.text)
        document = html.fromstring(page.text)
        links = document.xpath('//section[@id="patient-return-actions"]//a')
        self.assertEqual([link.get('href') for link in links], ['/ydental/clinical', '/ydental/treatment'])
        self.assertTrue(all(link.get('target') is None for link in links))

        clinical = self.url_open('/ydental/clinical')
        self.assertEqual(clinical.status_code, 200, clinical.text)
        treatment_link = html.fromstring(clinical.text).xpath('//nav/a[@href="/ydental/treatment"]')
        self.assertEqual(len(treatment_link), 1)
        self.assertIsNone(treatment_link[0].get('target'))
        treatment = self.url_open('/ydental/treatment')
        self.assertEqual(treatment.status_code, 200, treatment.text)
        clinical_link = html.fromstring(treatment.text).xpath('//nav/a[@href="/ydental/clinical"]')
        self.assertEqual(len(clinical_link), 1)
        self.assertIsNone(clinical_link[0].get('target'))

        # A remaining unrelated write grant must not expose a stale medical link.
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'exam': 'write', 'medical': 'none'})
        self.env.flush_all()
        page = self.url_open('/ydental/queue')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertFalse(html.fromstring(page.text).xpath('//section[@id="patient-return-actions"]//a[@href="/ydental/clinical"]'))

    def test_http_rpc_attachment_export_and_readonly_boundaries(self):
        receive(self);price(self);args=self.medical();r=self.t_action('execute',self.dose(args));self.assertEqual(r.status_code,200,r.text);event=r.json()['event_id']
        self.assertIn('error',self.rpc('ydental.treatment.service','_operate',['execute',{},key()]))
        self.assertIn('error',self.rpc('ydental.treatment.event','write',[[event],{'ydental_quantity':99}],{'ydental_treatment_mutation':True}))
        self.assertIn('error',self.rpc('ydental.treatment.event','export_data',[[event],['ydental_quantity']]))
        self.assertIn('error',self.rpc('ir.attachment','create',[{'name':'blocked','res_model':'ydental.treatment.event','res_id':event,'datas':'YQ=='}]))
        self.select('reader');self.assertEqual(self.url_open('/ydental/treatment').status_code,200);self.assertEqual(self.t_action('execute',self.dose(args)).status_code,403)
        self.select('none');self.assertEqual(self.url_open('/ydental/treatment').status_code,403)

    def test_missing_workstation_settings_blocks_workbench_with_explanation(self):
        self.select('doctor')
        self.env['ir.config_parameter'].sudo().set_str('ydental_queue.heartbeat_seconds', '')
        self.env.flush_all()
        page = self.url_open('/ydental/treatment')
        self.assertEqual(page.status_code, 422)
        self.assertIn('工位心跳或超时设置缺失或无效', page.text)
        self.assertIn('/ydental/queue', page.text)
        self.assertNotIn('workbench.js', page.text)
        self.assertNotIn('data-operation="execute"', page.text)
        self.select('none')
        self.assertEqual(self.url_open('/ydental/treatment').status_code, 403)

    def test_http_csrf_unknown_arguments_oldtab_and_no_price(self):
        args=self.medical();self.assertEqual(self.t_action('execute',self.dose(args)).status_code,409)
        self.assertEqual(self.t_action('execute',self.dose(args)|{'unit_price':0}).status_code,409)
        self.assertEqual(self.t_action('invented',{}).status_code,409)
        r=self.url_open('/ydental/treatment/action',data={'operation':'execute','revision':self.revision,'connection':self.connection,'payload':'{}','key':key()});self.assertEqual(r.status_code,400)
        self.connection=key()+key();self.assertEqual(self.t_action('execute',self.dose(args)).status_code,403)

    def test_http_multi_role_actual_pharmacy_execution_selects_pharmacy_workbench(self):
        receive(self,kind='medicine');price(self,catalog=self.drug_catalog,amount=10)
        self.admin._grant(self.users['doctor'].id,self.stores[0].id,{'pharmacy':'write'})
        args=self.medical()
        line={'mapping_id':self.drug_mapping.id,'quantity':6,'uom_id':self.uom.id,
            'product_id':self.products['medicine'],'specification':'Synthetic specification',
            'usage':'Synthetic usage','frequency':'Synthetic frequency','course':'Synthetic course'}
        draft=self.t_action('order',args|{'kind':'prescription','purpose':'Synthetic dual-role dispensing','lines':[line]})
        self.assertEqual(draft.status_code,200,draft.text)
        issued=self.t_action('issue',args|{'order_id':draft.json()['order_id'],'version':draft.json()['version']})
        self.assertEqual(issued.status_code,200,issued.text);order=issued.json()
        hand=self.action('handover',self.args()|{'lease_id':self.lease['lease_id'],'lease_token':self.lease['token']})
        self.assertEqual(hand.status_code,200,hand.text)
        exited=self.action('exit',{'lease_id':self.lease['lease_id'],'token':self.lease['token']},True)
        self.assertEqual(exited.status_code,200,exited.text)
        task=self.root['ydental.intake.task'].browse(order['task_ids'][0])
        self.front._operate('arrive',{'patient_id':task.ydental_patient_id.id},key())
        self.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
        entered=self.action('enter',{'station_id':self.pharmacy_station.id},True)
        self.assertEqual(entered.status_code,200,entered.text);lease=entered.json()
        held={'lease_id':lease['lease_id'],'token':lease['token']}
        call=self.action('call',held,True);self.assertEqual(call.status_code,200,call.text)
        started=self.action('start',held|{'entry_id':call.json()['entry_id']},True)
        self.assertEqual(started.status_code,200,started.text)
        queue_page = self.url_open('/ydental/queue')
        self.assertEqual(queue_page.status_code, 200, queue_page.text)
        current_links = html.fromstring(queue_page.text).xpath('//section[@id="patient-return-actions"]//a')
        self.assertEqual([link.get('href') for link in current_links], ['/ydental/treatment'])
        self.assertIsNone(current_links[0].get('target'))
        page=self.url_open('/ydental/treatment');self.assertEqual(page.status_code,200,page.text)
        self.assertIn('data-role="pharmacy"',page.text)
        self.assertIn('data-execution="'+str(started.json()['execution_id'])+'"',page.text)
        dispense=self.t_action('dispense',{'execution_id':started.json()['execution_id'],'lease_id':lease['lease_id'],
            'lease_token':lease['token'],'order_id':order['order_id'],'order_version':order['version'],
            'line_id':order['line_ids'][0],'lot_id':self.lots['medicine'],'quantity':4,
            'source':key(),'reason':'Synthetic actual four','already_performed':False,'policy':'demo_confirmation'})
        self.assertEqual(dispense.status_code,200,dispense.text)

    def test_pharmacy_current_patient_order_survives_more_than_100_other_orders(self):
        receive(self, kind='medicine')
        price(self, catalog=self.drug_catalog, amount=10)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'pharmacy': 'write'})
        self.select()
        without_execution = self.url_open('/ydental/treatment')
        self.assertEqual(without_execution.status_code, 200, without_execution.text)
        workbench = html.fromstring(without_execution.content).xpath('//main[contains(concat(" ", normalize-space(@class), " "), " o_ydental_treatment ")]')[0]
        self.assertIn(workbench.get('data-execution'), (None, '0'))
        line = {'mapping_id': self.drug_mapping.id, 'quantity': 1, 'uom_id': self.uom.id,
                'product_id': self.products['medicine'], 'specification': 'Synthetic specification',
                'usage': 'Synthetic usage', 'frequency': 'Synthetic frequency', 'course': 'Synthetic course'}

        def issue(args):
            draft = self.t_action('order', args | {'kind': 'prescription', 'purpose': 'Synthetic scoped list', 'lines': [line]})
            self.assertEqual(draft.status_code, 200, draft.text)
            issued = self.t_action('issue', args | {'order_id': draft.json()['order_id'], 'version': draft.json()['version']})
            self.assertEqual(issued.status_code, 200, issued.text)
            return issued.json()

        def handover():
            result = self.action('handover', self.args() | {'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token']})
            self.assertEqual(result.status_code, 200, result.text)
            result = self.action('exit', {'lease_id': self.lease['lease_id'], 'token': self.lease['token']}, True)
            self.assertEqual(result.status_code, 200, result.text)

        order = issue(self.medical())
        handover()
        other_args = self.medical()
        newer = [issue(other_args) for _ in range(101)]
        handover()
        task = self.root['ydental.intake.task'].browse(order['task_ids'][0])
        self.front._operate('arrive', {'patient_id': task.ydental_patient_id.id}, key())
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        entered = self.action('enter', {'station_id': self.pharmacy_station.id}, True)
        self.assertEqual(entered.status_code, 200, entered.text)
        lease = entered.json()
        held = {'lease_id': lease['lease_id'], 'token': lease['token']}
        call = self.action('call', held, True)
        self.assertEqual(call.status_code, 200, call.text)
        started = self.action('start', held | {'entry_id': call.json()['entry_id']}, True)
        self.assertEqual(started.status_code, 200, started.text)
        page = self.url_open('/ydental/treatment')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('data-order="%s"' % order['order_id'], page.text)
        self.assertNotIn('data-order="%s"' % newer[-1]['order_id'], page.text)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'pharmacy': 'none'})
        self.assertEqual(self.url_open('/ydental/treatment').status_code, 403)

    def test_pharmacy_without_current_execution_cannot_view_prescriptions(self):
        args = self.medical()
        line = {'mapping_id': self.drug_mapping.id, 'quantity': 1, 'uom_id': self.uom.id,
                'product_id': self.products['medicine'], 'specification': 'Synthetic specification',
                'usage': 'Synthetic usage', 'frequency': 'Synthetic frequency', 'course': 'Synthetic course'}
        draft = self.t_action('order', args | {'kind': 'prescription', 'purpose': 'Synthetic idle check', 'lines': [line]})
        self.assertEqual(draft.status_code, 200, draft.text)
        issued = self.t_action('issue', args | {'order_id': draft.json()['order_id'], 'version': draft.json()['version']})
        self.assertEqual(issued.status_code, 200, issued.text)
        handed = self.action('handover', self.args() | {'lease_id': self.lease['lease_id'], 'lease_token': self.lease['token']})
        self.assertEqual(handed.status_code, 200, handed.text)
        exited = self.action('exit', {'lease_id': self.lease['lease_id'], 'token': self.lease['token']}, True)
        self.assertEqual(exited.status_code, 200, exited.text)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'pharmacy': 'write'})
        self.select()
        page = self.url_open('/ydental/treatment')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('data-role="pharmacy"', page.text)
        self.assertTrue(any(message in page.text for message in (
            'No current pharmacy encounter', '当前没有可办理的药房接诊',
        )))
        self.assertNotIn('data-order="%s"' % issued.json()['order_id'], page.text)
        self.assertNotIn('data-event=', page.text)
        self.admin._grant(self.users['doctor'].id, self.stores[1].id, {'medical': 'none', 'pharmacy': 'write'})
        switch = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': self.revision, 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[1].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200, switch.text)
        self.revision = switch.json()['revision']
        page = self.url_open('/ydental/treatment')
        self.assertEqual(page.status_code, 200, page.text)
        self.assertNotIn('data-order="%s"' % issued.json()['order_id'], page.text)
        self.admin._grant(self.users['doctor'].id, self.stores[1].id, {'pharmacy': 'none'})
        self.assertEqual(self.url_open('/ydental/treatment').status_code, 403)

    def test_http_rework_blank_rx_draft_issue_reject_then_complete(self):
        args=self.medical()
        line={'mapping_id':self.drug_mapping.id,'quantity':6,'uom_id':self.uom.id,'product_id':self.products['medicine'],
            'specification':'','usage':'  ','frequency':'','course':''}
        draft=self.t_action('order',args|{'kind':'prescription','purpose':'Incomplete HTTP draft','lines':[line]})
        self.assertEqual(draft.status_code,200,draft.text)
        issue=self.t_action('issue',args|{'order_id':draft.json()['order_id'],'version':draft.json()['version']})
        self.assertEqual(issue.status_code,409,issue.text)
        self.assertEqual(self.root['ydental.treatment.order'].browse(draft.json()['order_id']).state,'draft')
        line.update(specification='Synthetic reviewed specification',usage='Explicit usage',frequency='Explicit frequency',course='Explicit course')
        edit=self.t_action('edit_order',args|{'order_id':draft.json()['order_id'],'version':draft.json()['version'],'purpose':'Completed HTTP draft','lines':[line]})
        self.assertEqual(edit.status_code,200,edit.text)
        issue=self.t_action('issue',args|{'order_id':edit.json()['order_id'],'version':edit.json()['version']})
        self.assertEqual(issue.status_code,200,issue.text);self.assertTrue(issue.json()['task_ids'])

    def test_http_rework_empty_chairside_and_price_publish_denied(self):
        price(self,catalog=self.drug_catalog,amount=10);args=self.medical()
        dose=self.dose(args)|{'catalog_id':self.drug_catalog.id,'materials':[]}
        response=self.t_action('execute',dose);self.assertEqual(response.status_code,409,response.text)
        self.assertFalse(self.root['ydental.treatment.event'].search_count([('ydental_execution_id','=',args['execution_id'])]))
        response=self.t_action('publish_medicine',{'catalog_id':self.drug_catalog.id,'product_id':self.products['medicine'],
            'uom_id':self.uom.id,'evidence':'Medical role has no price publication authority','policy':'demo_confirmation'})
        self.assertEqual(response.status_code,403,response.text)

    def test_http_rework_source_only_company_controlled_referral_and_target_rpc_denied(self):
        from datetime import timedelta
        from odoo import fields
        from .treatment_common import cross_legal_target
        store,mapping,slot=cross_legal_target(self);args=self.medical()
        self.assertNotIn(store.company_id,self.users['doctor'].company_ids)
        page=self.url_open('/ydental/treatment');self.assertIn('value="'+str(mapping.id)+'"',page.text)
        for payload in ({'mode':'timed','start':str(self.start),'end':str(self.end)},
                {'mode':'untimed','valid_until':str(fields.Datetime.now()+timedelta(days=1))}):
            response=self.t_action('refer',args|payload|{'mapping_id':mapping.id,'source':key(),'reason':'Trusted cross-legal HTTP source'})
            self.assertEqual(response.status_code,200,response.text)
        self.assertIn('error',self.rpc('ydental.intake.mapping','write',[[mapping.id],{'name':'Forbidden target write'}]))
        self.assertIn('error',self.rpc('ydental.intake.mapping','read',[[mapping.id],['name']]))
        self.assertEqual(self.url_open('/ydental/treatment').status_code,200)

    def test_http_rework_medicine_association_rpc_crud_export_attachment_denied(self):
        price(self,catalog=self.drug_catalog,amount=10);args=self.medical()
        link=self.root['ydental.treatment.medicine.link'].search([('ydental_store_id','=',self.stores[0].id)])
        self.assertTrue(link)
        self.assertIn('error',self.rpc('ydental.treatment.service','_publish_medicine',[self.products['medicine'],self.drug_catalog.id,self.uom.id,'Forged','demo_confirmation']))
        self.assertIn('error',self.rpc('ydental.treatment.medicine.link','create',[{'name':'forged'}],{'ydental_treatment_mutation':True}))
        self.assertIn('error',self.rpc('ydental.treatment.medicine.link','write',[[link.id],{'ydental_product_id':False}]))
        self.assertIn('error',self.rpc('ydental.treatment.medicine.link','unlink',[[link.id]]))
        self.assertIn('error',self.rpc('ydental.treatment.medicine.link','export_data',[[link.id],['ydental_evidence']]))
        self.assertIn('error',self.rpc('ir.attachment','create',[{'name':'blocked','res_model':'ydental.treatment.medicine.link','res_id':link.id,'datas':'YQ=='}]))
