from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .ydental_print_service import digest, normalized


class YDentalPrintSummaryService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_payload(self, kind, source_id, version, purpose=None, template_id=None):
        if kind == 'clinical_summary':
            _service, selection, _selected, _category = self._original_authorize(kind, source_id, version, purpose)
            selected_template_id = selection.template_id.id
            if template_id and template_id != selected_template_id:
                raise UserError(self.env._('policy_conflict: Use the template and policy version frozen in this explicit source selection.'))
            template_id = selected_template_id or None
        return super()._original_payload(kind, source_id, version, purpose, template_id)

    def _select_clinical_sources(self, document_ids, mode='complete', template_id=None):
        if (not isinstance(document_ids, list) or not document_ids or len(document_ids) > 40
                or any(type(value) is not int or value < 1 for value in document_ids)
                or len(set(document_ids)) != len(document_ids) or mode not in ('draft', 'complete', 'excerpt')):
            raise ValidationError(self.env._('invalid_source: Explicitly select one to forty distinct clinical sources and a summary mode.'))
        access = self.env['ydental.access.service']
        store = access._check('medical', 'read').ydental_store_id
        rows = []
        patient = False
        for document_id in document_ids:
            document = self.env['ydental.clinical.document'].sudo().browse(document_id).exists()
            if not document:
                raise AccessError(self.env._('access_denied: Every selected clinical source must be available.'))
            self._authorize('clinical', document.id, document.ydental_version, require_export=False)
            canonical = self.env['ydental.patient.service']._patient(document.ydental_patient_id.id)
            if patient and patient != canonical or document.ydental_store_id != store:
                raise AccessError(self.env._('access_denied: A summary must identify one patient and the current source store.'))
            patient = canonical
            rows.append({'id': document.id, 'version': document.ydental_version, 'state_at_selection': document.state})
        template, _facts, _sha = self._original_template_facts('clinical_summary', template_id)
        if mode == 'excerpt' and (not template or not template.allow_excerpt):
            raise UserError(self.env._('policy_required: A published current-store policy must explicitly permit confirmed excerpts.'))
        selection = self.env['ydental.document.selection']._new({'ydental_patient_id': patient.id, 'ydental_store_id': store.id,
            'ydental_version': 1, 'actor_id': self.env.uid, 'selected_at': fields.Datetime.now(),
            'documents': rows, 'mode': mode, 'template_id': template.id})
        self._original_audit('source_selection', selection, 'medical', {'selection_id': selection.id,
            'document_ids': document_ids, 'mode': mode, 'template_id': template.id})
        return {'selection_id': selection.id, 'kind': 'clinical_summary', 'source_id': selection.id, 'version': 1}

    def _original_authorize(self, kind, source_id, version, purpose=None):
        if kind != 'clinical_summary':
            return super()._original_authorize(kind, source_id, version, purpose)
        access = self.env['ydental.access.service']
        store = access._check('medical', 'read').ydental_store_id
        selection = self.env['ydental.document.selection'].sudo().browse(self._id(source_id)).exists()
        if not selection or selection.ydental_store_id != store or version != 1 or purpose:
            raise AccessError(self.env._('access_denied: Select an explicit clinical collection in this store.'))
        patient = self.env['ydental.patient.service']._patient(selection.ydental_patient_id.id)
        for row in selection.documents:
            current = self.env['ydental.clinical.document'].sudo().browse(row['id']).exists()
            if not current:
                raise AccessError(self.env._('access_denied: A selected clinical source is unavailable.'))
            _service, document, _selected, _category = self._authorize('clinical', row['id'], current.ydental_version, require_export=False)
            if self.env['ydental.patient.service']._patient(document.ydental_patient_id.id) != patient:
                raise AccessError(self.env._('access_denied: A selected source no longer belongs to this authorized patient.'))
        return self, selection, False, 'medical'

    def _original_source(self, kind, source_id, version, purpose=None):
        if kind != 'clinical_summary':
            return super()._original_source(kind, source_id, version, purpose)
        service, selection, _selected, category = self._original_authorize(kind, source_id, version, purpose)
        patient = self.env['ydental.patient.service']._patient(selection.ydental_patient_id.id)
        confirmed = []
        unconfirmed = []
        all_payloads = []
        for row in selection.documents:
            _service, document, _category, payload, signature = self._source('clinical', row['id'], row['version'], require_export=False)
            _authorized, _document, selected, _category = self._authorize('clinical', row['id'], row['version'], require_export=False)
            saved_confirmed = selected and selected.ydental_kind in ('confirm', 'correct')
            (confirmed if saved_confirmed else unconfirmed).append(row['id'])
            all_payloads.append({'document_id': document.id, 'selected_version': row['version'],
                'confirmed': bool(saved_confirmed), 'payload': payload, 'sha256': signature})
        if selection.mode == 'complete' and unconfirmed:
            raise UserError(self.env._('incomplete_sources: Selected clinical sources awaiting confirmation: %s', unconfirmed))
        if selection.mode == 'excerpt':
            template, facts, _sha = self._original_template_facts('clinical_summary', selection.template_id.id)
            if not template.allow_excerpt:
                raise UserError(self.env._('policy_required: This published policy does not permit confirmed excerpts.'))
            if not confirmed:
                raise UserError(self.env._('incomplete_sources: No confirmed source can be included in this excerpt.'))
        status = {'draft': self.env._('Incomplete selected source collection; not a complete medical record'),
            'complete': self.env._('All explicitly selected clinical sources confirmed; complete within the listed scope'),
            'excerpt': self.env._('Policy-approved confirmed excerpt; not a complete medical record')}[selection.mode]
        sections = []
        for row in all_payloads:
            included = selection.mode != 'excerpt' or row['confirmed']
            payload = row['payload']
            sections.append({'label': self.env._('Source document %s / selected version %s', row['document_id'], row['selected_version']),
                'paragraphs': [status, self.env._('Included') if included else self.env._('Not included: selected source is awaiting confirmation')]
                    + ['%s: %s' % (label, value) for label, value in payload['details']]})
            if included:
                for section in payload['sections']:
                    sections.append({'label': self.env._('Source %s / %s', row['document_id'], section['label']),
                        'paragraphs': section['paragraphs']})
        payload = {'kind': kind, 'title': self.env._('Clinical source collection PDF'), 'template': 'YD-S12-CLINICAL-SUMMARY-1',
            'source_id': selection.id, 'version': 1, 'status': status, 'selected_state': status,
            'identity': [self._pair(self.env._('Patient'), patient.name), self._pair(self.env._('Patient number'), patient.ydental_number),
                self._pair(self.env._('Source store'), selection.ydental_store_id.name)],
            'details': [self._pair(self.env._('Explicit source collection ID'), selection.id),
                self._pair(self.env._('All selected document IDs'), [row['id'] for row in selection.documents]),
                self._pair(self.env._('Confirmed selected sources'), confirmed), self._pair(self.env._('Unconfirmed selected sources'), unconfirmed),
                self._pair(self.env._('Excerpt policy template ID'), selection.template_id.id)],
            'sections': sections, 'teeth': [], 'lines': [], 'events': [],
            'selected_sources': all_payloads,
            'versions': {'selection': [selection.id, 1, selection.mode],
                'documents': [[row['document_id'], row['selected_version'], row['confirmed'], row['sha256']] for row in all_payloads],
                'source_patient': selection.ydental_patient_id.id, 'canonical_patient': patient.id}}
        if len(normalized(payload).encode()) > 400000:
            raise ValidationError(self.env._('size_limit: The selected collection exceeds the document limit.'))
        return service, selection, category, payload, digest(normalized(payload))

    def _original_choices(self):
        choices = super()._original_choices()
        access = self.env['ydental.access.service']
        try:
            store = access._check('medical', 'read').ydental_store_id
        except AccessError:
            return choices
        for selection in self.env['ydental.document.selection'].sudo().search([('ydental_store_id', '=', store.id)], limit=100):
            try:
                self._original_authorize('clinical_summary', selection.id, 1)
            except (AccessError, UserError):
                continue
            choices.append({'kind': 'clinical_summary', 'id': selection.id, 'version': 1, 'state': selection.mode,
                'kind_label': self.env._('Explicit clinical source collection')})
        return choices

    def _original_handlers(self):
        return super()._original_handlers() | {'select_clinical_sources': self._select_clinical_sources}
