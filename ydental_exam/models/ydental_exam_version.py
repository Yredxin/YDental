from odoo import fields, models


class YDentalExamVersion(models.Model):
    _name = 'ydental.exam.version'
    _description = 'Immutable examination result text version'
    _inherit = 'ydental.treatment.record'

    ydental_result_id = fields.Many2one('ydental.exam.result', required=True, ondelete='restrict', index=True)
    ydental_number = fields.Integer(required=True)
    ydental_kind = fields.Selection([('draft', 'Draft save'), ('confirm', 'Result confirmation'),
                                     ('correction', 'Evidenced correction')], required=True)
    ydental_findings = fields.Text()
    ydental_measurements = fields.Json()
    ydental_conclusion = fields.Text()
    ydental_reason = fields.Char()
    ydental_recorded_at = fields.Datetime(required=True)
    ydental_previous_id = fields.Many2one('ydental.exam.version', ondelete='restrict')
    _number = models.Constraint('UNIQUE(ydental_result_id, ydental_number)', 'Result versions are strictly numbered.')
