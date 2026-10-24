"""Normal browser primitives using the existing private Playwright packages.

The historical package directory name does not enable any synthetic clock.
Only normal password login/store selection occurs; no profile/session is saved.
"""
import os
import hashlib
import json
import stat
from pathlib import Path
import sys
from urllib.parse import urlencode, urlsplit

from admission_probe import ROOT, TARGET
from http_client import BASE, ROLE_PROVIDER

RUNTIME = ROOT / '.local/s11/operations/clock-operator-users-ui-c981cd0-attempt15-runtime-snapshot'
CHROMIUM = ROOT / '.local/s11/browsers/chromium-1248/chrome-linux64/chrome'
LIBS = ROOT / '.local/s11/browser-deps/root/usr/lib/x86_64-linux-gnu'
FONTCONFIG = ROOT / '.local/s12/fontconfig/fonts.conf'
BROWSER_NATIVE = ROOT / '.local/s13/browser-native'
BROWSER_NATIVE_MANIFEST = ROOT / '.local/s13/browser-native-manifest.json'
GREENLET_VERSION = '3.5.6'
GREENLET_RANGE = '>=3.1.1,<4'
NATIVE_MANIFEST_SHA256 = '7e6c0939fb0f0a0d50a29fb0d20bc353dcdc22bf765efe18d69b4687326f88d9'
GREENLET_BINARY_SHA256 = 'a39d6693c3aee88d76b6156e2fe915639bd47b0106c88676efa96ccb62df4e65'


def browser_environment_facts():
    """Validate the explicit private corrective wheel without starting a driver.

    This corrects an observed dependency-range mismatch. It does not establish
    the cause of the earlier native crash or claim that it cannot recur.
    """
    info = BROWSER_NATIVE_MANIFEST.lstat()
    if (BROWSER_NATIVE_MANIFEST.is_symlink() or not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.geteuid() or info.st_mode & 0o077):
        raise RuntimeError('The explicit browser native manifest is not private and owned.')
    raw = BROWSER_NATIVE_MANIFEST.read_bytes()
    if hashlib.sha256(raw).hexdigest() != NATIVE_MANIFEST_SHA256:
        raise RuntimeError('The reviewed corrective browser wheel manifest changed.')
    manifest = json.loads(raw)
    if (manifest.get('package') != 'greenlet' or manifest.get('version') != GREENLET_VERSION
            or manifest.get('required_greenlet_range') != GREENLET_RANGE
            or manifest.get('expected_playwright_version') != '1.64.0'):
        raise RuntimeError('The fixed browser dependency binding differs from the reviewed versions.')
    info = BROWSER_NATIVE.lstat()
    if (BROWSER_NATIVE.is_symlink() or not stat.S_ISDIR(info.st_mode)
            or info.st_uid != os.geteuid() or info.st_mode & 0o077):
        raise RuntimeError('The corrective native dependency directory is not private and owned.')
    expected = {}
    for item in manifest['files']:
        relative = Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts or item['path'] in expected:
            raise RuntimeError('Unsafe or duplicate native dependency path.')
        expected[item['path']] = item
    actual = set()
    for path in BROWSER_NATIVE.rglob('*'):
        info = path.lstat()
        if path.is_symlink() or info.st_uid != os.geteuid():
            raise RuntimeError('Browser native dependency ownership or path mismatch.')
        if not path.is_file():
            continue
        relative = path.relative_to(BROWSER_NATIVE).as_posix()
        if '__pycache__' in path.parts or relative == '.lock' and info.st_size == 0:
            continue
        actual.add(relative)
        if (relative not in expected or info.st_size != expected[relative]['bytes']
                or hashlib.sha256(path.read_bytes()).hexdigest() != expected[relative]['sha256']):
            raise RuntimeError('A corrective native dependency payload changed.')
    if actual != set(expected):
        raise RuntimeError('The corrective dependency file set differs from its fixed manifest.')
    return {'playwright_version_expected': '1.64.0', 'greenlet_version_expected': GREENLET_VERSION,
            'required_greenlet_range': GREENLET_RANGE, 'native_manifest_sha256': NATIVE_MANIFEST_SHA256,
            'corrective_wheel_sha256': manifest['wheel']['sha256'],
            'native_directory': str(BROWSER_NATIVE), 'original_snapshot_preserved': True,
            'earlier_native_crash_cause': 'UNKNOWN'}



def import_browser():
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('The actual existing browser package snapshot requires Python 3.12.')
    if not RUNTIME.is_dir() or not CHROMIUM.is_file() or not LIBS.is_dir() or not FONTCONFIG.is_file():
        raise RuntimeError('The existing private browser packages or font configuration are unavailable.')
    sys.dont_write_bytecode = True
    browser_environment_facts()
    loaded = sys.modules.get('greenlet')
    if loaded is not None and Path(loaded.__file__).resolve() != BROWSER_NATIVE / 'greenlet/__init__.py':
        raise RuntimeError('An incompatible greenlet was already loaded; do not reload a native extension in place.')
    sys.path[:] = [str(BROWSER_NATIVE), str(RUNTIME), *[entry for entry in sys.path
        if entry not in (str(BROWSER_NATIVE), str(RUNTIME))]]
    os.environ['LD_LIBRARY_PATH'] = str(LIBS) + (':' + os.environ['LD_LIBRARY_PATH'] if os.environ.get('LD_LIBRARY_PATH') else '')
    os.environ['FONTCONFIG_FILE'] = str(FONTCONFIG)
    os.environ['FONTCONFIG_PATH'] = str(FONTCONFIG.parent)
    import greenlet
    if (greenlet.__version__ != GREENLET_VERSION
            or Path(greenlet.__file__).resolve() != BROWSER_NATIVE / 'greenlet/__init__.py'):
        raise RuntimeError('The actual loaded corrective greenlet version or module path differs.')
    extension = sys.modules.get('greenlet._greenlet')
    expected_extension = BROWSER_NATIVE / 'greenlet/_greenlet.cpython-312-x86_64-linux-gnu.so'
    if (extension is None or Path(extension.__file__).resolve() != expected_extension
            or hashlib.sha256(expected_extension.read_bytes()).hexdigest() != GREENLET_BINARY_SHA256):
        raise RuntimeError('The actual loaded greenlet native extension differs from the fixed payload.')
    from playwright import _repo_version
    if _repo_version.__version__ != '1.64.0':
        raise RuntimeError('The existing approved Playwright API version changed.')
    from playwright.sync_api import sync_playwright
    return sync_playwright


def loaded_browser_environment_facts():
    facts = browser_environment_facts()
    greenlet = sys.modules.get('greenlet')
    extension = sys.modules.get('greenlet._greenlet')
    if greenlet is not None:
        facts.update(greenlet_version_loaded=greenlet.__version__, greenlet_module=str(Path(greenlet.__file__).resolve()))
    if extension is not None:
        facts.update(greenlet_extension=str(Path(extension.__file__).resolve()),
                     greenlet_extension_sha256=hashlib.sha256(Path(extension.__file__).read_bytes()).hexdigest())
    return facts


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
