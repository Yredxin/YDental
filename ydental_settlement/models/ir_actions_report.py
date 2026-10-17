"""Bound settlement rendering without browser resources or textual engine errors."""
from contextlib import ExitStack
import shutil
import subprocess
import tempfile

from lxml import etree, html

from odoo import models
from odoo.exceptions import AccessError, UserError
from odoo.addons.base_report_wkhtmltox.models.ir_actions_report import _wkhtml
from odoo.addons.ydental_access.diagnostics import emit_event, record_exception

from .ydental_settlement_service import SettlementPdfScope


REPORT = 'ydental_settlement.ydental_settlement_pdf'
_TAGS = frozenset({'html', 'head', 'meta', 'body', 'main', 'div', 'h1', 'p',
                   'span', 'table', 'thead', 'tbody', 'tr', 'th', 'td'})
_STYLES = frozenset({
    "font-family:'Noto Sans CJK SC',sans-serif;font-size:12px;line-height:1.6",
    'color:#a00;font-weight:bold', 'width:100%;border-collapse:collapse', 'width:100%',
})
_REMOVED_OPTIONS = {
    '--cookie-jar': 1, '--cookie': 2, '--custom-header': 2,
    '--custom-header-propagation': 0, '--no-custom-header-propagation': 0,
    '--header-html': 1, '--header-center': 1, '--header-left': 1, '--header-right': 1,
    '--header-font-name': 1, '--header-font-size': 1, '--header-spacing': 1,
    '--header-line': 0, '--no-header-line': 0,
    '--footer-html': 1, '--footer-center': 1, '--footer-left': 1, '--footer-right': 1,
    '--footer-font-name': 1, '--footer-font-size': 1, '--footer-spacing': 1,
    '--footer-line': 0, '--no-footer-line': 0,
    '--javascript-delay': 1, '--enable-javascript': 0, '--disable-javascript': 0,
    '--encoding': 1,
}


