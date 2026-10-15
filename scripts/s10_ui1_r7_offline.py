"""SIMULATED R7 actual create/CLI and full run with native form constraints."""
from contextlib import redirect_stdout
from datetime import date
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import s10_ui1_r7_control as control
import s10_ui1_r7_browser as web
from s10_ui1_r2_evidence import read_complete
checks=[]

class FakeSocket:
    def __enter__(self): return self
    def __exit__(self,*_):pass
    def bind(self,address): assert address==('127.0.0.1',control.PORT)
class CreateCursor:
    def __init__(self,state):self.state=state
    def __enter__(self):return self
    def __exit__(self,*_):pass
    def execute(self,query):
        assert 'CREATE DATABASE' in str(query)
        self.state['calls']+=1
        if self.state['fail_sql']:raise RuntimeError('SIMULATED CREATE fail')
        self.state['created']=True
class CreateConn:
    def __init__(self,state):
        self.state=state;self.autocommit=False
        self.info=type('Info',(),{'transaction_status':control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self):return CreateCursor(self.state)
    def close(self):pass

def create_case(root,fail=None):
    root.mkdir()
    local=root/'.local';local.mkdir()
    sr=local/control.SOURCE
    fs=sr/'data/filestore'/control.SOURCE;fs.mkdir(parents=True)
    raw=b'nonempty-r7-clone-input';(fs/'alpha').write_bytes(raw)
    expected={'alpha':{'sha256':hashlib.sha256(raw).hexdigest()}}
    (sr/'fixture.json').write_text(json.dumps({'db':control.SOURCE,'oid':2100265,'actors':{'frontdesk':6}}))
    if fail=='copy':(fs/'alpha').write_bytes(b'changed')
    run=local/control.NAME
    state={'calls':0,'created':False,'fail_sql':fail=='sql','tail':0}
    def identity(expect_target=False):
        if expect_target:
            assert state['created'];state['tail']+=1
            return {'password':'FAKE'},expected,314159 if fail=='tail' and state['tail']>1 else 271828
        assert not state['created']
        return {'password':'FAKE'},expected,None
    with patch.multiple(control,ROOT=root,SOURCE_RUN=sr,RUN=run,identity=identity), \
         patch.object(control.socket,'socket',return_value=FakeSocket()), \
         patch.object(control.psycopg2,'connect',side_effect=lambda **kw:CreateConn(state)):
        if fail:
            try:
                with redirect_stdout(io.StringIO()):control.dispatch('create')
            except (AssertionError,RuntimeError,ValueError):pass
            else:raise AssertionError('create failure admitted '+fail)
            assert not (run/'create-complete.json').exists()
            checks.append('actual_create_'+fail+'_rejected')
            return
        with redirect_stdout(io.StringIO()):control.dispatch('create')
        assert state['calls']==1 and state['tail']==2
        assert (run/'data/filestore'/control.NAME/'alpha').read_bytes()==raw
        assert read_complete(run/'create-complete.json')['phase']=='VERIFIED'
        assert read_complete(run/'fixture.json')['inherited_from']['oid']==2100265
        try:control.dispatch('create')
        except (AssertionError,FileExistsError):pass
        else:raise AssertionError('repeat create admitted')
        assert state['calls']==1
        with patch.object(control,'inherited_baseline',side_effect=RuntimeError('drift')):
            try:control.dispatch('serve')
            except RuntimeError:pass
            else:raise AssertionError('serve after drift')
        assert not (run/'http-r7.attempt.json').exists()
        with patch.object(control,'inherited_baseline',return_value={'same':True}),patch.object(control,'qweb_loaded',return_value=False):
            try:control.dispatch('serve')
            except AssertionError:pass
            else:raise AssertionError('serve without candidate QWeb')
        assert not (run/'http-r7.attempt.json').exists()
        try:control.dispatch('unknown')
        except ValueError:pass
        else:raise AssertionError('unknown CLI admitted')
        checks.append('actual_create_copy_sql_marker_tail_repeat_and_serve_gates')

class State:
    def __init__(self,fault=None):
        self.fault=fault;self.revisions={'manager':10,'frontdesk':20};self.grant='write'
        self.store={'manager':1,'frontdesk':1};self.money=0;self.exports=3;self.mail=0
        self.audit_events={'login':0,'login.scope':0,'store.switch':0,'authorization.change':0}
        self.requests=[];self.responses=[];self.pages=[]
    def finance(self,database=web.NAME):
        assert database in (web.NAME,web.SOURCE)
        return {'moves':((1,100),(2,40)),'receipts':tuple(range(1,9)),
                'native_payments':((1,60),(2,20)),'money':self.money}
    def audit(self):
        return {'exports':self.exports,'mail':self.mail,'bus':30,
                'categories':sorted(self.audit_events.items())}

class Response:
    def __init__(self,status=200,headers=None,url='http://127.0.0.1:18276/ydental/settlement',method='GET'):
        self.status=status;self.headers=headers or {};self.url=url
        self.request=type('Req',(),{'method':method})()

class Locator:
    def __init__(self,page,selector):self.page=page;self.selector=selector
    def locator(self,selector):return Locator(self.page,self.selector+' '+selector)
    def count(self):
        if 'business_date' in self.selector:return 1 if self.page.state.fault!='missing_date_dom' else 0
        if 'operation' in self.selector and 'switch' in self.selector:return 1
        if 'operation' in self.selector and 'close' in self.selector:return 0 if self.page.state.fault=='missing_form' else 1
        if 'data-ui1-feedback' in self.selector:return 1 if self.page.feedback else 0
        return 1
    def input_value(self):
        if 'csrf_token' in self.selector:return 'token-'+self.page.role
        if 'revision' in self.selector:
            if '/ydental/access/action' in self.selector:return str(self.page.state.revisions[self.page.role])
            return self.page.form_revision
        raise AssertionError(self.selector)
    def inner_text(self):
        if self.selector=='h1':return '线下结算工作台'
        if 'data-ui1-feedback' in self.selector:return self.page.feedback
        raise AssertionError(self.selector)
    def fill(self,value):
        if 'business_date' in self.selector:
            if self.page.state.fault=='drop_date_fill':return
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise RuntimeError('native date fill rejected')
            self.page.date_value=value
        else:self.page.filled[self.selector]=value
    def select_option(self,value):
        assert value=='cash';self.page.channel=value
    def evaluate(self,script):
        if 'el.value' in script:return {'value':self.page.date_value,'required':True,'type':'date',
            'valid':self.page.valid,'validation_message':'' if self.page.valid else 'Please fill out this field.'}
        if 'form.checkValidity()' in script:return self.page.valid
        if 'form.elements' in script:return [] if self.page.valid else [{'name':'business_date','type':'date','required':True}]
        raise AssertionError(script)
    def click(self,timeout=None):
        if self.selector=='button[type=submit]' and not self.page.is_close:
            assert self.page.filled.get('[name=login]') and self.page.filled.get('[name=password]')
            self.page.state.audit_events['login']+=1;self.page.state.audit_events['login.scope']+=1
            return
        assert self.page.is_close and timeout==5000
        if not self.page.valid or self.page.state.fault=='no_post':return
        request=type('Req',(),{'method':'POST','url':web.BASE+'/ydental/settlement/action',
            'headers':{'content-type':'application/x-www-form-urlencoded'},
            'post_data':'operation=close&output=html&business_date='+self.page.date_value+
                        '&channel=cash&csrf_token=synthetic&key=synthetic&revision='+self.page.form_revision})()
        self.page.state.requests.append(request)
        for cb in self.page.listeners.get('request',[]):cb(request)
        status=409 if self.page.state.fault=='wrong_status' else 303
        response=Response(status,{'location':'/ydental/settlement?notice='+'a'*32,
            'content-type':'text/html'},web.BASE+'/ydental/settlement/action','POST')
        response.request=request
        self.page.state.responses.append(response)
        for cb in self.page.listeners.get('response',[]):cb(response)
        self.page.url=web.BASE+'/ydental/settlement?notice='+'a'*32
        self.page.feedback='' if self.page.state.fault=='no_feedback' else '请求未完成，请核对权限'
        if self.page.state.fault=='money_change':self.page.state.money+=1

class Page:
    def __init__(self,state,role):
        self.state=state;self.role=role;self.url='';self.feedback='';self.date_value=''
        self.form_revision='';self.channel='cash';self.filled={};self.is_close=False
        self.listeners={'request':[],'response':[]}
    @property
    def valid(self):return bool(re.fullmatch(r'\d{4}-\d{2}-\d{2}',self.date_value))
    def goto(self,url,**_):
        self.url=url;self.feedback=''
        self.is_close='/ydental/settlement' in url
        if self.is_close:self.form_revision=str(self.state.revisions[self.role])
        return Response(200,url=url)
    def reload(self,**_):return self.goto(self.url)
    def locator(self,selector):return Locator(self,selector)
    def wait_for_url(self,pattern,**_):
        if pattern=='**/ydental/access':return
        assert pattern=='**/ydental/settlement?notice=*' and '?notice=' in self.url
    def on(self,name,callback):self.listeners[name].append(callback)
    def remove_listener(self,name,callback):self.listeners[name].remove(callback)
    def evaluate(self,script,fields):
        assert "fetch('/ydental/access/action'" in script
        assert fields['token']=='token-'+self.role and fields['revision']==str(self.state.revisions[self.role])
        if "operation:'switch'" in script:
            self.state.revisions[self.role]+=1
            self.state.audit_events['store.switch']+=1
            return {'status':200,'data':{'revision':str(self.state.revisions[self.role])}}
        assert "operation:'grant'" in script and self.role=='manager' and self.state.grant=='write'
        self.state.grant='read';self.state.audit_events['authorization.change']+=1
        return {'status':200,'data':{'revision':str(self.state.revisions[self.role])}}

class Context:
    def __init__(self,state,role):self.state=state;self.role=role
    def route(self,pattern,cb):assert pattern=='**/*'
    def new_page(self):
        page=Page(self.state,self.role);self.state.pages.append(page);return page
    def close(self):pass
class Browser:
    def __init__(self,state):self.state=state;self.i=0
    def new_context(self,**_):
        role=['manager','frontdesk'][self.i];self.i+=1;return Context(self.state,role)
    def close(self):pass
class Playwright:
    def __init__(self,state):self.firefox=type('Firefox',(),{'launch':lambda _,**kw:Browser(state)})()
    def __enter__(self):return self
    def __exit__(self,*_):pass
class Cursor:
    def __init__(self,state):self.state=state;self.query='';self.args=None
    def __enter__(self):return self
    def __exit__(self,*_):pass
    def execute(self,query,args=None):self.query=query;self.args=args
    def fetchone(self):
        if 'SELECT login' in self.query:return ('synthetic-'+str(self.args[0]),)
        if 'ydental_business_date' in self.query:return (date(2026,10,15),)
        raise AssertionError(self.query)
    def fetchall(self):
        if "g.ydental_category='settlement'" in self.query:return [(self.state.grant,)]
        raise AssertionError(self.query)
class Conn:
    def __init__(self,state):self.state=state
    def __enter__(self):return self
    def __exit__(self,*_):pass
    def set_session(self,**kw):assert kw=={'readonly':True}
    def cursor(self):return Cursor(self.state)

def browser_case(root,fault=None):
    root.mkdir(exist_ok=True)
    state=State(fault)
    fixture={'db':web.NAME,'oid':271828,'actors':{'manager':5,'frontdesk':6},'store_id':1}
    with patch.multiple(web,RUN=root,fixture=fixture,dbargs={'password':'FAKE'},
        finance=state.finance,audit=state.audit,sync_playwright=lambda:Playwright(state)), \
        patch.object(web.psycopg2,'connect',side_effect=lambda **kw:Conn(state)), \
        patch.dict(os.environ,{'YDENTAL_UI1_SYNTHETIC_PASSWORD':'FAKE_ONLY'}):
        if fault:
            try:web.run()
            except (RuntimeError,AssertionError,IsADirectoryError):pass
            else:raise AssertionError('fault admitted '+fault)
            assert not (root/'browser-complete.json').exists()
            checks.append('whole_run_'+fault+'_no_complete')
            return
        web.run()
    complete=read_complete(root/'browser-complete.json')
    assert complete['status']=='R7_HTML_DENIAL_LIMITED_PASS'
    assert state.grant=='read' and state.money==0
    assert len(state.requests)==1 and len(state.responses)==1
    events=[json.loads(s) for s in (root/'browser-events.jsonl').read_text().splitlines()]
    assert [e['label'] for e in events]==['login','login','prefilled_form','grant_read',
        'old_page_retained','html_denied','post_invariants','refresh_safe']
    assert events[2]['state']['form_valid'] and events[4]['revision_same']
    assert events[5]['response']['status']==303 and events[5]['feedback_denied']
    assert complete['finance']['money']==0 and complete['audit']['exports']==3
    checks.append('actual_whole_run_native_valid_date_single_post_303_feedback_finance_and_marker')

with tempfile.TemporaryDirectory(prefix='ui1-r7-full-flow-') as tmp:
    root=Path(tmp)
    create_case(root/'create-ok')
    for fault in ('copy','sql','tail'):create_case(root/('create-'+fault),fault)
    # The Fake browser itself enforces HTML5 required: empty input cannot dispatch POST.
    state=State();page=Page(state,'frontdesk');page.goto(web.BASE+'/ydental/settlement')
    form=page.locator('form:has(input[name="operation"][value="close"])')
    assert web.close_form_state(form)['form_valid'] is False
    form.locator('button[type=submit]').click(timeout=5000)
    assert state.requests==[]
    form.locator('input[name="business_date"]').fill('2026-10-15')
    assert web.close_form_state(form)['form_valid'] is True
    form.locator('button[type=submit]').click(timeout=5000)
    assert len(state.requests)==1
    checks.append('fake_native_required_empty_no_post_valid_date_one_post')
    browser_case(root/'browser-ok')
    blocked=root/'browser-event-fail';blocked.mkdir();(blocked/'browser-events.jsonl').mkdir()
    browser_case(blocked,'event_write_failure')
    for fault in ('drop_date_fill','missing_form','missing_date_dom','no_post',
                  'wrong_status','no_feedback','money_change'):
        browser_case(root/('browser-'+fault),fault)
print(json.dumps({'status':'SIMULATED_PASS','checks':checks,'real_create':0,
    'real_odoo':0,'real_firefox':0},indent=2))
