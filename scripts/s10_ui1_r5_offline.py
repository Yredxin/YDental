"""SIMULATED full R5 CREATE/CLI and PDF response contract checks."""

from contextlib import redirect_stdout
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import s10_ui1_r5_control as control
from s10_ui1_r4_pdf_contract import classify_pdf_response
from s10_ui1_r2_evidence import read_complete, write_once

checks = []


class FakeSocket:
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def bind(self, address): assert address == ('127.0.0.1', control.PORT)


class FakeCursor:
    def __init__(self, state): self.state = state
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def execute(self, query):
        assert 'CREATE DATABASE' in str(query)
        self.state['create_calls'] += 1
        if self.state['fail_create']:
            raise RuntimeError('SIMULATED CREATE failure')
        self.state['created'] = True


class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.autocommit = False
        self.info = type('Info', (), {'transaction_status':
            control.psycopg2.extensions.TRANSACTION_STATUS_IDLE})()
    def cursor(self): return FakeCursor(self.state)
    def close(self): pass


def sandbox(root, *, fail_copy=False, fail_create=False, bad_oid=False):
    root.mkdir()
    local = root / '.local'; local.mkdir()
    source_run = local / control.SOURCE
    source_fs = source_run / 'data/filestore' / control.SOURCE
    source_fs.mkdir(parents=True)
    data = {'alpha': b'nonempty R3 source', 'folder/beta': b'second nonempty file'}
    expected = {}
    for rel, raw in data.items():
        path = source_fs / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected[rel] = {'sha256': hashlib.sha256(raw).hexdigest()}
    (source_run / 'fixture.json').write_text(json.dumps({'db': control.SOURCE,
        'oid': 2100265, 'fees': [1, 2], 'actors': {'frontdesk': 6}}))
    if fail_copy:
        (source_fs / 'alpha').write_bytes(b'changed after manifest')
    run = local / control.NAME
    state = {'created': False, 'create_calls': 0, 'postcalls': 0,
             'fail_create': fail_create}

    def identity(expect_target=False):
        if expect_target:
            assert state['created']
            state['postcalls'] += 1
            oid = 314159 if bad_oid and state['postcalls'] > 1 else 271828
        else:
            assert not state['created']
            oid = None
        return {'password': 'SIMULATED_ONLY'}, expected, oid

    return source_run, run, state, data, identity


def run_case(root, **flags):
    source_run, run, state, files, identity = sandbox(root, **flags)
    with patch.multiple(control, ROOT=root, SOURCE_RUN=source_run, RUN=run, identity=identity), \
         patch.object(control.socket, 'socket', return_value=FakeSocket()), \
         patch.object(control.psycopg2, 'connect', side_effect=lambda **kw: FakeConnection(state)):
        if flags:
            try:
                with redirect_stdout(io.StringIO()): control.dispatch('create')
            except (AssertionError, RuntimeError, ValueError):
                pass
            else:
                raise AssertionError('Expected CREATE failure did not occur')
            assert not (run / 'create-complete.json').exists()
            expected_calls = 0 if flags.get('fail_copy') else 1
            assert state['create_calls'] == expected_calls
            checks.append('actual_create_' + next(iter(flags)) + '_fails_closed')
            return
        with redirect_stdout(io.StringIO()): control.dispatch('create')
        assert state['create_calls'] == 1 and state['postcalls'] == 2
        assert all((run / 'data/filestore' / control.NAME / rel).read_bytes() == raw
                   for rel, raw in files.items())
        assert read_complete(run / 'create-complete.json')['phase'] == 'VERIFIED'
        fixture = read_complete(run / 'fixture.json')
        assert fixture['db'] == control.NAME and fixture['oid'] == 271828
        assert fixture['inherited_from']['oid'] == 2100265
        with patch.object(control, 'assert_source_baseline', return_value={'finance': True}), \
             patch.object(control, 'finance_snapshot', return_value={'finance': True}), \
             patch.object(control, 'qweb_loaded', return_value=True):
            with redirect_stdout(io.StringIO()): control.dispatch('verify-target')
        checks.append('actual_create_copy_fake_sql_marker_adapter_tail_and_cli_dispatch')
        try: control.dispatch('create')
        except (AssertionError, FileExistsError): pass
        else: raise AssertionError('repeat CREATE was allowed')
        assert state['create_calls'] == 1
        checks.append('one_time_create_repeat_rejected')
        with patch.object(control, 'inherited_baseline', side_effect=RuntimeError('bad inherited finance')):
            try: control.dispatch('serve')
            except RuntimeError: pass
            else: raise AssertionError('HTTP admitted after bad finance')
        assert not (run / 'http-r5.attempt.json').exists()
        checks.append('finance_failure_blocks_http')
        with patch.object(control, 'inherited_baseline', return_value={'finance': True}), \
             patch.object(control, 'qweb_loaded', return_value=False):
            try: control.dispatch('serve')
            except AssertionError: pass
            else: raise AssertionError('HTTP admitted before candidate QWeb')
        assert not (run / 'http-r5.attempt.json').exists()
        checks.append('qweb_failure_blocks_http')
        try: control.dispatch('unknown')
        except ValueError: pass
        else: raise AssertionError('unknown CLI admitted')
        checks.append('unknown_cli_rejected')


