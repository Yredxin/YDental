from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL

from .geometry import capability_commands


class YDentalSpaceVersion(models.AbstractModel):
    _name = 'ydental.space.version'
    _description = 'Versioned clinic space configuration'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    ydental_version = fields.Integer(default=1, readonly=True, copy=False, required=True, string='Content version')

    def _space_authorize(self, operation):
        self.check_access(operation)

    def _space_floors(self):
        return self if self._name == 'ydental.space.floor' else self.mapped('ydental_floor_id')

    def _space_lock(self):
        # Configuration is low-frequency. One transaction lock also protects
        # the reverse-reference set while shared artwork is edited or placed.
        # Always authorize (and lock the login scope) before acquiring this lock.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [26002])
        floors = self._space_floors().sudo().sorted('id')
        if floors:
            self.env.cr.execute('SELECT id FROM ydental_space_floor WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(floors.ids)])
            floors.invalidate_recordset()
        if self:
            self.env.cr.execute(SQL('SELECT id FROM %s WHERE id IN %s ORDER BY id FOR UPDATE',
                                    SQL.identifier(self._table), tuple(self.ids)))
            self.invalidate_recordset()
        return floors

    def _space_touch(self):
        for floor in self._space_floors().sudo():
            # Parent version is derived metadata; auth and locks precede this call.
            super(YDentalSpaceVersion, floor).write({'ydental_version': floor.ydental_version + 1})

    def _check_space_change(self, values):
        """S03/S06 override under the same floor lock, then call super.

        No schedule, queue or execution model is queried by this lower layer.
        The hook runs before any change, including name/geometry and archiving.
        """

    @api.model_create_multi
    def create(self, vals_list):
        self._space_authorize('create')
        self._space_lock()
        vals_list = [dict(values) for values in vals_list]
        for values in vals_list:
            if 'ydental_category' in self._fields:
                if values.get('ydental_category', 'space') != 'space':
                    raise AccessError(self.env._('access_denied: Space configuration requires space authorization.'))
                values['ydental_category'] = 'space'
            if 'ydental_version' in values and values['ydental_version'] != 1:
                raise UserError(self.env._('version_conflict: New configuration starts at version one.'))
            for key in ('ydental_add_capability_ids', 'ydental_remove_capability_ids', 'ydental_capability_ids'):
                if key in values:
                    capability_commands(self.env, values[key])
        if 'ydental_floor_id' in self._fields:
            floors = self.env['ydental.space.floor'].browse([values.get('ydental_floor_id') for values in vals_list])
            floors.check_access('write')
            floors._space_lock()
        records = super().create(vals_list)
        records._space_lock()
        records._check_space_change({'create': True})
        records._space_touch()
        records._space_audit('space.create')
        return records

    def write(self, vals):
        self._space_authorize('write')
        self._space_lock()
        expected = vals.get('ydental_version')
        if type(expected) is not int or any(record.ydental_version != expected for record in self):
            raise UserError(self.env._('version_conflict: Configuration changed. Reload before saving.'))
        if {'ydental_store_id', 'ydental_category', 'ydental_floor_id'} & vals.keys():
            raise AccessError(self.env._('access_denied: Space ownership is immutable.'))
        for key in ('ydental_add_capability_ids', 'ydental_remove_capability_ids', 'ydental_capability_ids'):
            if key in vals:
                capability_commands(self.env, vals[key])
        self._check_space_change(vals)
        before = {record.id: record._space_snapshot() for record in self}
        result = super().write(dict(vals, ydental_version=expected + 1))
        self._space_touch()
        self._space_audit('space.modify', before)
        return result

    def _space_snapshot(self):
        self.ensure_one()
        values = {'name': self.name, 'active': self.active, 'version': self.ydental_version}
        for key in ('ydental_x', 'ydental_y', 'ydental_width', 'ydental_height', 'ydental_angle',
                    'ydental_reporting', 'ydental_callable', 'ydental_enabled', 'ydental_points'):
            if key in self._fields:
                values[key] = self[key]
        for key in ('parent_id', 'ydental_area_id', 'ydental_floor_id', 'ydental_resource_id',
                    'ydental_station_id', 'ydental_capability_ids', 'ydental_add_capability_ids',
                    'ydental_remove_capability_ids'):
            if key in self._fields:
                values[key] = self[key].ids
        return values

    def _space_audit(self, event, before=None):
        if not self.env.su:
            service = self.env['ydental.access.service']
            self.env['ydental.access.audit'].sudo().create([
                service._audit_values(event, 'space', record, record.ydental_store_id.id,
                                      before=(before or {}).get(record.id), after=record._space_snapshot(),
                                      source='space_model') for record in self
            ])

    def unlink(self):
        raise AccessError(self.env._('Archive space configuration to preserve stable references.'))

    def action_archive(self):
        self.ensure_one()
        return self.write({'active': False, 'ydental_version': self.ydental_version})

    def action_unarchive(self):
        self.ensure_one()
        return self.write({'active': True, 'ydental_version': self.ydental_version})
