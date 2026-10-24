import base64
import hashlib

from odoo import models
from odoo.exceptions import AccessError, UserError

from odoo.addons.ydental_print.models.ydental_print_service import digest, normalized


class YDentalPrintService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_authorize(self, kind, source_id, version, purpose=None):
        if kind != 'lab_label':
            return super()._original_authorize(kind, source_id, version, purpose)
        if purpose or type(version) is not int or version < 1:
            raise AccessError(self.env._('source_required: Select a current laboratory label source in this store.'))
        lab = self.env['ydental.lab.service']
        store = lab._access()
        order = lab._get_order(self._id(source_id), store)
        self.env['ydental.lab.order'].browse(order.id).check_access('read')
        self.env['ydental.patient.service']._current_relation(order.ydental_patient_id, store)
        if order.ydental_version != version:
            raise UserError(self.env._('version_conflict: Review the current laboratory order version.'))
        return self, order, False, 'medical'

    def _original_source(self, kind, source_id, version, purpose=None):
        if kind != 'lab_label':
            return super()._original_source(kind, source_id, version, purpose)
        service, order, _selected, category = self._original_authorize(kind, source_id, version, purpose)
        # Native local barcode rendering encodes only the existing package
        # identification string, never a patient record URL or bearer token.
        barcode = self.env['ir.actions.report'].barcode('QR', order.ydental_internal_code, width=180, height=180)
        payload = {'kind': kind, 'title': self.env._('Internal laboratory package identification label'),
            'template': 'YD-S12-LAB-LABEL-1', 'source_id': order.id, 'version': version,
            'identity': [self._pair(self.env._('Source store'), order.ydental_store_id.name),
                self._pair(self.env._('Work order ID'), order.id)],
            'status': dict(order._fields['state']._description_selection(self.env))[order.state],
            'selected_state': self.env._('Identification only. This code is not an access credential and does not receive or put away goods.'),
            'details': [self._pair(self.env._('Internal identification code'), order.ydental_internal_code),
                self._pair(self.env._('External package code'), order.ydental_package_code),
                self._pair(self.env._('Cycle / original order'), '%s / %s' % (order.ydental_rework_no, order.ydental_parent_order_id.id or order.id)),
                self._pair(self.env._('Teeth'), ', '.join(str(value) for value in order.ydental_teeth)),
                self._pair(self.env._('Material / shade'), '%s / %s' % (order.ydental_material, order.ydental_shade or '-')),
                self._pair(self.env._('Quantity'), order.ydental_quantity),
                self._pair(self.env._('Responsible person'), order.ydental_responsible_id.name),
                self._pair(self.env._('Planned UTC'), str(order.ydental_planned_at))],
            'sections': [], 'teeth': [], 'lines': [], 'events': [],
            'barcode': {'format': 'QR', 'value': order.ydental_internal_code,
                'png': base64.b64encode(barcode).decode('ascii'), 'sha256': hashlib.sha256(barcode).hexdigest()},
            'versions': {'order': [order.id, order.ydental_version, order.state],
                'source_patient': order.ydental_patient_id.id, 'source_event': order.ydental_source_event_id.id,
                'cycle': order.ydental_rework_no, 'parent': order.ydental_parent_order_id.id}}
        return service, order, category, payload, digest(normalized(payload))

    def _original_choices(self):
        choices = super()._original_choices()
        try:
            store = self.env['ydental.lab.service']._access()
        except AccessError:
            return choices
        for order in self.env['ydental.lab.order'].sudo().search([('ydental_store_id', '=', store.id)], order='id desc', limit=100):
            try:
                self._original_authorize('lab_label', order.id, order.ydental_version)
            except (AccessError, UserError):
                continue
            choices.append({'kind': 'lab_label', 'id': order.id, 'version': order.ydental_version,
                'state': order.state, 'kind_label': self.env._('Internal laboratory label')})
        return choices
