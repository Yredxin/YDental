"""One Firefox session for close 9; refund 14 is permanently read only."""

from datetime import datetime, timezone
import hashlib
from html import escape
import json
import os
from pathlib import Path
import secrets
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT/'.local/s00-b-deps'
sys.path.insert(0,str(DEPS/'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(DEPS/'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH',str(DEPS/'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE',str(DEPS/'browser-fonts.conf'))
from playwright.sync_api import sync_playwright

from s10_p0_06_control import PRIVATE, save_once, verify_target, web_diff, capture, load_capture, ROOT as CONTROL_ROOT
from s10_p0_06_snapshot import TARGET, TARGET_RUN, PORT, connect

BASE = 'http://127.0.0.1:'+str(PORT)


def validate_form(fields, operation, record):
    assert fields['action'] == '/ydental/settlement/action'
    assert fields['method'] == 'post' and fields['visible'] and fields['valid']
    assert fields['output'] == 'html' and fields['csrf'] and fields['key']
    assert fields['revision_match'] and fields['reason']
    assert fields['record'] == str(record)
    assert fields['operation'] == operation == 'unlock' and record == 9
    assert fields['button_enabled']
    return True


def validate_response(response, operation, record, *, accepted):
    assert response['method'] == 'POST' and response['path'] == '/ydental/settlement/action'
    assert response['content_type'].startswith('application/x-www-form-urlencoded')
    assert response['post']['operation'] == [operation]
    assert response['post']['output'] == ['html']
    assert response['post']['close_id'] == [str(record)]
    assert response['post']['csrf_token'] and response['post']['revision'] and response['post']['key']
    if accepted:
        assert response['status'] == 303 and response['location_path'] == '/ydental/settlement'
        assert response['notice'] and response['feedback'] == '操作已受理，请核对下方业务记录。'
    else:
        assert response['status'] == 303 and response['notice']
        assert response['server_denial_log']
        assert response['feedback'] == '请求未完成，请核对权限、门店或输入后重试。' or (
            response['feedback'] is None and response['landing_status'] in (403, 404))
    return True


class Browser:
    def __init__(self, playwright):
        self.browser = playwright.firefox.launch(headless=True)
        self.contexts = []
        self.errors = []
        self.sent = set()
        self.page_users = {}
        self.gets = []
        self.baseline = None
        self.requests = []
        self.route_posts = set()

    def close(self):
        for context in self.contexts:
            context.close()
        self.browser.close()

    def route(self, route, actor):
        request = route.request
        address = urlsplit(request.url)
        try:
            assert address.hostname == '127.0.0.1' and address.port == PORT
            if request.method == 'POST':
                data = parse_qs(request.post_data or '',keep_blank_values=True)
                if address.path == '/web/login':
                    name = f'login-{actor}'
                elif address.path == '/ydental/access/action':
                    assert data['operation'] == ['switch']
                    assert data['store_id'] == [str(3 if actor == 14 else 1)]
                    name = f'switch-{actor}'
                else:
                    assert address.path == '/ydental/settlement/action'
                    assert data['operation'] == ['unlock'] and data['close_id'] == ['9']
                    name = 'deny-user14' if actor == 14 else 'unlock-user6'
                    intent = json.loads((PRIVATE/f'{name}-intent.json').read_text())
                    assert data['key'] == [intent['key']] and data['revision'] == [intent['revision']]
                    assert data['reason'] == [intent['reason']] and data['output'] == ['html']
                    assert hashlib.sha256(data['csrf_token'][0].encode()).hexdigest() == intent['csrf_sha256']
                assert actor in (6,14) and (PRIVATE/f'{name}-intent.json').exists()
                assert name not in self.route_posts, ('duplicate native POST',name)
                self.route_posts.add(name)
            route.continue_()
        except Exception as error:
            self.errors.append('ROUTE_STOP: '+str(error))
            route.abort()

    def note_request(self, actor, request):
        if request.method=='GET' and urlsplit(request.url).path=='/ydental/settlement':
            self.requests.append({'actor':actor,'method':'GET','url':request.url})

    def login(self, user_id, store_id):
        assert (user_id,store_id) in ((14,3),(6,1))
        with connect(TARGET) as conn, conn.cursor() as cur:
            cur.execute('SELECT login,active FROM res_users WHERE id=%s',(user_id,))
            login, active = cur.fetchone()
        assert active
        context = self.browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
        context.route('**/*',lambda route:self.route(route,user_id))
        context.on('request',lambda request:self.note_request(user_id,request))
        page = context.new_page()
        page.on('pageerror',lambda error:self.errors.append(str(error)))
        self.contexts.append(context); self.page_users[page] = user_id
        response = page.goto(BASE+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
        assert response.status == 200
        page.locator('[name=login]').fill(login)
        page.locator('[name=password]').fill('s05-test-password')
        before = capture(TARGET)
        save_once(PRIVATE/f'login-{user_id}-intent.json',{'actor':user_id,'operation':'native_login',
            'oid':verify_target(),'utc':datetime.now(timezone.utc).isoformat()})
        with page.expect_response(lambda r:r.request.method=='POST' and urlsplit(r.url).path=='/web/login') as pending:
            page.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        after = capture(TARGET)
        save_once(PRIVATE/f'login-{user_id}-observed.json',{'http':pending.value.status,
            'url':page.url,'snapshot':after})
        assert pending.value.status in (302,303) and not self.errors
        web_diff(self.baseline,after,gets=self.gets)
        switch = page.locator('form[action="/ydental/access/action"]:has(input[name=operation][value="switch"])')
        assert switch.count() == 1
        switch.locator('select[name=store_id]').select_option(str(store_id))
        assert switch.evaluate('(f)=>f.checkValidity()')
        before=after
        save_once(PRIVATE/f'switch-{user_id}-intent.json',{'actor':user_id,'store':store_id,
            'operation':'switch','oid':verify_target(),'utc':datetime.now(timezone.utc).isoformat()})
        with page.expect_response(lambda r:r.request.method=='POST' and urlsplit(r.url).path=='/ydental/access/action') as pending:
            switch.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        after=capture(TARGET)
        save_once(PRIVATE/f'switch-{user_id}-observed.json',{'http':pending.value.status,
            'url':page.url,'snapshot':after})
        assert pending.value.status in (302,303) and not self.errors
        web_diff(self.baseline,after,gets=self.gets)
        return page

    def get(self, page, stage, *, click=None):
        before=capture(TARGET)
        offset=len(self.requests)
        save_once(PRIVATE/f'{stage}-intent.json',{'actor':self.page_users[page],
            'operation':'native_workbench_GET','oid':verify_target()})
        if click is None:
            response=page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded')
        else:
            with page.expect_navigation(wait_until='domcontentloaded') as pending:
                click.click()
            response=pending.value
        after=capture(TARGET)
        save_once(PRIVATE/f'{stage}-observed.json',{'http':response.status,'url':page.url,'snapshot':after})
        self.bind_get(before,after,self.page_users[page],response.status,offset)
        web_diff(before,after,gets=self.gets)
        assert response.status==200 and not self.errors
        return response

    def bind_get(self,before,after,actor,status,offset):
        requests=self.requests[offset:]
        assert len(requests)==1 and requests[0]['actor']==actor and status==200
        table='ydental_access_audit'
        rows=after['all']['rows'][table]
        ids=sorted(i for i in set(rows)-set(before['all']['rows'][table])
            if rows[i]['ydental_event']=='settlement.invoice_view')
        entry={'actor':actor,'store':3 if actor==14 else 1,'method':'GET','status':status,
            'path':'/ydental/settlement','url':requests[0]['url'],
            'audit_ids':ids,'invoice_ids':[rows[i]['ydental_target_id'] for i in ids]}
        self.gets.append(entry)
        save_once(PRIVATE/f'get-binding-{len(self.gets)}.json',entry)
        return entry

    def page_two(self,page,kind,record):
        assert kind=='closes' and record==9
        self.get(page,'user6-workbench-first')
        link=page.locator('a[href*="closes_page=2"]:has-text("下一页")')
        assert link.count()==1 and link.is_visible()
        href=link.get_attribute('href')
        assert urlsplit(href).path=='/ydental/settlement'
        assert parse_qs(urlsplit(href).query).get('closes_page')==['2']
        self.get(page,'user6-closes-page2',click=link)
        assert '日结 9 /' in page.locator('main.o_ydental_settlement').inner_text()
        png=PRIVATE/'closes-page2.png';assert not png.exists()
        page.screenshot(path=str(png),full_page=True);os.chmod(png,0o600)
        save_once(PRIVATE/'closes-page2.json',{'href':href,'record':9,
            'screenshot_sha256':hashlib.sha256(png.read_bytes()).hexdigest()})
        return page

    def form(self,page,operation,record,reason):
        assert operation == 'unlock' and record == 9
        field = 'close_id'
        selector = ('form[action="/ydental/settlement/action"]:has(input[name=close_id]'
                    '[value="9"]):has(input[name=operation][value="unlock"])')
        form = page.locator(selector)
        assert form.count() == 1
        form.locator('input[name=reason]').fill(reason)
        fields = {'action':form.get_attribute('action'),'method':form.get_attribute('method'),
            'visible':form.is_visible(),'valid':form.evaluate('(f)=>f.checkValidity()'),
            'output':form.locator('input[name=output]').input_value(),
            'csrf':bool(form.locator('input[name=csrf_token]').input_value()),
            'key':bool(form.locator('input[name=key]').input_value()),
            'revision_match':form.locator('input[name=revision]').input_value()==
                page.locator('main.o_ydental_settlement').get_attribute('data-revision'),
            'reason':bool(form.locator('input[name=reason]').input_value()),
            'record':form.locator('input[name='+field+']').input_value(),
            'operation':form.locator('input[name=operation]').input_value(),
            'button_enabled':form.locator('button[type=submit]').is_enabled()}
        validate_form(fields,operation,record)
        return form,fields

    def submit(self,page,form,operation,record):
        guard_send(self.sent, self.page_users[page], operation, record)
        with page.expect_response(lambda r:r.request.method=='POST' and
                urlsplit(r.url).path=='/ydental/settlement/action') as pending:
            with page.expect_navigation(wait_until='domcontentloaded') as navigation:
                assert operation == 'unlock' and record == 9
                form.locator('button[type=submit]').click()
        response = pending.value
        request = response.request
        data = parse_qs(request.post_data or '',keep_blank_values=True)
        location = urlsplit(response.headers.get('location',''))
        feedback = page.locator('[data-ui1-feedback="1"]')
        return {'method':request.method,'path':urlsplit(response.url).path,
            'content_type':request.headers.get('content-type',''),
            'post':{key:data.get(key,[]) for key in ('operation','output','close_id',
                'csrf_token','revision','key','reason')},'status':response.status,
            'location_path':location.path,'notice':bool(parse_qs(location.query).get('notice')),
            'landing_status':navigation.value.status,
            'feedback':feedback.inner_text() if feedback.count()==1 else None}


def guard_send(ledger, user_id, operation, record):
    assert user_id in (6,14) and operation == 'unlock' and record == 9
    key = (user_id, operation, record)
    assert key not in ledger, ('duplicate_post', key)
    ledger.add(key)


def observe_once(browser, page, form, stage, actor, store, reason, baseline, *, accepted=False):
    """Persist intent, send one native HTML request, persist independent observation, then assert."""
    before = capture(TARGET)
    web_diff(baseline, before, gets=browser.gets)
    key = form.locator('input[name=key]').input_value()
    revision = form.locator('input[name=revision]').input_value()
    csrf = form.locator('input[name=csrf_token]').input_value()
    assert key and revision and csrf and reason
    cookies=page.context.cookies(BASE)
    sid=next(x['value'] for x in cookies if x['name']=='session_id')
    session_hash=hashlib.sha256(sid[:42].encode()).hexdigest()
    sessions=[r for r in before['all']['rows']['ydental_access_session'].values() if r['ydental_key_hash']==session_hash]
    assert len(sessions)==1 and sessions[0]['ydental_user_id']==actor
    assert sessions[0]['ydental_store_id']==store and str(sessions[0]['ydental_revision'])==revision
    assert before['all']['rows']['ydental_settlement_close'][9]['ydental_state']=='confirmed'
    assert store==(1 if accepted else 3) and actor==(6 if accepted else 14)
    assert not any(r['ydental_key'] == key for r in before['all']['rows']['ydental_settlement_receipt'].values())
    if accepted:
        prior=json.loads((PRIVATE/'deny-user14-intent.json').read_text())
        assert prior['key'] != key and (PRIVATE/'deny-user14-gate.json').exists()
    log_path=TARGET_RUN/'http.log'
    log_offset=log_path.stat().st_size
    intent = {'stage':stage,'operation':'unlock','close_id':9,'actor':actor,'store':store,
              'key':key,'reason':reason,'revision':revision,'csrf_sha256':hashlib.sha256(csrf.encode()).hexdigest(),
              'oid':verify_target(),'utc':datetime.now(timezone.utc).isoformat(),
              'scope_session_id':sessions[0]['id'],'scope_revision':sessions[0]['ydental_revision'],
              'model_expected':('accepted_latest_confirmed_store1' if accepted else 'AccessError_confirmed_close_store1_ne_scope_store3')}
    save_once(PRIVATE/f'{stage}-intent.json',intent)
    get_offset=len(browser.requests)
    try:
        response = browser.submit(page,form,'unlock',9)
        response_error = None
    except Exception as error:
        response = None
        response_error = type(error).__name__ + ': ' + str(error)[:220]
    if response is not None:
        with log_path.open('rb') as stream:
            stream.seek(log_offset)
            log_delta=stream.read().decode(errors='replace')
        response['server_denial_log']=(f'actor={actor} action=settlement.action result=denied' in log_delta)
    save_once(PRIVATE/f'{stage}-response.json',{'response':response,'error':response_error})
    after = capture(TARGET)
    save_once(PRIVATE/f'{stage}-snapshot.json',after)
    save_once(PRIVATE/f'{stage}-observed.json', {'stage':stage,'response':response,
        'response_error':response_error,'before_table_signatures':before['all']['signatures'],
        'after_table_signatures':after['all']['signatures'],
        'before_close9':before['all']['rows']['ydental_settlement_close'][9],
        'after_close9':after['all']['rows']['ydental_settlement_close'][9],
        'before_mutex':before['all']['rows']['ydental_settlement_mutex'],
        'after_mutex':after['all']['rows']['ydental_settlement_mutex'],
        'new_receipt_ids': sorted(set(after['all']['rows']['ydental_settlement_receipt'])-
                                  set(before['all']['rows']['ydental_settlement_receipt'])),
        'new_audit_ids':sorted(set(after['all']['rows']['ydental_access_audit'])-
                               set(before['all']['rows']['ydental_access_audit']))})
    if response_error:
        raise RuntimeError('COMMIT_UNKNOWN: '+stage+'; request was not retried')
    browser.bind_get(before,after,actor,response['landing_status'],get_offset)
    validate_response(response,'unlock',9,accepted=accepted)
    assert response['post']['key'] == [key] and response['post']['revision'] == [revision]
    assert response['post']['reason'] == [reason]
    assert len(response['post']['csrf_token']) == 1 and response['post']['csrf_token'][0] == csrf
    assert not browser.errors
    gate = web_diff(before,after,unlock=accepted,intent=intent if accepted else None,
                    denied_actor=None if accepted else actor, gets=browser.gets)
    save_once(PRIVATE/f'{stage}-gate.json',gate)
    return after


def stable_cross_form(page, reason):
    original=page.locator('form[action="/ydental/settlement/action"]:has('
        'input[name=close_id][value="63"]):has(input[name=operation][value="unlock"])')
    assert original.count()==1 and original.is_visible()
    handle=original.element_handle()
    original.evaluate('(f)=>{f.dataset.p006Form="cross"}')
    form=page.locator('form[data-p006-form="cross"]')
    assert form.count()==1 and form.evaluate('(f,h)=>f===h',handle)
    hidden={name:form.locator('input[name='+name+']').input_value()
        for name in ('csrf_token','revision','key','output','operation')}
    assert form.locator('input[name=close_id]').input_value()=='63'
    form.locator('input[name=close_id]').evaluate('(el)=>{el.value="9"}')
    form.locator('input[name=reason]').fill(reason)
    assert form.count()==1 and form.evaluate('(f,h)=>f===h',handle)
    assert all(form.locator('input[name='+name+']').input_value()==value for name,value in hidden.items())
    fields=read_fields(page,form)
    validate_form(fields,'unlock',9)
    return form,fields


def read_fields(page,form):
    return {'action':form.get_attribute('action'),'method':form.get_attribute('method'),
        'visible':form.is_visible(),'valid':form.evaluate('(f)=>f.checkValidity()'),
        'output':form.locator('input[name=output]').input_value(),
        'csrf':bool(form.locator('input[name=csrf_token]').input_value()),
        'key':bool(form.locator('input[name=key]').input_value()),
        'revision_match':form.locator('input[name=revision]').input_value()==
            page.locator('main.o_ydental_settlement').get_attribute('data-revision'),
        'reason':bool(form.locator('input[name=reason]').input_value()),
        'record':form.locator('input[name=close_id]').input_value(),
        'operation':form.locator('input[name=operation]').input_value(),
        'button_enabled':form.locator('button[type=submit]').is_enabled()}


def negative_cross_store(browser,baseline):
    page=browser.login(14,3)
    browser.get(page,'user14-workbench-first')
    reason='P0-06 synthetic cross-store unlock denial'
    form,fields=stable_cross_form(page,reason)
    save_once(PRIVATE/'cross-form-stable.json',{'original':63,'target':9,'same_dom_node':True,'fields':fields})
    return observe_once(browser,page,form,'deny-user14',14,3,reason,baseline)


def main():
    verify_target()
    assert (PRIVATE/'clone-snapshot.json').exists() and (PRIVATE/'http-ready.json').exists()
    baseline=load_capture(PRIVATE/'clone-snapshot.json')
    initial=capture(TARGET)
    web_diff(baseline,initial)
    save_once(PRIVATE/'web-baseline.json',initial)
    with sync_playwright() as playwright:
        browser=Browser(playwright)
        browser.baseline=baseline
        try:
            # A must pass all response, audit and financial gates before B starts.
            after_user14=negative_cross_store(browser,initial)
            user6=browser.login(6,1)
            browser.page_two(user6,'closes',9)
            reason='P0-06 synthetic finance unlock review'
            # A new read-only check freezes the exact state before the sole permitted success POST.
            pre_unlock=capture(TARGET)
            web_diff(initial,pre_unlock,gets=browser.gets)
            assert pre_unlock['all']['rows']['ydental_settlement_close'][9]['ydental_state']=='confirmed'
            assert pre_unlock['all']['rows']['ydental_settlement_refund'][14]==baseline['all']['rows']['ydental_settlement_refund'][14]
            assert pre_unlock['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision']==243
            assert set(pre_unlock['all']['rows']['ydental_settlement_receipt'])==set(baseline['all']['rows']['ydental_settlement_receipt'])
            form,fields=browser.form(user6,'unlock',9,reason)
            assert fields['revision_match']
            final=observe_once(browser,user6,form,'unlock-user6',6,1,reason,pre_unlock,accepted=True)
            cumulative=web_diff(baseline,final,unlock=True,intent=json.loads((PRIVATE/'unlock-user6-intent.json').read_text()),gets=browser.gets)
            save_once(PRIVATE/'get-bindings.json',browser.gets)
            save_once(PRIVATE/'cumulative-gate.json',cumulative)
            save_once(PRIVATE/'positive-complete.json',{'close9':'unlocked','refund14':'rejected',
                'oid':verify_target(),'negative_posts':1,'unlock_posts':1,'page_errors':browser.errors})
        finally:
            save_once(PRIVATE/'browser-request-ledger.json',{'posts':sorted(browser.route_posts),'gets':browser.requests,'errors':browser.errors})
            browser.close()


if __name__=='__main__':
    main()
