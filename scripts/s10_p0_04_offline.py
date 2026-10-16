"""No Odoo write: inject faults into the same controller, HTML and field gate."""
from copy import deepcopy
import hashlib
import json

import s10_p0_04_control as c
from s10_p0_04_browser import validate_form, validate_response, guard_send

REASON = 'P0-04 synthetic finance unlock review'
KEY = 'p004-offline-unique-key'
INTENT = {'operation':'unlock','close_id':9,'actor':6,'store':1,'key':KEY,'reason':REASON}


def html_form():
    return {'action':'/ydental/settlement/action','method':'post','visible':True,
        'valid':True,'output':'html','csrf':True,'key':True,'revision_match':True,
        'reason':True,'record':'9','operation':'unlock','button_enabled':True}


def http_response(accepted):
    return {'method':'POST','path':'/ydental/settlement/action',
        'content_type':'application/x-www-form-urlencoded',
        'post':{'operation':['unlock'],'output':['html'],'close_id':['9'],
                'csrf_token':['OWN'],'revision':['CURRENT'],'key':[KEY]},
        'status':303,'location_path':'/ydental/settlement','notice':True,
        'landing_status':200 if accepted else 403,'server_denial_log':not accepted,
        'feedback':('操作已受理，请核对下方业务记录。' if accepted else
                    '请求未完成，请核对权限、门店或输入后重试。')}


def changed_signature(state, table):
    state['all']['signatures'][table]={'rows':len(state['all']['rows'][table]),
        'sha256':hashlib.sha256((table+' SIMULATED').encode()).hexdigest()}


def success_state(source):
    state=deepcopy(source)
    row=state['all']['rows']['ydental_settlement_close'][9]
    row.update({'ydental_state':'unlocked','ydental_unlocked_by_id':6,
        'ydental_unlock_reason':REASON,'ydental_unlocked_at':'2026-10-16T02:00:00',
        'write_uid':6,'write_date':'2026-10-16T02:00:00'})
    mutex=state['all']['rows']['ydental_settlement_mutex'][1]
    mutex['ydental_revision']=244
    receipt=deepcopy(state['all']['rows']['ydental_settlement_receipt'][242])
    receipt.update({'id':300,'ydental_key':KEY,'ydental_operation':'unlock',
        'ydental_actor_id':6,'ydental_store_id':1,
        'ydental_result':{'close_id':9,'state':'unlocked'},
        'ydental_fingerprint':hashlib.sha256(json.dumps(
            ['unlock',1,{'close_id':9,'reason':REASON}],sort_keys=True,ensure_ascii=True).encode()).hexdigest()})
    state['all']['rows']['ydental_settlement_receipt'][300]=receipt
    audit=deepcopy(state['all']['rows']['ydental_access_audit'][2661])
    audit.update({'id':2662,'ydental_event':'settlement.unlock','ydental_result':'accepted',
        'ydental_target_id':9,'ydental_target_model':'ydental.settlement.close',
        'ydental_reason':REASON,'ydental_after':{'cycle':1}})
    state['all']['rows']['ydental_access_audit'][2662]=audit
    for table in ('ydental_settlement_close','ydental_settlement_mutex',
                  'ydental_settlement_receipt','ydental_access_audit'):
        changed_signature(state,table)
    return state


