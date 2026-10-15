"""Run the actual W3 dispatcher and event writer against a bounded fake Web/SQL seam.

This is a programming contract check. It makes no claim about a real browser.
"""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile
from urllib.parse import urlsplit
from unittest.mock import patch

import s10_e2e_w3_browser as browser
from s10_e2e_w3_browser import STEPS, WebDriver, run


class FakeResponse:
    def __init__(self, url, status=200):
        self.url = url
        self.status = status
        self.headers = {'content-type': 'text/html' if status == 303 else 'application/json'}
        self.request = type('FakeRequest', (), {'method': 'POST'})()

    def text(self):
        return 'SIMULATED_RESPONSE'


class FakeContext:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


class FakeSQLConnection:
    def __init__(self, driver):
        self.driver = driver
        self.readonly = False

    def set_session(self, readonly=False):
        assert readonly is True
        self.readonly = True

    def cursor(self):
        assert self.readonly
        return FakeSQLCursor(self.driver)

    def close(self):
        return None


class FakeSQLCursor:
    def __init__(self, driver):
        self.driver = driver
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def execute(self, query, params):
        driver = self.driver
        assert query.startswith('SELECT ') and isinstance(params, list)
        if 'FROM ydental_intake_task' in query:
            task_id = params[0]
            mappings = {101: 21, 301: 22, 302: 23, 303: 23}
            assert task_id in mappings
            driver.current_task = task_id
            self.rows = [(100, 99 if driver.wrong_task_at == driver.current else 1,
                          mappings[task_id], 'pending', 1)]
        elif 'JOIN ydental_treatment_segment' in query:
            assert params[0:4] == [202, 'issued', 'prescription', 'issued']
            sequence = params[4]
            assert sequence in (1, 2) and params[-2:] == [100, 1]
            self.rows = [] if driver.unissued_at == driver.current else [
                (402, 302 if sequence == 1 else 303, 23)]
        elif 'JOIN ydental_treatment_order' in query:
            assert params == [201, 'issued', 'exam', 'issued', 100, 1]
            self.rows = [] if driver.unissued_at == driver.current else [(401, 301, 22)]
        else:
            raise AssertionError(('unexpected_sql', query))

    def fetchall(self):
        return self.rows


class FakeLocator:
    def __init__(self, page, selector='', index=None):
        self.page = page
        self.selector = selector
        self.index = index

    def locator(self, selector):
        return FakeLocator(self.page, self.selector + ' ' + selector)

    @property
    def first(self):
        return self.nth(0)

    @property
    def last(self):
        return self.nth(self.count() - 1)

    def nth(self, index):
        return FakeLocator(self.page, self.selector, index)

    def count(self):
        driver = self.page.driver
        if driver.missing_at == driver.current and driver.missing_selector in self.selector:
            return 0
        if '.task-id' in self.selector and self.page.role != 'pharmacy':
            return 0
        if 'input[name=fee_ids]' in self.selector:
            return 1 if self.index is not None else len(driver.data['fees'])
        if 'input[name=invoice_ids]' in self.selector:
            return 1 if self.index is not None else len(driver.data['invoices'])
        return 1

    def evaluate(self, script):
        assert 'checkValidity' in script
        return self.page.driver.invalid_at != self.page.driver.current

    def is_enabled(self):
        return not (self.page.driver.disabled_at == self.page.driver.current and
                    'data-operation' in self.selector)

    def fill(self, value):
        assert isinstance(value, str) and value != ''

    def select_option(self, value):
        assert str(value)

    def check(self):
        assert self.count() == 1

    def click(self):
        assert self.count() == 1
        return None

    def inner_text(self):
        if '.queue-state' in self.selector:
            return 'calling'
        if 'data-ui1-feedback' in self.selector:
            return '请求未完成' if self.page.driver.denied_at == self.page.driver.current else '操作已受理，请核对下方业务记录。'
        if '.task-id' in self.selector:
            raise AssertionError('Fake QWeb: examination has no segment task label')
        return 'SIMULATED_TEXT'

    def input_value(self):
        if 'name="task_id"' in self.selector:
            return str(self.page.driver.current_task)
        if 'name="version"' in self.selector:
            return '1'
        if 'name=actual_utc' in self.selector:
            return '2026-10-15T06:00:00+00:00'
        return 'SIMULATED_VALUE'

    def get_attribute(self, name):
        driver = self.page.driver
        if name == 'data-task':
            return '101'
        if name == 'data-order':
            return '201' if 'exam' in self.selector else '202'
        if name == 'data-allowed':
            return 'false' if driver.old_revision_at == driver.current else 'true'
        if name == 'action':
            return '/ydental/settlement/action' if '/ydental/settlement/action' in self.selector else '/ydental/intake/action'
        if name == 'value':
            if 'fee_ids' in self.selector:
                return str(driver.data['fees'][self.index]['id'])
            if 'invoice_ids' in self.selector:
                return str(driver.data['invoices'][self.index]['id'])
        raise AssertionError(('unexpected_attribute', name, self.selector))


