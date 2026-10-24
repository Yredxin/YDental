from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .ydental_print_service import digest, normalized


class YDentalPrintSummaryService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_chain_key(self, kind, source, store):
        if kind != 'clinical_summary':
            return super()._original_chain_key(kind, source, store)
        return int(source.scope_sha256[:8], 16) & 0x7FFFFFFF

    def _original_previous(self, kind, source, store, previous_id):
        if kind != 'clinical_summary':
            return super()._original_previous(kind, source, store, previous_id)
        selections = self.env['ydental.document.selection'].sudo().search([
            ('ydental_store_id', '=', store.id), ('scope_sha256', '=', source.scope_sha256)])
        latest = self.env['ydental.document.original'].sudo().search([
            ('kind', '=', kind), ('source_model', '=', source._name),
            ('source_id', 'in', selections.ids), ('store_id', '=', store.id)], order='version desc', limit=1)
        if latest.id != (previous_id or False):
            raise UserError(self.env._('version_conflict: Select the latest original for this exact clinical source collection.'))
        if latest:
            _authorized, previous_selection, _category = self._original_reauthorize(latest)
            patient = self.env['ydental.patient.service']._patient(source.ydental_patient_id.id)
            previous_patient = self.env['ydental.patient.service']._patient(previous_selection.ydental_patient_id.id)
            if patient != previous_patient or {row['id'] for row in source.documents} != {row['id'] for row in previous_selection.documents}:
                raise UserError(self.env._('scope_conflict: A summary successor requires the same patient, store and complete intended document set.'))
            if self.env['ydental.document.original'].sudo().search_count([('previous_id', '=', latest.id)]):
                raise UserError(self.env._('version_conflict: This original already has a successor.'))
        return latest

    def _summary_execution_facts(self, document_ids):
        orders = self.env['ydental.treatment.order'].sudo().search([
            ('ydental_document_id', 'in', document_ids)], order='id')
        lines = self.env['ydental.treatment.line'].sudo().search([
            ('ydental_order_id', 'in', orders.ids)], order='id')
        domain = fields.Domain('ydental_document_id', 'in', document_ids) | fields.Domain('ydental_order_line_id', 'in', lines.ids)
        events = self.env['ydental.treatment.event'].sudo().search(domain, order='id')
        if len(orders) > 100 or len(lines) > 500 or len(events) > 1000:
            raise ValidationError(self.env._('size_limit: The selected clinical execution history exceeds the document limit.'))
        return {'orders': [{'id': row.id, 'document_id': row.ydental_document_id.id,
                    'document_version': row.ydental_document_version, 'version': row.ydental_version,
                    'kind': row.ydental_kind, 'state': row.state, 'author_id': row.ydental_actor_id.id,
                    'author': row.ydental_actor_id.name} for row in orders],
                'lines': [{'id': row.id, 'order_id': row.ydental_order_id.id, 'state': row.state,
                    'service': row.ydental_mapping_id.ydental_catalog_id.name, 'quantity': row.ydental_quantity,
                    'unit': row.ydental_uom_id.name} for row in lines],
                'events': [{'id': row.id, 'document_id': row.ydental_document_id.id,
                    'document_version': row.ydental_document_version, 'line_id': row.ydental_order_line_id.id,
                    'kind': row.ydental_kind, 'state': row.state, 'actor_id': row.ydental_actor_id.id,
                    'actor': row.ydental_actor_id.name, 'actual_at': str(row.ydental_actual_at),
                    'business_date': str(row.ydental_business_date), 'quantity': row.ydental_quantity,
                    'unit': row.ydental_uom_id.name, 'price_snapshot_id': row.ydental_price_snapshot_id.id}
                    for row in events]}

    def _original_request_template(self, kind, source_id, version, purpose, template_id):
        if kind != 'clinical_summary':
            return super()._original_request_template(kind, source_id, version, purpose, template_id)
        _service, selection, _selected, _category = self._original_authorize(kind, source_id, version, purpose)
        if template_id and template_id != selection.template_id.id:
            raise UserError(self.env._('policy_conflict: Use the template and policy version frozen in this explicit source selection.'))
        return selection.template_id.id or None

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
            'scope_sha256': digest(normalized([store.id, sorted(document_ids)])),
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
        source_traces = []
        author_labels = {self.env._('Original author'), self.env._('Current responsible person'),
            self.env._('Selected version contributor'), self.env._('Selected version recorded at (UTC)'),
            self.env._('Text correction reason')}
        for row in all_payloads:
            included = selection.mode != 'excerpt' or row['confirmed']
            payload = row['payload']
            sections.append({'label': self.env._('Source document %s / selected version %s', row['document_id'], row['selected_version']),
                'paragraphs': [status, self.env._('Included') if included else self.env._('Not included: selected source is awaiting confirmation')]
                    + ['%s: %s' % (label, value) for label, value in payload['details'] if label in author_labels]})
            source_traces.append({'label': self.env._('Source document %s: version trace', row['document_id']),
                'paragraphs': ['%s: %s' % (label, value) for label, value in payload['details'] if label not in author_labels]})
            if included:
                for section in payload['sections']:
                    sections.append({'label': self.env._('Source %s / %s', row['document_id'], section['label']),
                        'paragraphs': section['paragraphs']})
        included_ids = confirmed if selection.mode == 'excerpt' else [row['id'] for row in selection.documents]
        execution_facts = self._summary_execution_facts(included_ids)
        order_model = self.env['ydental.treatment.order']
        order_kinds = dict(order_model._fields['ydental_kind']._description_selection(self.env))
        order_states = dict(order_model._fields['state']._description_selection(self.env))
        line_states = dict(self.env['ydental.treatment.line']._fields['state']._description_selection(self.env))
        event_model = self.env['ydental.treatment.event']
        event_kinds = dict(event_model._fields['ydental_kind']._description_selection(self.env))
        event_states = dict(event_model._fields['state']._description_selection(self.env))
        for order in execution_facts['orders']:
            order_lines = [row for row in execution_facts['lines'] if row['order_id'] == order['id']]
            sections.append({'label': self.env._('Order %s / source document %s', order['id'], order['document_id']),
                'paragraphs': [self.env._('Order type: %(kind)s; state: %(state)s; author: %(author)s; source text version: %(version)s',
                    kind=order_kinds[order['kind']], state=order_states[order['state']], author=order['author'], version=order['document_version'])]
                    + [self.env._('Line %(line)s / %(service)s / state %(state)s / approved quantity %(quantity)s %(unit)s',
                        line=row['id'], service=row['service'], state=line_states[row['state']], quantity=row['quantity'], unit=row['unit'])
                        for row in order_lines]})
        sections.append({'label': self.env._('Actual execution and dispensing facts, separate from order issuance'),
            'paragraphs': [self.env._('Event %(event)s / %(kind)s / operator %(actor)s / UTC %(time)s / actual quantity %(quantity)s %(unit)s / reconciliation %(state)s',
                event=row['id'], kind=event_kinds[row['kind']], actor=row['actor'], time=row['actual_at'], quantity=row['quantity'],
                unit=row['unit'], state=event_states[row['state']]) for row in execution_facts['events']]
                or [self.env._('No actual execution or dispensing is recorded for these selected sources.')]})
        sections += source_traces
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
            'selection_scope_sha256': selection.scope_sha256,
            'execution_facts': execution_facts,
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
        for selection in self.env['ydental.document.selection'].sudo().search(self._original_search_domain([
                ('ydental_store_id', '=', store.id)]), limit=100):
            try:
                self._original_authorize('clinical_summary', selection.id, 1)
            except (AccessError, UserError):
                continue
            choices.append({'kind': 'clinical_summary', 'id': selection.id, 'version': 1, 'state': selection.mode,
                'kind_label': self.env._('Explicit clinical source collection')})
        return choices

    def _original_handlers(self):
        return super()._original_handlers() | {'select_clinical_sources': self._select_clinical_sources}
