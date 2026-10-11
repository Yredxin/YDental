from odoo import fields, models


class YDentalAccessMembership(models.Model):
    _name = 'ydental.access.membership'
    _description = 'YDental store employment'

    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict', index=True)
    ydental_employee_id = fields.Many2one('hr.employee', required=True, ondelete='restrict')
    ydental_is_manager = fields.Boolean(default=False)
    active = fields.Boolean(default=True)

    _user_store_unique = models.Constraint(
        'UNIQUE(ydental_user_id, ydental_store_id)', 'One membership per account and store is required.',
    )
