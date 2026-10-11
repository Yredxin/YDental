import math

from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError


class YDentalSpaceFloor(models.Model):
    _name = 'ydental.space.floor'
    _description = 'Clinic floor'
    _inherit = ['ydental.space.version', 'ydental.access.source']

    ydental_category = fields.Selection(default='space', readonly=True)
    ydental_width = fields.Float(default=1000, required=True)
    ydental_height = fields.Float(default=700, required=True)
    ydental_area_ids = fields.One2many('ydental.space.area', 'ydental_floor_id')
    ydental_station_ids = fields.One2many('ydental.space.station', 'ydental_floor_id')
    ydental_item_ids = fields.One2many('ydental.space.item', 'ydental_floor_id')

    @api.constrains('ydental_width', 'ydental_height', 'ydental_category')
    def _check_dimensions(self):
        for floor in self:
            if floor.ydental_category != 'space' or not all(
                math.isfinite(value) and 0 < value <= 100000
                for value in (floor.ydental_width, floor.ydental_height)
            ):
                raise ValidationError(self.env._('A space floor needs finite positive dimensions.'))

    def _space_touch(self):
        # The floor's own write already increments its aggregate version.
        return

    def _check_space_change(self, values):
        super()._check_space_change(values)
        if values.get('active') is False and (self.ydental_area_ids or self.ydental_station_ids or self.ydental_item_ids):
            raise ValidationError(self.env._('Archive floor contents first.'))
        self.ydental_station_ids._check_space_change({'floor_change': values})

    def action_plan(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.client', 'tag': 'ydental_space.plan', 'params': {'floor_id': self.id}}

    def action_save_geometry(self, version, changes):
        self.ensure_one()
        self.check_access('write')
        self._space_lock()
        if type(version) is not int or version != self.ydental_version:
            raise UserError(self.env._('version_conflict: The floor changed. Reload before saving.'))
        if not isinstance(changes, list) or len(changes) > 500:
            raise ValidationError(self.env._('At most 500 geometry changes are allowed.'))
        models_by_kind = {'area': 'ydental.space.area', 'station': 'ydental.space.station', 'item': 'ydental.space.item'}
        keys = {'ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle', 'ydental_points'}
        with self.env.cr.savepoint():
            for change in changes:
                if not isinstance(change, dict) or set(change) != {'kind', 'id', 'values'} or change['kind'] not in models_by_kind:
                    raise ValidationError(self.env._('Invalid geometry change.'))
                values = change['values']
                if not isinstance(values, dict) or not set(values) <= keys:
                    raise ValidationError(self.env._('Only geometry can be saved through the plan.'))
                if 'ydental_points' in values and change['kind'] != 'area':
                    raise ValidationError(self.env._('Polygon points belong to areas.'))
                record = self.env[models_by_kind[change['kind']]].browse(change['id'])
                record.check_access('write')
                if record.ydental_floor_id != self:
                    raise ValidationError(self.env._('The object belongs to another floor.'))
                record.write(dict(values, ydental_version=record.ydental_version))
        return {'result': 'accepted', 'version': self.ydental_version}

    def action_snapshot(self):
        self.ensure_one()
        self.check_access('read')
        service = self.env['ydental.access.service']
        member = service._check('space')
        fields_geometry = ['name', 'active', 'ydental_version', 'ydental_x', 'ydental_y',
                           'ydental_width', 'ydental_height', 'ydental_angle']
        areas = self.ydental_area_ids.read(fields_geometry + ['parent_id', 'ydental_shape', 'ydental_points',
                    'ydental_reporting', 'ydental_queue_area_id', 'ydental_capability_ids', 'ydental_purpose'])
        stations = self.ydental_station_ids.read(fields_geometry + ['ydental_area_id', 'ydental_kind',
                    'ydental_queue_area_id', 'ydental_capability_ids', 'ydental_callable', 'ydental_enabled'])
        items = self.ydental_item_ids.read(fields_geometry + ['ydental_resource_id', 'ydental_station_id'])
        return {'floor': self.read(['name', 'ydental_store_id', 'ydental_version', 'ydental_width', 'ydental_height'])[0],
                'areas': areas, 'stations': stations, 'items': items,
                'writable': service._levels(member)['space'] == 'write',
                'capabilities': self.env['ydental.access.capability'].search_read([], ['name']),
                'resources': self.env['ydental.space.resource'].search_read([], ['name', 'ydental_kind']),
                'runtime': self.ydental_station_ids._get_runtime_states()}
