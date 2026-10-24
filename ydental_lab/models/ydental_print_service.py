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
        patient = self.env['ydental.patient.service']._patient(order.ydental_patient_id.id)
        state_labels = {'draft': self.env._('Laboratory draft'),
            'sent': self.env._('Dispatched work order; supplier shipment not implied'),
            'processing': self.env._('Laboratory processing'), 'received': self.env._('Physically received'),
            'available': self.env._('Put away and awaiting fit'), 'rework_returned': self.env._('Returned for rework'),
            'done': self.env._('Actually fitted'), 'cancelled': self.env._('Cancelled before put-away'),
            'exception': self.env._('Laboratory exception closed')}
        label_states = dict(state_labels, sent=self.env._('Work order sent'),
            draft=self.env._('Draft'), processing=self.env._('Processing'))
        payload = {'kind': kind, 'title': self.env._('Internal laboratory package identification label'),
            'template': 'YD-S13-LAB-LABEL-3', 'source_id': order.id, 'version': version,
            'identity': [self._pair(self.env._('Source store'), order.ydental_store_id.name),
                self._pair(self.env._('Work order ID'), order.id)],
            'status': state_labels[order.state],
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
            'label_identity': [self._pair(self.env._('Source store'), order.ydental_store_id.name),
                self._pair(self.env._('Patient number'), patient.ydental_number)],
            'label_details': [self._pair(self.env._('Teeth'), ', '.join(str(value) for value in order.ydental_teeth)),
                self._pair(self.env._('Material / shade'), '%s / %s' % (order.ydental_material, order.ydental_shade or '-')),
                self._pair(self.env._('Quantity'), order.ydental_quantity),
                self._pair(self.env._('Processing instructions'), order.ydental_instructions)],
            'label_business': {'store': order.ydental_store_id.name, 'patient_number': patient.ydental_number,
                'state': label_states[order.state], 'teeth': ', '.join(str(value) for value in order.ydental_teeth),
                'material': order.ydental_material, 'shade': order.ydental_shade or self.env._('Not recorded'),
                'quantity': order.ydental_quantity, 'instructions': order.ydental_instructions},
            'barcode': {'format': 'QR', 'value': order.ydental_internal_code, 'width': 180, 'height': 180},
            'versions': {'order': [order.id, order.ydental_version, order.state],
                'source_patient': order.ydental_patient_id.id, 'source_event': order.ydental_source_event_id.id,
                'cycle': order.ydental_rework_no, 'parent': order.ydental_parent_order_id.id}}
        return service, order, category, payload, digest(normalized(payload))

    def _original_scope(self, payload, signature, purpose):
        if payload['kind'] == 'lab_label':
            # Native PNG encoding is not deterministic across requests. The
            # reviewed source freezes the exact semantic code and dimensions;
            # the typed render snapshot separately freezes actual PNG bytes.
            barcode = payload['barcode']
            image = self.env['ir.actions.report'].barcode(barcode['format'], barcode['value'],
                width=barcode['width'], height=barcode['height'])
            payload = dict(payload, barcode=dict(barcode, png=base64.b64encode(image).decode('ascii'),
                sha256=hashlib.sha256(image).hexdigest()))
        return super()._original_scope(payload, signature, purpose)

    def _original_choices(self):
        choices = super()._original_choices()
        try:
            store = self.env['ydental.lab.service']._access()
        except AccessError:
            return choices
        for order in self.env['ydental.lab.order'].sudo().search(self._original_search_domain([
                ('ydental_store_id', '=', store.id)]), order='id desc', limit=100):
            try:
                self._original_authorize('lab_label', order.id, order.ydental_version)
            except (AccessError, UserError):
                continue
            choices.append({'kind': 'lab_label', 'id': order.id, 'version': order.ydental_version,
                'state': order.state, 'kind_label': self.env._('Internal laboratory label')})
        return choices
