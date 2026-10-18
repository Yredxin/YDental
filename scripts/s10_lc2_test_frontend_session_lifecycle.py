"""OFFLINE_ONLY native session export/delete and login snapshot regression.

Uses the existing Node executable to evaluate fixed checkout loader/session code
and the actual snapshot expression. No browser, Odoo, provider or network calls.
"""
import ast
import json
from pathlib import Path
import re
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from s10_lc2_browser import BrowserBoundaryError, BrowserSession

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT.parent / 'addons/web/static/src'
NODE = ROOT / '.local/s00-b-deps/verify-lib/playwright/driver/node'


def snapshot_expression():
    tree = ast.parse((ROOT / 'scripts/s10_lc2_browser.py').read_text())
    method = next(node for node in ast.walk(tree) if isinstance(node, ast.AsyncFunctionDef)
                  and node.name == '_login_initialization_snapshot')
    return next(ast.literal_eval(node.args[0]) for node in ast.walk(method)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'evaluate')


def evaluate_native_snapshot(*, state='exported', fallback=False, unrecognized=False, invalid_language=False):
    loader = (WEB / 'module_loader.js').read_text()
    session_module = (WEB / 'session.js').read_text()
    assert session_module.count('export const session = ') == 1
    native_factory = session_module.replace('export const session = ', 'const session = ', 1)
    localization = (WEB / 'core/l10n/localization_plugin.js').read_text()
    route_expression = re.search(r'^    translationURL = (.+);$', localization, re.M).group(1)
    configuration = {'bundle_params': {'lang': 'en_US'}}
    if not fallback:
        configuration['translationURL'] = '/website/translations'
    if invalid_language:
        configuration['bundle_params']['lang'] = 'de_DE'
    if unrecognized:
        configuration['translationURL'] = '/SYNTHETIC_UNEXPECTED_ROUTE?secret=SYNTHETIC_VALUE'
        configuration['bundle_params']['lang'] = 'SYNTHETIC_LANGUAGE'
    script = '''
globalThis.window = globalThis;
globalThis.location = {search: ''};
globalThis.CustomEvent ||= class extends Event {constructor(type, options) {super(type); this.detail=options.detail;}};
globalThis.document = {documentElement: {lang: ''}, readyState: 'complete',
    querySelector: () => ({elements: [{name:'login'}, {name:'password'},
        {name:'csrf_token'}, {name:'webauthn_response'}, {name:'SYNTHETIC_UNKNOWN_FIELD'}],
        querySelector: () => ({value:''})})};
globalThis.odoo = {};
'''+loader+'\n'
    if state in {'bootstrap', 'exported'}:
        script += 'odoo.__session_info__ = '+json.dumps(configuration)+';\n'
        # Reading private session fields must fail this test instead of crossing
        # the evaluate boundary. Only the two public configuration fields matter.
        script += "Object.defineProperty(odoo.__session_info__, 'session_secret', {get(){throw Error('PRIVATE_FIELD_READ');}});\n"
    if state in {'exported', 'empty_export'}:
        script += "odoo.define('@web/session', [], () => {"+native_factory+'\nreturn {session};});\n'
    script += 'const snapshot = ('+snapshot_expression()+')();\n'
    if state == 'exported':
        script += "if ('__session_info__' in odoo) throw Error('NATIVE_DELETE_MISSING');\n"
        script += "const session=odoo.loader.require('@web/session').session;\n"
        script += 'const actualProducerRoute='+route_expression+';\n'
        if not unrecognized:
            script += "if (snapshot.translationURL !== actualProducerRoute) throw Error('PRODUCER_ROUTE_MISMATCH');\n"
    script += 'console.log(JSON.stringify(snapshot));\n'
    outcome = subprocess.run([str(NODE)], input=script, text=True, capture_output=True,
                             timeout=10, check=True)
    return json.loads(outcome.stdout)


class FakeLocator:
    def locator(self, selector):
        return self

    async def count(self):
        return 1

    async def is_visible(self):
        return True

    async def is_editable(self, **kwargs):
        return True

    async def get_attribute(self, name):
        return 'password'


def page_for(configuration):
    async def evaluate(expression):
        return configuration
    return SimpleNamespace(evaluate=evaluate, locator=lambda selector: FakeLocator())


