from odoo import api, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalSettlementRecord(models.AbstractModel):
    _name = 'ydental.settlement.record'
    _description = 'Protected settlement record'

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_settlement_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the settlement service.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_settlement_mutation') is not _MUTATION:
            raise AccessError(self.env._('history_immutable: Settlement evidence cannot be overwritten.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Settlement evidence cannot be deleted.'))

    @api.model
    def _new(self, vals):
        return self.sudo().with_context(ydental_settlement_mutation=_MUTATION).create(vals)

    def _save(self, vals):
        return self.sudo().with_context(ydental_settlement_mutation=_MUTATION).write(vals)
