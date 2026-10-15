"""SIMULATED R6 actual create/CLI and whole browser run, with external boundaries faked."""
from contextlib import redirect_stdout
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_ui1_r6_control as control
import s10_ui1_r6_browser as web
from s10_ui1_r2_evidence import read_complete

checks = []

class FakeSocket:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def bind(self, address): assert address == ('127.0.0.1', control.PORT)

class FakeCreateCursor:
    def __init__(self, state): self.state = state
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def execute(self, query):
        assert 'CREATE DATABASE' in str(query)
        self.state['calls'] += 1
        if self.state['fail_create']: raise RuntimeError('simulated CREATE failure')
        self.state['created'] = True

class FakeCreateConnection:
    def __init__(self, state):
        self.state = state
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status': control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self): return FakeCreateCursor(self.state)
    def close(self): pass

def create_case(root, *, fail_copy=False, fail_create=False, bad_oid=False):
    root.mkdir()
    local = root / '.local'; local.mkdir()
    source_run = local / control.SOURCE
    source_fs = source_run / 'data/filestore' / control.SOURCE
    source_fs.mkdir(parents=True)
    data = {'alpha': b'nonempty-R6-input', 'folder/beta': b'another-nonempty-file'}
    expected = {}
    for rel, raw in data.items():
        path = source_fs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected[rel] = {'sha256': hashlib.sha256(raw).hexdigest()}
    (source_run / 'fixture.json').write_text(json.dumps({'db':control.SOURCE,'oid':2100265,'fees':[1,2], 'actors':{'frontdesk':6}}))
    if fail_copy: (source_fs / 'alpha').write_bytes(b'changed-after-manifest')
    run = local / control.NAME
    state = {'created':False,'calls':0,'postcalls':0,'fail_create':fail_create}
    def identity(expect_target=False):
        if expect_target:
            assert state['created']
            state['postcalls'] += 1
            return {'password':'FAKE'}, expected, 314159 if bad_oid and state['postcalls']>1 else 271828
        assert not state['created']
        return {'password':'FAKE'}, expected, None
    with patch.multiple(control, ROOT=root, SOURCE_RUN=source_run, RUN=run, identity=identity), \
         patch.object(control.socket,'socket',return_value=FakeSocket()), \
         patch.object(control.psycopg2,'connect',side_effect=lambda **kw:FakeCreateConnection(state)):
        if fail_copy or fail_create or bad_oid:
            try:
                with redirect_stdout(io.StringIO()): control.dispatch('create')
            except (AssertionError,RuntimeError,ValueError): pass
            else: raise AssertionError('CREATE failure was admitted')
            assert not (run/'create-complete.json').exists()
            assert state['calls'] == (0 if fail_copy else 1)
            checks.append('actual_create_'+('copy' if fail_copy else 'sql' if fail_create else 'tail')+'_failure_closed')
            return
        with redirect_stdout(io.StringIO()): control.dispatch('create')
        assert state['calls']==1 and state['postcalls']==2
        assert read_complete(run/'create-complete.json')['phase']=='VERIFIED'
        assert read_complete(run/'fixture.json')['inherited_from']['oid']==2100265
        assert all((run/'data/filestore'/control.NAME/rel).read_bytes()==raw for rel,raw in data.items())
        checks.append('actual_create_dispatch_copy_sql_marker_tail_success')
        try: control.dispatch('create')
        except (AssertionError, FileExistsError): pass
        else: raise AssertionError('repeat create accepted')
        assert state['calls']==1
        checks.append('repeat_create_closed')
        with patch.object(control,'inherited_baseline',side_effect=RuntimeError('finance drift')):
            try: control.dispatch('serve')
            except RuntimeError: pass
            else: raise AssertionError('HTTP after finance drift')
        assert not (run/'http-r6.attempt.json').exists()
        with patch.object(control,'inherited_baseline',return_value={'same':True}), patch.object(control,'qweb_loaded',return_value=False):
            try: control.dispatch('serve')
            except AssertionError: pass
            else: raise AssertionError('HTTP without QWeb')
        assert not (run/'http-r6.attempt.json').exists()
        try: control.dispatch('unknown')
        except ValueError: pass
        else: raise AssertionError('unknown command accepted')
        checks.append('actual_dispatch_stage_gates_and_unknown_rejected')

