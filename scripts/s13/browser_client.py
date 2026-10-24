"""Normal browser primitives using the existing private Playwright packages.

The historical package directory name does not enable any synthetic clock.
Only normal password login/store selection occurs; no profile/session is saved.
"""
import os
from pathlib import Path
import sys
from urllib.parse import urlencode, urlsplit

from admission_probe import ROOT, TARGET
from http_client import BASE, ROLE_PROVIDER

RUNTIME = ROOT / '.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot'
CHROMIUM = ROOT / '.local/s11/browsers/chromium-1248/chrome-linux64/chrome'
LIBS = ROOT / '.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'
FONTCONFIG = ROOT / '.local/s12/fontconfig/fonts.conf'


def import_browser():
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('The actual existing browser package snapshot requires Python 3.12.')
    if not RUNTIME.is_dir() or not CHROMIUM.is_file() or not LIBS.is_dir() or not FONTCONFIG.is_file():
        raise RuntimeError('The existing private browser packages or font configuration are unavailable.')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(RUNTIME))
    os.environ['LD_LIBRARY_PATH'] = str(LIBS) + (':' + os.environ['LD_LIBRARY_PATH'] if os.environ.get('LD_LIBRARY_PATH') else '')
    os.environ['FONTCONFIG_FILE'] = str(FONTCONFIG)
    os.environ['FONTCONFIG_PATH'] = str(FONTCONFIG.parent)
    from playwright.sync_api import sync_playwright
    return sync_playwright


def url_fact(url):
    parsed = urlsplit(url)
    return {'scheme': parsed.scheme, 'path': parsed.path if parsed.scheme in ('http', 'https') else '<' + parsed.scheme + '>'}


class Observer:
    def __init__(self, context):
        self.responses = []
        self.failures = []
        self.external_blocks = []
        self.page_error_classes = []
        context.on('page', self.register_page)
        context.on('response', self.response)
        context.on('requestfailed', lambda request: self.failures.append(
            dict(url_fact(request.url), method=request.method, resource_type=request.resource_type)))
        context.route('**/*', self.route)

    def register_page(self, page):
        page.on('pageerror', lambda error: self.page_error_classes.append(type(error).__name__))

    def response(self, response):
        self.responses.append(dict(url_fact(response.url), method=response.request.method,
            status=response.status, resource_type=response.request.resource_type))

    def route(self, route):
        parsed = urlsplit(route.request.url)
        if parsed.scheme in ('data', 'about', 'blob') or (
                parsed.scheme in ('http', 'https') and parsed.hostname == '127.0.0.1' and parsed.port == 18411):
            route.continue_()
        else:
            self.external_blocks.append({'scheme': parsed.scheme, 'host': parsed.hostname})
            route.abort()

    def facts(self):
        return {'responses': self.responses, 'request_failures': self.failures,
            'external_blocks': self.external_blocks, 'page_error_classes': self.page_error_classes,
            'request_bodies_headers_cookies_tokens_recorded': False}


def login(page, account, expected_uid):
    page.goto(BASE + '/web/login?' + urlencode({'db': TARGET}), wait_until='domcontentloaded', timeout=30000)
    form = page.locator('form.oe_login_form')
    form.wait_for(state='visible', timeout=20000)
    form.locator('input[name="login"]').fill(account['login'])
    form.locator('input[name="password"]').fill(account['password'])
    with page.expect_response(lambda response: urlsplit(response.url).path == '/web/login'
            and response.request.method == 'POST', timeout=30000) as authenticated:
        form.locator('button[type="submit"].btn-primary').click()
    page.wait_for_load_state('domcontentloaded', timeout=30000)
    identity = page.evaluate("""async () => {
        const response = await fetch('/web/session/get_session_info', {
            method:'POST', headers:{'Content-Type':'application/json'},
            body:JSON.stringify({jsonrpc:'2.0',method:'call',params:{},id:1})});
        const value = await response.json();
        return {status:response.status, uid:(value.result||{}).uid||null};
    }""")
    if identity['status'] != 200 or identity['uid'] != expected_uid:
        raise RuntimeError('Normal browser login did not establish the expected ordinary actor.')
    return {'uid': identity['uid'], 'login_post_status': authenticated.value.status,
        'layer': 'BROWSER_NORMAL_LOGIN', 'credentials_recorded': False}


def switch_store(page, store_id):
    page.goto(BASE + '/ydental/access', wait_until='domcontentloaded', timeout=30000)
    form = page.locator('form').filter(has=page.locator('input[name="operation"][value="switch"]'))
    option = form.locator('select[name="store_id"] option').evaluate_all(
        '(rows) => rows.map(row => ({value:row.value,label:row.textContent}))')
    selected = next((row for row in option if row['value'] == str(store_id)), None)
    if not selected:
        raise RuntimeError('The authorized store is absent from the normal selector.')
    form.locator('select[name="store_id"]').select_option(label=selected['label'])
    with page.expect_response(lambda response: urlsplit(response.url).path == '/ydental/access/action'
            and response.request.method == 'POST', timeout=30000) as switched:
        form.locator('button[type="submit"]').click()
    page.wait_for_load_state('domcontentloaded', timeout=30000)
    if switched.value.status not in (200, 302, 303) or not page.locator('main.o_ydental_access_page').count():
        raise RuntimeError('Normal store selection did not complete.')
    return {'store_id': store_id, 'selected_label': selected['label'], 'status': switched.value.status,
            'layer': 'BROWSER_NORMAL_STORE_FORM'}
