"""One native HTML close form denial in one bounded Firefox run."""
import configparser
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import parse_qs, urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from s10_ui1_r2_contract import validate_marker
from s10_ui1_r2_evidence import encode, write_once
from s10_ui1_r7_web import own_credentials, close_form_state

NAME = 'ydental_s10_test_20261015060000_c1d2e3f4'
SOURCE = 'ydental_s10_test_20261015033000_a4c82d17'
RUN = ROOT / '.local' / NAME
PORT = 18276
BASE = 'http://127.0.0.1:' + str(PORT)
fixture = None
dbargs = None


def bootstrap():
    global fixture, dbargs
    marker = json.loads((RUN / 'database.json').read_text())
    fixture = json.loads((RUN / 'fixture.json').read_text())
    cfg = configparser.ConfigParser(interpolation=None)
    assert cfg.read(RUN / 'odoo.conf')
    dbargs = dict(host='127.0.0.1', port=5432, user='odoo',
                  password=cfg['options']['db_password'], dbname=NAME)
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s', (NAME,))
            oid = cur.fetchone()[0]
            cur.execute('SELECT system_identifier::text FROM pg_control_system()')
            cluster = cur.fetchone()[0]
    assert fixture['db'] == NAME and fixture['oid'] == oid
    validate_marker(marker=marker, database=NAME, oid=oid, cluster=cluster,
        actual_core='f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb',
        config=RUN / 'odoo.conf', run=RUN, auth=6184612591,
        base='09cbcfea575bd488e617a5f597bab3c9d9286eae', port=PORT,
        source=SOURCE, source_oid=2100265,
        policy=RUN / 'network-policy/sitecustomize.py',
        prepare=ROOT / 'scripts/s10_ui1_r7_control.py',
        control=ROOT / 'scripts/s10_ui1_r7_control.py',
        browser=ROOT / 'scripts/s10_ui1_r7_browser.py',
        contract=ROOT / 'scripts/s10_ui1_r2_contract.py')


def event(label, **detail):
    with (RUN / 'browser-events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(encode({'utc': datetime.now(timezone.utc),
            'label': label, **detail}), ensure_ascii=True, sort_keys=True) + '\n')
        stream.flush(); os.fsync(stream.fileno())


def finance(database=NAME):
    queries = (
        ('moves', 'SELECT id,move_type,state,amount_total,amount_residual FROM account_move ORDER BY id'),
        ('move_lines', 'SELECT id,move_id,account_id,debit,credit FROM account_move_line ORDER BY id'),
        ('receipts', 'SELECT id,ydental_operation FROM ydental_settlement_receipt ORDER BY id'),
        ('payments', 'SELECT id,ydental_amount,ydental_channel FROM ydental_settlement_payment ORDER BY id'),
        ('refunds', 'SELECT id,ydental_amount,ydental_state,ydental_native_payment_id,ydental_credit_note_id FROM ydental_settlement_refund ORDER BY id'),
        ('closes', 'SELECT id,ydental_state,ydental_gross,ydental_refunded,ydental_pending FROM ydental_settlement_close ORDER BY id'),
        ('native_payments', 'SELECT id,amount,state,move_id,journal_id FROM account_payment ORDER BY id'),
        ('partials', 'SELECT id,amount,debit_move_id,credit_move_id FROM account_partial_reconcile ORDER BY id'),
    )
    with psycopg2.connect(**{**dbargs, 'dbname':database}) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            rows = {}
            for label, query in queries:
                cur.execute(query); rows[label] = cur.fetchall()
            return rows


def audit():
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM ydental_access_audit WHERE ydental_event='settlement.report_download'")
            exports = cur.fetchone()[0]
            cur.execute('SELECT count(*) FROM mail_mail'); mail = cur.fetchone()[0]
            cur.execute('SELECT count(*) FROM bus_bus'); bus = cur.fetchone()[0]
            cur.execute('SELECT ydental_event,count(*) FROM ydental_access_audit GROUP BY ydental_event ORDER BY ydental_event')
            categories = cur.fetchall()
            return {'exports': exports, 'mail': mail, 'bus': bus, 'categories': categories}


def front_grant():
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT g.ydental_level FROM ydental_access_grant g "
                        "JOIN ydental_access_membership m ON m.id=g.ydental_membership_id "
                        "WHERE m.ydental_user_id=%s AND m.ydental_store_id=%s "
                        "AND g.ydental_category='settlement'", (fixture['actors']['frontdesk'], fixture['store_id']))
            return cur.fetchall()


