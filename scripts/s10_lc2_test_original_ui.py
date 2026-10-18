"""Offline contracts from installed frontend producers into the actual UI gate."""
import ast
import asyncio
import contextlib
import copy
import inspect
import json
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from urllib.parse import urlencode, urlsplit
from unittest.mock import patch
from xml.etree import ElementTree

from s10_lc2_browser import BrowserBoundaryError, BrowserSession
from s10_lc2_task_profile import MAIN, MAIN_A_ENGINEERING, MAIN_A_ORIGINAL_UI
import s10_lc2_main_a_original_runner as runner

ROOT = Path(__file__).resolve().parents[1]
ADDONS = ROOT.parent / 'addons'


def method_source(path, name):
    method = next(node for node in ast.walk(ast.parse(path.read_text()))
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name)
    method = copy.deepcopy(method)
    method.decorator_list = []
    return method


def frontend_config(lang='en_US'):
    # Execute the actual installed override with a minimal parent dictionary;
    # the override's super()/request/lang/translationURL code is unmodified.
    method = method_source(ADDONS / 'http_routing/models/ir_http.py', 'get_frontend_session_info')
    parent = type('Base', (), {'get_frontend_session_info': lambda self: {'bundle_params': {'lang': 'parent'}}})
    tree = ast.Module(body=[ast.ClassDef(name='Effective', bases=[ast.Name(id='Base', ctx=ast.Load())],
        keywords=[], body=[method], decorator_list=[])], type_ignores=[])
    scope = {'Base': parent, 'request': SimpleNamespace(is_frontend=True, lang=SimpleNamespace(code=lang))}
    exec(compile(ast.fix_missing_locations(tree), '<actual-http-routing-method>', 'exec'), scope)
    return scope['Effective']().get_frontend_session_info()


def native_translation_urls(config):
    localization = (ADDONS / 'web/static/src/core/l10n/localization_plugin.js').read_text()
    urls = (ADDONS / 'web/static/src/core/utils/urls.js').read_text()
    expression = re.search(r'^    translationURL = (.+);$', localization, re.M).group(1)
    function = re.search(r'export function objectToUrlEncodedString\(obj\) \{.*?^\}', urls, re.S | re.M).group(0).removeprefix('export ')
    method = re.search(r'^    async fetchTranslations\(hash\) \{.*?^    \}', localization, re.S | re.M).group(0)
    script = function + '\nconst session=' + json.dumps(config) + ';\nconst translationURL=' + expression + ';\n'
    script += '''(async()=>{const requests=[];let currentHash;
const browser={fetch:async(url,options)=>{requests.push(url);if(options.cache!=="no-store")throw Error("CACHE_CONTRACT_CHANGED");return {ok:true,json:async()=>({hash:currentHash})}}};
const receiver={translationURL,lang:session.bundle_params.lang,
''' + method + '''};
for(const hash of [undefined,"a".repeat(40)]){currentHash=hash;await receiver.fetchTranslations(hash);}
console.log(JSON.stringify(requests));})().catch(()=>process.exit(1));'''
    outcome = subprocess.run([str(ROOT / '.local/s00-b-deps/verify-lib/playwright/driver/node')],
        input=script, text=True, capture_output=True, timeout=10, check=True)
    return json.loads(outcome.stdout)


def gate(message_id=MAIN_A_ORIGINAL_UI):
    session = BrowserSession.__new__(BrowserSession)
    session.base_url = 'http://127.0.0.1:18410'
    session.database = MAIN
    session.case_id = 'A-ORIGINAL'
    session.task_profile = SimpleNamespace(message_id=message_id, verify=lambda: None)
    session._declared_login_user_id = 5
    session._allow_invalid_settlement = False
    return session


def request(path, *, method='GET', form=None):
    return SimpleNamespace(url='http://127.0.0.1:18410' + path, method=method,
        post_data=None if form is None else urlencode(form))


