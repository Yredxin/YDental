"""One Firefox process spanning the original and upgraded UI1 HTTP servers."""

import configparser
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit

import psycopg2

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright

NAME = 'ydental_s10_test_20261015011000_a91c4d70'
RUN = ROOT / '.local' / NAME
PORT = 18269
BASE = 'http://127.0.0.1:' + str(PORT)
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', NAME)
marker = json.loads((RUN / 'database.json').read_text())
fixture = json.loads((RUN / 'fixture.json').read_text())
assert marker['database'] == NAME and fixture['db'] == NAME and marker['oid'] == fixture['oid']
cfg = configparser.ConfigParser(interpolation=None)
assert cfg.read(RUN / 'odoo.conf')
dbargs = dict(host='127.0.0.1', port=5432, user='odoo',
              password=cfg['options']['db_password'], dbname=NAME)


def exclusive(name, data):
    path = RUN / name
    with path.open('x', encoding='utf-8') as stream:
        json.dump(data, stream, ensure_ascii=True, indent=2, sort_keys=True)
        stream.write('\n')


def event(label, **data):
    with (RUN / 'browser-events.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'utc': datetime.now(timezone.utc).isoformat(),
                                 'label': label, **data}, ensure_ascii=True, sort_keys=True, default=str) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def ledger(name):
    with (RUN / 'ui1-commit-ledger.jsonl').open('a', encoding='utf-8') as stream:
        stream.write(json.dumps({'name': name, 'status': 'COMMITTED',
                                 'utc': datetime.now(timezone.utc).isoformat()}) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def state():
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            counts = {}
            for table in ('ydental_settlement_receipt', 'ydental_settlement_payment',
                          'ydental_settlement_refund', 'ydental_settlement_close',
                          'account_move', 'account_payment', 'account_partial_reconcile',
                          'ydental_access_audit', 'mail_message', 'mail_mail', 'bus_bus'):
                cur.execute('SELECT count(*) FROM ' + table)
                counts[table] = cur.fetchone()[0]
            cur.execute("SELECT move_type,state,count(*),coalesce(sum(amount_total),0) FROM account_move "
                        "GROUP BY move_type,state ORDER BY move_type,state")
            moves = cur.fetchall()
            cur.execute("SELECT p.id,p.ydental_amount,p.ydental_channel,p.ydental_business_date,"
                        "a.id,a.state,m.state,a.journal_id FROM ydental_settlement_payment p "
                        "JOIN account_payment a ON a.id=p.ydental_payment_id "
                        "JOIN account_move m ON m.id=a.move_id ORDER BY p.id")
            payments = cur.fetchall()
            cur.execute("SELECT r.id,r.ydental_amount,r.ydental_state,r.ydental_native_payment_id,"
                        "r.ydental_credit_note_id,r.ydental_approver_id FROM ydental_settlement_refund r ORDER BY r.id")
            refunds = cur.fetchall()
            cur.execute("SELECT id,ydental_business_date,ydental_state,ydental_gross,"
                        "ydental_refunded,ydental_pending FROM ydental_settlement_close ORDER BY id")
            closes = cur.fetchall()
            return {'counts': counts, 'moves': moves, 'payments': payments,
                    'refunds': refunds, 'closes': closes}


def finance(value):
    keys = ('ydental_settlement_receipt', 'ydental_settlement_payment',
            'ydental_settlement_refund', 'ydental_settlement_close',
            'account_move', 'account_payment', 'account_partial_reconcile')
    return tuple(value['counts'][key] for key in keys)


def login(browser, role, store_id):
    context = browser.new_context(viewport={'width': 1440, 'height': 900},
                                  locale='zh-CN', accept_downloads=True)
    context.route('**/*', lambda route: route.continue_()
                  if urlsplit(route.request.url).hostname == '127.0.0.1'
                  and urlsplit(route.request.url).port == PORT else route.abort())
    page = context.new_page()
    response = page.goto(BASE + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
    assert response.status == 200
    with psycopg2.connect(**dbargs) as conn:
        conn.set_session(readonly=True)
        with conn.cursor() as cur:
            cur.execute('SELECT login FROM res_users WHERE id=%s', (fixture['actors'][role],))
            user_login = cur.fetchone()[0]
    page.locator('[name=login]').fill(user_login)
    page.locator('[name=password]').fill('s05-test-password')
    page.locator('button[type=submit]').click()
    page.wait_for_url('**/ydental/access')
    result = switch(page, store_id)
    assert result['status'] == 200, result
    event('login', role=role, store_id=store_id, status=response.status)
    return context, page


def switch(page, store_id):
    page.goto(BASE + '/ydental/access', wait_until='domcontentloaded')
    return page.evaluate('''async store => {const body=new URLSearchParams({
        operation:'switch',revision:document.querySelector('[name=revision]').value,
        csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',
        payload:JSON.stringify({store_id:store})});
        const r=await fetch('/ydental/access/action',{method:'POST',body});
        return {status:r.status,content_type:r.headers.get('content-type'),data:await r.json()};}''', store_id)


def board(page):
    response = page.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
    assert response.status == 200 and page.locator('h1').inner_text() == '线下结算工作台'
    return response


def operation_form(page, operation, selector=''):
    form = page.locator('form:has(input[name="operation"][value="' + operation + '"])' + selector)
    assert form.count() == 1, (operation, form.count())
    return form


def post_form(page, form, name, button='button[type=submit]'):
    before = state()
    key = form.locator('input[name="key"]').input_value()
    with page.expect_response(lambda response: response.request.method == 'POST'
                              and urlsplit(response.url).path == '/ydental/settlement/action') as response_info:
        form.locator(button).click()
    response = response_info.value
    page.wait_for_load_state('domcontentloaded')
    details = {'name': name, 'key_sha256': hashlib.sha256(key.encode()).hexdigest(),
               'request_content_type': response.request.headers.get('content-type'),
               'response_content_type': response.headers.get('content-type'),
               'status': response.status, 'request_url': urlsplit(response.request.url).path,
               'response_url': urlsplit(response.url).path,
               'location': response.headers.get('location'),
               'page_path': urlsplit(page.url).path,
               'has_workbench': page.locator('h1:has-text("线下结算工作台")').count() == 1,
               'feedback': page.locator('[data-ui1-feedback]').inner_text()
                   if page.locator('[data-ui1-feedback]').count() == 1 else None,
               'before': before, 'after': state()}
    event('form_post', **details)
    return details, response


def api(page, operation, payload, revision=None, token=None):
    return page.evaluate('''async a => {const body=new URLSearchParams(a.payload);
        body.set('operation',a.operation);
        body.set('revision',a.revision || document.querySelector('[name=revision]').value);
        body.set('csrf_token',a.token === null ? document.querySelector('[name=csrf_token]').value : a.token);
        const r=await fetch('/ydental/settlement/action',{method:'POST',body});
        let data; try {data=await r.json()} catch(e) {data={invalid_json:true}};
        return {status:r.status,content_type:r.headers.get('content-type'),data};}''',
        {'operation': operation, 'payload': payload, 'revision': revision,
         'token': token})


def pdf(page, kind, source_id):
    url = '/ydental/settlement/pdf/' + kind + '/' + str(source_id)
    link = page.locator('a[href="' + url + '"]')
    assert link.count() == 1, (kind, source_id, link.count())
    with page.expect_response(lambda response: urlsplit(response.url).path == url) as response_info:
        with page.expect_download() as download_info:
            link.click()
    response = response_info.value
    download = download_info.value
    target = RUN / ('ui1-' + kind + '.pdf')
    download.save_as(target)
    data = target.read_bytes()
    detail = {'kind': kind, 'source_id': source_id, 'status': response.status,
              'content_type': response.headers.get('content-type'),
              'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
              'header_sha256': response.headers.get('x-ydental-pdf-sha256')}
    assert detail['status'] == 200 and detail['content_type'].startswith('application/pdf')
    assert data.startswith(b'%PDF-') and detail['sha256'] == detail['header_sha256']
    event('pdf_download', **detail)
    return detail


def wait_after():
    started = time.monotonic()
    while time.monotonic() - started < 850:
        if (RUN / 'resume-after.json').exists() and (RUN / 'http-after.pid').exists():
            return
        time.sleep(1)
    raise RuntimeError('UI1 after-server marker timeout; STOP')


with sync_playwright() as playwright:
    browser = playwright.firefox.launch(headless=True)
    contexts = {}
    try:
        manager_ctx, manager = login(browser, 'manager', fixture['store_id'])
        contexts['manager'] = manager_ctx
        assert board(manager).status == 200
        baseline_form = operation_form(manager, 'bill')
        baseline_form.locator('input[name="fee_ids"][value="' + str(fixture['fees'][0]) + '"]').check()
        baseline, reply = post_form(manager, baseline_form, 'baseline_bill')
        assert reply.status == 200
        result = reply.json()
        assert result.get('result') == 'accepted' and result.get('amount') == 100
        assert baseline['after']['counts']['ydental_settlement_receipt'] == baseline['before']['counts']['ydental_settlement_receipt'] + 1
        assert baseline['after']['counts']['account_move'] > baseline['before']['counts']['account_move']
        ledger('baseline_bill')
        manager.screenshot(path=str(RUN / 'ui1-original-json.png'), full_page=True)
        reproduced = (baseline['response_content_type'].startswith('application/json')
                      and baseline['page_path'] == '/ydental/settlement/action'
                      and not baseline['has_workbench'])
        exclusive('baseline-proved.json' if reproduced else 'baseline-not-reproduced.json',
                  {'reproduced': reproduced, 'status': baseline['status'],
                   'content_type': baseline['response_content_type'], 'page_path': baseline['page_path'],
                   'has_workbench': baseline['has_workbench'], 'invoice_id': result.get('invoice_id'),
                   'state': baseline['after']})
        event('baseline_decision', reproduced=reproduced)
        if not reproduced:
            sys.exit(0)
        wait_after()
        assert board(manager).status == 200
        front_ctx, front = login(browser, 'frontdesk', fixture['store_id'])
        contexts['frontdesk'] = front_ctx
        reader_ctx, reader = login(browser, 'reader', fixture['store_id'])
        contexts['reader'] = reader_ctx
        assert board(front).status == 200
        post_bill_form = operation_form(front, 'bill')
        post_bill_form.locator('input[name="fee_ids"][value="' + str(fixture['fees'][1]) + '"]').check()
        post_bill, _ = post_form(front, post_bill_form, 'post_bill')
        assert post_bill['status'] == 303 and post_bill['has_workbench'] and post_bill['feedback']
        ledger('post_bill')
        with psycopg2.connect(**dbargs) as conn:
            conn.set_session(readonly=True)
            with conn.cursor() as cur:
                cur.execute("SELECT ydental_invoice_id FROM ydental_settlement_source WHERE ydental_fee_id=%s", (fixture['fees'][1],))
                invoice_id = cur.fetchone()[0]
        pdf(front, 'bill', invoice_id)
        assert board(front).status == 200
        pay_form = operation_form(front, 'pay')
        pay_form.locator('input[name="invoice_ids"][value="' + str(invoice_id) + '"]').check()
        pay_form.locator('input[name="amount"]').fill('60')
        pay_form.locator('select[name="channel"]').select_option('cash')
        pay_form.locator('input[name="proof"]').fill('UI1 synthetic cash confirmation')
        pay_payload = {'key': pay_form.locator('input[name="key"]').input_value(),
                       'invoice_ids': str(invoice_id), 'amount': '60', 'channel': 'cash',
                       'actual_utc': pay_form.locator('input[name="actual_utc"]').input_value(),
                       'proof': 'UI1 synthetic cash confirmation'}
        post_pay, _ = post_form(front, pay_form, 'post_pay')
        assert post_pay['status'] == 303 and post_pay['has_workbench'] and post_pay['feedback']
        ledger('post_pay')
        payment_id = post_pay['after']['payments'][-1][0]
        assert float(post_pay['after']['payments'][-1][1]) == 60
        pdf(front, 'receipt', payment_id)
        assert board(front).status == 200
        before_replay = state()
        replay = api(front, 'pay', pay_payload)
        after_replay = state()
        assert replay['status'] == 200 and replay['data'].get('result') == 'already_accepted'
        assert finance(before_replay) == finance(after_replay)
        event('json_same_key_replay', result=replay, before=before_replay, after=after_replay)
        front.reload(wait_until='domcontentloaded')
        assert finance(state()) == finance(after_replay)
        event('refresh_no_duplicate', state=state())

        request_form = front.locator('form:has(input[name="operation"][value="refund_request"]):has(input[name="payment_id"][value="' + str(payment_id) + '"])')
        assert request_form.count() == 1
        request_form.locator('input[name="amount"]').fill('20')
        request_form.locator('input[name="reason"]').fill('UI1 synthetic return reason')
        requested, _ = post_form(front, request_form, 'post_refund_request')
        assert requested['status'] == 303 and requested['has_workbench'] and requested['feedback']
        ledger('post_refund_request')
        refund_id = requested['after']['refunds'][-1][0]
        assert requested['after']['refunds'][-1][2] == 'requested'
        assert board(front).status == 200
        self_approve = api(front, 'refund_approve', {'refund_id': str(refund_id),
            'reason': 'UI1 requester must be refused', 'key': 'ui1-self-approve-' + str(refund_id)})
        assert self_approve['status'] in (403, 409)
        event('requester_self_approve_denied', status=self_approve['status'], state=state())

        assert switch(manager, fixture['other_store_id'])['status'] == 200
        manager.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
        cross = api(manager, 'refund_approve', {'refund_id': str(refund_id),
            'reason': 'UI1 cross-store forbidden', 'key': 'ui1-cross-store-' + str(refund_id)})
        assert cross['status'] == 403
        event('cross_store_denied', status=cross['status'], state=state())
        assert switch(manager, fixture['store_id'])['status'] == 200
        assert board(manager).status == 200
        approve_form = manager.locator('form:has(input[name="refund_id"][value="' + str(refund_id) + '"]):has(button[value="refund_approve"])')
        approve_form.locator('input[name="reason"]').fill('UI1 independent synthetic approval')
        approved, _ = post_form(manager, approve_form, 'post_refund_approve', 'button[value="refund_approve"]')
        assert approved['status'] == 303 and approved['has_workbench'] and approved['feedback']
        assert approved['after']['refunds'][-1][2] == 'approved'
        ledger('post_refund_approve')

        assert board(front).status == 200
        execute_form = front.locator('form:has(input[name="operation"][value="refund_execute"]):has(input[name="refund_id"][value="' + str(refund_id) + '"])')
        execute_form.locator('input[name="proof"]').fill('UI1 synthetic offline cash refund')
        executed, _ = post_form(front, execute_form, 'post_refund_execute')
        assert executed['status'] == 303 and executed['has_workbench'] and executed['feedback']
        assert executed['after']['refunds'][-1][2] == 'done'
        ledger('post_refund_execute')
        pdf(front, 'refund', refund_id)

        assert board(front).status == 200
        close_form = operation_form(front, 'close')
        close_form.locator('input[name="business_date"]').fill(str(executed['after']['payments'][-1][3]))
        close_form.locator('select[name="channel"]').select_option('cash')
        closed, _ = post_form(front, close_form, 'post_close')
        assert closed['status'] == 303 and closed['has_workbench'] and closed['feedback']
        assert closed['after']['closes'][-1][2] == 'confirmed'
        ledger('post_close')
        close_id = closed['after']['closes'][-1][0]
        assert board(manager).status == 200
        unlock_form = manager.locator('form:has(input[name="operation"][value="unlock"]):has(input[name="close_id"][value="' + str(close_id) + '"])')
        unlock_form.locator('input[name="reason"]').fill('UI1 synthetic finance review')
        unlocked, _ = post_form(manager, unlock_form, 'post_unlock')
        assert unlocked['status'] == 303 and unlocked['has_workbench'] and unlocked['feedback']
        assert unlocked['after']['closes'][-1][2] == 'unlocked'
        ledger('post_unlock')

        # JSON negative semantics and server side CSRF stay independent of HTML mode.
        assert board(reader).status == 200
        assert reader.locator('form:has(input[name="operation"][value="pay"])').count() == 0
        no_write = api(reader, 'bill', {'fee_ids': str(fixture['fees'][0]),
            'discount': '0', 'reason': '', 'key': 'ui1-no-write-' + str(invoice_id)})
        assert no_write['status'] == 403
        event('frontdesk_without_write_denied', status=no_write['status'], state=state())
        invalid = api(front, 'unknown', {'key': 'ui1-invalid-' + str(invoice_id)})
        assert invalid['status'] == 409
        event('json_409_preserved', status=invalid['status'], state=state())
        bad_csrf = api(front, 'bill', {'fee_ids': str(fixture['fees'][0]),
            'discount': '0', 'reason': '', 'key': 'ui1-bad-csrf-' + str(invoice_id)}, token='invalid')
        assert bad_csrf['status'] == 403
        event('invalid_csrf_denied', status=bad_csrf['status'], state=state())
        direct_pdf = reader_ctx.request.get(BASE + '/ydental/settlement/pdf/receipt/' + str(payment_id))
        assert direct_pdf.status == 403
        event('unauthorized_pdf_denied', status=direct_pdf.status)

        # Keep the old frontdesk form and revision, then revoke its write right.
        assert board(front).status == 200
        stale = operation_form(front, 'close')
        stale_revision = stale.locator('input[name="revision"]').input_value()
        assert switch(manager, fixture['store_id'])['status'] == 200
        manager.goto(BASE + '/ydental/access', wait_until='domcontentloaded')
        revoked = manager.evaluate('''async a => {const body=new URLSearchParams({
            operation:'grant',revision:document.querySelector('[name=revision]').value,
            csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',
            payload:JSON.stringify({user_id:a.user_id,store_id:a.store_id,levels:{settlement:'read'}})});
            const r=await fetch('/ydental/access/action',{method:'POST',body});
            return {status:r.status,data:await r.json()};}''',
            {'user_id': fixture['actors']['frontdesk'], 'store_id': fixture['store_id']})
        assert revoked['status'] == 200
        ledger('revoke_right')
        stale_result = api(front, 'close', {'business_date': str(executed['after']['payments'][-1][3]),
            'channel': 'cash', 'key': 'ui1-stale-revision-' + str(close_id)}, revision=stale_revision)
        assert stale_result['status'] == 403
        event('stale_revision_denied', status=stale_result['status'], state=state())

        # No controlled finance rows are fabricated for a >50 web pagination claim.
        exclusive('browser-complete.json', {'status': 'HTTP_FIREFOX_PASS_LIMITED',
            'baseline_raw_json_reproduced': True, 'final_state': state(),
            'business_commits': 10, 'pagination_over_50': 'NOT_RUN'})
        event('complete', status='HTTP_FIREFOX_PASS_LIMITED')
    finally:
        for context in contexts.values():
            context.close()
        browser.close()
