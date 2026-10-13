from odoo import api, fields, models
from odoo.exceptions import AccessError


PROFILE_GUARD = object()
PROFILE_FIELDS = {'ydental_exam_family', 'ydental_exam_review_actor_id',
                  'ydental_exam_reviewed_at', 'ydental_exam_review_reason'}


class YDentalAccessCapability(models.Model):
    _inherit = 'ydental.access.capability'

    ydental_exam_family = fields.Selection([
        ('oral', 'Oral examination'), ('periodontal', 'Periodontal examination'),
        ('panorama', 'Panorama'), ('cbct', 'CBCT'),
    ], groups=fields.NO_ACCESS)
    ydental_exam_review_actor_id = fields.Many2one('res.users', ondelete='restrict', groups=fields.NO_ACCESS)
    ydental_exam_reviewed_at = fields.Datetime(groups=fields.NO_ACCESS)
    ydental_exam_review_reason = fields.Char(groups=fields.NO_ACCESS)

    @api.model_create_multi
    def create(self, vals_list):
        if any(PROFILE_FIELDS & vals.keys() for vals in vals_list):
            raise AccessError(self.env._('access_denied: Review examination capability through its controlled action.'))
        return super().create(vals_list)

    def write(self, vals):
        if PROFILE_FIELDS & vals.keys() and self.env.context.get('ydental_exam_profile_guard') is not PROFILE_GUARD:
            raise AccessError(self.env._('access_denied: Review examination capability through its controlled action.'))
        return super().write(vals)
