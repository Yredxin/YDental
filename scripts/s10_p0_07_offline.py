"""Same execute_pipeline/source/clone/request/DOM/audit gates, no Odoo or Firefox."""
from copy import deepcopy
import hashlib
import json
import s10_p0_07_control as c
from s10_p0_07_browser import validate_request,validate_page,BASE

STAMP='2026-10-16 03:00:00'


def signature(state,table):
    state['all']['signatures'][table]={'rows':len(state['all']['rows'].get(table,{})),
        'sha256':hashlib.sha256(json.dumps(state['all']['rows'].get(table,{}),sort_keys=True).encode()).hexdigest()}


def login_state(state,actor,switch=False):
    rows=state['all']['rows'];store=1 if actor==6 else 3
    sid=800+actor
    if not switch:
        user=deepcopy(rows['res_users_log'][3 if actor==6 else 5])
        user.update(id=sid,create_date=STAMP,write_date=STAMP)
        rows['res_users_log'][sid]=user
        dev=deepcopy(rows['res_device_log'][3 if actor==6 else 5])
        dev.update(id=sid,session_identifier='SIMULATED'+str(actor),first_activity=STAMP,last_activity=STAMP)
        rows['res_device_log'][sid]=dev
        sess=deepcopy(rows['ydental_access_session'][179 if actor==6 else 181])
        sess.update(id=sid,ydental_key_hash=hashlib.sha256(dev['session_identifier'].encode()).hexdigest(),
                    ydental_store_id=None,ydental_revision=0,create_date=STAMP,write_date=STAMP)
        rows['ydental_access_session'][sid]=sess
        events=('login','login.scope')
    else:
        rows['ydental_access_session'][sid].update(ydental_store_id=store,ydental_revision=1)
        events=('store.switch',)
    for event in events:
        template={(6,'login'):2662,(6,'login.scope'):2663,(6,'store.switch'):2664,
                  (14,'login'):2668,(14,'login.scope'):2669,(14,'store.switch'):2670}[(actor,event)]
        row=deepcopy(rows['ydental_access_audit'][template]);ident=4000+len(rows['ydental_access_audit'])
        row.update(id=ident,create_date=STAMP,write_date=STAMP,ydental_target_id=actor if event=='login' else sid)
        rows['ydental_access_audit'][ident]=row
    for table in ('ydental_access_audit','ydental_access_session','res_users_log','res_device_log'):signature(state,table)


def dom_for(facts):
    return {'status':200,'main_count':1,'visible':True,'revision':'1','store_name':facts['store_name'],
        'errors':[],'rows':[{'id':r['id'],'state':r['state'],'amount':r['amount']} for r in facts['rows']],
        'url':BASE+'/ydental/settlement'+('?refunds_page=2' if facts['page']==2 else ''),
        'pagination':f"共 {facts['count']} 条；第 {facts['page']} 页" if facts['count']>50 else None,
        'next':'/ydental/settlement?refunds_page=2' if facts['store']==1 and facts['page']==1 else None,
        'prev':'/ydental/settlement' if facts['page']==2 else None}


