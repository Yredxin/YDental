from odoo import models


class YDentalTreatmentService(models.AbstractModel):
    _inherit = 'ydental.treatment.service'

    def _bookkeep(self, event):
        if event.ydental_kind == 'exam':
            template = self.env['ydental.exam.template'].sudo().search([
                ('ydental_store_id', '=', event.ydental_store_id.id),
                ('ydental_catalog_id', '=', event.ydental_catalog_id.id),
                ('ydental_active', '=', True)], limit=1)
            if template.ydental_material_required and not self._model('consumption').search_count([
                    ('ydental_event_id', '=', event.id)]):
                if event.state != 'pending' or event.ydental_pending_reason != 'material_evidence_missing':
                    event._save({'state': 'pending', 'ydental_pending_reason': 'material_evidence_missing'})
                    self._audit('exam_material_evidence_pending', event,
                        {'template_id': template.id, 'event_id': event.id})
                return
        return super()._bookkeep(event)

    def _issue(self, order_id, version, execution_id, lease_id, lease_token, document_id, document_version):
        response = super()._issue(order_id, version, execution_id, lease_id, lease_token,
                                  document_id, document_version)
        order = self._model('order').browse(response['order_id'])
        if order.ydental_kind == 'exam':
            today = self.env['ydental.supply.service']._date(order.ydental_store_id)
            self._model('line').browse(response['line_ids'])._save({'ydental_exam_validated_date': today})
        return response
