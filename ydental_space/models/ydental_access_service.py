from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {
            'space_floor': 'ydental.space.floor', 'space_area': 'ydental.space.area',
            'space_station': 'ydental.space.station', 'space_item': 'ydental.space.item',
            'space_resource': 'ydental.space.resource',
        }
