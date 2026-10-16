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

from s10_p0_04_control import PRIVATE, save_once, verify_target, web_diff, capture, load_capture
from s10_p0_04_snapshot import TARGET, TARGET_RUN, PORT, connect

BASE = 'http://127.0.0.1:'+str(PORT)


def validate_form(fields, operation, record):
    assert fields['action'] == '/ydental/settlement/action'
    assert fields['method'] == 'post' and fields['visible'] and fields['valid']
    assert fields['output'] == 'html' and fields['csrf'] and fields['key']
    assert fields['revision_match'] and fields['reason']
    assert fields['record'] == str(record)
    assert fields['operation'] == operation
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

    def close(self):
        for context in self.contexts:
            context.close()
        self.browser.close()

    def login(self, user_id, store_id):
        with connect(TARGET) as conn, conn.cursor() as cur:
            cur.execute('SELECT login,active FROM res_users WHERE id=%s',(user_id,))
            login, active = cur.fetchone()
        assert active
        context = self.browser.new_context(viewport={'width':1440,'height':900},locale='zh-CN')
        context.route('**/*',lambda route: route.continue_()
            if urlsplit(route.request.url).hostname == '127.0.0.1'
            and urlsplit(route.request.url).port == PORT else route.abort())
        page = context.new_page()
        page.on('pageerror',lambda error: self.errors.append(str(error)))
        response = page.goto(BASE+'/web/login?redirect=/ydental/access',wait_until='domcontentloaded')
        assert response.status == 200
        page.locator('[name=login]').fill(login)
        page.locator('[name=password]').fill('s05-test-password')
        page.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        switch = page.locator('form[action="/ydental/access/action"]:has(input[name=operation][value="switch"])')
        assert switch.count() == 1
        switch.locator('select[name=store_id]').select_option(str(store_id))
        assert switch.evaluate('(f)=>f.checkValidity()')
        switch.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        self.contexts.append(context)
        self.page_users[page] = user_id
        save_once(PRIVATE/f'login-{user_id}.json',{'user_id':user_id,'store_id':store_id,
            'login_http':response.status,'switch':'HTML_FORM'})
        return page

    def page_two(self, page, kind, record):
        first = page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded')
        assert first.status == 200
        assert page.locator('main.o_ydental_settlement').count() == 1
        link = page.locator(f'a[href*="{kind}_page=2"]:has-text("下一页")')
        assert link.count() == 1 and link.is_visible()
        href = link.get_attribute('href')
        assert urlsplit(href).path == '/ydental/settlement'
        assert parse_qs(urlsplit(href).query).get(kind+'_page') == ['2']
        link.click()
        page.wait_for_url('**/*'+kind+'_page=2*')
        assert page.locator('main.o_ydental_settlement').count() == 1
        text = page.locator('main.o_ydental_settlement').inner_text()
        assert ('退款 '+str(record)+'：' if kind=='refunds' else '日结 '+str(record)+' /') in text
        png = PRIVATE/f'{kind}-page2.png'
        assert not png.exists()
        page.screenshot(path=str(png),full_page=True)
        os.chmod(png,0o600)
        save_once(PRIVATE/f'{kind}-page2.json',{'href':href,'record':record,
            'screenshot_sha256':hashlib.sha256(png.read_bytes()).hexdigest(),
            'pageerror_count':len(self.errors)})
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
                'csrf_token','revision','key')},'status':response.status,
            'location_path':location.path,'notice':bool(parse_qs(location.query).get('notice')),
            'landing_status':navigation.value.status,
            'feedback':feedback.inner_text() if feedback.count()==1 else None}


def guard_send(ledger, user_id, operation, record):
    key = (user_id, operation, record)
    assert key not in ledger, ('duplicate_post', key)
    ledger.add(key)


def observe_once(browser, page, form, stage, actor, store, reason, baseline, *, accepted=False):
    """Persist intent, send one native HTML request, persist independent observation, then assert."""
    before = capture(TARGET)
    web_diff(baseline, before)
    key = form.locator('input[name=key]').input_value()
    revision = form.locator('input[name=revision]').input_value()
    csrf = form.locator('input[name=csrf_token]').input_value()
    assert key and revision and csrf and reason
    assert not any(r['ydental_actor_id'] == actor and r['ydental_store_id'] == store
                   and r['ydental_key'] == key for r in before['all']['rows']['ydental_settlement_receipt'].values())
    log_path=TARGET_RUN/'http.log'
    log_offset=log_path.stat().st_size
    intent = {'stage':stage,'operation':'unlock','close_id':9,'actor':actor,'store':store,
              'key':key,'reason':reason,'revision':revision,'csrf_sha256':hashlib.sha256(csrf.encode()).hexdigest(),
              'oid':verify_target(),'utc':datetime.now(timezone.utc).isoformat()}
    save_once(PRIVATE/f'{stage}-intent.json',intent)
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
    validate_response(response,'unlock',9,accepted=accepted)
    assert response['post']['key'] == [key] and response['post']['revision'] == [revision]
    assert len(response['post']['csrf_token']) == 1 and response['post']['csrf_token'][0] == csrf
    assert not browser.errors
    gate = web_diff(before,after,unlock=accepted,intent=intent if accepted else None,
                    denied_actor=None if accepted else actor)
    save_once(PRIVATE/f'{stage}-gate.json',gate)
    return after


