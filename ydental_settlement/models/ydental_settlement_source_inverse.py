from odoo import fields, models


class YDentalTreatmentFee(models.Model):
    _inherit = 'ydental.treatment.fee'

    ydental_settlement_source_ids = fields.One2many(
        'ydental.settlement.source', 'ydental_fee_id', readonly=True)


class AccountMove(models.Model):
    _inherit = 'account.move'

    ydental_settlement_source_ids = fields.One2many(
        'ydental.settlement.source', 'ydental_invoice_id', readonly=True)
