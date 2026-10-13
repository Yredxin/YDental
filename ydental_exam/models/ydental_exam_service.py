import base64
import binascii
import hashlib
import inspect
import json
from datetime import timedelta
from dataclasses import dataclass
import io
import math

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import consteq
from odoo.tools.pdf import PdfFileReader, PdfReadError
from odoo.addons.base.models.ir_qweb import QWebError

from .ydental_access_capability import PROFILE_GUARD


TEMPLATES = {
    'oral-demo-1': {'capability': 'oral', 'measurements': {'count': 'count'}},
    'periodontal-demo-1': {'capability': 'periodontal', 'measurements': {'depth_mm': 'mm'}},
    'panorama-demo-1': {'capability': 'panorama', 'measurements': {'length_mm': 'mm'}},
    'cbct-demo-1': {'capability': 'cbct', 'measurements': {'length_mm': 'mm'}},
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=True, sort_keys=True).encode()).hexdigest()


@dataclass(frozen=True)
class ExamPdfScope:
    actor_id: int
    session_id: int
    revision: int
    result_id: int
    version: int
    digest: str


class YDentalExamService(models.AbstractModel):
    _name = 'ydental.exam.service'
    _description = 'Frozen examination line, actual execution and independent result authority'

    def _model(self, name):
        return self.env['ydental.exam.' + name].sudo()

    def _store(self, write=False):
        access = self.env['ydental.access.service']
        level = 'write' if write else 'read'
        try:
            member = access._check('exam', level, write=write)
        except AccessError:
            if write:
                raise
            member = access._check('medical', 'read')
        store = member.ydental_store_id
        if store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: The source company is outside the account scope.'))
        return store

    def _line(self, line_id, write=False):
        store = self._store(write)
        line = self.env['ydental.treatment.line'].sudo().browse(self.env['ydental.intake.service']._id(line_id)).exists()
        if not line or line.ydental_order_id.ydental_kind != 'exam' or line.ydental_store_id != store or (
                line.ydental_order_id.ydental_patient_id != line.ydental_patient_id or
                line.ydental_task_id.ydental_mapping_id != line.ydental_mapping_id):
            raise AccessError(self.env._('source_required: Select a real frozen examination line in this store.'))
        self.env['ydental.patient.service']._current_relation(line.ydental_patient_id, store)
        return line

    def _result(self, line, create=False, execution=None):
        result = self._model('result').search([('ydental_line_id', '=', line.id)], limit=1)
        if not result and create:
            catalog = line.ydental_mapping_id.ydental_catalog_id
            template = self._model('template').search([
                ('ydental_store_id', '=', line.ydental_store_id.id),
                ('ydental_catalog_id', '=', catalog.id), ('ydental_active', '=', True)], limit=1)
            if not template or template.ydental_code not in TEMPLATES or (
                    catalog.ydental_capability_id.sudo().ydental_exam_family !=
                    TEMPLATES[template.ydental_code]['capability']):
                raise UserError(self.env._('template_required: Bind a reviewed demonstration template to this exact examination catalog.'))
            result = self._model('result')._new({'name': line.name, 'ydental_store_id': line.ydental_store_id.id,
                'ydental_category': 'exam', 'ydental_patient_id': line.ydental_patient_id.id,
                'ydental_actor_id': self.env.uid, 'ydental_original_author_id': self.env.uid,
                'ydental_responsible_id': self.env.uid,
                'ydental_line_id': line.id, 'ydental_execution_id': execution.id if execution else False,
                'ydental_template_code': template.ydental_code,
                'ydental_template_version': 'S09-DRAFT-1'})
        return result

    def _bind_template(self, catalog_id, code, reason, material_required=False):
        store = self._store(write=True)
        self.env['ydental.access.service']._check('medical', 'write', write=True)
        catalog = self.env['ydental.intake.catalog'].sudo().browse(self.env['ydental.intake.service']._id(catalog_id)).exists()
        if type(material_required) is not bool or not catalog or catalog.ydental_kind != 'exam' or code not in TEMPLATES or (
                not catalog.ydental_capability_id.active):
            raise ValidationError(self.env._('template_required: Select an active examination catalog and a reviewed demonstration template.'))
        if catalog.ydental_capability_id.sudo().ydental_exam_family != TEMPLATES[code]['capability']:
            raise ValidationError(self.env._('template_capability_mismatch: Review the exact service capability before binding its matching examination template.'))
        reason = self.env['ydental.intake.service']._text(reason)
        mapping = self.env['ydental.intake.mapping'].sudo().search([
            ('ydental_catalog_id', '=', catalog.id), ('ydental_store_id', '=', store.id)], limit=1)
        if not mapping:
            raise AccessError(self.env._('source_required: This catalog has no current mapping in this store.'))
        previous = self._model('template').search([
            ('ydental_catalog_id', '=', catalog.id), ('ydental_store_id', '=', store.id)], limit=1)
        if previous:
            if previous.ydental_code != code or previous.ydental_material_required != material_required:
                raise UserError(self.env._('history_immutable: Create a new catalog for a different result template.'))
            return {'template_id': previous.id, 'code': previous.ydental_code}
        template = self._model('template')._new({'name': catalog.name, 'ydental_store_id': store.id,
            'ydental_category': 'exam', 'ydental_patient_id': False, 'ydental_actor_id': self.env.uid,
            'ydental_catalog_id': catalog.id, 'ydental_code': code, 'ydental_active': True,
            'ydental_reason': reason, 'ydental_material_required': material_required})
        self._audit('template_bound', template, {'catalog_id': catalog.id, 'code': code,
            'material_required': material_required}, reason)
        return {'template_id': template.id, 'code': code}

    def _review_capability(self, capability_id, family, reason):
        store = self._store(write=True)
        self.env['ydental.access.service']._check('medical', 'write', write=True)
        if not self.env.user.has_group('ydental_access.ydental_group_manager') or family not in {
                item['capability'] for item in TEMPLATES.values()}:
            raise AccessError(self.env._('access_denied: A store clinical administrator must review the examination capability family.'))
        capability = self.env['ydental.access.capability'].sudo().browse(
            self.env['ydental.intake.service']._id(capability_id)).exists()
        mapped = self.env['ydental.intake.mapping'].sudo().search_count([
            ('ydental_store_id', '=', store.id), ('ydental_catalog_id.ydental_kind', '=', 'exam'),
            ('ydental_catalog_id.ydental_capability_id', '=', capability.id)]) if capability else 0
        if not capability or not capability.active or not mapped:
            raise AccessError(self.env._('source_required: Review a live examination capability mapped to this store.'))
        reason = self.env['ydental.intake.service']._text(reason)
        if len(reason) > 240:
            raise ValidationError(self.env._('invalid_reason: Keep the reviewed capability evidence within 240 characters.'))
        if capability.ydental_exam_family:
            if capability.ydental_exam_family != family:
                raise UserError(self.env._('history_immutable: The reviewed capability family cannot be silently changed.'))
            return {'capability_id': capability.id, 'family': family}
        capability.with_context(ydental_exam_profile_guard=PROFILE_GUARD).write({
            'ydental_exam_family': family, 'ydental_exam_review_actor_id': self.env.uid,
            'ydental_exam_reviewed_at': fields.Datetime.now(), 'ydental_exam_review_reason': reason})
        self.env['ydental.access.service']._audit('exam.capability_reviewed', 'exam', capability, store.id,
            after={'capability_id': capability.id, 'family': family}, reason=reason,
            source='examination_capability_review')
        return {'capability_id': capability.id, 'family': family}

    def _revalidate(self, line_id, execution_id, lease_id, lease_token, document_id, document_version, reason):
        treatment = self.env['ydental.treatment.service']
        execution, _document = treatment._medical(execution_id, lease_id, lease_token,
            document_id, document_version)
        line = treatment._get('line', line_id, 'medical')
        if line.ydental_order_id.ydental_kind != 'exam' or line.state != 'issued' or (
                line.ydental_patient_id != execution.ydental_patient_id or
                line.ydental_store_id != execution.ydental_store_id or
                line.ydental_task_id.state not in ('pending', 'accepted')):
            raise AccessError(self.env._('source_required: Revalidate only a real unfinished order line for this patient.'))
        reason = self.env['ydental.intake.service']._text(reason)
        today = self.env['ydental.supply.service']._date(line.ydental_store_id)
        if line.ydental_exam_validated_date != today:
            line._save({'ydental_exam_validated_date': today})
            self._audit('next_day_revalidated', line, {'date': str(today), 'execution_id': execution.id}, reason)
        return {'line_id': line.id, 'validated_date': str(today), 'state': line.state}

    def _audit(self, action, record, after=None, reason=False):
        self.env['ydental.access.service']._audit('exam.' + action, 'exam', record, record.ydental_store_id.id,
            after=after, reason=reason, source='examination_service')

    def _actual(self, line, execution_id, lease_id, lease_token, inline=False):
        self._store(write=True)
        treatment = self.env['ydental.treatment.service']
        queue = self.env['ydental.queue.service']
        execution = treatment._serving(execution_id, lease_id, lease_token, 'medical' if inline else 'exam')
        if execution.ydental_patient_id != line.ydental_patient_id or execution.ydental_store_id != line.ydental_store_id:
            raise AccessError(self.env._('source_required: The patient and examination source must match.'))
        if inline:
            if execution != line.ydental_order_id.ydental_execution_id or line.state not in ('issued', 'done', 'partial', 'aborted') or (
                    line.ydental_mapping_id.ydental_catalog_id.ydental_capability_id not in
                    execution.ydental_lease_id.ydental_station_id.ydental_capability_ids.filtered('active') or
                    line.ydental_mapping_id.ydental_catalog_id.ydental_capability_id not in
                    self.env.user.sudo().ydental_capability_ids.filtered('active')):
                raise AccessError(self.env._('qualification_required: Inline examination needs its original serving segment and exact capability.'))
            code = line.ydental_mapping_id.ydental_catalog_id.ydental_qualification
            if code and not self._qualification(code, line.ydental_store_id, self.env.uid):
                raise AccessError(self.env._('qualification_required: A reviewed live staff qualification is required.'))
        elif execution.ydental_task_id != line.ydental_task_id or line.state not in ('started', 'done', 'aborted', 'partial'):
            raise AccessError(self.env._('source_required: The real examination task must be serving.'))
        return execution

    def _qualification(self, code, store, user_id):
        now = fields.Datetime.now()
        return bool(self._model('qualification').search_count([
            ('ydental_code', '=', code), ('ydental_store_id', '=', store.id),
            ('ydental_user_id', '=', user_id), ('ydental_revoked', '=', False),
            ('ydental_valid_from', '<=', now), ('ydental_valid_until', '>', now)]))

    def _editor(self, result, version):
        session, connection = self.env['ydental.queue.service']._connection()
        if result.ydental_responsible_id.id != self.env.uid:
            raise AccessError(self.env._('responsibility_required: Take over this result with an explicit reason before editing.'))
        if type(version) is not int or result.ydental_version != version:
            raise UserError(self.env._('version_conflict: Refresh the examination result before editing.'))
        if result.ydental_current_editor_id and result.ydental_edit_until > fields.Datetime.now() and (
                result.ydental_current_editor_id.id != self.env.uid or result.ydental_edit_session_id != session or
                result.ydental_edit_revision != session.ydental_revision or
                not consteq(result.ydental_edit_connection_hash, connection.key_hash)):
            raise AccessError(self.env._('editor_busy: This result is held by another live editor.'))
        result._save({'ydental_current_editor_id': self.env.uid, 'ydental_edit_session_id': session.id,
            'ydental_edit_revision': session.ydental_revision, 'ydental_edit_connection_hash': connection.key_hash,
            'ydental_edit_until': fields.Datetime.now() + timedelta(minutes=5)})

    def _release_editor(self, line_id, version):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or result.ydental_responsible_id.id != self.env.uid or result.ydental_version != version:
            raise AccessError(self.env._('responsibility_required: Release only your current result version.'))
        session, connection = self.env['ydental.queue.service']._connection()
        if result.ydental_current_editor_id and (
                result.ydental_edit_session_id != session or
                not consteq(result.ydental_edit_connection_hash or '', connection.key_hash)):
            raise AccessError(self.env._('editor_busy: This result is held by another live editor.'))
        result._save({'ydental_current_editor_id': False, 'ydental_edit_session_id': False,
            'ydental_edit_revision': 0, 'ydental_edit_connection_hash': False, 'ydental_edit_until': False})
        self._audit('editor_released', result, {'version': version})
        return {'result_id': result.id, 'version': version, 'state': result.state}

    def _takeover(self, line_id, version, reason):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or result.ydental_version != version or result.ydental_responsible_id.id == self.env.uid:
            raise UserError(self.env._('version_conflict: Select another operator current result version.'))
        if result.ydental_current_editor_id and result.ydental_edit_until > fields.Datetime.now():
            raise AccessError(self.env._('editor_busy: The current editor must release or expire first.'))
        reason = self.env['ydental.intake.service']._text(reason)
        previous = result.ydental_responsible_id.id
        result._save({'ydental_responsible_id': self.env.uid,
            'ydental_current_editor_id': False, 'ydental_edit_session_id': False,
            'ydental_edit_revision': 0, 'ydental_edit_connection_hash': False, 'ydental_edit_until': False})
        self._audit('responsibility_taken', result, {'from_user_id': previous, 'to_user_id': self.env.uid}, reason)
        return {'result_id': result.id, 'version': version, 'state': result.state}

    def _content(self, findings, measurements, conclusion, template_code):
        if template_code not in TEMPLATES or not isinstance(findings, str) or len(findings) > 12000 or (
                not isinstance(conclusion, str) or len(conclusion) > 12000 or not isinstance(measurements, dict)):
            raise ValidationError(self.env._('invalid_result: Use a reviewed demonstration template and bounded text.'))
        allowed = TEMPLATES[template_code]['measurements']
        if set(measurements) - set(allowed):
            raise ValidationError(self.env._('invalid_result: Unknown measurement field.'))
        for key, row in measurements.items():
            if not isinstance(row, dict) or set(row) != {'status', 'value', 'unit'} or (
                    row['status'] not in ('known', 'unknown', 'not_applicable') or row['unit'] != allowed[key] or
                    row['status'] == 'known' and (type(row['value']) not in (int, float) or
                        row['value'] < 0 or row['value'] > 10000 or not math.isfinite(row['value'])) or
                    row['status'] != 'known' and row['value'] is not None):
                raise ValidationError(self.env._('invalid_result: Provide a value with its native unit, or explicit unknown/not applicable.'))
        return findings.strip(), measurements, conclusion.strip()

    def _version(self, result, kind, reason=''):
        previous = self._model('version').search([('ydental_result_id', '=', result.id)], order='ydental_number desc', limit=1)
        version = self._model('version')._new({'name': result.name, 'ydental_store_id': result.ydental_store_id.id,
            'ydental_category': 'exam', 'ydental_patient_id': result.ydental_patient_id.id, 'ydental_actor_id': self.env.uid,
            'ydental_result_id': result.id, 'ydental_number': result.ydental_version,
            'ydental_kind': kind, 'ydental_findings': result.ydental_findings,
            'ydental_measurements': result.ydental_measurements, 'ydental_conclusion': result.ydental_conclusion,
            'ydental_reason': reason, 'ydental_recorded_at': fields.Datetime.now(),
            'ydental_previous_id': previous.id if previous else False})
        self._audit(kind, version, {'result_id': result.id, 'version': result.ydental_version}, reason)
        return version

    def _grant_qualification(self, user_id, code, valid_from, valid_until, evidence):
        access = self.env['ydental.access.service']
        store = access._scope(write=True).ydental_store_id
        access._check_personnel(store.id, user_id)
        user = self.env['res.users'].sudo().browse(self.env['ydental.intake.service']._id(user_id)).exists()
        member = access._membership(user.id, store.id) if user else False
        if not user or not user.active or not member or not member.ydental_employee_id.active or user.id == self.env.uid:
            raise AccessError(self.env._('access_denied: A different active store employee is required.'))
        if not isinstance(code, str) or not code.strip() or len(code) > 120 or not isinstance(evidence, str) or not evidence.strip():
            raise ValidationError(self.env._('qualification_required: Record an exact qualification code and reviewed evidence.'))
        start, end = fields.Datetime.to_datetime(valid_from), fields.Datetime.to_datetime(valid_until)
        if not start or not end or end <= start:
            raise ValidationError(self.env._('invalid_time: Qualification validity must have ordered UTC bounds.'))
        row = self._model('qualification')._new({'name': code, 'ydental_store_id': store.id, 'ydental_category': 'exam',
            'ydental_patient_id': False, 'ydental_actor_id': self.env.uid, 'ydental_user_id': user.id,
            'ydental_code': code.strip(), 'ydental_valid_from': start, 'ydental_valid_until': end,
            'ydental_evidence': evidence.strip()[:240]})
        self._audit('qualification_granted', row, {'user_id': user.id, 'code': code.strip()})
        return {'qualification_id': row.id}

    def _draft(self, line_id, execution_id, lease_id, lease_token, inline, version, findings, measurements, conclusion):
        line = self._line(line_id, write=True)
        execution = self._actual(line, execution_id, lease_id, lease_token, inline)
        result = self._result(line, create=True, execution=execution)
        if result.state in ('confirmed', 'aborted'):
            raise UserError(self.env._('version_conflict: A confirmed or aborted result needs its own controlled action.'))
        self._editor(result, version)
        if not isinstance(measurements, dict):
            raise ValidationError(self.env._('invalid_result: Measurement updates must be a field map.'))
        findings, measurements, conclusion = self._content(findings,
            dict(result.ydental_measurements or {}) | measurements, conclusion, result.ydental_template_code)
        result._save({'ydental_findings': findings, 'ydental_measurements': measurements,
            'ydental_conclusion': conclusion, 'ydental_version': version + 1})
        self._version(result, 'draft')
        return {'result_id': result.id, 'version': result.ydental_version, 'state': result.state}

    def _perform(self, line_id, execution_id, lease_id, lease_token, inline, reason, materials, actual_at=None):
        line = self._line(line_id, write=True)
        execution = self._actual(line, execution_id, lease_id, lease_token, inline)
        if line.state not in ('issued', 'started') or self._model('result').search([('ydental_line_id', '=', line.id), ('ydental_event_id', '!=', False)], limit=1):
            raise UserError(self.env._('already_started: This line already has an actual execution fact.'))
        result = self._result(line, create=True, execution=execution)
        if result.state not in ('draft', 'started'):
            raise UserError(self.env._('version_conflict: This result cannot be performed again.'))
        catalog = line.ydental_mapping_id.ydental_catalog_id
        event = self.env['ydental.treatment.service']._event(execution, catalog, line.ydental_quantity,
            's09-exam-line-' + str(line.id), reason, materials, already_performed=True,
            kind='exam', line=line, actual_at=actual_at)
        result._save({'ydental_execution_id': execution.id, 'ydental_event_id': event['event_id'],
            'ydental_started_at': fields.Datetime.now(), 'ydental_business_date': self.env['ydental.supply.service']._date(line.ydental_store_id),
            'ydental_station_id': execution.ydental_lease_id.ydental_station_id.id, 'state': 'pending'})
        line._save({'state': 'done'})
        response = dict(event, result_id=result.id, line_id=line.id,
            event_state=event['state'], result_document_state=result.state,
            order_line_state=line.state, fee_source_state='recorded' if event['fee_id'] else 'absent')
        self._audit('actual_performed', result, response, reason)
        return response

    def _confirm(self, line_id, version, reason):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or not result.ydental_event_id or result.state not in ('pending', 'partial') or not result.ydental_findings:
            raise UserError(self.env._('result_required: Actual execution and reviewed findings are required.'))
        self._editor(result, version)
        reason = self.env['ydental.intake.service']._text(reason)
        result._save({'state': 'confirmed', 'ydental_completed_at': fields.Datetime.now(), 'ydental_version': version + 1})
        self._version(result, 'confirm', reason)
        return {'result_id': result.id, 'version': result.ydental_version, 'state': result.state}

    def _correct(self, line_id, version, findings, measurements, conclusion, reason):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or result.state != 'confirmed':
            raise UserError(self.env._('result_required: Correct only a confirmed result.'))
        self._editor(result, version)
        reason = self.env['ydental.intake.service']._text(reason)
        if not isinstance(measurements, dict):
            raise ValidationError(self.env._('invalid_result: Measurement updates must be a field map.'))
        findings, measurements, conclusion = self._content(findings,
            dict(result.ydental_measurements or {}) | measurements, conclusion, result.ydental_template_code)
        if not findings:
            raise ValidationError(self.env._('result_required: Confirmed findings cannot be blank.'))
        result._save({'ydental_findings': findings, 'ydental_measurements': measurements,
            'ydental_conclusion': conclusion, 'ydental_version': version + 1})
        self._version(result, 'correction', reason)
        return {'result_id': result.id, 'version': result.ydental_version, 'state': result.state}

    def _abort(self, line_id, execution_id, lease_id, lease_token, reason, inline=False):
        line = self._line(line_id, write=True)
        execution = self._actual(line, execution_id, lease_id, lease_token, inline)
        reason = self.env['ydental.intake.service']._text(reason)
        result = self._result(line, create=True, execution=execution)
        if result.state in ('aborted', 'partial', 'confirmed'):
            raise UserError(self.env._('version_conflict: This actual examination is already resolved.'))
        if result.ydental_event_id:
            result._save({'state': 'partial', 'ydental_completed_at': fields.Datetime.now()})
            line._save({'state': 'partial'})
            state = 'partial'
        else:
            result._save({'state': 'aborted', 'ydental_started_at': execution.ydental_started_at,
                'ydental_completed_at': fields.Datetime.now()})
            line._save({'state': 'aborted'})
            state = 'aborted'
        self._audit('actual_aborted', result, {'state': state, 'execution_id': execution.id}, reason)
        return {'result_id': result.id, 'state': state}

    def _finish(self, line_id, execution_id, lease_id, lease_token, reason, inline=False):
        line = self._line(line_id, write=True)
        execution = self._actual(line, execution_id, lease_id, lease_token, inline)
        result = self._result(line)
        if line.state not in ('done', 'aborted', 'partial') or not result:
            raise UserError(self.env._('reconcile_required: Resolve the actual examination fact before leaving.'))
        event = result.ydental_event_id
        pending = bool(event and event.state == 'pending' and event.ydental_already_performed and
            event.ydental_pending_reason and event.ydental_order_line_id == line and
            event.ydental_execution_id == execution and event.ydental_store_id == line.ydental_store_id)
        if event and event.state != 'confirmed' and not pending:
            raise UserError(self.env._('reconcile_required: Resolve the actual examination fact before leaving.'))
        reason = self.env['ydental.intake.service']._text(reason)
        if pending:
            self._audit('pending_departure', result, {'event_id': event.id,
                'pending_reason': event.ydental_pending_reason, 'original_actor_id': event.ydental_actor_id.id,
                'actual_at': str(event.ydental_actual_at), 'execution_id': execution.id}, reason)
        if inline:
            self._audit('inline_exam_resolved', result, {'execution_id': execution.id,
                'line_id': line.id, 'pending_event_id': event.id if pending else False}, reason)
            return {'execution_id': execution.id, 'state': 'medical_continues_pending_reconciliation' if pending else 'medical_continues',
                'line_id': line.id, 'pending_event_id': event.id if pending else False}
        queue = self.env['ydental.queue.service']
        queue._finish_exam_segment(execution, reason)
        queue._exit(lease_id, lease_token)
        return {'execution_id': execution.id, 'state': 'completed_pending_reconciliation' if pending else 'completed',
            'line_id': line.id, 'pending_event_id': event.id if pending else False}

    def _reconcile(self, line_id, reason):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or not result.ydental_event_id or result.ydental_event_id.ydental_actor_id.id != self.env.uid:
            raise AccessError(self.env._('access_denied: Only the original examination operator may reconcile this fact.'))
        reason = self.env['ydental.intake.service']._text(reason)
        event = result.ydental_event_id
        self.env['ydental.treatment.service']._bookkeep(event)
        response = self.env['ydental.treatment.service']._event_result(event)
        self._audit('reconciled', result, response, reason)
        return response

    def _verify_materials(self, line_id, materials, reason):
        line = self._line(line_id, write=True)
        result = self._result(line)
        event = result.ydental_event_id if result else False
        if not event or event.ydental_actor_id.id != self.env.uid or event.ydental_order_line_id != line or (
                not event.ydental_already_performed or event.state != 'pending' or
                event.ydental_pending_reason != 'material_evidence_missing'):
            raise AccessError(self.env._('source_required: Only the original operator may verify missing material evidence for this actual examination.'))
        reason = self.env['ydental.intake.service']._text(reason)
        treatment = self.env['ydental.treatment.service']
        rows = treatment._material_rows(materials, 'exam', line.ydental_store_id)
        if not rows or treatment._model('consumption').search_count([('ydental_event_id', '=', event.id)]):
            raise UserError(self.env._('material_evidence_missing: Supply each real physical batch exactly once.'))
        for row in rows:
            treatment._new('consumption', event, {'name': event.ydental_source,
                'ydental_event_id': event.id, 'ydental_lot_id': row['lot_id'],
                'ydental_quantity': row['quantity'], 'ydental_uom_id': row['uom_id'],
                'ydental_kind': row['kind']})
        event._save({'ydental_exam_material_review': reason,
            'ydental_exam_material_verified_at': fields.Datetime.now(), 'ydental_pending_reason': False})
        treatment._bookkeep(event)
        response = treatment._event_result(event)
        self._audit('materials_verified', result, {'event_id': event.id,
            'reported_materials': rows, 'event_state': event.state}, reason)
        return response

    def _operate(self, operation, payload, key):
        handlers = {'grant_qualification': self._grant_qualification,
            'review_capability': self._review_capability,
            'bind_template': self._bind_template, 'revalidate': self._revalidate,
            'release_editor': self._release_editor, 'takeover': self._takeover,
            'draft': self._draft,
            'perform': self._perform, 'confirm': self._confirm, 'correct': self._correct,
            'abort': self._abort, 'finish': self._finish, 'reconcile': self._reconcile,
            'verify_materials': self._verify_materials,
            'attach': self._attachment}
        if operation not in handlers or not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 120:
            raise ValidationError(self.env._('invalid_action: Select a documented examination action and stable key.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_action: Unknown or missing examination arguments.')) from error
        queue = self.env['ydental.queue.service']
        if operation not in ('grant_qualification', 'bind_template', 'review_capability'):
            if operation == 'revalidate':
                self.env['ydental.access.service']._check('medical', 'write', write=True)
            else:
                self._store(write=True)
            queue._connection()
        digest = fingerprint([operation, payload])
        with self.env.cr.savepoint():
            queue._locks()
            self.env['ydental.inventory.service']._lock()
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [32008])
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [33009])
            if operation not in ('grant_qualification', 'bind_template', 'review_capability'):
                if operation == 'revalidate':
                    self.env['ydental.access.service']._check('medical', 'write', write=True)
                else:
                    self._store(write=True)
                queue._connection()
            prior = self._model('receipt').search([('ydental_actor_id', '=', self.env.uid), ('ydental_key', '=', key)], limit=1)
            if prior:
                if prior.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: This examination key belongs to another action.'))
                return dict(prior.ydental_result, result='already_accepted')
            response = handlers[operation](**payload)
            store = self.env['ydental.access.service']._scope().ydental_store_id
            self._model('receipt')._new({'name': operation, 'ydental_store_id': store.id, 'ydental_category': 'exam',
                'ydental_patient_id': False, 'ydental_actor_id': self.env.uid,
                'ydental_key': key, 'ydental_fingerprint': digest, 'ydental_result': response})
            return dict(response, result='accepted')

    def _view(self, line_id):
        line = self._line(line_id)
        result = self._result(line)
        versions = self._model('version').search([('ydental_result_id', '=', result.id)], order='ydental_number') if result else []
        self._audit('view', line, {'result_id': result.id if result else 0})
        return {'line_id': line.id, 'line_state': line.state, 'result_id': result.id if result else 0,
            'result_state': result.state if result else 'unwritten', 'version': result.ydental_version if result else 0,
            'template': result.ydental_template_code if result else '', 'findings': result.ydental_findings if result else '',
            'conclusion': result.ydental_conclusion if result else '',
            'measurements': result.ydental_measurements if result else {},
            'versions': [{'number': v.ydental_number, 'kind': v.ydental_kind, 'author': v.ydental_actor_id.name,
                          'recorded_at': str(v.ydental_recorded_at), 'reason': v.ydental_reason or ''} for v in versions]}

    def _attachment(self, line_id, version, filename, mimetype, encoded):
        line = self._line(line_id, write=True)
        result = self._result(line)
        if not result or result.ydental_version != version or result.state in ('aborted', 'confirmed'):
            raise UserError(self.env._('version_conflict: Save a current editable result before attaching evidence.'))
        self._editor(result, version)
        if not isinstance(filename, str) or not 1 <= len(filename) <= 120 or '/' in filename or '\\' in filename or (
                mimetype not in ('image/jpeg', 'image/png', 'application/pdf') or not isinstance(encoded, str)):
            raise ValidationError(self.env._('invalid_attachment: Select a bounded JPEG, PNG or PDF evidence file.'))
        try:
            binary = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError, binascii.Error) as error:
            raise ValidationError(self.env._('invalid_attachment: Invalid file encoding.')) from error
        if not 1 <= len(binary) <= 5000000 or not (binary.startswith(b'\xff\xd8') if mimetype == 'image/jpeg' else
                binary.startswith(b'\x89PNG\r\n\x1a\n') if mimetype == 'image/png' else binary.startswith(b'%PDF-')):
            raise ValidationError(self.env._('invalid_attachment: File signature or size is invalid.'))
        record = self.env['ir.attachment'].sudo().create({'name': filename, 'type': 'binary',
            'raw': binary, 'mimetype': mimetype, 'res_model': 'ydental.exam.result', 'res_id': result.id,
            'public': False})
        self._audit('attachment_added', result, {'attachment_id': record.id,
            'sha256': hashlib.sha256(binary).hexdigest()})
        return {'attachment_id': record.id, 'sha256': hashlib.sha256(binary).hexdigest()}

    def _attachment_download(self, line_id, attachment_id):
        line = self._line(line_id)
        result = self._result(line)
        record = self.env['ir.attachment'].sudo().browse(self.env['ydental.intake.service']._id(attachment_id)).exists()
        if not result or not record or record.res_model != 'ydental.exam.result' or record.res_id != result.id or record.public:
            raise AccessError(self.env._('access_denied: This examination attachment is unavailable.'))
        self.env['ydental.access.service']._check('export', 'write')
        raw = bytes(record.raw)
        self._audit('attachment_download', result, {'attachment_id': record.id,
            'sha256': hashlib.sha256(raw).hexdigest()})
        return raw, record.mimetype, record.name

    def _pdf_payload(self, line_id, version):
        line = self._line(line_id)
        result = self._result(line)
        if not result or type(version) is not int or version < 1:
            raise AccessError(self.env._('access_denied: A saved examination result is required.'))
        selected = self._model('version').search([('ydental_result_id', '=', result.id),
            ('ydental_number', '=', version)], limit=1)
        if not selected:
            raise UserError(self.env._('version_conflict: The requested result version is unavailable.'))
        self.env['ydental.access.service']._check('export', 'write')
        event = result.ydental_event_id
        patient = self.env['ydental.patient.service']._patient(line.ydental_patient_id.id)
        measurements = selected.ydental_measurements or {}
        payload = {'result_id': result.id, 'line_id': line.id, 'version': version,
            'patient_number': patient.ydental_number, 'store': line.ydental_store_id.name,
            'catalog': line.ydental_mapping_id.ydental_catalog_id.name,
            'template_version': result.ydental_template_version,
            'original_author': result.ydental_original_author_id.name,
            'version_author': selected.ydental_actor_id.name,
            'operator': event.ydental_actor_id.name if event else '',
            'station': result.ydental_station_id.name if result.ydental_station_id else '',
            'actual_at': str(event.ydental_actual_at) if event else '',
            'business_date': str(event.ydental_business_date) if event else '',
            'event_id': event.id if event else 0,
            'state': {'draft': '草稿', 'confirm': '已确认', 'correction': '已更正'}[selected.ydental_kind],
            'findings': selected.ydental_findings or '', 'conclusion': selected.ydental_conclusion or '',
            'measurements': [{'name': k, 'value': v['value'] if v['value'] is not None else '',
                'unit': v['unit'], 'status': v['status']} for k, v in sorted(measurements.items())]}
        return result, payload

    def _validate_pdf_scope(self):
        scope = self.env.context.get('ydental_exam_pdf_scope')
        session = self.env['ydental.access.service']._scope()
        if type(scope) is not ExamPdfScope or (scope.actor_id, scope.session_id, scope.revision) != (
                self.env.uid, session.id, session.ydental_revision):
            raise AccessError(self.env._('access_denied: A controlled examination report request is required.'))
        result = self._model('result').browse(scope.result_id).exists()
        if not result:
            raise AccessError(self.env._('access_denied: Examination result is unavailable.'))
        source, payload = self._pdf_payload(result.ydental_line_id.id, scope.version)
        if fingerprint(payload) != scope.digest:
            raise UserError(self.env._('version_conflict: Report source changed during rendering.'))
        return payload

    def _pdf(self, line_id, version):
        result, payload = self._pdf_payload(line_id, version)
        session = self.env['ydental.access.service']._scope()
        scope = ExamPdfScope(self.env.uid, session.id, session.ydental_revision,
                             result.id, version, fingerprint(payload))
        reports = self.env['ir.actions.report'].with_context(
            ydental_exam_pdf_scope=scope, lang='zh_CN', force_report_rendering=True,
            report_pdf_no_attachment=True)
        try:
            pdf, kind = reports._render_qweb_pdf('ydental_exam.ydental_exam_pdf', [result.id])
            if kind != 'pdf' or not isinstance(pdf, bytes) or not pdf.startswith(b'%PDF-') or len(pdf) > 10000000 or (
                    len(PdfFileReader(io.BytesIO(pdf)).pages) > 20):
                raise UserError(self.env._('render_failed: The examination PDF is invalid or exceeds the page limit.'))
        except (QWebError, PdfReadError, OSError, ValueError) as error:
            raise UserError(self.env._('render_failed: The examination PDF could not be generated.')) from error
        digest = hashlib.sha256(pdf).hexdigest()
        self._audit('report_download', result, {'version': version, 'pdf_sha256': digest})
        return pdf, digest
