import hashlib
import inspect
import io
import json
import re
import zipfile
from dataclasses import replace

from psycopg2.errors import UniqueViolation

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.pdf import PdfFileReader, PdfReadError
from odoo.addons.base.models.ir_qweb import QWebError

from .ydental_print_service import REPORT, digest, normalized


class YDentalPrintOriginalService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_version_summary(self, payload):
        kind = payload['kind']
        versions = payload['versions']
        rows = []
        def add(label, value):
            rows.append({'label': label, 'value': str(value)})
        if kind == 'clinical_summary':
            selection = versions['selection']
            add(self.env._('Explicit source collection'), '#%s / %s' % (selection[0], selection[2]))
            for document_id, selected_version, confirmed, _sha in versions['documents']:
                add(self.env._('Clinical document %s', document_id),
                    self.env._('Selected version %(version)s / %(state)s', version=selected_version,
                        state=self.env._('Confirmed') if confirmed else self.env._('Awaiting confirmation')))
        elif kind in ('clinical', 'consent'):
            document = versions['document']
            selected = versions['selected_version']
            add(self.env._('Clinical document'), '#%s / selected v%s' % (document[0], payload['version']))
            add(self.env._('Saved text version record'), '#%s / %s' % (selected[0], selected[2]))
            add(self.env._('Reception segment'), versions['source_segment'])
        elif kind == 'prescription':
            order = versions['order']
            add(self.env._('Prescription order'), '#%s / v%s / %s' % (order[0], order[1], order[2]))
            for line_id, state in versions['lines']:
                add(self.env._('Prescription line %s', line_id), state)
        elif kind == 'exam':
            result = versions['result']
            selected = versions['selected']
            add(self.env._('Examination result'), '#%s / selected v%s' % (result[0], selected[1]))
            add(self.env._('Saved result version record'), '#%s / %s' % (selected[0], selected[2]))
            add(self.env._('Frozen examination line'), versions['line'][0])
            add(self.env._('Actual examination event'), versions['event'][0] if versions['event'] else self.env._('Not recorded'))
        elif kind == 'lab_label':
            order = versions['order']
            add(self.env._('Laboratory order'), '#%s / v%s / %s' % (order[0], order[1], order[2]))
            add(self.env._('Source actual event'), versions['source_event'])
            add(self.env._('Cycle / original order'), '%s / %s' % (versions['cycle'], versions['parent'] or order[0]))
        elif kind == 'bill':
            add(self.env._('Original internal bill'), '#%s' % payload['source_id'])
            for row in versions.get('accounting', {}).get('sources', []):
                add(self.env._('Bill source %s', row['id']), self.env._(
                    'Bill %(bill)s / fee %(fee)s / frozen price version %(version)s',
                    bill=row['ydental_invoice_id'], fee=row['ydental_fee_id'], version=row['ydental_price_version']))
        elif kind in ('receipt', 'refund'):
            add(self.env._('Collection record') if kind == 'receipt' else self.env._('Refund record'),
                '#%s' % payload['source_id'])
            for allocation in versions.get('allocations', []):
                add(self.env._('Original bill %s', allocation['invoice_id']),
                    '%s / source IDs %s' % (allocation['number'], ', '.join(str(value) for value in allocation['source_ids'])))
            for refund in versions.get('refunds', []):
                add(self.env._('Refund source %s', refund['id']), refund['ydental_state'])
        else:
            add(self.env._('Source record / selected version'), '#%s / v%s' % (payload['source_id'], payload['version']))
        return rows

    def _original_patient(self, source, kind):
        return source.ydental_patient_id

    def _original_authorize(self, kind, source_id, version, purpose=None):
        # Single copies use the existing source permission. Bulk delivery adds
        # S01 export permission separately, before any source is projected.
        return self._authorize(kind, source_id, version, purpose, require_export=False)

    def _original_source(self, kind, source_id, version, purpose=None):
        return self._source(kind, source_id, version, purpose, require_export=False)

    def _original_choices(self):
        access = self.env['ydental.access.service']
        store = access._scope().ydental_store_id
        levels = access._levels(access._membership(self.env.uid, store.id))
        choices = []
        if levels['medical'] in ('read', 'write'):
            self.env['ydental.clinical.service']._access()
            documents = self.env['ydental.clinical.document'].sudo().search(self._original_search_domain([
                ('ydental_store_id', '=', store.id)]), order='id desc', limit=100)
            for document in documents:
                if self.env['ydental.patient.service']._current_relation(document.ydental_patient_id, store, required=False):
                    for kind in ('clinical', 'consent'):
                        choices.append({'kind': kind, 'id': document.id, 'version': document.ydental_version,
                            'state': document.state, 'kind_label': self.env._('Clinical text') if kind == 'clinical' else self.env._('Consent awaiting signature')})
        if levels['medical'] in ('read', 'write') or levels['pharmacy'] in ('read', 'write'):
            orders = self.env['ydental.treatment.order'].sudo().search(self._original_search_domain([
                ('ydental_store_id', '=', store.id), ('ydental_kind', '=', 'prescription')]), order='id desc', limit=100)
            for order in orders:
                try:
                    self._original_authorize('prescription', order.id, order.ydental_version)
                except (AccessError, UserError):
                    continue
                choices.append({'kind': 'prescription', 'id': order.id, 'version': order.ydental_version,
                    'state': order.state, 'kind_label': self.env._('Prescription')})
        return choices

    def _original_template_facts(self, kind, template_id=None):
        store = self.env['ydental.access.service']._scope().ydental_store_id
        template = self.env['ydental.document.template'].sudo().browse(self._id(template_id)).exists() if template_id else self.env['ydental.document.template']
        if template and (template.kind != kind or template.store_id != store or template.state != 'published'):
            raise AccessError(self.env._('template_unpublished: Select a published template for this type and current store.'))
        facts = {'code': 'YD-S13-SYNTHETIC-6', 'version': '6', 'state': 'synthetic_unreviewed',
            'language': 'zh_CN',
            'synthetic': True, 'paper': 'label100x70' if kind == 'lab_label' else 'a4',
            'body': '', 'applicability': 'Synthetic software demonstration only',
            'allow_excerpt': False, 'approval_reference': False, 'reviewer': False, 'reviewed_at': False,
            'publisher': False, 'published_at': False}
        if template:
            facts.update({'code': template.name, 'version': template.version, 'state': template.state,
                'synthetic': template.synthetic, 'paper': template.paper, 'body': template.body,
                'applicability': template.applicability, 'allow_excerpt': template.allow_excerpt,
                'approval_reference': template.approval_reference, 'reviewer': template.reviewed_by_id.id,
                'reviewed_at': str(template.reviewed_at), 'publisher': template.published_by_id.id,
                'published_at': str(template.published_at)})
        facts['layout_version'] = 'YD-S13-UX-LAYOUT-6'
        facts['qweb'] = {xmlid: self.env.ref(xmlid).sudo().with_context(lang='zh_CN').arch_db for xmlid in (
            'ydental_print.ydental_document_pdf', 'ydental_print.ydental_pdf_layout')}
        paper_xmlid = {'80mm': 'ydental_print.ydental_pdf_80mm',
            'label100x70': 'ydental_print.ydental_pdf_label100x70'}.get(facts['paper'], 'ydental_print.ydental_pdf_a4')
        paper = self.env.ref(paper_xmlid).sudo()
        facts['paperformat'] = {name: paper[name] for name in ('format', 'page_height', 'page_width', 'orientation',
            'margin_top', 'margin_bottom', 'margin_left', 'margin_right', 'dpi', 'disable_shrinking')}
        return template, facts, digest(normalized(facts))

    def _original_payload(self, kind, source_id, version, purpose=None, template_id=None):
        service, source, category, payload, source_sha = self._original_source(kind, source_id, version, purpose)
        template, template_facts, template_sha = service._original_template_facts(kind, template_id)
        # Every rendered value is frozen here. The report reads this payload,
        # never live names, prices, clinical text or template body during render.
        payload = dict(payload, original=True, synthetic=template_facts['synthetic'], paper=template_facts['paper'],
            content_template=template_facts['code'], content_template_version=template_facts['version'],
            template_state=template_facts['state'], applicability=template_facts['applicability'],
            template_digest=template_sha, template=payload['template'] + ' / ' + template_facts['code'])
        payload['layout_version'] = template_facts['layout_version']
        payload['template_state_label'] = {
            'synthetic_unreviewed': self.env._('Synthetic / unreviewed'),
            'draft': self.env._('Draft'), 'reviewed': self.env._('Reviewed'),
            'published': self.env._('Published'),
        }[template_facts['state']]
        payload['template_paragraphs'] = [template_facts['body'][i:i + 350]
            for i in range(0, len(template_facts['body']), 350)]
        if not template:
            payload['applicability'] = self.env._('Synthetic software demonstration only')
        technical_identity = {self.env._('Canonical patient ID'), self.env._('Source patient ID'),
            self.env._('Source store ID'), self.env._('Viewing store ID')}
        technical_details = {self.env._('Independent document ID'), self.env._('Current document version'),
            self.env._('Selected version previous ID'), self.env._('Source reception segment'), self.env._('Current reception segment'),
            self.env._('Clinical field template'), self.env._('Order ID'), self.env._('Source document and version'), self.env._('Frozen examination line'),
            self.env._('Source template code / version'), self.env._('Explicit source collection ID'), self.env._('All selected document IDs'),
            self.env._('Excerpt policy template ID')}
        payload['business_identity'] = [row for row in payload['identity'] if row[0] not in technical_identity]
        payload['business_details'] = [row for row in payload['details'] if row[0] not in technical_details]
        payload['technical_details'] = [row for row in payload['identity'] if row[0] in technical_identity]
        payload['technical_details'] += [row for row in payload['details'] if row[0] in technical_details]
        actors = []
        for field_name in ('ydental_author_id', 'ydental_actor_id', 'ydental_original_author_id'):
            if field_name in source._fields and source[field_name]:
                actors.append(source[field_name].name)
        state = source.state if 'state' in source._fields else payload['status']
        payload['footer_provenance'] = '%s #%s / v%s / %s / %s' % (
            kind[:20], source.id, version, str(state)[:20], ', '.join(dict.fromkeys(actors))[:24])
        payload['version_summary'] = service._original_version_summary(payload)
        if template_facts['body']:
            payload['sections'] = list(payload['sections']) + [{'label': self.env._('Reviewed template content'),
                'paragraphs': [template_facts['body'][i:i + 350] for i in range(0, len(template_facts['body']), 350)]}]
        payload['sections'] = [dict(section, paragraphs=[
            block for paragraph in section['paragraphs']
            for block in ([paragraph[index:index + 350] for index in range(0, len(paragraph), 350)] or [''])])
            for section in payload['sections']]
        if not template_facts['synthetic']:
            _authorized, _source, selected, _category = service._original_authorize(kind, source_id, version, purpose)
            confirmed_text = selected and selected.ydental_kind in ('confirm', 'correct', 'correction')
            if (kind in ('clinical', 'exam') and not confirmed_text
                    or kind == 'prescription' and source.state not in ('issued', 'done')
                    or kind == 'clinical_summary' and source.mode == 'draft'):
                raise UserError(self.env._('incomplete_sources: Unconfirmed sources cannot be issued with a formal published document template.'))
            titles = {'clinical': self.env._('Confirmed clinical text PDF'),
                'prescription': self.env._('Issued prescription PDF'),
                'consent': self.env._('Consent content awaiting signature'),
                'exam': self.env._('Confirmed examination report PDF'),
                'clinical_summary': self.env._('Explicitly scoped clinical source collection PDF')}
            payload['title'] = titles.get(kind, payload['title'])
        return service, source, category, payload, digest(normalized(payload)), template, template_facts, template_sha

    def _original_scope(self, payload, signature, purpose):
        return replace(self._render_scope(payload, signature, purpose), original=True)

    def _original_request_template(self, kind, source_id, version, purpose, template_id):
        return template_id or None

    def _original_chain_key(self, kind, source, store):
        return source.id

    def _original_previous(self, kind, source, store, previous_id):
        latest = self.env['ydental.document.original'].sudo().search([
            ('kind', '=', kind), ('source_id', '=', source.id), ('store_id', '=', store.id)], order='version desc', limit=1)
        if latest.id != (previous_id or False):
            raise UserError(self.env._('version_conflict: Select the latest original as the previous version.'))
        return latest

    def _original_preview(self, kind, source_id, version, purpose=None, template_id=None):
        service, source, category, payload, signature, template, facts, template_sha = self._original_payload(kind, source_id, version, purpose, template_id)
        scope = service._original_scope(payload, signature, purpose)
        try:
            html, _ = service.env['ir.actions.report'].with_context(ydental_print_scope=scope, lang='zh_CN')._render_qweb_html(REPORT, [source.id])
        except (QWebError, OSError) as error:
            raise UserError(self.env._('render_failed: The document preview could not be generated.')) from error
        service._original_audit('view', source, category, {'source_sha256': signature, 'template_sha256': template_sha})
        return {'html': html.decode() if isinstance(html, bytes) else str(html), 'source_digest': signature,
            'template_digest': template_sha, 'versions': payload['versions'], 'template_id': template.id}

    def _store_original(self, kind, source_id, version, expected_digest, key, purpose=None, previous_id=None, template_id=None):
        if (not isinstance(expected_digest, str) or not re.fullmatch('[a-f0-9]{64}', expected_digest)
                or not isinstance(key, str) or not 16 <= len(key) <= 128):
            raise ValidationError(self.env._('invalid_source: Review a source and supply a stable generation key.'))
        template_id = self._original_request_template(kind, source_id, version, purpose, template_id)
        originals = self.env['ydental.document.original'].sudo()
        prior = originals.search([('actor_id', '=', self.env.uid), ('request_key', '=', key)], limit=1)
        if prior:
            if expected_digest != prior.source_sha256:
                raise UserError(self.env._('version_conflict: This generation key belongs to a different reviewed source digest.'))
            if (prior.kind, prior.source_id, prior.source_version, prior.purpose or None, prior.previous_id.id, prior.template_id.id) != (
                    kind, source_id, version, purpose or None, previous_id or False, template_id or False):
                raise UserError(self.env._('version_conflict: This original key belongs to another request.'))
            self._original_bytes(prior.id, 'recovery')
            return {'original_id': prior.id, 'version': prior.version, 'sha256': prior.pdf_sha256, 'duplicate': True}
        service, source, category, payload, signature, template, template_facts, template_sha = self._original_payload(kind, source_id, version, purpose, template_id)
        # Source version chains are serialized without changing any clinical,
        # accounting or inventory source to acquire a lock.
        if signature != expected_digest:
            raise UserError(self.env._('version_conflict: The source changed. Review before generating an original.'))
        store = service.env['ydental.access.service']._scope().ydental_store_id
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [32031, service._original_chain_key(kind, source, store)])
        latest = service._original_previous(kind, source, store, previous_id)
        scope = service._original_scope(payload, signature, purpose)
        render_facts = json.loads(scope.payload)
        reports = service.env['ir.actions.report'].with_context(ydental_print_scope=scope, lang='zh_CN',
            force_report_rendering=True, report_pdf_no_attachment=True)
        try:
            pdf, output_type = reports._render_qweb_pdf(REPORT, [source.id])
            if output_type != 'pdf' or not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF-') or len(pdf) > 10000000:
                raise UserError(self.env._('render_failed: The engine did not produce a valid bounded PDF.'))
            if len(PdfFileReader(io.BytesIO(pdf)).pages) > 80:
                raise UserError(self.env._('size_limit: This document exceeds the page limit.'))
        except (QWebError, PdfReadError, OSError, ValueError) as error:
            raise UserError(self.env._('render_failed: The engine did not produce a valid bounded PDF.')) from error
        # All reads share Odoo's repeatable-read transaction snapshot. A source
        # committed by another connection cannot splice new fields into this
        # already frozen payload; file and source facts describe that snapshot.
        patient = service._original_patient(source, kind)
        original = originals._new({'kind': kind, 'source_model': source._name, 'source_id': source.id,
            'source_version': version, 'purpose': purpose, 'patient_id': patient.id, 'store_id': store.id,
            'company_id': store.company_id.id, 'category': category, 'actor_id': self.env.uid,
            'generated_at': fields.Datetime.to_datetime(render_facts['generated_at']), 'request_key': key, 'version': latest.version + 1 if latest else 1,
            'previous_id': latest.id, 'source_facts': payload, 'source_sha256': signature,
            'render_facts': render_facts,
            'template_id': template.id, 'template_facts': template_facts, 'template_sha256': template_sha,
            'pdf_sha256': hashlib.sha256(pdf).hexdigest()})
        attachment = self.env['ir.attachment'].sudo().create({'name': 'document-original-%s-v%s.pdf' % (original.id, original.version),
            'type': 'binary', 'raw': pdf, 'mimetype': 'application/pdf', 'res_model': original._name,
            'res_id': original.id, 'company_id': store.company_id.id, 'public': False, 'access_token': False})
        original._attach_once(attachment)
        service._original_audit('generate', source, category, {'original_id': original.id, 'version': original.version,
            'source_sha256': signature, 'template_sha256': template_sha, 'pdf_sha256': original.pdf_sha256})
        return {'original_id': original.id, 'version': original.version, 'sha256': original.pdf_sha256, 'duplicate': False}

    def _original_reauthorize(self, original):
        # Recheck live source authorization, not current content equality. An
        # old prescription still downloads after legitimate dispensing changes.
        source = self.env[original.source_model].sudo().browse(original.source_id).exists()
        if not source:
            raise UserError(self.env._('original_missing: The original source is unavailable.'))
        current_version = source.ydental_version if 'ydental_version' in source._fields else original.source_version
        service, source, _selected, category = self._original_authorize(original.kind, original.source_id, current_version, original.purpose or None)
        store = service.env['ydental.access.service']._scope().ydental_store_id
        patient = service.env['ydental.patient.service']._patient(service._original_patient(source, original.kind).id)
        frozen_patient = service.env['ydental.patient.service']._patient(original.patient_id.id)
        if (original.company_id != store.company_id or original.store_id != store
                or patient != frozen_patient or source._name != original.source_model):
            raise AccessError(self.env._('access_denied: This original is outside the current authorized source scope.'))
        return service, source, category

    def _original_bytes(self, original_id, operation='download'):
        if operation not in ('download', 'pdf_view', 'print_request', 'recovery', 'export'):
            raise ValidationError(self.env._('invalid_action: Select a documented original operation.'))
        original = self.env['ydental.document.original'].sudo().browse(self._id(original_id)).exists()
        if not original:
            raise UserError(self.env._('original_missing: The document original is unavailable.'))
        service, source, category = self._original_reauthorize(original)
        attachment = original.attachment_id
        if (not attachment or attachment.res_model != original._name or attachment.res_id != original.id
                or attachment.company_id != original.company_id or attachment.public or attachment.access_token):
            raise UserError(self.env._('original_missing: The stored original file is unavailable.'))
        raw = attachment.raw.content
        if not raw or hashlib.sha256(raw).hexdigest() != original.pdf_sha256:
            raise UserError(self.env._('original_corrupt: The stored file does not match its checksum.'))
        service._original_audit(operation, source, category, {'original_id': original.id, 'version': original.version,
            'pdf_sha256': original.pdf_sha256})
        return raw, original.pdf_sha256

    def _original_export(self, original_ids):
        self.env['ydental.access.service']._check('export', 'write')
        if (not isinstance(original_ids, list) or not original_ids or len(original_ids) > 20
                or len(set(original_ids)) != len(original_ids) or any(type(value) is not int or value < 1 for value in original_ids)):
            raise ValidationError(self.env._('size_limit: Select between one and twenty distinct originals.'))
        files = [(value, self._original_bytes(value, 'export')[0]) for value in original_ids]
        if sum(len(raw) for _, raw in files) > 20000000:
            raise ValidationError(self.env._('size_limit: This batch exceeds the export size limit.'))
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for original_id, raw in files:
                archive.writestr('document-original-%s.pdf' % original_id, raw)
        return output.getvalue()

    def _original_audit(self, operation, source, category, after):
        access = self.env['ydental.access.service']
        access._audit('document.' + operation, category, source, access._scope().ydental_store_id.id,
            source='document_original', after=dict(after, paper_output='unknown'))

    def _original_search_domain(self, domain, patient_field='ydental_patient_id'):
        term = self.env.context.get('ydental_document_term', '')
        if not term:
            return domain
        return fields.Domain.AND([fields.Domain(domain),
            fields.Domain(patient_field + '.name', 'ilike', term)
            | fields.Domain(patient_field + '.ydental_number', 'ilike', term)])

    def _original_kind_labels(self):
        return {'clinical': self.env._('Clinical text'), 'clinical_summary': self.env._('Clinical source collection'),
            'consent': self.env._('Consent awaiting signature'), 'prescription': self.env._('Prescription'),
            'exam': self.env._('Examination report'), 'bill': self.env._('Internal bill'),
            'receipt': self.env._('Actual collection receipt'), 'refund': self.env._('Refund approval or execution voucher'),
            'lab_label': self.env._('Laboratory identification label')}

    def _original_snapshot_status(self, kind, facts):
        if kind == 'refund':
            state = facts.get('versions', {}).get('native_facts', {}).get('state')
            return {'requested': self.env._('Refund requested; not approved'),
                'approved': self.env._('Approved; awaiting actual refund'),
                'failed': self.env._('Refund execution failed; pending verification'),
                'unknown': self.env._('Refund execution result unknown; pending verification'),
                'done': self.env._('Actually refunded'), 'rejected': self.env._('Refund rejected'),
                'cancelled': self.env._('Refund cancelled')}.get(state, facts.get('status', ''))
        if kind == 'clinical_summary':
            selection = facts.get('versions', {}).get('selection', [])
            return {'draft': self.env._('Incomplete selected source collection; not a complete medical record'),
                'excerpt': self.env._('Policy-approved confirmed excerpt; not a complete medical record'),
                'complete': self.env._('All explicitly selected clinical sources confirmed; complete within the listed scope')}.get(
                    selection[2] if len(selection) > 2 else '', facts.get('status', ''))
        if kind == 'lab_label':
            order = facts.get('versions', {}).get('order', [])
            return {'draft': self.env._('Laboratory draft'),
                'sent': self.env._('Dispatched work order; supplier shipment not implied'),
                'processing': self.env._('Laboratory processing'), 'received': self.env._('Physically received'),
                'available': self.env._('Put away and awaiting fit'), 'rework_returned': self.env._('Returned for rework'),
                'done': self.env._('Actually fitted'), 'cancelled': self.env._('Cancelled before put-away'),
                'exception': self.env._('Laboratory exception closed')}.get(order[2] if len(order) > 2 else '', facts.get('status', ''))
        if kind in ('bill', 'receipt'):
            return self.env._('Frozen business snapshot; current balances may differ')
        value = facts.get('selected_state') or facts.get('status', '')
        labels = {
            'Confirmed result text': self.env._('Confirmed result text'),
            'Draft result text; incomplete': self.env._('Draft result text; incomplete'),
            'Text confirmed, not a formal medical signature': self.env._('Text confirmed, not a formal medical signature'),
            'Selected text is a draft; awaiting completion or confirmation.': self.env._('Selected text is a draft; awaiting completion or confirmation.'),
            'Awaiting completion / explanation / signature / verification': self.env._('Awaiting completion / explanation / signature / verification'),
            'Formal prescription signing is not approved. This is not a receipt, invoice or payment proof.': self.env._('Formal prescription signing is not approved. This is not a receipt, invoice or payment proof.'),
        }
        return labels.get(value, value)

    def _original_workbench(self, term='', page=1):
        if not isinstance(term, str) or len(term) > 100 or type(page) is not int or page < 1:
            raise ValidationError(self.env._('invalid_search: Use a patient name or business number and a valid page.'))
        self = self.with_context(ydental_document_term=term.strip())
        store = self.env['ydental.access.service']._scope().ydental_store_id
        kind_labels = self._original_kind_labels()
        rows = []
        candidates = self.env['ydental.document.original'].sudo().search(self._original_search_domain(
            [('store_id', '=', store.id)], patient_field='patient_id'))
        for original in candidates:
            try:
                self._original_reauthorize(original)
            except (AccessError, UserError):
                continue
            if len(rows) >= 5000:
                raise UserError(self.env._('size_limit: Narrow the patient search before listing more originals.'))
            rows.append({'id': original.id, 'kind': original.kind, 'source_id': original.source_id,
                'version': original.version, 'sha256': original.pdf_sha256, 'previous_id': original.previous_id.id,
                'generated_at': str(original.generated_at), 'synthetic': original.template_facts['synthetic'],
                'title': kind_labels.get(original.kind, original.kind),
                'patient_name': original.patient_id.name, 'patient_number': original.patient_id.ydental_number,
                'status': self._original_snapshot_status(original.kind, original.source_facts),
                'trace': {'pdf_sha256': original.pdf_sha256, 'original_id': original.id,
                    'previous_original_id': original.previous_id.id, 'source_model': original.source_model, 'source_id': original.source_id,
                    'source_version': original.source_version, 'source_sha256': original.source_sha256,
                    'template_sha256': original.template_sha256,
                    'layout_version': original.template_facts.get('layout_version', 'S12 layout'),
                    'template': original.template_facts['code'], 'template_version': original.template_facts['version'],
                    'frozen_title': original.source_facts.get('title', ''),
                    'details': original.source_facts.get('details', []),
                    'versions': original.source_facts.get('version_summary', [])}})
        choices = []
        for choice in self._original_choices():
            try:
                _service, source, _selected, _category = self._original_authorize(
                    choice['kind'], choice['id'], choice['version'])
            except (AccessError, UserError):
                continue
            patient = self._original_patient(source, choice['kind'])
            state_field = 'ydental_state' if 'ydental_state' in source._fields else 'state'
            state = source[state_field] if state_field in source._fields else choice['state']
            selection = source._fields.get(state_field)
            state_label = dict(selection._description_selection(self.env)).get(state, state) if selection and selection.type == 'selection' else state
            if choice['kind'] == 'lab_label' and state == 'sent':
                state_label = self.env._('Dispatched work order; supplier shipment not implied')
            number = source.name if 'name' in source._fields else ''
            if choice['kind'] == 'receipt':
                number = source.ydental_payment_id.name
            choice = dict(choice, kind_label=kind_labels.get(choice['kind'], choice['kind']),
                patient_label='%s / %s' % (patient.name, patient.ydental_number),
                patient_name=patient.name, patient_number=patient.ydental_number,
                state_label=state_label,
                source_label='%s / %s / %s' % (patient.name, patient.ydental_number, number or str(source.create_date)))
            choices.append(choice)
        total = len(rows)
        page_count = max(1, (total + 29) // 30)
        page = min(page, page_count)
        return {'choices': choices, 'choices_limit': 100, 'originals': rows[(page - 1) * 30:page * 30],
            'term': term.strip(), 'pagination': {'page': page, 'page_count': page_count, 'total': total,
                'previous': page - 1 if page > 1 else None, 'next': page + 1 if page < page_count else None},
            'templates': self.env['ydental.document.template'].sudo().search([('store_id', '=', store.id), ('state', '=', 'published')])}

    def _template_manager(self):
        access = self.env['ydental.access.service']
        store = access._scope(write=True).ydental_store_id
        if not access._is_group_manager() or not store or store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: Group document policy administration is required.'))
        return store

    def _configure_document_template(self, name, kind, version, body, applicability, synthetic=True, paper='a4', allow_excerpt=False, approval_reference=None):
        store = self._template_manager()
        if (any(not isinstance(value, str) or not value.strip() or len(value) > maximum for value, maximum in (
                (name, 120), (kind, 40), (version, 80), (body, 40000), (applicability, 240)))
                or type(synthetic) is not bool or type(allow_excerpt) is not bool or paper not in ('a4', '80mm', 'label100x70')
                or paper == 'label100x70' and kind != 'lab_label'
                or approval_reference is not None and (not isinstance(approval_reference, str) or len(approval_reference) > 240)):
            raise ValidationError(self.env._('invalid_template: Use bounded plain text, an explicit purpose and valid paper settings.'))
        template = self.env['ydental.document.template']._new({'name': name.strip(), 'kind': kind,
            'store_id': store.id, 'version': version.strip(), 'body': body, 'applicability': applicability.strip(),
            'synthetic': synthetic, 'paper': paper, 'allow_excerpt': allow_excerpt,
            'approval_reference': approval_reference, 'state': 'draft'})
        self._original_audit('template_create', template, 'medical', {'template_id': template.id, 'state': template.state, 'synthetic': synthetic})
        return {'template_id': template.id, 'state': template.state}

    def _review_document_template(self, template_id, action):
        store = self._template_manager()
        template = self.env['ydental.document.template'].sudo().browse(self._id(template_id)).exists()
        if not template or template.store_id != store or action not in ('review', 'publish'):
            raise AccessError(self.env._('access_denied: Select a template in the current store and a documented review action.'))
        if action == 'review':
            if template.state != 'draft':
                raise UserError(self.env._('version_conflict: Only draft template versions can be reviewed.'))
            template._save({'state': 'reviewed', 'reviewed_by_id': self.env.uid, 'reviewed_at': fields.Datetime.now()})
        else:
            if template.state != 'reviewed' or not template.synthetic and not template.approval_reference:
                raise UserError(self.env._('template_unapproved: Review the version and record the formal approval reference before publishing.'))
            template._save({'state': 'published', 'published_by_id': self.env.uid, 'published_at': fields.Datetime.now()})
        self._original_audit('template_' + action, template, 'medical', {'template_id': template.id,
            'state': template.state, 'synthetic': template.synthetic})
        return {'template_id': template.id, 'state': template.state}

    def _original_handlers(self):
        return {'preview': self._original_preview, 'generate': self._store_original,
            'download': lambda original_id: self._original_bytes(original_id, 'download'),
            'pdf_view': lambda original_id: self._original_bytes(original_id, 'pdf_view'),
            'print_request': lambda original_id: self._original_bytes(original_id, 'print_request'),
            'export': self._original_export, 'template_create': self._configure_document_template,
            'template_review': self._review_document_template}

    def _original_operate(self, operation, payload):
        handlers = self._original_handlers()
        if operation not in handlers or not isinstance(payload, dict):
            raise ValidationError(self.env._('invalid_action: Select a documented document operation.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_source: Unknown or missing document arguments.')) from error
        access = self.env['ydental.access.service']
        access._lock_user(self.env.uid)
        session = access._scope(write=True)
        self.env.cr.execute('UPDATE ydental_access_session SET ydental_revision=ydental_revision WHERE id=%s', [session.id])
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR NO KEY UPDATE', [self.env.uid])
        self.env.cr.execute('SELECT id FROM ydental_access_membership WHERE ydental_user_id=%s AND ydental_store_id=%s FOR NO KEY UPDATE', [self.env.uid, session.ydental_store_id.id])
        member_ids = [row[0] for row in self.env.cr.fetchall()]
        self.env.cr.execute('SELECT id FROM ydental_access_grant WHERE ydental_membership_id=ANY(%s) FOR NO KEY UPDATE', [member_ids])
        try:
            with self.env.cr.savepoint():
                return handlers[operation](**payload)
        except UniqueViolation as error:
            raise UserError(self.env._('version_conflict: A concurrent request already preserved this version or file. Refresh the saved result before retrying.')) from error
