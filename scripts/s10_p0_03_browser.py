"""One Firefox, real page two links and one native HTML click per old object."""

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

from s10_p0_03_control import PRIVATE, save_once, verify_target, web_diff, capture, load_capture
from s10_p0_03_snapshot import TARGET, PORT, connect

BASE = 'http://127.0.0.1:'+str(PORT)


def facts():
    with connect(TARGET) as conn, conn.cursor() as cur:
        cur.execute('SELECT to_jsonb(r)::text FROM ydental_settlement_refund r WHERE id=14')
        refund = json.loads(cur.fetchone()[0])
        cur.execute('SELECT to_jsonb(c)::text FROM ydental_settlement_close c WHERE id=9')
        close = json.loads(cur.fetchone()[0])
        cur.execute('SELECT id,ydental_event,ydental_result,ydental_user_id,ydental_store_id '
                    'FROM ydental_access_audit ORDER BY id')
        audit = cur.fetchall()
    return {'refund':refund,'close':close,'audit':audit}


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
    assert response['post']['refund_id' if operation == 'refund_reject' else 'close_id'] == [str(record)]
    assert response['post']['csrf_token'] and response['post']['revision'] and response['post']['key']
    if accepted:
        assert response['status'] == 303 and response['location_path'] == '/ydental/settlement'
        assert response['notice'] and response['feedback'] == '操作已受理，请核对下方业务记录。'
    else:
        assert response['status'] in (403,409) or (
            response['status'] == 303 and response['feedback'] == '请求未完成，请核对权限、门店或输入后重试。')
    return True


def validate_action(before, after, operation):
    assert after['refund']['id'] == before['refund']['id'] == 14
    assert after['close']['id'] == before['close']['id'] == 9
    assert len(after['audit']) >= len(before['audit'])
    new_audits = after['audit'][len(before['audit']):]
    if operation == 'refund_reject':
        assert before['refund']['ydental_state'] == 'requested'
        assert after['refund']['ydental_state'] == 'rejected'
        assert after['refund']['ydental_approver_id'] == 6
        assert after['refund']['ydental_decision_reason']
        assert after['refund']['ydental_native_payment_id'] is None
        assert after['refund']['ydental_credit_note_id'] is None
        assert after['close'] == before['close']
        assert any(x[1] == 'settlement.refund.reject' and x[2] == 'accepted' and x[3] == 6
                   for x in new_audits)
    elif operation == 'unlock':
        assert before['close']['ydental_state'] == 'confirmed'
        assert after['close']['ydental_state'] == 'unlocked'
        assert after['close']['ydental_unlocked_by_id'] == 6
        assert after['close']['ydental_unlock_reason']
        for field in ('ydental_gross','ydental_refunded','ydental_pending','ydental_cycle'):
            assert after['close'][field] == before['close'][field]
        assert after['refund'] == before['refund']
        assert any(x[1] == 'settlement.unlock' and x[2] == 'accepted' and x[3] == 6
                   for x in new_audits)
    else:
        assert after['refund'] == before['refund'] and after['close'] == before['close']
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
        field = 'refund_id' if operation=='refund_reject' else 'close_id'
        selector = ('form[action="/ydental/settlement/action"]:has(input[name='+field+']'
                    '[value="'+str(record)+'"]):has(button[value="refund_reject"])'
                    if operation=='refund_reject' else
                    'form[action="/ydental/settlement/action"]:has(input[name=close_id]'
                    '[value="'+str(record)+'"]):has(input[name=operation][value="unlock"])')
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
            'operation':operation if operation=='refund_reject' else form.locator('input[name=operation]').input_value(),
            'button_enabled':(form.locator('button[value=refund_reject]') if operation=='refund_reject'
                else form.locator('button[type=submit]')).is_enabled()}
        validate_form(fields,operation,record)
        return form,fields

    def submit(self,page,form,operation,record):
        guard_send(self.sent, self.page_users[page], operation, record)
        with page.expect_response(lambda r:r.request.method=='POST' and
                urlsplit(r.url).path=='/ydental/settlement/action') as pending:
            with page.expect_navigation(wait_until='domcontentloaded'):
                if operation=='refund_reject': form.locator('button[value=refund_reject]').click()
                else: form.locator('button[type=submit]').click()
        response = pending.value
        request = response.request
        data = parse_qs(request.post_data or '',keep_blank_values=True)
        location = urlsplit(response.headers.get('location',''))
        feedback = page.locator('[data-ui1-feedback="1"]')
        return {'method':request.method,'path':urlsplit(response.url).path,
            'content_type':request.headers.get('content-type',''),
            'post':{key:data.get(key,[]) for key in ('operation','output','refund_id','close_id',
                'csrf_token','revision','key')},'status':response.status,
            'location_path':location.path,'notice':bool(parse_qs(location.query).get('notice')),
            'feedback':feedback.inner_text() if feedback.count()==1 else None}


