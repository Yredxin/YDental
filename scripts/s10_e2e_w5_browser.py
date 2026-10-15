"""One fresh manager Firefox session, paying existing invoice 1 at most twice."""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright

from s10_e2e_w5_control import RUN, verify_target, write_once
from s10_e2e_w5_snapshot import (NAME, PORT, SOURCE_RUN, STABLE_AFTER_PAYMENT,
    canonical, connect, exact_signature, money, views)

FIXTURE = ROOT / '.local/ydental_s10_test_20261015060000_b6c7d8e9/fixture.json'


def dec(value):
    return Decimal(str(value))


def validate_money(actual, amounts, residuals, baseline):
    """Check each native payment, journal, posting, partial and original source."""
    assert len(amounts) == len(residuals) <= 2
    assert amounts == (500, 240)[:len(amounts)]
    assert residuals == (240, 0)[:len(residuals)]
    invoice = actual['invoices']
    assert len(invoice) == 1 and invoice[0]['id'] == 1
    assert invoice[0]['state'] == 'posted' and dec(invoice[0]['total']) == Decimal(740)
    assert dec(invoice[0]['residual']) == Decimal(residuals[-1] if residuals else 740)
    expected_state = ('paid', 'in_payment') if len(amounts) == 2 else ('partial',) if amounts else ('not_paid',)
    assert invoice[0]['payment_state'] in expected_state
    assert actual['sources'] == baseline['sources']
    assert actual['cash_configs'] == baseline['cash_configs']
    assert len(actual['native_moves']) == 1 + len(amounts)
    assert actual['native_moves'][0] == baseline['native_moves'][0]
    assert all(row['type'] == 'entry' and row['state'] == 'posted'
               for row in actual['native_moves'][1:])
    assert len(actual['payments']) == len(amounts)
    assert len(actual['partials']) == len(amounts)
    assert len(actual['settlement_payments']) == len(amounts)
    assert len(actual['payment_invoices']) == len(amounts)
    assert len(actual['receipts']) == 1 + len(amounts)
    assert actual['receipts'][0] == baseline['receipts'][0]
    assert [row['operation'] for row in actual['receipts'][1:]] == ['pay'] * len(amounts)
    assert len(actual['invoice_lines']) == len(baseline['invoice_lines']) == 5
    assert [row['id'] for row in actual['invoice_lines']] == [1, 2, 3, 4, 5]
    assert [dec(row['residual']) for row in actual['invoice_lines'][:4]] == [
        dec(row['residual']) for row in baseline['invoice_lines'][:4]]
    assert dec(actual['invoice_lines'][4]['residual']) == Decimal(residuals[-1] if residuals else 740)
    cash = baseline['cash_configs']
    assert cash == [{'store': 1, 'company': 1, 'journal': cash[0]['journal']}]
    for index, amount in enumerate(amounts):
        native = actual['payments'][index]
        internal = actual['settlement_payments'][index]
        partial = actual['partials'][index]
        relation = actual['payment_invoices'][index]
        assert native['payment_type'] == 'inbound' and native['partner_type'] == 'customer'
        assert native['state'] in ('in_process', 'paid')
        assert native['company'] == 1 and native['journal'] == cash[0]['journal']
        assert native['move_state'] == 'posted' and native['move'] == actual['native_moves'][index+1]['id']
        assert dec(native['amount']) == dec(internal['amount']) == dec(partial['amount']) == Decimal(amount)
        assert internal['payment'] == native['id'] and internal['channel'] == 'cash'
        assert internal['store'] == 1 and internal['patient'] == 1
        assert relation == {'settlement_payment': internal['id'], 'invoice': 1}
        assert partial['company'] == 1 and partial['debit'] == 5
        credit_lines = [row for row in actual['payment_lines']
                        if row['id'] == partial['credit'] and row['move'] == native['move']]
        assert len(credit_lines) == 1 and dec(credit_lines[0]['credit']) == Decimal(amount)
        assert dec(sum(row['balance'] for row in actual['payment_lines'] if row['move'] == native['move'])) == 0
    accepted = [row for row in actual['audits'] if row['event'] == 'settlement.pay'
                and row['result'] == 'accepted' and row['user'] == 5 and row['store'] == 1]
    assert len(accepted) == len(amounts)
    assert not any(row['event'] == 'settlement.pay' for row in baseline['audits'])
    return {'invoice': 1, 'residual': str(invoice[0]['residual']),
            'native_payments': [row['id'] for row in actual['payments']],
            'partials': [row['id'] for row in actual['partials']]}


