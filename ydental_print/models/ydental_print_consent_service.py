import base64
import binascii
import hashlib
import io

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.pdf import PdfFileReader, PdfReadError

from .ydental_print_service import digest, normalized


class YDentalPrintConsentService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _configure_document_template(self, name, kind, version, body, applicability, synthetic=True, paper='a4',
                                     allow_excerpt=False, approval_reference=None, accepted_previous_template_ids=None):
        store = self._template_manager()
        previous_ids = accepted_previous_template_ids or []
        if (not isinstance(previous_ids, list) or len(previous_ids) > 30
                or any(type(value) is not int or value < 1 for value in previous_ids)
                or len(set(previous_ids)) != len(previous_ids)):
            raise ValidationError(self.env._('invalid_policy: Select distinct explicit earlier consent template versions.'))
        prior = self.env['ydental.document.template'].sudo().browse(previous_ids).exists()
        if previous_ids and (kind != 'consent' or len(prior) != len(previous_ids)
                or any(row.kind != 'consent' or row.store_id != store or row.state != 'published'
                    or row.synthetic != synthetic for row in prior)):
            raise ValidationError(self.env._('invalid_policy: Earlier accepted consent versions must be published in this same store and mode.'))
        result = super()._configure_document_template(name, kind, version, body, applicability,
            synthetic, paper, allow_excerpt, approval_reference)
        self.env['ydental.document.template'].sudo().browse(result['template_id'])._save({
            'accepted_previous_template_ids': sorted(previous_ids)})
        return result

    def _original_template_facts(self, kind, template_id=None):
        template, facts, _signature = super()._original_template_facts(kind, template_id)
        facts['accepted_previous_template_ids'] = template.accepted_previous_template_ids if template else []
        return template, facts, digest(normalized(facts))

    def _consent_original(self, original_id, write=False):
        original = self.env['ydental.document.original'].sudo().browse(self._id(original_id)).exists()
        if not original or original.kind != 'consent':
            raise AccessError(self.env._('access_denied: Select an authorized consent original.'))
        service, source, _category = self._original_reauthorize(original)
        if write:
            service.env['ydental.access.service']._check('medical', 'write', write=True)
        return original, service, source

    def _consent_upload(self, original_id, filename, content):
        original, service, source = self._consent_original(original_id, write=True)
        if (not isinstance(filename, str) or not filename.strip() or len(filename) > 120
                or not isinstance(content, str) or len(content) > 7000000):
            raise ValidationError(self.env._('invalid_evidence: Supply a bounded PDF filename and file.'))
        try:
            raw = base64.b64decode(content, validate=True)
            if not raw.startswith(b'%PDF-') or not raw or len(raw) > 5000000 or len(PdfFileReader(io.BytesIO(raw)).pages) > 80:
                raise ValidationError(self.env._('invalid_evidence: Upload a valid PDF of at most 5 MB and 80 pages.'))
        except (binascii.Error, ValueError, PdfReadError) as error:
            raise ValidationError(self.env._('invalid_evidence: Upload a valid bounded PDF.')) from error
        evidence = self.env['ydental.consent.evidence']._new({'original_id': original.id, 'patient_id': original.patient_id.id,
            'store_id': original.store_id.id, 'template_id': original.template_id.id,
            'template_sha256': original.template_sha256, 'uploaded_by_id': self.env.uid,
            'uploaded_at': fields.Datetime.now(), 'filename': filename.strip(),
            'sha256': hashlib.sha256(raw).hexdigest(), 'synthetic': original.template_facts['synthetic'], 'state': 'pending'})
        attachment = self.env['ir.attachment'].sudo().create({'name': filename.strip(), 'type': 'binary', 'raw': raw,
            'mimetype': 'application/pdf', 'res_model': evidence._name, 'res_id': evidence.id,
            'company_id': original.company_id.id, 'public': False, 'access_token': False})
        evidence._save({'attachment_id': attachment.id})
        service._original_audit('consent_upload', source, 'medical', {'original_id': original.id,
            'evidence_id': evidence.id, 'state': evidence.state, 'synthetic': evidence.synthetic, 'sha256': evidence.sha256})
        return {'evidence_id': evidence.id, 'state': evidence.state, 'sha256': evidence.sha256, 'synthetic': evidence.synthetic}

    def _consent_verify(self, evidence_id, conclusion, reason):
        evidence = self.env['ydental.consent.evidence'].sudo().browse(self._id(evidence_id)).exists()
        if not evidence:
            raise AccessError(self.env._('access_denied: Select an authorized uploaded consent.'))
        original, service, source = self._consent_original(evidence.original_id.id, write=True)
        if conclusion not in ('verified', 'rejected') or not isinstance(reason, str) or not reason.strip() or len(reason) > 500:
            raise ValidationError(self.env._('verification_required: Record the verification conclusion and a reason.'))
        self.env.cr.execute('SELECT id FROM ydental_consent_evidence WHERE id=%s FOR UPDATE', [evidence.id])
        evidence.invalidate_recordset(['state'])
        if evidence.state != 'pending':
            raise UserError(self.env._('history_immutable: This upload already has a verification conclusion.'))
        if (evidence.store_id != original.store_id or evidence.patient_id != original.patient_id
                or evidence.template_id != original.template_id or evidence.template_sha256 != original.template_sha256):
            raise AccessError(self.env._('access_denied: The uploaded evidence does not match its original scope and version.'))
        evidence._save({'state': conclusion, 'verified_by_id': self.env.uid, 'verified_at': fields.Datetime.now(),
            'verification_reason': reason.strip()})
        service._original_audit('consent_verify', source, 'medical', {'evidence_id': evidence.id,
            'state': evidence.state, 'synthetic': evidence.synthetic},)
        return {'evidence_id': evidence.id, 'state': evidence.state, 'synthetic': evidence.synthetic}

    def _consent_evidence_bytes(self, evidence_id):
        evidence = self.env['ydental.consent.evidence'].sudo().browse(self._id(evidence_id)).exists()
        if not evidence:
            raise AccessError(self.env._('access_denied: This consent evidence is unavailable.'))
        original, service, source = self._consent_original(evidence.original_id.id)
        attachment = evidence.attachment_id
        if (not attachment or attachment.res_model != evidence._name or attachment.res_id != evidence.id
                or attachment.public or attachment.access_token or attachment.company_id != original.company_id):
            raise UserError(self.env._('original_missing: The uploaded consent file is unavailable.'))
        raw = attachment.raw.content
        if not raw or hashlib.sha256(raw).hexdigest() != evidence.sha256:
            raise UserError(self.env._('original_corrupt: The uploaded consent file failed its checksum.'))
        service._original_audit('consent_download', source, 'medical', {'evidence_id': evidence.id, 'sha256': evidence.sha256})
        return raw, evidence.sha256

    def _consent_status(self, patient_id):
        access = self.env['ydental.access.service']
        store = access._check('medical', 'read').ydental_store_id
        patient = self.env['ydental.patient.service']._patient(patient_id)
        self.env['ydental.patient.service']._current_relation(patient, store)
        templates = self.env['ydental.document.template'].sudo().search([
            ('store_id', '=', store.id), ('kind', '=', 'consent'), ('state', '=', 'published')])
        evidence = self.env['ydental.consent.evidence'].sudo().search([
            ('store_id', '=', store.id), ('state', '=', 'verified')])
        rows = []
        for template in templates:
            accepted_ids = {template.id, *(template.accepted_previous_template_ids or [])}
            current = evidence.filtered(lambda row: row.template_id.id in accepted_ids
                and row.synthetic == template.synthetic
                and self.env['ydental.patient.service']._patient(row.patient_id.id) == patient)
            rows.append({'template_id': template.id, 'template_version': template.version,
                'synthetic': template.synthetic, 'store_id': store.id,
                'status': 'verified_under_current_published_policy' if current else 'awaiting_current_store_version_verification',
                'evidence_ids': current.ids, 'accepted_previous_template_ids': template.accepted_previous_template_ids,
                'prior_version_policy': 'only_explicit_versions_in_this_published_policy'})
        access._audit('document.consent_status', 'medical', patient, store.id,
            source='document_original', after={'published_template_ids': templates.ids})
        return rows

    def _original_handlers(self):
        return super()._original_handlers() | {'consent_upload': self._consent_upload,
            'consent_verify': self._consent_verify, 'consent_download': self._consent_evidence_bytes,
            'consent_status': self._consent_status}

    def _original_workbench(self):
        values = super()._original_workbench()
        original_ids = [row['id'] for row in values['originals'] if row['kind'] == 'consent']
        values['consent_evidence'] = self.env['ydental.consent.evidence'].sudo().search([
            ('original_id', 'in', original_ids)], order='id desc', limit=100)
        return values
