from odoo import models


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _check_ydental_source_report(self, report_ref, docids):
        report = self._get_report(report_ref)
        service = self.env['ydental.access.service']
        if not self.env.su and report.model in service._get_sources().values():
            records = self.env[report.model].browse(docids or [])
            records.check_access('read')
            session = service._scope()
            for record in records:
                service._audit('source.report_render', record.sudo().ydental_category, record,
                               session.ydental_store_id.id, source='native_report')

    def _render_qweb_html(self, report_ref, docids, data=None):
        self._check_ydental_source_report(report_ref, docids)
        return super()._render_qweb_html(report_ref, docids, data)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        # Guard cached attachments too, before the HTML renderer can be skipped.
        self._check_ydental_source_report(report_ref, res_ids)
        return super()._render_qweb_pdf(report_ref, res_ids, data)