class NativeSessionLifecycle(unittest.TestCase):
    def test_before_and_after_actual_native_export_delete_have_same_configuration(self):
        before = evaluate_native_snapshot(state='bootstrap')
        after = evaluate_native_snapshot(state='exported')
        self.assertEqual(before['configuration_source'], 'BOOTSTRAP_GLOBAL')
        self.assertEqual(after['configuration_source'], 'NATIVE_EXPORTED_MODULE')
        self.assertTrue(before['configuration_observed'] and after['configuration_observed'])
        for name in ('translationURL', 'language', 'html_language'):
            self.assertEqual(before[name], after[name])
        self.assertEqual(after['translationURL'], '/website/translations')
        self.assertEqual(after['html_language'], 'EMPTY')

    def test_absent_or_empty_native_configuration_does_not_invent_defaults(self):
        for state in ('missing', 'empty_export'):
            value = evaluate_native_snapshot(state=state)
            self.assertFalse(value['configuration_observed'])
            self.assertIsNone(value['translationURL'])
            self.assertIsNone(value['language'])

    def test_actual_localization_fallback_only_after_configuration_is_observed(self):
        value = evaluate_native_snapshot(state='exported', fallback=True)
        self.assertTrue(value['configuration_observed'])
        self.assertEqual(value['translationURL'], '/web/webclient/translations')

    def test_only_known_configuration_and_field_names_cross_evaluation_boundary(self):
        value = evaluate_native_snapshot(state='exported', unrecognized=True)
        self.assertEqual(value['translationURL'], 'UNRECOGNIZED_TRANSLATION_ROUTE')
        self.assertEqual(value['language'], 'UNRECOGNIZED_LANGUAGE')
        self.assertTrue(value['unknown_fields'])
        self.assertNotIn('SYNTHETIC', json.dumps(value))
        self.assertNotIn('session_secret', value)


class SnapshotReadinessLifecycle(unittest.IsolatedAsyncioTestCase):
    async def test_real_snapshot_handles_consumed_session_and_empty_html_language(self):
        native = evaluate_native_snapshot(state='exported')
        # The fixed synthetic unknown field above separately tests redaction;
        # a normal login form contains only declared fields.
        native['unknown_fields'] = False
        session = BrowserSession.__new__(BrowserSession)
        session.page = page_for(native)
        session._fatal = None
        session._responses = []
        snapshot = await session._login_initialization_snapshot()
        self.assertTrue(snapshot['configuration_observed'])
        self.assertEqual(snapshot['configuration_source'], 'NATIVE_EXPORTED_MODULE')
        self.assertEqual(snapshot['html_language'], 'EMPTY')
        session._check = lambda: None
        with tempfile.TemporaryDirectory() as temporary:
            session.directory = Path(temporary)
            await session._wait_login_form_ready()

    async def test_observed_unrecognized_native_route_rejects_final_readiness(self):
        native = evaluate_native_snapshot(state='exported', unrecognized=True)
        native['unknown_fields'] = False
        session = BrowserSession.__new__(BrowserSession)
        # FakeLocator exposes no fill method: this stage cannot enter input.
        session.page = page_for(native)
        session._fatal = None
        session._responses = []
        session._check = lambda: None
        snapshot = await session._login_initialization_snapshot()
        self.assertTrue(snapshot['configuration_observed'])
        self.assertEqual(snapshot['translation_route'], 'UNRECOGNIZED_TRANSLATION_ROUTE')
        with tempfile.TemporaryDirectory() as temporary:
            session.directory = Path(temporary)
            with self.assertRaisesRegex(BrowserBoundaryError, 'ORIGINAL_UI_FRONTEND_CONFIGURATION_NOT_ADMITTED'):
                await session._wait_login_form_ready()

    async def test_observed_invalid_native_language_still_rejects_readiness(self):
        native = evaluate_native_snapshot(state='exported', invalid_language=True)
        native['unknown_fields'] = False
        session = BrowserSession.__new__(BrowserSession)
        session.page = page_for(native)
        session._fatal = None
        session._responses = []
        session._check = lambda: None
        snapshot = await session._login_initialization_snapshot()
        self.assertTrue(snapshot['configuration_observed'])
        self.assertEqual(snapshot['translation_route'], '/website/translations')
        self.assertEqual(snapshot['bundle_language'], 'UNRECOGNIZED_LANGUAGE')
        with tempfile.TemporaryDirectory() as temporary:
            session.directory = Path(temporary)
            with self.assertRaisesRegex(BrowserBoundaryError, 'ORIGINAL_UI_FRONTEND_CONFIGURATION_NOT_ADMITTED'):
                await session._wait_login_form_ready()

    async def test_missing_configuration_waits_then_observes_native_export(self):
        absent = evaluate_native_snapshot(state='missing')
        loaded = evaluate_native_snapshot(state='exported')
        loaded['unknown_fields'] = False
        session = BrowserSession.__new__(BrowserSession)
        session.page = page_for(absent)
        session._fatal = None
        session._responses = []
        session._check = lambda: None
        waits = []
        async def become_loaded(seconds):
            waits.append(seconds)
            session.page = page_for(loaded)
        with tempfile.TemporaryDirectory() as temporary:
            session.directory = Path(temporary)
            with patch('s10_lc2_browser.asyncio.sleep', side_effect=become_loaded):
                await session._wait_login_form_ready()
        self.assertEqual(waits, [.1])


if __name__ == '__main__':
    unittest.main()
