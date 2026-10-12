from odoo import api, fields, models
from odoo.exceptions import AccessError

_MUTATION = object()


class YDentalTreatmentRecord(models.AbstractModel):
    _name = 'ydental.treatment.record'
    _description = 'Protected clinical execution source'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_patient_id = fields.Many2one('ydental.patient', ondelete='restrict', index=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        # These economic/order sources are scoped to this store. Shared clinical
        # text is available through S08-A's purpose-audited historical reader.
        access = self.env['ydental.access.service']
        store = access._scope().ydental_store_id
        return super()._source_domain(operation) & fields.Domain('ydental_store_id', '=', store.id)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_treatment_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the controlled treatment action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_treatment_mutation') is not _MUTATION:
            raise AccessError(self.env._('history_immutable: Clinical sources cannot be overwritten.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Clinical source history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_treatment_mutation=_MUTATION).create(values)

    def _save(self, values):
        return self.with_context(ydental_treatment_mutation=_MUTATION).write(values)