def close_date():
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute('SELECT ydental_business_date FROM ydental_settlement_close WHERE id=1')
            row = cur.fetchone()
            if not row or not row[0]: raise RuntimeError('inherited close business date missing; STOP')
            return row[0].isoformat()


def login(browser, role):
    context = browser.new_context(viewport={'width':1440,'height':900}, locale='zh-CN')
    context.route('**/*', lambda route: route.continue_()
        if urlsplit(route.request.url).hostname == '127.0.0.1'
        and urlsplit(route.request.url).port == PORT else route.abort())
    page = context.new_page()
    assert page.goto(BASE + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded').status == 200
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute('SELECT login FROM res_users WHERE id=%s', (fixture['actors'][role],))
            user_login = cur.fetchone()[0]
    page.locator('[name=login]').fill(user_login)
    page.locator('[name=password]').fill(os.environ['YDENTAL_UI1_SYNTHETIC_PASSWORD'])
    page.locator('button[type=submit]').click()
    page.wait_for_url('**/ydental/access')
    own = own_credentials(page, BASE)
    result = page.evaluate('''async a => {const body=new URLSearchParams({
        operation:'switch',revision:a.revision,csrf_token:a.token,
        output:'json',payload:JSON.stringify({store_id:a.store_id})});
        const r=await fetch('/ydental/access/action',{method:'POST',body});
        return {status:r.status,data:await r.json()};}''',
        {'revision':own['revision'],'token':own['csrf_token'],'store_id':fixture['store_id']})
    if result['status'] != 200 or not result['data'].get('revision'):
        raise RuntimeError('synthetic login store scope failed; STOP')
    event('login', role=role, store_id=fixture['store_id'], status=200)
    return context, page


def grant_read(manager):
    own = own_credentials(manager, BASE)
    before, before_audit = finance(), audit()
    result = manager.evaluate('''async a => {const body=new URLSearchParams({
        operation:'grant',revision:a.revision,csrf_token:a.token,output:'json',
        payload:JSON.stringify({user_id:a.user_id,store_id:a.store_id,levels:{settlement:'read'}})});
        const r=await fetch('/ydental/access/action',{method:'POST',body});
        return {status:r.status,data:await r.json()};}''',
        {'revision':own['revision'],'token':own['csrf_token'],
         'user_id':fixture['actors']['frontdesk'],'store_id':fixture['store_id']})
    after_audit = audit()
    event('grant_read', status=result['status'], before=before_audit, after=after_audit,
          finance_unchanged=before==finance(), grant=front_grant())
    if result['status'] != 200 or front_grant() != [('read',)] or finance() != before:
        raise RuntimeError('revoke failed or changed finance; STOP')
    if after_audit['exports'] != before_audit['exports'] or after_audit['mail'] != before_audit['mail']:
        raise RuntimeError('revoke changed PDF export or mail; STOP')


def form_request(page, form, business_date):
    requests, responses = [], []
    def on_request(request):
        if request.method == 'POST' and urlsplit(request.url).path == '/ydental/settlement/action':
            payload = parse_qs(request.post_data or '', keep_blank_values=True)
            requests.append({'method':'POST','path':'/ydental/settlement/action',
                'content_type':request.headers.get('content-type',''),
                'operation':payload.get('operation'), 'output':payload.get('output'),
                'business_date':payload.get('business_date'), 'channel':payload.get('channel'),
                'csrf_present':bool(payload.get('csrf_token',[''])[0]),
                'key_present':bool(payload.get('key',[''])[0]),
                'revision_present':bool(payload.get('revision',[''])[0])})
    def on_response(response):
        if response.request.method == 'POST' and urlsplit(response.url).path == '/ydental/settlement/action':
            responses.append({'status':response.status,'content_type':response.headers.get('content-type',''),
                              'location':response.headers.get('location','')})
    state_before_click=close_form_state(form)
    if not state_before_click['form_valid'] or not state_before_click['valid']:
        event('html_invalid_before_click', state=state_before_click)
        raise RuntimeError('close form invalid before native click; STOP')
    page.on('request', on_request); page.on('response', on_response)
    try:
        try:
            form.locator('button[type=submit]').click(timeout=5000)
        except PlaywrightTimeoutError:
            event('html_click_timeout', requests=requests, responses=responses,
                  state=close_form_state(form) if not requests else state_before_click)
            raise RuntimeError('native close form click timed out; STOP')
        if not requests:
            state=close_form_state(form)
            event('html_no_post', state=state)
            raise RuntimeError('native close form did not send POST; STOP')
        try:
            page.wait_for_url('**/ydental/settlement?notice=*', timeout=10000)
        except PlaywrightTimeoutError:
            event('html_redirect_timeout', requests=requests, responses=responses)
            raise RuntimeError('close POST did not reach local workbench; STOP')
        if len(requests) != 1 or len(responses) != 1:
            event('html_request_incomplete', requests=requests, responses=responses)
            raise RuntimeError('close POST or response count unexpected; STOP')
        req, resp=requests[0],responses[0]
        feedback = page.locator('[data-ui1-feedback]').inner_text() if page.locator('[data-ui1-feedback]').count()==1 else ''
        result={'request':req,'response':resp,'page_path':urlsplit(page.url).path,
                'feedback_denied':'请求未完成' in feedback,'state_before_click':state_before_click}
        event('html_denied', **result)
        location=urlsplit(resp['location'])
        notice=parse_qs(location.query).get('notice',[''])[0]
        if (req['business_date'] != [business_date] or req['channel'] != ['cash']
                or req['operation'] != ['close'] or req['output'] != ['html']
                or not all(req[k] for k in ('csrf_present','key_present','revision_present'))
                or not req['content_type'].startswith('application/x-www-form-urlencoded')
                or resp['status'] != 303 or location.path != '/ydental/settlement'
                or len(notice) != 32 or result['page_path'] != '/ydental/settlement'
                or not result['feedback_denied']):
            raise RuntimeError('HTML denial response or feedback invalid; STOP')
        return result
    finally:
        page.remove_listener('request',on_request)
        page.remove_listener('response',on_response)


def run():
    with sync_playwright() as playwright:
        browser=playwright.firefox.launch(headless=True)
        contexts={}
        try:
            manager_ctx, manager=login(browser,'manager'); contexts['manager']=manager_ctx
            front_ctx, front=login(browser,'frontdesk'); contexts['front']=front_ctx
            inherited_money=finance()
            if inherited_money != finance(SOURCE) or front_grant() != [('write',)]:
                raise RuntimeError('inherited finance or front permission drift; STOP')
            inherited_audit=audit()
            business_date=close_date()
            old_page=front_ctx.new_page()
            assert old_page.goto(BASE+'/ydental/settlement',wait_until='domcontentloaded').status==200
            assert old_page.locator('h1').inner_text()=='线下结算工作台'
            old_form=old_page.locator('form:has(input[name="operation"][value="close"])')
            if old_form.count()!=1: raise RuntimeError('old close form missing; STOP')
            date_field=old_form.locator('input[name="business_date"]')
            date_field.fill(business_date)
            old_form.locator('select[name="channel"]').select_option('cash')
            state_before=close_form_state(old_form)
            old_revision=old_form.locator('input[name="revision"]').input_value()
            event('prefilled_form', state=state_before, business_date=business_date,
                  revision=old_revision, finance_unchanged=finance()==inherited_money)
            if (state_before['value']!=business_date or state_before['type']!='date'
                    or not state_before['required'] or not state_before['valid']
                    or not state_before['form_valid'] or state_before['invalid_fields']):
                raise RuntimeError('native close form validity failed before revoke; STOP')
            grant_read(manager)
            front_after=own_credentials(front,BASE)
            state_after=close_form_state(old_form)
            event('old_page_retained', revision_same=front_after['revision']==old_revision,
                  state=state_after, finance_unchanged=finance()==inherited_money)
            if (front_after['revision'] != old_revision or state_after['value'] != business_date
                    or not state_after['form_valid'] or not state_after['valid']):
                raise RuntimeError('old front page or revision changed after revoke; STOP')
            before_post, before_audit=finance(), audit()
            result=form_request(old_page,old_form,business_date)
            after_post, after_audit=finance(), audit()
            event('post_invariants', finance_unchanged=before_post==after_post==inherited_money,
                  audit_before=before_audit, audit_after=after_audit)
            if (before_post != after_post or after_post != inherited_money
                    or after_audit['exports'] != inherited_audit['exports']
                    or after_audit['mail'] != inherited_audit['mail']):
                raise RuntimeError('denied HTML request changed finance/export/mail; STOP')
            old_page.reload(wait_until='domcontentloaded')
            if finance()!=inherited_money or audit()['exports']!=inherited_audit['exports']:
                raise RuntimeError('refresh changed finance/export; STOP')
            event('refresh_safe', finance_unchanged=True)
            write_once(RUN/'browser-complete.json',{'status':'R7_HTML_DENIAL_LIMITED_PASS',
                'finance':finance(),'audit':audit(),'business_date':business_date,
                'html_status':result['response']['status'], 'pagination_over_50':'NOT_RUN'})
        finally:
            for context in contexts.values(): context.close()
            browser.close()

if __name__=='__main__':
    bootstrap()
    run()
