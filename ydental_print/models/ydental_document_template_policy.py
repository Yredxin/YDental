from odoo import fields, models


class YDentalDocumentTemplate(models.Model):
    _inherit = 'ydental.document.template'

    accepted_previous_template_ids = fields.Json(default=list,
        help='Explicit same-store consent template versions accepted by this published policy. Empty means no prior version is accepted.')