class FakeOps:
    def __init__(self,source,pre,fault):
        self.source=source;self.pre=pre;self.fault=fault;self.state=None
        self.stopped=False;self.started=False;self.posts=set();self.gets=[]
    def source_readonly(self):
        before=deepcopy(self.source)
        if self.fault=='source_drift':before['all']['signatures']['account_move']['sha256']='BAD'
        if self.fault=='source_oid':before['managed']['oid']=2100320
        if self.fault=='source_store_permission':before['managed']['business']['grants']=[]
        if self.fault=='source_close_state':before['all']['rows']['ydental_settlement_close'][9]['ydental_state']='confirmed'
        return before
    def check_source(self,before):c.source_gate(before)
    def clone_compare(self,before):
        state=deepcopy(before);state['managed']['database']=c.s.TARGET;state['managed']['oid']=9999999
        if self.fault=='clone_drift':state['all']['signatures']['account_payment']['sha256']='BAD'
        if self.fault=='clone_qweb':state['managed']['views']={}
        c.clone_equal(before,state)
        self.state=state;return deepcopy(state)
    def start_http(self):self.started=True
    def browser_flow(self,clone):
        for actor,store in ((6,1),(14,3)):
            for switch in (False,True):
                csrf='SIMULATED_CSRF';path='/ydental/access/action' if switch else '/web/login'
                intent={'actor':actor,'csrf_sha256':hashlib.sha256(csrf.encode()).hexdigest(),
                    'operation':'switch' if switch else 'native_login','login':'SYNTHETIC','scope_revision':0}
                data={'csrf_token':[csrf],'operation':['switch'],'store_id':[str(store)],'revision':['0']} if switch else {
                    'csrf_token':[csrf],'login':['SYNTHETIC'],'password':['SYNTHETIC'],'redirect':['/ydental/access']}
                if self.fault=='bad_identity_csrf':data['csrf_token']=['BAD']
                if self.fault=='bad_identity_store' and switch:data['store_id']=['3']
                validate_request('POST',BASE+path,data,actor,self.posts,intent)
                if self.fault=='duplicate_identity_POST':validate_request('POST',BASE+path,data,actor,self.posts,intent)
                login_state(self.state,actor,switch)
                c.web_diff(clone,self.state,gets=self.gets)
            for number in ((1,2) if actor==6 else (1,)):
                facts=self.pre['refund_pages'][f'{store}-{number}'];dom=dom_for(facts)
                if number==2:
                    if self.fault=='wrong_page_id':dom['rows'][1]['id']=14
                    if self.fault=='wrong_state':dom['rows'][1]['state']='approved'
                    if self.fault=='wrong_store_name':dom['store_name']='BAD'
                    if self.fault=='wrong_page_query':dom['url']=BASE+'/ydental/settlement'
                    if self.fault=='fake_main':dom['main_count']=0
                    if self.fault=='fake_visibility':dom['visible']=False
                    if self.fault=='wrong_page_count':dom['pagination']='共 64 条；第 2 页'
                    if self.fault=='wrong_next':dom['next']='/ydental/settlement?refunds_page=3'
                    if self.fault=='http403':dom['status']=403
                    if self.fault=='response_unknown':dom['status']=None
                    if self.fault=='page_error':dom['errors']=['ERROR']
                if actor==14 and self.fault=='cross_store_leak':dom['rows'].append({'id':13,'state':'requested','amount':'1.00'})
                validate_request('GET',dom['url'],{},actor,self.posts)
                validate_page(dom,facts,actor,self.pre['selection']['selected'])
                if self.fault in ('pay_POST','refund_POST','unlock_POST'):
                    op={'pay_POST':'pay','refund_POST':'refund_execute','unlock_POST':'unlock'}[self.fault]
                    validate_request('POST',BASE+'/ydental/settlement/action',{'operation':[op]},actor,self.posts,{})
                if self.fault=='pdf_GET':validate_request('GET',BASE+'/ydental/settlement/pdf/refund/13',{},actor,self.posts)
                audits=[]
                for target in ([5,6,8,9] if actor==14 else []):
                    row=deepcopy(self.state['all']['rows']['ydental_access_audit'][2671])
                    ident=8000+target;row.update(id=ident,create_date=STAMP,write_date=STAMP,ydental_target_id=target)
                    self.state['all']['rows']['ydental_access_audit'][ident]=row;audits.append(ident)
                if actor==14:
                    entry={'actor':actor,'store':store,'method':'GET','status':200,'path':'/ydental/settlement',
                        'audit_ids':audits,'invoice_ids':[5,6,8,9]}
                    self.gets.append(entry)
                    row=self.state['all']['rows']['ydental_access_audit'][8005]
                    mapping={'audit_actor':'ydental_user_id','audit_store':'ydental_store_id','audit_model':'ydental_target_model',
                        'audit_target':'ydental_target_id','audit_source':'ydental_source','audit_reason':'ydental_reason'}
                    if self.fault in mapping:row[mapping[self.fault]]='BAD'
                    if self.fault=='audit_missing':del self.state['all']['rows']['ydental_access_audit'][8005]
                    if self.fault=='audit_extra':self.state['all']['rows']['ydental_access_audit'][9999]=deepcopy(row)
                    if self.fault=='audit_without_GET':self.gets=[]
                    if self.fault=='audit_duplicate_GET':self.gets*=2
                    if self.fault=='audit_bad_GET_status':entry['status']=409
                    if self.fault=='audit_bad_GET_method':entry['method']='POST'
                    if self.fault=='audit_bad_GET_actor':entry['actor']=6
                    if self.fault=='extra_GET':self.gets*=3
                else:self.gets.append({'actor':actor,'store':store,'method':'GET','status':200,
                    'path':'/ydental/settlement','audit_ids':[],'invoice_ids':[]})
                signature(self.state,'ydental_access_audit')
                field_faults={'receipt_write':('ydental_settlement_receipt',243,'ydental_operation','pay'),
                    'mutex_write':('ydental_settlement_mutex',1,'ydental_revision',245),
                    'close_write':('ydental_settlement_close',9,'ydental_state','confirmed'),
                    'refund_write':('ydental_settlement_refund',13,'ydental_state','approved'),
                    'old_audit_write':('ydental_access_audit',2689,'ydental_event','BAD'),
                    'asset_unknown':('ir_attachment',1075,'public',False),
                    'mail_unknown':('mail_message',next(iter(self.state['all']['rows']['mail_message'])),'body','BAD'),
                    'user_permission':('res_users',6,'active',False)}
                if self.fault in field_faults:
                    table,i,k,v=field_faults[self.fault];self.state['all']['rows'][table][i][k]=v;signature(self.state,table)
                if self.fault=='module_drift':self.state['managed']['modules']['base']['state']='uninstalled'
                if self.fault=='schema_drift':self.state['managed']['schema']['sha256']='BAD'
                if self.fault in ('money_drift','stock_drift','acl_drift'):
                    table={'money_drift':'account_payment','stock_drift':'stock_move','acl_drift':'ir_model_access'}[self.fault]
                    self.state['all']['signatures'][table]['sha256']='BAD'
                if self.fault=='unknown_file':self.state['managed']['filestore']['files']['unknown.pdf']='BAD'
                c.web_diff(clone,self.state,gets=self.gets)
    def stop_http(self):self.stopped=True
    def readonly_final(self,before,clone):
        assert self.stopped
        c.web_diff(clone,self.state,gets=self.gets)
        assert len(self.gets)==3 and len(self.posts)==4
        return self.state