class State:
    def __init__(self, fault=None):
        self.fault=fault; self.pages=[]; self.requests=[]; self.permissions={'frontdesk':'write','reader':'read'}
        self.revisions={'manager':10,'frontdesk':20,'reader':30}
        self.store={'manager':1,'frontdesk':1,'reader':1}
        self.money=0; self.exports=3; self.mail=0; self.audit_seq=234
        self.browser=None
    def finance(self, database=web.NAME):
        assert database in (web.NAME,web.SOURCE)
        return {'moves':((1,100),(2,40)), 'receipts':tuple(range(1,9)),
                'native_payments':((1,60),(2,20)), 'money':self.money}
    def audit(self):
        return {'recent':[(self.audit_seq,'synthetic.login',5)],'exports':self.exports,'mail':self.mail,'bus':30,'categories':[('synthetic.login',self.audit_seq)]}

class Response:
    def __init__(self,status=200,headers=None,url='http://127.0.0.1:18275/ydental/settlement'):
        self.status=status; self.headers=headers or {}; self.url=url
        self.request=type('Req',(),{'method':'POST'})()
    def json(self): return {'error':'access_denied'}

class Locator:
    def __init__(self,page,selector): self.page=page; self.selector=selector
    def count(self):
        s=self.selector
        if 'operation' in s and 'switch' in s: return 1
        if 'operation' in s and 'bill' in s: return 0 if self.page.role=='reader' else 1
        if 'operation' in s and 'close' in s: return 1 if self.page.form_available else 0
        if 'data-ui1-feedback' in s: return 1 if self.page.feedback else 0
        return 1
    def locator(self,selector): return Locator(self.page,self.selector+' '+selector)
    def input_value(self):
        if 'csrf_token' in self.selector: return 'own-token-'+self.page.role
        if 'revision' in self.selector: return str(self.page.state.revisions[self.page.role]) if '/ydental/access/action' in self.selector else (self.page.form_revision or str(self.page.state.revisions[self.page.role]))
        raise AssertionError(self.selector)
    def inner_text(self):
        if self.selector=='h1': return '线下结算工作台'
        if 'data-ui1-feedback' in self.selector: return self.page.feedback
        raise AssertionError(self.selector)
    def fill(self,value): self.page.filled[self.selector]=value
    def click(self):
        if self.selector=='button[type=submit]' and not self.page.expecting:
            assert self.page.filled.get('[name=login]') and self.page.filled.get('[name=password]')
            return
        assert self.page.expecting and self.page.form_available
        self.page.state.requests.append({'role':self.page.role,'path':'/ydental/settlement/action','method':'POST','kind':'html'})
        self.page.captured=Response(303,{'location':'/ydental/settlement?notice='+'d'*32,'content-type':'text/html'},
                                    'http://127.0.0.1:18275/ydental/settlement/action')
        self.page.url='http://127.0.0.1:18275/ydental/settlement?notice='+'d'*32
        self.page.feedback='请求未完成，请重试'
        self.page.expecting=False

class ExpectResponse:
    def __init__(self,page,predicate): self.page=page; self.predicate=predicate
    def __enter__(self): self.page.expecting=True; return self
    def __exit__(self,*_):
        assert self.page.captured and self.predicate(self.page.captured)
        self.value=self.page.captured

