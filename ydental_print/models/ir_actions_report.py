import json
import shutil
import subprocess

from odoo import models
from odoo.exceptions import AccessError, UserError

from odoo.addons.base_report_wkhtmltox.models.ir_actions_report import _wkhtml

from .ydental_print_service import REPORT, RenderScope


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def get_paperformat(self):
        scope = self.env.context.get('ydental_print_scope')
        if len(self) == 1 and self.report_name == REPORT and isinstance(scope, RenderScope) and scope.original:
            payload = self.env['ydental.print.service']._validate_render_scope()
            xmlid = 'ydental_print.ydental_pdf_80mm' if payload.get('paper') == '80mm' else 'ydental_print.ydental_pdf_a4'
            return self.env.ref(xmlid)
        return super().get_paperformat()

    def _get_report(self, report_ref):
        report = super()._get_report(report_ref)
        if report.report_name == REPORT:
            self.env['ydental.print.service']._validate_render_scope()
        return report

    def _get_layout(self):
        if len(self) == 1 and self.report_name == REPORT:
            return self.env.ref('ydental_print.ydental_pdf_layout')
        return super()._get_layout()

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None, set_viewport_size=False):
        result = super()._build_wkhtmltopdf_args(paperformat_id, landscape, specific_paperformat_args, set_viewport_size)
        if isinstance(self.env.context.get('ydental_print_scope'), RenderScope):
            result += ['--encoding', 'UTF-8', '--disable-javascript', '--footer-right', 'YDental | [page]/[topage]', '--footer-font-size', '8']
            scope = self.env.context['ydental_print_scope']
            if scope.original:
                payload = json.loads(scope.payload)
                footer = payload['footer_provenance']
                if payload.get('paper') == '80mm':
                    footer = '#%s / v%s' % (payload['source_id'], payload['version'])
                result += ['--footer-left', footer, '--footer-font-name', 'Noto Sans CJK SC']
        return result

    def _run_wkhtmltopdf(self, args):
        if not isinstance(self.env.context.get('ydental_print_scope'), RenderScope):
            return super()._run_wkhtmltopdf(args)
        self.env['ydental.print.service']._validate_render_scope()
        matcher = shutil.which('fc-match')
        if not matcher:
            raise UserError(self.env._('font_unavailable: A verified Chinese PDF font is required.'))
        try:
            font = subprocess.run([matcher, '-f', '%{family}', 'Noto Sans CJK SC'], capture_output=True, text=True, timeout=5, check=True)
            if 'Noto Sans CJK SC' not in font.stdout:
                raise UserError(self.env._('font_unavailable: A verified Chinese PDF font is required.'))
            # Inline-only controlled layout. Do not hand the engine a login
            # cookie or generated HTML header/footer URLs. No external assets.
            cleaned = []
            skip = False
            for arg in args:
                if skip:
                    skip = False
                elif arg in ('--cookie-jar', '--header-html', '--footer-html'):
                    skip = True
                else:
                    cleaned.append(arg)
            process = subprocess.run([_wkhtml().bin, *cleaned], capture_output=True, text=True, timeout=30, check=False)
        except subprocess.TimeoutExpired as error:
            raise UserError(self.env._('render_timeout: PDF generation exceeded its bounded deadline.')) from error
        except (OSError, subprocess.CalledProcessError) as error:
            raise UserError(self.env._('render_failed: The Chinese PDF engine is unavailable.')) from error
        if process.returncode:
            # Never expose engine stderr, file names or source HTML in responses.
            raise UserError(self.env._('render_failed: The PDF engine rejected this generation request.'))
        return process

