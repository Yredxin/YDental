"""One native Firefox login and doc1 acquire/confirm/automatic release, once.

All actions originate in the existing native page. Route gates only validate,
record and continue those requests; no response fabrication or product JS patch.
"""
import asyncio
from datetime import datetime, timezone
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
os.environ['DEBUG'] = 'pw:browser'
from playwright.async_api import async_playwright

import s10_p0_11_control as c
from s10_p0_11_eligibility import credentials, source_rows, digest

BASE = 'http://127.0.0.1:' + str(c.PORT)
CLINICAL = '/ydental/clinical?document_id=1'
LOGIN = '/web/login?redirect=' + CLINICAL.replace('?', '%3F').replace('=', '%3D')
LOGIN_FIELDS = {'csrf_token', 'login', 'password', 'type', 'webauthn_response', 'redirect'}
ACTION_FIELDS = {'operation', 'payload', 'revision', 'connection', 'csrf_token'}


def validate_action(data, context, old):
    assert set(data) == ACTION_FIELDS and all(len(v) == 1 for v in data.values())
    operation = data['operation'][0]
    assert operation in ('acquire', 'confirm', 'release')
    assert data['revision'] == ['1']
    connection = data['connection'][0]
    assert re.fullmatch('[A-Za-z0-9]{32,128}', connection)
    assert c.sha(connection.encode()) == context['connection_sha256']
    assert c.sha(data['csrf_token'][0].encode()) == context['csrf_sha256']
    payload = json.loads(data['payload'][0])
    expected = {'document_id'} | ({'editor_token'} if operation != 'acquire' else set())
    if operation == 'confirm':
        expected |= {'expected_version', 'content', 'key'}
    assert set(payload) == expected and payload['document_id'] == 1
    if operation != 'acquire':
        assert c.sha(payload['editor_token'].encode()) == context['editor_sha256']
    if operation == 'confirm':
        assert payload['expected_version'] == 2 and payload['content'] == old['ydental_content']
        assert isinstance(payload['key'], str) and 16 <= len(payload['key']) <= 128
        assert payload['key'] not in context['old_keys']
    return operation, payload


