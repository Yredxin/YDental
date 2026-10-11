from odoo import fields, models


class YDentalPatientMerge(models.Model):
    _name = 'ydental.patient.merge'
    _description = 'Store merge request and group identity verification'
    _inherit = 'ydental.patient.record'

    ydental_source_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', string='Source')
    ydental_target_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', string='Target')
    ydental_source_version = fields.Integer(required=True, string='Source version')
    ydental_target_version = fields.Integer(required=True, string='Target version')
    ydental_reason = fields.Char(required=True, string='Reason')
    ydental_requested_by_id = fields.Many2one('res.users', required=True, ondelete='restrict', string='Requested by')
    ydental_confirmed_by_id = fields.Many2one('res.users', ondelete='restrict', readonly=True, string='Confirmed by')
    ydental_decision_reason = fields.Char(readonly=True, string='Decision reason')
    ydental_conflicts = fields.Json(readonly=True, string='Conflicts')
    ydental_reference_counts = fields.Json(readonly=True, string='Reference counts')
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
