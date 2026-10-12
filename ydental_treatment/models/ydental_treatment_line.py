from odoo import fields, models


class YDentalTreatmentLine(models.Model):
    _name = 'ydental.treatment.line'
    _description = 'YDentalTreatmentLine'
    _inherit = 'ydental.treatment.record'

    ydental_order_id = fields.Many2one('ydental.treatment.order', required=True, ondelete='restrict', index=True)
    ydental_mapping_id = fields.Many2one('ydental.intake.mapping', required=True, ondelete='restrict')
    ydental_product_id = fields.Many2one('product.product', ondelete='restrict')
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_specification = fields.Char()
    ydental_usage = fields.Char()
    ydental_frequency = fields.Char()
    ydental_course = fields.Char()
    ydental_reason = fields.Char()
    ydental_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    state = fields.Selection([('draft', 'Draft'), ('issued', 'Awaiting execution'), ('cancelled', 'Unperformed item cancelled'), ('started', 'Started by examination service'), ('done', 'Execution completed')], required=True, default='draft')
    _positive = models.Constraint('CHECK(ydental_quantity > 0)', 'An order quantity must be positive.')
