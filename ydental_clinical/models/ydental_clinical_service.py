import hashlib
import inspect
import json
import secrets
from dataclasses import dataclass
from datetime import timedelta

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import consteq


TEXT_FIELDS = ('chief_complaint', 'history', 'findings', 'diagnosis', 'treatment_plan', 'suggested_materials', 'follow_up')
TEETH = tuple(q * 10 + n for q in range(1, 9) for n in range(1, 9 if q < 5 else 6))


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class DocumentLock:
    document_id: int
    token: str
    lease_id: int | None = None
    lease_token: str | None = None


@dataclass(frozen=True)
class SaveIntent:
    actor_id: int
    execution_id: int
    document_id: int
    version: int


class YDentalClinicalService(models.AbstractModel):
    _name = 'ydental.clinical.service'
    _description = 'Clinical text authorization and version transactions'

    def _queue(self):
        return self.env['ydental.queue.service']

    def _model(self, name='document'):
        # Only fixed server-selected clinical entities; never accepts a public model name.
        return self.env['ydental.clinical.' + name].sudo()

    def _audit(self, event, doc, before=None, after=None, reason=False):
        access = self.env['ydental.access.service']
        return access._audit('clinical.' + event, 'medical', doc, access._scope().ydental_store_id.id,
                             before=before, after=after, reason=reason, source='clinical_document')

    def _access(self, write=False):
        return self.env['ydental.access.service']._check('medical', 'write' if write else 'read', write=write).ydental_store_id

    def _document(self, document_id, write=False):
        store = self._access(write)
        doc = self._model().browse(self.env['ydental.intake.service']._id(document_id)).exists()
        if not doc:
            raise AccessError(self.env._('access_denied: This clinical document is unavailable.'))
        if write and doc.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Write clinical text only in its source store.'))
        if not write:
            self.env['ydental.clinical.document'].browse(doc.id).check_access('read')
        self.env['ydental.patient.service']._current_relation(doc.ydental_patient_id, store)
        return doc

    def _content(self, content):
        if not isinstance(content, dict) or set(content) != set(TEXT_FIELDS) | {'teeth'}:
            raise ValidationError(self.env._('invalid_content: Submit the complete clinical draft field set.'))
        result = {}
        for name in TEXT_FIELDS:
            text = content[name]
            if not isinstance(text, str) or len(text) > 10000:
                raise ValidationError(self.env._('invalid_content: Clinical text exceeds its allowed size.'))
            result[name] = text
        teeth = content['teeth']
        if not isinstance(teeth, list) or len(teeth) > 53:
            raise ValidationError(self.env._('invalid_tooth: Invalid FDI tooth collection.'))
        seen = set()
        rows = []
        for row in teeth:
            if not isinstance(row, dict) or set(row) != {'tooth', 'state', 'surfaces'}:
                raise ValidationError(self.env._('invalid_tooth: Supply tooth, state and surfaces.'))
            tooth, state, surfaces = row['tooth'], row['state'], row['surfaces']
            if type(tooth) is not int or tooth not in (0,) + TEETH or tooth in seen or state not in ('present', 'missing', 'unknown', 'not_applicable'):
                raise ValidationError(self.env._('invalid_tooth: Select a valid distinct FDI tooth and explicit state.'))
            if not isinstance(surfaces, list) or any(not isinstance(s, str) for s in surfaces) or len(set(surfaces)) != len(surfaces):
                raise ValidationError(self.env._('invalid_surface: Select distinct legal tooth surfaces.'))
            allowed = {'M', 'D', 'B', 'L', 'I' if tooth % 10 <= 3 else 'O'}
            if (tooth == 0 and state != 'not_applicable') or (tooth != 0 and state == 'not_applicable') or (state != 'present' and surfaces) or not set(surfaces) <= allowed:
                raise ValidationError(self.env._('invalid_surface: Surfaces must match the tooth and its recorded state.'))
            seen.add(tooth)
            rows.append({'tooth': tooth, 'state': state, 'surfaces': sorted(surfaces)})
        result['teeth'] = sorted(rows, key=lambda row: row['tooth'])
        return result

    def _empty(self):
        return dict.fromkeys(TEXT_FIELDS, '') | {'teeth': []}

    def _operate(self, operation, payload):
        handlers = {'open': self._open, 'acquire': self._acquire, 'heartbeat': self._heartbeat,
                    'release': self._release, 'save': self._save, 'confirm': self._confirm,
                    'correct': self._correct, 'handover': self._handover, 'transfer': self._transfer}
        if operation not in handlers or not isinstance(payload, dict):
            raise ValidationError(self.env._('invalid_action: Unknown clinical document action.'))
        try:
            inspect.signature(handlers[operation]).bind(**payload)
        except TypeError as error:
            raise ValidationError(self.env._('invalid_action: Unknown or missing clinical arguments.')) from error
        self._access(write=True)
        self._queue()._connection()
        with self.env.cr.savepoint():
            # Preserve S06 lock order. The common queue fence also serializes CAS,
            # document locks and handover with patient/permission transactions.
            self._queue()._locks()
            self._access(write=True)
            return handlers[operation](**payload) | {'result': 'accepted'}

    def _open(self, execution_id, lease_id, lease_token):
        queue = self._queue()
        lease = queue._held(lease_id, lease_token)
        execution = queue._source_execution(execution_id, lease)
        if execution.state != 'serving' or lease.ydental_category != 'medical' or lease.ydental_expires_at <= queue._now():
            raise AccessError(self.env._('access_denied: Start the real medical reception before creating its document.'))
        self.env['ydental.patient.service']._current_relation(execution.ydental_patient_id, self._access(True))
        doc = self._model().search([('ydental_current_execution_id', '=', execution.id)], limit=1)
        if not doc:
            doc = self._model()._new({'name': execution.name, 'ydental_store_id': execution.ydental_store_id.id,
                'ydental_patient_id': execution.ydental_patient_id.id, 'ydental_execution_id': execution.id,
                'ydental_current_execution_id': execution.id,
                'ydental_author_id': self.env.uid, 'ydental_responsible_id': self.env.uid,
                'ydental_content': self._empty()})
            self._audit('create', doc)
        return self._acquire(doc.id, lease_id, lease_token)

    def _eligible_responsible(self, doc, user):
        access = self.env['ydental.access.service']
        member = access._membership(user.id, doc.ydental_store_id.id)
        snapshot = doc.ydental_current_execution_id.ydental_service_snapshot
        return bool(user.active and doc.ydental_store_id.company_id in user.company_ids and member and
            member.ydental_employee_id.active and access._levels(member)['medical'] == 'write' and
            snapshot['capability_id'] in user.ydental_capability_ids.filtered('active').ids and
            (not snapshot['qualification'] or self._queue()._qualification_satisfied(
                doc.ydental_current_execution_id.ydental_task_id, doc.ydental_current_execution_id.ydental_lease_id.ydental_station_id, user)))

    def _valid_editor(self, doc):
        queue = self._queue()
        if not doc.ydental_editor_id or not doc.ydental_editor_expires or doc.ydental_editor_expires <= queue._now():
            return False
        session = doc.ydental_session_id
        if not session or session.ydental_revision != doc.ydental_session_revision or session.ydental_store_id != doc.ydental_store_id or not self._eligible_responsible(doc, doc.ydental_editor_id):
            return False
        lease = doc.ydental_editor_lease_id
        if lease and (not lease.ydental_active or lease.ydental_expires_at <= queue._now() or
                      lease.ydental_revision != session.ydental_revision or lease.ydental_session_id != session or
                      self._queue()._service_eligibility(self._queue()._execution_entry(doc.ydental_current_execution_id),
                          lease.ydental_station_id, doc.ydental_editor_id)):
            return False
        return True

    def _acquire(self, document_id, lease_id=None, lease_token=None):
        doc = self._document(document_id, True)
        queue = self._queue()
        session, connection = queue._connection()
        execution = doc.ydental_current_execution_id
        if execution.state in ('serving', 'reserved', 'verify'):
            lease = queue._held(lease_id, lease_token)
            if execution.state == 'verify' or execution.ydental_lease_id != lease or lease.ydental_expires_at <= queue._now():
                raise AccessError(self.env._('access_denied: The current reception holder must edit this document.'))
        else:
            lease = queue._model('lease')
            if doc.ydental_responsible_id.id != self.env.uid or not self._eligible_responsible(doc, self.env.user.sudo()):
                raise AccessError(self.env._('access_denied: Only the authorized responsible person may complete this document.'))
        if self._valid_editor(doc):
            raise UserError(self.env._('editor_busy: This independent document already has a connected editor.'))
        if doc.ydental_editor_id:
            self._audit('editor_invalidated', doc, after={'previous_editor_id': doc.ydental_editor_id.id})
        token = secrets.token_urlsafe(32)
        doc._save({'ydental_editor_id': self.env.uid, 'ydental_session_id': session.id,
            'ydental_session_revision': session.ydental_revision, 'ydental_connection_hash': connection.key_hash,
            'ydental_editor_hash': digest(token), 'ydental_editor_lease_id': lease.id,
            'ydental_editor_expires': queue._now() + timedelta(seconds=queue._settings()[1])})
        self._audit('edit_acquire', doc)
        return self._snapshot(doc) | {'editor_token': token}

    def _held(self, document_id, editor_token):
        doc = self._document(document_id, True)
        session, connection = self._queue()._connection()
        if not self._valid_editor(doc) or doc.ydental_editor_id.id != self.env.uid or doc.ydental_session_id != session or not consteq(doc.ydental_connection_hash, connection.key_hash) or not isinstance(editor_token, str) or len(editor_token) > 128 or not consteq(doc.ydental_editor_hash, digest(editor_token)):
            raise AccessError(self.env._('editor_expired: This connection no longer holds the document.'))
        return doc

    def _heartbeat(self, document_id, editor_token):
        doc = self._held(document_id, editor_token)
        doc._save({'ydental_editor_expires': self._queue()._now() + timedelta(seconds=self._queue()._settings()[1])})
        return {'document_id': doc.id, 'version': doc.ydental_version}

    def _clear_editor(self, doc):
        doc._save({'ydental_editor_id': False, 'ydental_session_id': False, 'ydental_session_revision': 0,
            'ydental_connection_hash': False, 'ydental_editor_hash': False, 'ydental_editor_expires': False,
            'ydental_editor_lease_id': False})

    def _release(self, document_id, editor_token):
        doc = self._held(document_id, editor_token)
        self._clear_editor(doc)
        self._audit('edit_release', doc)
        return {'document_id': doc.id}

    def _append(self, doc, expected_version, content, key, kind, reason=''):
        if type(expected_version) is not int or expected_version < 0 or not isinstance(key, str) or not 16 <= len(key) <= 128:
            raise ValidationError(self.env._('invalid_version: Supply a server version and stable request key.'))
        content = self._content(content)
        signature = digest(json.dumps([expected_version, content, kind, reason], sort_keys=True, ensure_ascii=False))
        versions = self._model('version')
        prior = versions.search([('ydental_document_id', '=', doc.id), ('ydental_request_key', '=', key)], limit=1)
        if prior:
            if prior.ydental_request_digest != signature or prior.ydental_author_id.id != self.env.uid:
                raise UserError(self.env._('version_conflict: This request key belongs to different content.'))
            return self._snapshot(doc) | {'saved_version': prior.ydental_number, 'duplicate': True}
        if doc.ydental_version != expected_version:
            raise UserError(self.env._('version_conflict: Refresh before editing a newer clinical version.'))
        if kind == 'save' and doc.state == 'confirmed' or kind == 'correct' and doc.state != 'confirmed':
            raise UserError(self.env._('correction_required: Confirmed text requires a new correction and reason.'))
        if kind in ('confirm', 'correct') and not any(content[name].strip() for name in TEXT_FIELDS) and not content['teeth']:
            raise ValidationError(self.env._('content_required: Empty clinical text cannot be confirmed.'))
        previous = versions.search([('ydental_document_id', '=', doc.id)], order='ydental_number desc', limit=1)
        now = self._queue()._now()
        version = versions._new({'ydental_store_id': doc.ydental_store_id.id, 'ydental_document_id': doc.id,
            'ydental_patient_id': doc.ydental_patient_id.id, 'ydental_number': expected_version + 1,
            'ydental_content': content, 'ydental_author_id': self.env.uid, 'ydental_recorded_at': now,
            'ydental_kind': kind, 'ydental_reason': reason, 'ydental_previous_id': previous.id,
            'ydental_request_key': key, 'ydental_request_digest': signature, 'ydental_template': doc.ydental_template})
        doc._save({'ydental_version': version.ydental_number, 'ydental_content': content, 'ydental_saved_at': now,
                   **({'state': 'confirmed'} if kind in ('confirm', 'correct') else {})})
        self._audit(kind, doc, before={'version': expected_version}, after={'version': version.ydental_number}, reason=reason)
        return self._snapshot(doc) | {'saved_version': version.ydental_number}

    def _save(self, document_id, editor_token, expected_version, content, key):
        return self._append(self._held(document_id, editor_token), expected_version, content, key, 'save')

    def _confirm(self, document_id, editor_token, expected_version, content, key):
        doc = self._held(document_id, editor_token)
        return self._append(doc, expected_version, content, key, 'confirm')

    def _correct(self, document_id, editor_token, expected_version, content, key, reason):
        reason = self.env['ydental.intake.service']._text(reason)
        return self._append(self._held(document_id, editor_token), expected_version, content, key, 'correct', reason)

    def _handover(self, document_id, editor_token, expected_version, content, key, lease_id, lease_token, mapping_id=None, reason=''):
        doc = self._held(document_id, editor_token)
        if doc.ydental_current_execution_id.ydental_lease_id.id != lease_id:
            raise AccessError(self.env._('access_denied: Handover must use the original reception.'))
        if doc.state == 'confirmed':
            if doc.ydental_version != expected_version or self._content(content) != doc.ydental_content:
                raise UserError(self.env._('version_conflict: Confirmed text must be synchronized before handover.'))
        else:
            self._append(doc, expected_version, content, key, 'save')
        intent = SaveIntent(self.env.uid, doc.ydental_current_execution_id.id, doc.id, doc.ydental_version)
        return self._queue().with_context(ydental_clinical_save=intent)._operate('handover', {
            'lease_id': lease_id, 'token': lease_token, 'execution_id': doc.ydental_current_execution_id.id,
            'mapping_id': mapping_id, 'reason': reason}) | {'document_id': doc.id, 'version': doc.ydental_version}

    def _transfer(self, document_id, expected_version, user_id, reason):
        doc = self._document(document_id, True)
        member = self.env['ydental.access.service']._membership(self.env.uid, doc.ydental_store_id.id)
        if doc.ydental_current_execution_id.state not in ('handover', 'interrupted') or doc.ydental_version != expected_version or (
                doc.ydental_responsible_id.id != self.env.uid and not member.ydental_is_manager):
            raise AccessError(self.env._('access_denied: Only its responsible person or store manager may transfer pending text.'))
        if self._valid_editor(doc):
            raise UserError(self.env._('editor_busy: Release the valid editor before responsibility transfer.'))
        user = self.env['res.users'].sudo().browse(self.env['ydental.intake.service']._id(user_id)).exists()
        if not user or not self._eligible_responsible(doc, user):
            raise AccessError(self.env._('access_denied: The new responsible person needs current medical write and source qualifications.'))
        reason = self.env['ydental.intake.service']._text(reason)
        previous = doc.ydental_responsible_id.id
        self._clear_editor(doc)
        doc._save({'ydental_responsible_id': user.id})
        self._audit('responsibility_transfer', doc, before={'user_id': previous}, after={'user_id': user.id}, reason=reason)
        return self._snapshot(doc)

    def _snapshot(self, doc):
        return {'document_id': doc.id, 'execution_id': doc.ydental_current_execution_id.id, 'source_execution_id': doc.ydental_execution_id.id, 'version': doc.ydental_version,
            'state': doc.state, 'content': doc.ydental_content, 'template': doc.ydental_template,
            'saved_at': fields.Datetime.to_string(doc.ydental_saved_at) if doc.ydental_saved_at else False,
            'responsible_id': doc.ydental_responsible_id.id}

    def _read(self, document_id, purpose=None):
        if purpose:
            preliminary = self._model().browse(self.env['ydental.intake.service']._id(document_id)).exists()
            if not preliminary:
                raise AccessError(self.env._('access_denied: This clinical document is unavailable.'))
            self = self.env['ydental.access.service']._patient_care(preliminary.ydental_patient_id.id, purpose).env[self._name]
        doc = self._document(document_id)
        self._audit('view', doc)
        return self._snapshot(doc)
