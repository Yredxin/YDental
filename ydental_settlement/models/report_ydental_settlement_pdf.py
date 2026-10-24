from odoo import fields, models
from odoo.exceptions import AccessError
from odoo.tools.misc import formatLang


class YDentalSettlementPdf(models.AbstractModel):
    _name = 'report.ydental_settlement.ydental_settlement_pdf'
    _description = 'Bound synthetic settlement, receipt and refund PDF'

    def _get_report_values(self, docids, data=None):
        payload = self.env['ydental.settlement.service']._validate_pdf_scope()
        if docids != [payload['source_id']] or data and set(data) - {'report_type', 'debug'} or data and data.get('debug', False) is not False:
            raise AccessError(self.env._('access_denied: Arbitrary settlement report arguments are unavailable.'))
        currency = self.env['ydental.access.service']._scope().ydental_store_id.company_id.currency_id
        payload = dict(payload, generated_at=str(fields.Datetime.now()), layout_version='YD-S13-SETTLEMENT-2')
        amount_fields = {'discount', 'total', 'received', 'residual', 'refunded', 'pending', 'net', 'requested'}
        for name in amount_fields & payload.keys():
            payload[name] = formatLang(self.env, payload[name], digits=currency.decimal_places)
        for name in ('lines', 'allocations'):
            if name in payload:
                payload[name] = [dict(row, amount=formatLang(self.env, row['amount'], digits=currency.decimal_places))
                    for row in payload[name]]
        if 'state' in payload:
            payload['state_label'] = dict(self.env['ydental.settlement.refund']._fields['ydental_state']._description_selection(self.env))[payload['state']]
        if payload.get('channel'):
            payload['channel'] = dict(self.env['ydental.settlement.payment']._fields['ydental_channel']._description_selection(self.env)).get(payload['channel'], payload['channel'])
        if payload.get('refund_channel'):
            payload['refund_channel'] = dict(self.env['ydental.settlement.refund']._fields['ydental_refund_channel']._description_selection(self.env))[payload['refund_channel']]
        return {'doc_ids': docids, 'doc_model': 'ydental.settlement.receipt', 'docs': [], 'p': payload}
