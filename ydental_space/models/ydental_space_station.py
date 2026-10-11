from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .geometry import check_geometry


class YDentalSpaceStation(models.Model):
    _name = 'ydental.space.station'
    _description = 'Stable clinic workstation'
    _inherit = ['ydental.space.version', 'ydental.access.source']

    ydental_store_id = fields.Many2one(string='Store')
    ydental_category = fields.Selection(default='space', readonly=True, string='Business category')
    ydental_floor_id = fields.Many2one('ydental.space.floor', required=True, ondelete='restrict', index=True, string='Floor')
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict', index=True, string='Area')
    ydental_queue_area_id = fields.Many2one('ydental.space.area', related='ydental_area_id.ydental_queue_area_id', related_sudo=False, string='Reporting area')
    ydental_kind = fields.Selection([('care', 'Treatment'), ('exam', 'Examination'),
                                     ('pharmacy', 'Pharmacy'), ('settlement', 'Settlement')], required=True, default='care', string='Workstation or artwork type')
    ydental_enabled = fields.Boolean(default=True, string='Enabled')
    ydental_callable = fields.Boolean(default=True, string='Can call patients')
    ydental_item_ids = fields.One2many('ydental.space.item', 'ydental_station_id', string='Placed artwork')
    ydental_add_capability_ids = fields.Many2many('ydental.access.capability', 'ydental_space_station_add_rel', string='Added capabilities')
    ydental_remove_capability_ids = fields.Many2many('ydental.access.capability', 'ydental_space_station_remove_rel', string='Removed capabilities')
    ydental_capability_ids = fields.Many2many('ydental.access.capability', compute='_compute_capabilities', string='Capabilities')
    ydental_x = fields.Float(default=40, string='X coordinate')
    ydental_y = fields.Float(default=60, string='Y coordinate')
    ydental_width = fields.Float(default=90, string='Width')
    ydental_height = fields.Float(default=70, string='Height')
    ydental_angle = fields.Float(string='Direction')

    @api.depends('ydental_item_ids.ydental_resource_id.ydental_capability_ids', 'ydental_item_ids.active',
                 'ydental_add_capability_ids', 'ydental_remove_capability_ids')
    def _compute_capabilities(self):
        for station in self:
            base = station.ydental_item_ids.filtered('active').ydental_resource_id.ydental_capability_ids
            station.ydental_capability_ids = (base | station.ydental_add_capability_ids) - station.ydental_remove_capability_ids

    @api.constrains('ydental_area_id', 'ydental_floor_id', 'ydental_store_id', 'ydental_category',
                    'active', 'ydental_kind', 'ydental_callable', 'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle')
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

    def write(self, vals):
        self.check_access('write')
        self._space_lock()
        previous = {station.id: (station.ydental_x, station.ydental_y, station.ydental_width,
                                station.ydental_height, station.ydental_angle) for station in self}
        result = super().write(vals)
        if {'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle'} & vals.keys():
            for station in self:
                x, y, width, height, angle = previous[station.id]
                scale_x = station.ydental_width / width
                scale_y = station.ydental_height / height
                for item in station.ydental_item_ids:
                    item.write({'ydental_x': station.ydental_x + (item.ydental_x - x) * scale_x,
                                'ydental_y': station.ydental_y + (item.ydental_y - y) * scale_y,
                                'ydental_width': item.ydental_width * scale_x,
                                'ydental_height': item.ydental_height * scale_y,
                                'ydental_angle': item.ydental_angle + station.ydental_angle - angle,
                                'ydental_version': item.ydental_version})
        return result
