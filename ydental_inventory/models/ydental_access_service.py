from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {'inventory_batch': 'ydental.inventory.batch', 'inventory_config': 'ydental.inventory.config',
            'inventory_event': 'ydental.inventory.event', 'inventory_operation': 'ydental.inventory.operation'}