def validate_audit_progress(before, after):
    def count(rows, event, store):
        return sum(row['event'] == event and row['result'] == 'accepted'
                   and row['user'] == 5 and row['store'] == store for row in rows)
    initial = before['audits']
    final = after['audits']
    assert count(final, 'login.scope', None) >= count(initial, 'login.scope', None) + 1
    assert count(final, 'settlement.invoice_view', 1) >= count(initial, 'settlement.invoice_view', 1) + 2
    assert count(final, 'settlement.pay', 1) == count(initial, 'settlement.pay', 1) + 2
    assert count(final, 'settlement.bill', 1) == count(initial, 'settlement.bill', 1)
    return True


def validate_form(fields, amount):
    assert amount in (500, 240)
    assert fields['operation'] == 'pay' and fields['invoice_ids'] == ['1']
    assert fields['output'] == 'html' and fields['channel'] == 'cash'
    assert fields['amount'] == str(amount) and fields['csrf_present']
    assert fields['key_present'] and fields['revision_match']
    assert fields['actual_utc_present'] and fields['proof_present']
    assert fields['form_valid'] and fields['form_visible']
    assert fields['action'] == '/ydental/settlement/action'
    assert fields['method'] == 'post' and fields['button_enabled']
    return True


def validate_response(outcome, amount):
    assert outcome['http_status'] == 303, ('payment_http_class', outcome['http_status'])
    assert outcome['method'] == 'POST' and outcome['path'] == '/ydental/settlement/action'
    assert outcome['request_content_type'].startswith('application/x-www-form-urlencoded')
    assert outcome['response_content_type'] in ('text/html; charset=utf-8', 'text/html') or outcome['response_content_type'].startswith('text/html;')
    assert outcome['location_path'] == '/ydental/settlement'
    assert outcome['notice_present'] and outcome['accepted_feedback']
    assert outcome['form_fields'] == {'operation': 'pay', 'output': 'html', 'invoice_ids': ['1'],
                                      'amount': str(amount), 'channel': 'cash',
                                      'csrf_present': True, 'revision_present': True,
                                      'key_present': True, 'actual_utc_present': True,
                                      'proof_present': True}
    return True


def persist_intent(folder, index, amount):
    write_once(Path(folder) / f'pay-{index}-intent.json', {'amount': amount, 'invoice': 1,
        'utc': datetime.now(timezone.utc).isoformat(), 'one_shot': True})


def persist_observed(folder, index, amount, outcome, after):
    write_once(Path(folder) / f'pay-{index}-observed.json', {'amount': amount, 'response': outcome,
        'money': after['money'], 'stable': after['stable'],
        'utc': datetime.now(timezone.utc).isoformat()})


def payment_flow(adapter):
    """Actual high-level payment code path, also driven by the offline adapter."""
    before = adapter.snapshot()
    validate_money(before['money'], (), (), before['money'])
    for index, (amount, residual) in enumerate(((500, 240), (240, 0)), start=1):
        current = adapter.snapshot()
        validate_money(current['money'], (500,240)[:index-1], (240,0)[:index-1], before['money'])
        assert current['stable'] == before['stable'], 'clinical/stock/source changed before payment'
        fields = adapter.load_form(amount, current['money'])
        validate_form(fields, amount)
        adapter.intent(index, amount)
        outcome = {'error': 'POST response not observed'}
        post_error = None
        try:
            outcome = adapter.submit(index, amount)
        except BaseException as error:
            post_error = repr(error)
            outcome = adapter.observed_response(index)
            outcome['error'] = post_error
        finally:
            # Funds may commit before the client sees a response.  Persist the
            # response and a fresh read-only ledger snapshot before asserting.
            try:
                after = adapter.snapshot()
            except BaseException as error:
                adapter.record(index, amount, outcome,
                    {'snapshot_error': repr(error), 'money': {}, 'stable': {}})
                raise
            adapter.record(index, amount, outcome, after)
        assert post_error is None, ('payment_post_exception', post_error)
        validate_response(outcome, amount)
        validate_money(after['money'], (500,240)[:index], (240,0)[:index], before['money'])
        assert after['stable'] == before['stable'], 'clinical/stock/source changed after payment'
        adapter.confirm(index, amount, after)
    return True


