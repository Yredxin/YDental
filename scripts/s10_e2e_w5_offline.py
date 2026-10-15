"""Exercise W5's real stage order, validators and payment flow without writes."""

from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import tempfile

from s10_e2e_w5_browser import payment_flow, persist_intent, persist_observed, validate_audit_progress, validate_money
from s10_e2e_w5_control import execute_pipeline, validate_clone, write_once
from s10_e2e_w5_snapshot import NAME, SOURCE, state


def form(amount):
    return {'operation': 'pay', 'invoice_ids': ['1'], 'output': 'html',
        'channel': 'cash', 'amount': str(amount), 'csrf_present': True,
        'key_present': True, 'revision_match': True, 'actual_utc_present': True,
        'proof_present': True, 'form_valid': True, 'form_visible': True,
        'action': '/ydental/settlement/action', 'method': 'post', 'button_enabled': True}


def response(amount):
    return {'http_status': 303, 'method': 'POST', 'path': '/ydental/settlement/action',
        'request_content_type': 'application/x-www-form-urlencoded',
        'response_content_type': 'text/html; charset=utf-8',
        'location_path': '/ydental/settlement', 'notice_present': True,
        'accepted_feedback': True,
        'form_fields': {'operation':'pay','output':'html','invoice_ids':['1'],
            'amount':str(amount),'channel':'cash','csrf_present':True,
            'revision_present':True,'key_present':True,'actual_utc_present':True,
            'proof_present':True}}


class FakeWeb:
    def __init__(self, source, folder, fault=None):
        self.before = deepcopy(source)
        self.current = deepcopy(source)
        self.fault = fault
        self.folder = folder
        self.posts = []
        self.records = []
        self.confirmed = []
        self.intents = []
        self.current['money']['audits'].append({'id':990,'event':'login.scope',
            'result':'accepted','user':5,'store':None})

    def snapshot(self):
        return deepcopy(self.current)

    def load_form(self, amount, current):
        fields = form(amount)
        if self.fault == 'old_installed_view':
            raise AssertionError('installed output=html absent')
        if self.fault == 'missing_output' and amount == 500:
            fields['output'] = None
        if self.fault == 'wrong_invoice' and amount == 500:
            fields['invoice_ids'] = ['2']
        if self.fault == 'invalid_html' and amount == 500:
            fields['form_valid'] = False
        if self.fault == 'missing_csrf' and amount == 500:
            fields['csrf_present'] = False
        if self.fault == 'missing_key' and amount == 500:
            fields['key_present'] = False
        if self.fault == 'invalid_amount' and amount == 500:
            fields['amount'] = '501'
        if self.fault == 'missing_proof' and amount == 500:
            fields['proof_present'] = False
        if self.fault == 'bad_action' and amount == 500:
            fields['action'] = '/wrong/action'
        if self.fault == 'stale_revision' and amount == 500:
            fields['revision_match'] = False
        if self.fault == 'no_role' and amount == 500:
            fields['form_visible'] = False
        self.current['money']['audits'].append({'id':991 if amount == 500 else 992,
            'event':'settlement.invoice_view','result':'accepted','user':5,'store':1})
        return fields

    def intent(self, index, amount):
        assert index == len(self.intents) + 1
        persist_intent(self.folder, index, amount)
        self.intents.append(amount)

    def _commit(self, index, amount):
        m = self.current['money']
        assert amount == (500, 240)[index-1] and len(m['payments']) == index-1
        cash = m['cash_configs'][0]['journal']
        move = index+1
        m['native_moves'].append({'id':move,'type':'entry','state':'posted',
            'total':Decimal(0),'company':1,'journal':cash})
        m['payments'].append({'id':index,'state':'in_process','payment_type':'inbound',
            'partner_type':'customer','amount':Decimal(amount),'company':1,
            'journal':cash,'move':move,'move_state':'posted'})
        m['settlement_payments'].append({'id':index,'payment':index,'amount':Decimal(amount),
            'channel':'cash','store':1,'patient':1})
        m['payment_invoices'].append({'settlement_payment':index,'invoice':1})
        m['partials'].append({'id':index,'amount':Decimal(amount),'debit':5,
                              'credit':5+index*2,'company':1})
        m['payment_lines'].extend([
            {'id':4+index*2,'move':move,'account':20,'debit':Decimal(amount),
             'credit':Decimal(0),'balance':Decimal(amount)},
            {'id':5+index*2,'move':move,'account':5,'debit':Decimal(0),
             'credit':Decimal(amount),'balance':Decimal(-amount)}])
        m['receipts'].append({'id':index+1,'operation':'pay','result':{'amount':amount}})
        m['audits'].append({'id':1000+index,'event':'settlement.pay','result':'accepted',
                            'user':5,'store':1})
        residual = Decimal(740-sum((500,240)[:index]))
        m['invoices'][0]['residual'] = residual
        m['invoices'][0]['payment_state'] = 'paid' if index == 2 else 'partial'
        m['invoice_lines'][4]['residual'] = residual
        if self.fault == 'wrong_partial' and index == 1:
            m['partials'][0]['amount'] = Decimal(499)
        if self.fault == 'duplicate_payment' and index == 2:
            m['payments'].append(deepcopy(m['payments'][-1]))
        if self.fault == 'cross_invoice' and index == 2:
            m['payment_invoices'][-1]['invoice'] = 2
        if self.fault == 'stock_drift' and index == 1:
            self.current['stable']['stock_move']['sha256'] = 'f'*64

    def submit(self, index, amount):
        assert len(self.posts) == index-1
        self.posts.append(amount)
        if self.fault == 'forbidden_403' and index == 1:
            outcome = response(amount); outcome['http_status'] = 403
            return outcome
        self._commit(index, amount)
        if self.fault == 'lost_response_500' and index == 1:
            raise TimeoutError('response lost after committed first payment')
        if self.fault == 'lost_response_240' and index == 2:
            raise TimeoutError('response lost after committed second payment')
        outcome = response(amount)
        if self.fault == 'http_200_500' and index == 1:
            outcome['http_status'] = 200
        if self.fault == 'denied_feedback_500' and index == 1:
            outcome['accepted_feedback'] = False
        if self.fault == 'http_409_240' and index == 2:
            outcome['http_status'] = 409
        if self.fault == 'wrong_payload_500' and index == 1:
            outcome['form_fields']['output'] = None
        return outcome

    def record(self, index, amount, outcome, after):
        persist_observed(self.folder, index, amount, outcome, after)
        self.records.append({'index':index,'amount':amount,'response':outcome,
                             'native_payment_count':len(after['money']['payments'])})

    def observed_response(self, index):
        return {'request_sent':index <= len(self.posts)}

    def confirm(self, index, amount, after):
        self.confirmed.append(amount)