def guard_send(ledger, user_id, operation, record):
    key = (user_id, operation, record)
    assert key not in ledger, ('duplicate_post', key)
    ledger.add(key)


def action(browser,page,operation,record,baseline):
    reason = 'P0-03 synthetic historical audit decision'
    form,fields = browser.form(page,operation,record,reason)
    before = facts(); before_snapshot = capture(TARGET)
    web_diff(baseline,before_snapshot,refund=(operation=='unlock'),
        close=False)
    save_once(PRIVATE/f'{operation}-intent.json',{'operation':operation,'record':record,
        'oid':verify_target(),'fields':fields,'utc':datetime.now(timezone.utc).isoformat()})
    try:
        response = browser.submit(page,form,operation,record)
    except Exception as error:
        after = facts(); after_snapshot = capture(TARGET)
        save_once(PRIVATE/f'{operation}-observed.json', {'response_error':type(error).__name__,
            'before':{'refund':before['refund'],'close':before['close']},
            'after':{'refund':after['refund'],'close':after['close']},
            'signatures':after_snapshot['managed']['tables']})
        raise
    # A submitted request is never retried, including on response loss.
    after = facts(); after_snapshot = capture(TARGET)
    save_once(PRIVATE/f'{operation}-observed.json',{'response':response,
        'before':{'refund':before['refund'],'close':before['close'],'audit_count':len(before['audit'])},
        'after':{'refund':after['refund'],'close':after['close'],'audit_count':len(after['audit'])},
        'signatures':after_snapshot['managed']['tables']})
    validate_response(response,operation,record,accepted=True)
    validate_action(before,after,operation)
    web_diff(baseline,after_snapshot,refund=True,
        close=(operation=='unlock'))
    assert not browser.errors
    return after_snapshot


def negative_cross_store(browser,baseline):
    page = browser.login(14,3)
    response = page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded')
    assert response.status == 200
    form = page.locator('form[action="/ydental/settlement/action"]:has('
        'input[name=close_id][value="63"]):has(input[name=operation][value="unlock"])')
    assert form.count()==1
    # A cross-store attacker can alter the target ID, but has only their own
    # live session's native HTML form, CSRF token, revision and new key.
    form.locator('input[name=close_id]').evaluate('(el)=>{el.value="9"}')
    form.locator('input[name=reason]').fill('P0-03 synthetic cross-store denial')
    fields={'operation':'unlock','record':form.locator('input[name=close_id]').input_value(),
        'action':form.get_attribute('action'),'method':form.get_attribute('method'),
        'visible':form.is_visible(),'valid':form.evaluate('(f)=>f.checkValidity()'),
        'output':form.locator('input[name=output]').input_value(),
        'csrf':bool(form.locator('input[name=csrf_token]').input_value()),
        'key':bool(form.locator('input[name=key]').input_value()),
        'revision_match':form.locator('input[name=revision]').input_value()==
            page.locator('main.o_ydental_settlement').get_attribute('data-revision'),
        'reason':True,'button_enabled':form.locator('button[type=submit]').is_enabled()}
    validate_form(fields,'unlock',9)
    before=facts(); pre=capture(TARGET)
    save_once(PRIVATE/'negative-cross-store-intent.json',{'user_id':14,'store_id':3,
        'operation':'unlock','close_id':9,'own_tokens':True,'fields':fields})
    try:
        outcome=browser.submit(page,form,'unlock',9)
    except Exception as error:
        after=facts();post=capture(TARGET)
        save_once(PRIVATE/'negative-cross-store-observed.json',{'response_error':type(error).__name__,
            'refund_unchanged':before['refund']==after['refund'],
            'close_unchanged':before['close']==after['close'],'signatures':post['managed']['tables']})
        raise
    after=facts(); post=capture(TARGET)
    save_once(PRIVATE/'negative-cross-store-observed.json',{'response':outcome,
        'refund_unchanged':before['refund']==after['refund'],
        'close_unchanged':before['close']==after['close'],
        'audit_delta':len(after['audit'])-len(before['audit'])})
    validate_response(outcome,'unlock',9,accepted=False)
    validate_action(before,after,'negative')
    web_diff(pre,post,refund=False,close=False)
    web_diff(baseline,post,refund=True,close=True)
    return post


