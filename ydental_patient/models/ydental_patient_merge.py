from odoo import fields, models


class YDentalPatientMerge(models.Model):
    _name = 'ydental.patient.merge'
    _description = 'Store merge request and group identity verification'
    _inherit = 'ydental.patient.record'

    ydental_source_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_target_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_source_version = fields.Integer(required=True)
    ydental_target_version = fields.Integer(required=True)
    ydental_reason = fields.Char(required=True)
    ydental_requested_by_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_confirmed_by_id = fields.Many2one('res.users', ondelete='restrict', readonly=True)
    ydental_decision_reason = fields.Char(readonly=True)
    ydental_conflicts = fields.Json(readonly=True)
    ydental_reference_counts = fields.Json(readonly=True)
    state = fields.Selection([
        ('requested', 'Awaiting group verification'), ('blocked', 'Resolve active business conflicts'),
        ('confirmed', 'Confirmed'), ('rejected', 'Rejected'),
    ], required=True, default='requested', readonly=True)

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        store = self.env['ydental.patient.service']._access()
        if self.env['ydental.access.service']._is_group_manager():
            return fields.Domain('ydental_store_id.company_id', 'in', self.env.user.company_ids.ids)
        return fields.Domain('ydental_store_id', '=', store.id)