class Page:
    def __init__(self,state,role):
        self.state=state; self.role=role; self.url=''; self.feedback=''; self.form_available=False
        self.form_revision=None; self.filled={}; self.expecting=False; self.captured=None
    def goto(self,url,**_):
        self.url=url; self.feedback=''
        if '/ydental/settlement' in url:
            self.form_available=self.role!='reader' and self.state.permissions.get(self.role)=='write'
            self.form_revision=str(self.state.revisions[self.role])
            if self.state.fault=='missing_html' and self.role=='frontdesk': self.form_available=False
        return Response(200,url=url)
    def locator(self,selector): return Locator(self,selector)
    def evaluate(self,script,fields):
        if "fetch('/ydental/access/action'" in script:
            if "operation:'switch'" in script:
                assert fields['token']=='own-token-'+self.role and fields['revision']==str(self.state.revisions[self.role])
                self.state.revisions[self.role]+=1
                self.state.store[self.role]=fields['store_id']
                self.state.audit_seq+=1
                return {'status':200,'data':{'revision':str(self.state.revisions[self.role])}}
            if "operation:'grant'" in script:
                assert self.role=='manager' and self.state.store['manager']==1
                self.state.permissions['frontdesk']='read'; self.state.audit_seq+=1
                return {'status':200,'data':{'revision':str(self.state.revisions['manager'])}}
            raise AssertionError('unknown access operation')
        assert "fetch('/ydental/settlement/action'" in script
        assert fields['csrf_token']=='own-token-'+self.role or fields['csrf_token']=='invalid'
        self.state.requests.append({'role':self.role,'path':'/ydental/settlement/action',
            'method':'POST','operation':fields['operation'],'revision':fields['revision'],
            'csrf_valid':fields['csrf_token']!='invalid'})
        if fields['csrf_token']=='invalid': status=400; error=None
        elif fields['revision'] != str(self.state.revisions[self.role]): status=409; error='version_conflict'
        elif self.role=='reader' or self.state.permissions.get(self.role)!='write': status=403; error='access_denied'
        elif fields['operation']=='unknown': status=409; error='unknown_operation'
        else: raise AssertionError('unplanned successful financial operation')
        if self.state.fault=='reader_success' and self.role=='reader': status=200; error=None
        if self.state.fault=='wrong_status' and self.role=='reader': status=409; error='version_conflict'
        if self.state.fault=='missing_sent' and self.role=='reader':
            return {'status':403,'content_type':'application/json','body_class':'json','data':{'error':'access_denied'}}
        if self.state.fault=='money_change' and self.role=='reader': self.state.money+=1
        return {'sent':True,'status':status,'content_type':'application/json' if status!=400 else 'text/html',
                'body_class':'json' if status!=400 else 'html', 'data':{'error':error} if error else None}
    def wait_for_url(self,pattern): assert pattern=='**/ydental/access'
    def wait_for_load_state(self,state): assert state=='domcontentloaded'
    def expect_response(self,predicate): return ExpectResponse(self,predicate)

class API:
    def __init__(self, state,role): self.state=state;self.role=role
    def get(self,url):
        assert '/ydental/settlement/pdf/' in url and self.role=='reader'
        self.state.requests.append({'role':self.role,'path':url.split(':18275')[1],'method':'GET'})
        return Response(403,{'content-type':'application/json'})
class Context:
    def __init__(self,state,role): self.state=state;self.role=role;self.request=API(state,role)
    def route(self,pattern,callback): assert pattern=='**/*'
    def new_page(self):
        page=Page(self.state,self.role);self.state.pages.append(page);return page
    def close(self): pass
class Browser:
    def __init__(self,state): self.state=state;self.i=0
    def new_context(self,**kwargs):
        role=['manager','frontdesk','reader'][self.i];self.i+=1
        return Context(self.state,role)
    def close(self): pass
class FakePlaywright:
    def __init__(self,state): self.firefox=type('Firefox',(),{'launch':lambda _,**kw:Browser(state)})()
    def __enter__(self): return self
    def __exit__(self,*_): pass
