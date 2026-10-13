from odoo import fields, models


class YDentalExamResult(models.Model):
    _name = 'ydental.exam.result'
    _description = 'Independent examination result for one frozen order line'
    _inherit = 'ydental.treatment.record'

    ydental_line_id = fields.Many2one('ydental.treatment.line', required=True, ondelete='restrict', index=True)
    ydental_execution_id = fields.Many2one('ydental.queue.execution', ondelete='restrict')
    ydental_event_id = fields.Many2one('ydental.treatment.event', ondelete='restrict')
    ydental_original_author_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_template_code = fields.Char(required=True)
    ydental_template_version = fields.Char(required=True)
    ydental_version = fields.Integer(required=True, default=0)
    ydental_findings = fields.Text()
    ydental_measurements = fields.Json()
    ydental_conclusion = fields.Text()
    ydental_current_editor_id = fields.Many2one('res.users', ondelete='restrict')
    ydental_edit_session_id = fields.Many2one('ydental.access.session', ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_edit_revision = fields.Integer(groups=fields.NO_ACCESS)
    ydental_edit_connection_hash = fields.Char(groups=fields.NO_ACCESS)
    ydental_edit_until = fields.Datetime(groups=fields.NO_ACCESS)
    ydental_started_at = fields.Datetime()
    ydental_completed_at = fields.Datetime()
    ydental_business_date = fields.Date()
    ydental_station_id = fields.Many2one('ydental.space.station', ondelete='restrict')
    state = fields.Selection([('draft', 'Draft'), ('started', 'Actual examination started'),
                              ('pending', 'Actual examination; result pending'),
                              ('partial', 'Partially completed'), ('confirmed', 'Result confirmed'),
                              ('aborted', 'Actual examination aborted')], required=True, default='draft')
    _one_line = models.Constraint('UNIQUE(ydental_line_id)', 'Each frozen examination line has one result history.')
