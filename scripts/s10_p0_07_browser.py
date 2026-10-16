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
import s10_p0_07_control as c
s=c.s
BASE='http://127.0.0.1:'+str(s.PORT)


def validate_request(method,url,data,actor,ledger,intent=None):
    """Called before every real network request, also by the full offline pipeline."""
    a=urlsplit(url)
    assert a.scheme=='http' and a.hostname=='127.0.0.1' and a.port==s.PORT
    assert actor in (6,14)
    if method=='POST':
        assert a.path in ('/web/login','/ydental/access/action'), 'ALL_SETTLEMENT_POST_FORBIDDEN'
        assert intent and intent['actor']==actor and intent['csrf_sha256']
        assert data.get('csrf_token') and hashlib.sha256(data['csrf_token'][0].encode()).hexdigest()==intent['csrf_sha256']
        assert not a.query
        if a.path=='/web/login':
            assert intent['operation']=='native_login' and data['login']==[intent['login']]
            assert data['password'] and data['redirect']==['/ydental/access']
            assert set(data)<=set(('csrf_token','login','password','redirect','type'))
            key=f'login-{actor}'
        else:
            assert intent['operation']=='switch' and data['operation']==['switch']
            assert data['store_id']==[str(1 if actor==6 else 3)]
            assert data['revision']==[str(intent['scope_revision'])]
            assert set(data)=={'csrf_token','operation','store_id','revision'}
            key=f'switch-{actor}'
        assert key not in ledger,('duplicate_identity_POST',key)
        assert len(ledger)<4
        ledger.add(key)
        return key
    assert method=='GET'
    assert a.path in ('/web/login','/ydental/access','/ydental/settlement','/website/translations') or re.fullmatch(r'/web/assets/[0-9a-f]{7}/web\.[A-Za-z0-9_]+\.min\.(?:css|js|woff2)',a.path),('forbidden_GET',a.path)
    if a.path=='/ydental/settlement':
        q=parse_qs(a.query,keep_blank_values=True)
        assert q in ({},{'refunds_page':['2']})
        assert actor==6 or q=={}
    return None


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
        self.baseline=c.load_capture(c.PRIVATE/'clone-snapshot.json')
        self.selected=json.loads(c.PREFLIGHT.read_text())['selection']['selected']

    def close(self):
        for context in self.contexts:context.close()
        self.browser.close()

    def route(self,route,actor):
        req=route.request
        try:
            key=validate_request(req.method,req.url,parse_qs(req.post_data or '',keep_blank_values=True),actor,self.posts,self.active_intents.get(actor))
            if req.method=='GET' and urlsplit(req.url).path=='/ydental/settlement':
                assert self.active_get and self.active_get['actor']==actor
                assert len(self.route_gets)<3
                assert (actor,req.url) not in self.route_gets
                assert req.url==self.active_get['url']
                self.route_gets.append((actor,req.url))
            route.continue_()
        except Exception as error:
            self.errors.append('ROUTE_STOP '+type(error).__name__+': '+str(error))
            route.abort()

    def note_request(self,actor,request):
        # Store only hashes of native identity payloads; never public credentials/cookies.
        self.ledger.append({'actor':actor,'method':request.method,'url':request.url,
                            'payload_sha256':hashlib.sha256((request.post_data or '').encode()).hexdigest()})
        if request.method=='GET' and urlsplit(request.url).path=='/ydental/settlement':
            self.get_requests.append({'actor':actor,'url':request.url,'method':'GET'})

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
            status=None;error=type(exc).__name__+': '+str(exc)[:200]
        after=c.capture(s.TARGET)
        c.save_once(c.PRIVATE/f'{stage}-observed.json',{'http':status,'url':page.url,'error':error,'snapshot':after})
        assert error is None and status in (302,303) and not self.errors,'identity response unknown/invalid; STOP'
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
        page=context.new_page();self.page_actors[page]=actor
        page.on('pageerror',lambda exc:self.errors.append(str(exc)))
        page.on('download',lambda download:self.errors.append('FORBIDDEN_DOWNLOAD'))
        response=page.goto(BASE+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
        assert response.status==200 and not self.errors
        page.locator('[name=login]').fill(login)
        page.locator('[name=password]').fill('s05-test-password')
        form=page.locator('form[action="/web/login"]')
        assert form.count()==1
        self.identity_post(page,form,actor,f'login-{actor}',{'operation':'native_login','login':login,'path':'/web/login'})
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
        except Exception as exc:status=None;error=type(exc).__name__+': '+str(exc)[:200]
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
        c.web_diff(before,after,gets=self.gets);c.web_diff(self.baseline,after,gets=self.gets)
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
