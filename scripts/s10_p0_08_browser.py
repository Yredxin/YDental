"""One Firefox; native identity POSTs only, three settlement GETs, no business POST."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

ROOT=Path(__file__).resolve().parents[1]
DEPS=ROOT/'.local/s00-b-deps'
sys.path.insert(0,str(DEPS/'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(DEPS/'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH',str(DEPS/'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE',str(DEPS/'browser-fonts.conf'))
from playwright.sync_api import sync_playwright
import s10_p0_08_control as c
s=c.s
BASE='http://127.0.0.1:'+str(s.PORT)


class GateFailure(AssertionError):
    def __init__(self, code):
        import inspect
        self.failure_code=code
        frame=inspect.currentframe().f_back.f_back
        self.location={'file':Path(frame.f_code.co_filename).name,'line':frame.f_lineno}
        super().__init__(code)


def require(ok,code):
    if not ok:raise GateFailure(code)


LOGIN_FIELDS={'csrf_token','login','password','type','webauthn_response','redirect'}
SWITCH_FIELDS={'csrf_token','operation','store_id','revision'}
ASSETS={
 '/web/assets/ed6b35f/web.material_symbols_outlined.min.woff2',
 '/web/assets/c58ad13/web.odoo_ui_icons.min.woff2',
 '/web/assets/db959f3/web.assets_frontend_minimal.min.js',
 '/web/assets/15f5270/web.assets_frontend.min.css',
 '/web/assets/c5332a1/web.assets_frontend_lazy.min.js'}


def validate_request(method,url,data,actor,ledger,intent=None,headers=None):
    """Native fixed controller + installed web.login/auth_passkey contract N1-N9."""
    headers=headers or {}
    a=urlsplit(url)
    require(a.scheme=='http' and a.netloc=='127.0.0.1:'+str(s.PORT) and not a.fragment,'N1_ORIGIN')
    require(actor in (6,14),'N2_ACTOR')
    q=parse_qs(a.query,keep_blank_values=True)
    if method=='POST':
        require(a.path in ('/web/login','/ydental/access/action'),'N3_POST_PATH')
        require(headers.get('origin')==BASE,'N1_POST_ORIGIN')
        ref=urlsplit(headers.get('referer',''))
        require(ref.scheme=='http' and ref.netloc==a.netloc,'N1_REFERER_ORIGIN')
        require(headers.get('content-type')=='application/x-www-form-urlencoded','N3_CONTENT_TYPE')
        require(intent and intent.get('actor')==actor and intent.get('path')==a.path,'N2_INTENT')
        require(not q,'N3_POST_QUERY')
        fields=LOGIN_FIELDS if a.path=='/web/login' else SWITCH_FIELDS
        require(set(data)==fields,'N4_FIELD_SET')
        require(all(isinstance(v,list) and len(v)==1 for v in data.values()),'N4_FIELD_COUNT')
        require(bool(data['csrf_token'][0]) and s.sha(data['csrf_token'][0].encode())==intent.get('csrf_sha256'),'N5_CSRF')
        if a.path=='/web/login':
            require(ref.path=='/web/login' and parse_qs(ref.query)=={'redirect':['/ydental/access']},'N3_LOGIN_REFERER')
            require(intent['operation']=='native_login','N2_LOGIN_OPERATION')
            require(s.sha(data['login'][0].encode())==intent.get('login_sha256'),'N2_LOGIN_ACTOR')
            require(bool(data['password'][0]) and s.sha(data['password'][0].encode())==intent.get('password_sha256'),'N2_PASSWORD')
            require(data['type']==['password'] and data['webauthn_response']==[''],'N6_PASSWORD_MODE')
            require(data['redirect']==['/ydental/access'],'N6_REDIRECT')
            key=f'login-{actor}'
        else:
            require(ref.path=='/ydental/access' and not ref.query,'N3_SWITCH_REFERER')
            require(intent['operation']=='switch' and data['operation']==['switch'],'N7_SWITCH_OPERATION')
            require(data['store_id']==[str(1 if actor==6 else 3)] and intent.get('store')==(1 if actor==6 else 3),'N7_STORE')
            require(data['revision']==['0'] and intent.get('scope_revision')==0,'N7_REVISION')
            key=f'switch-{actor}'
        require(key not in ledger and len(ledger)<4,'N8_DUPLICATE_POST')
        ledger.add(key)
        return key
    require(method=='GET','N3_METHOD')
    require(a.path in ASSETS|{'/web/login','/ydental/access','/ydental/settlement','/website/translations'},'N9_GET_PATH')
    if a.path=='/web/login':require(q=={'redirect':['/ydental/access']},'N9_LOGIN_QUERY')
    elif a.path=='/ydental/settlement':
        require(q in ({},{'refunds_page':['2']}) and (actor==6 or q=={}),'N9_WORKBENCH_QUERY')
    elif a.path=='/website/translations':require(q=={'hash':[''],'lang':['zh_CN']},'N9_TRANSLATION_QUERY')
    else:require(not q,'N9_RESOURCE_QUERY')
    return None


def validate_identity_response(status,error,url,errors):
    require(error is None and status in (302,303) and not errors,'N0_IDENTITY_RESPONSE_UNKNOWN')
    require(url==BASE+'/ydental/access','N0_IDENTITY_REDIRECT')


def form_structure(form):
    return form.evaluate("""f=>({action:f.getAttribute('action'),method:f.method,
      enctype:f.enctype,controls:Array.from(f.elements).filter(e=>e.name).map(e=>({
        name:e.name,type:e.type,hidden:e.type==='hidden',required:e.required,disabled:e.disabled}))})""")


def validate_identity_dom(structure,login):
    fields=LOGIN_FIELDS if login else SWITCH_FIELDS
    require(structure['action']==('/web/login' if login else '/ydental/access/action'),'D1_FORM_ACTION')
    require(structure['method']=='post' and structure['enctype']=='application/x-www-form-urlencoded','D1_FORM_METHOD')
    controls=structure['controls']
    require({e['name'] for e in controls}==fields and len(controls)==len(fields),'D2_FORM_FIELDS')
    expected={'csrf_token':('hidden',False),'login':('text',True),'password':('password',True),
        'type':('hidden',False),'webauthn_response':('hidden',False),'redirect':('hidden',False)} if login else {
        'csrf_token':('hidden',False),'operation':('hidden',False),'store_id':('select-one',False),'revision':('hidden',False)}
    for e in controls:
        require((e['type'],e['required'])==expected[e['name']] and not e['disabled'],'D2_FORM_CONTROL')
    return True


def failure_record(error,method,url,data,actor,stage,headers,payload):
    a=urlsplit(url)
    known=LOGIN_FIELDS|SWITCH_FIELDS|{'refunds_page','hash','lang'}
    label=lambda k:k if k in known else 'unknown_sha256_'+s.sha(k.encode())[:16]
    return {'failure_code':getattr(error,'failure_code','N0_UNEXPECTED_GATE_EXCEPTION'),
        'actor':actor,'stage':stage,'path':a.path if a.path in ASSETS|{'/web/login','/ydental/access','/ydental/access/action','/ydental/settlement'} else 'unknown_path_sha256_'+s.sha(a.path.encode()),
        'method':method,'contract':'N1-N9/D1-D2','field_counts':{label(k):len(v) for k,v in data.items()},
        'query_keys':sorted(label(k) for k in parse_qs(a.query,keep_blank_values=True)),
        'content_type':headers.get('content-type',''),'payload_sha256':s.sha(payload.encode()),
        'location':getattr(error,'location',{'file':'s10_p0_08_browser.py','line':0}),
        'exception_type':type(error).__name__}


def synthetic_password():
    # Existing P006 synthetic credential; no new credential or plaintext logging.
    import ast
    tree=ast.parse((ROOT/'scripts/s10_p0_06_browser.py').read_text())
    matches=[n.args[0].value for n in ast.walk(tree) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Attribute) and n.func.attr=='fill' and n.args
        and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str)
        and isinstance(n.func.value,ast.Call) and n.func.value.args
        and isinstance(n.func.value.args[0],ast.Constant) and n.func.value.args[0].value=='[name=password]']
    require(len(matches)==1,'N2_EXISTING_CREDENTIAL')
    return matches[0]


def validate_page(dom,facts,actor,selected):
    assert (actor,facts['store']) in ((6,1),(14,3))
    assert dom['status']==200 and dom['main_count']==1 and dom['visible']
    assert dom['revision']=='1' and dom['store_name']==facts['store_name']
    assert dom['errors']==[] and dom['rows']==[{'id':r['id'],'state':r['state'],'amount':r['amount']} for r in facts['rows']]
    a=urlsplit(dom['url']);assert a.path=='/ydental/settlement'
    q=parse_qs(a.query)
    assert q==({'refunds_page':['2']} if facts['page']==2 else {})
    if facts['count']>50:
        assert dom['pagination']==f"共 {facts['count']} 条；第 {facts['page']} 页"
        if facts['page']==1:
            assert dom['next']=='/ydental/settlement?refunds_page=2'
            assert selected['id'] not in [r['id'] for r in dom['rows']]
        else:
            assert dom['prev']=='/ydental/settlement' and dom['next'] is None
            assert {'id':selected['id'],'state':selected['state'],'amount':selected['amount']} in dom['rows']
    else:
        assert actor==14 and dom['pagination'] is None and dom['next'] is None
        assert selected['id'] not in [r['id'] for r in dom['rows']]
    assert selected['id']!=14 and selected['store']==1 and selected['page']==2
    return True


class Browser:
    def __init__(self,pw):
        self.browser=pw.firefox.launch(headless=True)
        self.contexts=[];self.errors=[];self.posts=set();self.get_requests=[]
        self.ledger=[];self.gets=[];self.page_actors={};self.active_intents={};self.active_get=None;self.route_gets=[]
        self.resource_counts={};self.route_index=0;self.response_index=0
        self.baseline=c.load_capture(c.PRIVATE/'clone-snapshot.json')
        self.selected=json.loads(c.PREFLIGHT.read_text())['selection']['selected']

    def close(self):
        for context in self.contexts:context.close()
        self.browser.close()

    def route(self,route,actor):
        req=route.request
        data=parse_qs(req.post_data or '',keep_blank_values=True)
        try:
            require(not self.errors,'N0_ALREADY_STOPPED')
            validate_request(req.method,req.url,data,actor,self.posts,self.active_intents.get(actor),req.headers)
            if req.method=='GET':
                path=urlsplit(req.url).path
                key=(actor,path)
                count=self.resource_counts.get(key,0)+1
                limit=2 if path=='/ydental/access' else (2 if actor==6 else 1) if path=='/ydental/settlement' else 6 if path in ASSETS|{'/website/translations'} else 1
                require(count<=limit and sum(self.resource_counts.values())<90,'N9_GET_BUDGET')
                self.resource_counts[key]=count
            if req.method=='GET' and urlsplit(req.url).path=='/ydental/settlement':
                require(self.active_get and self.active_get['actor']==actor,'N9_GET_INTENT')
                require(len(self.route_gets)<3 and (actor,req.url) not in self.route_gets,'N9_WORKBENCH_BUDGET')
                require(req.url==self.active_get['url'],'N9_GET_INTENT_URL')
                self.route_gets.append((actor,req.url))
            c.save_once(c.PRIVATE/f'route-allowed-{self.route_index}.json',{'actor':actor,'method':req.method,
                'path':urlsplit(req.url).path,'field_counts':{k:len(v) for k,v in data.items()},'payload_sha256':s.sha((req.post_data or '').encode())})
            self.route_index+=1
            route.continue_()
        except Exception as error:
            failure=failure_record(error,req.method,req.url,data,actor,self.active_intents.get(actor,{}).get('operation','GET'),req.headers,req.post_data or '')
            c.save_once(c.PRIVATE/f'route-failure-{len(self.errors)}.json',failure)
            self.errors.append(failure['failure_code'])
            route.abort()

    def note_request(self,actor,request):
        a=urlsplit(request.url)
        self.ledger.append({'actor':actor,'method':request.method,'path':a.path,
                            'payload_sha256':s.sha((request.post_data or '').encode())})
        if request.method=='GET' and a.path=='/ydental/settlement':
            self.get_requests.append({'actor':actor,'url':request.url,'method':'GET'})

    def note_response(self,actor,response):
        try:
            path=urlsplit(response.url).path
            method=response.request.method
            require(response.status in ((302,303) if method=='POST' else (200,)),'N0_HTTP_STATUS')
            if method=='POST':require(response.headers.get('location')=='/ydental/access','N0_HTTP_REDIRECT')
            if path in ASSETS:
                row=next(a for a in json.loads(c.PREFLIGHT.read_text())['native_contract']['existing_assets'] if a['url']==path)
                body=response.body()
                require(len(body)==row['file_size'] and s.sha(body)==row['sha256'],'N0_ASSET_RESPONSE_HASH')
            c.save_once(c.PRIVATE/f'response-{self.response_index}.json',{'actor':actor,'path':path,'method':method,'status':response.status})
            self.response_index+=1
        except Exception as error:
            code=getattr(error,'failure_code','N0_RESPONSE_OBSERVATION_UNKNOWN')
            c.save_once(c.PRIVATE/f'response-failure-{len(self.errors)}.json',{'failure_code':code,'actor':actor,
                'method':response.request.method,'path_sha256':s.sha(urlsplit(response.url).path.encode()),'status':response.status})
            self.errors.append(code)

    def scope(self,page,actor,store):
        cookies=page.context.cookies(BASE)
        sid=next(x['value'] for x in cookies if x['name']=='session_id')
        digest=hashlib.sha256(sid[:42].encode()).hexdigest()
        observed=c.capture(s.TARGET)
        rows=[r for r in observed['all']['rows']['ydental_access_session'].values() if r['ydental_key_hash']==digest]
        assert len(rows)==1 and rows[0]['ydental_user_id']==actor
        assert rows[0]['ydental_store_id']==store and rows[0]['ydental_revision']==(0 if store is None else 1)
        c.web_diff(self.baseline,observed,gets=self.gets)
        return rows[0]

    def identity_post(self,page,form,actor,stage,intent):
        before=c.capture(s.TARGET)
        c.web_diff(self.baseline,before,gets=self.gets)
        structure=form_structure(form)
        c.save_once(c.PRIVATE/f'{stage}-form-structure.json',structure)
        validate_identity_dom(structure,intent['operation']=='native_login')
        csrf=form.locator('input[name=csrf_token]').input_value()
        assert csrf and form.evaluate('(f)=>f.checkValidity()')
        intent.update({'actor':actor,'csrf_sha256':hashlib.sha256(csrf.encode()).hexdigest(),
                       'oid':c.verify_target(),'utc':datetime.now(timezone.utc).isoformat()})
        c.save_once(c.PRIVATE/f'{stage}-intent.json',intent)
        self.active_intents[actor]=intent
        try:
            with page.expect_response(lambda r:r.request.method=='POST' and urlsplit(r.url).path==intent['path']) as pending:
                form.locator('button[type=submit]').click()
            page.wait_for_url('**/ydental/access')
            status=pending.value.status
            error=None
        except Exception as exc:
            status=None;error=type(exc).__name__
        after=c.capture(s.TARGET)
        c.save_once(c.PRIVATE/f'{stage}-observed.json',{'http':status,'url':page.url,'error':error,'snapshot':after})
        validate_identity_response(status,error,page.url,self.errors)
        c.web_diff(self.baseline,after,gets=self.gets)
        self.active_intents.pop(actor)
        return after

    def login(self,actor,store):
        assert (actor,store) in ((6,1),(14,3))
        with s.connect(s.TARGET) as conn,conn.cursor() as cur:
            cur.execute('SELECT login,active FROM res_users WHERE id=%s',(actor,))
            login,active=cur.fetchone();assert active
        context=self.browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
        self.contexts.append(context)
        context.route('**/*',lambda route:self.route(route,actor))
        context.on('request',lambda req:self.note_request(actor,req))
        context.on('response',lambda resp:self.note_response(actor,resp))
        page=context.new_page();self.page_actors[page]=actor
        page.on('pageerror',lambda exc:self.errors.append('N0_PAGE_ERROR'))
        page.on('download',lambda download:self.errors.append('FORBIDDEN_DOWNLOAD'))
        response=page.goto(BASE+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
        assert response.status==200 and not self.errors
        page.locator('[name=login]').fill(login)
        password=synthetic_password()
        page.locator('[name=password]').fill(password)
        form=page.locator('form[action="/web/login"]')
        assert form.count()==1
        self.identity_post(page,form,actor,f'login-{actor}',{'operation':'native_login','login_sha256':s.sha(login.encode()),'password_sha256':s.sha(password.encode()),'path':'/web/login'})
        scope=self.scope(page,actor,None)
        form=page.locator('form[action="/ydental/access/action"]:has(input[name=operation][value="switch"])')
        assert form.count()==1
        form.locator('select[name=store_id]').select_option(str(store))
        assert form.locator('input[name=revision]').input_value()==str(scope['ydental_revision'])
        self.identity_post(page,form,actor,f'switch-{actor}',{'operation':'switch','store':store,
            'scope_session_id':scope['id'],'scope_revision':scope['ydental_revision'],'path':'/ydental/access/action'})
        self.scope(page,actor,store)
        return page

    def read_dom(self,page,status):
        main=page.locator('main.o_ydental_settlement')
        section=main.locator('section').filter(has=page.locator('h2',has_text='线下付款与退款'))
        assert section.count()==1
        rows=section.locator('a[href^="/ydental/settlement/pdf/refund/"]').evaluate_all('''anchors=>anchors.map(a=>{
            const p=a.closest('p'),spans=p.querySelectorAll(':scope > span');
            if(spans.length!==3)throw Error('refund row shape');
            const id=Number(spans[0].textContent.trim());
            if(a.getAttribute('href')!=='/ydental/settlement/pdf/refund/'+id)throw Error('refund ID link mismatch');
            return {id,state:spans[2].textContent.trim(),amount:Number(spans[1].textContent.trim()).toFixed(2)};
        })''')
        # Refund pagination is the final nav in this section, after the refund rows.
        nav=section.locator('nav[aria-label="分页"]').last
        pagination=None;prev=None;nextlink=None
        if nav.count():
            text=nav.locator(':scope > span').inner_text()
            if re.fullmatch(r'共 63 条；第 [12] 页',text):
                pagination=text
                pl=nav.locator('a',has_text='上一页');nl=nav.locator('a',has_text='下一页')
                prev=pl.get_attribute('href') if pl.count() else None
                nextlink=nl.get_attribute('href') if nl.count() else None
        return {'status':status,'main_count':main.count(),'visible':main.is_visible(),
            'revision':main.get_attribute('data-revision'),'store_name':main.locator(':scope > p strong').first.inner_text(),
            'rows':rows,'pagination':pagination,'prev':prev,'next':nextlink,'url':page.url,'errors':self.errors.copy()}

    def get(self,page,stage,number,click=None):
        actor=self.page_actors[page];store=1 if actor==6 else 3
        scope=self.scope(page,actor,store)
        facts=c.refund_sql(s.TARGET,store,number)
        expected=json.loads(c.PREFLIGHT.read_text())['refund_pages'][f'{store}-{number}']
        assert c.equivalent(facts,expected),'refund SQL drift before GET'
        before=c.capture(s.TARGET);offset=len(self.get_requests)
        url=BASE+'/ydental/settlement'+('?refunds_page=2' if number==2 else '')
        intent={'actor':actor,'store':store,'method':'GET','url':url,'scope_session_id':scope['id'],
                'scope_revision':scope['ydental_revision'],'oid':c.verify_target()}
        c.save_once(c.PRIVATE/f'{stage}-intent.json',intent)
        self.active_get=intent
        try:
            if click is None:response=page.goto(url,wait_until='domcontentloaded')
            else:
                with page.expect_navigation(wait_until='domcontentloaded') as pending:click.click()
                response=pending.value
            status=response.status;error=None
        except Exception as exc:status=None;error=type(exc).__name__
        after=c.capture(s.TARGET)
        c.save_once(c.PRIVATE/f'{stage}-observed.json',{'http':status,'url':page.url,'error':error,'snapshot':after})
        assert error is None and status==200 and not self.errors,'GET response unknown/invalid; STOP'
        requests=self.get_requests[offset:];assert len(requests)==1 and requests[0]['url']==url
        rows=after['all']['rows']['ydental_access_audit']
        ids=sorted(i for i in set(rows)-set(before['all']['rows']['ydental_access_audit']))
        entry={'actor':actor,'store':store,'method':'GET','status':status,'path':'/ydental/settlement',
            'url':url,'audit_ids':ids,'invoice_ids':[rows[i]['ydental_target_id'] for i in ids]}
        self.gets.append(entry)
        c.save_once(c.PRIVATE/f'get-binding-{len(self.gets)}.json',entry)
        c.web_diff(before,after,gets=[entry]);c.web_diff(self.baseline,after,gets=self.gets)
        dom=self.read_dom(page,status)
        validate_page(dom,facts,actor,self.selected)
        assert c.refund_sql(s.TARGET,store,number)==facts
        png=c.PRIVATE/f'{stage}.png';assert not png.exists()
        page.screenshot(path=str(png),full_page=True);os.chmod(png,0o600)
        c.save_once(c.PRIVATE/f'{stage}-page.json',{'dom':dom,'independent_sql':facts,
            'screenshot_sha256':s.file_sha(png),'scope_session_id':scope['id'],'scope_revision':scope['ydental_revision']})
        self.active_get=None
        return dom


def main():
    c.verify_target()
    with sync_playwright() as pw:
        browser=Browser(pw)
        try:
            c.web_diff(browser.baseline,c.capture(s.TARGET))
            user6=browser.login(6,1)
            browser.get(user6,'user6-refunds-page1',1)
            link=user6.locator('a[href="/ydental/settlement?refunds_page=2"]',has_text='下一页')
            assert link.count()==1 and link.is_visible()
            browser.get(user6,'user6-refunds-page2',2,click=link)
            user14=browser.login(14,3)
            browser.get(user14,'user14-store3-list',1)
            assert browser.posts=={'login-6','switch-6','login-14','switch-14'}
            assert len(browser.gets)==3 and not browser.errors
            c.save_once(c.PRIVATE/'get-bindings.json',browser.gets)
            c.save_once(c.PRIVATE/'positive-complete.json',{'selected':browser.selected,
                'settlement_POST':0,'page_errors':browser.errors,'identity_POSTs':4,'settlement_GETs':3})
        finally:
            c.save_once(c.PRIVATE/'browser-request-ledger.json',{'posts':sorted(browser.posts),
                'requests':browser.ledger,'gets':browser.get_requests,'errors':browser.errors})
            browser.close()


if __name__=='__main__':main()
