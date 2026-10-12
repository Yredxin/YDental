"""Real Firefox S05 UI evidence on a recorded isolated preview only."""
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
    parser.add_argument('--port', type=int, default=18115)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s05_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
        'ydental_intake', 'ydental_intake_test', 'scripts/s05*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s05-rework/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S05 synthetic service intake and demonstration pricing UI', 'database': args.db, 'tested_commit': commit,
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

        def form(page, operation):
            return page.locator('form').filter(has=page.locator('input[name=operation][value="' + operation + '"]')).first

        def action(page, operation, payload, key=None):
            return page.evaluate('''async args => {
                const body = new URLSearchParams({operation:args.operation, payload:JSON.stringify(args.payload), output:'json',
                    key:args.key || crypto.randomUUID(), revision:document.querySelector('input[name=revision]').value,
                    csrf_token:document.querySelector('input[name=csrf_token]').value});
                const response=await fetch('/ydental/intake/action',{method:'POST',body});
                return {status:response.status,body:await response.json()};
            }''', {'operation': operation, 'payload': payload, 'key': key})

        try:
            desk_context, page = login('frontdesk')
            page.goto(base + '/ydental/intake')
            check('intake explains pending is separate from queue', 'A pending task has no queue number' in page.locator('body').inner_text())
            screenshot(page, desk_context, '01-qualified-before-arrival.png')
            arrival = form(page, 'arrive')
            arrival.locator('select[name=patient_id]').select_option(str(preview['patient_id']))
            arrival.locator('button').click()
            page.wait_for_url('**/ydental/intake')
            check('actual arrival visible after explicit form', page.locator('body').inner_text().count('2026-') > 0)
            task_id = preview['qualification']['task_id']
            row = page.locator('tr[data-task="%s"]' % task_id)
            row.get_by_role('button', name='Report this task', exact=True).click()
            page.wait_for_url('**/ydental/intake')
            check('first task accepted through UI', 'Intake position accepted' in page.locator('tr[data-task="%s"]' % task_id).inner_text())
            screenshot(page, desk_context, '02-arrival-and-explicit-report.png')
            other_id = preview['other']['task_id']
            page.locator('tr[data-task="%s"]' % other_id).get_by_role('button', name='Report this task', exact=True).click()
            page.wait_for_url('**/ydental/intake')
            check('switch leaves original task pending', 'Pending reporting' in page.locator('tr[data-task="%s"]' % task_id).inner_text())
            check('switch accepts chosen implant task', 'Intake position accepted' in page.locator('tr[data-task="%s"]' % other_id).inner_text())
            screenshot(page, desk_context, '03-switch-area-preserves-original-qualification.png')
            row = page.locator('tr[data-task="%s"]' % other_id)
            row.locator('summary').click()
            void = row.locator('form').filter(has=page.locator('input[name=operation][value=void]'))
            void.locator('input[name=reason]').fill('S05 Firefox explicit position void, keep qualification')
            void.locator('select[name=cancel_qualification]').select_option('no')
            void.locator('button').click()
            page.wait_for_url('**/ydental/intake')
            check('void returns task to pending', 'Pending reporting' in page.locator('tr[data-task="%s"]' % other_id).inner_text())
            check('void keeps unused qualification visible', 'Valid unused qualification' in page.locator('body').inner_text())
            screenshot(page, desk_context, '04-void-only-keeps-qualification.png')
            page.locator('tr[data-task="%s"]' % other_id).get_by_role('button', name='Report this task', exact=True).click()
            page.wait_for_url('**/ydental/intake')
            check('valid qualification can report again', 'Intake position accepted' in page.locator('tr[data-task="%s"]' % other_id).inner_text())

            manager_context, manager_page = login('manager')
            manager_page.goto(base + '/ydental/intake/prices')
            check('production price policy visibly unapproved', 'Production price locking policy is awaiting business approval' in manager_page.locator('body').inner_text())
            catalog = form(manager_page, 'catalog')
            catalog.locator('input[name=code]').fill('s05_firefox_' + datetime.now(timezone.utc).strftime('%H%M%S'))
            catalog.locator('input[name=name]').fill('S05 Firefox Service')
            catalog.locator('select[name=capability_id]').select_option(label='S05 Cleaning')
            catalog.locator('select[name=uom_id]').select_option(label='Units')
            catalog.locator('button').click()
            manager_page.wait_for_url('**/ydental/intake/prices')
            check('group catalog created through form', 'S05 Firefox Service' in manager_page.locator('body').inner_text())
            catalog_id = manager_page.locator('#create-price select[name=catalog_id] option').filter(has_text='S05 Firefox Service').get_attribute('value')
            from datetime import timedelta
            valid_start = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=2)
            valid_end = valid_start + timedelta(days=7)

            def publish_ui(amount, begin, replace=False):
                target = manager_page.locator('#create-price')
                target.locator('select[name=catalog_id]').select_option(catalog_id)
                target.locator('select[name=currency_id]').select_option(str(preview['currency_id']))
                target.locator('input[name=unit_price]').fill(str(amount))
                target.locator('input[name=start]').fill(begin.strftime('%Y-%m-%dT%H:%M'))
                target.locator('input[name=end]').fill(valid_end.strftime('%Y-%m-%dT%H:%M'))
                target.locator('input[name=reason]').fill('S05 Firefox demonstration price')
                target.locator('button').click()
                manager_page.wait_for_url('**/ydental/intake/prices')
                row = manager_page.locator('#price-versions tr[data-price]').filter(has_text='S05 Firefox Service').first
                row.locator('input[name=reason]').fill('S05 Firefox reviewed price')
                row.locator('button').click()
                manager_page.wait_for_url('**/ydental/intake/prices')
                row = manager_page.locator('#price-versions tr[data-price]').filter(has_text='S05 Firefox Service').first
                row.locator('input[name=reason]').fill('S05 Firefox approved demonstration publication')
                if replace:
                    option = row.locator('select[name=replace_choice] option').filter(has_text='S05 Firefox Service: 600').first
                    row.locator('select[name=replace_choice]').select_option(option.get_attribute('value'))
                row.locator('button').click()
                manager_page.wait_for_url('**/ydental/intake/prices')
                check('price %s reviewed and published through UI' % amount, 'Published' in manager_page.locator('#price-versions tr[data-price]').filter(has_text='S05 Firefox Service').first.inner_text())

            publish_ui(600, valid_start)
            snapshot = manager_page.locator('#demo-snapshot')
            snapshot.locator('select[name=catalog_id]').select_option(catalog_id)
            snapshot.locator('select[name=currency_id]').select_option(str(preview['currency_id']))
            snapshot.locator('input[name=source]').fill('S05 Firefox frozen 600')
            snapshot.locator('button').click()
            manager_page.wait_for_url('**/ydental/intake/prices')
            check('demo snapshot 600 shown', 'S05 Firefox frozen 600: S05 Firefox Service 600' in manager_page.locator('#price-snapshots').inner_text())
            screenshot(manager_page, manager_context, '05-price-600-frozen-demo.png')
            publish_ui(620, datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=2), replace=True)
            check('replacement leaves historic snapshot 600', 'S05 Firefox frozen 600: S05 Firefox Service 600' in manager_page.locator('#price-snapshots').inner_text())
            screenshot(manager_page, manager_context, '06-price-620-published-old-snapshot-600.png')
            no_price = action(manager_page, 'catalog', {'code':'s05_firefox_no_price_' + datetime.now(timezone.utc).strftime('%H%M%S'),
                'name':'S05 Firefox Missing Price', 'kind':'care', 'capability_id':int(form(manager_page,'catalog').locator('select[name=capability_id]').input_value()),
                'uom_id':int(form(manager_page,'catalog').locator('select[name=uom_id]').input_value())})
            check('unpriced group service created', no_price['status'] == 200)
            missing = action(manager_page, 'snapshot', {'catalog_id':no_price['body']['id'], 'currency_id':preview['currency_id'], 'quantity':1, 'source':'firefox-missing-real', 'policy':'demo_confirmation'})
            check('missing effective price explicitly rejected', missing['status'] == 409 and 'missing_price:' in missing['body']['error'])
            denied = action(manager_page, 'snapshot', {'catalog_id':int(catalog_id), 'currency_id':preview['currency_id'], 'quantity':1, 'source':'firefox-production', 'policy':'production'})
            check('unpublished production policy refused', denied['status'] == 409)

            reader_context, reader_page = login('reader')
            reader_page.goto(base + '/ydental/intake')
            check('read only role has no acquisition form', reader_page.locator('#intake-create').count() == 0)
            screenshot(reader_page, reader_context, '07-reader-no-write-controls.png')
            reader_page.goto(base + '/ydental/access')
            denied = action(reader_page, 'arrive', {'patient_id':preview['patient_id']})
            check('read only HTTP action denied', denied['status'] == 403)
            none_context, none_page = login('none')
            response = none_page.goto(base + '/ydental/intake')
            check('no permission role denied intake', response.status == 403)
            catalog_context, catalog_page = login('catalog')
            catalog_page.goto(base + '/ydental/intake/prices')
            check('group manager price none has catalog controls', catalog_page.locator('#create-catalog').count() == 1)
            check('group manager price none has no store price or mapping controls', all(
                catalog_page.locator('form input[name=operation][value="' + op + '"]').count() == 0
                for op in ('mapping', 'mapping_edit', 'price', 'review', 'publish', 'snapshot')))
            catalog_form = form(catalog_page, 'catalog')
            catalog_form.locator('input[name=code]').fill('s05_group_only_' + datetime.now(timezone.utc).strftime('%H%M%S'))
            catalog_form.locator('input[name=name]').fill('S05 Group Only Firefox')
            catalog_form.locator('button').click()
            catalog_page.wait_for_url('**/ydental/intake/prices')
            check('group price none creates catalog through UI', 'S05 Group Only Firefox' in catalog_page.locator('body').inner_text())
            edit = catalog_page.locator('form').filter(has=catalog_page.locator('input[name=name][value="S05 Group Only Firefox"]'))
            edit.locator('input[name=name]').fill('S05 Group Only Renamed')
            edit.locator('select[name=active]').select_option('no')
            edit.locator('button').click()
            catalog_page.wait_for_url('**/ydental/intake/prices')
            check('group price none edits and disables catalog through UI', 'S05 Group Only Renamed' in catalog_page.locator('input[name=name]').evaluate_all('(nodes) => nodes.map(n=>n.value)'))
            check('group price none forged price action denied', action(catalog_page, 'price', {})['status'] == 403)
            screenshot(catalog_page, catalog_context, '09-group-catalog-without-store-price.png')
            page.goto(base + '/ydental/intake')
            check('future reservation actual arrival recorded today', action(page, 'arrive', {'patient_id':preview['future']['patient_id']})['status'] == 200)
            future = action(page, 'report', {'task_id':preview['future']['task_id'], 'version':preview['future']['task_version']})
            check('tomorrow reservation report rejected today', future['status'] == 409 and 'reporting_date_mismatch:' in future['body']['error'])
            screenshot(page, desk_context, '10-future-day-report-rejected.png')
            early = action(page, 'report', {'task_id':preview['early']['task_id'], 'version':preview['early']['task_version']})
            check('same local day several hours early zero balance report succeeds', early['status'] == 200)
            doctor_context, doctor_page = login('doctor')
            doctor_page.goto(base + '/ydental/intake')
            for op in ('refer_timed', 'refer_untimed'):
                denied = action(doctor_page, op, {'source_task_id':preview['qualification']['task_id'],
                    'version':preview['qualification']['task_version'], 'mapping_id':preview['mappings'][1][0],
                    'permit':{'actor_id':access['doctor']['id']}})
                check('ordinary doctor HTTP ' + op + ' denied', denied['status'] == 403)
            screenshot(doctor_page, doctor_context, '11-doctor-no-public-referral-initiation.png')
            manager_page.goto(base + '/ydental/intake/prices')
            switched = manager_page.evaluate('''async uid => {
                const response = await fetch('/web/dataset/call_kw/res.users/write', {method:'POST',
                    headers:{'Content-Type':'application/json'}, body:JSON.stringify({jsonrpc:'2.0',method:'call',id:1,
                        params:{model:'res.users',method:'write',args:[[uid],{lang:'zh_CN'}],kwargs:{}}})});
                return response.json();
            }''', access['manager']['id'])
            check('own language preference changed through native RPC', switched.get('result') is True)
            chinese_context, manager_page = login('manager')
            manager_page.goto(base + '/ydental/intake/prices')
            check('Chinese catalog and pricing heading', manager_page.locator('h1').inner_text() == '项目目录与价目')
            check('Chinese production policy disclaimer', '正式生产锁价政策待业务负责人批准' in manager_page.locator('body').inner_text())
            screenshot(manager_page, chinese_context, '08-chinese-catalog-and-price-policy.png')
            check('no browser JavaScript errors', not errors)
            result['result'] = 'PASS'
        except Exception as error:
            result['result'] = 'FAIL'
            result['error_type'] = type(error).__name__
            raise
        finally:
            result['pageerror_count'] = len(errors)
            result['ended_utc'] = datetime.now(timezone.utc).isoformat()
            (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            browser.close()
            print(json.dumps({'result': result.get('result'), 'checks': len(result['checks']),
                'summary': str((evidence / 'summary.json').relative_to(ROOT))}))


if __name__ == '__main__':
    main()
