from odoo import fields, models


class YDentalPatientPolicy(models.Model):
    _name = 'ydental.patient.policy'
    _description = 'Store document policy prompt, no signature or document generation'
    _inherit = 'ydental.patient.record'

    ydental_code = fields.Char(required=True)
    ydental_body_reference = fields.Char()
    ydental_approved = fields.Boolean(readonly=True)
    ydental_approved_by_id = fields.Many2one('res.users', ondelete='restrict', readonly=True)
    ydental_required = fields.Boolean(default=True)
    active = fields.Boolean(default=True)
    _code_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_code)', 'Store policy codes must be unique.')

    def _source_domain(self, operation):
        if operation == 'read':
            store = self.env['ydental.patient.service']._access()
            return fields.Domain('ydental_store_id', '=', store.id)
        return fields.Domain.FALSE
