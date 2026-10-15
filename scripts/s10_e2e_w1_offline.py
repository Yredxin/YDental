"""Offline gate for actual W1 browser dispatch, evidence and failure stops."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile

from s10_e2e_w1_browser import STEPS, WebDriver, run


class FakeLocator:
    def __init__(self, page, selector=''):
        self.page = page
        self.selector = selector
        self.values = {}

    def locator(self, selector):
        return FakeLocator(self.page, self.selector + ' ' + selector)

    @property
    def first(self): return self

    @property
    def last(self): return self

    def nth(self, _index): return self

    def count(self):
        if 'input[name=fee_ids]' in self.selector:
            return len(self.page.driver.data['fees'])
        return 1

    def evaluate(self, script):
        if 'checkValidity' in script:
            return self.page.valid
        return True

    def fill(self, value):
        assert isinstance(value, str) and value != ''
        self.values['fill'] = value

    def select_option(self, value):
        assert str(value)
        self.values['select'] = value

    def check(self): self.values['checked'] = True

    def click(self): return None

    def inner_text(self):
        if '.task-id' in self.selector:
            if self.page.role == 'pharmacy': return '303'
            return '301' if 'data-order="201"' in self.selector else '302'
        return '1'

    def get_attribute(self, name):
        if name == 'data-task': return '101'
        if name == 'data-order':
            return '201' if 'exam' in self.selector else '202'
        return '1'


class FakePage:
    def __init__(self, role):
        self.role = role
        self.valid = True

    def locator(self, selector): return FakeLocator(self, selector)

    def wait_for_function(self, _script): return True

    def wait_for_timeout(self, _duration): return None

    def expect_response(self, endpoint):
        assert endpoint == '**/ydental/clinical/action'
        class ResponseContext:
            value = type('Response', (), {'status':200})()
            def __enter__(self): return self
            def __exit__(self, *_args): return None
        return ResponseContext()


class FakeWebDriver(WebDriver):
    """Use the production perform() branches with fake HTTP, browser and DOM."""

    def __init__(self, fail_at=None, invalid_at=None, repeat_at=None, missing_role=None):
        self.fixture = {'patient': 100, 'store': 1, 'care_station': 11,
            'exam_station': 12, 'pharmacy_station': 13, 'care_mapping': 21,
            'exam_mapping': 22, 'pharmacy_mapping': 23,
            'care_catalog': 31, 'medicine_product': 32,
            'material_lot': 33, 'medicine_lot': 34,
            'slot_start': '2026-10-15 12:00:00',
            'slot_end': '2026-10-15 15:00:00'}
        self.pages = {role: FakePage(role) for role in ('front','doctor','exam','pharmacy','manager')}
        for page in self.pages.values(): page.driver = self
        self.ids = {}
        self.fail_at = fail_at
        self.invalid_at = invalid_at
        self.repeat_at = repeat_at
        self.missing_role = missing_role
        self.current = None
        self.data = {'fees':[], 'invoices':[], 'payments':[], 'partials':[], 'inventory':[]}

    def snapshot(self): return deepcopy(self.data)

    def open_roles(self):
        assert set(self.pages) == {'front','doctor','exam','pharmacy','manager'}
        if self.missing_role:
            raise RuntimeError('SIMULATED missing business role ' + self.missing_role)

    def nav(self, page, path):
        assert path.startswith('/ydental/')
        return None

    def html(self, page, form):
        assert form.evaluate('(f)=>f.checkValidity()'), 'HTML5 required field rejected submission'
        assert self.current != self.fail_at, 'Fake HTML POST failure'
        return {'status':'WEB_ACTUAL','http_status':303,'url':'/ydental/action','method':'POST'}

    def dynamic(self, page, form, endpoint):
        assert form.evaluate('(f)=>f.checkValidity()'), 'HTML5 required field rejected submission'
        assert self.current != self.fail_at, 'Fake dynamic POST failure'
        return {'status':'WEB_ACTUAL','http_status':200,'url':endpoint,'method':'POST'}

    def queue_click(self, page, selector):
        assert selector and self.current != self.fail_at, 'Fake queue POST failure'
        return {'status':'WEB_ACTUAL','http_status':200,'url':'/ydental/queue/action','method':'POST'}

    def perform(self, name):
        self.current = name
        if name == self.invalid_at:
            self.pages['front' if name in ('reserve','arrive') else
                       'doctor' if name in ('treatment','exam_order','prescription') else
                       'exam' if name == 'examination' else 'manager'].valid = False
        out = super().perform(name)
        if name == self.fail_at:
            raise RuntimeError('Fake missing button or response after branch')
        if name in ('treatment','examination','dispense_four','dispense_two'):
            amount = {'treatment':'600','examination':'80','dispense_four':'40','dispense_two':'20'}[name]
            self.data['fees'].append({'id': 1000 + len(self.data['fees']), 'amount': Decimal(amount)})
        elif name == 'bill':
            self.data['invoices'].append({'id': 2000, 'state':'posted',
                                          'total':Decimal('740'), 'residual':Decimal('740')})
        elif name in ('pay_five_hundred','pay_two_forty'):
            amount = Decimal('500' if name == 'pay_five_hundred' else '240')
            self.data['payments'].append({'id': 3000 + len(self.data['payments']), 'amount':amount})
            self.data['partials'].append({'id': 4000 + len(self.data['partials']), 'amount':amount})
            self.data['invoices'][0]['residual'] -= amount
        if name == self.repeat_at and name == 'treatment':
            self.data['fees'].append({'id': 1999, 'amount':Decimal('600')})
        return out


def test_case(fail_at=None, invalid_at=None, repeat_at=None, missing_role=None):
    with tempfile.TemporaryDirectory(prefix='s10-w1-offline-') as tmp:
        path = Path(tmp) / 'events.jsonl'
        driver = FakeWebDriver(fail_at, invalid_at, repeat_at, missing_role)
        failed = False
        try:
            run(driver, path)
        except (AssertionError, RuntimeError) as exc:
            failed = True
            if not (fail_at or invalid_at or repeat_at or missing_role):
                raise AssertionError(f'Unexpected offline failure: {driver.current}: {exc}') from exc
        expected_failure = bool(fail_at or invalid_at or repeat_at or missing_role)
        assert failed == expected_failure
        complete = path.with_suffix('.complete.json')
        assert complete.exists() is not expected_failure
        events = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        assert all(row['number'] == index and row['request']['method'] == 'POST'
                   for index, row in enumerate(events, 1))
        if not expected_failure:
            assert len(events) == len(STEPS)
            assert events[5]['amount'] == {'decimal':'600'}
            assert events[-1]['time']['datetime'].endswith('+00:00')
            assert json.loads(complete.read_text())['steps'] == len(STEPS)
        else:
            assert len(events) < len(STEPS)


def main():
    test_case()
    for name, _, _ in STEPS:
        test_case(fail_at=name)
    test_case(invalid_at='reserve')
    test_case(invalid_at='treatment')
    test_case(repeat_at='treatment')
    test_case(missing_role='pharmacy')
    print(json.dumps({'status':'SIMULATED_PASS','real_run_steps':len(STEPS),
                      'failure_cases':len(STEPS)+4,'evidence_writer':'ROUND_TRIP_PASS'}))


if __name__ == '__main__': main()
