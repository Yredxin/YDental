from odoo import models
from odoo.exceptions import AccessError, ValidationError


class YDentalPrintRequestService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _record_print_request_failure(self, request_audit_id, reason, simulated=True):
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 500 or simulated is not True:
            raise ValidationError(self.env._('invalid_failure: Record a bounded reason for the explicitly simulated device failure.'))
        access = self.env['ydental.access.service']
        store = access._scope().ydental_store_id
        event = self.env['ydental.access.audit'].sudo().browse(self._id(request_audit_id)).exists()
        if (not event or event.ydental_event != 'document.print_request' or event.ydental_user_id.id != self.env.uid
                or event.ydental_store_id != store or event.ydental_result != 'accepted'):
            raise AccessError(self.env._('access_denied: Select your own authorized original print request in this store.'))
        original_id = (event.ydental_after or {}).get('original_id')
        original = self.env['ydental.document.original'].sudo().browse(self._id(original_id)).exists()
        if not original:
            raise AccessError(self.env._('access_denied: The requested original is unavailable.'))
        _service, source, category = self._original_reauthorize(original)
        failure = access._audit('document.print_failure', category, source, store.id,
            source='document_original', reason=reason.strip(),
            after={'request_audit_id': event.id, 'original_id': original.id,
                'device_result': 'simulated_device_failure', 'paper_output': 'unknown', 'simulated': True})
        return {'audit_id': failure.id, 'request_audit_id': event.id,
            'device_result': 'simulated_device_failure', 'paper_output': 'unknown', 'simulated': True}

    def _original_handlers(self):
        return super()._original_handlers() | {'print_failure': self._record_print_request_failure}

    def _original_workbench(self):
        values = super()._original_workbench()
        access = self.env['ydental.access.service']
        store = access._scope().ydental_store_id
        available_ids = {row['id'] for row in values['originals']}
        requests = self.env['ydental.access.audit'].sudo().search([
            ('ydental_user_id', '=', self.env.uid), ('ydental_store_id', '=', store.id),
            ('ydental_event', '=', 'document.print_request'), ('ydental_result', '=', 'accepted')], limit=30)
        values['print_requests'] = [{'audit_id': row.id, 'original_id': row.ydental_after.get('original_id'),
            'requested_at': str(row.create_date)} for row in requests if row.ydental_after.get('original_id') in available_ids]
        return values
