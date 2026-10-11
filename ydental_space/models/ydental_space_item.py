from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .geometry import check_geometry


class YDentalSpaceItem(models.Model):
    _name = 'ydental.space.item'
    _description = 'Artwork placement on a floor'
    _inherit = ['ydental.space.version', 'ydental.access.source']

    ydental_category = fields.Selection(default='space', readonly=True)
    ydental_floor_id = fields.Many2one('ydental.space.floor', required=True, ondelete='restrict', index=True)
    ydental_resource_id = fields.Many2one('ydental.space.resource', required=True, ondelete='restrict', index=True)
    ydental_station_id = fields.Many2one('ydental.space.station', ondelete='restrict', index=True)
    ydental_x = fields.Float(default=40)
    ydental_y = fields.Float(default=60)
    ydental_width = fields.Float(default=60)
    ydental_height = fields.Float(default=50)
    ydental_angle = fields.Float()

    @api.constrains('ydental_floor_id', 'ydental_store_id', 'ydental_category', 'ydental_resource_id',
                    'ydental_station_id', 'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle')
    def _check_item(self):
        for item in self.sudo():
            check_geometry(item)
            if item.ydental_category != 'space' or item.ydental_store_id != item.ydental_floor_id.ydental_store_id or (
                item.ydental_resource_id.ydental_store_id and item.ydental_resource_id.ydental_store_id != item.ydental_store_id
            ) or item.ydental_station_id and item.ydental_station_id.ydental_floor_id != item.ydental_floor_id:
                raise ValidationError(self.env._('Artwork, workstation and floor must have compatible ownership.'))
            if not item.ydental_floor_id.active or not item.ydental_resource_id.active:
                raise ValidationError(self.env._('Select an active floor and artwork.'))

    def _check_space_change(self, values):
        super()._check_space_change(values)
        self.ydental_station_id._check_space_change({'resource_change': values})
