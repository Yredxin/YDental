from odoo import api, fields, models
from odoo.exceptions import AccessError


MUTATION = object()


class YDentalLabRecord(models.AbstractModel):
    _name = 'ydental.lab.record'
    _description = 'Controlled dental laboratory record'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_version = fields.Integer(default=1, required=True, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_lab_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use the dental laboratory workflow.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_lab_mutation') is not MUTATION:
            raise AccessError(self.env._('history_immutable: Use the dental laboratory workflow.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Laboratory history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_lab_mutation=MUTATION).create(values)

    def _save(self, values):
        self.ensure_one()
        return self.with_context(ydental_lab_mutation=MUTATION).write(
            dict(values, ydental_version=self.ydental_version + 1))