class FakeOps:
    def __init__(self, source, folder, fault=None, browser_fault=None):
        self.base = deepcopy(source)
        self.target = None
        self.fault = fault
        self.folder = folder
        self.browser_fault = browser_fault
        self.events = []
        self.started = False
        self.stopped = False
        self.browser_adapter = None
        self.create_count = self.http_count = self.browser_count = 0

    def source(self):
        self.events.append('source')
        return deepcopy(self.base)

    def create(self, source):
        self.events.append('create')
        self.create_count += 1
        assert self.create_count == 1 and source == self.base
        if self.fault == 'clone_failed':
            raise RuntimeError('simulated CREATE failure')
        self.target = deepcopy(source)
        self.target['database'] = NAME
        if self.fault == 'clone_economic_drift':
            self.target['exact']['ydental_treatment_fee']['sha256'] = '0'*64
        if self.fault == 'clone_filestore_drift':
            self.target['filestore']['manifest_sha256'] = '0'*64
        if self.fault == 'clone_view_drift':
            self.target['views']['ydental_settlement.ydental_settlement_tokens']['en_US']['sha256'] = '0'*64
        if self.fault == 'clone_module_drift':
            self.target['module_meta']['ydental_settlement']['write_date'] = 'SIMULATED_BAD'

    def before(self, source):
        self.events.append('before')
        validate_clone(source, self.base, self.target)
        return deepcopy(self.target)

    def start(self):
        self.events.append('start')
        self.http_count += 1
        self.started = True
        if self.fault == 'http_start_failure':
            raise RuntimeError('simulated HTTP startup failure')

    def http_started(self):
        return self.started

    def browser(self):
        self.events.append('browser')
        self.browser_count += 1
        self.browser_adapter = FakeWeb({'money':deepcopy(self.target['money']),
            'stable':{table:self.target['exact'][table] for table in
                __import__('s10_e2e_w5_snapshot').STABLE_AFTER_PAYMENT}}, self.folder, self.browser_fault)
        payment_flow(self.browser_adapter)
        self.target['money'] = deepcopy(self.browser_adapter.current['money'])

    def final(self, before, source):
        self.events.append('final')
        validate_money(self.target['money'], (500,240), (240,0), before['money'])
        validate_audit_progress(before['money'], self.target['money'])
        assert self.base == source

    def stop(self):
        self.events.append('stop')
        self.stopped = True


