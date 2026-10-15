"""Inject failures into the exact P0-02 pipeline and HTML validators, with no writes."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

import s10_p0_02_control as control
from s10_p0_02_browser import validate_action, validate_form, validate_response
from s10_p0_02_snapshot import (SOURCE, ALLOWED_VIEWS, snapshot)


def form(operation, record):
    return {'action':'/ydental/settlement/action','method':'post','visible':True,
        'valid':True,'output':'html','csrf':True,'key':True,'revision_match':True,
        'reason':True,'record':str(record),'operation':operation,'button_enabled':True}


def response(operation, record):
    field = 'refund_id' if operation=='refund_reject' else 'close_id'
    return {'method':'POST','path':'/ydental/settlement/action',
        'content_type':'application/x-www-form-urlencoded','post':{
            'operation':[operation],'output':['html'],field:[str(record)],
            'csrf_token':['OWN'],'revision':['CURRENT'],'key':['UNIQUE']},
        'status':303,'location_path':'/ydental/settlement','notice':True,
        'feedback':'操作已受理，请核对下方业务记录。'}


def fact_pair():
    refund={'id':14,'ydental_state':'requested','ydental_requester_id':5,
        'ydental_approver_id':None,'ydental_decision_reason':None,
        'ydental_native_payment_id':None,'ydental_credit_note_id':None}
    close={'id':9,'ydental_state':'confirmed','ydental_gross':'0.00',
        'ydental_refunded':'0.00','ydental_pending':'0.00','ydental_cycle':1,
        'ydental_unlocked_by_id':None,'ydental_unlock_reason':None}
    return {'refund':refund,'close':close,'audit':[]}


class FakeOps:
    def __init__(self, source, fault=None):
        self.source = deepcopy(source)
        self.fault = fault
        self.stages = []
        self.posts = []
        self.stopped = False
        self.cloned = None
        self.updated = None
        self.current = None

    def source_readonly(self):
        self.stages.append('source_readonly')
        result = deepcopy(self.source)
        if self.fault=='source_oid': result['oid']=0
        return result

    def check_source(self, before):
        self.stages.append('check_source')
        control.source_gate(before)

    def clone_compare(self, before):
        self.stages.append('clone_compare')
        self.cloned = deepcopy(before)
        self.cloned['database']=control.TARGET; self.cloned['oid']=2100999
        if self.fault=='clone_business':
            self.cloned['tables']['ydental_settlement_payment']['sha256']='DRIFT'
        control.equal_clone(before,self.cloned)
        return deepcopy(self.cloned)

    def upgrade_diff(self,before,cloned):
        self.stages.append('upgrade_diff')
        self.updated=deepcopy(cloned)
        token=self.updated['views']['ydental_settlement.ydental_settlement_tokens']
        token['arch']['en_US']+='\n<input name="output" value="html"/>'
        token['row']['arch_db']['en_US']=token['arch']['en_US']
        token['languages']['en_US']['has_output_html']=True
        token['languages']['en_US']['sha256']='NEW'
        token_id=str(token['row']['id'])
        self.updated['view_rows'][token_id]['arch_db']['en_US']=token['arch']['en_US']
        self.updated['modules']['ydental_settlement']['write_date']='2026-10-15T12:00:00'
        if self.fault=='old_qweb':
            self.updated['views']['ydental_settlement.ydental_settlement_tokens']=deepcopy(
                cloned['views']['ydental_settlement.ydental_settlement_tokens'])
            self.updated['view_rows'][token_id]=deepcopy(cloned['view_rows'][token_id])
        if self.fault=='other_lang':
            token['arch']['zh_CN']='old'
            token['row']['arch_db']['zh_CN']='old'
            token['languages']['zh_CN']={'has_output_html':False,'sha256':'OLD'}
            self.updated['view_rows'][token_id]['arch_db']['zh_CN']='old'
        if self.fault=='module_version': self.updated['modules']['account']['latest_version']='999'
        if self.fault=='module_state': self.updated['modules']['account']['state']='uninstalled'
        if self.fault=='module_other_field': self.updated['modules']['account']['summary']='altered'
        if self.fault=='unbounded_module': self.updated['modules']['account']['write_date']='changed'
        if self.fault=='schema': self.updated['schema']['sha256']='changed'
        if self.fault=='business': self.updated['tables']['ydental_settlement_payment']['sha256']='changed'
        if self.fault=='acl': self.updated['tables']['ydental_access_grant']['sha256']='changed'
        if self.fault=='economy': self.updated['tables']['account_payment']['sha256']='changed'
        if self.fault=='model_data': self.updated['tables']['ir_model_data']['sha256']='changed'
        if self.fault=='other_view':
            name=next(k for k in self.updated['views'] if k not in ALLOWED_VIEWS)
            self.updated['views'][name]['row']['write_date']='changed'
            self.updated['view_rows'][str(self.updated['views'][name]['row']['id'])]['write_date']='changed'
        control.diff_upgrade(cloned,self.updated,self.source)
        self.current=deepcopy(self.updated)
        return deepcopy(self.updated)

    def start_http(self):
        self.stages.append('start_http')

    def browser_flow(self,updated):
        self.stages.append('browser_flow')
        facts=fact_pair()
        for index,(op,record) in enumerate((('refund_reject',14),('unlock',9))):
            if self.fault=='wrong_page' and index==0: raise AssertionError('page two link wrong')
            if self.fault=='missing_record' and index==0: raise AssertionError('ID14 absent')
            if self.fault=='bad_role' and index==0: raise AssertionError('approver not eligible')
            fields=form(op,record)
            if self.fault=='missing_output' and index==0: fields['output']=None
            if self.fault=='invalid_html' and index==0: fields['valid']=False
            if self.fault=='missing_csrf' and index==0: fields['csrf']=False
            if self.fault=='missing_key' and index==0: fields['key']=False
            if self.fault=='stale_revision' and index==0: fields['revision_match']=False
            validate_form(fields,op,record)
            if self.fault=='duplicate_post' and self.posts: raise AssertionError('duplicate POST')
            self.posts.append(op)
            observed=response(op,record)
            if self.fault=='http200' and index==0: observed['status']=200
            if self.fault=='http403' and index==0: observed['status']=403
            if self.fault=='http409' and index==0: observed['status']=409
            if self.fault=='lost_response' and index==0: raise TimeoutError('committed, response lost')
            validate_response(observed,op,record,accepted=True)
            before=deepcopy(facts)
            if op=='refund_reject':
                facts['refund'].update(ydental_state='rejected',ydental_approver_id=6,
                    ydental_decision_reason='synthetic')
                facts['audit'].append((1,'settlement.refund.reject','accepted',6,1))
                self.current['tables']['ydental_settlement_refund']['sha256']='REFUND_REJECTED'
            else:
                facts['close'].update(ydental_state='unlocked',ydental_unlocked_by_id=6,
                    ydental_unlock_reason='synthetic')
                facts['audit'].append((2,'settlement.unlock','accepted',6,1))
                self.current['tables']['ydental_settlement_close']['sha256']='CLOSE_UNLOCKED'
            if self.fault=='partial_money' and index==0:
                self.current['tables']['account_payment']['sha256']='MONEY_CHANGED'
            validate_action(before,facts,op)
            control.diff_web(updated,self.current,refund_done=True,close_done=(op=='unlock'))
        for negative_op,negative_id in (('unlock',9),('refund_reject',14)):
            self.posts.append('negative_'+negative_op)
            denial=response(negative_op,negative_id)
            denial['feedback']='请求未完成，请核对权限、门店或输入后重试。'
            if self.fault=='negative_accepted':
                denial['feedback']='操作已受理，请核对下方业务记录。'
            validate_response(denial,negative_op,negative_id,accepted=False)
            control.diff_web(updated,self.current,refund_done=True,close_done=True)

    def stop_http(self):
        self.stages.append('stop_http'); self.stopped=True

    def readonly_final(self,before,updated):
        self.stages.append('readonly_final')
        control.diff_web(updated,self.current,refund_done=True,close_done=True)
        return self.current


def main():
    source=snapshot(SOURCE,business=True)
    control.source_gate(source)
    with tempfile.TemporaryDirectory(prefix='s10-p002-fake-') as temp:
        pre=Path(temp)/'preflight.json'
        pre.write_text(json.dumps({'module_write_date_candidates':['ydental_settlement']}))
        cases=['PASS','source_oid','clone_business','old_qweb','other_lang',
            'module_version','module_state','module_other_field','unbounded_module',
            'schema','business','acl','economy','model_data','other_view',
            'wrong_page','missing_record','bad_role','missing_output','invalid_html',
            'missing_csrf','missing_key','stale_revision','http200','http403',
            'http409','lost_response','partial_money','negative_accepted']
        results={}
        with patch.object(control,'PREFLIGHT',pre):
            for case in cases:
                fake=FakeOps(source,None if case=='PASS' else case)
                try:
                    control.execute_pipeline(fake)
                    assert case=='PASS', ('unexpected pass',case)
                    results[case]='SIMULATED_PASS'
                except (AssertionError,TimeoutError) as error:
                    assert case!='PASS',error
                    assert len(fake.posts)<=1 if case in ('lost_response','partial_money',
                        'http200','http403','http409') else len(fake.posts)<=4
                    results[case]='FAIL_CLOSED'
        assert results['PASS']=='SIMULATED_PASS'
        assert all(value=='FAIL_CLOSED' for key,value in results.items() if key!='PASS')
        print(json.dumps({'status':'SIMULATED_PASS','cases':results,'count':len(results)}))


if __name__=='__main__':
    main()
