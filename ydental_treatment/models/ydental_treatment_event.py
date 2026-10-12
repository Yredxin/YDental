from odoo import fields, models


class YDentalTreatmentEvent(models.Model):
    _name = 'ydental.treatment.event'
    _description = 'YDentalTreatmentEvent'
    _inherit = 'ydental.treatment.record'

    ydental_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict', index=True)
    ydental_document_id = fields.Many2one('ydental.clinical.document', ondelete='restrict')
    ydental_document_version = fields.Integer()
    ydental_order_line_id = fields.Many2one('ydental.treatment.line', ondelete='restrict', index=True)
    ydental_parent_id = fields.Many2one('ydental.treatment.event', ondelete='restrict')
    ydental_source = fields.Char(required=True, index=True)
    ydental_fingerprint = fields.Char(required=True)
    ydental_kind = fields.Selection([('treatment', 'Treatment'), ('chairside', 'Chairside medication'), ('prescription', 'Actual dispensing'), ('correction', 'Quantity correction')], required=True)
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict')
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_teeth = fields.Json()
    ydental_actual_at = fields.Datetime(required=True)
    ydental_business_date = fields.Date(required=True)
    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict')
    ydental_reason = fields.Char(required=True)
    ydental_already_performed = fields.Boolean()
    ydental_price_snapshot_id = fields.Many2one('ydental.intake.snapshot', ondelete='restrict')
    ydental_price_review_id = fields.Many2one('ydental.treatment.price.review', ondelete='restrict')
    ydental_pending_reason = fields.Char()
    state = fields.Selection([('pending', 'Fact awaiting reconciliation'), ('confirmed', 'Fee and stock confirmed')], required=True, default='pending')
    _source_once = models.Constraint('UNIQUE(ydental_store_id, ydental_source)', 'A clinical source executes once.')
    _quantity_nonzero = models.Constraint('CHECK(ydental_quantity <> 0)', 'An execution quantity cannot be zero.')
