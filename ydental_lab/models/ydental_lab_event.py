from odoo import fields, models


class YDentalLabEvent(models.Model):
    _name = 'ydental.lab.event'
    _description = 'Immutable laboratory workflow event'
    _inherit = 'ydental.lab.record'
    _order = 'id desc'

    ydental_order_id = fields.Many2one('ydental.lab.order', required=True, ondelete='restrict', index=True)
    ydental_cooperation_id = fields.Many2one('ydental.lab.cooperation', ondelete='restrict')
    ydental_vendor_qualification_version = fields.Integer()
    ydental_vendor_qualification_valid_until = fields.Date()
    ydental_cooperation_active_at_dispatch = fields.Boolean()
    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_kind = fields.Selection([
        ('created', 'Created'), ('sent', 'Sent'), ('processing', 'Processing started'),
        ('received', 'Physical receipt'), ('putaway', 'Stock put away'),
        ('rework', 'Rework cycle opened'), ('rework_return', 'Returned to supplier'),
        ('additional_terms_approved', 'Additional service terms approved'),
        ('additional_service_performed', 'Additional service actually performed'),
        ('zero_supplier_cost_confirmed', 'No additional supplier cost confirmed'),
        ('cancelled', 'Cancelled'), ('exception', 'Exception closed'), ('fit', 'Actually fitted'),
        ('code_bound', 'Package code bound'),
    ], required=True)
    ydental_before_state = fields.Char()
    ydental_after_state = fields.Char(required=True)
    ydental_reason = fields.Char()
    ydental_inventory_event_id = fields.Many2one('ydental.inventory.event', ondelete='restrict')
    ydental_purchase_line_id = fields.Many2one('purchase.order.line', ondelete='restrict', groups='purchase.group_purchase_user')
    ydental_vendor_cost = fields.Monetary(currency_field='ydental_cost_currency_id', groups='purchase.group_purchase_user')
    ydental_cost_currency_id = fields.Many2one('res.currency', ondelete='restrict')
    ydental_purchase_cost_snapshot = fields.Json(groups='purchase.group_purchase_user', readonly=True)
    ydental_purchase_state_at_dispatch = fields.Selection(
        [('purchase', 'Purchase confirmed'), ('done', 'Purchase done')], groups='purchase.group_purchase_user', readonly=True)
    ydental_patient_fee_id = fields.Many2one('ydental.treatment.fee', ondelete='restrict')
    ydental_patient_fee_amount = fields.Monetary(currency_field='ydental_fee_currency_id', groups='ydental_access.ydental_group_manager')
    ydental_fee_currency_id = fields.Many2one('res.currency', ondelete='restrict')
    ydental_recorded_at = fields.Datetime(required=True)
