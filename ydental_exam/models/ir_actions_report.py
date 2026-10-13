import shutil
import subprocess

from odoo import models
from odoo.exceptions import UserError

from odoo.addons.base_report_wkhtmltox.models.ir_actions_report import _wkhtml

from .ydental_exam_service import ExamPdfScope


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_report(self, report_ref):
        report = super()._get_report(report_ref)
        if report.report_name == 'ydental_exam.ydental_exam_pdf':
            self.env['ydental.exam.service']._validate_pdf_scope()
        return report

    def _get_layout(self):
        if len(self) == 1 and self.report_name == 'ydental_exam.ydental_exam_pdf':
            return self.env.ref('ydental_print.ydental_pdf_layout')
        return super()._get_layout()

    def _build_wkhtmltopdf_args(self, paperformat_id, landscape, specific_paperformat_args=None, set_viewport_size=False):
        args = super()._build_wkhtmltopdf_args(paperformat_id, landscape, specific_paperformat_args, set_viewport_size)
        if isinstance(self.env.context.get('ydental_exam_pdf_scope'), ExamPdfScope):
            args += ['--encoding', 'UTF-8', '--disable-javascript']
        return args

    def _run_wkhtmltopdf(self, args):
        if not isinstance(self.env.context.get('ydental_exam_pdf_scope'), ExamPdfScope):
            return super()._run_wkhtmltopdf(args)
        self.env['ydental.exam.service']._validate_pdf_scope()
        matcher = shutil.which('fc-match')
        if not matcher:
            raise UserError(self.env._('font_unavailable: A verified Chinese PDF font is required.'))
        try:
            font = subprocess.run([matcher, '-f', '%{family}', 'Noto Sans CJK SC'], capture_output=True,
                                  text=True, timeout=5, check=True)
            if 'Noto Sans CJK SC' not in font.stdout:
                raise UserError(self.env._('font_unavailable: A verified Chinese PDF font is required.'))
            cleaned = []
            skip = False
            for arg in args:
                if skip:
                    skip = False
                elif arg in ('--cookie-jar', '--header-html', '--footer-html'):
                    skip = True
                else:
                    cleaned.append(arg)
            process = subprocess.run([_wkhtml().bin, *cleaned], capture_output=True,
                                     text=True, timeout=30, check=False)
        except subprocess.TimeoutExpired as error:
            raise UserError(self.env._('render_timeout: PDF generation exceeded its bounded deadline.')) from error
        except (OSError, subprocess.CalledProcessError) as error:
            raise UserError(self.env._('render_failed: The Chinese PDF engine is unavailable.')) from error
        if process.returncode:
            raise UserError(self.env._('render_failed: The PDF engine rejected this generation request.'))
        return process
