from odoo import models


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _allow_demo_supply(self):
        # Only the explicitly isolated S03 demo capacity input is adapted.
        # Clinical documents, save hooks and lock authority are the real product.
        from .. import pre_init_hook
        pre_init_hook(self.env)
        return True