class FakeCursor:
    def __init__(self,state): self.state=state;self.query=''
    def __enter__(self): return self
    def __exit__(self,*_): pass
    def execute(self,query,args=None): self.query=query;self.args=args
    def fetchone(self):
        if 'SELECT login' in self.query: return ('synthetic-'+str(self.args[0]),)
        if 'ydental_business_date' in self.query: return ('2026-10-15',)
        raise AssertionError(self.query)
    def fetchall(self):
        if "g.ydental_category='export'" in self.query: return [('export','read')]
        if "g.ydental_category='settlement'" in self.query: return [('read',)]
        raise AssertionError(self.query)
class FakeConn:
    def __init__(self,state):self.state=state
    def __enter__(self):return self
    def __exit__(self,*_):pass
    def set_session(self,**kw): assert kw=={'readonly':True}
    def cursor(self):return FakeCursor(self.state)

def browser_case(root,fault=None):
    root.mkdir(exist_ok=True); state=State(fault)
    fixture={'db':web.NAME,'oid':271828,'actors':{'manager':5,'frontdesk':6,'reader':8},
             'store_id':1,'other_store_id':2,'fees':[1,2]}
    with patch.multiple(web,RUN=root,fixture=fixture,dbargs={'password':'FAKE'},
                        finance=state.finance,audit=state.audit,
                        sync_playwright=lambda:FakePlaywright(state)), \
         patch.object(web.psycopg2,'connect',side_effect=lambda **kw:FakeConn(state)), \
         patch.dict(os.environ,{'YDENTAL_UI1_SYNTHETIC_PASSWORD':'FAKE_ONLY'}):
        if fault:
            try: web.run()
            except (RuntimeError,AssertionError,IsADirectoryError): pass
            else: raise AssertionError('fault did not fail closed: '+fault)
            assert not (root/'browser-complete.json').exists()
            checks.append('whole_run_'+fault+'_failure_no_complete')
            return
        web.run()
    complete=read_complete(root/'browser-complete.json')
    assert complete['status']=='FIREFOX_R6_NEGATIVE_PASS' and complete['finance']['money']==0
    events=[json.loads(line) for line in (root/'browser-events.jsonl').read_text().splitlines()]
    labels=[e['label'] for e in events]
    expected=['login','login','login','negative_request','negative_request','negative_request',
              'negative_request','negative_request','manager_switch_b','manager_switch_a',
              'negative_request','grant_read','negative_request','html_revoked','forged_notice_rejected']
    assert labels==expected,(labels,expected)
    scenarios=[e['scenario'] for e in events if e['label']=='negative_request']
    assert scenarios==['reader_bill','front_unknown','front_bad_csrf','reader_pdf_receipt',
                       'reader_pdf_refund','manager_old_revision','front_revoked_current_revision']
    assert all(e['finance_unchanged'] for e in events if 'finance_unchanged' in e)
    assert len([r for r in state.requests if r['method']=='POST'])==6
    assert any(r['role']=='reader' and r['operation']=='bill' for r in state.requests)
    assert len([r for r in state.requests if r['method']=='GET'])==2
    assert state.permissions['frontdesk']=='read' and state.store['manager']==1
    checks.append('actual_whole_run_all_15_events_6_post_2_pdf_unchanged_and_complete')

with tempfile.TemporaryDirectory(prefix='ui1-r6-full-flow-') as tmp:
    root=Path(tmp)
    create_case(root/'create-pass')
    create_case(root/'create-copy-fail',fail_copy=True)
    create_case(root/'create-sql-fail',fail_create=True)
    create_case(root/'create-tail-fail',bad_oid=True)
    browser_case(root/'browser-pass')
    blocked_events=root/'browser-event-write-fail'
    blocked_events.mkdir()
    (blocked_events/'browser-events.jsonl').mkdir()
    browser_case(blocked_events,'event_write_failure')
    for fault in ('reader_success','wrong_status','missing_sent','money_change','missing_html'):
        browser_case(root/('browser-'+fault),fault)

print(json.dumps({'status':'SIMULATED_PASS','checks':checks,'real_create':0,
                  'real_odoo':0,'real_firefox':0},indent=2))
