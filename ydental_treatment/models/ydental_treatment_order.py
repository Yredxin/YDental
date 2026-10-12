from odoo import fields, models


class YDentalTreatmentOrder(models.Model):
    _name = 'ydental.treatment.order'
    _description = 'YDentalTreatmentOrder'
    _inherit = 'ydental.treatment.record'

    ydental_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict', index=True)
    ydental_document_id = fields.Many2one('ydental.clinical.document', required=True, ondelete='restrict')
    ydental_document_version = fields.Integer(required=True)
    ydental_kind = fields.Selection([('exam', 'Examination order'), ('prescription', 'Take-away prescription')], required=True)
    ydental_purpose = fields.Char(required=True)
    ydental_version = fields.Integer(default=1, required=True)
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Issued, frozen'), ('done', 'All approved quantities dispensed')], required=True, default='draft')
