from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase, tagged

from .common import setup, opened, save_args, handover_args, bind, key, queue_bind, serving


@tagged('post_install', '-at_install')
class TestClinicalDocument(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        cls.admin._grant(cls.users['reader'].id, cls.stores[0].id, {'medical': 'read'})

    def counts(self):
        return {m: self.root[m].search_count([]) for m in ('stock.move', 'stock.quant', 'ydental.inventory.event', 'ydental.intake.snapshot', 'ydental.supply.event')}

    def test_three_real_saves_cas_and_economic_invariance(self):
        s,q,l,e,d = opened(self); before=self.counts()
        for i in range(3):
            a=save_args(d, 'Synthetic version '+str(i)); r=s._operate('save',a); d.update(r)
        self.assertEqual(d['version'],3); self.assertEqual(before,self.counts())
        self.assertEqual(s._operate('save',a)['version'],3)
        with self.assertRaises(UserError): s._operate('save',a | {'key':key()})
        self.assertEqual(s._model('version').search_count([('ydental_document_id','=',d['document_id'])]),3)

    def test_independent_locks_and_old_connection(self):
        s,q,l,e,d=opened(self)
        with self.assertRaises(UserError): s._operate('acquire',{'document_id':d['document_id'],'lease_id':l['lease_id'],'lease_token':l['token']})
        other=q._bind_connection(key()+key()).env[s._name]
        with self.assertRaises(AccessError): other._operate('save',save_args(d))
        s._operate('release',{'document_id':d['document_id'],'editor_token':d['editor_token']})
        new=s._operate('acquire',{'document_id':d['document_id'],'lease_id':l['lease_id'],'lease_token':l['token']})
        with self.assertRaises(AccessError): s._operate('save',save_args(d))
        self.assertNotEqual(new['editor_token'],d['editor_token'])

    def test_expiry_and_revocation_reject_cached_editor(self):
        s,q,l,e,d=opened(self)
        doc=s._model().browse(d['document_id']); doc._save({'ydental_editor_expires':q._now()-timedelta(seconds=1)})
        with self.assertRaises(AccessError): s._operate('save',save_args(d))
        doc._save({'ydental_editor_expires':q._now()+timedelta(seconds=20)})
        self.admin._grant(self.users['doctor'].id,self.stores[0].id,{'medical':'read'})
        with self.assertRaises(AccessError): s._operate('save',save_args(d))

    def test_fdi_permanent_primary_and_anterior_surfaces(self):
        s,q,l,e,d=opened(self)
        for tooth in (11,18,21,28,31,38,41,48,51,55,61,65,71,75,81,85):
            a=save_args(d); a['content']['teeth']=[{'tooth':tooth,'state':'present','surfaces':['M','I' if tooth%10<=3 else 'O','L']}]
            d.update(s._operate('save',a))
        for tooth in (10,19,49,50,56,86,99,True,'11'):
            a=save_args(d);a['content']['teeth']=[{'tooth':tooth,'state':'present','surfaces':[]}]
            with self.assertRaises(ValidationError):s._operate('save',a)

    def test_unknown_missing_not_applicable_and_invalid_surfaces(self):
        s,q,l,e,d=opened(self)
        for tooth,state,surfaces in [(11,'unknown',[]),(18,'missing',[]),(0,'not_applicable',[])]:
            a=save_args(d);a['content']['teeth']=[{'tooth':tooth,'state':state,'surfaces':surfaces}];d.update(s._operate('save',a))
        for row in [(11,'present',['O']),(18,'present',['I']),(18,'missing',['M']),(0,'present',[]),(11,'not_applicable',[]),(11,'normal',[]),(11,'present',['M','M'])]:
            a=save_args(d);a['content']['teeth']=[dict(zip(('tooth','state','surfaces'),row))]
            with self.assertRaises(ValidationError):s._operate('save',a)

    def test_confirmation_correction_preserves_authors_and_economics(self):
        s,q,l,e,d=opened(self); before=self.counts()
        a=save_args(d);d.update(s._operate('confirm',a)); old=s._model('version').search([('ydental_document_id','=',d['document_id'])])
        with self.assertRaises(UserError):s._operate('save',save_args(d))
        with self.assertRaises((ValidationError,UserError)):s._operate('correct',save_args(d)|{'reason':''})
        r=s._operate('correct',save_args(d,'Correction synthetic text')|{'reason':'Correct transcription only'})
        self.assertEqual(r['version'],2);self.assertEqual(old.ydental_content['chief_complaint'],'Synthetic complaint')
        self.assertEqual(old.ydental_author_id,self.users['doctor']);self.assertEqual(before,self.counts())
        with self.assertRaises(AccessError):old.write({'ydental_author_id':self.second.id})
        with self.assertRaises(AccessError):old.unlink()

    def test_handover_real_save_pending_and_unique_continuation(self):
        s,q,l,e,d=opened(self); before=self.counts()
        r=s._operate('handover',handover_args(d,l)); doc=s._model().browse(d['document_id'])
        self.assertEqual(doc.state,'pending');self.assertFalse(doc.ydental_editor_id);self.assertEqual(e.state,'handover')
        self.assertEqual(doc.ydental_version,1);self.assertEqual(doc.ydental_content['chief_complaint'],'Synthetic complaint')
        retry=q._operate('handover',{'lease_id':l['lease_id'],'token':l['token'],'execution_id':e.id})
        self.assertEqual(retry['continuation_task_id'],r['continuation_task_id']);self.assertEqual(before,self.counts())
        self.assertFalse(q._busy(q._model('lease').browse(l['lease_id'])))

    def test_handover_save_and_continuation_failure_roll_back(self):
        s,q,l,e,d=opened(self); a=handover_args(d,l)
        with patch.object(type(q),'_continuation',side_effect=UserError('Injected continuation failure')):
            with self.assertRaises(UserError):s._operate('handover',a)
        doc=s._model().browse(d['document_id']); self.assertEqual(doc.ydental_version,0);self.assertTrue(doc.ydental_editor_id);self.assertEqual(e.state,'serving')
        with self.assertRaises(UserError):q._operate('handover',{'lease_id':l['lease_id'],'token':l['token'],'execution_id':e.id})
        self.assertEqual(s._operate('handover',a)['state'],'handover')

    def test_d1_pending_d2_independent_and_responsibility_transfer(self):
        s,q,l,e,d=opened(self);r=s._operate('handover',handover_args(d,l))
        task=self.root['ydental.intake.task'].browse(r['continuation_task_id']);self.front._operate('report',{'task_id':task.id,'version':task.ydental_version},key())
        q2,l2,e2=serving(self,self.second,self.other_station,task)
        s2=q2.env[s._name];d2=s2._operate('open',{'execution_id':e2.id,'lease_id':l2['lease_id'],'lease_token':l2['token']})
        d1=s._operate('acquire',{'document_id':d['document_id']})
        self.assertNotEqual(d1['document_id'],d2['document_id']);self.assertEqual(q._unresolved_execution(e.ydental_patient_id.id),e2)
        with self.assertRaises(UserError):s._operate('transfer',{'document_id':d1['document_id'],'expected_version':d1['version'],'user_id':self.second.id,'reason':'Transfer responsibility'})
        s._operate('release',{'document_id':d1['document_id'],'editor_token':d1['editor_token']})
        s._operate('transfer',{'document_id':d1['document_id'],'expected_version':d1['version'],'user_id':self.second.id,'reason':'Transfer responsibility'})
        received=s2._operate('acquire',{'document_id':d1['document_id']});s2._operate('confirm',save_args(received))
        self.assertEqual(e2.state,'serving');self.assertEqual(s2._model().browse(d2['document_id']).state,'draft')
        self.assertEqual(s2._model().browse(d1['document_id']).ydental_author_id,self.users['doctor'])

    def test_native_rpc_read_export_and_attachments(self):
        s,q,l,e,d=opened(self);s._operate('save',save_args(d))
        reader=bind(self,self.users['reader']).env['ydental.clinical.document'].browse(d['document_id'])
        self.assertTrue(reader.read(['ydental_content']))
        with self.assertRaises(AccessError):reader.read(['ydental_editor_hash'])
        with self.assertRaises(AccessError):reader.export_data(['ydental_content'])
        with self.assertRaises(AccessError):reader.with_context(ydental_clinical_mutation=True).write({'state':'confirmed'})
        with self.assertRaises(AccessError):reader.env['ir.attachment'].create({'name':'forged','res_model':'ydental.clinical.document','res_id':reader.id,'datas':b'YQ=='})
        self.admin._grant(self.users['reader'].id,self.stores[0].id,{'export':'write'})
        self.assertTrue(reader.export_data(['ydental_content']))
        self.admin._grant(self.users['reader'].id,self.stores[0].id,{'medical':'none'})
        with self.assertRaises(AccessError):reader.read(['ydental_content'])

    def test_cross_store_write_and_old_session_revision(self):
        s,q,l,e,d=opened(self)
        other=bind(self,self.users['doctor'],self.stores[1]).env[s._name]
        with self.assertRaises(AccessError):other._read(d['document_id'])
        # Actual relation is required before purpose-scoped shared history.
        session=s.env['ydental.access.service']._scope();session.sudo().write({'ydental_revision':session.ydental_revision+1})
        with self.assertRaises(UserError):s._operate('save',save_args(d))

    def test_external_reserve_remains_fail_closed(self):
        s,q,l,e,d=opened(self)
        target=self.front._new('task',self.stores[0],dict(self.front._identity(e.ydental_patient_id),name='Synthetic untrusted external',ydental_mapping_id=self.mappings[0][2].id,ydental_source_kind='derived'))
        with self.assertRaises(AccessError):q._operate('reserve',{'lease_id':l['lease_id'],'token':l['token'],'execution_id':e.id,'target_task_id':target.id})
        self.assertEqual(e.state,'serving')

    def test_onsite_verify_uses_persisted_draft_no_false_author(self):
        s,q,l,e,d=opened(self);s._operate('save',save_args(d))
        q._model('lease').browse(l['lease_id'])._save({'ydental_expires_at':q._now()-timedelta(seconds=1)})
        q._timeout();self.assertEqual(e.state,'verify')
        newq=queue_bind(self,self.second)
        r=newq._operate('takeover_verify',{'execution_id':e.id,'confirmed':True,'reason':'Actual on-site synthetic takeover'})
        self.assertEqual(e.state,'interrupted');doc=s._model().browse(d['document_id']);self.assertEqual(doc.state,'pending');self.assertFalse(doc.ydental_editor_id)
        self.assertEqual(doc.ydental_author_id,self.users['doctor']);self.assertNotEqual(r['execution_id'],e.id)

    def test_hold_restore_keeps_same_real_document_then_handover_releases_it(self):
        s,q,l,e,d=opened(self);d.update(s._operate('save',save_args(d)))
        target=self.front._new('task',self.stores[0],dict(self.front._identity(e.ydental_patient_id),name='Explicit synthetic external prerequisite only',ydental_mapping_id=self.mappings[0][2].id,ydental_source_kind='derived'))
        # S09 is not installed. Only this guarded test supplies the external
        # prerequisite; document persistence, S06 reserve/restore are real.
        with patch.object(type(q),'_external_target_authorized',return_value=True):
            hold=q._operate('reserve',{'lease_id':l['lease_id'],'token':l['token'],'execution_id':e.id,'target_task_id':target.id})
        self.assertEqual(e.state,'reserved')
        restored=q._operate('restore',{'lease_id':l['lease_id'],'token':l['token'],'hold_id':hold['hold_id'],'confirmed':True})
        doc=s._model().browse(d['document_id']);self.assertEqual(doc.ydental_execution_id,e)
        self.assertEqual(doc.ydental_current_execution_id.id,restored['execution_id'])
        d.update(s._operate('save',save_args(d,'Same document after actual return')))
        done=s._operate('handover',handover_args(d,l));self.assertEqual(done['state'],'handover')
        self.assertFalse(doc.ydental_editor_id);self.assertEqual(doc.state,'pending')

    def test_invalid_content_save_failure_does_not_hand_back(self):
        s,q,l,e,d=opened(self);a=handover_args(d,l);a['content']['teeth']=[{'tooth':99,'state':'present','surfaces':[]}]
        with self.assertRaises(ValidationError):s._operate('handover',a)
        doc=s._model().browse(d['document_id']);self.assertEqual(doc.ydental_version,0);self.assertEqual(e.state,'serving');self.assertTrue(doc.ydental_editor_id)

    def test_current_capability_revocation_rejects_existing_editor(self):
        s,q,l,e,d=opened(self)
        self.users['doctor'].write({'ydental_capability_ids':[fields.Command.clear()]})
        with self.assertRaises(AccessError):s._operate('save',save_args(d))

    def test_native_confirmed_versions_and_distinct_clinical_audit_events(self):
        s,q,l,e,d=opened(self);d.update(s._operate('save',save_args(d)));d.update(s._operate('confirm',save_args(d)))
        s._read(d['document_id']);d.update(s._operate('correct',save_args(d)|{'reason':'Synthetic corrected text'}))
        events=self.root['ydental.access.audit'].search([('ydental_target_model','=','ydental.clinical.document'),('ydental_target_id','=',d['document_id'])]).mapped('ydental_event')
        self.assertTrue({'clinical.view','clinical.save','clinical.confirm','clinical.correct'}<=set(events))

    def test_shared_history_requires_purpose_current_relation_and_live_read(self):
        s,q,l,e,d=opened(self);s._operate('save',save_args(d))
        self.admin._grant(self.users['reader'].id,self.stores[1].id,{'medical':'read','export':'write'})
        other=bind(self,self.users['reader'],self.stores[1]).env[s._name]
        with self.assertRaises(AccessError):other._read(d['document_id'])
        with self.assertRaises(AccessError):other._read(d['document_id'],'history_review')
        front=bind(self,self.users['frontdesk'],self.stores[1])
        front._operate('arrive',{'patient_id':e.ydental_patient_id.id},key())
        self.assertEqual(other._read(d['document_id'],'history_review')['document_id'],d['document_id'])
        scoped=other.env['ydental.access.service']._patient_care(e.ydental_patient_id.id,'history_review')
        source=scoped.env['ydental.clinical.document'].browse(d['document_id'])
        self.assertTrue(source.export_data(['ydental_content']))
        with self.assertRaises(AccessError):other._operate('acquire',{'document_id':d['document_id']})
        self.admin._grant(self.users['reader'].id,self.stores[1].id,{'medical':'none'})
        with self.assertRaises(AccessError):source.read(['ydental_content'])

    def test_upstream_real_inventory_receive_issue_and_no_clinical_source_bypass(self):
        # Explicit native multi-location prerequisite in this rollback-only test.
        # Avoid res.config.settings' unrelated global pricelist archival when
        # real committed S05 price sources already exist during upgrade tests.
        self.root.ref('stock.group_stock_user').write({'implied_ids': [fields.Command.link(self.root.ref('stock.group_stock_multi_locations').id)]})
        self.admin._grant(self.users['manager'].id,self.stores[0].id,{'warehouse':'write'})
        stock=self.group.env['ydental.inventory.service']
        stock._operate('setup',{'code':str(self.stores[0].id)[-5:]},key())
        product=stock._operate('product',{'code':'S08A-'+key(),'name':'Synthetic regression material','kind':'material','stock_uom_id':self.uom.id,'issue_uom_id':self.uom.id,'step':1,'specification':'Synthetic only'},key())
        lot=stock._operate('lot',{'product_id':product['id'],'name':'S08A-'+key(),'expiration':fields.Datetime.to_string(fields.Datetime.now()+timedelta(days=30))},key())['id']
        stock._operate('receive',{'lot_id':lot,'quantity':10,'uom_id':self.uom.id,'source_key':key(),'reason':'S08-A upstream real receipt regression'},key())
        stock._operate('issue',{'lot_id':lot,'quantity':2,'uom_id':self.uom.id,'source_key':key(),'reason':'S08-A upstream real issue regression'},key())
        s,q,l,e,d=opened(self);before=self.counts();d.update(s._operate('save',save_args(d)));s._operate('confirm',save_args(d))
        self.assertEqual(before,self.counts())
        with self.assertRaises(AccessError):stock._source_action({'kind':'treatment','lot_id':lot,'already_performed':True})

    def test_no_admin_force_or_json_document_lock(self):
        s,q,l,e,d=opened(self)
        with self.assertRaises(AccessError):q._document_lock({'document_id':d['document_id']},'acquire')
        with self.assertRaises(ValidationError):s._operate('force_release',{'document_id':d['document_id']})
        with self.assertRaises(AccessError):s._model().with_context(ydental_clinical_mutation=True).create({'name':'Forged'})
