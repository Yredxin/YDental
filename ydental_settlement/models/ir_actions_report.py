"""Observe the native renderer without replacing its report or engine behavior."""
from odoo import models
from odoo.exceptions import AccessError
from odoo.addons.ydental_access.diagnostics import emit_event, record_exception

from .ydental_settlement_service import SettlementPdfScope


REPORT = 'ydental_settlement.ydental_settlement_pdf'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _run_pdf_engine_without_processing(self, engine_name, bodies, report_ref=False, **kwargs):
        bound = self
        if engine_name == 'wkhtmltopdf':
            report = self._get_report(report_ref) if report_ref else self
            if len(report) == 1 and report.report_name == REPORT:
                if type(self.env.context.get('ydental_settlement_pdf_scope')) is not SettlementPdfScope:
                    raise AccessError(self.env._('access_denied: A bound settlement export request is required.'))
                self.env['ydental.settlement.service']._validate_pdf_scope()
                # Native callers pass an empty report set here. Keep their original
                # environment, not the sudo environment returned by _get_report.
                bound = self.browse(report.id)
        return super(IrActionsReport, bound)._run_pdf_engine_without_processing(
            engine_name, bodies, report_ref, **kwargs)

    def _run_wkhtmltopdf(self, args):
        if len(self) != 1 or self.report_name != REPORT:
            return super()._run_wkhtmltopdf(args)
        if type(self.env.context.get('ydental_settlement_pdf_scope')) is not SettlementPdfScope:
            raise AccessError(self.env._('access_denied: A bound settlement export request is required.'))
        self.env['ydental.settlement.service']._validate_pdf_scope()
        try:
            result = super()._run_wkhtmltopdf(args)
        except BaseException as primary:
            primary_id = record_exception(primary, 'ydental_settlement.report', 'pdf.renderer', investigate=True)
            emit_event('renderer.error', component='ydental_settlement.report', stage='pdf.renderer',
                       outcome='UNKNOWN', root_event_id=primary_id, severity='ERROR',
                       transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED')
            raise
        observation_id = None
        try:
            code = result.returncode
        except Exception as observation_error:
            observation_id = record_exception(observation_error, 'ydental_settlement.report',
                                              'evidence.renderer', investigate=True)
            code = None
        known = type(code) is int
        emit_event('renderer.exit', component='ydental_settlement.report', stage='pdf.renderer',
                   root_event_id=observation_id,
                   renderer_exit_code=code if known and code >= 0 else None,
                   renderer_signal=-code if known and code < 0 else None,
                   outcome=('NATIVE_CRASH' if known and code < 0 else 'NONZERO_NOT_NATIVE'
                            if known and code > 0 else 'EXITED' if known else 'UNKNOWN'),
                   severity='CRITICAL' if known and code < 0 else 'INFO',
                   transaction_phase='NOT_OBSERVED', commit_observation='NOT_OBSERVED')
        # CompletedProcess exposes no child PID or reap proof. Do not invent either.
        return result
