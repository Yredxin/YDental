from odoo import fields, models

from .constants import CATEGORIES, LEVELS


class YDentalAccessGrant(models.Model):
    _name = 'ydental.access.grant'
    _description = 'YDental expanded business permission'

    ydental_membership_id = fields.Many2one(
        'ydental.access.membership', required=True, ondelete='restrict', index=True,
    )
    ydental_category = fields.Selection(CATEGORIES, required=True)
    ydental_level = fields.Selection(LEVELS, required=True, default='none')

    _membership_category_unique = models.Constraint(
        'UNIQUE(ydental_membership_id, ydental_category)', 'One level per membership and category is required.',
    )
