import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError

from .geometry import check_geometry


class YDentalSpaceArea(models.Model):
    _name = 'ydental.space.area'
    _description = 'Clinic reporting and display area'
    _inherit = ['ydental.space.version', 'ydental.access.source']

    ydental_category = fields.Selection(default='space', readonly=True)
    ydental_floor_id = fields.Many2one('ydental.space.floor', required=True, ondelete='restrict', index=True)
    parent_id = fields.Many2one('ydental.space.area', ondelete='restrict', index=True)
    ydental_child_ids = fields.One2many('ydental.space.area', 'parent_id')
    ydental_station_ids = fields.One2many('ydental.space.station', 'ydental_area_id')
    ydental_purpose = fields.Selection([
        ('care', 'Treatment'), ('exam', 'Examination'), ('pharmacy', 'Pharmacy'),
        ('settlement', 'Settlement'), ('waiting', 'Waiting'), ('toilet', 'Toilet'),
        ('sterilization', 'Sterilization'), ('other', 'Other'),
    ], default='care', required=True)
    ydental_reporting = fields.Boolean(string='Separate reporting queue')
    ydental_prefix = fields.Char(string='Queue display prefix')
    ydental_missed_limit = fields.Integer(string='Missed calls parameter', help='Not approved for production until S06 publication.')
    ydental_queue_area_id = fields.Many2one('ydental.space.area', compute='_compute_queue_area', recursive=True)
    ydental_capability_ids = fields.Many2many('ydental.access.capability', compute='_compute_capabilities')
    ydental_shape = fields.Selection([('rect', 'Rectangle'), ('polygon', 'Polygon')], default='rect', required=True)
    ydental_points = fields.Json(default=list)
    ydental_x = fields.Float(default=20)
    ydental_y = fields.Float(default=20)
    ydental_width = fields.Float(default=300)
    ydental_height = fields.Float(default=200)
    ydental_angle = fields.Float()

    @api.depends('ydental_reporting', 'parent_id.ydental_queue_area_id')
    def _compute_queue_area(self):
        for area in self:
            area.ydental_queue_area_id = area if area.ydental_reporting else area.parent_id.ydental_queue_area_id

    @api.depends('ydental_station_ids.ydental_capability_ids', 'ydental_station_ids.active',
                 'ydental_station_ids.ydental_enabled', 'ydental_child_ids.ydental_capability_ids')
    def _compute_capabilities(self):
        for area in self:
            stations = area.ydental_station_ids.filtered(lambda station: station.active and station.ydental_enabled)
            area.ydental_capability_ids = stations.ydental_capability_ids | area.ydental_child_ids.ydental_capability_ids

    @api.constrains('parent_id', 'ydental_floor_id', 'ydental_store_id', 'ydental_category',
                    'ydental_reporting', 'ydental_purpose', 'ydental_missed_limit', 'active',
                    'ydental_shape', 'ydental_points', 'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle')
    def _check_area(self):
        for area in self.sudo():
            check_geometry(area)
            if area.ydental_category != 'space' or area.ydental_store_id != area.ydental_floor_id.ydental_store_id:
                raise ValidationError(self.env._('Area and floor must belong to the same store.'))
            ancestors = {area.id}
            parent = area.parent_id
            while parent:
                if parent.id in ancestors or parent.ydental_floor_id != area.ydental_floor_id:
                    raise ValidationError(self.env._('Area parents must form an acyclic tree on one floor.'))
                ancestors.add(parent.id)
                parent = parent.parent_id
            if area.ydental_reporting and area.ydental_purpose not in ('care', 'exam', 'pharmacy'):
                raise ValidationError(self.env._('This display-only area cannot accept reporting.'))
            if area.ydental_missed_limit < 0:
                raise ValidationError(self.env._('Missed calls parameter cannot be negative.'))
            if not area.active and (area.ydental_child_ids or area.ydental_station_ids):
                raise ValidationError(self.env._('Archive child areas and workstations first.'))
            if not area.ydental_floor_id.active or area.parent_id and not area.parent_id.active:
                raise ValidationError(self.env._('Select an active floor and parent area.'))
            if area.ydental_shape == 'polygon':
                points = area.ydental_points
                if not isinstance(points, list) or not 3 <= len(points) <= 100 or any(
                    not isinstance(point, list) or len(point) != 2 or any(
                        type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 100000
                        for value in point) for point in points
                ):
                    raise ValidationError(self.env._('A polygon needs 3 to 100 finite coordinate pairs.'))

    def _check_space_change(self, values):
        super()._check_space_change(values)
        if {'parent_id', 'ydental_reporting', 'active', 'ydental_purpose'} & values.keys():
            descendants = self
            frontier = self
            while frontier:
                frontier = frontier.ydental_child_ids
                descendants |= frontier
            descendants.ydental_station_ids._check_space_change({'reporting_topology': values})
