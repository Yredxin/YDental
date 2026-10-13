from odoo import fields, models


class YDentalTreatmentMedicineLink(models.Model):
    _name = 'ydental.treatment.medicine.link'
    _description = 'Published store medicine SKU and service price provenance'
    _inherit = 'ydental.treatment.record'

    ydental_product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, ondelete='restrict')
    ydental_price_id = fields.Many2one('ydental.intake.price', required=True, ondelete='restrict')
    ydental_currency_id = fields.Many2one('res.currency', required=True, ondelete='restrict')
    ydental_product_name = fields.Char(required=True)
    ydental_evidence = fields.Char(required=True)
    ydental_published_at = fields.Datetime(required=True)
    ydental_policy = fields.Selection([('demo_confirmation', 'Demonstration; production pricing policy awaits approval')], required=True)
    state = fields.Selection([('published', 'Published')], required=True, default='published')

    _one_catalog = models.Constraint('UNIQUE(ydental_store_id, ydental_catalog_id)', 'A medicine fee catalog identifies one real SKU in a store.')
    _one_sku_unit = models.Constraint('UNIQUE(ydental_store_id, ydental_product_id, ydental_uom_id)', 'A medicine SKU and unit use one explicit store fee catalog.')
