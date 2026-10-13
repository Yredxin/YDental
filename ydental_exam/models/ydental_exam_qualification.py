from odoo import fields, models


class YDentalExamQualification(models.Model):
    _name = 'ydental.exam.qualification'
    _description = 'Reviewed staff examination qualification'
    _inherit = 'ydental.treatment.record'

    ydental_user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    ydental_code = fields.Char(required=True)
    ydental_valid_from = fields.Datetime(required=True)
    ydental_valid_until = fields.Datetime(required=True)
    ydental_evidence = fields.Char(required=True)
    ydental_revoked = fields.Boolean(default=False)
    _unique = models.Constraint('UNIQUE(ydental_store_id, ydental_user_id, ydental_code, ydental_valid_from)',
                                'A reviewed qualification version is unique.')
    _dates = models.Constraint('CHECK(ydental_valid_until > ydental_valid_from)',
                               'Qualification expiry must follow its start.')
