from odoo import fields, models
from odoo.exceptions import UserError


class YDentalSpaceStation(models.Model):
    _inherit = 'ydental.space.station'

    ydental_test_in_use = fields.Boolean(groups=fields.NO_ACCESS)

    def _check_space_change(self, values):
        super()._check_space_change(values)
        protected = {'ydental_area_id', 'active', 'ydental_enabled', 'ydental_kind',
                     'reporting_topology', 'resource_change', 'resource_definition', 'floor_change',
                     'ydental_add_capability_ids', 'ydental_remove_capability_ids'}
        if protected & values.keys() and self.sudo().filtered('ydental_test_in_use'):
            raise UserError(self.env._('Synthetic in-use protection: no task migration is permitted.'))
