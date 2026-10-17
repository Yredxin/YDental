"""Pure fake-ORM/child transport checks; not an Odoo framework or PDF run."""
import ast
from dataclasses import dataclass
import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace
import traceback
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'ydental_settlement/models/ir_actions_report.py'
EVENTS = []
PRIMARY = []


class UserError(Exception):
    pass


class AccessError(Exception):
    pass


@dataclass(frozen=True)
class SettlementPdfScope:
    actor_id: int = 7


class FakeEnv:
    def __init__(self, scope):
        self.context = {'ydental_settlement_pdf_scope': scope}
        self.validations = 0
        self.invalid = False

    def __getitem__(self, model):
        assert model == 'ydental.settlement.service'
        return self

    def _validate_pdf_scope(self):
        self.validations += 1
        if self.invalid:
            raise AccessError('synthetic stale scope')
        return {'source_id': 77}

    def _(self, message):
        return message

    def ref(self, name):
        return ('layout', name)


class FakeBase:
    def __len__(self):
        return 1

    def browse(self, record_id):
        assert record_id == self.id
        return self

    def get_paperformat(self):
        return 'existing-paperformat'

    def _build_wkhtmltopdf_args(self, paperformat, landscape, **kwargs):
        assert paperformat == 'existing-paperformat'
        return ['--disable-local-file-access', '--quiet']

    def _run_wkhtmltopdf(self, args):
        return 'unrelated-native-super'

    def _get_layout(self):
        return 'unrelated-layout'


def record_exception(error, component, stage):
    PRIMARY.append((type(error).__name__, component, stage))
    return 'synthetic-primary-' + str(len(PRIMARY))


tree = ast.parse(SOURCE.read_text(), filename=str(SOURCE))
tree.body = [node for node in tree.body if not (
    isinstance(node, ast.ImportFrom) and
    (node.level or (node.module or '').startswith('odoo')))]
namespace = {'__name__': 'offline_actual_renderer', 'models': SimpleNamespace(Model=FakeBase),
             'UserError': UserError, 'AccessError': AccessError,
             'SettlementPdfScope': SettlementPdfScope,
             '_wkhtml': lambda: SimpleNamespace(bin='/synthetic/private/engine'),
             'emit_event': lambda event, **fields: EVENTS.append({'event': event, **fields}),
             'record_exception': record_exception}
exec(compile(tree, str(SOURCE), 'exec'), namespace)
Report = namespace['IrActionsReport']


class Child:
    def __init__(self, code=0, text='', timeout=False, cleanup=False):
        self.pid = 441
        self.returncode = None
        self.code, self.text, self.timeout, self.cleanup = code, text, timeout, cleanup
        self.calls = []
        self.killed = False

    def communicate(self, *, timeout):
        self.calls.append(timeout)
        if self.timeout and len(self.calls) == 1:
            raise subprocess.TimeoutExpired(['SENTINEL-private-command'], timeout,
                                            output='SENTINEL-private-output')
        self.returncode = -9 if self.killed else self.code
        return self.text, None

    def kill(self):
        self.killed = True
        if self.cleanup:
            raise OSError('SENTINEL-private-cleanup')