class OriginalUIContracts(unittest.TestCase):
    def test_actual_installed_override_and_js_producer_reach_final_gate(self):
        for lang in ('en_US', 'zh_CN'):
            effective = frontend_config(lang)
            self.assertEqual(effective['translationURL'], '/website/translations')
            self.assertEqual(effective['bundle_params']['lang'], lang)
            for path in native_translation_urls(effective):
                self.assertEqual(gate()._request_allowed(request(path)), '/website/translations')
            for path in native_translation_urls({'bundle_params': {'lang': lang}}):
                self.assertEqual(gate()._request_allowed(request(path)), '/web/webclient/translations')

    def test_effective_other_installed_overrides_do_not_replace_translation_url(self):
        installed = json.loads((ROOT / '.local/s10-lc2-main-a-20261018-03/observe-terminal.json').read_bytes())['modules']
        overrides = []
        for module in installed:
            path = ADDONS / module['name'] / 'models/ir_http.py'
            if not path.exists():
                path = ROOT / module['name'] / 'models/ir_http.py'
            if not path.exists():
                continue
            tree = ast.parse(path.read_text())
            methods = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'get_frontend_session_info']
            if methods:
                overrides.append(module['name'])
                if module['name'] != 'http_routing':
                    self.assertNotIn('translationURL', ast.unparse(methods[0]))
        self.assertEqual(set(overrides), {'web', 'http_routing', 'bus', 'portal', 'auth_timeout'})

    def test_translation_query_is_narrow_and_foreign_target_rejected(self):
        rejected = ['/website/translations?hash=&lang=en_US&mods=web',
                    '/website/translations?hash=&lang=en_US&lang=zh_CN',
                    '/website/translations?hash=bad&lang=en_US',
                    '/website/translations?hash=&lang=xx_XX', '/website/anything',
                    '/website/translations?lang=en_US', '/website/translations?hash=&lang=en_US#x']
        for path in rejected:
            with self.subTest(path=path), self.assertRaises((BrowserBoundaryError, ValueError)):
                gate()._request_allowed(request(path))
        with self.assertRaises(BrowserBoundaryError):
            gate()._request_allowed(SimpleNamespace(url='http://127.0.0.1:18411/website/translations?hash=&lang=en_US', method='GET', post_data=None))
        with self.assertRaises(BrowserBoundaryError):
            gate(MAIN_A_ENGINEERING)._request_allowed(request('/website/translations?hash=&lang=en_US'))

    def test_installed_passkey_hidden_field_empty_normal_password_form(self):
        template = ElementTree.parse(ADDONS / 'auth_passkey/views/auth_passkey_login_templates.xml')
        hidden = template.find(".//template[@inherit_id='web.login']/xpath/input")
        self.assertEqual(hidden.attrib, {'type': 'hidden', 'name': 'webauthn_response'})
        base = ElementTree.parse(ADDONS / 'web/views/webclient_templates.xml')
        form = base.find(".//template[@id='web.login']//form")
        names = {element.get('name') for element in form.iter('input') if element.get('name')}
        self.assertTrue({'csrf_token', 'login', 'password', 'redirect'} <= names)
        form_data = {'login': 'public-test-alias', 'password': 'offline-synthetic',
                     'csrf_token': 'offline-synthetic', 'redirect': '/ydental/access',
                     hidden.get('name'): ''}
        self.assertEqual(gate()._request_allowed(request('/web/login', method='POST', form=form_data)), '/web/login')
        for change in ({'webauthn_response': 'nonempty'}, {'type': 'webauthn'}, {'uid': '7'}):
            with self.subTest(change=change), self.assertRaises(BrowserBoundaryError):
                gate()._request_allowed(request('/web/login', method='POST', form=form_data | change))
        for uid in (None, 7):
            session = gate()
            session._declared_login_user_id = uid
            with self.assertRaises(BrowserBoundaryError):
                session._request_allowed(request('/web/login', method='POST', form=form_data))

    def test_only_standard_store_form_and_no_clinical_or_auth_rpc(self):
        form = {'operation': 'switch', 'revision': '0', 'store_id': '1', 'csrf_token': 'offline'}
        self.assertEqual(gate()._request_allowed(request('/ydental/access/action', method='POST', form=form)), '/ydental/access/action')
        for path, bad in [('/ydental/access/action', form | {'store_id': '2'}),
                          ('/ydental/clinical/action', {'operation': 'release'}),
                          ('/web/session/authenticate', {}),
                          ('/web/session/get_session_info', {}),
                          ('/website/translations?hash=&lang=en_US', {})]:
            with self.subTest(path=path), self.assertRaises(BrowserBoundaryError):
                gate()._request_allowed(request(path, method='POST', form=bad))

    def test_actual_access_html_action_redirect_contract(self):
        source = ROOT / 'ydental_access/controllers/access.py'
        methods = [method_source(source, name) for name in ('action', '_execute', '_form_arguments')]
        service = SimpleNamespace(_switch=lambda store_id: 1,
            env=SimpleNamespace(cr=SimpleNamespace(savepoint=contextlib.nullcontext)))
        redirect_source = method_source(ROOT.parent / 'odoo/http/requestlib.py', 'redirect')
        self.assertEqual(ast.literal_eval(redirect_source.args.defaults[0]), 303)
        web_request = SimpleNamespace(redirect=lambda path: {'status': 303, 'location': path}, env=service.env)
        tree = ast.Module(body=[ast.ClassDef(name='Access', bases=[], keywords=[],
            body=methods, decorator_list=[])], type_ignores=[])
        scope = {'request': web_request, 'json': json, 'AccessError': PermissionError,
                 'UserError': RuntimeError, 'ValidationError': ValueError}
        exec(compile(ast.fix_missing_locations(tree), '<actual-access-controller>', 'exec'), scope)
        controller = scope['Access']()
        controller._service = lambda revision=None: service
        self.assertEqual(controller.action('switch', '0', store_id='1'), {'status': 303, 'location': '/ydental/access'})
        self.assertEqual(controller._execute(service, 'switch', {'store_id': 1}), {'revision': 1})

    def test_saved_actual_download_blocks_another_click(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            self.assertFalse(runner.already_downloaded(directory))
            artifacts = directory / 'browser-ui-example/binary-artifacts'
            artifacts.mkdir(parents=True)
            (artifacts / 'actual.stored-original.pdf').write_bytes(b'%PDF-offline-sentinel')
            self.assertTrue(runner.already_downloaded(directory))

    def test_actual_runner_uses_only_fixed_reader5_and_original_browser(self):
        source = inspect.getsource(runner)
        self.assertIn("path = directory / 'user-5.json'", source)
        self.assertNotIn('run_editor', source)
        self.assertNotIn('acquire', source)
        self.assertNotIn('session_info', source)
        self.assertIn('original_ui(app.budget', source)


class LoginActualCallContract(unittest.IsolatedAsyncioTestCase):
    async def test_actual_login_redirect_to_access_and_form_sequence(self):
        # Invoke the actual login body, not a hand-built equivalent. No provider,
        # Playwright, application or network is used in this source regression.
        method = method_source(ROOT / 'scripts/s10_lc2_browser.py', 'login')
        namespace = dict(BrowserSession.login.__globals__)
        namespace['save_once'] = lambda *args: None
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), '<actual-login-body>', 'exec'), namespace)
        calls = []
        async def goto(path):
            calls.append(('goto', path))
        async def ready():
            calls.append(('ready', None))
        class Locator:
            def __init__(self, selector):
                self.selector = selector
            async def fill(self, value, **kwargs):
                calls.append(('fill', self.selector))
            async def click(self):
                calls.append(('click', self.selector))
        async def wait_url(predicate):
            self.assertTrue(predicate('http://127.0.0.1:18410/ydental/access'))
        async def perform(action):
            return await action()
        async def snapshot():
            return {'not_dom_export': True}
        fake = SimpleNamespace(_check=lambda: None, _logged_in=False, task_profile=gate().task_profile,
            database=MAIN, directory=Path('/tmp/offline-no-write'), _goto=goto,
            _wait_login_form_ready=ready, _perform=perform, _login_initialization_snapshot=snapshot,
            page=SimpleNamespace(locator=Locator, wait_for_url=wait_url, url='http://127.0.0.1:18410/ydental/access'))
        await namespace['login'](fake, 'offline', 'offline', user_id=5)
        self.assertEqual(urlsplit(calls[0][1]).path, '/web/login')
        self.assertIn('redirect=%2Fydental%2Faccess', calls[0][1])
        self.assertEqual([item[0] for item in calls], ['goto', 'ready', 'fill', 'fill', 'click'])
        self.assertTrue(fake._logged_in)


if __name__ == '__main__':
    unittest.main()
