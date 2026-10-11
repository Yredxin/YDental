"""Browser-only supplement for the recorded S00-B loopback preview.

Use Chromium with its sandbox, then default Firefox, then default WebKit.
Never disable a sandbox. Credentials, profiles and downloads stay private;
only synthetic screenshots and sanitized metadata are published.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
VIEWPORT = {'width': 1280, 'height': 900}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s00b_test_[0-9]{14}_[a-f0-9]{8}', args.db), 'Database name refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink(), 'Run directory symlink refused')
    marker = run / 'database.json'
    require(not marker.is_symlink(), 'Creation record symlink refused')
    metadata = json.loads(marker.read_text())
    require(metadata['database'] == args.db
            and metadata['endpoint'] == {'host': '127.0.0.1', 'port': '5432', 'user': 'odoo'}
            and metadata['cluster'] == '7694897083368259627'
            and metadata['port'] == 18079, 'Preview identity differs from approved isolation')
    config = run / 'odoo.conf'
    require(not config.is_symlink() and sha(config) == metadata['config_sha256'], 'Configuration changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(config).encode() in Path('/proc/%s/cmdline' % pid).read_bytes().split(b'\0'),
            'Preview process identity differs; refusing HTTP requests')
    access_path = run / 'access.json'
    require(not access_path.is_symlink() and stat.S_IMODE(access_path.stat().st_mode) == 0o600
            and access_path.stat().st_uid == os.getuid(), 'Credentials must be local owned mode 0600')
    # Reject inherited settings that could disable browser security or log secrets.
    require(not any(os.environ.get(k) for k in ('MOZ_DISABLE_CONTENT_SANDBOX',
            'MOZ_DISABLE_RDD_SANDBOX', 'MOZ_DISABLE_GMP_SANDBOX',
            'WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS', 'DEBUG', 'PWDEBUG')),
            'Unsafe browser or debug environment refused')
    access = json.loads(access_path.read_text())
    secrets = {str(item[key]) for item in access.values() for key in ('login', 'password')}
    base = 'http://127.0.0.1:18079'
    private = run / ('browser-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f'))
    private.mkdir(mode=0o700)
    evidence = ROOT / 'docs/evidence/s00-b'
    evidence.mkdir(exist_ok=True)
    commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    require(not subprocess.check_output(['git', '-C', str(ROOT), 'diff', 'HEAD', '--',
            'scripts', 'ydental_base'], text=True), 'Commit browser code before executing')
    output = {'scope': 'S00-B browser UI supplement only', 'tested_commit': commit,
              'database': args.db, 'started_utc': utc(), 'playwright_version': version('playwright'),
              'viewport': VIEWPORT, 'launch_attempts': [], 'checks': [],
              'prior_http_pdf_install_upgrade_isolation': 'unchanged; not rerun'}

    def clean(value):
        text = str(value)
        for secret in sorted(secrets, key=len, reverse=True):
            if secret:
                text = text.replace(secret, '[REDACTED]')
        return re.sub(r'(?i)((?:password|cookie|token|authorization|session_id)\s*[:=]\s*)\S+',
                      r'\1[REDACTED]', text)

    def snapshot(page, ctx, name):
        secrets.update(c['value'] for c in ctx.cookies() if c['value'])
        visible = page.locator('body').inner_text()
        require(not any(s and s in visible for s in secrets), 'Visible secret; screenshot refused')
        require(page.locator('input[type=password]:visible').count() == 0, 'Password field visible')
        require(not re.search(r'(?i)(?:session_id|csrf_token|authorization|password)\s*[:=]', visible),
                'Sensitive label/value visible; screenshot refused')
        path = evidence / name
        page.screenshot(path=str(path), full_page=True)
        require(not any(s.encode() in path.read_bytes() for s in secrets if s), 'Screenshot byte scan failed')
        return {'screenshot': str(path.relative_to(ROOT)), 'screenshot_sha256': sha(path),
                'secret_check': 'visible text, password fields and PNG byte scan passed; visual review pending'}

    with sync_playwright() as playwright:
        browser = None
        for engine in ('chromium', 'firefox', 'webkit'):
            attempt = {'browser_type': engine, 'time_utc': utc(), 'headless': True,
                       'sandbox': 'explicitly enabled' if engine == 'chromium' else 'default; no security overrides'}
            try:
                options = {'headless': True, 'timeout': 30000}
                if engine == 'chromium':
                    options['chromium_sandbox'] = True
                browser = getattr(playwright, engine).launch(**options)
                attempt.update(status='PASS', browser_version=browser.version)
            except Exception as error:
                message = str(error)
                reason = ('No usable sandbox' if 'No usable sandbox' in message or 'sandboxing failed' in message
                          else 'missing browser/dependencies' if 'dependencies' in message or 'Executable' in message
                          else 'browser launch failed')
                attempt.update(status='BLOCKED', error_type=type(error).__name__, reason=reason)
                # Browser launch happens before any credentials enter the browser.
                (private / (engine + '-launch.txt')).write_text(clean(message))
                attempt['private_log_sha256'] = sha(private / (engine + '-launch.txt'))
            output['launch_attempts'].append(attempt)
            if browser:
                break
        if not browser:
            output.update(status='BLOCKED', exit_code=2)
        else:
            output.update(browser_type=engine, browser_version=browser.version)
            for role in ('authorized_zh', 'authorized_en', 'unauthorized', 'portal'):
                record = {key: output[key] for key in ('tested_commit', 'browser_type', 'browser_version',
                                                       'playwright_version', 'viewport')}
                record.update(case=role, time_utc=utc(), status='FAIL', console_error=[], pageerror=[])
                output['checks'].append(record)
                ctx = browser.new_context(viewport=VIEWPORT, accept_downloads=True, service_workers='block')
                ctx.set_default_timeout(30000)
                # Browser requests, including assets, cannot leave this exact loopback origin.
                ctx.route('**/*', lambda route: route.continue_()
                          if urlsplit(route.request.url).scheme == 'http'
                          and urlsplit(route.request.url).netloc == '127.0.0.1:18079' else route.abort())
                page = ctx.new_page()
                page.on('console', lambda msg, r=record: r['console_error'].append(clean(msg.text))
                        if msg.type == 'error' else None)
                page.on('pageerror', lambda error, r=record: r['pageerror'].append(clean(error)))
                stage = 'login'
                try:
                    page.goto(base + '/web/login?db=' + args.db + '&redirect=/ydental')
                    credential = access[role]
                    page.locator('input[name=login]').fill(credential['login'])
                    page.locator('input[name=password]').fill(credential['password'])
                    with page.expect_navigation(wait_until='load'):
                        page.locator('button[type=submit]').click()
                    require('/web/login' not in page.url, 'Login did not complete')
                    stage = 'entry'
                    response = page.goto(base + '/ydental', wait_until='load')
                    record.update(url=page.url, http_final_status=response.status, title=clean(page.title()))
                    body = page.locator('body').inner_text()
                    if role.startswith('authorized_'):
                        heading = '牙科' if role == 'authorized_zh' else 'Dental'
                        welcome = '欢迎使用 YDental。' if role == 'authorized_zh' else 'Welcome to YDental.'
                        require(response.status == 200, 'Authorized entry status differs')
                        require(page.locator('h1').inner_text() == heading and welcome in body,
                                'Entry language differs')
                        require('P00' not in body and '基线已就绪' not in body and '基线就绪' not in body,
                                'Legacy entry text remains')
                        require(not record['pageerror'], 'Entry JavaScript error')
                        record.update(snapshot(page, ctx, 'browser-' + role.replace('_', '-') + '.png'))
                        if role == 'authorized_zh':
                            stage = 'download buttons'
                            for paper in ('a4', 'narrow'):
                                item = {key: record[key] for key in ('tested_commit', 'browser_type', 'browser_version',
                                        'playwright_version', 'viewport', 'title', 'screenshot', 'screenshot_sha256')}
                                item.update(case='download_' + paper, time_utc=utc(), status='FAIL',
                                            url=base + '/ydental/sample/' + paper, console_error=[], pageerror=[])
                                output['checks'].append(item)
                                with page.expect_download() as event, page.expect_response(item['url']) as download_response:
                                    page.locator('a[href="/ydental/sample/' + paper + '"]').click()
                                download = event.value
                                require(download.failure() is None, 'Download failed')
                                destination = private / (paper + '.pdf')
                                download.save_as(destination)
                                pdf = destination.read_bytes()
                                require(pdf.startswith(b'%PDF-') and download.suggested_filename.endswith('.pdf'),
                                        'Downloaded file is not PDF')
                                require(download_response.value.status == 200, 'Download status differs')
                                item.update(status='PASS', http_final_status=download_response.value.status,
                                            download_event=True, pdf_magic=True, bytes=len(pdf), sha256=sha(destination),
                                            console_error=list(record['console_error']), pageerror=list(record['pageerror']))
                        stage = 'rendered application menu'
                        menu_response = page.goto(base + '/odoo', wait_until='load')
                        page.locator('.o_navbar_apps_menu button').click()
                        dental = page.locator('.o_app[data-menu-xmlid="ydental_base.ydental_base_menu_root"]')
                        dental.wait_for(state='visible')
                        require(dental.count() == 1 and dental.inner_text() == heading, 'Dental menu differs')
                        require(page.locator('.o_app').filter(has_text=re.compile('^' + heading + '$')).count() == 1,
                                'Duplicate Dental application entry')
                        record.update(menu_count=1, menu_label=heading, menu_http_status=menu_response.status,
                                      menu_url=page.url)
                        record['menu_evidence'] = snapshot(page, ctx, 'browser-menu-' + role[-2:] + '.png')
                        # Exercise the actual native menu entry and return to the page.
                        with page.expect_navigation(wait_until='load'):
                            dental.click()
                        require(page.url == base + '/ydental' and page.locator('h1').inner_text() == heading,
                                'Native menu did not open Dental')
                        record['menu_click_opened_entry'] = True
                        require(not record['pageerror'], 'Menu JavaScript error')
                    else:
                        require(response.status == 403, 'Unauthorized entry was not refused')
                        require(page.locator('main.o_ydental_base_home').count() == 0,
                                'Unauthorized user obtained Dental page')
                        record.update(snapshot(page, ctx, 'browser-' + role + '.png'))
                    record['status'] = 'PASS'
                except Exception as error:
                    # Playwright fill/navigation exceptions may embed credentials. Never publish their message.
                    record.update(status='FAIL', failed_stage=stage, error_type=type(error).__name__)
                finally:
                    record['finished_utc'] = utc()
                    ctx.close()
            browser.close()
            output.update(status='PASS' if all(r['status'] == 'PASS' for r in output['checks']) else 'FAIL')
            output['exit_code'] = 0 if output['status'] == 'PASS' else 1
    output.update(finished_utc=utc(), test_count=len(output['checks']))
    value = json.dumps(output, ensure_ascii=False, indent=2) + '\n'
    require(not any(s in value for s in secrets if s), 'Secret found in metadata; publication refused')
    (private / 'result.json').write_text(value)
    (evidence / 'browser-ui.json').write_text(value)
    print('Browser UI:', output['status'], '; checks:', output['test_count'], '; exit:', output['exit_code'])
    return output['exit_code']


if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('Browser verifier stopped safely:', type(error).__name__)
        sys.exit(2)
