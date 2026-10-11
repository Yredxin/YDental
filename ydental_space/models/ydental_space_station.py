from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .geometry import check_geometry


class YDentalSpaceStation(models.Model):
    _name = 'ydental.space.station'
    _description = 'Stable clinic workstation'
    _inherit = ['ydental.space.version', 'ydental.access.source']

    ydental_category = fields.Selection(default='space', readonly=True)
    ydental_floor_id = fields.Many2one('ydental.space.floor', required=True, ondelete='restrict', index=True)
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict', index=True)
    ydental_queue_area_id = fields.Many2one('ydental.space.area', related='ydental_area_id.ydental_queue_area_id', related_sudo=False)
    ydental_kind = fields.Selection([('care', 'Treatment'), ('exam', 'Examination'),
                                     ('pharmacy', 'Pharmacy'), ('settlement', 'Settlement')], required=True, default='care')
    ydental_enabled = fields.Boolean(default=True)
    ydental_callable = fields.Boolean(default=True)
    ydental_item_ids = fields.One2many('ydental.space.item', 'ydental_station_id')
    ydental_add_capability_ids = fields.Many2many('ydental.access.capability', 'ydental_space_station_add_rel')
    ydental_remove_capability_ids = fields.Many2many('ydental.access.capability', 'ydental_space_station_remove_rel')
    ydental_capability_ids = fields.Many2many('ydental.access.capability', compute='_compute_capabilities')
    ydental_x = fields.Float(default=40)
    ydental_y = fields.Float(default=60)
    ydental_width = fields.Float(default=90)
    ydental_height = fields.Float(default=70)
    ydental_angle = fields.Float()

    @api.depends('ydental_item_ids.ydental_resource_id.ydental_capability_ids', 'ydental_item_ids.active',
                 'ydental_add_capability_ids', 'ydental_remove_capability_ids')
    def _compute_capabilities(self):
        for station in self:
            base = station.ydental_item_ids.filtered('active').ydental_resource_id.ydental_capability_ids
            station.ydental_capability_ids = (base | station.ydental_add_capability_ids) - station.ydental_remove_capability_ids

    @api.constrains('ydental_area_id', 'ydental_floor_id', 'ydental_store_id', 'ydental_category',
                    'ydental_kind', 'ydental_callable', 'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle')
    def _check_station(self):
        for station in self.sudo():
            check_geometry(station)
            if station.ydental_category != 'space' or station.ydental_store_id != station.ydental_floor_id.ydental_store_id or (
                station.ydental_area_id.ydental_floor_id != station.ydental_floor_id
            ):
                raise ValidationError(self.env._('A workstation must belong to one store and floor.'))
            if not station.ydental_area_id.active or not station.ydental_floor_id.active:
                raise ValidationError(self.env._('Select an active floor and area.'))
            if station.ydental_kind == 'settlement' and station.ydental_callable:
                raise ValidationError(self.env._('Settlement workstations do not call patients.'))

    def _get_runtime_states(self):
        """S06 supplies authoritative states; absent integration stays explicit."""
        self.check_access('read')
        return [{'id': station.id, 'state': 'not_connected',
                 'label': self.env._('Execution status not connected')} for station in self]
