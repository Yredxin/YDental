"""One bounded data-HTML browser dependency/lifecycle probe, no app or login.

The root controller schedules this only after source review. The caller must
record the actual OS return status. This is not a YDental UX/business pass and
cannot prove the cause of an earlier Native failure or permanent stability.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / '.local/s13'


def write_new(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if not re.fullmatch('[A-Za-z0-9_-]{1,60}', args.label):
        raise RuntimeError('A fresh explicit bounded probe label is required.')
    directory = PRIVATE / 'verification' / ('browser-runtime-' + args.label)
    directory.mkdir(mode=0o700, parents=True)
    result = {'status': 'INCOMPLETE_DATA_HTML_PROBE', 'client_pid': os.getpid(), 'client_parent_pid': os.getppid(),
        'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), 'database_or_login_requested': False,
        'app_or_economic_requests': False, 'credentials_provider_read': False, 'external_http_requests_allowed': False,
        'earlier_native_cause': 'UNKNOWN', 'manifest_does_not_prove_process_exit_zero': True}
    write_new(directory / 'intent.json', result)
    # Import inside main so the actual client identity precedes native imports.
    import browser_client as browser
    sync_playwright = browser.import_browser()
    result['browser_environment'] = browser.loaded_browser_environment_facts()
    client = context = page = None
    try:
        with sync_playwright() as playwright:
            client = playwright.chromium.launch(headless=True, executable_path=str(browser.CHROMIUM))
            try:
                context = client.new_context(locale='zh-CN', timezone_id='UTC', viewport={'width': 1366, 'height': 768})
                blocked = []
                def local_only(route):
                    if route.request.url.startswith(('data:', 'about:')):
                        route.continue_()
                    else:
                        blocked.append({'scheme': route.request.url.split(':', 1)[0]})
                        route.abort()
                context.route('**/*', local_only)
                page = context.new_page()
                text = '<!doctype html><meta charset="utf-8"><title>Local dependency probe</title><main><h1>合成浏览器依赖验证</h1><p>无数据库、无登录、无业务动作。</p></main>'
                response = page.goto('data:text/html;charset=utf-8,' + quote(text), wait_until='load', timeout=30000)
                if page.locator('h1').inner_text() != '合成浏览器依赖验证':
                    raise RuntimeError('The bounded local HTML probe did not render its own literal content.')
                result['local_page_loaded'] = True
                result['root_dimensions'] = page.evaluate('() => ({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth})')
                image = directory / 'local-data-html.png'
                page.screenshot(path=str(image), full_page=True, timeout=30000)
                os.chmod(image, 0o600)
                result['screenshot_sha256'] = hashlib.sha256(image.read_bytes()).hexdigest()
                result['blocked_nonlocal_requests'] = blocked
            finally:
                try:
                    if context is not None:
                        context.close()
                finally:
                    client.close()
        result.update(status='BOUNDED_DATA_HTML_ACTIONS_COMPLETE_REQUIRES_REAL_EXIT', api_context_exit_complete=True)
        code = 0
    except Exception as error:
        result.update(status='DATA_HTML_PROBE_FAILED_NO_AUTOMATIC_RETRY', error_class=type(error).__name__)
        code = 2
    finally:
        page = context = client = sync_playwright = None
    digest = write_new(directory / 'result.json', result)
    print(json.dumps({'status': result['status'], 'client_pid': result['client_pid'],
        'result_sha256': digest, 'result': str((directory / 'result.json').relative_to(ROOT))}))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
