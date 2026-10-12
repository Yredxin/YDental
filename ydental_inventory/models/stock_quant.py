from odoo import api, fields, models


class StockQuant(models.Model):
    _name = 'stock.quant'
    _inherit = ['stock.quant', 'ydental.inventory.native']

    ydental_store_id = fields.Many2one('ydental.access.store', readonly=True, ondelete='restrict', index=True, string='Inventory store')

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [dict(v) for v in vals_list]
        for vals in vals_list:
            if vals.get('location_id'):
                vals['ydental_store_id'] = self.env['stock.location'].sudo().browse(vals['location_id']).ydental_store_id.id
        return super().create(vals_list)
