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
    parser.add_argument('--cases', nargs='+', choices=['verify_execution', 'verify_hold', 'hold_targets', 'revoked_reopen'],
                        default=['verify_execution', 'verify_hold', 'hold_targets', 'revoked_reopen'])
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
    credentials = run / 'access-rework.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials permission mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview-rework.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'ydental_queue', 'ydental_queue_test', 'scripts/s06b*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s06b-rework/new-browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S06-B real queue, unscheduled workstation leases and actual start UI', 'database': args.db, 'tested_commit': commit,
              'browser': 'Firefox', 'sandbox': 'default, no overrides', 'checks': [], 'screenshots': [], 'selected_cases': args.cases}
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
            for kind, operation, label in (
                    ('verify_execution', 'takeover_verify', 'Save and take over actual execution'),
                    ('verify_hold', 'handover_verify_hold', 'Save reserved segment and create continuation')):
                if kind not in args.cases:
                    continue
                c = preview[kind]
                context, page = open_case(kind, 'second')
                form = page.locator('form[data-queue-form="%s"]' % operation)
                form.wait_for(state='visible')
                check(kind + ' has controlled on-site action', form.count() == 1)
                screenshot(page, context, kind + '-before.png')
                denied = qaction(page, operation, {'execution_id': c['execution'], 'confirmed': False, 'reason': 'missing presence confirmation'})
                check(kind + ' refuses unconfirmed presence', denied['status'] == 403)
                form.locator('[name=confirmed]').check()
                form.locator('[name=reason]').fill('Physically inspecting patient and original workstation')
                click_reload(page, label)
                new = holder(page)
                sensitive.add(new['token'])
                check(kind + ' issues a bound holding lease', page.locator('#holding-workstation').get_attribute('data-lease') == str(new['lease_id']))
                check(kind + ' leaves verification list', page.locator('form[data-verify-execution="%s"]' % c['execution']).count() == 0)
                check(kind + ' rejects second handling', qaction(page, operation, {'execution_id': c['execution'], 'confirmed': True, 'reason': 'duplicate onsite handling'})['status'] == 409)
                if kind == 'verify_execution':
                    check('actual takeover remains serving', row(page, c['task']).locator('.queue-state').inner_text() == 'serving')
                else:
                    check('hold handover leaves unique pending continuation', page.locator('[data-pending-task]').count() >= 1)
                screenshot(page, context, kind + '-after.png')
                context.close()

            if 'hold_targets' in args.cases:
                c = preview['hold_targets']
                context, page = open_case('hold_targets', 'frontdesk')
                for target, trusted in (('care', False), ('untrusted', False), ('extra', True)):
                    form = page.locator('[data-pending-task="%s"] form[data-queue-form=report]' % c[target])
                    form.wait_for(state='visible')
                    if trusted:
                        with page.expect_navigation(wait_until='domcontentloaded'):
                            form.get_by_role('button').click()
                        check('additional trusted external target reports', row(page, c[target]).locator('.queue-state').inner_text() == 'waiting')
                        screenshot(page, context, 'hold-trusted-external.png')
                    else:
                        with page.expect_response(lambda r: '/ydental/intake/action' in r.url) as response:
                            form.get_by_role('button').click()
                        check('hold rejects ' + target, response.value.status == 409)
                        page.locator('#queue-result').filter(has_text='hold_target_required').wait_for(state='visible')
                        screenshot(page, context, 'hold-denied-' + target + '.png')
                context.close()

            if 'revoked_reopen' in args.cases:
                c = preview['revoked_reopen']
                context, page = open_case('revoked_reopen', 'frontdesk')
                form = page.locator('[data-pending-task="%s"] form[data-queue-form=report]' % c['task'])
                form.wait_for(state='visible')
                with page.expect_navigation(wait_until='domcontentloaded'):
                    form.get_by_role('button').click()
                check('reopened same task reports without new append', row(page, c['task']).locator('.queue-state').inner_text() == 'waiting')
                screenshot(page, context, 'revoked-reopen-ordinary-report.png')
                context.close()
                context, page = open_case('revoked_reopen')
                sit(page, c['station'])
                click_reload(page, 'Call next matching task')
                click_reload(page, 'Start actual execution')
                check('revoked history does not block ordinary reopened start', row(page, c['task']).locator('.queue-state').inner_text() == 'serving')
                screenshot(page, context, 'revoked-reopen-ordinary-start.png')
                context.close()
            check('no browser script errors', not errors)
            result['result'] = 'PASS'
        finally:
            result.setdefault('result', 'FAIL_OR_INTERRUPTED')
            result['pageerror_count'] = len(errors)
            (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            browser.close()
        print(json.dumps({'result': result['result'], 'checks': len(result['checks']), 'screenshots': len(result['screenshots']), 'evidence': str(evidence)}))


if __name__ == '__main__':
    main()
