"""Guarded Firefox inspection of committed synthetic examination and controlled PDF."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / '.local/s00-b-deps'
sys.path.insert(0, str(DEPS / 'verify-lib'))
os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(DEPS / 'browsers'))
os.environ.setdefault('LD_LIBRARY_PATH', str(DEPS / 'browser-libs/usr/lib/x86_64-linux-gnu'))
os.environ.setdefault('FONTCONFIG_FILE', str(DEPS / 'browser-fonts.conf'))
from playwright.sync_api import sync_playwright


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', required=True)
    parser.add_argument('--port', required=True, type=int)
    parser.add_argument('--require-chinese', action='store_true')
    args = parser.parse_args()
    require(re.fullmatch(r'ydental_s09_test_[0-9]{14}_[0-9a-f]{8}', args.db), 'Database name refused')
    run = ROOT / '.local' / args.db
    require(not run.is_symlink() and run.is_dir(), 'Guard directory refused')
    metadata = json.loads((run / 'database.json').read_text())
    require(metadata['database'] == args.db and metadata['port'] == args.port and
            metadata['cluster'] == '7694897083368259627' and
            sha(run / 'odoo.conf') == metadata['config_sha256'], 'Database or config identity changed')
    pid = int((run / 'serve.pid').read_text())
    require(str(run / 'odoo.conf').encode() in Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0'),
            'Dedicated preview PID mismatch')
    credentials = run / 'access.json'
    require(stat.S_IMODE(credentials.stat().st_mode) == 0o600 and
            credentials.stat().st_uid == os.getuid(), 'Private credentials guard failed')
    accounts = json.loads(credentials.read_text())
    if args.require_chinese:
        require(accounts.get('language') == 'zh_CN', 'Final Chinese account fixture missing')
    f1 = json.loads((run / 'f1-result.json').read_text())
    require(f1['result'] == 'PASS' and f1['amount'] == 80 and f1['event_state'] == 'confirmed',
            'Committed F1 source is not eligible for UI review')
    evidence = ROOT / 'docs/evidence/s09-rework/browser' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    evidence.mkdir(parents=True)
    base = f'http://127.0.0.1:{args.port}'
    result = {'database': args.db, 'product_sha': '92a32bf5eb70c85eca4e020df1920d28c1908b50',
              'checks': [], 'screenshots': [], 'pageerrors': [], 'pdf': {}}

    def check(name, condition):
        require(condition, name)
        result['checks'].append(name)

    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(headless=True)

        def login(role):
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='zh-CN')
            context.route('**/*', lambda route: route.continue_() if (
                urlsplit(route.request.url).hostname == '127.0.0.1' and
                urlsplit(route.request.url).port == args.port) else route.abort())
            page = context.new_page()
            page.on('pageerror', lambda error: result['pageerrors'].append(str(error)))
            account = accounts[role]
            page.goto(base + '/web/login?redirect=/ydental/access', wait_until='domcontentloaded')
            page.locator('[name=login]').fill(account['login'])
            page.locator('[name=password]').fill(account['password'])
            page.locator('button[type=submit]').click()
            page.wait_for_url('**/ydental/access')
            selected = page.evaluate("""async store => {
                const body = new URLSearchParams({operation:'switch',
                    revision:document.querySelector('[name=revision]').value,
                    csrf_token:document.querySelector('[name=csrf_token]').value,
                    output:'json',payload:JSON.stringify({store_id:store})});
                const response=await fetch('/ydental/access/action',{method:'POST',body});
                return {status:response.status,data:await response.json()};
            }""", accounts['store_id'])
            check(role + ' switched to synthetic store', selected['status'] == 200)
            return context, page

        try:
            doctor_context, doctor = login('doctor')
            doctor.goto(base + '/ydental/exam', wait_until='domcontentloaded')
            panel = doctor.locator(f'section[data-line="{f1["line"]}"]')
            check('doctor sees committed panorama result', panel.count() == 1 and
                  ('已确认' in panel.inner_text() if args.require_chinese else
                   'Result confirmed' in panel.inner_text() or '已确认' in panel.inner_text()))
            details = doctor_context.request.get(base + f'/ydental/exam/result/{f1["line"]}')
            check('doctor opens independent authored findings and versions', details.status == 200 and
                  '合成全景所见' in details.json()['findings'] and details.json()['version'] == f1['version'])
            check('doctor sees original fee source and frozen price', str(f1['event']) in panel.inner_text() and
                  str(f1['price_snapshot']) in panel.inner_text())
            check('CBCT remains unfinished', doctor.locator(f'section[data-line="{f1["other_line"]}"]').count() == 1)
            target = evidence / 'doctor-partial-result.png'
            doctor.screenshot(path=str(target), full_page=True)
            result['screenshots'].append({'file': str(target.relative_to(ROOT)), 'sha256': sha(target)})
            denied = doctor_context.request.get(base + f'/ydental/exam/report/{f1["line"]}/{f1["version"]}')
            check('doctor without export cannot download PDF', denied.status == 403)

            examiner_context, examiner = login('examiner')
            examiner.goto(base + '/ydental/exam', wait_until='domcontentloaded')
            panel = examiner.locator(f'section[data-line="{f1["line"]}"]')
            check('examiner sees own confirmed result', panel.count() == 1 and
                  ('已确认' in panel.inner_text() if args.require_chinese else
                   'Result confirmed' in panel.inner_text() or '已确认' in panel.inner_text()))
            with examiner.expect_download() as download_info:
                panel.locator(f'a[href="/ydental/exam/report/{f1["line"]}/{f1["version"]}"]').click()
            download = download_info.value
            pdf = evidence / 'synthetic-examination-demo.pdf'
            download.save_as(pdf)
            check('authorized Firefox downloads genuine PDF', pdf.read_bytes().startswith(b'%PDF-') and
                  pdf.stat().st_size > 1000)
            result['pdf'] = {'file': str(pdf.relative_to(ROOT)), 'sha256': sha(pdf), 'bytes': pdf.stat().st_size}
            target = evidence / 'examiner-result.png'
            examiner.screenshot(path=str(target), full_page=True)
            result['screenshots'].append({'file': str(target.relative_to(ROOT)), 'sha256': sha(target)})

            reader_context, reader = login('reader')
            reader_response = reader.goto(base + '/ydental/exam', wait_until='domcontentloaded')
            if args.require_chinese:
                check('read only user sees workbench', reader_response.status == 200 and
                      reader.locator('.o_ydental_exam').count() == 1)
            else:
                check('candidate reader lacks examination grant', reader_response.status == 403)
            check('read only user cannot export', reader_context.request.get(
                base + f'/ydental/exam/report/{f1["line"]}/{f1["version"]}').status == 403)
            if args.require_chinese:
                target = evidence / 'reader-workbench.png'
                reader.screenshot(path=str(target), full_page=True)
                result['screenshots'].append({'file': str(target.relative_to(ROOT)), 'sha256': sha(target)})

            none_context, none = login('none')
            check('ungranted user workbench denied', none_context.request.get(base + '/ydental/exam').status == 403)
            check('Firefox page errors zero', not result['pageerrors'])
        finally:
            browser.close()
    (evidence / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
