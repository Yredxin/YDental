"""Actual Firefox, real RPC/HTTP bodies and one controlled T05 response loss."""
import asyncio
import base64
from datetime import datetime, timezone
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import sys
import time
from urllib.parse import parse_qs, urlsplit
import s10_closeout_v1_contract as c

DEPS = c.ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.update(PLAYWRIGHT_BROWSERS_PATH=str(DEPS / 'browsers'),
    LD_LIBRARY_PATH=str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'),
    FONTCONFIG_FILE=str(DEPS / 'browser-fonts.conf'))
from PIL import Image
from playwright.async_api import async_playwright

BASE = 'http://127.0.0.1:' + str(c.PORT)
COUNTS = {'requests': 0, 'original_GET': 0, 'original_generation': 0, 'refund_PDF': 0}
MODE = sys.argv[1] if len(sys.argv) > 1 else 'pre'
STOPPED = False
LOSS_USED = False
SERVER_OBSERVER = {}
SECRET = c.read(c.PRIVATE / 'Web-secret.json')
T05 = c.read(c.RUN / 'T05.json')


def event(name, **facts):
    with (c.OUT / 'HTTP-events.jsonl').open('a') as stream:
        stream.write(c.canonical({'event': name, **facts}) + '\n'); stream.flush(); os.fsync(stream.fileno())


def dispatch(method, url, kind):
    path = urlsplit(url).path
    assert urlsplit(url).netloc == f'127.0.0.1:{c.PORT}'
    assert path.startswith(('/web/login', '/web/assets/', '/web/static/', '/website/translations',
                            '/ydental/access', '/ydental/settlement', '/web/content/', '/web/image/',
                            '/web/dataset/call_kw/')), 'REQUEST_OUTSIDE_FROZEN_PATHS'
    COUNTS['requests'] += 1
    assert COUNTS['requests'] + (c.read(c.OUT / 'Web-browser-result-pre.json')['request_counts']['requests'] if MODE == 'post' else 0) <= 600
    assert not ('/bill-original/create/' in path), 'ORIGINAL_GENERATION_BUDGET_ZERO'
    if '/bill-original/' in path:
        assert method == 'GET'
        COUNTS['original_GET'] += 1
        assert COUNTS['original_GET'] <= 12
    if '/ydental/settlement/pdf/' in path:
        assert path == '/ydental/settlement/pdf/refund/' + str(T05['refund_id'])
        COUNTS['refund_PDF'] += 1; assert COUNTS['refund_PDF'] <= 2
    event('dispatch', method=method, path=path, kind=kind)


def save_response(label, response, body):
    path = c.PRIVATE / (label + '.body')
    with path.open('xb') as stream:
        stream.write(body); stream.flush(); os.fsync(stream.fileno())
    headers = dict(response.headers)
    c.save(c.PRIVATE / (label + '-headers.json'), headers)
    metadata = {'label': label, 'status': response.status, 'MIME': headers.get('content-type'),
                'bytes': len(body), 'sha256': c.sha(body), 'body_saved_before_assertion': True}
    c.save(c.OUT / (label + '-response.json'), metadata)
    return metadata


def no_pdf_leak(body):
    reference = (c.ROOT / 'docs/evidence/s10-p0-21/UI-retained-original.pdf').read_bytes()
    assert not body.startswith(b'%PDF') and reference not in body and base64.b64encode(reference) not in body
    assert c.sha(body) != SECRET['original_sha256'], 'UNAUTHORIZED_ORIGINAL_BYTES'


async def wait_release(name, timeout=600):
    c.save(c.PRIVATE / ('browser-wait-' + name + '.json'), {'no_new_requests_while_waiting': True})
    start = time.monotonic()
    while not (c.PRIVATE / ('continue-' + name + '.json')).exists():
        assert time.monotonic() - start < timeout
        if (c.PRIVATE / 'STOP.json').exists():
            raise AssertionError('ORCHESTRATOR_STOPPED')
        await asyncio.sleep(.25)


