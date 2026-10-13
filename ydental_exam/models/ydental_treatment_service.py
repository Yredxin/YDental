from odoo import models


class YDentalTreatmentService(models.AbstractModel):
    _inherit = 'ydental.treatment.service'

    def _issue(self, order_id, version, execution_id, lease_id, lease_token, document_id, document_version):
        response = super()._issue(order_id, version, execution_id, lease_id, lease_token,
                                  document_id, document_version)
        order = self._model('order').browse(response['order_id'])
        if order.ydental_kind == 'exam':
            today = self.env['ydental.supply.service']._date(order.ydental_store_id)
            self._model('line').browse(response['line_ids'])._save({'ydental_exam_validated_date': today})
        return response
