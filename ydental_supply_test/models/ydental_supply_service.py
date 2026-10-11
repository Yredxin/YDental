import os
import re

from odoo import models
from odoo.exceptions import AccessError, UserError


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _allow_demo_supply(self):
        return bool(re.fullmatch(r'ydental_s03_test_[0-9]{14}_[a-f0-9]{8}', self.env.cr.dbname) and os.environ.get('YDENTAL_S03_RUN_DIR'))

    def _check_capacity_source(self, operation, payload):
        # Test-only server adapter. No public method/route or context bypass.
        # It can never authorize an installed business database.
        if not re.fullmatch(r'ydental_s03_test_[0-9]{14}_[a-f0-9]{8}', self.env.cr.dbname) or not os.environ.get('YDENTAL_S03_RUN_DIR'):
            raise AccessError(self.env._('Synthetic supply source refused outside isolated S03 validation.'))
        return self._access(write=True)

    def _check_queue_empty(self, business):
        # Deliberately fail closed unless the server-owned test fixture says empty.
        if not re.fullmatch(r'ydental_s03_test_[0-9]{14}_[a-f0-9]{8}', self.env.cr.dbname) or not os.environ.get('YDENTAL_S03_RUN_DIR'):
            return super()._check_queue_empty(business)
        if self.env['ir.config_parameter'].sudo().get_str('ydental_supply_test.queue') != 'synthetic_empty':
            raise UserError(self.env._('Synthetic waiting or calling remains.'))
        return None