class FakePage:
    def __init__(self, role, driver):
        self.role = role
        self.driver = driver
        self.url = 'http://127.0.0.1:18278/ydental/access'

    def goto(self, url, **_kwargs):
        self.url = url
        return FakeResponse(url)

    def locator(self, selector):
        return FakeLocator(self, selector)

    def expect_response(self, expected):
        path = expected.removeprefix('**') if isinstance(expected, str) else (
            '/ydental/settlement/action' if self.driver.current in ('bill', 'pay_five_hundred', 'pay_two_forty') else
            '/ydental/intake/action' if self.driver.current in ('reserve', 'arrive', 'report_care', 'report_exam', 'report_pharmacy', 'report_remainder') else
            '/ydental/queue/action')
        status = 303 if path in ('/ydental/settlement/action', '/ydental/intake/action') and self.driver.current in ('reserve', 'arrive', 'bill', 'pay_five_hundred', 'pay_two_forty') else 200
        if self.driver.http_fail_at == self.driver.current:
            status = 409
        return FakeContext(FakeResponse('http://127.0.0.1:18278' + path, status))

    def expect_navigation(self, **_kwargs):
        return FakeContext(None)

    def once(self, _name, _callback):
        return None

    def wait_for_function(self, _expression, **_kwargs):
        return True

    def screenshot(self, path, full_page=False):
        assert full_page is True
        Path(path).write_bytes(b'SIMULATED_PNG_' + self.role.encode())


class FakeWebDriver(WebDriver):
    def __init__(self, **faults):
        self.base = 'http://127.0.0.1:18278'
        self.fixture = {'patient': 100, 'store': 1, 'care_station': 11,
            'exam_station': 12, 'pharmacy_station': 13, 'care_mapping': 21,
            'exam_mapping': 22, 'pharmacy_mapping': 23, 'care_catalog': 31,
            'medicine_product': 32, 'material_lot': 33, 'medicine_lot': 34,
            'slot_start': '2026-10-15 12:00:00', 'slot_end': '2026-10-15 15:00:00'}
        self.pages = {role: FakePage(role, self) for role in ('front', 'doctor', 'exam', 'pharmacy', 'manager')}
        self.ids = {}
        self.current = None
        self.current_task = 101
        self.data = {'fees': [], 'invoices': [], 'payments': [], 'partials': [], 'inventory': [],
                     'sources': [], 'offline_payments': [], 'receipts': [], 'audits': []}
        self.page_errors = []
        self.missing_at = faults.get('missing_at')
        self.missing_selector = faults.get('missing_selector', 'form')
        self.invalid_at = faults.get('invalid_at')
        self.disabled_at = faults.get('disabled_at')
        self.old_revision_at = faults.get('old_revision_at')
        self.http_fail_at = faults.get('http_fail_at')
        self.denied_at = faults.get('denied_at')
        self.wrong_task_at = faults.get('wrong_task_at')
        self.unissued_at = faults.get('unissued_at')
        self.extra_fee_at = faults.get('extra_fee_at')
        self.preexisting_invoice_at = faults.get('preexisting_invoice_at')
        self.wrong_amount_at = faults.get('wrong_amount_at')

    def open_roles(self):
        assert set(self.pages) == {'front', 'doctor', 'exam', 'pharmacy', 'manager'}

    def snapshot(self):
        result = deepcopy(self.data)
        counts = {'ydental_treatment_event': len(result['fees']),
                  'ydental_treatment_fee': len(result['fees']),
                  'ydental_inventory_event': len(result['inventory']),
                  'stock_move': len(result['inventory']),
                  'ydental_settlement_source': len(result['sources']),
                  'ydental_settlement_receipt': len(result['receipts']),
                  'ydental_settlement_payment': len(result['offline_payments']),
                  'account_payment': len(result['payments']),
                  'account_partial_reconcile': len(result['partials'])}
        result.update(counts)
        return result

    def perform(self, name):
        self.current = name
        if name == self.preexisting_invoice_at:
            self.data['invoices'].append({'id': 999, 'state': 'posted', 'total': Decimal('1'), 'residual': Decimal('1')})
        result = super().perform(name)
        if name in ('treatment', 'examination', 'dispense_four', 'dispense_two'):
            amount = '39' if name == self.wrong_amount_at else {'treatment': '600', 'examination': '80', 'dispense_four': '40', 'dispense_two': '20'}[name]
            kind = 'treatment' if name == 'treatment' else 'exam' if name == 'examination' else 'prescription'
            unit = '600' if name == 'treatment' else '80' if name == 'examination' else '10'
            fee_id = 1000 + len(self.data['fees'])
            self.data['fees'].append({'id': fee_id, 'event': fee_id + 100, 'amount': Decimal(amount),
                                      'patient': 100,
                                      'state': 'confirmed', 'kind': kind, 'unit_price': Decimal(unit),
                                      'snapshot_amount': Decimal(amount)})
            if name != 'examination':
                quantity = {'treatment': 1, 'dispense_four': 4, 'dispense_two': 2}[name]
                self.data['inventory'].append({'id': 5000 + len(self.data['inventory']), 'event': fee_id + 100,
                                               'move': 6000 + len(self.data['inventory']),
                                               'quantity': quantity, 'move_quantity': quantity,
                                               'move_state': 'done'})
        elif name == 'bill':
            self.data['invoices'].append({'id': 2000, 'state': 'posted', 'total': Decimal('740'), 'residual': Decimal('740')})
            for fee in self.data['fees']:
                self.data['sources'].append({'id': 7000 + len(self.data['sources']), 'fee': fee['id'],
                                             'invoice': 2000, 'line': 8000 + len(self.data['sources']),
                                             'amount': fee['amount'], 'patient': 100})
            self.data['receipts'].append({'id': 9001, 'operation': 'bill', 'store': 1})
        elif name in ('pay_five_hundred', 'pay_two_forty'):
            amount = Decimal('500' if name == 'pay_five_hundred' else '240')
            payment_id = 3000 + len(self.data['payments'])
            self.data['payments'].append({'id': payment_id, 'amount': amount,
                                          'move': 3500 + len(self.data['payments']), 'move_state': 'posted'})
            self.data['partials'].append({'id': 4000 + len(self.data['partials']), 'amount': amount})
            self.data['offline_payments'].append({'id': 5000 + len(self.data['offline_payments']),
                                                  'native': payment_id, 'amount': amount,
                                                  'channel': 'cash', 'patient': 100})
            self.data['receipts'].append({'id': 9000 + len(self.data['receipts']) + 1,
                                          'operation': 'pay', 'store': 1})
            self.data['invoices'][0]['residual'] -= amount
        self.data['audits'].append({'id': 10000 + len(self.data['audits']), 'event': name,
                                    'result': 'accepted', 'model': 'simulated', 'target': 1, 'store': 1})
        if name == self.extra_fee_at:
            self.data['fees'].append({'id': 1999, 'amount': Decimal('1')})
        return result


