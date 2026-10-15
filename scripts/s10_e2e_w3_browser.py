"""One real Firefox pass through the W3 clinical, stock and settlement desks.

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
from s10_e2e_w3_control import NAME, PORT, RUN, endpoint, verified_target
from s10_e2e_w3_evidence import read_complete, write_once

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
            cur.execute('SELECT f.id, f.ydental_event_id, f.ydental_amount, f.ydental_price_snapshot_id, '
                        'f.ydental_patient_id, e.state, e.ydental_kind, s.ydental_unit_price, s.ydental_amount '
                        'FROM ydental_treatment_fee f JOIN ydental_treatment_event e ON e.id=f.ydental_event_id '
                        'JOIN ydental_intake_snapshot s ON s.id=f.ydental_price_snapshot_id '
                        'WHERE f.ydental_patient_id=%s ORDER BY f.id', [patient])
            out['fees'] = [dict(zip(('id','event','amount','snapshot','patient','state','kind','unit_price','snapshot_amount'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, state, amount_total, amount_residual, company_id FROM account_move '
                        "WHERE move_type='out_invoice' ORDER BY id")
            out['invoices'] = [dict(zip(('id','state','total','residual','company'), row)) for row in cur.fetchall()]
            cur.execute('SELECT p.id, p.state, p.amount, p.company_id, p.move_id, m.state '
                        'FROM account_payment p LEFT JOIN account_move m ON m.id=p.move_id ORDER BY p.id')
            out['payments'] = [dict(zip(('id','state','amount','company','move','move_state'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, amount, debit_move_id, credit_move_id FROM account_partial_reconcile ORDER BY id')
            out['partials'] = [dict(zip(('id','amount','debit','credit'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, ydental_fee_id, ydental_invoice_id, ydental_line_id, ydental_original_amount, '
                        'ydental_patient_id FROM ydental_settlement_source ORDER BY id')
            out['sources'] = [dict(zip(('id','fee','invoice','line','amount','patient'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, ydental_payment_id, ydental_amount, ydental_channel, ydental_patient_id '
                        'FROM ydental_settlement_payment ORDER BY id')
            out['offline_payments'] = [dict(zip(('id','native','amount','channel','patient'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, ydental_operation, ydental_store_id FROM ydental_settlement_receipt ORDER BY id')
            out['receipts'] = [dict(zip(('id','operation','store'), row)) for row in cur.fetchall()]
            cur.execute('SELECT id, ydental_event, ydental_result, ydental_target_model, ydental_target_id, '
                        'ydental_store_id FROM ydental_access_audit ORDER BY id')
            out['audits'] = [dict(zip(('id','event','result','model','target','store'), row)) for row in cur.fetchall()]
            cur.execute('SELECT i.id, i.ydental_lot_id, i.ydental_quantity, i.ydental_move_id, '
                        'c.ydental_event_id, m.state, m.quantity FROM ydental_inventory_event i '
                        'LEFT JOIN ydental_treatment_consumption c ON c.ydental_inventory_event_id=i.id '
                        'LEFT JOIN stock_move m ON m.id=i.ydental_move_id '
                        'ORDER BY i.id')
            out['inventory'] = [dict(zip(('id','lot','quantity','move','event','move_state','move_quantity'), row)) for row in cur.fetchall()]
            return out
    finally:
        conn.close()


def validate_transition(step, before, after):
    expected_fee_delta = 1 if step in ('treatment', 'examination', 'dispense_four', 'dispense_two') else 0
    expected_stock_delta = 1 if step in ('treatment', 'dispense_four', 'dispense_two') else 0
    assert after['ydental_treatment_fee'] - before['ydental_treatment_fee'] == expected_fee_delta
    assert after['ydental_treatment_event'] - before['ydental_treatment_event'] == expected_fee_delta
    assert after['ydental_inventory_event'] - before['ydental_inventory_event'] == expected_stock_delta
    assert after['stock_move'] - before['stock_move'] == expected_stock_delta
    assert after['ydental_settlement_source'] - before['ydental_settlement_source'] == (4 if step == 'bill' else 0)
    assert after['ydental_settlement_receipt'] - before['ydental_settlement_receipt'] == (1 if step in ('bill', 'pay_five_hundred', 'pay_two_forty') else 0)
    assert after['ydental_settlement_payment'] - before['ydental_settlement_payment'] == (1 if step in ('pay_five_hundred', 'pay_two_forty') else 0)
    assert after['account_payment'] - before['account_payment'] == (1 if step in ('pay_five_hundred', 'pay_two_forty') else 0)
    assert after['account_partial_reconcile'] - before['account_partial_reconcile'] == (1 if step in ('pay_five_hundred', 'pay_two_forty') else 0)
    fees = [Decimal(str(row['amount'])) for row in after['fees']]
    expected_fee = {'treatment': ('600', 'treatment', '600'),
                    'examination': ('80', 'exam', '80'),
                    'dispense_four': ('40', 'prescription', '10'),
                    'dispense_two': ('20', 'prescription', '10')}
    new_fees = [row for row in after['fees'] if row['id'] not in {old['id'] for old in before['fees']}]
    new_inventory = [row for row in after['inventory'] if row['id'] not in {old['id'] for old in before['inventory']}]
    if step in expected_fee:
        amount, kind, unit = expected_fee[step]
        assert len(new_fees) == 1 and Decimal(str(new_fees[0]['amount'])) == Decimal(amount)
        assert new_fees[0]['state'] == 'confirmed' and new_fees[0]['kind'] == kind
        assert Decimal(str(new_fees[0]['unit_price'])) == Decimal(unit)
        assert Decimal(str(new_fees[0]['snapshot_amount'])) == Decimal(amount)
    else:
        assert not new_fees and after['fees'] == before['fees'], ('unexpected_fee', step)
    expected_stock = {'treatment': Decimal('1'), 'dispense_four': Decimal('4'),
                      'dispense_two': Decimal('2')}
    if step in expected_stock:
        assert len(new_inventory) == 1, ('stock_delta', step, new_inventory)
        stock = new_inventory[0]
        assert stock['event'] == new_fees[0]['event'] and stock['move']
        assert stock['move_state'] == 'done' and Decimal(str(stock['move_quantity'])) == expected_stock[step]
        assert Decimal(str(stock['quantity'])) == expected_stock[step]
    else:
        assert not new_inventory and after['inventory'] == before['inventory'], ('unexpected_stock', step)
    if step not in ('bill', 'pay_five_hundred', 'pay_two_forty'):
        assert after['invoices'] == before['invoices'] and after['payments'] == before['payments'] and after['partials'] == before['partials']
        assert after['sources'] == before['sources'] and after['offline_payments'] == before['offline_payments']
        assert after['receipts'] == before['receipts']
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
    if step == 'bill':
        assert not before['invoices'] and len(after['invoices']) == 1
        assert after['payments'] == before['payments'] and after['partials'] == before['partials']
        assert len(after['sources']) == 4 and not before['sources']
        assert {row['fee'] for row in after['sources']} == {row['id'] for row in after['fees']}
        assert all(row['invoice'] == after['invoices'][0]['id'] and row['patient'] == after['fees'][0]['patient'] for row in after['sources'])
        assert sum(Decimal(str(row['amount'])) for row in after['sources']) == Decimal('740')
        assert len(after['receipts']) == len(before['receipts']) + 1 and after['receipts'][-1]['operation'] == 'bill'
    if step in ('pay_five_hundred', 'pay_two_forty'):
        assert after['fees'] == before['fees'] and len(after['payments']) == len(before['payments']) + 1
        assert len(after['partials']) == len(before['partials']) + 1
        assert after['sources'] == before['sources']
        assert len(after['offline_payments']) == len(before['offline_payments']) + 1
        offline = after['offline_payments'][-1]
        assert offline['native'] == after['payments'][-1]['id'] and offline['channel'] == 'cash'
        assert after['payments'][-1]['move'] and after['payments'][-1]['move_state'] == 'posted'
        assert Decimal(str(offline['amount'])) == Decimal('500' if step == 'pay_five_hundred' else '240')
        assert len(after['receipts']) == len(before['receipts']) + 1 and after['receipts'][-1]['operation'] == 'pay'
    assert all(row['result'] == 'accepted' for row in after['audits'] if row['id'] not in {old['id'] for old in before['audits']})


def run(driver, evidence_path):
    driver.action_path = evidence_path.with_name('browser-actions.jsonl')
    driver.open_roles()
    before = driver.snapshot()
    assert before['fees'] == before['invoices'] == before['payments'] == before['partials'] == []
    assert before['sources'] == before['offline_payments'] == before['receipts'] == []
    for number, (name, kind, amount) in enumerate(STEPS, 1):
        driver.current_step = name
        outcome = driver.perform(name)
        assert outcome['status'] == 'WEB_ACTUAL' and outcome['http_status'] in (200, 303), (name, outcome)
        after = driver.snapshot()
        validate_transition(name, before, after)
        screenshot = driver.capture(number, name, evidence_path.parent)
        event(evidence_path, {'number': number, 'name': name, 'classification': kind,
                              'amount': amount, 'request': outcome,
                              'before': before, 'after': after,
                              'screenshot': screenshot,
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
        self.page_errors = []

    def task_row(self, task_id, mapping_id=None):
        """Read the committed task identity independently of the Web response."""
        conn = psycopg2.connect(dbname=NAME, **endpoint())
        conn.set_session(readonly=True)
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT ydental_patient_id, ydental_store_id, ydental_mapping_id, '
                            'state, ydental_version FROM ydental_intake_task WHERE id=%s', [task_id])
                rows = cur.fetchall()
                assert len(rows) == 1, ('task_identity', task_id)
                patient, store, mapping, state, version = rows[0]
                assert (patient, store) == (self.fixture['patient'], self.fixture['store'])
                if mapping_id is not None:
                    assert mapping == mapping_id, ('task_mapping', task_id, mapping)
                return {'id': task_id, 'mapping': mapping, 'state': state, 'version': version}
        finally:
            conn.close()

    def issued_task(self, kind, order_id, sequence=1):
        """Resolve an issued order through its real line and task or segment."""
        conn = psycopg2.connect(dbname=NAME, **endpoint())
        conn.set_session(readonly=True)
        try:
            with conn.cursor() as cur:
                if kind == 'exam':
                    cur.execute('SELECT l.id, l.ydental_task_id, l.ydental_mapping_id '
                                'FROM ydental_treatment_line l JOIN ydental_treatment_order o '
                                'ON o.id=l.ydental_order_id WHERE o.id=%s AND o.state=%s '
                                'AND o.ydental_kind=%s AND l.state=%s AND o.ydental_patient_id=%s '
                                'AND o.ydental_store_id=%s',
                                [order_id, 'issued', 'exam', 'issued', self.fixture['patient'], self.fixture['store']])
                    rows = cur.fetchall()
                    assert len(rows) == 1, ('issued_exam_line', order_id, rows)
                    line_id, task_id, mapping_id = rows[0]
                else:
                    cur.execute('SELECT l.id, s.ydental_task_id, l.ydental_mapping_id '
                                'FROM ydental_treatment_line l JOIN ydental_treatment_order o '
                                'ON o.id=l.ydental_order_id JOIN ydental_treatment_segment s '
                                'ON s.ydental_order_id=o.id WHERE o.id=%s AND o.state=%s '
                                'AND o.ydental_kind=%s AND l.state=%s AND s.ydental_sequence=%s '
                                'AND s.state=%s AND o.ydental_patient_id=%s AND o.ydental_store_id=%s',
                                [order_id, 'issued', 'prescription', 'issued', sequence, 'pending',
                                 self.fixture['patient'], self.fixture['store']])
                    rows = cur.fetchall()
                    assert len(rows) == 1, ('issued_pharmacy_segment', order_id, sequence, rows)
                    line_id, task_id, mapping_id = rows[0]
                assert type(task_id) is int and task_id > 0
                task = self.task_row(task_id, mapping_id)
                assert task['state'] == 'pending', task
                return line_id, task_id
        finally:
            conn.close()

    def queue_report_form(self, task_id):
        task = self.task_row(task_id)
        assert task['state'] == 'pending', task
        page = self.pages['front']
        self.nav(page, '/ydental/queue')
        item = page.locator(f'#continuation-reception [data-pending-task="{task_id}"]')
        assert item.count() == 1, ('pending_queue_item', task_id)
        form = item.locator('form[data-queue-form="report"]')
        assert form.count() == 1, ('report_form', task_id)
        assert form.locator('input[name="task_id"]').input_value() == str(task_id)
        assert form.locator('input[name="version"]').input_value() == str(task['version'])
        return page, form

    def snapshot(self):
        return snapshot(NAME, self.fixture['patient'])

    def record_action(self, outcome):
        event(self.action_path, {'step': self.current_step, 'response': outcome,
                                 'time': datetime.now(timezone.utc)})
        return outcome

    def capture(self, number, name, evidence_dir):
        roles = {'reserve': 'front', 'arrive': 'front', 'report_care': 'front',
                 'care_start': 'doctor', 'document': 'doctor', 'treatment': 'doctor',
                 'exam_order': 'doctor', 'prescription': 'doctor', 'care_handover': 'doctor',
                 'report_exam': 'front', 'exam_start': 'exam', 'examination': 'exam',
                 'report_pharmacy': 'front', 'pharmacy_start': 'pharmacy',
                 'dispense_four': 'pharmacy', 'finish_first': 'pharmacy',
                 'report_remainder': 'front', 'pharmacy_restart': 'pharmacy',
                 'dispense_two': 'pharmacy', 'finish_final': 'pharmacy',
                 'bill': 'manager', 'pay_five_hundred': 'manager', 'pay_two_forty': 'manager'}
        assert not self.page_errors and name in roles
        directory = evidence_dir / 'screenshots'
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / f'{number:02d}-{name}.png'
        assert not path.exists()
        self.pages[roles[name]].screenshot(path=str(path), full_page=True)
        os.chmod(path, 0o600)
        return {'file': str(path.relative_to(evidence_dir)), 'sha256': digest(path)}

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
        page.set_default_timeout(8000)
        page.set_default_navigation_timeout(20000)
        page.on('pageerror', lambda exc: self.page_errors.append(str(exc)))
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
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        r = page.goto(self.base + path, wait_until='domcontentloaded')
        assert r.status == 200, (path, r.status)
        assert not self.page_errors, ('browser_pageerror', self.page_errors)

    def html(self, page, form):
        assert form.count() == 1 and form.evaluate('(f)=>f.checkValidity()'), 'missing or invalid HTML form'
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        endpoint = form.get_attribute('action')
        with page.expect_response(lambda r: r.request.method == 'POST') as reply:
            with page.expect_navigation(wait_until='domcontentloaded'):
                form.locator('button[type=submit],button:not([type])').first.click()
        status = reply.value.status
        assert status in (200, 303), status
        assert reply.value.request.method == 'POST'
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        if endpoint == '/ydental/settlement/action':
            assert status == 303, ('settlement_http_class', status)
            feedback = page.locator('[data-ui1-feedback="1"]')
            assert feedback.count() == 1 and '操作已受理' in feedback.inner_text(), ('settlement_feedback', page.url)
        return self.record_action({'status': 'WEB_ACTUAL', 'http_status': status,
                'url': urlsplit(reply.value.url).path, 'method': reply.value.request.method,
                'content_type': reply.value.headers.get('content-type', '')})

    def dynamic(self, page, form, endpoint):
        assert form.count() == 1 and form.evaluate('(f)=>f.checkValidity()'), 'missing or invalid dynamic form'
        assert form.get_attribute('data-allowed') == 'true', ('action_not_allowed', endpoint)
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        page.once('dialog', lambda dialog: dialog.accept())
        with page.expect_response('**' + endpoint) as response:
            with page.expect_navigation(wait_until='domcontentloaded'):
                form.locator('button[type=submit]').click()
        reply = response.value
        assert reply.status == 200, (endpoint, reply.status, reply.text()[:200])
        assert reply.request.method == 'POST' and 'application/json' in reply.headers.get('content-type', '')
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        return self.record_action({'status': 'WEB_ACTUAL', 'http_status': reply.status,
                'url': urlsplit(reply.url).path, 'method': reply.request.method,
                'content_type': reply.headers.get('content-type', '')})

    def queue_click(self, page, selector):
        assert page.locator(selector).count() == 1, selector
        assert page.locator(selector).is_enabled(), ('queue_action_disabled', selector)
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        with page.expect_response('**/ydental/queue/action') as response:
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator(selector).click()
        assert response.value.status == 200, (selector, response.value.status)
        assert response.value.request.method == 'POST' and 'application/json' in response.value.headers.get('content-type', '')
        assert not self.page_errors, ('browser_pageerror', self.page_errors)
        return self.record_action({'status': 'WEB_ACTUAL', 'http_status': response.value.status,
                'url': '/ydental/queue/action', 'method': response.value.request.method,
                'content_type': response.value.headers.get('content-type', '')})

    def perform(self, name):
        f = self.fixture
        if name == 'reserve':
            page = self.pages['front']
            self.nav(page, '/ydental/intake')
            form = page.locator('#intake-create form').first
            assert form.count() == 1
            form.locator('[name=operation]').select_option('reserve')
            form.locator('[name=patient_id]').select_option(str(f['patient']))
            form.locator('[name=mapping_id]').select_option(str(f['care_mapping']))
            form.locator('[name=start]').fill(f['slot_start'].replace(' ', 'T')[:16])
            form.locator('[name=end]').fill(f['slot_end'].replace(' ', 'T')[:16])
            result = self.html(page, form)
            rows = page.locator('#intake-tasks tr[data-task]')
            assert rows.count() == 1, 'only one new care task is allowed'
            self.ids['care_task'] = int(rows.first.get_attribute('data-task'))
            assert self.task_row(self.ids['care_task'], f['care_mapping'])['state'] == 'pending'
            return result
        if name == 'arrive':
            page = self.pages['front']; self.nav(page, '/ydental/intake')
            form = page.locator('#intake-create form').nth(1)
            assert form.count() == 1
            form.locator('[name=patient_id]').select_option(str(f['patient']))
            return self.html(page, form)
        if name.startswith('report_'):
            key = {'report_care':'care_task','report_exam':'exam_task',
                   'report_pharmacy':'pharmacy_task','report_remainder':'remainder_task'}[name]
            page, form = self.queue_report_form(self.ids[key])
            return self.html(page, form)
        if name in ('care_start', 'exam_start', 'pharmacy_start', 'pharmacy_restart'):
            role = 'doctor' if name == 'care_start' else 'exam' if name == 'exam_start' else 'pharmacy'
            page = self.pages[role]; self.nav(page, '/ydental/queue')
            station = f['care_station'] if role == 'doctor' else f['exam_station'] if role == 'exam' else f['pharmacy_station']
            if not page.locator('#holding-workstation').count():
                self.queue_click(page, f'button[data-operation=enter][data-station="{station}"]')
            self.queue_click(page, 'button[data-operation=call]')
            task_key = 'care_task' if role == 'doctor' else 'exam_task' if role == 'exam' else ('pharmacy_task' if name == 'pharmacy_start' else 'remainder_task')
            row = f'tr[data-task="{self.ids[task_key]}"]'
            assert page.locator(row).count() == 1 and page.locator(row + ' .queue-state').inner_text() == 'calling'
            result = self.queue_click(page, row + ' button[data-operation=start]')
            self.nav(page, '/ydental/clinical' if role == 'doctor' else '/ydental/exam' if role == 'exam' else '/ydental/treatment')
            return result
        if name == 'document':
            page = self.pages['doctor']
            assert page.locator('#open-document').count() == 1
            page.locator('#open-document').click()
            page.wait_for_function('document.querySelector("textarea[name=chief_complaint]") && !document.querySelector("textarea[name=chief_complaint]").disabled', timeout=8000)
            page.locator('[name=chief_complaint]').fill('W3 synthetic documented treatment reason')
            with page.expect_response('**/ydental/clinical/action') as response:
                page.locator('#save-document').click()
            assert response.value.status == 200 and response.value.request.method == 'POST'
            page.wait_for_function('Number(document.querySelector("#server-version").textContent)>0', timeout=8000)
            return self.record_action({'status':'WEB_ACTUAL','http_status':200,
                                       'url':'/ydental/clinical/action','method':'POST'})
        if name == 'treatment':
            page = self.pages['doctor']; self.nav(page, '/ydental/treatment')
            form = page.locator('form[data-operation=execute]')
            assert form.count() == 1
            form.locator('[name=catalog_id]').select_option(str(f['care_catalog']))
            form.locator('[name=quantity]').fill('1'); form.locator('[name=tooth]').fill('16')
            form.locator('[name=tooth_state]').select_option('present')
            form.locator('[name=surfaces]').fill('O')
            form.locator('[name=lot_id]').select_option(str(f['material_lot']))
            form.locator('[name=material_quantity]').fill('1')
            form.locator('[name=reason]').fill('W3 synthetic actual physical treatment')
            return self.dynamic(page, form, '/ydental/treatment/action')
        if name in ('exam_order','prescription'):
            page = self.pages['doctor']; self.nav(page, '/ydental/treatment')
            form = page.locator('form[data-operation=order]')
            assert form.count() == 1
            kind = 'exam' if name == 'exam_order' else 'prescription'
            form.locator('[name=kind]').select_option(kind)
            form.locator('[name=purpose]').fill('W3 synthetic ' + kind + ' clinical order')
            line = form.locator('.o_ydental_treatment_line')
            line.locator('[name=mapping_id]').select_option(str(f['exam_mapping'] if kind == 'exam' else f['pharmacy_mapping']))
            line.locator('[name=quantity]').fill('1' if kind == 'exam' else '6')
            if kind == 'prescription':
                line.locator('[name=product_id]').select_option(str(f['medicine_product']))
                for field in ('specification','usage','frequency','course'):
                    line.locator('[name='+field+']').fill('W3 synthetic reviewed ' + field)
            self.dynamic(page, form, '/ydental/treatment/action')
            article = page.locator(f'article[data-order-kind="{kind}"]').last
            assert article.count() == 1, ('draft_order_missing', kind)
            order = int(article.get_attribute('data-order'))
            result = self.dynamic(page, article.locator('form[data-operation=issue]'), '/ydental/treatment/action')
            article = page.locator(f'article[data-order="{order}"]')
            self.ids[kind + '_order'] = order
            assert article.count() == 1
            line_id, task_id = self.issued_task(kind, order)
            assert article.locator(f'tr[data-line="{line_id}"]').count() == 1
            self.ids[kind + '_line'] = line_id
            self.ids['exam_task' if kind == 'exam' else 'pharmacy_task'] = task_id
            return result
        if name == 'care_handover':
            page = self.pages['doctor']; self.nav(page, '/ydental/clinical')
            assert page.locator('#open-document').count() == 1
            page.locator('#open-document').click()
            page.wait_for_function('document.querySelector("textarea[name=chief_complaint]") && !document.querySelector("textarea[name=chief_complaint]").disabled', timeout=8000)
            with page.expect_response('**/ydental/clinical/action') as response:
                page.locator('#handover-document').click()
            assert response.value.status == 200 and response.value.request.method == 'POST'
            self.record_action({'status':'WEB_ACTUAL','http_status':200,
                                'url':'/ydental/clinical/action','method':'POST'})
            self.nav(page, '/ydental/queue')
            return self.queue_click(page, 'button[data-operation=exit]')
        if name == 'examination':
            page = self.pages['exam']; self.nav(page, '/ydental/exam')
            panel = page.locator(f'section[data-line]')
            assert panel.count() == 1, 'exactly one ordered examination required'
            form = panel.locator('form[data-operation=draft]')
            form.locator('[name=findings]').fill('W3 synthetic actual examined finding')
            self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=perform]')
            form.locator('[name=reason]').fill('W3 synthetic actual completed examination')
            result = self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=confirm]')
            form.locator('[name=reason]').fill('W3 synthetic examined result review')
            self.dynamic(page, form, '/ydental/exam/action')
            panel = page.locator('section[data-line]')
            form = panel.locator('form[data-operation=finish]')
            form.locator('[name=reason]').fill('W3 synthetic examination segment complete')
            self.dynamic(page, form, '/ydental/exam/action')
            return result
        if name in ('dispense_four','dispense_two'):
            page = self.pages['pharmacy']; self.nav(page, '/ydental/treatment')
            form = page.locator(f'article[data-order="{self.ids["prescription_order"]}"] form[data-operation=dispense]')
            form.locator('[name=lot_id]').select_option(str(f['medicine_lot']))
            form.locator('[name=quantity]').fill('4' if name == 'dispense_four' else '2')
            form.locator('[name=reason]').fill('W3 synthetic physically dispensed ' + ('four' if name == 'dispense_four' else 'two'))
            return self.dynamic(page, form, '/ydental/treatment/action')
        if name in ('finish_first','finish_final'):
            page = self.pages['pharmacy']; self.nav(page, '/ydental/treatment')
            form = page.locator(f'article[data-order="{self.ids["prescription_order"]}"] form[data-operation=finish]')
            form.locator('[name=reason]').fill('W3 synthetic end of actual dispensing segment')
            result = self.dynamic(page, form, '/ydental/treatment/action')
            if name == 'finish_first':
                line_id, task_id = self.issued_task('prescription', self.ids['prescription_order'], sequence=2)
                assert line_id == self.ids['prescription_line']
                self.ids['remainder_task'] = task_id
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
                fee_ids = [int(boxes.nth(i).get_attribute('value')) for i in range(4)]
                actual = self.snapshot()
                assert sorted(fee_ids) == sorted(row['id'] for row in actual['fees'])
                assert [Decimal(str(row['amount'])) for row in actual['fees']] == [Decimal('600'), Decimal('80'), Decimal('40'), Decimal('20')]
                assert not actual['invoices'] and not actual['payments']
                for i in range(4): boxes.nth(i).check()
            else:
                boxes = form.locator('input[name=invoice_ids]')
                assert boxes.count() == 1
                actual = self.snapshot()
                assert int(boxes.first.get_attribute('value')) == actual['invoices'][0]['id']
                boxes.first.check()
                form.locator('[name=amount]').fill('500' if name == 'pay_five_hundred' else '240')
                form.locator('[name=channel]').select_option('cash')
                assert form.locator('[name=actual_utc]').input_value()
                form.locator('[name=proof]').fill('W3 synthetic offline cash receipt')
            return self.html(page, form)
        raise AssertionError('Unknown W3 step ' + name)


def main():
    assert verified_target() > 0
    fixture = json.loads((RUN / 'fixture.json').read_text())
    assert fixture['database'] == NAME and fixture['oid'] == verified_target()
    assert read_complete(RUN / 'prepare-attempt.json.result')['exit_code'] == 0
    assert read_complete(RUN / 'http.attempt.json')['stage'] == 'W3_HTTP'
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
