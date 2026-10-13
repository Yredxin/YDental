from odoo import models


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _allow_demo_supply(self):
        # Keep real S03 capacity, eligibility and queue checks; only admit the
        # explicitly guarded synthetic demo policy in this S10 test database.
        from .. import pre_init_hook
        pre_init_hook(self.env)
        return True