def original_gate(before, after, changes):
    assert not [row for row in changes if row['economic']]
    for table in ['ydental_settlement_bill_original', 'ydental_clinical_document', 'ydental_clinical_version']:
        assert c.canonical(before['tables'][table]) == c.canonical(after['tables'][table])
    original_ids = {row['attachment_id'] for row in before['tables']['ydental_settlement_bill_original']}
    for row in changes:
        if row['table'] == 'ir_attachment':
            assert row['physical_key'][2] not in original_ids
            assert row['before_count'] == 0 and row['after_count'] == 1
            assert (row['after'][0].get('url') or '').startswith('/web/assets/')
    return {'economic_original_document_facts_exact': True, 'login_and_read_audits_in_full_diff': True}


def verify_T05(snapshot):
    tables = snapshot['tables']; rid = T05['refund_id']
    refund = next(row for row in tables['ydental_settlement_refund'] if row['id'] == rid)
    assert refund['ydental_state'] == 'done' and refund['ydental_payment_id'] == T05['payment_id']
    assert float(refund['ydental_amount']) == 2 and refund['ydental_native_payment_id']
    payments = [row for row in tables['account_payment'] if row['id'] == refund['ydental_native_payment_id']]
    assert len(payments) == 1 and float(payments[0]['amount']) == 2
    move = next(row for row in tables['account_move'] if row['id'] == payments[0]['move_id'])
    assert move['state'] == 'posted'
    request_rows = [row for row in tables['ydental_settlement_refund'] if row['ydental_payment_id'] == T05['payment_id']]
    assert len(request_rows) == 1
    receipts = [row for row in tables['ydental_settlement_receipt'] if row['ydental_key'] == T05['execute_key']
                and row['ydental_actor_id'] == T05['actor_uid']]
    assert len(receipts) == 1 and receipts[0]['ydental_operation'] == 'refund_execute'
    assert receipts[0]['ydental_result']['refund_id'] == rid
    inbound = next(r for r in tables['ydental_settlement_payment'] if r['id'] == T05['payment_id'])
    assert Decimal(str(inbound['ydental_amount'])) == Decimal('6')
    original_native = next(r for r in tables['account_payment'] if r['id'] == inbound['ydental_payment_id'])
    peer = [r for r in tables['account_payment'] if r['partner_id'] == original_native['partner_id']]
    assert len([r for r in peer if r['payment_type'] == 'inbound']) == 1
    assert len([r for r in peer if r['payment_type'] == 'outbound']) == 1
    assert refund['ydental_requester_id'] != refund['ydental_approver_id']
    credits = [r for r in tables['account_move'] if r['partner_id'] == original_native['partner_id'] and r['move_type'] == 'out_refund']
    assert len(credits) == 1 and credits[0]['state'] == 'posted' and Decimal(str(credits[0]['amount_total'])) == Decimal('2')
    assert credits[0]['company_id'] == move['company_id'] == original_native['company_id']
    credit_lines = {r['id'] for r in tables['account_move_line'] if r['move_id'] == credits[0]['id']}
    parts = [r for r in tables['account_partial_reconcile'] if r['credit_move_id'] in credit_lines]
    assert len(parts) == 1 and Decimal(str(parts[0]['amount'])) == Decimal('2')
    return {'refund_id': rid, 'native_payment_id': payments[0]['id'], 'native_move_id': move['id'],
            'operation_receipt_id': receipts[0]['id'], 'received': 6, 'refunded': 2, 'net': 4}


