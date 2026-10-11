from odoo import models
from odoo.exceptions import AccessError


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _get_report(self, report_ref):
        report = super()._get_report(report_ref)
        if report.report_name in (
            'ydental_base.ydental_sample_a4', 'ydental_base.ydental_sample_narrow',
        ) and (not self.env.user._is_internal() or not self.env.user.has_group(
            'ydental_base.ydental_base_group_user'
        )):
            # Report group visibility alone does not protect direct rendering routes.
            raise AccessError(self.env._('YDental application access is required.'))
        return report

    def _get_layout(self):
        if len(self) == 1 and self.report_name in (
            'ydental_base.ydental_sample_a4', 'ydental_base.ydental_sample_narrow',
        ):
            # Synthetic samples use inline styles; no asset HTTP callbacks are needed.
            return self.env.ref('ydental_base.ydental_sample_layout')
        return super()._get_layout()
