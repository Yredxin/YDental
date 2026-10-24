"""Default-off, one-source S12 synthetic client-timeout observation seam."""
import logging
import os
import re
import time

from odoo import models
from odoo.exceptions import UserError
from odoo.addons.ydental_print.models.ydental_print_service import REPORT, RenderScope


_logger = logging.getLogger(__name__)
PLAN = 'YD-S12-DOCUMENTS-REPORTS-V1'
TARGET = 'ydental_s11_synth_20261023_01'
DELAY_SECONDS = 3
PREFIX = 'YDENTAL_S12_RENDER_DELAY_'


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        scope = self.env.context.get('ydental_print_scope')
        enabled = os.environ.get(PREFIX + 'ENABLE') == PLAN
        if (enabled and self.env.cr.dbname == TARGET and report_ref == REPORT
                and isinstance(scope, RenderScope) and scope.original and scope.kind == 'clinical'):
            values = [os.environ.get(PREFIX + field, '') for field in ('ACTOR', 'SOURCE', 'VERSION')]
            if any(not re.fullmatch('[1-9][0-9]{0,8}', value) for value in values):
                raise UserError(self.env._('test_probe_invalid: The S12 synthetic delay requires explicit actor, source and version bindings.'))
            if tuple(map(int, values)) == (scope.actor, scope.source_id, scope.version):
                # Validate the same existing typed source/actor/scope before a
                # delay. The ordinary native renderer still runs unchanged.
                self.env['ydental.print.service']._validate_render_scope()
                _logger.info('S12_TIMEOUT_PROBE_PAUSE_START actor=%s source=%s version=%s seconds=%s',
                             scope.actor, scope.source_id, scope.version, DELAY_SECONDS)
                time.sleep(DELAY_SECONDS)
                _logger.info('S12_TIMEOUT_PROBE_PAUSE_END actor=%s source=%s version=%s',
                             scope.actor, scope.source_id, scope.version)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
