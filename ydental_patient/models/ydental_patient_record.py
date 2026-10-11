from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalPatientRecord(models.AbstractModel):
    _name = 'ydental.patient.record'
    _description = 'Controlled patient identity record'
    _inherit = 'ydental.access.source'
    _ydental_global = False

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='patient', readonly=True, string='Business category')
    ydental_version = fields.Integer(required=True, default=1, readonly=True, string='Version')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        if self._ydental_global:
            self.env['ydental.patient.service']._access()
            return fields.Domain.TRUE
        return super()._source_domain(operation)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_patient_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled patient action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_patient_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled patient action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Patient identity history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_patient_mutation=_MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.with_context(ydental_patient_mutation=_MUTATION).write(
                dict(values, ydental_version=record.ydental_version + 1))