async def main():
    c.checkpoint()
    assert not (c.PRIVATE / 'firefox-launch-intent.json').exists()
    old_tables = source_rows()
    old_doc = old_tables['ydental_clinical_document'][0]
    login, password = credentials(old_tables)
    assets = {r['url'] for r in old_tables['ir_attachment'] if (r.get('url') or '').startswith('/web/assets/')}
    static = {'/ydental_clinical/static/src/document/document.js', '/ydental_clinical/static/src/document/document.css'}
    counts = {'FIREFOX_LAUNCH': 0, 'NATIVE_LOGIN_POST': 0, 'STORE_SWITCH_POST': 0,
              'CLINICAL_GET': 0, 'ACQUIRE': 0, 'CONFIRM': 0, 'RELEASE': 0, 'HEARTBEAT': 0,
              'OTHER_POST': 0, 'PDF': 0}
    requests, responses, page_errors = [], [], []
    context = {'old_keys': [r['ydental_request_key'] for r in old_tables['ydental_clinical_version']]}
    accepted = {op: asyncio.Event() for op in ('acquire', 'confirm', 'release')}
    fatal = asyncio.Event()
    failure = []
    browser = None
    page = None

    def fail(code, detail=None):
        if not fatal.is_set():
            failure.append({'code': code, 'detail_sha256': c.sha(str(detail).encode()) if detail else None})
            fatal.set()

    async def guarded(awaitable):
        operation = asyncio.ensure_future(awaitable)
        error = asyncio.create_task(fatal.wait())
        done, pending = await asyncio.wait((operation, error), return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        if fatal.is_set():
            raise AssertionError(failure[0]['code'])
        return await operation

    def record_dom(name, data):
        c.save(c.OUT / ('dom-' + name + '.json'), data)

    async def screenshot(name):
        await page.screenshot(path=str(c.PRIVATE / (name + '.png')), full_page=True)

    async def route_handler(route):
        request = route.request
        url = urlsplit(request.url)
        try:
            assert not fatal.is_set(), 'PRIOR_FAILURE_STOP'
            assert url.scheme == 'http' and url.netloc == f'127.0.0.1:{c.PORT}' and not url.fragment, 'ORIGIN'
            headers = await request.all_headers()
            payload_text = request.post_data or ''
            data = parse_qs(payload_text, keep_blank_values=True)
            q = parse_qs(url.query, keep_blank_values=True)
            if request.method == 'GET':
                if url.path == '/web/login':
                    assert q == {'redirect': [CLINICAL]} and counts['NATIVE_LOGIN_POST'] == 0
                elif url.path == '/ydental/clinical':
                    assert q == {'document_id': ['1']} and counts['NATIVE_LOGIN_POST'] == 1 and counts['CLINICAL_GET'] < 2
                    if counts['CLINICAL_GET'] == 1:
                        await accepted['release'].wait()
                        c.capture_gate('released', context)
                        await screenshot('released-before-final-get')
                    counts['CLINICAL_GET'] += 1
                elif url.path == '/website/translations':
                    assert q == {'hash': [''], 'lang': ['zh_CN']}
                else:
                    assert url.path in assets | static and not q, 'GET_NOT_ALLOWLISTED'
                requests.append({'method': 'GET', 'path': url.path, 'query_keys': sorted(q)})
            else:
                assert request.method == 'POST' and not q
                assert headers.get('origin') == BASE and urlsplit(headers.get('referer', '')).netloc == url.netloc
                assert headers.get('content-type', '').split(';')[0] == 'application/x-www-form-urlencoded'
                assert 'session_id=' in headers.get('cookie', '')
                if url.path == '/web/login':
                    assert counts['NATIVE_LOGIN_POST'] == 0 and set(data) == LOGIN_FIELDS
                    assert all(len(v) == 1 for v in data.values())
                    assert data['login'] == [login] and data['password'] == [password]
                    assert data['type'] == ['password'] and data['webauthn_response'] == [''] and data['redirect'] == [CLINICAL]
                    assert data['csrf_token'][0] and c.sha(data['csrf_token'][0].encode()) == context['login_csrf_sha256']
                    c.gate(c.snapshot(c.NAME), 'startup', {})
                    counts['NATIVE_LOGIN_POST'] += 1
                    op = 'native-login'
                else:
                    assert url.path == '/ydental/clinical/action', 'OTHER_POST_FORBIDDEN'
                    op, payload = validate_action(data, context, old_doc)
                    if op == 'acquire':
                        assert counts['ACQUIRE'] == counts['CONFIRM'] == counts['RELEASE'] == 0
                        c.capture_gate('login-view', context)
                    elif op == 'confirm':
                        assert counts['ACQUIRE'] == 1 and counts['CONFIRM'] == counts['RELEASE'] == 0
                        await accepted['acquire'].wait()
                        context['confirm_key'] = payload['key']
                        c.capture_gate('acquired', context)
                        await screenshot('acquired-before-confirm')
                    else:
                        assert counts['ACQUIRE'] == counts['CONFIRM'] == 1 and counts['RELEASE'] == 0
                        await accepted['confirm'].wait()
                        c.capture_gate('confirmed', context)
                        await screenshot('confirmed-before-release')
                    counts[op.upper()] += 1
                c.save(c.PRIVATE / ('intent-' + op + '.json'), {'method': 'POST', 'path': url.path,
                    'actor': 7, 'data': data, 'headers': headers, 'utc': datetime.now(timezone.utc).isoformat(), 'one_shot': True})
                requests.append({'method': 'POST', 'path': url.path, 'operation': op, 'actor': 7,
                    'payload_sha256': c.sha(payload_text.encode()), 'origin_ok': True, 'csrf_bound': True, 'cookie_present': True,
                    'scope_revision': 1 if op != 'native-login' else None})
            await route.continue_()
        except Exception as error:
            fail('REQUEST_GATE_STOP', error)
            c.save(c.PRIVATE / ('request-gate-failure-' + str(len(requests)) + '.json'), {
                'error': str(error), 'path': url.path, 'method': request.method})
            await route.abort()

    async def response_handler(response):
        request = response.request
        path = urlsplit(response.url).path
        try:
            data = parse_qs(request.post_data or '', keep_blank_values=True)
            info = {'method': request.method, 'path': path, 'status': response.status,
                    'content_type': response.headers.get('content-type', '')}
            responses.append(info)
            assert response.status < 400, 'HTTP_ERROR_STOP'
            if request.method == 'POST':
                op = 'native-login' if path == '/web/login' else data['operation'][0]
                body = None if response.status == 303 else await response.body()
                c.save(c.PRIVATE / ('response-' + op + '.json'), {'status': response.status,
                    'headers': await response.all_headers(), 'body': body.decode('utf-8') if body is not None else None,
                    'redirect_body_unavailable_via_browser_api': body is None, 'url': response.url})
                info['operation'] = op
                info['body_sha256'] = c.sha(body) if body is not None else None
                if op == 'native-login':
                    assert response.status == 303 and response.headers.get('location') == CLINICAL, 'LOGIN_REDIRECT'
                else:
                    assert response.status == 200 and info['content_type'].startswith('application/json')
                    result = json.loads(body)
                    assert result['result'] == 'accepted' and result['document_id'] == 1
                    if op == 'acquire':
                        assert result['version'] == 2 and result['state'] == 'pending' and result['responsible_id'] == 7
                        assert result['content'] == old_doc['ydental_content'] and result['editor_token']
                        context['editor_sha256'] = c.sha(result['editor_token'].encode())
                    elif op == 'confirm':
                        assert result['version'] == result['saved_version'] == 3 and result['state'] == 'confirmed'
                        assert result['content'] == old_doc['ydental_content'] and not result.get('duplicate')
                    elif op == 'release':
                        assert set(result) == {'document_id', 'result'}
                    accepted[op].set()
            elif path == '/ydental/clinical':
                body = await response.body()
                c.save(c.PRIVATE / ('clinical-get-' + str(counts['CLINICAL_GET']) + '.html.json'),
                       {'status': response.status, 'body': body.decode('utf-8')})
        except Exception as error:
            fail('RESPONSE_GATE_STOP', error)

    try:
        async with async_playwright() as pw:
            c.save(c.PRIVATE / 'firefox-launch-intent.json', {'attempt': 1, 'browser': 'Firefox', 'context': 1, 'actor': 7})
            browser = await pw.firefox.launch(headless=True, env=os.environ.copy())
            counts['FIREFOX_LAUNCH'] = 1
            browser_context = await browser.new_context(locale='zh-CN', timezone_id='UTC', viewport={'width': 1440, 'height': 1100}, service_workers='block')
            page = await browser_context.new_page()
            page.set_default_timeout(20000)
            page.on('pageerror', lambda e: (page_errors.append(str(e)), fail('FIREFOX_PAGE_ERROR', e)))
            page.on('crash', lambda: fail('FIREFOX_PAGE_CRASH'))
            page.on('response', response_handler)
            await browser_context.route('**/*', route_handler)
            await guarded(page.goto(BASE + LOGIN, wait_until='domcontentloaded'))
            form = page.locator('form.oe_login_form')
            assert await form.count() == 1
            structure = await form.evaluate("f=>({action:f.getAttribute('action'),method:f.method,enctype:f.enctype,names:Array.from(f.elements).filter(e=>e.name).map(e=>e.name)})")
            assert structure['action'] == '/web/login' and structure['method'] == 'post'
            assert set(structure['names']) == LOGIN_FIELDS and len(structure['names']) == len(LOGIN_FIELDS)
            context['login_csrf_sha256'] = c.sha((await form.locator('[name=csrf_token]').input_value()).encode())
            await form.locator('[name=login]').fill(login)
            await form.locator('[name=password]').fill(password)
            await guarded(form.locator('button[type=submit]').click())
            await guarded(page.locator('.o_ydental_clinical').wait_for(state='visible'))
            dom = await page.locator('.o_ydental_clinical').evaluate("r=>({document:r.dataset.document,revision:r.dataset.revision,version:r.dataset.version,state:r.dataset.state,execution:r.dataset.execution,heartbeat:r.dataset.heartbeat,canHandover:r.dataset.canHandover,content:Object.fromEntries(Array.from(r.querySelectorAll('textarea[name]')).map(f=>[f.name,f.value]).concat([['teeth',Array.from(r.querySelectorAll('#tooth-summary [data-row]')).map(li=>({tooth:Number(li.dataset.row),state:li.dataset.state,surfaces:li.dataset.surfaces.split(',').filter(Boolean)}))]])),csrf:r.querySelector('[name=csrf_token]').value,connection:sessionStorage.getItem('ydental_queue_connection'),holder:sessionStorage.getItem('ydental_queue_holder')})")
            assert (dom['document'], dom['revision'], dom['version'], dom['state'], dom['execution'], dom['heartbeat'], dom['canHandover']) == ('1', '1', '2', 'pending', '0', '2', 'no')
            assert dom['content'] == old_doc['ydental_content'] and dom['holder'] is None
            assert dom['connection'] and re.fullmatch('[A-Za-z0-9]{32,128}', dom['connection'])
            context['connection_sha256'] = c.sha(dom['connection'].encode())
            context['csrf_sha256'] = c.sha(dom['csrf'].encode())
            record_dom('before', {k: v for k, v in dom.items() if k not in ('csrf', 'content', 'connection', 'holder')} | {'content_sha256': digest(dom['content']), 'same_original_content': True})
            await screenshot('before-acquire')
            await guarded(page.locator('#open-document').click())
            await guarded(page.locator('#confirm-document').wait_for(state='visible'))
            await guarded(page.wait_for_function("!document.querySelector('#confirm-document').disabled"))
            # No text input/change events: native confirm submits the server's original content.
            await guarded(page.locator('#confirm-document').click())
            await guarded(page.wait_for_function("document.querySelector('.o_ydental_clinical')?.dataset.state==='confirmed' && document.querySelector('.o_ydental_clinical')?.dataset.version==='3'"))
            assert accepted['acquire'].is_set() and accepted['confirm'].is_set() and accepted['release'].is_set()
            final = await page.locator('.o_ydental_clinical').evaluate("r=>({document:r.dataset.document,revision:r.dataset.revision,version:r.dataset.version,state:r.dataset.state,serverVersion:r.querySelector('#server-version').textContent,versionRows:r.querySelectorAll('#version-history>li').length,editorStored:sessionStorage.getItem('ydental_clinical_editor_1')!==null,releaseDisabled:r.querySelector('#release-document').disabled})")
            assert final['document'] == '1' and final['version'] == final['serverVersion'] == '3' and final['state'] == 'confirmed'
            assert final['versionRows'] == 3 and not final['editorStored'] and final['releaseDisabled']
            record_dom('after', final)
            c.capture_gate('final-view', context)
            await screenshot('final-confirmed-v3')
            assert counts == {'FIREFOX_LAUNCH': 1, 'NATIVE_LOGIN_POST': 1, 'STORE_SWITCH_POST': 0,
                'CLINICAL_GET': 2, 'ACQUIRE': 1, 'CONFIRM': 1, 'RELEASE': 1, 'HEARTBEAT': 0, 'OTHER_POST': 0, 'PDF': 0}
            assert not page_errors and not fatal.is_set()
            c.save(c.PRIVATE / 'accepted-context.json', context)
            await browser.close()
            browser = None
    except Exception as error:
        fail('BROWSER_FLOW_STOP', error)
    finally:
        if browser is not None:
            await browser.close()
        c.save(c.OUT / 'browser-result.json', {'status': 'BLOCKED' if failure else 'SCOPED_CODEX_SELF_TEST_COMPLETE_PENDING_GPT',
            'counts': counts, 'requests': requests, 'responses': responses, 'failure': failure,
            'page_errors_count': len(page_errors), 'page_error_sha256': [c.sha(e.encode()) for e in page_errors],
            'connection_sha256': context.get('connection_sha256'), 'scope_revision': 1, 'actor': 7,
            'screenshots_private_only': [p.name for p in sorted(c.PRIVATE.glob('*.png'))]})
    if failure:
        raise AssertionError(failure[0]['code'])


if __name__ == '__main__':
    asyncio.run(main())
