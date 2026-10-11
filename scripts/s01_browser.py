"""Real Firefox S01 UI evidence against only a recorded loopback preview.

No security overrides, profile/cookie export or credential output. Screenshots
contain only synthetic store/staff/source data. Failures remain in history.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess

from playwright.sync_api import sync_playwright
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s01_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink(), 'Symlink run refused')
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['cluster'] == '7694897083368259627'
            and metadata['endpoint'] == {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
            and metadata['port'] == 18089, 'Preview identity mismatch')
    require(sha(run / 'odoo.conf') == metadata['config_sha256'], 'Runtime configuration changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'), 'Preview PID mismatch')
    require(not any(os.environ.get(k) for k in ('MOZ_DISABLE_CONTENT_SANDBOX', 'MOZ_DISABLE_RDD_SANDBOX',
            'MOZ_DISABLE_GMP_SANDBOX', 'WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS', 'DEBUG', 'PWDEBUG')), 'Unsafe browser settings refused')
    credentials = run / 'access.json'
    require(not credentials.is_symlink() and stat.S_IMODE(credentials.stat().st_mode) == 0o600
            and credentials.stat().st_uid == os.getuid(), 'Private credential permissions mismatch')
    access = json.loads(credentials.read_text())
    preview = json.loads((run / 'preview.json').read_text())
    base = 'http://127.0.0.1:18089'
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain', '--',
            'ydental_access', 'ydental_access_test', 'scripts/s01.py', 'scripts/s01_probe.py', 'scripts/s01_browser.py'], text=True),
            'Commit implementation and browser code before verification')
    evidence = ROOT / 'docs/evidence/s01'
    evidence.mkdir(parents=True, exist_ok=True)
    result = {'scope': 'S01 synthetic UI only', 'tested_commit': commit, 'database': args.db,
              'started_utc': datetime.now(timezone.utc).isoformat(), 'browser': 'Firefox',
              'sandbox': 'default; no overrides', 'checks': [], 'screenshots': []}
    secrets = {str(value[k]) for value in access.values() for k in ('login', 'password')}

    def record(name, assertion):
        require(assertion, name)
        result['checks'].append({'check': name, 'result': 'PASS'})

    def snapshot(page, context, name):
        secrets.update(c['value'] for c in context.cookies() if re.search('session|csrf|token|auth', c['name'], re.I))
        text = page.locator('body').inner_text()
        require(not any(s and s in text for s in secrets), 'Visible credential or cookie; screenshot refused')
        require(page.locator('input[type=password]:visible').count() == 0, 'Visible password input')
        require(not re.search(r'(?:csrf_token|session_id|authorization|password)\s*[:=]', text, re.I), 'Sensitive visible label')
        path = evidence / name
        page.screenshot(path=str(path), full_page=True)
        require(not any(s.encode() in path.read_bytes() for s in secrets if s), 'Screenshot credential scan failed')
        result['screenshots'].append({'path': str(path.relative_to(ROOT)), 'sha256': sha(path)})

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)
        result['browser_version'] = browser.version

        def login(role):
            context = browser.new_context(viewport={'width': 1280, 'height': 900})
            context.route('**/*', lambda route: route.continue_() if (
                urlsplit(route.request.url).hostname == '127.0.0.1' and urlsplit(route.request.url).port == 18089
            ) else route.abort())
            page = context.new_page()
            page.goto(base + '/web/login', wait_until='domcontentloaded')
            page.locator('input[name=login]').fill(access[role]['login'])
            page.locator('input[name=password]').fill(access[role]['password'])
            page.locator('button[type=submit]').click()
            page.wait_for_url(lambda url: '/web/login' not in url, timeout=30000)
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            return context, page

        def switch(page, store_id):
            page.goto(base + '/ydental/access', wait_until='domcontentloaded')
            form = page.locator('form').filter(has=page.locator('input[name=operation][value=switch]'))
            form.locator('select[name=store_id]').select_option(str(store_id))
            form.locator('button').click()
            page.wait_for_url('**/ydental/access', timeout=15000)

        try:
            ctx_a, page_a = login('operator')
            ctx_b, page_b = login('operator')
            a, b, c = preview['stores']
            switch(page_a, a)
            switch(page_b, b)
            page_a.reload(wait_until='domcontentloaded')
            record('T03 independent browser login stores', 'S01 Synthetic Store A' in page_a.locator('strong').inner_text()
                   and 'S01 Synthetic Store B' in page_b.locator('strong').inner_text())
            snapshot(page_a, ctx_a, 'browser-store-a-zh.png')
            old = ctx_a.new_page()
            old.goto(base + '/ydental/s01-synthetic', wait_until='domcontentloaded')
            editable = old.locator('form').filter(has=old.locator('input[name=record_id][value="%s"]' % preview['source_a_id']))
            record('T01 authorized synthetic A page', editable.count() == 1)
            editable.locator('input[name=name]').fill('Synthetic browser write in A')
            editable.locator('button').click()
            old.wait_for_url('**/ydental/s01-synthetic', timeout=15000)
            record('T01 authorized browser write', old.locator('input[name=name][value="Synthetic browser write in A"]').count() == 1)
            stale = ctx_a.new_page()
            stale.goto(base + '/ydental/s01-synthetic', wait_until='domcontentloaded')
            switch(page_a, b)
            form = stale.locator('form').filter(has=stale.locator('input[name=record_id][value="%s"]' % preview['source_a_id']))
            form.locator('input[name=name]').fill('Stale browser attempt')
            with stale.expect_response('**/ydental/s01-synthetic/write') as response:
                form.locator('button').click()
            record('T03 old tab write refused', response.value.status == 409 and 'version_conflict' in stale.locator('body').inner_text())
            snapshot(stale, ctx_a, 'browser-stale-page.png')
            switch(page_b, c)
            page_b.goto(base + '/ydental/s01-synthetic', wait_until='domcontentloaded')
            record('T01 C no business permission', page_b.locator('form').count() == 0)
            ctx_m, manager = login('manager')
            switch(manager, a)
            snapshot(manager, ctx_m, 'browser-staff-zh.png')
            form = manager.locator('form').filter(has=manager.locator('input[name=operation][value=preview]'))
            form.locator('input[name=user_id]').fill(str(preview['roles']['operator']))
            form.locator('select[name=template_id]').select_option(str(preview['template_id']))
            form.locator('button').click()
            manager.wait_for_url('**/ydental/access/action', timeout=15000)
            record('T09 explicit template preview', manager.locator('h1').inner_text() == '确认模板变更')
            snapshot(manager, ctx_m, 'browser-template-preview-zh.png')
            manager.locator('button[type=submit]').click()
            manager.wait_for_url('**/ydental/access', timeout=15000)
            switch(page_a, a)
            page_a.goto(base + '/ydental/s01-synthetic', wait_until='domcontentloaded')
            record('T09 template removes omitted source rights', page_a.locator('form').count() == 0)
            request_result = page_a.request.get(base + '/web/content/' + str(preview['attachment_id']))
            record('T04 revoked native attachment denied', request_result.status != 200)
            native = ctx_m.new_page()
            native.goto(base + '/odoo', wait_until='domcontentloaded')
            native.wait_for_selector('.o_ydental_access_store_status', timeout=30000)
            record('global backend store status', 'S01 Synthetic Store A' in native.locator('.o_ydental_access_store_status').inner_text())
            snapshot(native, ctx_m, 'browser-global-status-zh.png')
            ctx_p, portal = login('portal')
            record('portal workspace denied', portal.request.get(base + '/ydental/access').status == 403)
            ctx_p.close()
            result['result'] = 'PASS'
        except Exception as error:
            result['result'] = 'FAIL'
            message = str(error)
            for secret in sorted(secrets, key=len, reverse=True):
                message = message.replace(secret, '[REDACTED]')
            result['failure'] = message[:1000]
        finally:
            browser.close()
    filename = 'browser-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S') + '.json'
    (evidence / filename).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'result': result['result'], 'checks': len(result['checks']), 'evidence': filename}))
    return 0 if result['result'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
