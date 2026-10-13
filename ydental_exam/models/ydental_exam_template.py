from odoo import fields, models


class YDentalExamTemplate(models.Model):
    _name = 'ydental.exam.template'
    _description = 'Reviewed demonstration template bound to one store catalog'
    _inherit = 'ydental.treatment.record'

    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, ondelete='restrict')
    ydental_code = fields.Selection([
        ('oral-demo-1', 'Oral demonstration'),
        ('periodontal-demo-1', 'Periodontal demonstration'),
        ('panorama-demo-1', 'Panorama demonstration'),
        ('cbct-demo-1', 'CBCT demonstration'),
    ], required=True)
    ydental_active = fields.Boolean(required=True, default=True)
    ydental_reason = fields.Char(required=True)

    _one_catalog = models.Constraint('UNIQUE(ydental_store_id, ydental_catalog_id)',
        'An examination catalog has one reviewed template per store.')
