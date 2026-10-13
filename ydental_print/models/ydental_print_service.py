import hashlib
import inspect
import io
import json
import re
from dataclasses import dataclass
from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.pdf import PdfFileReader
from odoo.tools.binary import BinaryBytes

from odoo.addons.ydental_clinical.models.ydental_clinical_service import TEXT_FIELDS


REPORT = 'ydental_print.ydental_document_pdf'
TEMPLATES = {'clinical': 'S08C-CLINICAL-1', 'prescription': 'S08C-RX-1', 'consent': 'S08C-CONSENT-1'}


def normalized(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class RenderScope:
    actor: int
    session: int
    revision: int
    kind: str
    source_id: int
    version: int
    purpose: str | None
    payload: str
    content_digest: str


class YDentalPrintService(models.AbstractModel):
    _name = 'ydental.print.service'
    _description = 'Read-only clinical PDF projection and controlled delivery'

    def _id(self, value):
        return self.env['ydental.intake.service']._id(value)

    def _authorize(self, kind, source_id, version, purpose=None):
        if kind not in TEMPLATES or type(version) is not int or version < 0 or purpose not in (None, '', 'diagnosis', 'history_review'):
            raise ValidationError(self.env._('invalid_source: Select a documented PDF type, source and version.'))
        access = self.env['ydental.access.service']
        session = access._scope()
        store = session.ydental_store_id
        access._check('export', 'write')
        if store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: The current company is unavailable.'))
        if kind in ('clinical', 'consent'):
            clinical = self.env['ydental.clinical.service']
            preliminary = self.env['ydental.clinical.document'].sudo().browse(self._id(source_id)).exists()
            if not preliminary:
                raise AccessError(self.env._('access_denied: This PDF source is unavailable.'))
            if purpose:
                clinical = access._patient_care(preliminary.ydental_patient_id.id, purpose).env['ydental.clinical.service']
            doc = clinical._document(source_id)
            versions = clinical._model('version')
            selected = versions.search([('ydental_document_id', '=', doc.id), ('ydental_number', '=', version)], limit=1)
            if (not selected and version != 0) or version == 0 and doc.ydental_version != 0:
                raise UserError(self.env._('version_conflict: The selected clinical version is unavailable.'))
            if selected:
                clinical.env['ydental.clinical.version'].browse(selected.id).check_access('read')
            return clinical.env[self._name], doc, selected, 'medical'
        treatment = self.env['ydental.treatment.service']
        order = self.env['ydental.treatment.order'].sudo().browse(self._id(source_id)).exists()
        if not order or order.ydental_kind != 'prescription' or order.ydental_store_id != store or purpose:
            raise AccessError(self.env._('access_denied: This prescription is unavailable in the current store.'))
        member = access._membership(self.env.uid, store.id)
        levels = access._levels(member)
        if levels['medical'] in ('read', 'write'):
            treatment._access('medical', False)
            self.env['ydental.treatment.order'].browse(order.id).check_access('read')
            category = 'medical'
        else:
            treatment._access('pharmacy', False)
            # Narrow trusted projection only: an issued prescription with a real
            # local pharmacy task, never clinical content or draft orders.
            segments = self.env['ydental.treatment.segment'].sudo().search([
                ('ydental_order_id', '=', order.id), ('ydental_store_id', '=', store.id)])
            if order.state not in ('issued', 'done') or not segments or any(
                s.ydental_task_id.ydental_patient_id != order.ydental_patient_id or
                s.ydental_task_id.ydental_store_id != store or s.ydental_task_id.ydental_mapping_id.ydental_execution_area_id.ydental_purpose != 'pharmacy'
                for s in segments
            ):
                raise AccessError(self.env._('access_denied: A real current prescription pharmacy task is required.'))
            category = 'pharmacy'
        self.env['ydental.patient.service']._current_relation(order.ydental_patient_id, store)
        if order.ydental_version != version:
            raise UserError(self.env._('version_conflict: Refresh the prescription version.'))
        return self, order, False, category

    def _choices(self):
        access = self.env['ydental.access.service']
        store = access._scope().ydental_store_id
        access._check('export', 'write')
        member = access._membership(self.env.uid, store.id)
        levels = access._levels(member)
        choices = []
        if levels['medical'] in ('read', 'write'):
            self.env['ydental.clinical.service']._access()
            docs = self.env['ydental.clinical.document'].sudo().search([('ydental_store_id', '=', store.id)], order='id desc', limit=100)
            orders = self.env['ydental.treatment.order'].sudo().search([('ydental_store_id', '=', store.id), ('ydental_kind', '=', 'prescription')], order='id desc', limit=100)
            for doc in docs:
                if self.env['ydental.patient.service']._current_relation(doc.ydental_patient_id, store, required=False):
                    choices.append({'kind': 'clinical', 'id': doc.id, 'version': doc.ydental_version, 'state': doc.state})
                    choices.append({'kind': 'consent', 'id': doc.id, 'version': doc.ydental_version, 'state': 'unsigned'})
        else:
            self.env['ydental.treatment.service']._access('pharmacy', False)
            segments = self.env['ydental.treatment.segment'].sudo().search([('ydental_store_id', '=', store.id)], order='id desc', limit=100)
            orders = segments.ydental_order_id
        for order in orders:
            if self.env['ydental.patient.service']._current_relation(order.ydental_patient_id, store, required=False):
                choices.append({'kind': 'prescription', 'id': order.id, 'version': order.ydental_version, 'state': order.state})
        return choices

    def _pair(self, label, value):
        return [label, str(value) if value is not False and value is not None and value != '' else self.env._('Not recorded')]

    def _source(self, kind, source_id, version, purpose=None):
        service, source, selected, category = self._authorize(kind, source_id, version, purpose)
        patient_service = service.env['ydental.patient.service']
        patient = patient_service._patient(source.ydental_patient_id.id)
        store = source.ydental_store_id
        title = {'clinical': self.env._('Clinical text demonstration PDF'),
                 'prescription': self.env._('Prescription demonstration PDF'),
                 'consent': self.env._('Unsigned consent demonstration PDF')}[kind]
        payload = {'kind': kind, 'title': title, 'template': TEMPLATES[kind], 'source_id': source.id,
            'version': version, 'identity': [self._pair(self.env._('Patient'), patient.name),
                self._pair(self.env._('Patient number'), patient.ydental_number),
                self._pair(self.env._('Canonical patient ID'), patient.id),
                self._pair(self.env._('Source patient ID'), source.ydental_patient_id.id),
                self._pair(self.env._('Source store'), store.name), self._pair(self.env._('Source store ID'), store.id),
                self._pair(self.env._('Viewing store ID'), service.env['ydental.access.service']._scope().ydental_store_id.id)],
            'details': [], 'sections': [], 'teeth': [], 'lines': [], 'events': []}
        if kind in ('clinical', 'consent'):
            doc = source
            content = service.env['ydental.clinical.service']._content(selected.ydental_content if selected else doc.ydental_content)
            current = {'draft': self.env._('Draft'), 'pending': self.env._('Document awaiting completion'), 'confirmed': self.env._('Text confirmed, not a formal medical signature')}
            payload['status'] = current[doc.state]
            payload['details'] = [self._pair(self.env._('Independent document ID'), doc.id),
                self._pair(self.env._('Selected text version'), version),
                self._pair(self.env._('Current document version'), doc.ydental_version),
                self._pair(self.env._('Current document state'), current[doc.state]),
                self._pair(self.env._('Original author'), doc.ydental_author_id.name),
                self._pair(self.env._('Current responsible person'), doc.ydental_responsible_id.name),
                self._pair(self.env._('Selected version contributor'), selected.ydental_author_id.name if selected else False),
                self._pair(self.env._('Selected version action'), dict(selected._fields['ydental_kind']._description_selection(self.env))[selected.ydental_kind] if selected else self.env._('Not recorded')),
                self._pair(self.env._('Selected version recorded at (UTC)'), str(selected.ydental_recorded_at) if selected else False),
                self._pair(self.env._('Selected version previous ID'), selected.ydental_previous_id.id if selected else False),
                self._pair(self.env._('Text correction reason'), selected.ydental_reason if selected else False),
                self._pair(self.env._('Source reception segment'), doc.ydental_execution_id.id),
                self._pair(self.env._('Current reception segment'), doc.ydental_current_execution_id.id),
                self._pair(self.env._('Original reception operator'), doc.ydental_execution_id.ydental_lease_id.ydental_actor_id.name),
                self._pair(self.env._('Original workstation'), doc.ydental_execution_id.ydental_lease_id.ydental_station_id.name),
                self._pair(self.env._('Original reception started at (UTC)'), str(doc.ydental_execution_id.ydental_started_at)),
                self._pair(self.env._('Clinical field template'), selected.ydental_template if selected else doc.ydental_template)]
            version_set = {'document': [doc.id, doc.ydental_version, doc.state], 'selected_version': [selected.id, version, selected.ydental_kind] if selected else [0, 0, 'unsaved'],
                'source_segment': doc.ydental_execution_id.id, 'current_segment': doc.ydental_current_execution_id.id,
                'canonical_patient': patient.id, 'source_patient': doc.ydental_patient_id.id}
            if kind == 'clinical':
                labels = [self.env._('Chief complaint'), self.env._('History'), self.env._('Findings'), self.env._('Diagnosis'),
                    self.env._('Treatment plan'), self.env._('Suggested materials'), self.env._('Follow-up')]
                for field, label in zip(TEXT_FIELDS, labels):
                    text = content[field] or self.env._('Not recorded; no clinical conclusion is inferred.')
                    # Bounded blocks wrap both CJK and unbroken malicious text.
                    paragraphs = [text[i:i + 350] for i in range(0, len(text), 350)]
                    payload['sections'].append({'label': label, 'paragraphs': paragraphs})
                tooth_labels = {'present': self.env._('Present'), 'missing': self.env._('Missing'), 'unknown': self.env._('Unknown'), 'not_applicable': self.env._('Not applicable')}
                payload['teeth'] = [{'tooth': row['tooth'], 'state': tooth_labels[row['state']], 'surfaces': ', '.join(row['surfaces']) or self.env._('Not recorded')} for row in content['teeth']]
                payload['selected_state'] = self.env._('Text confirmed, not a formal medical signature') if selected and selected.ydental_kind in ('confirm', 'correct') else self.env._('Selected text is a draft; awaiting completion or confirmation.')
            else:
                # The source is linked for review; its clinical statements are
                # deliberately not copied into an unapproved legal template.
                payload['status'] = self.env._('Demonstration / unreviewed / unsigned')
                payload['selected_state'] = self.env._('Awaiting completion / explanation / signature / verification')
                payload['sections'] = [{'label': label, 'paragraphs': [self.env._('To be completed and reviewed; left blank.')]} for label in (
                    self.env._('Proposed care and medical content'), self.env._('Risks and alternatives'), self.env._('Explanation and questions'),
                    self.env._('Patient decision'), self.env._('Patient signature'), self.env._('Clinician signature'),
                    self.env._('Guardian authority and signature'), self.env._('Signature date and verification'))]
        else:
            order = source
            lines = self.env['ydental.treatment.line'].sudo().search([('ydental_order_id', '=', order.id)], order='id')
            events = self.env['ydental.treatment.event'].sudo().search([('ydental_order_line_id', 'in', lines.ids), ('ydental_kind', '=', 'prescription')], order='id')
            if len(lines) > 100 or len(events) > 500:
                raise ValidationError(self.env._('size_limit: This source exceeds the single demonstration PDF limit.'))
            order_labels = {'draft': self.env._('Draft'), 'issued': self.env._('Issued, frozen'), 'done': self.env._('All approved quantities dispensed')}
            line_labels = dict(lines._fields['state']._description_selection(self.env))
            payload['status'] = order_labels[order.state]
            payload['selected_state'] = self.env._('Formal prescription signing is not approved. This is not a receipt, invoice or payment proof.')
            payload['details'] = [self._pair(self.env._('Order ID'), order.id), self._pair(self.env._('Order version'), order.ydental_version),
                self._pair(self.env._('Original prescribing clinician'), order.ydental_actor_id.name),
                self._pair(self.env._('Source document and version'), '%s / %s' % (order.ydental_document_id.id, order.ydental_document_version)),
                self._pair(self.env._('Source reception segment'), order.ydental_execution_id.id)]
            for line in lines:
                actual = events.filtered(lambda e: e.ydental_order_line_id == line)
                dispensed = sum(actual.mapped('ydental_quantity'))
                payload['lines'].append({'id': line.id, 'sku': line.ydental_product_id.default_code or str(line.ydental_product_id.id),
                    'product_id': line.ydental_product_id.id, 'name': line.ydental_product_id.name or self.env._('Not recorded'),
                    'product_specification': line.ydental_product_id.ydental_specification or self.env._('Not recorded'),
                    'specification': line.ydental_specification or self.env._('Not recorded'), 'usage': line.ydental_usage or self.env._('Not recorded'),
                    'frequency': line.ydental_frequency or self.env._('Not recorded'), 'course': line.ydental_course or self.env._('Not recorded'),
                    'approved': line.ydental_quantity, 'dispensed': dispensed, 'remaining': line.ydental_quantity - dispensed,
                    'unit': line.ydental_uom_id.name, 'unit_id': line.ydental_uom_id.id, 'state': line_labels[line.state],
                    'reason': line.ydental_reason or self.env._('Not recorded')})
            payload['events'] = [{'id': e.id, 'line_id': e.ydental_order_line_id.id, 'product_id': e.ydental_product_id.id,
                'quantity': e.ydental_quantity, 'actor': e.ydental_actor_id.name, 'time': str(e.ydental_actual_at),
                'business_date': str(e.ydental_business_date), 'state': dict(e._fields['state']._description_selection(self.env))[e.state],
                'price_source': e.ydental_price_snapshot_id.id, 'medicine_link': e.ydental_medicine_link_id.id} for e in events]
            version_set = {'order': [order.id, order.ydental_version, order.state],
                'lines': [[l.id, l.state] for l in lines], 'actual_dispensing_events': events.ids,
                'canonical_patient': patient.id, 'source_patient': order.ydental_patient_id.id}
        payload['versions'] = version_set
        serialized = normalized(payload)
        if len(serialized.encode()) > 400000:
            raise ValidationError(self.env._('size_limit: This source exceeds the single demonstration PDF limit.'))
        return service, source, category, payload, digest(serialized)

    def _render_scope(self, payload, signature, purpose):
        session = self.env['ydental.access.service']._scope()
        stamped = dict(payload, generated_by=self.env.user.name, generated_at=str(fields.Datetime.now()), source_digest=signature)
        text = normalized(stamped)
        return RenderScope(self.env.uid, session.id, session.ydental_revision, payload['kind'], payload['source_id'], payload['version'], purpose, text, digest(text))

    def _validate_render_scope(self):
        scope = self.env.context.get('ydental_print_scope')
        session = self.env['ydental.access.service']._scope()
        if not isinstance(scope, RenderScope) or (scope.actor, scope.session, scope.revision) != (self.env.uid, session.id, session.ydental_revision) or digest(scope.payload) != scope.content_digest:
            raise AccessError(self.env._('access_denied: Use the controlled PDF entry with a live source selection.'))
        self._authorize(scope.kind, scope.source_id, scope.version, scope.purpose)
        return json.loads(scope.payload)

    def _audit(self, operation, source, category, payload, signature, job=None, result='accepted'):
        access = self.env['ydental.access.service']
        access._audit('print.' + operation, category, source, access._scope().ydental_store_id.id,
            source='controlled_demo_pdf', result=result, after={'type': payload['kind'], 'version_set': payload['versions'],
                'template': payload['template'], 'source_digest': signature, 'job_id': job.id if job else False,
                'pdf_digest': job.ydental_pdf_digest if job else False, 'paper_output': 'unknown'})

    def _preview(self, kind, source_id, version, purpose=None):
        service, source, category, payload, signature = self._source(kind, source_id, version, purpose)
        scope = service._render_scope(payload, signature, purpose)
        html, _ = service.env['ir.actions.report'].with_context(ydental_print_scope=scope, lang='zh_CN')._render_qweb_html(REPORT, [source.id])
        self._audit('view', source, category, payload, signature)
        return {'html': html.decode() if isinstance(html, bytes) else str(html), 'source_digest': signature, 'versions': payload['versions'], 'template': payload['template']}

    def _job(self, job_id):
        session = self.env['ydental.access.service']._scope()
        # Narrow sudo is necessary because no ordinary ACL exposes job bodies.
        job = self.env['ydental.print.job'].sudo().browse(self._id(job_id)).exists()
        if not job or (job.ydental_actor_id.id, job.ydental_session_id.id, job.ydental_revision, job.ydental_store_id.id) != (
            self.env.uid, session.id, session.ydental_revision, session.ydental_store_id.id) or job.ydental_expires_at <= fields.Datetime.now():
            raise AccessError(self.env._('access_denied: This temporary PDF is unavailable. Generate a new demonstration copy.'))
        service, source, category, payload, signature = self._source(job.ydental_kind, job.ydental_source_id, job.ydental_version, job.ydental_purpose or None)
        if signature != job.ydental_source_digest:
            raise UserError(self.env._('version_conflict: The source changed. Review and generate a new demonstration copy.'))
        return job, source, category, payload, signature

    def _generate(self, kind, source_id, version, expected_digest, key, purpose=None):
        if not isinstance(expected_digest, str) or not re.fullmatch('[a-f0-9]{64}', expected_digest) or not isinstance(key, str) or not 16 <= len(key) <= 128:
            raise ValidationError(self.env._('invalid_source: Review the source digest and supply a stable generation key.'))
        service, source, category, payload, signature = self._source(kind, source_id, version, purpose)
        if signature != expected_digest:
            raise UserError(self.env._('version_conflict: The source changed. Review before generating a PDF.'))
        session = self.env['ydental.access.service']._scope()
        jobs = self.env['ydental.print.job'].sudo()
        prior = jobs.search([('ydental_session_id', '=', session.id), ('ydental_revision', '=', session.ydental_revision), ('ydental_key', '=', key)], limit=1)
        if prior:
            job, _, _, _, _ = self._job(prior.id)
            if (job.ydental_kind, job.ydental_source_id, job.ydental_version, job.ydental_source_digest) != (kind, source_id, version, expected_digest):
                raise UserError(self.env._('version_conflict: This generation key belongs to another source.'))
            self._audit('generate_repeat', source, category, payload, signature, job)
        else:
            scope = service._render_scope(payload, signature, purpose)
            reports = service.env['ir.actions.report'].with_context(ydental_print_scope=scope, lang='zh_CN', force_report_rendering=True, report_pdf_no_attachment=True)
            pdf, output_type = reports._render_qweb_pdf(REPORT, [source.id])
            if output_type != 'pdf' or not pdf.startswith(b'%PDF-') or len(pdf) > 10000000:
                raise UserError(self.env._('render_failed: The PDF engine did not produce a valid bounded PDF.'))
            if len(PdfFileReader(io.BytesIO(pdf)).pages) > 80:
                raise UserError(self.env._('size_limit: This PDF exceeds the demonstration page limit.'))
            job = jobs._new({'ydental_actor_id': self.env.uid, 'ydental_store_id': session.ydental_store_id.id,
                'ydental_session_id': session.id, 'ydental_revision': session.ydental_revision, 'ydental_kind': kind,
                'ydental_source_id': source_id, 'ydental_version': version, 'ydental_purpose': purpose,
                'ydental_source_digest': signature, 'ydental_pdf_digest': hashlib.sha256(pdf).hexdigest(),
                'ydental_template': TEMPLATES[kind], 'ydental_versions': payload['versions'],
                'ydental_expires_at': fields.Datetime.now() + timedelta(minutes=15), 'ydental_key': key,
                'ydental_pdf': BinaryBytes(pdf, filename='ydental-demonstration.pdf')})
            self._audit('generate', source, category, payload, signature, job)
        return {'job_id': job.id, 'pdf_digest': job.ydental_pdf_digest, 'source_digest': signature, 'versions': job.ydental_versions,
                'expires_at': str(job.ydental_expires_at), 'paper_output': 'unknown'}

    def _deliver(self, operation, job_id):
        if operation not in ('pdf_view', 'download', 'print_request'):
            raise ValidationError(self.env._('invalid_action: Select a documented PDF operation.'))
        job, source, category, payload, signature = self._job(job_id)
        pdf = job.ydental_pdf.content
        if hashlib.sha256(pdf).hexdigest() != job.ydental_pdf_digest:
            raise UserError(self.env._('render_failed: Temporary PDF integrity verification failed.'))
        self._audit('print_requested' if operation == 'print_request' else operation, source, category, payload, signature, job)
        return pdf, job.ydental_pdf_digest

    def _operate(self, operation, payload):
        # Public RPC cannot create RenderScope or S01 Binding instances. This
        # private service is reached only through the server HTTP adapter.
        handlers = {'preview': self._preview, 'generate': self._generate,
                    'pdf_view': lambda job_id: self._deliver('pdf_view', job_id),
                    'download': lambda job_id: self._deliver('download', job_id),
                    'print_request': lambda job_id: self._deliver('print_request', job_id)}
        if operation not in handlers or not isinstance(payload, dict):
            raise ValidationError(self.env._('invalid_action: Select a documented PDF operation.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_source: Unknown or missing PDF arguments.')) from error
        access = self.env['ydental.access.service']
        access._lock_user(self.env.uid)
        session = access._scope(write=True)
        # Under PostgreSQL repeatable read, advisory/row locks alone do not
        # refresh a waiting request's snapshot. A value-preserving session
        # fence makes a competing PDF action retry in a fresh transaction.
        self.env.cr.execute('UPDATE ydental_access_session SET ydental_revision=ydental_revision WHERE id=%s', [session.id])
        # Detect a grant/lifecycle change committed while this request waited
        # on the S01 actor lock; do not accept stale positive permission data.
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR UPDATE', [self.env.uid])
        self.env.cr.execute('SELECT id FROM ydental_access_membership WHERE ydental_user_id=%s AND ydental_store_id=%s FOR UPDATE', [self.env.uid, session.ydental_store_id.id])
        members = [row[0] for row in self.env.cr.fetchall()]
        self.env.cr.execute('SELECT id FROM ydental_access_grant WHERE ydental_membership_id=ANY(%s) FOR UPDATE', [members])
        with self.env.cr.savepoint():
            return handlers[operation](**payload)
