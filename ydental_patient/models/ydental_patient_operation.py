from odoo import fields, models


class YDentalPatientOperation(models.Model):
    _name = 'ydental.patient.operation'
    _description = 'Patient action idempotency receipt'
    _inherit = 'ydental.patient.record'

    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict', string='Actor')
    ydental_key = fields.Char(required=True, string='Key')
    ydental_fingerprint = fields.Char(required=True, string='Fingerprint')
    ydental_result = fields.Json(required=True, string='Result')
    _key_unique = models.Constraint('UNIQUE(ydental_actor_id, ydental_key)', 'A patient action key is unique per actor.')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        store = self.env['ydental.patient.service']._access()
        return fields.Domain('ydental_actor_id', '=', self.env.uid) & fields.Domain('ydental_store_id', '=', store.id)
