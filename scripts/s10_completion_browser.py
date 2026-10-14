import argparse
import configparser
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

import psycopg2

root = Path('/home/redxin/code/odoo/odoo-sd/code/sd-addons')
deps = root / '.local/s00-b-deps'
sys.path.insert(0, str(deps / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(deps / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(deps / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(deps / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--db', required=True)
parser.add_argument('--port', required=True, type=int)
parser.add_argument('--pid', required=True, type=int)
args = parser.parse_args()
assert re.fullmatch(r'ydental_s10_test_[0-9]{14}_[a-f0-9]{8}', args.db)
run = root / '.local' / args.db
marker = json.loads((run / 'database.json').read_text())
assert marker['database'] == args.db and marker['port'] == args.port
assert marker['config_sha256'] == hashlib.sha256((run / 'odoo.conf').read_bytes()).hexdigest()
assert os.fsencode(str(run / 'odoo.conf')) in Path(f'/proc/{args.pid}/cmdline').read_bytes().split(b'\0')
assert Path(f'/proc/{args.pid}/cwd').resolve() == root
f1 = json.loads((run / 'f1.json').read_text())
f5 = json.loads((run / 'f5.json').read_text())
history = json.loads((run / 'history.json').read_text())
config = configparser.ConfigParser()
assert config.read(run / 'odoo.conf')
with psycopg2.connect(host='127.0.0.1', port=5432, user='odoo',
        password=config['options']['db_password'], dbname=args.db) as db:
    db.set_session(readonly=True)
    with db.cursor() as cursor:
        cursor.execute('SELECT id, login FROM res_users WHERE id IN %s',
                       (tuple((f5['manager_id'], f5['frontdesk_id'], f1['none_id'])),))
        logins = dict(cursor.fetchall())
        cursor.execute('SELECT ydental_timezone FROM ydental_access_store WHERE id=%s', (f5['store_id'],))
        store_tz = cursor.fetchone()[0]
        cursor.execute('SELECT amount_residual FROM account_move WHERE id=%s', (f5['new_invoice_id'],))
        starting_residual = float(cursor.fetchone()[0])
base = f'http://127.0.0.1:{args.port}'

with sync_playwright() as playwright:
    browser = playwright.firefox.launch(headless=True)
    errors = []
    def login(user_id, store_id):
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, locale='zh-CN', accept_downloads=True)
        context.route('**/*', lambda route: route.continue_()
                      if urlsplit(route.request.url).hostname == '127.0.0.1'
                      and urlsplit(route.request.url).port == args.port else route.abort())
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
        page.locator('[name=login]').fill(logins[user_id])
        page.locator('[name=password]').fill('s05-test-password')
        page.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        result = page.evaluate('''async store => {const body=new URLSearchParams({
            operation:'switch',revision:document.querySelector('[name=revision]').value,
            csrf_token:document.querySelector('[name=csrf_token]').value,output:'json',
            payload:JSON.stringify({store_id:store})});
            const r=await fetch('/ydental/access/action',{method:'POST',body});
            return {status:r.status,data:await r.json()};}''', store_id)
        assert result['status'] == 200, result
        return context, page

    def board(page):
        response = page.goto(base + '/ydental/settlement', wait_until='domcontentloaded')
        assert response.status == 200 and page.locator('h1').inner_text() == '线下结算工作台'

    def action(page, form, button='button[type=submit]'):
        assert form.count() == 1, form.count()
        with page.expect_response('**/ydental/settlement/action') as response:
            form.locator(button).click()
        reply = response.value
        assert reply.status == 200, (reply.status, reply.text())
        result = reply.json()
        assert result['result'] == 'accepted', result
        return result

    manager_context, manager = login(f5['manager_id'], f5['store_id'])
    front_context, front = login(f5['frontdesk_id'], f5['store_id'])
    response = manager.goto(base + f'/ydental/settlement?patient_id={history["old_patient"]}',
                            wait_until='domcontentloaded')
    assert response.status == 200
    old_bill_form = manager.locator('form:has(input[name="operation"][value="bill"])')
    old_bill_form.locator(f'input[name="fee_ids"][value="{history["old_ready_fee"]}"]').check()
    old_bill = action(manager, old_bill_form)
    assert old_bill['amount'] == 600
    response = manager.goto(base + f'/ydental/settlement?patient_id={history["old_patient"]}',
                            wait_until='domcontentloaded')
    assert response.status == 200
    waive_form = manager.locator(f'form:has(input[name="operation"][value="waive"]):has(input[name="invoice_id"][value="{old_bill["invoice_id"]}"])')
    waive_form.locator('input[name="amount"]').fill('600')
    waive_form.locator('input[name="reason"]').fill('Documented synthetic full unpaid waiver')
    waived = action(manager, waive_form)
    assert waived['actually_refunded'] == 0
    recent_bills = []
    for fee_id in history['recent_fee_ids']:
        response = manager.goto(base + f'/ydental/settlement?patient_id={history["recent_patient"]}',
                                wait_until='domcontentloaded')
        assert response.status == 200
        bill_form = manager.locator('form:has(input[name="operation"][value="bill"])')
        bill_form.locator(f'input[name="fee_ids"][value="{fee_id}"]').check()
        billed = action(manager, bill_form)
        assert billed['amount'] == 600
        recent_bills.append(billed['invoice_id'])
    response = manager.goto(base + f'/ydental/settlement?patient_id={history["recent_patient"]}',
                            wait_until='domcontentloaded')
    assert response.status == 200
    multi_form = manager.locator('form:has(input[name="operation"][value="pay"])')
    for invoice_id in recent_bills:
        multi_form.locator(f'input[name="invoice_ids"][value="{invoice_id}"]').check()
    multi_form.locator('input[name="amount"]').fill('700')
    multi_form.locator('select[name="channel"]').select_option('cash')
    multi_form.locator('input[name="proof"]').fill('Actual synthetic two invoice offline receipt')
    multi_payment = action(manager, multi_form)
    assert [row['amount'] for row in multi_payment['allocations']] == [600, 100]
    board(manager)
    assert manager.get_by_text(str(starting_residual), exact=True).count() >= 1
    manager.screenshot(path=str(run / 'firefox-manager-before.png'), full_page=True)
    pay_form = manager.locator('form:has(input[name="operation"][value="pay"])')
    pay_form.locator(f'input[name="invoice_ids"][value="{f5["new_invoice_id"]}"]').check()
    pay_form.locator('input[name="amount"]').fill('10')
    pay_form.locator('select[name="channel"]').select_option('alipay')
    pay_form.locator('input[name="proof"]').fill('Actual synthetic Firefox manager offline 10')
    manager_pay = action(manager, pay_form)
    board(front)
    front_pay_form = front.locator('form:has(input[name="operation"][value="pay"])')
    front_pay_form.locator(f'input[name="invoice_ids"][value="{f5["new_invoice_id"]}"]').check()
    front_pay_form.locator('input[name="amount"]').fill('10')
    front_pay_form.locator('select[name="channel"]').select_option('card')
    front_pay_form.locator('input[name="proof"]').fill('Actual synthetic Firefox frontdesk offline 10')
    front_pay = action(front, front_pay_form)
    board(manager)
    assert manager.get_by_text(str(starting_residual - 20), exact=True).count() >= 1
    manager.screenshot(path=str(run / 'firefox-two-cashiers.png'), full_page=True)

    request_form = manager.locator(f'form:has(input[name="operation"][value="refund_request"]):has(input[name="payment_id"][value="{manager_pay["payment_id"]}"])')
    request_form.locator('input[name="amount"]').fill('5')
    request_form.locator('input[name="reason"]').fill('Actual synthetic refund request')
    requested = action(manager, request_form)
    board(front)
    approve_form = front.locator(f'form:has(input[name="refund_id"][value="{requested["refund_id"]}"]):has(button[value="refund_approve"])')
    approve_form.locator('input[name="reason"]').fill('Independent finance approval')
    approved = action(front, approve_form, 'button[value="refund_approve"]')
    assert approved['actually_refunded'] == 0
    board(manager)
    execute_form = manager.locator(f'form:has(input[name="operation"][value="refund_execute"]):has(input[name="refund_id"][value="{requested["refund_id"]}"])')
    execute_form.locator('input[name="proof"]').fill('Actual synthetic Firefox offline refund 5')
    executed = action(manager, execute_form)
    assert executed['actually_refunded'] == 5
    board(manager)
    manager.screenshot(path=str(run / 'firefox-refund-done.png'), full_page=True)

    board(front)
    rejected_form = front.locator(f'form:has(input[name="operation"][value="refund_request"]):has(input[name="payment_id"][value="{front_pay["payment_id"]}"])')
    rejected_form.locator('input[name="amount"]').fill('5')
    rejected_form.locator('input[name="reason"]').fill('Synthetic rejected request')
    rejected_request = action(front, rejected_form)
    board(manager)
    decision_form = manager.locator(f'form:has(input[name="refund_id"][value="{rejected_request["refund_id"]}"]):has(button[value="refund_reject"])')
    decision_form.locator('input[name="reason"]').fill('No actual return evidence')
    rejected = action(manager, decision_form, 'button[value="refund_reject"]')
    assert rejected['actually_refunded'] == 0

    board(front)
    uncertain_form = front.locator(f'form:has(input[name="operation"][value="refund_request"]):has(input[name="payment_id"][value="{front_pay["payment_id"]}"])')
    uncertain_form.locator('input[name="amount"]').fill('5')
    uncertain_form.locator('input[name="reason"]').fill('Synthetic uncertain request')
    uncertain_request = action(front, uncertain_form)
    board(manager)
    decision_form = manager.locator(f'form:has(input[name="refund_id"][value="{uncertain_request["refund_id"]}"]):has(button[value="refund_approve"])')
    decision_form.locator('input[name="reason"]').fill('Independent approval before status check')
    action(manager, decision_form, 'button[value="refund_approve"]')
    board(front)
    status_form = front.locator(f'form:has(input[name="operation"][value="refund_uncertain"]):has(input[name="refund_id"][value="{uncertain_request["refund_id"]}"])')
    status_form.locator('select[name="outcome"]').select_option('unknown')
    status_form.locator('input[name="reason"]').fill('External outcome unknown')
    unknown = action(front, status_form)
    assert unknown['actually_refunded'] == 0
    board(manager)
    cancel_form = manager.locator(f'form:has(input[name="operation"][value="refund_cancel"]):has(input[name="refund_id"][value="{uncertain_request["refund_id"]}"])')
    cancel_form.locator('input[name="verified_not_paid"]').check()
    cancel_form.locator('input[name="evidence"]').fill('Verified no actual cash or bank transfer')
    cancel_form.locator('input[name="reason"]').fill('Release protected capacity')
    cancelled = action(manager, cancel_form)
    assert cancelled['released'] == 5

    board(manager)
    close_form = manager.locator('form:has(input[name="operation"][value="close"])')
    close_form.locator('input[name="business_date"]').fill(str(datetime.now(timezone.utc).astimezone(ZoneInfo(store_tz)).date()))
    close_form.locator('select[name="channel"]').select_option('alipay')
    closed = action(manager, close_form)
    assert closed['gross'] == 10 and closed['refunded'] == 5
    board(front)
    unlock_form = front.locator(f'form:has(input[name="operation"][value="unlock"]):has(input[name="close_id"][value="{closed["close_id"]}"])')
    unlock_form.locator('input[name="reason"]').fill('Independent finance review of actual receipt')
    unlocked = action(front, unlock_form)
    assert unlocked['state'] == 'unlocked'
    board(manager)
    correction_form = manager.locator(f'form:has(input[name="operation"][value="reclassify"]):has(input[name="payment_id"][value="{manager_pay["payment_id"]}"])')
    correction_form.locator('select[name="new_channel"]').select_option('card')
    correction_form.locator('input[name="reason"]').fill('Actual source document shows card')
    corrected = action(manager, correction_form)
    assert corrected['actual_cash_refunded'] == 0

    board(manager)
    pdfs = {}
    for kind, source_id in (('bill', f5['new_invoice_id']),
                            ('receipt', manager_pay['payment_id']), ('refund', requested['refund_id'])):
        with manager.expect_download() as download:
            manager.locator(f'a[href="/ydental/settlement/pdf/{kind}/{source_id}"]').click()
        target = run / ('firefox-' + kind + '.pdf')
        download.value.save_as(str(target))
        raw = target.read_bytes()
        assert raw.startswith(b'%PDF-')
        pdfs[kind] = {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    manager.screenshot(path=str(run / 'firefox-final.png'), full_page=True)
    none_context, none = login(f1['none_id'], f1['store_id'])
    forbidden = none.goto(base + '/ydental/settlement', wait_until='domcontentloaded')
    assert forbidden.status == 403, forbidden.status
    denied_pdf = none.goto(base + f'/ydental/settlement/pdf/bill/{f1["invoice_id"]}', wait_until='domcontentloaded')
    assert denied_pdf.status == 403, denied_pdf.status
    none_context.close()
    front_context.close()
    manager_context.close()
    browser.close()
    assert not errors, errors
    print('S10_FIREFOX_BUTTONS', json.dumps({'manager_payment': manager_pay,
        'old_history_bill': old_bill, 'full_waiver': waived,
        'recent_bills': recent_bills, 'multi_invoice_payment': multi_payment,
        'frontdesk_payment': front_pay, 'refund_requested': requested,
        'approved': approved, 'executed': executed, 'rejected': rejected,
        'unknown': unknown, 'cancelled': cancelled, 'closed': closed,
        'unlocked': unlocked, 'corrected': corrected, 'pdfs': pdfs,
        'denied_status': forbidden.status, 'pageerrors': errors,
        'screenshots': ['firefox-manager-before.png', 'firefox-two-cashiers.png',
                        'firefox-refund-done.png', 'firefox-final.png']}), flush=True)