def negative_no_role(browser,baseline):
    page=browser.login(10,1)
    response=page.goto(BASE+'/ydental/access',wait_until='domcontentloaded')
    assert response.status==200
    native=page.locator('form[action="/ydental/access/action"]:has('
        'input[name=operation][value="switch"])')
    assert native.count()==1
    csrf=native.locator('input[name=csrf_token]').input_value()
    revision=native.locator('input[name=revision]').input_value()
    assert csrf and revision
    key=secrets.token_hex(16)
    # A forged browser HTML form demonstrates the server authorization boundary.
    # It uses only user 10's own live session and is clicked once as a real form.
    html=('<form method="post" action="/ydental/settlement/action">'+''.join(
        '<input type="hidden" name="'+name+'" value="'+escape(value,quote=True)+'"/>'
        for name,value in {'csrf_token':csrf,'revision':revision,'key':key,'output':'html',
            'refund_id':'14','reason':'P0-03 synthetic no-role denial'}.items())+
        '<button name="operation" value="refund_reject">Reject</button></form>')
    page.set_content(html)
    form=page.locator('form[action="/ydental/settlement/action"]')
    assert form.count()==1 and form.evaluate('(f)=>f.checkValidity()')
    before=facts(); pre=capture(TARGET)
    save_once(PRIVATE/'negative-no-role-intent.json',{'user_id':10,'store_id':1,
        'operation':'refund_reject','refund_id':14,'own_csrf':True,
        'own_revision':True,'unique_key':True,'synthetic_html_form':True})
    try:
        outcome=browser.submit(page,form,'refund_reject',14)
    except Exception as error:
        after=facts();post=capture(TARGET)
        save_once(PRIVATE/'negative-no-role-observed.json',{'response_error':type(error).__name__,
            'refund_unchanged':before['refund']==after['refund'],
            'close_unchanged':before['close']==after['close'],'signatures':post['managed']['tables']})
        raise
    after=facts(); post=capture(TARGET)
    save_once(PRIVATE/'negative-no-role-observed.json',{'response':outcome,
        'refund_unchanged':before['refund']==after['refund'],
        'close_unchanged':before['close']==after['close'],
        'audit_delta':len(after['audit'])-len(before['audit'])})
    validate_response(outcome,'refund_reject',14,accepted=False)
    validate_action(before,after,'negative')
    web_diff(pre,post,refund=False,close=False)
    web_diff(baseline,post,refund=True,close=True)
    return post


def main():
    verify_target()
    assert (PRIVATE/'clone-snapshot.json').exists() and (PRIVATE/'http-ready.json').exists()
    baseline = load_capture(PRIVATE/'clone-snapshot.json')
    initial = capture(TARGET)
    web_diff(baseline, initial)
    save_once(PRIVATE/'web-baseline.json', initial)
    with sync_playwright() as playwright:
        browser = Browser(playwright)
        try:
            page = browser.login(6,1)
            browser.page_two(page,'refunds',14)
            after_refund = action(browser,page,'refund_reject',14,baseline)
            browser.page_two(page,'closes',9)
            after_close = action(browser,page,'unlock',9,after_refund)
            after_negative1=negative_cross_store(browser,after_close)
            negative_no_role(browser,after_negative1)
            save_once(PRIVATE/'positive-complete.json',{'refund14':'rejected',
                'close9':'unlocked','oid':verify_target(),
                'money_unchanged':True,'negative_posts':2,'page_errors':browser.errors})
        finally:
            browser.close()


if __name__=='__main__':
    main()