def one_case(**faults):
    with tempfile.TemporaryDirectory(prefix='s10-w3-offline-') as tmp:
        path = Path(tmp) / 'events.jsonl'
        driver = FakeWebDriver(**faults)
        failed = False
        try:
            with patch.object(browser.psycopg2, 'connect', side_effect=lambda **_kwargs: FakeSQLConnection(driver)):
                run(driver, path)
        except (AssertionError, RuntimeError, IndexError, ValueError, KeyError) as error:
            failed = True
            if not faults:
                raise AssertionError(f'Unexpected fake failure at {driver.current}: {error}') from error
        assert failed == bool(faults), (faults, driver.current)
        complete = path.with_suffix('.complete.json')
        assert complete.exists() != bool(faults)
        events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        actions_path = path.with_name('browser-actions.jsonl')
        actions = [json.loads(line) for line in actions_path.read_text().splitlines()] if actions_path.exists() else []
        assert all(row['number'] == index and row['request']['method'] == 'POST'
                   for index, row in enumerate(events, 1))
        assert all(row['response']['method'] == 'POST' and row['step'] in {step[0] for step in STEPS}
                   for row in actions)
        assert all((path.parent / row['screenshot']['file']).is_file() and len(row['screenshot']['sha256']) == 64
                   for row in events)
        assert len(events) == (len(STEPS) if not faults else STEPS.index(next(s for s in STEPS if s[0] == driver.current)))
        if not faults:
            assert events[5]['amount'] == {'decimal': '600'}
            assert events[-1]['time']['datetime'].endswith('+00:00')
            assert json.loads(complete.read_text())['steps'] == 23
            assert {row['step'] for row in actions} == {step[0] for step in STEPS}
            assert len(actions) > len(STEPS)
        return len(events)


def main():
    one_case()
    for name, _, _ in STEPS:
        selector = '#open-document' if name == 'document' else 'button' if name in (
            'care_start', 'exam_start', 'pharmacy_start', 'pharmacy_restart', 'care_handover') else 'form'
        one_case(missing_at=name, missing_selector=selector)
    for fault in (
        {'invalid_at': 'reserve'}, {'invalid_at': 'treatment'}, {'invalid_at': 'pay_five_hundred'},
        {'disabled_at': 'care_start'}, {'old_revision_at': 'prescription'},
        {'http_fail_at': 'exam_order'}, {'http_fail_at': 'bill'},
        {'http_fail_at': 'report_exam'}, {'http_fail_at': 'finish_first'},
        {'denied_at': 'pay_five_hundred'}, {'wrong_task_at': 'report_exam'},
        {'unissued_at': 'exam_order'}, {'extra_fee_at': 'treatment'},
        {'preexisting_invoice_at': 'bill'}, {'wrong_amount_at': 'dispense_four'},
    ):
        one_case(**fault)
    print(json.dumps({'status': 'SIMULATED_PASS', 'actual_run_and_perform': True,
                      'real_event_writer': True, 'steps': len(STEPS), 'negative_cases': len(STEPS) + 15}))


if __name__ == '__main__':
    main()
