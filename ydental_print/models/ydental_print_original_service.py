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
            documents = self.env['ydental.clinical.document'].sudo().search([
                ('ydental_store_id', '=', store.id)], order='id desc', limit=100)
            for document in documents:
                if self.env['ydental.patient.service']._current_relation(document.ydental_patient_id, store, required=False):
                    for kind in ('clinical', 'consent'):
                        choices.append({'kind': kind, 'id': document.id, 'version': document.ydental_version,
                            'state': document.state, 'kind_label': self.env._('Clinical text') if kind == 'clinical' else self.env._('Consent awaiting signature')})
        if levels['medical'] in ('read', 'write') or levels['pharmacy'] in ('read', 'write'):
            orders = self.env['ydental.treatment.order'].sudo().search([
                ('ydental_store_id', '=', store.id), ('ydental_kind', '=', 'prescription')], order='id desc', limit=100)
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
        facts = {'code': 'YD-S12-SYNTHETIC-1', 'version': '1', 'state': 'synthetic_unreviewed',
            'language': 'zh_CN',
            'synthetic': True, 'paper': 'a4', 'body': '', 'applicability': 'Synthetic software demonstration only',
            'allow_excerpt': False, 'approval_reference': False, 'reviewer': False, 'reviewed_at': False,
            'publisher': False, 'published_at': False}
        if template:
            facts.update({'code': template.name, 'version': template.version, 'state': template.state,
                'synthetic': template.synthetic, 'paper': template.paper, 'body': template.body,
                'applicability': template.applicability, 'allow_excerpt': template.allow_excerpt,
                'approval_reference': template.approval_reference, 'reviewer': template.reviewed_by_id.id,
                'reviewed_at': str(template.reviewed_at), 'publisher': template.published_by_id.id,
                'published_at': str(template.published_at)})
        facts['qweb'] = {xmlid: self.env.ref(xmlid).sudo().with_context(lang='zh_CN').arch_db for xmlid in (
            'ydental_print.ydental_document_pdf', 'ydental_print.ydental_pdf_layout')}
        paper_xmlid = 'ydental_print.ydental_pdf_80mm' if facts['paper'] == '80mm' else 'ydental_print.ydental_pdf_a4'
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

    def _original_workbench(self):
        store = self.env['ydental.access.service']._scope().ydental_store_id
        rows = []
        for original in self.env['ydental.document.original'].sudo().search([('store_id', '=', store.id)], limit=100):
            try:
                self._original_reauthorize(original)
            except (AccessError, UserError):
                continue
            rows.append({'id': original.id, 'kind': original.kind, 'source_id': original.source_id,
                'version': original.version, 'sha256': original.pdf_sha256, 'previous_id': original.previous_id.id,
                'generated_at': str(original.generated_at), 'synthetic': original.template_facts['synthetic']})
        return {'choices': self._original_choices(), 'originals': rows,
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
                or type(synthetic) is not bool or type(allow_excerpt) is not bool or paper not in ('a4', '80mm')
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