def negative_no_role(browser, baseline):
    page=browser.login(10,1)
    response=page.goto(BASE+'/ydental/access',wait_until='domcontentloaded')
    assert response.status==200
    native=page.locator('form[action="/ydental/access/action"]:has(input[name=operation][value="switch"])')
    assert native.count()==1
    csrf=native.locator('input[name=csrf_token]').input_value()
    revision=native.locator('input[name=revision]').input_value()
    key=secrets.token_hex(16)
    assert csrf and revision and key
    reason='P0-04 synthetic no-role unlock denial'
    html=('<form method="post" action="/ydental/settlement/action">'+''.join(
        '<input type="hidden" name="'+name+'" value="'+escape(value,quote=True)+'"/>'
        for name,value in {'csrf_token':csrf,'revision':revision,'key':key,'output':'html',
            'operation':'unlock','close_id':'9'}.items())+
        '<input type="text" name="reason" required value="'+escape(reason,quote=True)+'"/>'+
        '<button type="submit">Unlock</button></form>')
    page.set_content(html)
    form=page.locator('form[action="/ydental/settlement/action"]')
    assert form.count()==1 and form.evaluate('(f)=>f.checkValidity()')
    assert form.locator('input[name=csrf_token]').input_value()==csrf
    assert form.locator('input[name=revision]').input_value()==revision
    return observe_once(browser,page,form,'deny-user10',10,1,reason,baseline)


def negative_cross_store(browser, baseline):
    page=browser.login(14,3)
    response=page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded')
    assert response.status==200
    form=page.locator('form[action="/ydental/settlement/action"]:has('
        'input[name=close_id][value="63"]):has(input[name=operation][value="unlock"])')
    assert form.count()==1 and form.is_visible()
    assert form.locator('input[name=close_id]').input_value()=='63'
    form.locator('input[name=close_id]').evaluate('(el)=>{el.value="9"}')
    reason='P0-04 synthetic cross-store unlock denial'
    form.locator('input[name=reason]').fill(reason)
    fields={'action':form.get_attribute('action'),'method':form.get_attribute('method'),
        'visible':form.is_visible(),'valid':form.evaluate('(f)=>f.checkValidity()'),
        'output':form.locator('input[name=output]').input_value(),
        'csrf':bool(form.locator('input[name=csrf_token]').input_value()),
        'key':bool(form.locator('input[name=key]').input_value()),
        'revision_match':form.locator('input[name=revision]').input_value()==
            page.locator('main.o_ydental_settlement').get_attribute('data-revision'),
        'reason':True,'record':form.locator('input[name=close_id]').input_value(),
        'operation':form.locator('input[name=operation]').input_value(),
        'button_enabled':form.locator('button[type=submit]').is_enabled()}
    validate_form(fields,'unlock',9)
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
        try:
            user6=browser.login(6,1)
            browser.page_two(user6,'closes',9)
            close=initial['all']['rows']['ydental_settlement_close'][9]
            assert close['ydental_state']=='confirmed' and close['ydental_store_id']==1
            assert close['ydental_cashier_id']==5 and close['ydental_business_date']=='2026-07-15'
            assert close['ydental_channel']=='card' and close['ydental_cycle']==1
            reason='P0-04 synthetic finance unlock review'
            form,fields=browser.form(user6,'unlock',9,reason)
            assert fields['revision_match']
            after_page=capture(TARGET)
            web_diff(initial,after_page)
            save_once(PRIVATE/'page2-readonly.json',after_page)
            after_user10=negative_no_role(browser,after_page)
            after_user14=negative_cross_store(browser,after_user10)
            # A new read-only check freezes the exact state before the sole permitted success POST.
            pre_unlock=capture(TARGET)
            assert pre_unlock==after_user14
            assert pre_unlock['all']['rows']['ydental_settlement_close'][9]['ydental_state']=='confirmed'
            assert pre_unlock['all']['rows']['ydental_settlement_refund'][14]==baseline['all']['rows']['ydental_settlement_refund'][14]
            assert pre_unlock['all']['rows']['ydental_settlement_mutex'][1]['ydental_revision']==243
            assert set(pre_unlock['all']['rows']['ydental_settlement_receipt'])==set(baseline['all']['rows']['ydental_settlement_receipt'])
            form,fields=browser.form(user6,'unlock',9,reason)
            assert fields['revision_match']
            final=observe_once(browser,user6,form,'unlock-user6',6,1,reason,pre_unlock,accepted=True)
            cumulative=web_diff(baseline,final,unlock=True,intent=json.loads((PRIVATE/'unlock-user6-intent.json').read_text()))
            save_once(PRIVATE/'cumulative-gate.json',cumulative)
            save_once(PRIVATE/'positive-complete.json',{'close9':'unlocked','refund14':'rejected',
                'oid':verify_target(),'negative_posts':2,'unlock_posts':1,'page_errors':browser.errors})
        finally:
            browser.close()


if __name__=='__main__':
    main()