class FakeOps:
    def __init__(self, source, fault):
        self.source=source; self.fault=fault; self.stages=[]; self.posts=[]; self.stopped=False
        self.current=None
    def source_readonly(self):
        self.stages.append('source_readonly')
        return deepcopy(self.source)
    def check_source(self, before):
        self.stages.append('check_source')
        if self.fault=='source_drift': raise AssertionError('source drift')
    def clone_compare(self,before):
        self.stages.append('clone_compare')
        clone=deepcopy(before)
        if self.fault=='clone_drift': raise AssertionError('clone drift')
        return clone
    def start_http(self):
        self.stages.append('start_http')
    def browser_flow(self,clone):
        self.stages.append('browser_flow')
        if self.fault=='page2_unreachable': raise AssertionError('page 2 missing')
        if self.fault=='wrong_close_id': raise AssertionError('close 9 absent')
        if self.fault=='not_latest_cycle': raise AssertionError('not latest cycle')
        form=html_form()
        for fault,field in {'bad_qweb':'output','bad_html5':'valid','bad_csrf':'csrf',
                            'bad_revision':'revision_match','missing_key':'key',
                            'no_role':'visible','bad_operation':'operation'}.items():
            if self.fault==fault: form[field]=False if field!='operation' else 'refund_reject'
        validate_form(form,'unlock',9)
        state=deepcopy(clone)
        for actor,store in ((10,1),(14,3)):
            guard_send(set(),actor,'unlock',9)
            self.posts.append((actor,'unlock',9))
            denial=http_response(False)
            if self.fault=='negative_accepted' and actor==10:
                denial['feedback']='操作已受理，请核对下方业务记录。'
            if self.fault=='negative_wrong_status' and actor==10: denial['status']=200
            validate_response(denial,'unlock',9,accepted=False)
            if self.fault=='negative_committed' and actor==10:
                state=success_state(clone)
            c.web_diff(clone,state)
        guard_send(set(),6,'unlock',9)
        self.posts.append((6,'unlock',9))
        response=http_response(True)
        if self.fault=='response_lost_committed':
            self.current=success_state(clone)
            raise TimeoutError('response lost after one committed POST')
        for fault, status in {'http200':200,'http403':403,'http409':409}.items():
            if self.fault==fault: response['status']=status
        validate_response(response,'unlock',9,accepted=True)
        state=success_state(clone)
        if self.fault=='duplicate_key': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_key']=clone['all']['rows']['ydental_settlement_receipt'][242]['ydental_key']
        if self.fault=='bad_fingerprint': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_fingerprint']='0'*64
        if self.fault=='bad_receipt_operation': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_operation']='pay'
        if self.fault=='bad_receipt_actor': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_actor_id']=14
        if self.fault=='bad_receipt_store': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_store_id']=3
        if self.fault=='bad_receipt_result': state['all']['rows']['ydental_settlement_receipt'][300]['ydental_result']={'close_id':9,'state':'confirmed'}
        if self.fault=='extra_receipt': state['all']['rows']['ydental_settlement_receipt'][301]=deepcopy(state['all']['rows']['ydental_settlement_receipt'][300])
        if self.fault=='mutex_twice': state['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision']=245
        if self.fault=='mutex_other_row': state['all']['rows']['ydental_settlement_mutex'][2]=deepcopy(state['all']['rows']['ydental_settlement_mutex'][1])
        if self.fault=='refund14_changed': state['all']['rows']['ydental_settlement_refund'][14]['ydental_state']='done'
        if self.fault=='amount_changed': state['all']['rows']['ydental_settlement_close'][9]['ydental_gross']=1
        if self.fault=='money_changed': changed_signature(state,'account_payment')
        if self.fault=='stock_changed': changed_signature(state,'stock_move')
        if self.fault=='audit_missing': del state['all']['rows']['ydental_access_audit'][2662]
        if self.fault=='audit_forged': state['all']['rows']['ydental_access_audit'][2662]['ydental_user_id']=14
        if self.fault=='asset_unknown': state['all']['rows']['ir_attachment'][99999]=deepcopy(state['all']['rows']['ir_attachment'][1075])
        if self.fault=='mail_unknown': state['all']['rows']['mail_message'][99999]=deepcopy(state['all']['rows']['mail_message'][1833])
        if self.fault=='module_changed': state['managed']['modules']['base']['state']='uninstalled'
        if self.fault=='acl_changed': changed_signature(state,'ir_model_access')
        if self.fault=='extra_table': state['all']['signatures']['unknown_table']={'rows':0,'sha256':'0'*64}
        if self.fault=='duplicate_post': guard_send({(6,'unlock',9)},6,'unlock',9)
        c.web_diff(clone,state,unlock=True,intent=INTENT)
        self.current=state
    def stop_http(self):
        self.stages.append('stop_http'); self.stopped=True
    def readonly_final(self,before,clone):
        self.stages.append('readonly_final')
        c.web_diff(clone,self.current,unlock=True,intent=INTENT)
        return self.current


def main():
    source=c.capture(c.s.SOURCE,business=False)
    faults=['source_drift','clone_drift','page2_unreachable','wrong_close_id','not_latest_cycle',
        'bad_qweb','bad_html5','bad_csrf','bad_revision','missing_key','no_role','bad_operation',
        'negative_accepted','negative_wrong_status','negative_committed','response_lost_committed',
        'http200','http403','http409','duplicate_key','bad_fingerprint','bad_receipt_operation',
        'bad_receipt_actor','bad_receipt_store','bad_receipt_result','extra_receipt','mutex_twice',
        'mutex_other_row','refund14_changed','amount_changed','money_changed','stock_changed',
        'audit_missing','audit_forged','asset_unknown','mail_unknown','module_changed',
        'acl_changed','extra_table','duplicate_post']
    results={}
    for case in ['PASS']+faults:
        fake=FakeOps(source,case)
        try:
            c.execute_pipeline(fake)
            assert case=='PASS',('unexpected_pass',case)
            results[case]='SIMULATED_PASS'
        except (AssertionError,TimeoutError,KeyError,ValueError) as error:
            assert case!='PASS',error
            assert fake.stopped or 'start_http' not in fake.stages
            assert len(fake.posts)<=3
            results[case]='FAIL_CLOSED'
    assert results['PASS']=='SIMULATED_PASS' and all(results[f]=='FAIL_CLOSED' for f in faults)
    print(json.dumps({'status':'SIMULATED_PASS','cases':results,'count':len(results)},ensure_ascii=False))


if __name__=='__main__': main()
