from odoo import fields, models


class YDentalIntakeCatalog(models.Model):
    _name = 'ydental.intake.catalog'
    _description = 'Group service catalog with native product identity'
    _inherit = 'ydental.intake.record'

    ydental_store_id = fields.Many2one(required=False)
    ydental_category = fields.Selection(default='price')
    active = fields.Boolean(default=True)
    ydental_code = fields.Char(required=True, index=True)
    ydental_kind = fields.Selection([
        ('care', 'Outpatient'), ('exam', 'Examination'), ('medicine', 'Medicine'),
        ('procedure', 'Procedure'), ('prosthesis', 'Prosthesis'),
    ], required=True)
    ydental_product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    ydental_capability_id = fields.Many2one('ydental.access.capability', required=True, ondelete='restrict')
    ydental_qualification = fields.Char(string='Required qualification')

    _code_unique = models.Constraint('UNIQUE(ydental_code)', 'Service codes must be unique across the group.')
    _product_unique = models.Constraint('UNIQUE(ydental_product_id)', 'A native product belongs to one service.')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        self.env['ydental.intake.service']._read_access(catalog=True)
        return fields.Domain.TRUE


class YDentalIntakeMapping(models.Model):
    _name = 'ydental.intake.mapping'
    _description = 'Store service reporting and execution mapping'
    _inherit = 'ydental.intake.record'

    ydental_category = fields.Selection(default='price')
    active = fields.Boolean(default=True)
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict', index=True)
    ydental_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')
    ydental_execution_area_id = fields.Many2one('ydental.space.area', required=True, ondelete='restrict')

    _mapping_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_catalog_id, ydental_area_id)', 'A store service area mapping must be unique.')

    def _source_domain(self, operation):
        if operation != 'read':
            return fields.Domain.FALSE
        store = self.env['ydental.intake.service']._read_access()
        return fields.Domain('ydental_store_id', '=', store.id)
