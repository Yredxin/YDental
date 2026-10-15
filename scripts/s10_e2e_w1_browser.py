"""One real Firefox pass through the W1 clinical, stock and settlement desks.

Each business step is followed by an independent, read-only PostgreSQL snapshot.
No service method is used for a treatment, examination, dispense, bill or pay.
"""

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright
import psycopg2
from s10_e2e_w1_control import NAME, PORT, RUN, endpoint, verified_target
from s10_e2e_w1_evidence import read_complete, write_once

STEPS = (
    ('reserve', 'WORKFLOW', None), ('arrive', 'WORKFLOW', None),
    ('report_care', 'WORKFLOW', None), ('care_start', 'WORKFLOW', None),
    ('document', 'WORKFLOW', None), ('treatment', 'ECONOMIC', Decimal('600')),
    ('exam_order', 'WORKFLOW', None), ('prescription', 'WORKFLOW', None),
    ('care_handover', 'WORKFLOW', None), ('report_exam', 'WORKFLOW', None),
    ('exam_start', 'WORKFLOW', None), ('examination', 'ECONOMIC', Decimal('80')),
    ('report_pharmacy', 'WORKFLOW', None), ('pharmacy_start', 'WORKFLOW', None),
    ('dispense_four', 'ECONOMIC', Decimal('40')), ('finish_first', 'WORKFLOW', None),
    ('report_remainder', 'WORKFLOW', None), ('pharmacy_restart', 'WORKFLOW', None),
    ('dispense_two', 'ECONOMIC', Decimal('20')), ('finish_final', 'WORKFLOW', None),
    ('bill', 'ECONOMIC', Decimal('740')), ('pay_five_hundred', 'ECONOMIC', Decimal('500')),
    ('pay_two_forty', 'ECONOMIC', Decimal('240')),
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def event(path, item):
    """Append one complete typed event; a partial tail cannot prove completion."""
    with open(path, 'a', encoding='utf-8') as stream:
        stream.write(json.dumps(item, ensure_ascii=False, default=lambda value:
            {'decimal': str(value)} if isinstance(value, Decimal) else
            {'datetime': value.isoformat()} if isinstance(value, datetime) else
            (_ for _ in ()).throw(TypeError(type(value).__name__))) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def snapshot(database, patient):
    ep = endpoint()
    conn = psycopg2.connect(dbname=database, **ep)
    conn.set_session(readonly=True)
    try:
        with conn.cursor() as cur:
            out = {}
            for table in ('ydental_treatment_event', 'ydental_treatment_fee', 'ydental_exam_result',
                          'ydental_inventory_event', 'ydental_settlement_source',
                          'ydental_settlement_receipt', 'ydental_settlement_payment',
                          'account_move', 'account_payment', 'account_partial_reconcile',
                          'stock_move', 'ydental_access_audit'):
                cur.execute('SELECT count(*) FROM ' + table)
                out[table] = cur.fetchone()[0]
            cur.execute('SELECT id, ydental_event_id, ydental_amount, ydental_price_snapshot_id, ydental_patient_id '
                        'FROM ydental_treatment_fee WHERE ydental_patient_id=%s ORDER BY id', [patient])
            out['fees'] = [dict(zip(('id','event','amount','snapshot','patient'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, state, amount_total, amount_residual, company_id FROM account_move '
                        "WHERE move_type='out_invoice' ORDER BY id")
            out['invoices'] = [dict(zip(('id','state','total','residual','company'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, state, amount, company_id, move_id FROM account_payment ORDER BY id')
            out['payments'] = [dict(zip(('id','state','amount','company','move'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, amount, debit_move_id, credit_move_id FROM account_partial_reconcile ORDER BY id')
            out['partials'] = [dict(zip(('id','amount','debit','credit'), row)) for row in cur.fetchall()]
            cur.execute('SELECT i.id, i.ydental_lot_id, i.ydental_quantity, i.ydental_move_id, '
                        'c.ydental_event_id FROM ydental_inventory_event i '
                        'LEFT JOIN ydental_treatment_consumption c ON c.ydental_inventory_event_id=i.id '
                        'ORDER BY i.id')
            out['inventory'] = [dict(zip(('id','lot','quantity','move','event'), row)) for row in cur.fetchall()]
            return out
    finally:
        conn.close()


def validate_transition(step, before, after):
    fees = [Decimal(str(row['amount'])) for row in after['fees']]
    if step == 'treatment':
        assert fees == [Decimal('600')]
    elif step == 'examination':
        assert fees == [Decimal('600'), Decimal('80')]
    elif step == 'dispense_four':
        assert fees == [Decimal('600'), Decimal('80'), Decimal('40')]
    elif step == 'dispense_two':
        assert fees == [Decimal('600'), Decimal('80'), Decimal('40'), Decimal('20')]
    elif step == 'bill':
        assert len(after['invoices']) == 1 and after['invoices'][0]['state'] == 'posted'
        assert Decimal(str(after['invoices'][0]['total'])) == Decimal('740')
        assert Decimal(str(after['invoices'][0]['residual'])) == Decimal('740')
    elif step == 'pay_five_hundred':
        assert Decimal(str(after['invoices'][0]['residual'])) == Decimal('240')
        assert len(after['payments']) == 1 and Decimal(str(after['payments'][0]['amount'])) == Decimal('500')
    elif step == 'pay_two_forty':
        assert Decimal(str(after['invoices'][0]['residual'])) == 0
        assert [Decimal(str(row['amount'])) for row in after['payments']] == [Decimal('500'), Decimal('240')]
        assert sorted(Decimal(str(row['amount'])) for row in after['partials']) == [Decimal('240'), Decimal('500')]
    if step not in ('treatment','examination','dispense_four','dispense_two','bill','pay_five_hundred','pay_two_forty'):
        for key in ('fees', 'invoices', 'payments', 'partials'):
            assert after[key] == before[key], f'unlisted financial change at {step}: {key}'


def run(driver, evidence_path):
    driver.open_roles()
    before = driver.snapshot()
    assert before['fees'] == before['invoices'] == before['payments'] == before['partials'] == []
    for number, (name, kind, amount) in enumerate(STEPS, 1):
        outcome = driver.perform(name)
        assert outcome['status'] == 'WEB_ACTUAL' and outcome['http_status'] in (200, 303), (name, outcome)
        after = driver.snapshot()
        validate_transition(name, before, after)
        event(evidence_path, {'number': number, 'name': name, 'classification': kind,
                              'amount': amount, 'request': outcome,
                              'before': before, 'after': after,
                              'time': datetime.now(timezone.utc)})
        before = after
    assert len(before['fees']) == 4 and len(before['payments']) == 2
    write_once(evidence_path.with_suffix('.complete.json'), {
        'status': 'WEB_ACTUAL_PASS', 'steps': len(STEPS), 'fees': [r['id'] for r in before['fees']],
        'invoice': before['invoices'][0]['id'], 'payments': [r['id'] for r in before['payments']]})


class WebDriver:
    def __init__(self, browser, fixture):
        self.fixture = fixture
        self.base = f'http://127.0.0.1:{PORT}'
        self.contexts = []
        self.pages = {}
        self.browser = browser
        self.ids = {}
        self.http = []

    def snapshot(self):
        return snapshot(NAME, self.fixture['patient'])

    def open_roles(self):
        f = self.fixture
        self.login('front', f['roles']['frontdesk'], 's05-test-password')
        self.login('doctor', f['roles']['doctor'], 's05-test-password')
        self.login('exam', f['exam_login'], 's06a-test-password')
        self.login('pharmacy', f['pharmacy_login'], 's08b-synthetic-password')
        self.login('manager', f['roles']['manager'], 's05-test-password')

    def login(self, role, login, password):
        context = self.browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
        context.route('**/*', lambda route: route.continue_() if (
            urlsplit(route.request.url).hostname == '127.0.0.1' and
            urlsplit(route.request.url).port == PORT) else route.abort())
        page = context.new_page()
        page.on('pageerror', lambda exc: (_ for _ in ()).throw(RuntimeError('browser pageerror: ' + str(exc))))
        page.goto(self.base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
        page.locator('[name=login]').fill(login)
        page.locator('[name=password]').fill(password)
        page.locator('button[type=submit]').click()
        page.wait_for_url('**/ydental/access')
        result = page.evaluate("""async store => {
          const body = new URLSearchParams({operation:'switch',
            revision:document.querySelector('[name=revision]').value,
            csrf_token:document.querySelector('[name=csrf_token]').value,
            output:'json',payload:JSON.stringify({store_id:store})});
          const r=await fetch('/ydental/access/action',{method:'POST',body});
          return {status:r.status,data:await r.json()};
        }""", self.fixture['store'])
        assert result['status'] == 200 and type(result['data'].get('revision')) is int
        self.contexts.append(context)
        self.pages[role] = page
        return page

    def nav(self, page, path):
        r = page.goto(self.base + path, wait_until='domcontentloaded')
        assert r.status == 200, (path, r.status)

    def html(self, page, form):
        assert form.count() == 1 and form.evaluate('(f)=>f.checkValidity()'), 'missing or invalid HTML form'
        with page.expect_response(lambda r: r.request.method == 'POST') as reply:
            with page.expect_navigation(wait_until='domcontentloaded'):
                form.locator('button[type=submit],button:not([type])').first.click()
        status = reply.value.status
        assert status in (200, 303), status
        return {'status': 'WEB_ACTUAL', 'http_status': status,
                'url': urlsplit(reply.value.url).path, 'method': 'POST'}

    def dynamic(self, page, form, endpoint):
        assert form.count() == 1 and form.evaluate('(f)=>f.checkValidity()'), 'missing or invalid dynamic form'
        page.once('dialog', lambda dialog: dialog.accept())
        with page.expect_response('**' + endpoint) as response:
            with page.expect_navigation(wait_until='domcontentloaded'):
                form.locator('button[type=submit]').click()
        reply = response.value
        assert reply.status == 200, (endpoint, reply.status, reply.text()[:200])
        return {'status': 'WEB_ACTUAL', 'http_status': reply.status,
                'url': urlsplit(reply.url).path, 'method': 'POST'}

    def queue_click(self, page, selector):
        assert page.locator(selector).count() == 1, selector
        with page.expect_response('**/ydental/queue/action') as response:
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator(selector).click()
        assert response.value.status == 200, (selector, response.value.status)
        return {'status': 'WEB_ACTUAL', 'http_status': response.value.status,
                'url': '/ydental/queue/action', 'method': 'POST'}

    def perform(self, name):
        f = self.fixture
        if name == 'reserve':
            page = self.pages['front']
            self.nav(page, '/ydental/intake')
            form = page.locator('#intake-create form').first
            form.locator('[name=operation]').select_option('reserve')
            form.locator('[name=patient_id]').select_option(str(f['patient']))
            form.locator('[name=mapping_id]').select_option(str(f['care_mapping']))
            form.locator('[name=start]').fill(f['slot_start'].replace(' ', 'T')[:16])
            form.locator('[name=end]').fill(f['slot_end'].replace(' ', 'T')[:16])
            result = self.html(page, form)
            self.ids['care_task'] = int(page.locator('#intake-tasks tr[data-task]').last.get_attribute('data-task'))
            return result
        if name == 'arrive':
            page = self.pages['front']; self.nav(page, '/ydental/intake')
            form = page.locator('#intake-create form').nth(1)
            form.locator('[name=patient_id]').select_option(str(f['patient']))
            return self.html(page, form)
        if name.startswith('report_'):
            page = self.pages['front']; self.nav(page, '/ydental/queue')
            key = {'report_care':'care_task','report_exam':'exam_task',
                   'report_pharmacy':'pharmacy_task','report_remainder':'remainder_task'}[name]
            form = page.locator(f'form[data-queue-form=report] input[name=task_id][value="{self.ids[key]}"]').locator('xpath=..')
            return self.html(page, form)
        if name in ('care_start', 'exam_start', 'pharmacy_start', 'pharmacy_restart'):
            role = 'doctor' if name == 'care_start' else 'exam' if name == 'exam_start' else 'pharmacy'
            page = self.pages[role]; self.nav(page, '/ydental/queue')
            station = f['care_station'] if role == 'doctor' else f['exam_station'] if role == 'exam' else f['pharmacy_station']
            if not page.locator('#holding-workstation').count():
                self.queue_click(page, f'button[data-operation=enter][data-station="{station}"]')
            self.queue_click(page, 'button[data-operation=call]')
            result = self.queue_click(page, 'button[data-operation=start]')
            self.nav(page, '/ydental/clinical' if role == 'doctor' else '/ydental/exam' if role == 'exam' else '/ydental/treatment')
            return result
        if name == 'document':
            page = self.pages['doctor']
            page.locator('#open-document').click()
            page.wait_for_function('!document.querySelector("textarea[name=chief_complaint]").disabled')
            page.locator('[name=chief_complaint]').fill('W1 synthetic documented treatment reason')
            with page.expect_response('**/ydental/clinical/action') as response:
                page.locator('#save-document').click()
            assert response.value.status == 200
            page.wait_for_function('Number(document.querySelector("#server-version").textContent)>0')
            return {'status':'WEB_ACTUAL','http_status':200,'url':'/ydental/clinical/action','method':'POST'}
        if name == 'treatment':
            page = self.pages['doctor']; self.nav(page, '/ydental/treatment')
            form = page.locator('form[data-operation=execute]')
            form.locator('[name=catalog_id]').select_option(str(f['care_catalog']))
            form.locator('[name=quantity]').fill('1'); form.locator('[name=tooth]').fill('16')
            form.locator('[name=tooth_state]').select_option('present')
            form.locator('[name=surfaces]').fill('O')
            form.locator('[name=lot_id]').select_option(str(f['material_lot']))
            form.locator('[name=material_quantity]').fill('1')
            form.locator('[name=reason]').fill('W1 synthetic actual physical treatment')
            return self.dynamic(page, form, '/ydental/treatment/action')
        if name in ('exam_order','prescription'):
            page = self.pages['doctor']; self.nav(page, '/ydental/treatment')
            form = page.locator('form[data-operation=order]')
            kind = 'exam' if name == 'exam_order' else 'prescription'
            form.locator('[name=kind]').select_option(kind)
            form.locator('[name=purpose]').fill('W1 synthetic ' + kind + ' clinical order')
            line = form.locator('.o_ydental_treatment_line')
            line.locator('[name=mapping_id]').select_option(str(f['exam_mapping'] if kind == 'exam' else f['pharmacy_mapping']))
            line.locator('[name=quantity]').fill('1' if kind == 'exam' else '6')
            if kind == 'prescription':
                line.locator('[name=product_id]').select_option(str(f['medicine_product']))
                for field in ('specification','usage','frequency','course'):
                    line.locator('[name='+field+']').fill('W1 synthetic reviewed ' + field)
            self.dynamic(page, form, '/ydental/treatment/action')
            article = page.locator(f'article[data-order-kind="{kind}"]').last
            order = int(article.get_attribute('data-order'))
            result = self.dynamic(page, article.locator('form[data-operation=issue]'), '/ydental/treatment/action')
            article = page.locator(f'article[data-order="{order}"]')
            self.ids[kind + '_order'] = order
            self.ids[kind + '_task'] = int(article.locator('.task-id').first.inner_text())
            if kind == 'exam': self.ids['exam_task'] = self.ids['exam_task']
            else: self.ids['pharmacy_task'] = self.ids['prescription_task']
            return result
        if name == 'care_handover':
            page = self.pages['doctor']; self.nav(page, '/ydental/clinical')
            page.locator('#open-document').click()
            page.wait_for_function('!document.querySelector("textarea[name=chief_complaint]").disabled')
            with page.expect_response('**/ydental/clinical/action') as response:
                page.locator('#handover-document').click()
            assert response.value.status == 200
            self.nav(page, '/ydental/queue')
            return self.queue_click(page, 'button[data-operation=exit]')
        if name == 'examination':
            page = self.pages['exam']; self.nav(page, '/ydental/exam')
            panel = page.locator(f'section[data-line]')
            assert panel.count() == 1, 'exactly one ordered examination required'
            form = panel.locator('form[data-operation=draft]')
            form.locator('[name=findings]').fill('W1 synthetic actual examined finding')
            self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=perform]')
            form.locator('[name=reason]').fill('W1 synthetic actual completed examination')
            result = self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=confirm]')
            form.locator('[name=reason]').fill('W1 synthetic examined result review')
            self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=finish]')
            form.locator('[name=reason]').fill('W1 synthetic examination segment complete')
            self.dynamic(page, form, '/ydental/exam/action')
            return result
        if name in ('dispense_four','dispense_two'):
            page = self.pages['pharmacy']; self.nav(page, '/ydental/treatment')
            form = page.locator(f'article[data-order="{self.ids["prescription_order"]}"] form[data-operation=dispense]')
            form.locator('[name=lot_id]').select_option(str(f['medicine_lot']))
            form.locator('[name=quantity]').fill('4' if name == 'dispense_four' else '2')
            form.locator('[name=reason]').fill('W1 synthetic physically dispensed ' + ('four' if name == 'dispense_four' else 'two'))
            return self.dynamic(page, form, '/ydental/treatment/action')
        if name in ('finish_first','finish_final'):
            page = self.pages['pharmacy']; self.nav(page, '/ydental/treatment')
            form = page.locator(f'article[data-order="{self.ids["prescription_order"]}"] form[data-operation=finish]')
            form.locator('[name=reason]').fill('W1 synthetic end of actual dispensing segment')
            result = self.dynamic(page, form, '/ydental/treatment/action')
            if name == 'finish_first':
                article = page.locator(f'article[data-order="{self.ids["prescription_order"]}"]')
                self.ids['remainder_task'] = int(article.locator('.task-id').last.inner_text())
                assert self.ids['remainder_task'] != self.ids['pharmacy_task']
            return result
        if name in ('bill','pay_five_hundred','pay_two_forty'):
            page = self.pages['manager']; self.nav(page, '/ydental/settlement?patient_id=' + str(f['patient']))
            operation = 'bill' if name == 'bill' else 'pay'
            form = page.locator(f'form[action="/ydental/settlement/action"]:has(input[name=operation][value="{operation}"])')
            assert form.count() == 1, name
            if name == 'bill':
                boxes = form.locator('input[name=fee_ids]')
                assert boxes.count() == 4, 'four actual fee sources before bill'
                for i in range(4): boxes.nth(i).check()
            else:
                boxes = form.locator('input[name=invoice_ids]')
                assert boxes.count() == 1
                boxes.first.check()
                form.locator('[name=amount]').fill('500' if name == 'pay_five_hundred' else '240')
                form.locator('[name=channel]').select_option('wechat')
                form.locator('[name=proof]').fill('W1 synthetic offline actual payment')
            return self.html(page, form)
        raise AssertionError('Unknown W1 step ' + name)


def main():
    assert verified_target() > 0
    fixture = json.loads((RUN / 'fixture.json').read_text())
    assert fixture['database'] == NAME and fixture['oid'] == verified_target()
    assert read_complete(RUN / 'prepare-attempt.json.result')['exit_code'] == 0
    assert read_complete(RUN / 'http.attempt.json')['stage'] == 'W1_HTTP'
    pid = int((RUN / 'http.pid').read_text().strip())
    assert str(RUN / 'odoo.conf').encode() in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert not (RUN / 'browser-attempt.json').exists()
    write_once(RUN / 'browser-attempt.json', {'database': NAME, 'started': datetime.now(timezone.utc).isoformat()})
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        driver = WebDriver(browser, fixture)
        try:
            run(driver, RUN / 'browser-events.jsonl')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