async def main():
    global STOPPED, LOSS_USED
    c.gate(business=True)
    async with async_playwright() as pw:
        browser = await pw.firefox.launch(headless=True, env=os.environ.copy())
        results = {'layer': 'REAL_FIREFOX_HTTP_RPC', 'overall': 'NOT_COMPLETE'}
        try:
            async def context():
                ctx = await browser.new_context(locale='zh-CN', viewport={'width': 1440, 'height': 1100},
                                                accept_downloads=True, service_workers='block')
                async def route(rt):
                    global LOSS_USED, SERVER_OBSERVER
                    request = rt.request
                    if STOPPED:
                        event('cancel', path=urlsplit(request.url).path); await rt.abort(); return
                    dispatch(request.method, request.url, 'browser')
                    payload = parse_qs(request.post_data or '')
                    if request.method == 'POST' and urlsplit(request.url).path == '/ydental/settlement/action':
                        assert payload.get('operation') == ['refund_execute'] and payload.get('refund_id') == [str(T05['refund_id'])]
                        assert payload.get('key') == [T05['execute_key']]
                    if (request.method == 'POST' and payload.get('operation') == ['refund_execute']
                            and payload.get('key') == [T05['execute_key']] and not LOSS_USED):
                        LOSS_USED = True
                        event('T05_response_loss_injection_intent', refund_id=T05['refund_id'],
                              request_key_sha256=c.sha(T05['execute_key'].encode()))
                        upstream = await rt.fetch()
                        body = await upstream.body()
                        save_response('D-server-response-observer-before-client-drop', upstream, body)
                        SERVER_OBSERVER = {'status': upstream.status, 'body': body}
                        event('T05_server_response_observed_client_not_delivered', status=upstream.status)
                        await rt.abort('failed')
                    else:
                        await rt.continue_()
                await ctx.route('**/*', route)
                ctx.on('response', lambda r: event('response', method=r.request.method, path=urlsplit(r.url).path, status=r.status))
                ctx.on('requestfailed', lambda r: event('failed', method=r.method, path=urlsplit(r.url).path))
                return ctx

            async def login(ctx, login_name, board=True):
                page = await ctx.new_page(); page.set_default_timeout(30000)
                await page.goto(BASE + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
                form = page.locator('form.oe_login_form')
                await form.locator('[name=login]').fill(login_name)
                await form.locator('[name=password]').fill(SECRET['password'])
                event('login_intent', login_sha256=c.sha(login_name.encode()))
                await form.locator('button[type=submit]').click(); await page.wait_for_url('**/ydental/access')
                switch = page.locator('form').filter(has=page.locator('[name=operation][value=switch]'))
                await switch.locator('select[name=store_id]').select_option(str(SECRET['store_id']))
                await switch.locator('button[type=submit]').click(); await page.wait_for_load_state('domcontentloaded')
                if board: await page.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
                return page

            async def click_original(page, label):
                (c.PRIVATE / (label + '.html')).write_text(await page.content())
                await page.screenshot(path=str(c.PRIVATE / (label + '.png')), full_page=True)
                link = page.locator(f'a[href="/ydental/settlement/bill-original/{SECRET["original_id"]}"]')
                assert await link.count() == 1
                event('real_UI_original_link_click_intent', original_id=SECRET['original_id'], label=label)
                async with page.expect_download() as pending:
                    await link.click()
                download = await pending.value
                assert await download.failure() is None
                path = c.PRIVATE / (label + '.pdf'); await download.save_as(str(path))
                digest = c.sha(path.read_bytes())
                c.save(c.OUT / (label + '-download.json'), {'layer': 'REAL_FIREFOX_UI_LINK', 'sha256': digest,
                       'bytes': path.stat().st_size, 'not_a_new_render': True})
                assert digest == SECRET['original_sha256']

            manager = await context(); page = await login(manager, SECRET['manager_login'])
            if MODE == 'post':
                await click_original(page, 'E-after-upgrade-original-v1')
                url = BASE + '/web/content/' + str(SECRET['attachment_id']) + '?download=true&access_token=' + SECRET['valid_raw_limited_token']
                dispatch('GET', url, 'post_upgrade_valid_token_negative')
                response = await manager.request.get(url, max_redirects=0)
                body = await response.body(); meta = save_response('E-valid-token-content', response, body)
                no_pdf_leak(body); assert response.status in (403, 404)
                reader = await context(); reader_page = await login(reader, SECRET['reader_login'], board=False)
                url = BASE + '/ydental/settlement/bill-original/' + str(SECRET['original_id'])
                dispatch('GET', url, 'post_upgrade_read_denial')
                response = await reader.request.get(url, max_redirects=0)
                body = await response.body(); save_response('E-read-none-export-write', response, body)
                no_pdf_leak(body); assert response.status == 403
                rpc_url = BASE + '/web/dataset/call_kw/ir.attachment.read'
                dispatch('POST', rpc_url, 'post_upgrade_RPC')
                response = await manager.request.post(rpc_url, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                    'params': {'model': 'ir.attachment', 'method': 'read', 'args': [[SECRET['attachment_id']], ['id', 'raw']], 'kwargs': {}}}), headers={'Content-Type': 'application/json'})
                body = await response.body(); save_response('E-RPC-attachment-read', response, body)
                no_pdf_leak(body); assert json.loads(body).get('error')
                c.save(c.OUT / 'Web-browser-result-post.json', {'layer': 'REAL_FIREFOX_HTTP_RPC',
                    'request_counts': COUNTS, 'original_generations': 0, 'same_SHA_UI_original': True,
                    'read_none_export_write_HTTP403': True, 'valid_token_and_RPC_denied': True})
                return
            await click_original(page, 'A-after-document-original-v1')
            after_A = await asyncio.to_thread(c.readonly, 'A-after-real-UI-retake')
            before_A = c.read(c.PRIVATE / 'r%s-D-recovered-committed-RO.json' % c.current_freeze()['round'])
            c.persist('A-real-UI-storage-window', before_A, after_A, original_gate)

            # Authenticated and genuinely anonymous finite native binary/RPC matrix.
            anonymous = await context()
            matrix = []
            for actor, ctx in [('ordinary_authorized_manager', manager), ('anonymous', anonymous)]:
                for token_kind in ['none', 'valid_limited_raw']:
                    token = '' if token_kind == 'none' else '&access_token=' + SECRET['valid_raw_limited_token']
                    for kind in ['content-download', 'image', 'image-download']:
                        aid = SECRET['attachment_id']
                        path = f'/web/content/{aid}?download=true' if kind == 'content-download' else (
                            f'/web/image/{aid}?download=true' if kind == 'image-download' else f'/web/image/{aid}?nocache=1')
                        url = BASE + path + token
                        label = 'C-%s-%s-%s' % (actor, token_kind, kind)
                        dispatch('GET', url, 'HTTP_API_negative')
                        response = await ctx.request.get(url, max_redirects=0)
                        body = await response.body(); meta = save_response(label, response, body)
                        no_pdf_leak(body)
                        if kind == 'image' and response.status == 200:
                            actual = Image.open(io.BytesIO(body)).convert('RGBA')
                            expected = Image.open(c.PRIVATE / 'expected-native-placeholder.png').convert('RGBA')
                            assert actual.size == expected.size and actual.tobytes() == expected.tobytes()
                            assert meta['MIME'].split(';')[0] == 'image/png'
                            meta['decoded_native_placeholder_pixels_equal'] = True
                            meta['pixel_sha256'] = c.sha(actual.tobytes())
                        else:
                            assert response.status in (403, 404), ('BINARY_DENIAL_STATUS', label, response.status)
                        matrix.append(meta | {'actor': actor, 'token_kind': token_kind, 'kind': kind})
                if actor == 'anonymous': continue
                for model, fields in [('ydental.settlement.bill.original', ['id', 'source_facts']),
                                      ('ir.attachment', ['id', 'raw'])]:
                    label = 'C-real-RPC-' + actor + '-' + model
                    ident = SECRET['original_id'] if model != 'ir.attachment' else SECRET['attachment_id']
                    url = BASE + '/web/dataset/call_kw/' + model + '.read'
                    dispatch('POST', url, 'REAL_JSON_RPC_negative')
                    response = await ctx.request.post(url, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 1,
                        'params': {'model': model, 'method': 'read', 'args': [[ident], fields], 'kwargs': {}}}),
                        headers={'Content-Type': 'application/json'}, max_redirects=0)
                    body = await response.body(); meta = save_response(label, response, body); no_pdf_leak(body)
                    payload = json.loads(body)
                    assert payload.get('error') and 'result' not in payload
                    meta['actual_RPC_error_name'] = payload['error'].get('data', {}).get('name')
                    matrix.append(meta | {'actor': actor, 'layer': 'REAL_JSON_RPC', 'model': model})
            rpc_rows = []
            for target in c.read(c.RUN / 'B-rpc-targets.json')['targets']:
                for operation in ['write', 'unlink']:
                    url = BASE + '/web/dataset/call_kw/' + target['model'] + '.' + operation
                    dispatch('POST', url, 'B-real-RPC-negative')
                    args = [[target['id']], target['values']] if operation == 'write' else [[target['id']]]
                    response = await manager.request.post(url, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 10,
                        'params': {'model': target['model'], 'method': operation, 'args': args, 'kwargs': {}}}),
                        headers={'Content-Type': 'application/json'}, max_redirects=0)
                    body = await response.body(); meta = save_response('B-RPC-' + target['model'] + '-' + operation, response, body)
                    payload = json.loads(body)
                    assert payload.get('error') and 'result' not in payload
                    assert payload['error']['data']['name'].endswith('AccessError')
                    rpc_rows.append(meta | {'model': target['model'], 'operation': operation, 'layer': 'REAL_RPC'})
            c.save(c.OUT / 'B-six-real-RPC-denials.json', rpc_rows)
            url = BASE + '/web/dataset/call_kw/ydental.settlement.service._bill_original_bytes'
            dispatch('POST', url, 'C-private-method-RPC')
            response = await manager.request.post(url, data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': 11,
                'params': {'model': 'ydental.settlement.service', 'method': '_bill_original_bytes',
                           'args': [SECRET['original_id']], 'kwargs': {}}}), headers={'Content-Type': 'application/json'})
            body = await response.body(); save_response('C-private-method-RPC', response, body)
            assert json.loads(body).get('error'); no_pdf_leak(body)

            c.save(c.OUT / 'C-actual-network-matrix.json', {'responses': matrix, 'P021_missing_body_not_reclassified': True})

            reader = await context(); reader_page = await login(reader, SECRET['reader_login'])
            await click_original(reader_page, 'C-authorized-reader-before-revocation')
            await reader_page.wait_for_load_state('networkidle')
            async def grant_reader(levels, label):
                assert levels in [{'export': 'none'}, {'settlement': 'none', 'export': 'write'}]
                csrf = await page.locator('input[name=csrf_token]').first.input_value()
                revision = await page.locator('input[name=revision]').first.input_value()
                target = BASE + '/ydental/access/action'
                dispatch('POST', target, 'C-real-authorized-grant')
                response = await manager.request.post(target, form={'operation': 'grant', 'revision': revision,
                    'csrf_token': csrf, 'output': 'json', 'payload': json.dumps({'user_id': SECRET['reader_id'],
                    'store_id': SECRET['store_id'], 'levels': levels})}, max_redirects=0)
                body = await response.body(); save_response(label, response, body)
                assert response.status == 200 and json.loads(body)['membership_id'] == 7
                stored = await asyncio.to_thread(c.readonly, label + '-committed')
                actual = {r['ydental_category']: r['ydental_level'] for r in stored['tables']['ydental_access_grant']
                          if r['ydental_membership_id'] == 7}
                assert all(actual.get(k, 'none') == value for k, value in levels.items())
                return stored
            await grant_reader({'export': 'none'}, 'C-http-revoke')
            url = BASE + '/ydental/settlement/bill-original/' + str(SECRET['original_id'])
            dispatch('GET', url, 'HTTP_live_revocation')
            response = await reader.request.get(url, max_redirects=0)
            body = await response.body(); meta = save_response('C-after-live-export-revocation', response, body)
            no_pdf_leak(body); assert response.status == 403
            c.save(c.OUT / 'C-live-revocation.json', meta | {'next_request_denied': True, 'not_old_page_CAS_conflict': True})

            await grant_reader({'settlement': 'none', 'export': 'write'}, 'C-http-restore')
            c.save(c.OUT / 'C-http-control-complete.json', {'real_authorized_actor': 5, 'restored_initial_levels': True, 'extra_Odoo_processes': 0})
            dispatch('GET', url, 'HTTP_read_none_export_write')
            response = await reader.request.get(url, max_redirects=0)
            body = await response.body(); save_response('C-read-none-export-write', response, body)
            no_pdf_leak(body); assert response.status == 403
            c.save(c.OUT / 'C-independent-read-denial.json', {'read_none_export_write_HTTP403': True,
                   'restored_initial_permissions': True})

            # Only the independent T05 refund is permitted to suffer one client-side loss.
            await page.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
            csrf = await page.locator('input[name=csrf_token]').first.input_value()
            revision = await page.locator('input[name=revision]').first.input_value()
            values = {'operation': 'refund_execute', 'revision': revision, 'csrf_token': csrf,
                      'key': T05['execute_key'], 'refund_id': str(T05['refund_id']),
                      'actual_utc': datetime.now(timezone.utc).isoformat(), 'proof': 'CLOSEOUT-T05 actual synthetic refund two; one controlled response loss'}
            c.save(c.PRIVATE / 'D-exact-HTTP-payload.json', values)
            js = """async values => { try {const r=await fetch('/ydental/settlement/action',{method:'POST',body:new URLSearchParams(values)});return {status:r.status,body:await r.text()};}catch(e){return {client_state:'unknown',network_error:String(e)};} }"""
            event('T05_actual_refund_POST_intent', refund_id=T05['refund_id'])
            first = await page.evaluate(js, values)
            c.save(c.OUT / 'D-client-unknown.json', first)
            known = await asyncio.to_thread(c.readonly, 'D-after-loss-verification')
            def lost_gate(a, b, changes):
                assert LOSS_USED and first.get('client_state') == 'unknown'
                assert SERVER_OBSERVER['status'] == 200 and json.loads(SERVER_OBSERVER['body'])['refund_id'] == T05['refund_id']
                copied = c.read(c.PRIVATE / 'clone-initial-RO.json')
                protected = {t: {row['id'] for row in rows if 'id' in row} for t, rows in copied['tables'].items()}
                for row in changes:
                    if row['economic'] and row['before_count']:
                        assert row['physical_key'][2] not in protected.get(row['table'], set()), ('COPIED_MONEY_CHANGED', row['table'])
                return verify_T05(b)
            verified = c.persist('D-response-loss-before-any-repeat', after_A, known, lost_gate)
            c.save(c.OUT / 'D-readonly-known-committed.json', verified | {'before_any_repeat': True})
            event('T05_verified_same_key_single_repeat_intent', refund_id=T05['refund_id'])
            repeated = await page.evaluate(js, values)
            c.save(c.PRIVATE / 'D-repeat-client-response.json', repeated)
            after = await asyncio.to_thread(c.readonly, 'D-after-same-key-repeat')
            def repeat_gate(a, b, changes):
                assert repeated['status'] == 200 and json.loads(repeated['body'])['result'] == 'already_accepted'
                assert verify_T05(b) == verified
                for row in changes:
                    assert row['table'] == 'ydental_settlement_mutex' and row['physical_key'][2] == 1
                    assert row['columns'] == ['ydental_revision'] and row['after'][0]['ydental_revision'] == row['before'][0]['ydental_revision'] + 1
                return {'all_economic_rows_exact': True, 'same_receipt_native_payment_credit_no_second_event': True}
            c.persist('D-one-known-same-key-repeat', known, after, repeat_gate)

            await page.goto(BASE + '/ydental/settlement', wait_until='domcontentloaded')
            link = page.locator(f'a[href="/ydental/settlement/pdf/refund/{T05["refund_id"]}"]')
            assert await link.count() == 1
            async with page.expect_download() as pending:
                await link.click()
            download = await pending.value
            await download.save_as(str(c.PRIVATE / 'D-new-refund-two.pdf'))
            results.update(overall='COMPLETE_PENDING_FINAL_STORAGE_AND_VISUAL_REVIEW', request_counts=COUNTS,
                           contexts=3, controlled_response_losses=1, original_generations=0, refund=verified)
            c.save(c.OUT / 'Web-browser-result-pre.json', results)
        finally:
            STOPPED = True; event('stop_new_dispatches')
            await browser.close(); event('browser_closed')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except BaseException:
        c.stop('BROWSER_OR_NETWORK_ASSERTION_FAILED')
        raise
