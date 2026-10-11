"""Real Firefox S04 UI evidence on a recorded isolated preview only."""
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
    parser.add_argument('--port', type=int, default=18106)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s04_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
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
        'ydental_patient', 'ydental_patient_test', 'scripts/s04*'], text=True), 'Commit implementation and verification first')
    evidence = ROOT / 'docs/evidence/s04/browser-attempts' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    result = {'scope': 'S04 synthetic patient workflow UI', 'database': args.db, 'tested_commit': commit,
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
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(base + '/web/login', wait_until='domcontentloaded')
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
                const response=await fetch('/ydental/patients/action',{method:'POST',body});
                return {status:response.status,body:await response.json()};
            }''', {'operation': operation, 'payload': payload, 'key': key})

        try:
            desk_context, page = login('frontdesk')
            patient_id = preview['original']['id']
            page.goto(base + '/ydental/patients/%s' % patient_id)
            check('shared phone produces possible duplicate link', page.locator('#duplicate-hints a').count() >= 1)
            check('frontdesk clinical link is absent', page.locator('#care-open').count() == 0)
            check('frontdesk page contains no clinical background', 'S04 SYNTHETIC CROSS STORE BACKGROUND' not in page.locator('body').inner_text())
            check('this store policy prompt exists', page.locator('#document-prompts li').count() >= 1)
            check('store relationship action is Chinese', form(page, 'relation').locator('button').inner_text() == '建立本店患者关系')
            check('actual arrival action is Chinese', form(page, 'arrival').locator('button').inner_text() == '记录当前真实到店')
            screenshot(page, desk_context, '01-frontdesk-shared-identity.png')
            form(page, 'arrival').locator('button').click()
            page.wait_for_url('**/ydental/patients/' + str(patient_id))
            check('actual arrival recorded through UI', page.locator('#store-relations').inner_text().find('2026-') >= 0)
            page.goto(base + '/ydental/patients')
            page.locator('#create-patient summary').click()
            target = form(page, 'create')
            target.locator('input[name=name]').fill('S04 Browser New Identity')
            target.locator('input[name=phone]').fill('2025550100')
            target.locator('button').click()
            page.wait_for_url(re.compile(r'/ydental/patients/\d+$'))
            new_id = int(page.url.rsplit('/', 1)[1])
            check('new identity has unique generated patient number', page.locator('#patient-identity').inner_text().startswith('P'))
            check('unknown phone region remains manual review', page.locator('span.alert-warning').count() == 1)
            page.locator('#add-contact summary').click()
            target = form(page, 'contact')
            target.locator('input[name=name]').fill('S04 Browser Declared Guardian')
            target.locator('select[name=relation]').select_option('guardian')
            target.locator('input[name=relationship]').fill('Declared parent, synthetic')
            target.locator('button').click()
            page.wait_for_url('**/ydental/patients/' + str(new_id))
            check('declared guardian saved without age or identity gate', 'S04 Browser Declared Guardian' in page.locator('#patient-contacts').inner_text())
            screenshot(page, desk_context, '02-new-identity-guardian-policy.png')
            page.locator('#edit-patient summary').click()
            target = form(page, 'edit')
            target.locator('input[name=name]').fill('S04 Browser Renamed Identity')
            target.locator('button').click()
            page.wait_for_url('**/ydental/patients/' + str(new_id))
            check('administrative rename survives reopen', 'S04 Browser Renamed Identity' in page.locator('#patient-identity').inner_text())
            page.locator('#request-merge summary').click()
            target = form(page, 'request_merge')
            target.locator('input[name=target_id]').fill(str(patient_id))
            target.locator('input[name=reason]').fill('Synthetic browser identity verification request')
            target.locator('button').click()
            page.wait_for_url('**/ydental/patients/' + str(new_id))
            page.goto(base + '/ydental/patients')
            check('store request appears without direct confirm control', page.locator('#merge-requests article').count() >= 1 and
                  page.locator('#merge-requests input[value=confirm]').count() == 0)
            screenshot(page, desk_context, '03-store-merge-request.png')
            doctor_context, doctor_page = login('doctor')
            doctor_page.goto(base + '/ydental/patients/%s' % patient_id)
            doctor_page.locator('#care-open button').click()
            doctor_page.wait_for_url('**/clinical?purpose=diagnosis')
            check('doctor reads selected patient cross-store background', 'S04 SYNTHETIC CROSS STORE BACKGROUND' in doctor_page.locator('#clinical-history').inner_text())
            check('cross-store entry has no edit form', doctor_page.locator('#clinical-history form').count() == 0)
            screenshot(doctor_page, doctor_context, '04-cross-store-care-readonly.png')
            response = action(doctor_page, 'clinical', {'patient_id': patient_id, 'record_id': preview['clinical_id'],
                'version': 1, 'values': {'allergies': 'Forbidden cross-store edit'}})
            check('browser cross-store write receives 403', response['status'] == 403)
            group_context, group_page = login('manager')
            group_page.goto(base + '/ydental/patients')
            target = form(group_page, 'confirm')
            target.locator('input[name=reason]').fill('Synthetic browser group identity confirmed')
            target.locator('button').click()
            group_page.wait_for_url('**/ydental/patients')
            check('group confirms store merge', group_page.locator('#merge-requests article').first.locator('form').count() == 0)
            page.goto(base + '/ydental/patients/' + str(new_id))
            check('merged source opens canonical patient', preview['original']['number'] in page.locator('#patient-identity').inner_text())
            check('merged contact remains available', 'S04 Browser Declared Guardian' in page.locator('#patient-contacts').inner_text())
            check('old number mapping retained', page.locator('#patient-numbers li').count() >= 2)
            screenshot(page, desk_context, '05-canonical-old-numbers.png')
            reader_context, reader_page = login('reader')
            reader_page.goto(base + '/ydental/patients')
            check('reader cannot see create form', reader_page.locator('#create-patient').count() == 0)
            reader_page.goto(base + '/ydental/access')
            denied = action(reader_page, 'create', {'values': {'name': 'Forbidden browser creation'}})
            check('reader write receives 403', denied['status'] == 403)
            check('no browser JavaScript errors', not errors)
            result['result'] = 'PASS'
        except Exception as error:
            result['result'] = 'FAIL'
            # Test messages contain synthetic labels only; no browser dumps.
            result['error_type'] = type(error).__name__
            raise
        finally:
            result['ended_utc'] = datetime.now(timezone.utc).isoformat()
            (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n')
            browser.close()
            print(json.dumps({'result': result.get('result'), 'checks': len(result['checks']),
                              'summary': str((evidence / 'summary.json').relative_to(ROOT))}))


if __name__ == '__main__':
    main()