class WebAdapter:
    def __init__(self, browser):
        self.browser = browser
        self.context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
        self.context.route('**/*', lambda route: route.continue_() if (
            urlsplit(route.request.url).hostname == '127.0.0.1' and
            urlsplit(route.request.url).port == PORT) else route.abort())
        self.page = self.context.new_page()
        self.page.set_default_timeout(8000)
        self.page.set_default_navigation_timeout(20000)
        self.errors = []
        self.page.on('pageerror', lambda error: self.errors.append(str(error)))
        self.base = f'http://127.0.0.1:{PORT}'
        self.form = None
        self.baseline = json.loads((RUN / 'before-web.json').read_text())
        self.observed = {}
        self.sent = {}
        self.last_key = None

    def login(self):
        fixture = json.loads(FIXTURE.read_text())
        assert fixture['database'] == 'ydental_s10_test_20261015060000_b6c7d8e9' and fixture['oid'] == 2100285
        login = fixture['roles']['manager']
        self.page.goto(self.base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
        self.page.locator('[name=login]').fill(login)
        self.page.locator('[name=password]').fill('s05-test-password')
        self.page.locator('button[type=submit]').click()
        self.page.wait_for_url('**/ydental/access')
        result = self.page.evaluate("""async store => {
          const body=new URLSearchParams({operation:'switch',
            revision:document.querySelector('[name=revision]').value,
            csrf_token:document.querySelector('[name=csrf_token]').value,
            output:'json',payload:JSON.stringify({store_id:store})});
          const r=await fetch('/ydental/access/action',{method:'POST',body});
          return {status:r.status,data:await r.json()};
        }""", fixture['store'])
        assert result['status'] == 200 and type(result['data'].get('revision')) is int
        assert not self.errors
        write_once(RUN / 'manager-login.json', {'role': 'manager', 'store': fixture['store'],
            'login_status': 200, 'switch_status': result['status'], 'revision_type': 'int'})

    def snapshot(self):
        connection = connect(NAME)
        try:
            actual = money(connection)
            stable = exact_signature(connection, STABLE_AFTER_PAYMENT)
            installed = views(connection)
            assert installed['ydental_settlement.ydental_settlement_tokens']['en_US']['has_output_html']
            return {'money': actual, 'stable': stable, 'views': installed}
        finally:
            connection.close()

    def load_form(self, amount, current):
        assert not self.errors
        invoice = current['invoices']
        assert len(invoice) == 1 and invoice[0]['id'] == 1
        assert dec(invoice[0]['residual']) == Decimal(740 if amount == 500 else 240)
        response = self.page.goto(self.base + '/ydental/settlement?patient_id=1', wait_until='domcontentloaded')
        assert response.status == 200 and not self.errors
        form = self.page.locator('form[action="/ydental/settlement/action"]:has(input[name=operation][value="pay"])')
        assert form.count() == 1
        boxes = form.locator('input[name=invoice_ids]')
        assert boxes.count() == 1 and boxes.first.get_attribute('value') == '1'
        boxes.first.check()
        form.locator('[name=amount]').fill(str(amount))
        form.locator('[name=channel]').select_option('cash')
        form.locator('[name=proof]').fill('W5 synthetic cash confirmation')
        self.form = form
        key = form.locator('[name=key]').input_value()
        assert key and key != self.last_key
        self.last_key = key
        actual_utc = form.locator('[name=actual_utc]').input_value()
        assert datetime.fromisoformat(actual_utc).tzinfo is not None
        fields = {
            'operation': form.locator('[name=operation]').input_value(),
            'invoice_ids': [boxes.first.get_attribute('value')],
            'output': form.locator('[name=output]').input_value(),
            'channel': form.locator('[name=channel]').input_value(),
            'amount': form.locator('[name=amount]').input_value(),
            'csrf_present': bool(form.locator('[name=csrf_token]').input_value()),
            'key_present': bool(key),
            'revision_match': form.locator('[name=revision]').input_value() ==
                self.page.locator('main.o_ydental_settlement').get_attribute('data-revision'),
            'actual_utc_present': bool(actual_utc),
            'proof_present': bool(form.locator('[name=proof]').input_value()),
            'form_valid': form.evaluate('(f)=>f.checkValidity()'),
            'form_visible': form.is_visible(),
            'action': form.get_attribute('action'),
            'method': form.get_attribute('method'),
            'button_enabled': form.locator('button[type=submit]').is_enabled(),
        }
        write_once(RUN / f'form-{amount}.json', {'fields': fields, 'installed_views': self.snapshot()['views'],
            'invoice_residual': str(invoice[0]['residual']), 'manager': True})
        return fields

    def intent(self, index, amount):
        persist_intent(RUN, index, amount)

    def submit(self, index, amount):
        assert self.form is not None and self.form.evaluate('(f)=>f.checkValidity()')
        def sent(request):
            if index not in self.sent and request.method == 'POST' and urlsplit(request.url).path == '/ydental/settlement/action':
                data = parse_qs(request.post_data or '', keep_blank_values=True)
                safe = {'method': request.method, 'path': urlsplit(request.url).path,
                    'request_content_type': request.headers.get('content-type',''),
                    'fields': {key: data.get(key, []) for key in ('operation','output','invoice_ids','amount','channel')},
                    'token_presence': {key: bool(data.get(key, [''])[0]) for key in ('csrf_token','revision','key','actual_utc','proof')}}
                self.sent[index] = safe
                write_once(RUN / f'pay-{index}-sent.json', safe)
        def received(response):
            if index not in self.observed and response.request.method == 'POST' and urlsplit(response.url).path == '/ydental/settlement/action':
                self.observed[index] = {'http_status':response.status,
                    'response_content_type':response.headers.get('content-type',''),
                    'location_path':urlsplit(response.headers.get('location','')).path,
                    'notice_present':bool(parse_qs(urlsplit(response.headers.get('location','')).query).get('notice'))}
                write_once(RUN / f'pay-{index}-response.json', self.observed[index])
        self.page.on('request', sent)
        self.page.on('response', received)
        with self.page.expect_response(lambda response: response.request.method == 'POST' and
                urlsplit(response.url).path == '/ydental/settlement/action') as reply:
            with self.page.expect_navigation(wait_until='domcontentloaded'):
                self.form.locator('button[type=submit]').click()
        response = reply.value
        request = response.request
        assert request.post_data is not None
        data = parse_qs(request.post_data, keep_blank_values=True)
        selected = {key: data.get(key, []) for key in ('operation','output','invoice_ids','amount','channel')}
        fields = {'operation': selected['operation'][0] if len(selected['operation']) == 1 else None,
                  'output': selected['output'][0] if len(selected['output']) == 1 else None,
                  'invoice_ids': selected['invoice_ids'],
                  'amount': selected['amount'][0] if len(selected['amount']) == 1 else None,
                  'channel': selected['channel'][0] if len(selected['channel']) == 1 else None,
                  'csrf_present': bool(data.get('csrf_token', [''])[0]),
                  'revision_present': bool(data.get('revision', [''])[0]),
                  'key_present': bool(data.get('key', [''])[0]),
                  'actual_utc_present': bool(data.get('actual_utc', [''])[0]),
                  'proof_present': bool(data.get('proof', [''])[0])}
        location = response.headers.get('location', '')
        parsed = urlsplit(location)
        feedback = self.page.locator('[data-ui1-feedback="1"]')
        result = {'http_status': response.status, 'method': request.method,
                  'path': urlsplit(response.url).path,
                  'request_content_type': request.headers.get('content-type', ''),
                  'response_content_type': response.headers.get('content-type', ''),
                  'location_path': parsed.path,
                  'notice_present': bool(parse_qs(parsed.query).get('notice')),
                  'accepted_feedback': feedback.count() == 1 and
                      feedback.inner_text() == '操作已受理，请核对下方业务记录。',
                  'form_fields': fields, 'page_errors': self.errors[:]}
        return result

    def observed_response(self, index):
        return {**self.observed.get(index, {}), 'request_sent':self.sent.get(index)}

    def record(self, index, amount, outcome, after):
        persist_observed(RUN, index, amount, outcome, after)

    def confirm(self, index, amount, after):
        assert not self.errors
        screenshot = RUN / f'pay-{index}-confirmed.png'
        assert not screenshot.exists()
        self.page.screenshot(path=str(screenshot), full_page=True)
        os.chmod(screenshot, 0o600)
        write_once(RUN / f'pay-{index}-confirmed.json', {'amount': amount,
            'invoice_residual': str(after['money']['invoices'][0]['residual']),
            'screenshot_sha256': hashlib.sha256(screenshot.read_bytes()).hexdigest()})


def main():
    verify_target()
    assert (RUN / 'before-web.json').is_file() and (RUN / 'http-ready.json').is_file()
    assert not (RUN / 'browser-started.json').exists()
    write_once(RUN / 'browser-started.json', {'utc': datetime.now(timezone.utc).isoformat(),
        'oid': verify_target()})
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        try:
            adapter = WebAdapter(browser)
            adapter.login()
            payment_flow(adapter)
            write_once(RUN / 'browser-complete.json', {'status': 'W5_PAYMENT_COMPLETION_LIMITED_PASS',
                'amounts': [500,240], 'invoice': 1})
        finally:
            browser.close()


if __name__ == '__main__':
    main()
