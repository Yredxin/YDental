"""Real Firefox S06A UI evidence on a recorded isolated preview only."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from urllib.parse import urlsplit

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
    parser.add_argument('--port', type=int, default=18116)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
    credentials = run / 'access.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials permission mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview.json').read_text())
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
        'ydental_queue', 'ydental_queue_test', 'scripts/s06a*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s06a/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S06-A real queue, unscheduled workstation leases and actual start UI', 'database': args.db, 'tested_commit': commit,
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
            }''', preview['stores'][0])
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

        def args(value):
            return {k:value[k] for k in ('lease_id','token')}

        def click_reload(page, label):
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.get_by_role('button', name=label, exact=True).click()

        try:
            second_context, second = login('second')
            second.goto(base + '/ydental/queue')
            with second.expect_navigation(wait_until='domcontentloaded'):
                second.locator('tr[data-station="%s"] button' % preview['stations'][1]).click()
            check('second authorized person enters idle target chair', holder(second)['station_id'] == preview['stations'][1])

            doctor_context, page = login('doctor')
            page.goto(base + '/ydental/queue')
            check('queue page shows current store and explicit staffing reason', 'Current store:' in page.locator('body').inner_text())
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('tr[data-station="%s"] button' % preview['stations'][0]).click()
            original = holder(page)
            sensitive.add(original['token'])
            check('unscheduled qualified doctor enters through real UI', original['station_id'] == preview['stations'][0])
            check('no assignment is a visible reminder', 'No assignment required' in page.locator('body').inner_text())
            screenshot(page, doctor_context, '01-unscheduled-workstation.png')
            response = qaction(page, 'switch', dict(args(original), station_id=preview['stations'][1]))
            check('occupied target switch fails', response['status'] == 409)
            page.reload()
            check('failed switch preserves original holding lease', holder(page)['lease_id'] == original['lease_id'])
            screenshot(page, doctor_context, '02-switch-failure-keeps-chair.png')
            click_reload(second, 'Exit / rest / logout workstation')
            page.reload()
            with page.expect_navigation(wait_until='domcontentloaded'):
                page.locator('tr[data-station="%s"] button' % preview['stations'][1]).click()
            moved = holder(page)
            sensitive.add(moved['token'])
            check('idle switch atomically acquires new chair', moved['station_id'] == preview['stations'][1] and moved['lease_id'] != original['lease_id'])
            check('old switch token rejected', qaction(page, 'heartbeat', args(original))['status'] == 403)
            screenshot(page, doctor_context, '03-idle-switch-success.png')
            another_context, another = login('doctor')
            another.goto(base + '/ydental/queue')
            check('another login cannot renew holding session', qaction(another, 'heartbeat', args(moved))['status'] == 403)
            check('another login UI is read only for held connection', another.get_by_role('button', name='Renew holding connection').is_disabled())
            another_context.close()
            click_reload(page, 'Call next matching task')
            row = page.locator('tr[data-task="%s"]' % preview['task_id'])
            check('waiting becomes calling via UI', row.locator('.queue-state').inner_text() == 'calling')
            screenshot(page, doctor_context, '04-real-calling.png')
            click_reload(page, 'Record real missed call')
            check('real missed call returns waiting with count one', row.locator('.queue-state').inner_text() == 'waiting' and row.locator('.queue-missed').inner_text() == '1')
            desk_context, desk = login('frontdesk')
            desk.goto(base + '/ydental/intake')
            with desk.expect_navigation(wait_until='domcontentloaded'):
                desk.locator('tr[data-task="%s"]' % preview['task_id']).get_by_role('button',name='Report this task',exact=True).click()
            page.reload()
            check('same unfinished task repeat report keeps missed count', row.locator('.queue-missed').inner_text() == '1')
            screenshot(page, doctor_context, '05-missed-repeat-report.png')
            click_reload(page, 'Call next matching task')
            entry_id = int(row.get_attribute('data-entry'))
            old_connection = page.evaluate("sessionStorage.getItem('ydental_queue_connection')")
            page.goto('about:blank')  # Holding document closed, no heartbeat timer.
            page.wait_for_timeout(21000)
            manager_context, manager = login('manager')
            manager.goto(base + '/ydental/queue')
            with manager.expect_navigation(wait_until='domcontentloaded'):
                manager.locator('tr[data-station="%s"] button' % preview['stations'][0]).click()
            page.goto(base + '/ydental/queue')
            check('timeout fault returns calling to waiting', row.locator('.queue-state').inner_text() == 'waiting')
            check('fault does not erase earlier real missed count', row.locator('.queue-missed').inner_text() == '1')
            check('expired holding token cannot revive', qaction(page,'heartbeat',args(moved),old_connection)['status'] == 403)
            screenshot(page, doctor_context, '06-timeout-requeue-old-end-rejected.png')
            manager.reload()
            click_reload(manager, 'Call next matching task')
            click_reload(manager, 'Start actual execution')
            mrow = manager.locator('tr[data-task="%s"]' % preview['task_id'])
            check('calling becomes minimal actual serving through UI', mrow.locator('.queue-state').inner_text() == 'serving')
            check('serving preserves earlier missed history', mrow.locator('.queue-missed').inner_text() == '1')
            manager_lease = holder(manager)
            check('serving holder cannot exit and erase patient', qaction(manager, 'exit', args(manager_lease))['status'] == 409)
            screenshot(manager, manager_context, '07-actual-serving-fence.png')
            reader_context, reader = login('reader')
            reader.goto(base + '/ydental/queue')
            check('readonly user sees accepted queue', reader.locator('tr[data-task="%s"]' % preview['task_id']).count() == 1)
            check('readonly has no workstation actions', reader.locator('[data-operation]').count() == 0)
            check('readonly POST is rejected at server', qaction(reader,'enter',{'station_id':preview['stations'][1]})['status'] == 403)
            screenshot(reader, reader_context, '08-readonly-no-actions.png')
            # Real backend page also receives the workstation systray integration.
            manager.goto(base + '/odoo', wait_until='networkidle')
            check('backend global workstation systray loads', manager.locator('.o_ydental_queue_workstation_status').count() == 1)
            screenshot(manager, manager_context, '09-global-workstation-position.png')
            check('no browser page errors', not errors)
            result['result'] = 'PASS'
        finally:
            result.setdefault('result', 'FAIL_OR_INTERRUPTED')
            result['pageerror_count'] = len(errors)
            (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            browser.close()
        print(json.dumps({'result':result['result'],'checks':len(result['checks']),'screenshots':len(result['screenshots']), 'evidence':str(evidence)}))


if __name__ == '__main__':
    main()
