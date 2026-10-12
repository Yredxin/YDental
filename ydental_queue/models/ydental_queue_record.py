from odoo import api, fields, models
from odoo.exceptions import AccessError


MUTATION = object()


class YDentalQueueRecord(models.AbstractModel):
    _name = 'ydental.queue.record'
    _description = 'Controlled workstation queue source'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_version = fields.Integer(default=1, required=True, readonly=True)

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        store = self.env['ydental.intake.service']._business_read_access()
        return fields.Domain('ydental_store_id', '=', store.id)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_queue_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a workstation action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_queue_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a workstation action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Queue and execution history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_queue_mutation=MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.with_context(ydental_queue_mutation=MUTATION).write(
                dict(values, ydental_version=record.ydental_version + 1))
