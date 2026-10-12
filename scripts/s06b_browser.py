"""Real Firefox S06B UI evidence on a recorded isolated preview only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

# Reuse only the already provisioned process-local browser assets. No install.
_BROWSER_DEPS = Path(__file__).resolve().parents[1] / '.local/s00-b-deps'
if (_BROWSER_DEPS / 'verify-lib/playwright/__init__.py').is_file():
    sys.path.insert(0, str(_BROWSER_DEPS / 'verify-lib'))
    os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(_BROWSER_DEPS / 'browsers'))
    os.environ.setdefault('LD_LIBRARY_PATH', str(_BROWSER_DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
    os.environ.setdefault('FONTCONFIG_FILE', str(_BROWSER_DEPS / 'browser-fonts.conf'))

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', type=int, default=18126)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s06b_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
    require(18000 <= args.port <= 18999, 'Isolated port refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink(), 'Symlink run refused')
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['port'] == args.port and
            metadata['cluster'] == '7694897083368259627' and metadata['endpoint'] == {
                'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}, 'Preview identity mismatch')
    require(sha(run / 'odoo.conf') == metadata['config_sha256'], 'Runtime config changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'), 'Preview PID mismatch')
    require(not any(os.environ.get(k) for k in ('MOZ_DISABLE_CONTENT_SANDBOX', 'MOZ_DISABLE_RDD_SANDBOX',
        'MOZ_DISABLE_GMP_SANDBOX', 'WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS', 'DEBUG', 'PWDEBUG')), 'Unsafe browser overrides refused')
    credentials = run / 'access-b.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials permission mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview-b.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'ydental_queue', 'ydental_queue_test', 'scripts/s06b*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s06b-rework/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S06-B real queue, unscheduled workstation leases and actual start UI', 'database': args.db, 'tested_commit': commit,
              'browser': 'Firefox', 'sandbox': 'default, no overrides', 'checks': [], 'screenshots': []}
    sensitive = {str(v[k]) for v in access.values() for k in ('login', 'password')}
    base = 'http://127.0.0.1:%s' % args.port

    def check(name, success):
        require(success, name)
        result['checks'].append({'check': name, 'result': 'PASS'})

    def screenshot(page, context, name):
        sensitive.update(c['value'] for c in context.cookies() if re.search('session|csrf|token|auth', c['name'], re.I))
        visible = page.locator('body').inner_text()
        require(not any(s and s in visible for s in sensitive), 'Visible credential, screenshot refused')
        require(page.locator('input[type=password]:visible').count() == 0, 'Visible password field')
        require(not re.search(r'(?:csrf_token|session_id|authorization|password)\s*[:=]', visible, re.I), 'Visible sensitive label')
        target = evidence / name
        page.screenshot(path=str(target), full_page=True)
        require(not any(s.encode() in target.read_bytes() for s in sensitive if s), 'Screenshot credential scan failed')
        result['screenshots'].append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target)})

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        result['browser_version'] = browser.version
        errors = []

        def login(role):
            context = browser.new_context(viewport={'width': 1360, 'height': 1000})
            context.route('**/*', lambda route: route.continue_() if (
                urlsplit(route.request.url).hostname == '127.0.0.1' and urlsplit(route.request.url).port == args.port
            ) else route.abort())
            page = context.new_page()
            def page_error(error):
                errors.append(str(error))
                # The runner captures stdout to its private log. Retain error
                # details for diagnosis, never copy this log into evidence.
                print(json.dumps({'private_pageerror': str(error), 'url': page.url}), flush=True)
            page.on('pageerror', page_error)
            def action_response(response):
                if '/ydental/queue/action' in response.url and response.status >= 400:
                    body = response.json()
                    print(json.dumps({'private_action_error': body.get('error', body.get('result')), 'status': response.status}), flush=True)
            page.on('response', action_response)
            page.goto(base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
            page.locator('input[name=login]').fill(access[role]['login'])
            page.locator('input[name=password]').fill(access[role]['password'])
            page.locator('button[type=submit]').click()
            page.wait_for_url(lambda url: '/web/login' not in url)
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            selected = page.evaluate('''async store_id => {
                const body = new URLSearchParams({operation:'switch', revision:document.querySelector('input[name=revision]').value,
                    csrf_token:document.querySelector('input[name=csrf_token]').value, output:'json', payload:JSON.stringify({store_id})});
                return (await fetch('/ydental/access/action',{method:'POST',body})).json();
            }''', preview[role.rsplit('_',1)[0]]['store'])
            require(type(selected.get('revision')) is int, 'Store switch failed')
            return context, page

        def qaction(page, operation, payload, connection=None):
            return page.evaluate("""async args => {
                const main = document.querySelector('.o_ydental_queue_workspace');
                const body = new URLSearchParams({operation:args.operation, payload:JSON.stringify(args.payload),
                    connection:args.connection || sessionStorage.getItem('ydental_queue_connection'),
                    revision:main.dataset.revision, csrf_token:main.querySelector('[name=csrf_token]').value});
                const response=await fetch('/ydental/queue/action',{method:'POST',body});
                return {status:response.status, body:await response.json()};
            }""", {'operation':operation, 'payload':payload, 'connection':connection})

        def holder(page):
            return page.evaluate("JSON.parse(sessionStorage.getItem('ydental_queue_holder'))")

        def lease_args(value):
            return {k:value[k] for k in ('lease_id','token')}

        def click_reload(page, label):
            with page.expect_navigation(wait_until='domcontentloaded'):
                with page.expect_response(lambda response: '/ydental/queue/action' in response.url) as action_response:
                    page.get_by_role('button', name=label, exact=True).click()
                response = action_response.value
                require(response.status == 200, 'UI action failed: ' + str(response.status) + ' ' + response.json().get('error', response.json().get('result', '')))

        def open_case(kind, role='doctor'):
            context, page = login(kind + '_' + role)
            page.goto(base + '/ydental/queue')
            return context, page

        def sit(page, station):
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('tr[data-station="%s"] button' % station).click()
            sensitive.add(holder(page)['token'])

        def form_reload(page, selector):
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator(selector).get_by_role('button').click()

        def row(page, task):
            return page.locator('tr[data-task="%s"]' % task)

        def begin(kind):
            context, page = open_case(kind)
            sit(page, preview[kind]['station'])
            click_reload(page, 'Call next matching task')
            click_reload(page, 'Start actual execution')
            return context, page

        def target_report(kind):
            context, desk = open_case(kind, 'frontdesk')
            form_reload(desk, '[data-pending-task="%s"] form[data-queue-form=report]' % preview[kind]['target'])
            return context, desk

        try:
            c = preview['hold']
            doctor_context, page = begin('hold')
            form_reload(page, 'form[data-queue-form=reserve]')
            check('serving becomes historical segment with independent waiting hold', page.locator('#position').get_attribute('data-state') == 'holding')
            check('holding doctor cannot call next in UI', page.get_by_role('button', name='Call next matching task', exact=True).is_disabled())
            check('holding doctor direct call is rejected', qaction(page, 'call', lease_args(holder(page)))['status'] == 409)
            screenshot(page, doctor_context, '01-reserved-workstation.png')
            desk_context, desk = target_report('hold')
            check('external explicit task reports while original hold exists', row(desk, c['target']).locator('.queue-state').inner_text() == 'waiting')
            before = desk.locator('tr[data-entry]').count()
            desk.locator('form[data-queue-form=query_return] input').fill(str(c['patient']))
            with desk.expect_response(lambda r: '/ydental/queue/action' in r.url):
                desk.locator('form[data-queue-form=query_return] button').click()
            desk.wait_for_function("document.querySelector('#queue-result').textContent.includes('Return to the original')")
            check('return query only hints original workstation and retains external queue', desk.locator('tr[data-entry]').count() == before and row(desk, c['target']).count() == 1)
            screenshot(desk, desk_context, '02-return-hint-external-waiting.png')
            second_context, second = open_case('hold', 'second')
            sit(second, c['exam_station'])
            click_reload(second, 'Call next matching task')
            page.reload()
            page.locator('form[data-queue-form=restore] [name=confirmed]').check()
            form_reload(page, 'form[data-queue-form=restore]')
            check('original doctor confirms return and resumes actual execution', page.locator('[data-execution]').count() == 1 and row(page, c['task']).locator('.queue-state').inner_text() == 'serving')
            second.reload()
            check('external calling withdrawn and other holder remains connected', row(second, c['target']).count() == 0 and second.locator('#holding-workstation').count() == 1)
            screenshot(page, doctor_context, '03-restored-after-external-call.png')
            form_reload(page, 'form[data-queue-form=handover]')
            check('handover retains doctor lease and clears patient execution', page.locator('#holding-workstation').count() == 1 and page.locator('[data-execution]').count() == 0)
            continuation = int(page.locator('[data-pending-task]').last.get_attribute('data-pending-task'))
            desk.reload()
            form_reload(desk, '[data-pending-task="%s"] form[data-queue-form=report]' % continuation)
            click_reload(second, 'Exit / rest / logout workstation')
            sit(second, c['other_station'])
            click_reload(second, 'Call next matching task')
            check('continuation can be called by another outpatient chair', row(second, continuation).locator('.queue-state').inner_text() == 'calling')
            click_reload(page, 'Call next matching task')
            check('original doctor can call next patient after saved handover', row(page, c['next_task']).locator('.queue-state').inner_text() == 'calling')
            screenshot(second, second_context, '04-continuation-other-chair.png')

            doctor_context.close(); desk_context.close(); second_context.close()
            context, actual = begin('external_serving')
            form_reload(actual, 'form[data-queue-form=reserve]')
            external_desk_context, external_desk = target_report('external_serving')
            ex_context, ex = open_case('external_serving', 'second')
            sit(ex, preview['external_serving']['exam_station'])
            click_reload(ex, 'Call next matching task')
            click_reload(ex, 'Start actual execution')
            actual.reload()
            actual.locator('form[data-queue-form=restore] [name=confirmed]').check()
            with actual.expect_response(lambda r: '/ydental/queue/action' in r.url) as refused:
                actual.locator('form[data-queue-form=restore] button').click()
            check('external actual serving prevents restore', refused.value.status == 409 and actual.locator('[data-hold]').count() == 1)
            screenshot(actual, context, '05-external-serving-refuses-return.png')

            context.close(); ex_context.close(); external_desk_context.close()
            fail_context, failed = begin('save_failure')
            with failed.expect_response(lambda r: '/ydental/queue/action' in r.url) as refused:
                failed.locator('form[data-queue-form=handover] button').click()
            check('failed latest draft save leaves actual execution held', refused.value.status == 409 and failed.locator('[data-execution]').count() == 1)
            check('failed save creates no continuation', failed.locator('[data-pending-task]').count() == 1)
            screenshot(failed, fail_context, '06-save-failure-no-half-handover.png')

            fail_context.close()
            for kind in ('append_start', 'append_revoke'):
                c = preview[kind]
                ordinary_context, ordinary = open_case(kind, 'frontdesk')
                check(kind + ': ordinary frontdesk has no append UI', ordinary.locator('form[data-queue-form=append]').count() == 0)
                check(kind + ': ordinary frontdesk POST append rejected', qaction(ordinary, 'append', {'task_id': c['task'], 'reason': 'ordinary unauthorized'})['status'] == 403)
                app_context, app = open_case(kind, 'price')
                app.locator('[data-pending-task="%s"] [name=reason]' % c['task']).fill('Explicit synthetic stopped-area task')
                form_reload(app, '[data-pending-task="%s"] form[data-queue-form=append]' % c['task'])
                permit_id = int(app.locator('[data-permit]').get_attribute('data-permit'))
                check(kind + ': explicitly authorized desk creates single permit in closed input', app.locator('[data-permit]').count() == 1)
                doc_context, doc = open_case(kind)
                sit(doc, c['station'])
                click_reload(doc, 'Call next matching task')
                if kind == 'append_start':
                    click_reload(doc, 'Record real missed call')
                    ordinary.reload()
                    form_reload(ordinary, '[data-pending-task="%s"] form[data-queue-form=report]' % c['task'])
                    doc.reload()
                    check('append repeat report retains missed count', row(doc, c['task']).locator('.queue-missed').inner_text() == '1')
                    click_reload(doc, 'Call next matching task')
                    old = holder(doc)
                    doc.goto('about:blank')
                    doc.wait_for_timeout(21000)
                    sweep_context, sweep = open_case(kind, 'manager')
                    sit(sweep, c['other_station'])
                    sweep_context.close()
                    doc.goto(base + '/ydental/queue')
                    check('append call fault preserves missed and same permit', row(doc, c['task']).locator('.queue-state').inner_text() == 'waiting' and row(doc, c['task']).locator('.queue-missed').inner_text() == '1')
                    sit(doc, c['station'])
                    click_reload(doc, 'Call next matching task')
                    click_reload(doc, 'Start actual execution')
                    app.locator('[data-permit] [name=reason]').fill('stale ordinary revoke after start')
                    with app.expect_response(lambda r: '/ydental/queue/action' in r.url) as rejected:
                        app.locator('[data-permit] button').click()
                    check('start first prevents ordinary permit revoke', rejected.value.status == 409)
                    app.reload()
                    check('permit UI agrees started and only one permit exists', app.locator('[data-permit]').count() == 1 and 'started' in app.locator('[data-permit]').inner_text())
                    screenshot(doc, doc_context, '07-appended-segment-serving.png')
                else:
                    app.locator('[data-permit] [name=reason]').fill('revoke before start')
                    form_reload(app, '[data-permit] form[data-queue-form=revoke]')
                    with doc.expect_response(lambda r: '/ydental/queue/action' in r.url) as rejected:
                        doc.get_by_role('button', name='Start actual execution', exact=True).click()
                    check('revoke first prevents stale start', rejected.value.status == 409)
                    doc.reload()
                    check('revoked calling no longer appears as active queue', row(doc, c['task']).count() == 0)
                    screenshot(doc, doc_context, '08-revoked-number-no-serving.png')

                ordinary_context.close(); app_context.close(); doc_context.close()
            pharmacy_context, pharmacy = begin('pharmacy')
            check('pharmacy-only authorized workstation uses same actual execution queue', row(pharmacy, preview['pharmacy']['task']).locator('.queue-state').inner_text() == 'serving')
            screenshot(pharmacy, pharmacy_context, '09-pharmacy-queue-only.png')
            language = pharmacy.evaluate("""async uid => (await fetch('/web/dataset/call_kw/res.users/write', {method:'POST', headers:{'Content-Type':'application/json'},
                body:JSON.stringify({jsonrpc:'2.0',id:1,method:'call',params:{model:'res.users',method:'write',args:[[uid],{lang:'zh_CN'}],kwargs:{}}})})).json()""", access['pharmacy_doctor']['id'])
            check('own Chinese language preference accepted', language.get('result') is True)
            chinese_context, chinese = open_case('pharmacy')
            check('B actions and source instructions are Chinese readable', '当前执行段' in chinese.locator('body').inner_text() and '工位队列' in chinese.locator('body').inner_text())
            screenshot(chinese, chinese_context, '10-chinese-b-workstation.png')
            check('no browser page errors', not errors)
            result['result'] = 'PASS'
        finally:
            result.setdefault('result', 'FAIL_OR_INTERRUPTED')
            result['pageerror_count'] = len(errors)
            (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            browser.close()
        print(json.dumps({'result': result['result'], 'checks': len(result['checks']), 'screenshots': len(result['screenshots']), 'evidence': str(evidence)}))


if __name__ == '__main__':
    main()