def main():
    source=c.load_capture(c.PRIVATE/'source-initial-readonly.json')
    pre=json.loads((c.PRIVATE/'preflight-candidate.json').read_text())
    faults=['source_drift','source_oid','source_store_permission','source_close_state','clone_drift','clone_qweb',
        'bad_identity_csrf','bad_identity_store','duplicate_identity_POST','wrong_page_id','wrong_state',
        'wrong_store_name','wrong_page_query','fake_main','fake_visibility','wrong_page_count','wrong_next',
        'http403','response_unknown','page_error','cross_store_leak','pay_POST','refund_POST','unlock_POST','pdf_GET',
        'audit_actor','audit_store','audit_model','audit_target','audit_source','audit_reason','audit_missing','audit_extra',
        'audit_without_GET','audit_duplicate_GET','audit_bad_GET_status','audit_bad_GET_method','audit_bad_GET_actor','extra_GET',
        'receipt_write','mutex_write','close_write','refund_write','old_audit_write','asset_unknown','mail_unknown',
        'user_permission','module_drift','schema_drift','money_drift','stock_drift','acl_drift','unknown_file']
    results={}
    for fault in ['PASS']+faults:
        ops=FakeOps(source,pre,fault)
        try:
            c.execute_pipeline(ops)
            assert fault=='PASS',('UNEXPECTED_PASS',fault)
            results[fault]='SIMULATED_PASS'
        except (AssertionError,KeyError,ValueError,TypeError) as error:
            if fault=='PASS':raise
            if str(error).startswith("('UNEXPECTED_PASS'"):raise
            assert ops.stopped or not ops.started
            results[fault]='FAIL_CLOSED'
    print(json.dumps({'status':'SIMULATED_PASS','count':len(results),'cases':results}))


if __name__=='__main__':main()