def _renderer_event(event, operation, child, outcome):
    code = child.returncode
    emit_event(event, component='ydental_settlement.report', operation=operation,
               stage='pdf.renderer', outcome=outcome,
               renderer_pid=child.pid,
               renderer_exit_code=code if code is not None and code >= 0 else None,
               renderer_signal=-code if code is not None and code < 0 else None,
               severity='CRITICAL' if code is not None and code < 0 else 'INFO',
               transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED')


def _run_owned(command, operation, timeout, capture_stdout=False):
    """Reap only this child; neither command nor engine output enters diagnostics."""
    child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                             stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, encoding='utf-8', errors='replace')
    _renderer_event('renderer.start', operation, child, 'STARTED')
    try:
        stdout, _stderr = child.communicate(timeout=timeout)
    except BaseException as primary:
        primary_id = record_exception(primary, 'ydental_settlement.report', 'pdf.renderer')
        try:
            child.kill()
            child.communicate(timeout=5)
        except BaseException as secondary:
            emit_event('renderer.cleanup_failed', component='ydental_settlement.report',
                       operation=operation, stage='pdf.renderer.cleanup',
                       exception_type=type(secondary).__name__, root_event_id=primary_id,
                       renderer_pid=child.pid, outcome='REAP_FAILED', severity='CRITICAL',
                       transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED')
        _renderer_event('renderer.exit', operation, child,
                        'TIMED_OUT' if isinstance(primary, subprocess.TimeoutExpired) else 'INTERRUPTED')
        raise
    _renderer_event('renderer.exit', operation, child,
                    'NATIVE_CRASH' if child.returncode < 0 else 'EXITED')
    return subprocess.CompletedProcess(command, child.returncode, stdout or '', '')


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _settlement_pdf_bound(self):
        if len(self) != 1 or self.report_name != REPORT:
            return False
        # The existing validator checks exact type, actor/session/revision and payload digest.
        # Never construct a print RenderScope or borrow the sudo report's environment.
        if type(self.env.context.get('ydental_settlement_pdf_scope')) is not SettlementPdfScope:
            raise AccessError(self.env._('access_denied: A bound settlement export request is required.'))
        self.env['ydental.settlement.service']._validate_pdf_scope()
        return True

    def _get_report(self, report_ref):
        report = super()._get_report(report_ref)
        if report.report_name == REPORT:
            self.env['ydental.settlement.service']._validate_pdf_scope()
        return report

    def _get_layout(self):
        if self._settlement_pdf_bound():
            return self.env.ref('ydental_print.ydental_pdf_layout')
        return super()._get_layout()

    def _run_pdf_engine_without_processing(self, engine_name, bodies, report_ref=False, *,
                                           header=None, footer=None, landscape=False,
                                           specific_paperformat_args=None, **kwargs):
        report = self._get_report(report_ref) if report_ref else self
        if engine_name != 'wkhtmltopdf' or len(report) != 1 or report.report_name != REPORT:
            return super()._run_pdf_engine_without_processing(
                engine_name, bodies, report_ref, header=header, footer=footer,
                landscape=landscape, specific_paperformat_args=specific_paperformat_args, **kwargs)
        bound = self.browse(report.id)
        bound._settlement_pdf_bound()
        try:
            # This report has fixed inline markup. Reject every resource-capable extension,
            # rather than attempting to parse all CSS or browser URL syntaxes.
            for body in bodies:
                root = html.fromstring(body, parser=html.HTMLParser(no_network=True))
                for node in root.iter():
                    if node.tag not in _TAGS:
                        raise ValueError('SETTLEMENT_PDF_RESOURCE_MARKUP')
                    for name, value in node.attrib.items():
                        if not ((name == 'style' and value in _STYLES)
                                or (name == 'class' and value == 'article page')
                                or (node.tag == 'meta' and name == 'charset' and value.lower() == 'utf-8')):
                            raise ValueError('SETTLEMENT_PDF_RESOURCE_ATTRIBUTE')
        except (ValueError, TypeError, etree.LxmlError) as primary:
            record_exception(primary, 'ydental_settlement.report', 'pdf.resources')
            raise UserError(self.env._('render_failed: Settlement PDF could not be generated.')) from None
        # Only this fixed inline report bypasses the generic engine's temporary
        # browser session/cookie-jar and header/footer creation. Reuse its paper
        # format arguments and ordinary report extension, never an HTTP client.
        args = bound._build_wkhtmltopdf_args(
            report.get_paperformat(), landscape,
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=kwargs.get('set_viewport_size', False))
        stack = ExitStack()
        had_primary = False
        primary_id = None
        try:
            try:
                directory = stack.enter_context(tempfile.TemporaryDirectory(prefix='ydental-settlement-pdf-'))
                paths = []
                for body in bodies:
                    source = stack.enter_context(tempfile.NamedTemporaryFile(
                        suffix='.html', prefix='body-', dir=directory))
                    source.write(body.encode('utf-8'))
                    source.flush()
                    paths.append(source.name)
                output = stack.enter_context(tempfile.NamedTemporaryFile(
                    suffix='.pdf', prefix='output-', dir=directory))
                bound._run_wkhtmltopdf([*args, *paths, output.name])
                return output.read()
            except BaseException as primary:
                had_primary = True
                primary_id = record_exception(primary, 'ydental_settlement.report', 'pdf.files')
                raise
            finally:
                try:
                    stack.close()
                except Exception as secondary:
                    if not had_primary:
                        raise
                    emit_event('renderer.cleanup_failed', component='ydental_settlement.report',
                               operation='pdf_files', stage='pdf.files.cleanup',
                               exception_type=type(secondary).__name__, root_event_id=primary_id,
                               outcome='CLEANUP_FAILED', severity='ERROR',
                               transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED')
        except OSError as primary:
            if not had_primary:
                record_exception(primary, 'ydental_settlement.report', 'pdf.files')
            raise UserError(self.env._('render_failed: Settlement PDF could not be generated.')) from None

    def _run_wkhtmltopdf(self, args):
        if not self._settlement_pdf_bound():
            return super()._run_wkhtmltopdf(args)
        try:
            matcher = shutil.which('fc-match')
            if not matcher:
                raise ValueError('SETTLEMENT_PDF_FONT_UNAVAILABLE')
            font = _run_owned([matcher, '-f', '%{family}', 'Noto Sans CJK SC'], 'font_match', 5, True)
            if font.returncode or 'Noto Sans CJK SC' not in font.stdout:
                raise ValueError('SETTLEMENT_PDF_FONT_UNAVAILABLE')
            cleaned = []
            index = 0
            while index < len(args):
                option = args[index]
                if option in _REMOVED_OPTIONS:
                    index += 1 + _REMOVED_OPTIONS[option]
                    continue
                if option.startswith(('--cookie', '--header-', '--footer-', '--custom-header')):
                    raise ValueError('SETTLEMENT_PDF_ENGINE_OPTION')
                cleaned.append(option)
                index += 1
            process = _run_owned([_wkhtml().bin, '--encoding', 'UTF-8', '--disable-javascript', *cleaned],
                                 'wkhtmltopdf', 30)
            if process.returncode:
                # All real negative exits were emitted before this public native error.
                # The independent parent must stop; no engine stderr is sent to core.
                raise UserError(self.env._('render_failed: Settlement PDF could not be generated.'))
            return process
        except (OSError, TypeError, ValueError, subprocess.TimeoutExpired) as primary:
            # A timed-out owned child already has its primary saved before cleanup.
            if not isinstance(primary, subprocess.TimeoutExpired):
                record_exception(primary, 'ydental_settlement.report', 'pdf.renderer')
            raise UserError(self.env._('render_failed: Settlement PDF could not be generated.')) from None
