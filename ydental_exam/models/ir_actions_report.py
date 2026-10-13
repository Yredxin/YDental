from odoo import models


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