def main():
    source = state(SOURCE)  # Only a real read-only SQL source snapshot.
    cases = []
    with tempfile.TemporaryDirectory(prefix='s10-w5-full-') as folder:
        good = FakeOps(source, Path(folder))
        execute_pipeline(good)
        assert good.events == ['source','create','before','start','browser','final','stop']
        assert (good.create_count,good.http_count,good.browser_count) == (1,1,1)
        assert good.browser_adapter.posts == [500,240]
        assert good.browser_adapter.confirmed == [500,240]
        assert [int((Path(folder)/f'pay-{i}-observed.json').exists()) for i in (1,2)] == [1,1]
    cases.append('full_same_stage_order')
    for fault, expected_posts in (
        ('clone_failed',0),('clone_economic_drift',0),('clone_filestore_drift',0),
        ('clone_view_drift',0),('clone_module_drift',0),
        ('http_start_failure',0)):
        with tempfile.TemporaryDirectory(prefix='s10-w5-fault-') as folder:
            ops = FakeOps(source, Path(folder), fault=fault)
            try:
                execute_pipeline(ops)
            except (AssertionError,RuntimeError):
                pass
            else:
                raise AssertionError('Expected STOP for '+fault)
            assert ops.browser_count == 0
            assert ops.stopped is (fault == 'http_start_failure')
        cases.append(fault)
    for fault, posts, records, confirmed in (
        ('old_installed_view',0,0,0),('missing_output',0,0,0),
        ('wrong_invoice',0,0,0),('invalid_html',0,0,0),
        ('missing_csrf',0,0,0),('missing_key',0,0,0),('invalid_amount',0,0,0),
        ('missing_proof',0,0,0),('bad_action',0,0,0),
        ('stale_revision',0,0,0),('no_role',0,0,0),
        ('forbidden_403',1,1,0),('lost_response_500',1,1,0),
        ('http_200_500',1,1,0),('denied_feedback_500',1,1,0),
        ('wrong_payload_500',1,1,0),('wrong_partial',1,1,0),('stock_drift',1,1,0),
        ('http_409_240',2,2,1),('lost_response_240',2,2,1),
        ('duplicate_payment',2,2,1),('cross_invoice',2,2,1)):
        with tempfile.TemporaryDirectory(prefix='s10-w5-fault-') as folder:
            ops = FakeOps(source, Path(folder), browser_fault=fault)
            try:
                execute_pipeline(ops)
            except (AssertionError,RuntimeError):
                pass
            else:
                raise AssertionError('Expected STOP for '+fault)
            adapter = ops.browser_adapter
            assert adapter is not None and len(adapter.posts) == posts
            assert len(adapter.records) == records and len(adapter.confirmed) == confirmed
            assert ops.stopped and ops.browser_count == 1 and ops.create_count == ops.http_count == 1
            assert sorted(p.name for p in Path(folder).glob('*intent.json')) == [f'pay-{i}-intent.json' for i in range(1,posts+1)]
            assert sorted(p.name for p in Path(folder).glob('*observed.json')) == [f'pay-{i}-observed.json' for i in range(1,records+1)]
        cases.append(fault)
    print(json.dumps({'status':'OFFLINE_PASS','cases':cases,'case_count':len(cases),
        'positive_payments':[500,240], 'source_readonly':True}))


if __name__ == '__main__':
    main()
