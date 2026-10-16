"""Same execute_pipeline/source/clone/request/DOM/audit gates, no Odoo or Firefox."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import s10_p0_09_control as c
from s10_p0_09_browser import validate_request as native_validate_request,validate_page,BASE,GateFailure,failure_record,validate_identity_response,Browser
from s10_p0_09_native_contract import login_fixture
from lxml import etree

def validate_request(method,url,data,actor,ledger,intent=None,headers=None):
    path='/ydental/access' if '/ydental/access/action' in url else '/web/login?redirect=/ydental/access'
    headers=headers or {'origin':BASE,'referer':BASE+path,'content-type':'application/x-www-form-urlencoded'}
    return native_validate_request(method,url,data,actor,ledger,intent,headers)


STAMP='2026-10-16 05:00:00'


def signature(state,table):
    state['all']['signatures'][table]={'rows':len(state['all']['rows'].get(table,{})),
        'sha256':hashlib.sha256(json.dumps(state['all']['rows'].get(table,{}),sort_keys=True).encode()).hexdigest()}


def login_state(state,actor,switch=False):
    rows=state['all']['rows'];store=1 if actor==6 else 3
    sid=800+actor
    if not switch:
        user=deepcopy(rows['res_users_log'][8 if actor==6 else 5])
        user.update(id=sid,create_date=STAMP,write_date=STAMP)
        rows['res_users_log'][sid]=user
        dev=deepcopy(rows['res_device_log'][8 if actor==6 else 5])
        dev.update(id=sid,session_identifier=('SIMULATED'+str(actor)).ljust(42,'x'),first_activity=STAMP,last_activity=STAMP)
        rows['res_device_log'][sid]=dev
        sess=deepcopy(rows['ydental_access_session'][184 if actor==6 else 181])
        sess.update(id=sid,ydental_key_hash=hashlib.sha256(dev['session_identifier'].encode()).hexdigest(),
                    ydental_store_id=None,ydental_revision=0,create_date=STAMP,write_date=STAMP)
        rows['ydental_access_session'][sid]=sess
        events=('login','login.scope')
    else:
        return switch_state(state,actor,store)

    for event in events:
        template={(6,'login'):2690,(6,'login.scope'):2691,(6,'store.switch'):2692,
                  (14,'login'):2668,(14,'login.scope'):2669,(14,'store.switch'):2670}[(actor,event)]
        row=deepcopy(rows['ydental_access_audit'][template]);ident=4000+len(rows['ydental_access_audit'])
        row.update(id=ident,create_date=STAMP,write_date=STAMP,ydental_target_id=actor if event=='login' else sid)
        rows['ydental_access_audit'][ident]=row
    for table in ('ydental_access_audit','ydental_access_session','res_users_log','res_device_log'):signature(state,table)


def switch_state(state,actor,dest):
    rows=state['all']['rows'];sid=800+actor;session=rows['ydental_access_session'][sid]
    old=session['ydental_store_id'] or False
    session.update(ydental_store_id=dest,ydental_revision=session['ydental_revision']+1)
    row=deepcopy(rows['ydental_access_audit'][2692 if actor==6 else 2670]);ident=4000+len(rows['ydental_access_audit'])
    row.update(id=ident,create_date=STAMP,write_date=STAMP,ydental_target_id=sid,ydental_store_id=dest,
        ydental_before={'store_id':old},ydental_after={'store_id':dest})
    rows['ydental_access_audit'][ident]=row
    for table in ('ydental_access_audit','ydental_access_session'):signature(state,table)


class FakeContext:
    def __init__(self,page):self.page=page
    def cookies(self,base):return [{'name':'session_id','value':self.page.cookie}]


class FakeForm:
    def __init__(self,page,selector):self.page=page;self.selector=selector
    def count(self):return 0 if self.selector=='main.o_ydental_settlement' else 1
    def locator(self,selector):return FakeForm(self.page,selector)
    def input_value(self):return str(self.page.ops.state['all']['rows']['ydental_access_session'][800+self.page.actor]['ydental_revision']) if not self.page.stale_dom else '99'
    def select_option(self,store):self.page.selected=int(store)


class FakePage:
    def __init__(self,ops,actor):
        self.ops=ops;self.actor=actor;self.selected=None;self.stale_dom=False
        self.cookie=('SIMULATED'+str(actor)).ljust(42,'x');self.context=FakeContext(self)
    def locator(self,selector):return FakeForm(self,selector)


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
        self.contract=deepcopy(json.loads((c.PRIVATE/'scope-contract.json').read_text()))
        if self.fault in ('PASS_C_SIMULATED','stale_switch_revision'):
            self.contract['C_enabled']=True
            self.contract['C_status']='SIMULATED_HYPOTHETICAL_PROVIDER_EVIDENCE_ONLY'
        reader=Browser.__new__(Browser)
        reader.baseline=clone;reader.capture=lambda:self.state;reader.scope_contract=self.contract
        reader.gets=self.gets;reader.scope_states={};reader.scope_counter=0
        def submit(page,form,actor,stage,intent):
            data={'csrf_token':['SIMULATED_CSRF'],'operation':['switch'],'store_id':[str(page.selected)],'revision':[str(intent['scope_revision'])]}
            intent.update(actor=actor,csrf_sha256=hashlib.sha256(b'SIMULATED_CSRF').hexdigest())
            if self.fault=='bad_identity_store':data['store_id']=['99']
            if self.fault=='bad_revision':data['revision']=['99']
            if self.fault=='stale_switch_revision':data['revision']=['0']
            validate_request('POST',BASE+'/ydental/access/action',data,actor,self.posts,intent)
            if self.fault=='duplicate_switch':validate_request('POST',BASE+'/ydental/access/action',data,actor,self.posts,intent)
            if self.fault=='switch_unknown_response':validate_identity_response(None,'UNKNOWN',BASE+'/ydental/access',[])
            switch_state(self.state,actor,page.selected)
            validate_identity_response(303,None,BASE+'/ydental/access',[])
        reader.identity_post=submit
        for actor,store in ((6,1),(14,3)):
            csrf='SIMULATED_CSRF';path='/web/login'
            intent={'actor':actor,'csrf_sha256':hashlib.sha256(csrf.encode()).hexdigest(),
                'operation':'native_login','path':path,'login_sha256':hashlib.sha256(b'SYNTHETIC').hexdigest(),
                'password_sha256':hashlib.sha256(b'SYNTHETIC').hexdigest()}
            data={e.get('name'):[e.get('value','')] for e in etree.HTML(login_fixture()).xpath('//input[@name]')}
            headers={'origin':BASE,'referer':BASE+'/web/login?redirect=/ydental/access','content-type':'application/x-www-form-urlencoded'}
            if self.fault=='bad_identity_csrf':data['csrf_token']=['BAD']
            if self.fault=='login_missing_field':data.pop('webauthn_response')
            if self.fault=='login_extra_field':data['UNKNOWN']=['SECRET']
            if self.fault=='login_duplicate_field':data['redirect']*=2
            if self.fault=='login_redirect':data['redirect']=['/web/become']
            if self.fault=='login_mode':data['type']=['webauthn']
            if self.fault=='login_webauthn':data['webauthn_response']=['SECRET']
            if self.fault=='login_actor':data['login']=['BAD']
            if self.fault=='login_password':data['password']=['BAD']
            if self.fault=='login_origin':headers['origin']='http://external.invalid'
            if self.fault=='login_content_type':headers['content-type']='application/json'
            if self.fault=='login_query':path+='?redirect=/ydental/access';intent['path']='/web/login'
            if self.fault=='unknown_url':path='/unknown';intent['path']=path
            if self.fault=='external_url':headers['referer']='http://external.invalid/'
            try:validate_request('POST',BASE+path,data,actor,self.posts,intent,headers)
            except GateFailure as error:
                proof=failure_record(error,'POST',BASE+path,data,actor,'SIMULATED',headers,'SIMULATED_SECRET')
                assert proof['failure_code'] and proof['location']['line']>0
                assert all(v not in json.dumps(proof) for v in ('SIMULATED_SECRET','SYNTHETIC','http://external.invalid'))
                raise
            if self.fault=='duplicate_identity_POST':validate_request('POST',BASE+path,data,actor,self.posts,intent,headers)
            if self.fault=='login_lost_response':validate_identity_response(None,'UNKNOWN',BASE+'/web/login',[])
            validate_identity_response(303,None,BASE+'/ydental/access',[])
            login_state(self.state,actor,False)
            default=store
            if self.fault in ('PASS_B','bad_identity_store','bad_revision','duplicate_switch','switch_unknown_response'):default=None
            if self.fault in ('PASS_C_SIMULATED','stale_switch_revision') and actor==14:default=4
            if self.fault in ('scope_c_disabled','scope_c_no_permission') and actor==14:default=4
            if default is not None:switch_state(self.state,actor,default)
            page=FakePage(self,actor)
            session=self.state['all']['rows']['ydental_access_session'][800+actor]
            if self.fault=='scope_wrong_actor':session['ydental_user_id']=5
            if self.fault=='scope_wrong_default' and actor==6:session['ydental_store_id']=2
            if self.fault=='scope_bad_revision':session['ydental_revision']=3
            if self.fault=='scope_cookie':page.cookie='WRONG'.ljust(42,'x')
            if self.fault=='scope_hash':session['ydental_key_hash']=hashlib.sha256(b'WRONG').hexdigest()
            if self.fault=='scope_old_session':page.cookie=self.state['all']['rows']['res_device_log'][3 if actor==6 else 5]['session_identifier']
            if self.fault=='scope_duplicate_session':
                self.state['all']['rows']['ydental_access_session'][9999]=deepcopy(session)
            if self.fault=='scope_stale_dom':page.stale_dom=True
            if self.fault=='scope_no_audit':
                ident=max(self.state['all']['rows']['ydental_access_audit']);del self.state['all']['rows']['ydental_access_audit'][ident]
            if self.fault=='scope_c_no_permission' and actor==14:
                self.contract['C_enabled']=True;self.contract['actors']['14']['valid_stores']=[3]
            if self.fault=='scope_busy':self.contract['actors'][str(actor)]['execution']['lease_ids']=[999]
            before_posts=len(self.posts)
            state=reader.select_scope(page,actor,store)
            assert state['store']==store and state['revision'] in (1,2)
            if default==store:assert len(self.posts)==before_posts,'AUTO_SWITCH_MUST_BE_SKIPPED'
            if default!=store:assert len(self.posts)==before_posts+1,'NECESSARY_SWITCH_MUST_BE_ONCE'
            reader.scope(page,actor,store,expected=reader.scope_states[actor])
            c.web_diff(clone,self.state,gets=self.gets,scope_contract=self.contract)
            for number in ((1,2) if actor==6 else (1,)):
                facts=self.pre['refund_pages'][f'{store}-{number}'];dom=dom_for(facts)
                dom['revision']=str(state['revision']);dom['scope_revision']=state['revision']
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
                c.web_diff(clone,self.state,gets=self.gets,scope_contract=self.contract)
    def stop_http(self):self.stopped=True
    def readonly_final(self,before,clone):
        assert self.stopped
        c.web_diff(clone,self.state,gets=self.gets,scope_contract=self.contract)
        assert len(self.gets)==3 and {'login-6','login-14'}<=self.posts<= {'login-6','login-14','switch-6','switch-14'}
        return self.state


def main():
    source=c.load_capture(c.PRIVATE/'source-initial-readonly.json')
    pre=json.loads((c.PRIVATE/'preflight-candidate.json').read_text())
    faults=['login_missing_field','login_extra_field','login_duplicate_field','login_redirect','login_mode',
        'login_webauthn','login_actor','login_password','login_origin','login_content_type','login_query','unknown_url',
        'external_url','bad_revision','login_lost_response','duplicate_switch','switch_unknown_response',
        'scope_wrong_actor','scope_wrong_default','scope_bad_revision','scope_cookie','scope_hash','scope_old_session',
        'scope_duplicate_session','stale_switch_revision','scope_stale_dom','scope_no_audit','scope_c_disabled','scope_c_no_permission','scope_busy','source_drift','source_oid','source_store_permission','source_close_state','clone_drift','clone_qweb',
        'bad_identity_csrf','bad_identity_store','duplicate_identity_POST','wrong_page_id','wrong_state',
        'wrong_store_name','wrong_page_query','fake_main','fake_visibility','wrong_page_count','wrong_next',
        'http403','response_unknown','page_error','cross_store_leak','pay_POST','refund_POST','unlock_POST','pdf_GET',
        'audit_actor','audit_store','audit_model','audit_target','audit_source','audit_reason','audit_missing','audit_extra',
        'audit_without_GET','audit_duplicate_GET','audit_bad_GET_status','audit_bad_GET_method','audit_bad_GET_actor','extra_GET',
        'receipt_write','mutex_write','close_write','refund_write','old_audit_write','asset_unknown','mail_unknown',
        'user_permission','module_drift','schema_drift','money_drift','stock_drift','acl_drift','unknown_file']
    results={};failure_codes={}
    actual_private=c.PRIVATE
    import tempfile
    scope_contract=json.loads((actual_private/'scope-contract.json').read_text())
    login_fixture() # cache fixed installed template before isolating per-case proof paths
    positives=['PASS','PASS_B','PASS_C_SIMULATED']
    for fault in positives+faults:
        ops=FakeOps(source,pre,fault)
        # Unique proof directory per simulated pipeline; no real resources.
        simdir=tempfile.TemporaryDirectory(prefix='p009-scope-'+fault+'-')
        c.PRIVATE=Path(simdir.name)
        (c.PRIVATE/'scope-contract.json').write_text(json.dumps(scope_contract))
        try:
            c.execute_pipeline(ops)
            assert fault in positives,('UNEXPECTED_PASS',fault)
            results[fault]='SIMULATED_PASS'
        except (AssertionError,KeyError,ValueError,TypeError) as error:
            if fault in positives:raise
            if str(error).startswith("('UNEXPECTED_PASS'"):raise
            assert ops.stopped or not ops.started
            code=getattr(error,'failure_code',error.args[0] if error.args else type(error).__name__)
            expected={'scope_wrong_actor':'S2_NEW_OWN_SESSION','scope_wrong_default':'S6_SESSION_STATE',
                'scope_bad_revision':'S6_SESSION_STATE','scope_cookie':'S2_SESSION_UNIQUE','scope_hash':'S2_SESSION_UNIQUE',
                'scope_old_session':'S2_NEW_OWN_SESSION','scope_duplicate_session':'S2_SESSION_UNIQUE','scope_stale_dom':'S4_DOM_REVISION',
                'scope_no_audit':'A4_REVISION_AUDIT_COUNT','scope_c_disabled':'S6_SESSION_STATE',
                'scope_c_no_permission':'S3_CURRENT_MEMBERSHIP','scope_busy':'S3_ACTOR_BUSY',
                'stale_switch_revision':'N7_REVISION','duplicate_switch':'N8_DUPLICATE_POST','switch_unknown_response':'N0_IDENTITY_RESPONSE_UNKNOWN'}
            if fault in expected:assert code==expected[fault],(fault,code,expected[fault])
            failure_codes[fault]=str(code)
            results[fault]='FAIL_CLOSED'
        finally:
            c.PRIVATE=actual_private;simdir.cleanup()
    print(json.dumps({'status':'SIMULATED_PASS','count':len(results),'cases':results,'failure_codes':failure_codes,'real_C_branch':'NOT_APPLICABLE','Browser_scope_same_method':True,'Browser_select_scope_same_method':True}))


if __name__=='__main__':main()
