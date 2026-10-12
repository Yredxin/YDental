from odoo import fields, models


class YDentalTreatmentConsumption(models.Model):
    _name = 'ydental.treatment.consumption'
    _description = 'YDentalTreatmentConsumption'
    _inherit = 'ydental.treatment.record'

    ydental_event_id = fields.Many2one('ydental.treatment.event', required=True, ondelete='restrict', index=True)
    ydental_lot_id = fields.Many2one('stock.lot', required=True, ondelete='restrict')
    ydental_quantity = fields.Float(required=True, digits='Product Unit')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_kind = fields.Selection([('treatment', 'Material'), ('chairside', 'Chairside medicine'), ('prescription', 'Take-away medicine')], required=True)
    ydental_inventory_event_id = fields.Many2one('ydental.inventory.event', ondelete='restrict')
    _one_lot = models.Constraint('UNIQUE(ydental_event_id, ydental_lot_id)', 'An execution records each batch once.')
    _positive = models.Constraint('CHECK(ydental_quantity > 0)', 'Material quantity must be positive.')