class RendererCase(unittest.TestCase):
    def setUp(self):
        EVENTS.clear()
        PRIMARY.clear()

    def report(self, scope=None, name=None):
        report = Report()
        report.id = 77
        report.env = FakeEnv(scope if scope is not None else SettlementPdfScope())
        report.report_name = name or namespace['REPORT']
        return report

    def test_exact_scope_and_existing_validation_are_both_required(self):
        class OtherScope(SettlementPdfScope):
            pass
        for scope in (object(), OtherScope()):
            report = self.report(scope)
            with self.assertRaises(AccessError):
                report._settlement_pdf_bound()
            self.assertEqual(report.env.validations, 0)
        report = self.report()
        report.env.invalid = True
        with self.assertRaises(AccessError):
            report._settlement_pdf_bound()
        self.assertEqual(report.env.validations, 1)

    def test_other_report_uses_unchanged_super_without_child(self):
        report = self.report(object(), 'other.report')
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('must not dispatch')):
            self.assertEqual(report._run_wkhtmltopdf([]), 'unrelated-native-super')
            self.assertEqual(report._get_layout(), 'unrelated-layout')

    def test_inline_body_bytes_private_files_and_cleanup(self):
        report = self.report()
        body = '<html><head><meta charset="utf-8"></head><body><div class="article page"><p>合成文本</p></div></body></html>'
        observed = []
        def render(current, args):
            self.assertIs(current.env, report.env)
            source, output = map(Path, args[-2:])
            observed.extend([source, output, source.parent])
            self.assertEqual(source.read_bytes(), body.encode('utf-8'))
            self.assertEqual(stat.S_IMODE(source.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(source.parent.stat().st_mode), 0o700)
            output.write_bytes(b'%PDF-synthetic-no-engine')
        with patch.object(Report, '_run_wkhtmltopdf', render):
            result = report._run_pdf_engine_without_processing(
                'wkhtmltopdf', [body], header='must-not-render', footer='must-not-render')
        self.assertEqual(result, b'%PDF-synthetic-no-engine')
        self.assertTrue(all(not item.exists() for item in observed))

    def test_resource_variants_rejected_before_any_child(self):
        variants = ['<img src="http://example.invalid">', '<iframe src="/x"></iframe>',
                    '<object data="/x"></object>', '<svg><image href="/x"/></svg>',
                    '<meta http-equiv="refresh" content="0;url=/x">',
                    '<div style="background:u\\72l(/x)"></div>',
                    '<div style="@import url(/x)"></div>', '<span srcset="/x 2x"></span>']
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('must not dispatch')):
            for snippet in variants:
                with self.subTest(snippet=snippet), self.assertRaises(UserError):
                    self.report()._run_pdf_engine_without_processing('wkhtmltopdf', [snippet])

    def test_real_helper_observes_only_primitive_start_and_exit(self):
        child = Child(-11)
        with patch.object(subprocess, 'Popen', return_value=child):
            result = namespace['_run_owned'](['/SENTINEL-private/engine'], 'wkhtmltopdf', 30)
        self.assertEqual(result.returncode, -11)
        self.assertEqual(EVENTS[-1]['outcome'], 'NATIVE_CRASH')
        self.assertEqual(EVENTS[-1]['renderer_signal'], 11)
        self.assertIsNone(EVENTS[-1]['renderer_exit_code'])
        self.assertNotIn('SENTINEL', repr(EVENTS))
        self.assertEqual(child.calls, [30])

    def test_font_and_engine_options_no_cookie_header_js_or_stderr(self):
        children = [Child(text='Noto Sans CJK SC'), Child()]
        commands = []
        def spawn(command, **kwargs):
            commands.append((command, kwargs))
            self.assertEqual(kwargs['stderr'], subprocess.DEVNULL)
            return children[len(commands) - 1]
        report = self.report()
        with patch.object(namespace['shutil'], 'which', return_value='/synthetic/fc-match'), \
             patch.object(subprocess, 'Popen', side_effect=spawn):
            result = report._run_wkhtmltopdf([
                '--cookie-jar', '/SENTINEL-cookie', '--header-html', '/SENTINEL-header',
                '--footer-right', 'SENTINEL-footer', '--javascript-delay', '1000',
                '--disable-local-file-access', '/synthetic/body.html', '/synthetic/output.pdf'])
        command = commands[1][0]
        self.assertEqual(command[1:4], ['--encoding', 'UTF-8', '--disable-javascript'])
        self.assertEqual(command[-2:], ['/synthetic/body.html', '/synthetic/output.pdf'])
        self.assertNotIn('SENTINEL', repr(command))
        self.assertEqual(result.stderr, '')
        self.assertEqual([item.calls for item in children], [[5], [30]])

    def test_timeout_reaps_exact_child_before_fixed_public_error(self):
        children = [Child(text='Noto Sans CJK SC'), Child(timeout=True)]
        with patch.object(namespace['shutil'], 'which', return_value='/synthetic/fc-match'), \
             patch.object(subprocess, 'Popen', side_effect=children):
            try:
                self.report()._run_wkhtmltopdf(['/synthetic/body', '/synthetic/output'])
            except UserError as public:
                text = ''.join(traceback.format_exception(type(public), public, public.__traceback__))
                self.assertNotIn('SENTINEL', text)
                self.assertTrue(public.__suppress_context__)
            else:
                self.fail('timeout silently succeeded')
        self.assertTrue(children[1].killed)
        self.assertEqual(children[1].calls, [30, 5])
        self.assertEqual([item[0] for item in PRIMARY], ['TimeoutExpired'])
        self.assertEqual(EVENTS[-1]['outcome'], 'TIMED_OUT')

    def test_failed_reap_preserves_timeout_and_separate_secondary(self):
        child = Child(timeout=True, cleanup=True)
        with patch.object(subprocess, 'Popen', return_value=child):
            with self.assertRaises(subprocess.TimeoutExpired):
                namespace['_run_owned'](['/synthetic/engine'], 'wkhtmltopdf', 30)
        secondary = next(item for item in EVENTS if item['event'] == 'renderer.cleanup_failed')
        self.assertEqual(secondary['root_event_id'], 'synthetic-primary-1')
        self.assertEqual(secondary['exception_type'], 'OSError')
        self.assertEqual(secondary['outcome'], 'REAP_FAILED')
        self.assertNotIn('SENTINEL', repr(EVENTS))


if __name__ == '__main__':
    unittest.main(verbosity=2)
