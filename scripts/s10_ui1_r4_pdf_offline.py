"""SIMULATED fake Playwright exercise of the actual R4 pdf() function."""

import ast
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.local/s00-b-deps/verify-lib'))
sys.path.insert(0, str(ROOT / 'scripts'))
import pymupdf
import s10_ui1_r4_control as control
from s10_ui1_r4_pdf_contract import classify_pdf_response


class FakeResponse:
    def __init__(self, status, content_type, body=b'', pdf_sha=None):
        self.status = status
        self.headers = {'content-type': content_type}
        if pdf_sha:
            self.headers['x-ydental-pdf-sha256'] = pdf_sha
        self._body = body
        self.url = 'http://127.0.0.1:18273/ydental/settlement/pdf/bill/2'
    def body(self): return self._body


class FakeDownload:
    def __init__(self, body): self.body = body
    def save_as(self, path): Path(path).write_bytes(self.body)


class FakeExpectation:
    def __init__(self, response): self.value = response
    def __enter__(self): return self
    def __exit__(self, *_): return None


class FakeLink:
    def __init__(self, page): self.page = page
    def count(self): return 1
    def click(self):
        if self.page.response.status == 200:
            for handler in self.page.listeners:
                handler(FakeDownload(self.page.response.body()))


class FakePage:
    def __init__(self, response):
        self.response = response
        self.listeners = []
    def locator(self, selector):
        assert selector == 'a[href="/ydental/settlement/pdf/bill/2"]'
        return FakeLink(self)
    def on(self, event, handler):
        assert event == 'download'
        self.listeners.append(handler)
    def remove_listener(self, event, handler):
        assert event == 'download'
        self.listeners.remove(handler)
    def expect_response(self, predicate):
        assert predicate(self.response)
        return FakeExpectation(self.response)
    def wait_for_timeout(self, ms):
        raise AssertionError('download listener did not capture the event')


tree = ast.parse((ROOT / 'scripts/s10_ui1_r4_browser.py').read_text())
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'pdf']
assert len(selected) == 1
function = compile(ast.Module(body=selected, type_ignores=[]), 's10_ui1_r4_browser.py', 'exec')


with tempfile.TemporaryDirectory(prefix='ui1-r4-pdf-') as temp:
    run = Path(temp)
    html = ('<html><head><meta charset="utf-8"></head><body>'
            '<p style="font-family:Noto Sans CJK SC">内部结算账单 法人 门店 演示 '
            '原生实收核销 当前应收余额 100 UI1 synthetic response test</p>'
            '</body></html>').encode()
    rendered = subprocess.run(['/usr/local/bin/wkhtmltopdf', '--quiet', '-','-'],
                              input=html, env=control.environment(), capture_output=True, timeout=30)
    assert rendered.returncode == 0 and rendered.stdout.startswith(b'%PDF-')
    pdf_bytes = rendered.stdout
    sha = hashlib.sha256(pdf_bytes).hexdigest()

    def exercise(label, response, *, audit_increment, expected):
        events, ledger = [], []
        states = [
            {'counts': {'ydental_access_audit': 178, 'mail_mail': 0, 'bus_bus': 30}},
            {'counts': {'ydental_access_audit': 178 + audit_increment, 'mail_mail': 0, 'bus_bus': 30}},
        ]
        def state(): return states.pop(0)
        money = {'moves': [(1, 'posted', 100), (2, 'posted', 100)]}
        scope = {'state': state, 'money_snapshot': lambda: money,
                 'event': lambda name, **details: events.append((name, details)),
                 'ledger': lambda name: ledger.append(name),
                 'RUN': run, 'hashlib': hashlib, 'os': os, 'urlsplit': urlsplit,
                 'pymupdf': pymupdf, 'classify_pdf_response': classify_pdf_response,
                 'unicodedata': unicodedata,
                 'finance': lambda value: 0}
        exec(function, scope)
        page = FakePage(response)
        try:
            result = scope['pdf'](page, 'bill', 2)
        except RuntimeError as error:
            assert expected == 'STOP' and str(error).endswith('STOP')
            result = None
        else:
            assert result['status'] == expected
        assert not page.listeners
        assert any(event[0] == 'pdf_http_response' for event in events)
        assert (ledger == ['pdf_bill']) is (expected == 200)
        if expected == 200:
            assert (run / 'ui1-bill.pdf').read_bytes() == pdf_bytes
        else:
            assert (run / 'ui1-bill-rejection.body').read_bytes() == response.body()
        for path in run.iterdir():
            path.unlink()
        return result

    exercise('200', FakeResponse(200, 'application/pdf', pdf_bytes, sha),
             audit_increment=1, expected=200)
    exercise('409-renderer', FakeResponse(409, 'application/json',
             b'{"error":"Unable to find the pdf engine on this system. The PDF can not be created."}'),
             audit_increment=1, expected='RENDERER_ONLY_BLOCKED')
    exercise('403', FakeResponse(403, 'application/json', b'{"error":"access_denied: no export"}'),
             audit_increment=1, expected='STOP')
    exercise('409-unknown', FakeResponse(409, 'application/json',
             b'{"error":"render_failed: Settlement PDF could not be generated."}'),
             audit_increment=1, expected='STOP')

print('SIMULATED_PASS actual R4 pdf(): 200+download, 409 renderer, 403, 409 unattributed; full rejection saved, no false PDF success')
