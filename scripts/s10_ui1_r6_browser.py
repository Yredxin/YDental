"""One bounded Firefox run for UI1-R6 negative Web checks only."""
import configparser
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from urllib.parse import parse_qs, urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright
from s10_ui1_r2_contract import validate_marker
from s10_ui1_r2_evidence import encode, write_once
from s10_ui1_r6_web import own_credentials, post

NAME = 'ydental_s10_test_20261015052000_b6d2a94f'
SOURCE = 'ydental_s10_test_20261015033000_a4c82d17'
RUN = ROOT / '.local' / NAME
PORT = 18275
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
    with psycopg2.connect(**dbargs) as identity_db:
        identity_db.set_session(readonly=True)
        with identity_db.cursor() as cur:
            cur.execute('SELECT oid FROM pg_database WHERE datname=%s', (NAME,))
            oid = cur.fetchone()[0]
            cur.execute('SELECT system_identifier::text FROM pg_control_system()')
            cluster = cur.fetchone()[0]
    assert fixture['db'] == NAME and fixture['oid'] == oid
    validate_marker(marker=marker, database=NAME, oid=oid, cluster=cluster,
        actual_core='f0c5a9b42f544e7f18dc6c8e1c93b957837e0bcb',
        config=RUN / 'odoo.conf', run=RUN, auth=6184420329,
        base='fc04662455528d6906370dbf15a3445faf6a9813', port=PORT,
        source=SOURCE, source_oid=2100265,
        policy=RUN / 'network-policy/sitecustomize.py',
        prepare=ROOT / 'scripts/s10_ui1_r6_control.py',
        control=ROOT / 'scripts/s10_ui1_r6_control.py',
        browser=ROOT / 'scripts/s10_ui1_r6_browser.py',
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
            cur.execute('SELECT id,ydental_event,ydental_user_id FROM ydental_access_audit ORDER BY id DESC LIMIT 6')
            recent = cur.fetchall()
            cur.execute("SELECT count(*) FROM ydental_access_audit WHERE ydental_event='settlement.report_download'")
            exports = cur.fetchone()[0]
            cur.execute('SELECT count(*) FROM mail_mail')
            mail = cur.fetchone()[0]
            cur.execute('SELECT count(*) FROM bus_bus')
            bus = cur.fetchone()[0]
            cur.execute('SELECT ydental_event,count(*) FROM ydental_access_audit GROUP BY ydental_event ORDER BY ydental_event')
            categories = cur.fetchall()
            return {'recent': recent, 'exports': exports, 'mail': mail, 'bus':bus, 'categories':categories}


def invariant(label, action, expected_status, *, kind='json', error_contains=None):
    before, before_audit = finance(), audit()
    result = action()
    after, after_audit = finance(), audit()
    # Emit the full result to the private run dir before assertions; public evidence is sanitized.
    event('negative_request', scenario=label, status=result.get('status'),
          content_type=result.get('content_type'), body_class=result.get('body_class'),
          error_class=('version_conflict' if 'version_conflict' in str(result.get('data')) else
                       'access_denied' if 'access_denied' in str(result.get('data')) else None),
          finance_unchanged=before == after, audit_before=before_audit, audit_after=after_audit)
    if (before != after or after_audit['mail'] != before_audit['mail']
            or after_audit['exports'] != before_audit['exports']):
        raise RuntimeError('finance or outbound mail changed on negative request; STOP')
    if result.get('status') != expected_status:
        raise RuntimeError(label + ': unexpected HTTP status; STOP')
    if kind == 'json' and not str(result.get('content_type','')).startswith('application/json'):
        raise RuntimeError(label + ': JSON contract changed; STOP')
    if error_contains and error_contains not in str(result.get('data')):
        raise RuntimeError(label + ': expected error class missing; STOP')
    return result, before_audit, after_audit


def login(browser, role, store_id):
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN')
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
    result = switch(page, store_id)
    assert result['status'] == 200 and result['data'].get('revision')
    event('login', role=role, store_id=store_id, switch_status=result['status'])
    return context, page


def switch(page, store_id):
    own = own_credentials(page, BASE)
    return page.evaluate('''async a => {const body=new URLSearchParams({
        operation:'switch', revision:a.revision, csrf_token:a.token,
        output:'json', payload:JSON.stringify({store_id:a.store_id})});
        const r=await fetch('/ydental/access/action',{method:'POST',body});
        return {status:r.status,data:await r.json()};}''',
        {'revision': own['revision'], 'token': own['csrf_token'], 'store_id': store_id})


def board(page):
    response = page.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
    assert response.status == 200 and page.locator('h1').inner_text() == '线下结算工作台'
    return response


def grant_read(manager):
    own = own_credentials(manager, BASE)
    before_money, before_audit = finance(), audit()
    result = manager.evaluate('''async a => {const body=new URLSearchParams({
        operation:'grant',revision:a.revision,csrf_token:a.token,output:'json',
        payload:JSON.stringify({user_id:a.user_id,store_id:a.store_id,levels:{settlement:'read'}})});
        const r=await fetch('/ydental/access/action',{method:'POST',body});
        return {status:r.status,data:await r.json()};}''',
        {'revision': own['revision'], 'token': own['csrf_token'],
         'user_id': fixture['actors']['frontdesk'], 'store_id': fixture['store_id']})
    after_audit = audit()
    if result['status'] != 200 or finance() != before_money or after_audit['mail'] != before_audit['mail']:
        raise RuntimeError('grant result or finance boundary changed; STOP')
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute("SELECT g.ydental_level FROM ydental_access_grant g "
                        "JOIN ydental_access_membership m ON m.id=g.ydental_membership_id "
                        "WHERE m.ydental_user_id=%s AND m.ydental_store_id=%s "
                        "AND g.ydental_category='settlement'", (fixture['actors']['frontdesk'], fixture['store_id']))
            if cur.fetchall() != [('read',)]:
                raise RuntimeError('grant did not set read; STOP')
    event('grant_read', status=result['status'], audit_before=before_audit,
          audit_after=after_audit, finance_unchanged=True)
    return result


def html_revoked(page, form):
    before = finance(); prior_audit = audit()
    with page.expect_response(lambda r: r.request.method == 'POST' and
                              urlsplit(r.url).path == '/ydental/settlement/action') as capture:
        form.locator('button[type=submit]').click()
    response = capture.value
    page.wait_for_load_state('domcontentloaded')
    parsed = urlsplit(response.headers.get('location', ''))
    feedback = page.locator('[data-ui1-feedback]').inner_text() if page.locator('[data-ui1-feedback]').count() == 1 else ''
    result = {'status': response.status, 'content_type': response.headers.get('content-type',''),
              'body_class': 'html_redirect', 'location_path': parsed.path,
              'notice_shape': len(parse_qs(parsed.query).get('notice',[''])[0]),
              'page_path': urlsplit(page.url).path, 'feedback_denied': '请求未完成' in feedback}
    event('html_revoked', **result, finance_unchanged=before == finance(),
          audit_before=prior_audit, audit_after=audit())
    if before != finance() or response.status != 303 or parsed.path != '/ydental/settlement' or result['notice_shape'] != 32 or result['page_path'] != '/ydental/settlement' or not result['feedback_denied']:
        raise RuntimeError('HTML rejection/feedback or finance invariant failed; STOP')
    return result


def run():
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        contexts = {}
        try:
            manager_ctx, manager = login(browser, 'manager', fixture['store_id']); contexts['manager'] = manager_ctx
            front_ctx, front = login(browser, 'frontdesk', fixture['store_id']); contexts['front'] = front_ctx
            reader_ctx, reader = login(browser, 'reader', fixture['store_id']); contexts['reader'] = reader_ctx
            inherited_money, inherited_exports = finance(), audit()['exports']
            if inherited_money != finance(SOURCE):
                raise RuntimeError('cloned finance differs from R4 source; STOP')
            assert board(reader).status == 200
            if reader.locator('form:has(input[name="operation"][value="bill"])').count():
                raise RuntimeError('reader has a write form; STOP')
            own_reader = own_credentials(reader, BASE)
            assert board(reader).status == 200
            denied, _, _ = invariant('reader_bill', lambda: post(reader, own_reader, 'bill',
                {'fee_ids': str(fixture['fees'][0]), 'discount':'0', 'reason':'',
                 'key':'ui1-r6-reader-denied'}), 403, error_contains='access_denied')
            assert denied['sent']

            assert board(front).status == 200
            own_front = own_credentials(front, BASE)
            assert board(front).status == 200
            unknown, _, _ = invariant('front_unknown', lambda: post(front, own_front, 'unknown',
                {'key':'ui1-r6-unknown'}), 409)
            unknown_error = str(unknown['data']['error']).lower()
            if not ('unknown' in unknown_error or '未知' in unknown_error):
                raise RuntimeError('unknown operation had wrong 409 error semantics; STOP')
            invariant('front_bad_csrf', lambda: post(front, own_front, 'bill',
                {'fee_ids':str(fixture['fees'][0]), 'discount':'0', 'reason':'',
                 'key':'ui1-r6-bad-csrf'}, token_override='invalid'), 400, kind='framework')

            with psycopg2.connect(**dbargs) as conn:
                conn.set_session(readonly=True)
                with conn.cursor() as cur:
                    cur.execute("SELECT g.ydental_category,g.ydental_level FROM ydental_access_grant g "
                                "JOIN ydental_access_membership m ON m.id=g.ydental_membership_id "
                                "WHERE m.ydental_user_id=%s AND m.ydental_store_id=%s AND g.ydental_category='export'",
                                (fixture['actors']['reader'],fixture['store_id']))
                    grants = cur.fetchall()
            if len(grants) > 1 or any(level not in ('none','read','write') for _,level in grants):
                raise RuntimeError('unexpected reader export grants; STOP')
            if grants == [('export','write')]:
                event('pdf_direct_not_run', reason='reader_has_export_write', grants=grants)
            else:
                for kind, source_id in (('receipt', 1), ('refund', 1)):
                    path = '/ydental/settlement/pdf/' + kind + '/' + str(source_id)
                    def direct(path=path):
                        response = reader_ctx.request.get(BASE + path)
                        return {'status':response.status,'content_type':response.headers.get('content-type',''),
                                'body_class':'json' if 'json' in response.headers.get('content-type','') else 'other',
                                'data':response.json() if 'json' in response.headers.get('content-type','') else None}
                    _, a0, a1 = invariant('reader_pdf_'+kind, direct, 403, error_contains='access_denied')
                    if a1['exports'] != a0['exports']:
                        raise RuntimeError('unauthorized PDF exported; STOP')

            assert board(manager).status == 200
            old = own_credentials(manager, BASE)
            before_money = finance()
            s1 = switch(manager, fixture['other_store_id'])
            if s1['status'] != 200 or finance() != before_money:
                raise RuntimeError('manager A to B failed or changed finance; STOP')
            event('manager_switch_b', status=s1['status'], revision_changed=str(s1['data'].get('revision')) != old['revision'], audit=audit())
            s2 = switch(manager, fixture['store_id'])
            if s2['status'] != 200 or finance() != before_money:
                raise RuntimeError('manager B to A failed or changed finance; STOP')
            event('manager_switch_a', status=s2['status'], audit=audit())
            assert board(manager).status == 200
            invariant('manager_old_revision', lambda: post(manager, old, 'unknown',
                {'key':'ui1-r6-stale'}), 409, error_contains='version_conflict')

            old_page = front_ctx.new_page()
            assert board(old_page).status == 200
            old_form = old_page.locator('form:has(input[name="operation"][value="close"])')
            if old_form.count() != 1:
                raise RuntimeError('front old HTML close form absent; STOP')
            before_front_revision = old_form.locator('input[name="revision"]').input_value()
            grant_read(manager)
            # The front session is unchanged by the manager grant. Its own current access
            # revision must still be used, so this tests permission rather than version.
            own_front_after = own_credentials(front, BASE)
            if own_front_after['revision'] != before_front_revision:
                raise RuntimeError('front revision unexpectedly changed on revoke; STOP')
            assert board(front).status == 200
            with psycopg2.connect(**dbargs) as conn:
                conn.set_session(readonly=True)
                with conn.cursor() as cur:
                    cur.execute('SELECT ydental_business_date FROM ydental_settlement_close WHERE id=1')
                    close_date = str(cur.fetchone()[0])
            invariant('front_revoked_current_revision', lambda: post(front, own_front_after, 'close',
                {'business_date':close_date, 'channel':'cash',
                 'key':'ui1-r6-revoked'}), 403, error_contains='access_denied')
            # This second tab retained the actual form loaded before the grant.
            html_revoked(old_page, old_form)
            front.goto(BASE + '/ydental/settlement?notice=' + 'a'*32, wait_until='domcontentloaded')
            if front.locator('[data-ui1-feedback]').count():
                raise RuntimeError('forged success notice shown; STOP')
            event('forged_notice_rejected')
            if finance() != inherited_money or audit()['exports'] != inherited_exports:
                raise RuntimeError('end-to-end finance or PDF export changed; STOP')
            write_once(RUN / 'browser-complete.json', {'status':'FIREFOX_R6_NEGATIVE_PASS',
                'finance': finance(), 'audit':audit(), 'pagination_over_50':'NOT_RUN'})
        finally:
            for context in contexts.values():
                context.close()
            browser.close()


if __name__ == '__main__':
    bootstrap()
    run()