with tempfile.TemporaryDirectory(prefix='ui1-r5-flow-') as temp:
    root = Path(temp)
    run_case(root / 'success')
    run_case(root / 'copy', fail_copy=True)
    run_case(root / 'sql', fail_create=True)
    run_case(root / 'oid', bad_oid=True)
    typed = {'date': date(2026, 10, 15), 'at': datetime(2026, 10, 15, tzinfo=timezone.utc),
             'nested': {'amount': Decimal('60.00'), 'part': Decimal('0.0001')}}
    path = root / 'typed.json'
    write_once(path, typed)
    assert read_complete(path) == typed
    try: write_once(path, {'false_success': True})
    except FileExistsError: pass
    else: raise AssertionError('Evidence overwrite allowed')
    checks.append('typed_date_datetime_decimal_exact_roundtrip_and_no_overwrite')

# The actual browser request function runs against a Fake Playwright page. No
# fake bypasses own_credentials(), post(), or their terminal checks.
from s10_ui1_r5_web import own_credentials, post
import ast

class FakeInput:
    def __init__(self, value): self.value = value
    def input_value(self): return self.value

class FakeForm:
    def __init__(self, page): self.page = page
    def count(self): return 1 if self.page.has_access_form else 0
    def locator(self, name):
        return FakeInput(self.page.token if 'csrf_token' in name else self.page.revision)

class FakePage:
    def __init__(self, role, *, form=True, token='own-token', revision='4'):
        self.role = role; self.has_access_form = form
        self.token = token; self.revision = revision; self.sent = []
        self.status = 403
    def goto(self, url, **kwargs):
        assert url.endswith('/ydental/access')
        return type('Response', (), {'status':200})()
    def locator(self, query):
        assert 'operation' in query and 'switch' in query
        return FakeForm(self)
    def evaluate(self, script, fields):
        assert "fetch('/ydental/settlement/action'" in script
        self.sent.append(fields.copy())
        if self.status in (200,403,409):
            return {'sent':True,'status':self.status,'content_type':'application/json',
                    'body_class':'json','data':{'error':'access_denied: test'}}
        return {'sent':True,'status':self.status,'content_type':'text/html',
                'body_class':'html','data':None}

reader = FakePage('reader')
own = own_credentials(reader, 'http://127.0.0.1:18274')
response = post(reader, own, 'bill', {'key':'synthetic-denied'})
assert response['status'] == 403 and len(reader.sent) == 1
assert reader.sent[0]['csrf_token'] == 'own-token' and reader.sent[0]['revision'] == '4'
checks.append('actual_reader_own_access_credentials_sends_unauthorized_post')
other = FakePage('other')
try: post(other, own, 'bill', {'key':'cross-role'})
except RuntimeError: pass
else: raise AssertionError('cross-role credentials accepted')
assert other.sent == []
for kwargs in ({'form':False}, {'token':''}, {'revision':''}):
    bad = FakePage('reader', **kwargs)
    try: own_credentials(bad, 'http://127.0.0.1:18274')
    except RuntimeError: pass
    else: raise AssertionError('missing own credentials accepted')
checks.append('missing_and_cross_role_credentials_fail_closed')
reader.status = 400
response = post(reader, own, 'bill', {'key':'bad-csrf'}, token_override='invalid')
assert response['status'] == 400 and reader.sent[-1]['csrf_token'] == 'invalid'
checks.append('actual_invalid_csrf_request_is_sent')
for status in (200,303,403,409):
    reader.status = status
    assert post(reader, own, 'unknown', {'key':'response-class'})['status'] == status
reader.status = 201
try: post(reader, own, 'unknown', {'key':'unexpected-success'})
except RuntimeError: pass
else: raise AssertionError('unknown success accepted')
checks.append('actual_post_200_303_400_403_409_and_unexpected_2xx_stop')

# Extract the *actual* invariant function to exercise its before/after branch
# without importing the runtime browser module, whose marker is intentionally
# absent before CREATE.
source = (ROOT / 'scripts/s10_ui1_r5_browser.py').read_text()
node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'invariant')
namespace = {}
exec(compile(ast.Module(body=[node],type_ignores=[]),'s10_ui1_r5_browser.py','exec'),namespace)
observed = {'money':0,'audit':0,'events':[]}
def money(): return {'receipt_rows':observed['money']}
def audit(): return {'mail':0,'exports':0,'recent':[]}
def event(label, **kwargs): observed['events'].append((label,kwargs))
namespace.update(finance=money,audit=audit,event=event)
assert namespace['invariant']('denial', lambda:{'status':403,'content_type':'application/json',
    'data':{'error':'access_denied'},'body_class':'json'},403,error_contains='access_denied')[0]['status']==403
observed['money']=0
try: namespace['invariant']('unexpected_success', lambda:{'status':200,'content_type':'application/json',
    'data':{},'body_class':'json'},403)
except RuntimeError: pass
else: raise AssertionError('unexpected business success accepted')
def mutate():
    observed['money']=1
    return {'status':403,'content_type':'application/json','data':{'error':'access_denied'},'body_class':'json'}
try: namespace['invariant']('mutated_finance',mutate,403)
except RuntimeError: pass
else: raise AssertionError('funding side effect accepted')
checks.append('actual_invariant_denial_success_and_finance_side_effect_paths')

print(json.dumps({'status': 'SIMULATED_PASS', 'checks': checks,
                  'actual_create_dispatch_web_and_invariant_called': True,
                  'new_databases_created': 0, 'odoo_processes': 0,
                  'firefox_processes': 0}, indent=2))
