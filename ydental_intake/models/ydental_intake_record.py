from odoo import api, fields, models
from odoo.exceptions import AccessError


MUTATION = object()


class YDentalIntakeRecord(models.AbstractModel):
    _name = 'ydental.intake.record'
    _description = 'Controlled service intake record'
    _inherit = 'ydental.access.source'

    name = fields.Char(required=True)
    ydental_store_id = fields.Many2one(string='Store')
    ydental_category = fields.Selection(default='frontdesk', readonly=True, string='Business category')
    ydental_version = fields.Integer(default=1, required=True, readonly=True, string='Version')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        if self._name in ('ydental.intake.entitlement', 'ydental.intake.task', 'ydental.intake.arrival', 'ydental.intake.position', 'ydental.intake.referral'):
            store = self.env['ydental.intake.service']._business_read_access()
            return fields.Domain('ydental_store_id', '=', store.id)
        return super()._source_domain(operation)

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_intake_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled intake action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_intake_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use a controlled intake action.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Intake and pricing history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.with_context(ydental_intake_mutation=MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.with_context(ydental_intake_mutation=MUTATION).write(
                dict(values, ydental_version=record.ydental_version + 1))


class YDentalIntakeOperation(models.Model):
    _name = 'ydental.intake.operation'
    _description = 'Atomic intake action receipt'
    _inherit = 'ydental.intake.record'

    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_key = fields.Char(required=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_result = fields.Json(required=True)

    _key_unique = models.Constraint('UNIQUE(ydental_actor_id, ydental_key)', 'Action keys must be unique per actor.')

    def _source_domain(self, operation):
        return super()._source_domain(operation) & fields.Domain('ydental_actor_id', '=', self.env.uid)


class YDentalIntakeMutex(models.Model):
    _name = 'ydental.intake.mutex'
    _description = 'Intake repeatable-read serialization fence'

    ydental_revision = fields.Integer(default=0)
