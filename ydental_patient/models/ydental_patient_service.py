import hashlib
import json
import re
from datetime import timezone
from zoneinfo import ZoneInfo

import phonenumbers

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalPatientService(models.AbstractModel):
    _name = 'ydental.patient.service'
    _description = 'Patient identity, arrival, policy and atomic merge service'

    def _access(self, write=False):
        access = self.env['ydental.access.service']
        session = access._scope(write=write)
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        categories = ('patient', 'frontdesk') if write else ('patient', 'frontdesk', 'medical', 'exam')
        level = 'write' if write else 'read'
        if not member or not any(
            access._levels(member)[category] in (('write',) if write else ('read', 'write'))
            for category in categories
        ):
            raise AccessError(self.env._('access_denied: Patient administration permission is required.'))
        # Reuse live membership, employee, execution and store checks from S01.
        for category in categories:
            if access._levels(member)[category] in (('write',) if write else ('read', 'write')):
                access._check(category, level, write=write)
                break
        return session.ydental_store_id

    def _group(self):
        self._access(write=True)
        if not self.env['ydental.access.service']._is_group_manager():
            raise AccessError(self.env._('access_denied: Group identity verification is required.'))

    def _lock(self):
        # Advisory locking alone does not refresh a repeatable-read snapshot.
        # Updating this fence forces a stale competing transaction to retry.
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [28004])
        mutex = self.env.ref('ydental_patient.ydental_patient_mutex')
        self.env.cr.execute('UPDATE ydental_patient_mutex SET ydental_revision=ydental_revision+1 WHERE id=%s', [mutex.id])
        self.env.invalidate_all()

    def _now(self):
        return fields.Datetime.now()

    def _date(self, store, instant):
        return instant.replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone)).date()

    def _text(self, value, maximum=300, required=False):
        if value is False or value is None:
            value = ''
        if not isinstance(value, str) or len(value) > maximum or required and not value.strip():
            raise ValidationError(self.env._('Enter valid text within the allowed length.'))
        return value.strip()

    def _id(self, value):
        if type(value) is not int or value <= 0:
            raise ValidationError(self.env._('A positive integer record identifier is required.'))
        return value

    def _patient(self, patient_id, canonical=True, active=False):
        patient = self.env['ydental.patient'].sudo().with_context(active_test=False).browse(self._id(patient_id)).exists()
        if not patient:
            raise AccessError(self.env._('access_denied: Select an existing patient.'))
        seen = set()
        while canonical and patient.ydental_merged_into_id:
            if patient.id in seen:
                raise UserError(self.env._('Patient identity mapping requires group review.'))
            seen.add(patient.id)
            patient = patient.ydental_merged_into_id
        if active and not patient.active:
            raise UserError(self.env._('This patient is archived. Review the identity before new activity.'))
        return patient

    def _version(self, record, version):
        if type(version) is not int or version != record.ydental_version:
            raise UserError(self.env._('version_conflict: Refresh the patient or merge request.'))

    def _phone(self, value, region):
        value = self._text(value, 100)
        region = self._text(region, 2).upper()
        if region and region not in phonenumbers.SUPPORTED_REGIONS:
            raise ValidationError(self.env._('Select a valid ISO phone region or leave it unknown.'))
        if not value:
            return '', region, '', 'empty'
        # Never use the server, store or user country to guess the phone region.
        if not value.startswith('+') and not region:
            return value, region, '', 'review'
        try:
            parsed = phonenumbers.parse(value, region or None)
        except phonenumbers.NumberParseException:
            return value, region, '', 'review'
        if not phonenumbers.is_valid_number(parsed) or parsed.extension:
            return value, region, '', 'review'
        return value, region, phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164), 'normalized'

    def _admin_values(self, values, previous=None):
        allowed = {'name', 'birth_date', 'birth_note', 'sex', 'phone', 'phone_region', 'email'}
        if not isinstance(values, dict) or set(values) - allowed:
            raise ValidationError(self.env._('Only documented administrative patient fields are accepted.'))
        result = {}
        if 'name' in values or previous is None:
            result['name'] = self._text(values.get('name'), 100, required=True)
        if 'birth_date' in values:
            try:
                birth = fields.Date.to_date(values['birth_date']) if values['birth_date'] else False
            except (TypeError, ValueError) as error:
                raise ValidationError(self.env._('Use a valid birth date or leave it unknown.')) from error
            if birth and birth > self._now().date():
                raise ValidationError(self.env._('A birth date cannot be in the future.'))
            result['ydental_birth_date'] = birth
        if 'birth_note' in values:
            result['ydental_birth_note'] = self._text(values['birth_note'], 100)
        if 'sex' in values:
            if values['sex'] not in ('unknown', 'female', 'male', 'other'):
                raise ValidationError(self.env._('Select a sex value, including unknown.'))
            result['ydental_sex'] = values['sex']
        if {'phone', 'phone_region'} & values.keys() or previous is None:
            phone, region, normalized, status = self._phone(
                values.get('phone', previous.ydental_phone if previous else ''),
                values.get('phone_region', previous.ydental_phone_region if previous else ''))
            result.update(ydental_phone=phone, ydental_phone_region=region,
                          ydental_phone_normalized=normalized, ydental_phone_status=status)
        if 'email' in values:
            email = self._text(values['email'], 200).lower()
            if email and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
                raise ValidationError(self.env._('Use a valid email address or leave it blank.'))
            result['ydental_email'] = email
        return result

    def _audit(self, event, record, before=None, after=None):
        access = self.env['ydental.access.service']
        access._audit('patient.' + event, 'patient', record, access._scope().ydental_store_id.id,
                      before=before, after=after, source='patient_service')

    def _authorize(self, operation):
        if operation in ('clinical',):
            return self.env['ydental.access.service']._check('medical', 'write', write=True).ydental_store_id
        store = self._access(write=True)
        if operation in ('policy', 'confirm', 'reject', 'refresh_merge'):
            self._group()
        return store

    def _operate(self, operation, payload, key):
        actions = {
            'create': self._create, 'edit': self._edit, 'archive': self._archive,
            'relation': self._relation_action, 'arrival': self._arrival, 'contact': self._contact,
            'clinical': self._clinical, 'policy': self._policy, 'request_merge': self._request_merge,
            'confirm': self._confirm, 'reject': self._reject, 'refresh_merge': self._refresh_merge,
        }
        if operation not in actions or not isinstance(payload, dict) or not isinstance(key, str) or not 1 <= len(key) <= 160:
            raise ValidationError(self.env._('A documented action, object and idempotency key are required.'))
        store = self._authorize(operation)
        fingerprint = hashlib.sha256(json.dumps(
            [operation, store.id, payload], sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        self._lock()
        # All effects and the receipt either succeed together or roll back.
        with self.env.cr.savepoint():
            receipts = self.env['ydental.patient.operation'].sudo()
            prior = receipts.search([('ydental_actor_id', '=', self.env.uid), ('ydental_key', '=', key)], limit=1)
            if prior:
                if prior.ydental_fingerprint != fingerprint:
                    raise UserError(self.env._('version_conflict: This action key was used for different arguments.'))
                return dict(prior.ydental_result, result='already_accepted')
            result = actions[operation](store, **payload)
            receipts._new({'name': operation, 'ydental_store_id': store.id, 'ydental_actor_id': self.env.uid,
                'ydental_key': key, 'ydental_fingerprint': fingerprint, 'ydental_result': result})
            return result

    def _new_partner(self, values, owner):
        # Fixed administrative whitelist, no x2many commands, account, messages,
        # notes or untrusted partner ID. Disable mail tracking and auto-following.
        return self.env['res.partner'].sudo().with_context(
            tracking_disable=True, mail_create_nosubscribe=True, mail_notrack=True,
        )._ydental_patient_new(dict(values, ydental_patient_owner_id=owner.id))

    def _create(self, store, values):
        values = self._admin_values(values)
        now = self._now()
        number = self.env.ref('ydental_patient.ydental_patient_sequence').sudo().next_by_id()
        if not number:
            raise UserError(self.env._('Patient numbering configuration is missing.'))
        # Patient owns the partner from the moment it becomes visible at commit.
        partner = self.env['res.partner'].sudo().with_context(tracking_disable=True)._ydental_patient_new({
            'name': values['name'], 'phone': values.get('ydental_phone'), 'email': values.get('ydental_email'),
        })
        patient = self.env['ydental.patient'].sudo()._new(dict(values,
            ydental_number=number, ydental_partner_id=partner.id, ydental_store_id=store.id,
            ydental_recorded_at=now, ydental_business_date=self._date(store, now)))
        partner._ydental_patient_save({'ydental_patient_owner_id': patient.id})
        self.env['ydental.patient.number'].sudo()._new({'name': number, 'ydental_patient_id': patient.id,
            'ydental_origin_patient_id': patient.id, 'ydental_store_id': store.id})
        self._ensure_relation(patient, store)
        self._audit('create', patient, after={'version': patient.ydental_version})
        return {'result': 'accepted', 'id': patient.id, 'number': number, 'version': patient.ydental_version,
                'duplicates': self._duplicates(patient.id)}

    def _edit(self, store, patient_id, version, values):
        patient = self._patient(patient_id, canonical=False, active=True)
        if patient.ydental_merged_into_id:
            raise UserError(self.env._('version_conflict: Open the canonical patient before editing.'))
        self._version(patient, version)
        values = self._admin_values(values, patient)
        patient._save(values)
        partner_values = {'name': patient.name, 'phone': patient.ydental_phone, 'email': patient.ydental_email}
        patient.ydental_partner_id._ydental_patient_save(partner_values)
        self._audit('modify', patient, before={'version': version},
                    after={'version': patient.ydental_version, 'fields': sorted(values)})
        return {'result': 'accepted', 'id': patient.id, 'version': patient.ydental_version}

    def _archive(self, store, patient_id, version, reason):
        patient = self._patient(patient_id, canonical=False)
        self._version(patient, version)
        reason = self._text(reason, required=True)
        if self._active_business(self._identity_ids(patient)):
            raise UserError(self.env._('Resolve active patient business before archiving.'))
        patient._save({'active': False})
        self._audit('archive', patient, after={'version': patient.ydental_version})
        return {'result': 'accepted', 'id': patient.id, 'version': patient.ydental_version}

    def _ensure_relation(self, patient, store):
        relations = self.env['ydental.patient.relation'].sudo()
        relation = relations.search([('ydental_patient_id', '=', patient.id),
            ('ydental_store_id', '=', store.id), ('ydental_superseded_by_id', '=', False)], limit=1)
        if not relation:
            relation = relations._new({'name': patient.ydental_number, 'ydental_patient_id': patient.id,
                'ydental_origin_patient_id': patient.id, 'ydental_store_id': store.id, 'ydental_created_at': self._now()})
        return relation

    def _relation_action(self, store, patient_id):
        patient = self._patient(patient_id, active=True)
        relation = self._ensure_relation(patient, store)
        self._audit('relation', relation, after={'patient_id': patient.id})
        return {'result': 'accepted', 'id': relation.id, 'patient_id': patient.id}

    def _arrival(self, store, patient_id, occurred_at=None, reason=''):
        patient = self._patient(patient_id, active=True)
        now = self._now()
        try:
            instant = fields.Datetime.to_datetime(occurred_at) if occurred_at else now
        except (TypeError, ValueError) as error:
            raise ValidationError(self.env._('Use a valid actual arrival time in UTC.')) from error
        if not instant or instant.tzinfo or instant > now:
            raise ValidationError(self.env._('Actual arrival time cannot be in the future or contain an offset.'))
        reason = self._text(reason, required=bool(occurred_at))
        relation = self._ensure_relation(patient, store)
        if relation.ydental_first_arrival:
            if occurred_at and instant != relation.ydental_first_arrival:
                raise UserError(self.env._('The first arrival is already recorded. Request a reviewed correction.'))
            return {'result': 'already_accepted', 'id': relation.id}
        relation._save({'ydental_first_arrival': instant, 'ydental_first_business_date': self._date(store, instant),
            'ydental_arrival_recorded_at': now, 'ydental_arrival_actor_id': self.env.uid, 'ydental_arrival_reason': reason})
        self._audit('arrival', relation, after={'patient_id': patient.id, 'version': relation.ydental_version})
        return {'result': 'accepted', 'id': relation.id}

    def _contact(self, store, patient_id, name, relation, relationship, phone='', phone_region='', email='',
                 verified=False, verification_note=''):
        patient = self._patient(patient_id, active=True)
        if relation not in ('contact', 'guardian', 'emergency') or type(verified) is not bool:
            raise ValidationError(self.env._('Select a contact relationship and explicit verification status.'))
        name = self._text(name, 100, required=True)
        relationship = self._text(relationship, 100, required=True)
        note = self._text(verification_note)
        if verified and not note:
            raise ValidationError(self.env._('Record the basis of contact or guardian verification.'))
        phone, region, normalized, status = self._phone(phone, phone_region)
        email = self._admin_values({'email': email}, patient)['ydental_email']
        partner = self._new_partner({'name': name, 'phone': phone, 'email': email}, patient)
        contact = self.env['ydental.patient.contact'].sudo()._new({'name': name, 'ydental_store_id': store.id,
            'ydental_patient_id': patient.id, 'ydental_origin_patient_id': patient.id, 'ydental_partner_id': partner.id,
            'ydental_relation': relation, 'ydental_relationship': relationship, 'ydental_phone': phone,
            'ydental_phone_region': region, 'ydental_phone_normalized': normalized, 'ydental_phone_status': status,
            'ydental_email': email, 'ydental_verified': verified, 'ydental_verification_note': note})
        self._audit('contact', contact, after={'patient_id': patient.id, 'version': contact.ydental_version})
        return {'result': 'accepted', 'id': contact.id}

    def _identity_snapshot(self, patient):
        return {'patient_id': patient.id, 'number': patient.ydental_number, 'name': patient.name,
                'birth_date': fields.Date.to_string(patient.ydental_birth_date), 'sex': patient.ydental_sex}

    def _clinical(self, store, patient_id, values, record_id=None, version=None):
        patient = self._patient(patient_id, active=True)
        if not isinstance(values, dict) or set(values) - {'allergies', 'prior_history', 'medication'}:
            raise ValidationError(self.env._('Only patient safety background fields are accepted.'))
        values = {'ydental_' + key: self._text(value, 4000) for key, value in values.items()}
        if record_id:
            record = self.env['ydental.patient.clinical'].sudo().browse(self._id(record_id)).exists()
            if not record or record.ydental_store_id != store or record.ydental_patient_id != patient:
                raise AccessError(self.env._('access_denied: Clinical writes require the current store and patient.'))
            self._version(record, version)
            record._save(dict(values, ydental_recorded_at=self._now(), ydental_actor_id=self.env.uid))
        else:
            record = self.env['ydental.patient.clinical'].sudo()._new(dict(values, name=patient.ydental_number,
                ydental_store_id=store.id, ydental_category='medical', ydental_patient_id=patient.id,
                ydental_origin_patient_id=patient.id, ydental_identity_snapshot=self._identity_snapshot(patient),
                ydental_recorded_at=self._now(), ydental_actor_id=self.env.uid))
        access = self.env['ydental.access.service']
        access._audit('patient.clinical.modify', 'medical', record, store.id,
                      after={'patient_id': patient.id, 'version': record.ydental_version})
        return {'result': 'accepted', 'id': record.id, 'version': record.ydental_version}

    def _policy(self, store, code, name, body_reference='', approved=False, required=True):
        if type(approved) is not bool or type(required) is not bool:
            raise ValidationError(self.env._('Policy approval and requirement must be explicit booleans.'))
        code = self._text(code, 60, required=True)
        name = self._text(name, 100, required=True)
        reference = self._text(body_reference, 200)
        records = self.env['ydental.patient.policy'].sudo()
        record = records.search([('ydental_store_id', '=', store.id), ('ydental_code', '=', code)], limit=1)
        values = {'name': name, 'ydental_body_reference': reference, 'ydental_approved': approved,
            'ydental_approved_by_id': self.env.uid if approved else False, 'ydental_required': required}
        if record:
            record._save(values)
        else:
            record = records._new(dict(values, ydental_code=code, ydental_store_id=store.id))
        self._audit('policy', record, after={'approved': approved, 'version': record.ydental_version})
        return {'result': 'accepted', 'id': record.id, 'version': record.ydental_version}

    def _document_facts(self, patient, store, policy):
        """S12 extends from approved same-store originals; no client signed flag."""
        return {'status': 'pending_verification'}

    def _prompts(self, patient_id):
        store = self._access()
        patient = self._patient(patient_id)
        policies = self.env['ydental.patient.policy'].sudo().search([
            ('ydental_store_id', '=', store.id), ('active', '=', True), ('ydental_required', '=', True)])
        if not policies:
            return [{'name': self.env._('Store document policy'), 'status': 'pending_configuration'}]
        return [{'id': policy.id, 'name': policy.name, 'version': policy.ydental_version,
                 'status': self._document_facts(patient, store, policy)['status']
                 if policy.ydental_approved and policy.ydental_body_reference else 'pending_configuration'}
                for policy in policies]

    def _duplicates(self, patient_id):
        self._access()
        patient = self._patient(patient_id)
        candidates = fields.Domain.FALSE
        if patient.ydental_birth_date:
            candidates |= fields.Domain('name', '=ilike', patient.name) & fields.Domain(
                'ydental_birth_date', '=', patient.ydental_birth_date)
        if patient.ydental_phone_normalized:
            candidates |= fields.Domain('ydental_phone_normalized', '=', patient.ydental_phone_normalized)
        elif patient.ydental_phone:
            candidates |= fields.Domain('ydental_phone', '=', patient.ydental_phone)
        if patient.ydental_email:
            candidates |= fields.Domain('ydental_email', '=', patient.ydental_email)
        matches = self.env['ydental.patient'].sudo().search(candidates & fields.Domain('id', '!=', patient.id) &
            fields.Domain('ydental_merged_into_id', '=', False), limit=30)
        return [{'id': p.id, 'name': p.name, 'number': p.ydental_number} for p in matches]

    def _search(self, term=''):
        self._access()
        term = self._text(term, 100)
        patients = self.env['ydental.patient'].with_context(active_test=False)
        domain = fields.Domain.TRUE
        if term:
            domain = fields.Domain.OR([fields.Domain('name', 'ilike', term), fields.Domain('ydental_number', '=', term),
                fields.Domain('ydental_phone', 'ilike', term), fields.Domain('ydental_phone_normalized', 'ilike', term),
                fields.Domain('ydental_email', 'ilike', term)])
            mapping = self.env['ydental.patient.number'].search([('name', '=', term)], limit=1)
            if mapping:
                domain |= fields.Domain('id', '=', mapping.ydental_patient_id.id)
        records = patients.search_fetch(domain, ['name', 'ydental_number', 'active', 'ydental_merged_into_id'], limit=50)
        return records

    def _identity_ids(self, patient):
        return self.env['ydental.patient.number'].sudo().search([
            ('ydental_patient_id', '=', patient.id)]).ydental_origin_patient_id.ids or patient.ids

    def _business_patient(self, patient_id):
        """Private downstream contract: lock before reading or creating activity.

        Caller owns its category/source authorization, calls this before any
        other business locks, uses returned canonical ID, and never commits.
        S05/S06/S08 will adapt through inheritance, not model probing.
        """
        self._lock()
        return self._patient(patient_id, active=True)

    def _active_business(self, patient_ids):
        """Upper modules append fixed {patient_id, kind, reference} summaries."""
        return []

    def _migrate_business(self, source_ids, target):
        """Move only live canonical references, preserving authors/snapshots.

        Called under the patient fence and merge savepoint after conflict checks.
        Upper modules extend with super(); failures roll back the whole merge.
        """
        return {}

    def _merge_conflicts(self, source, target):
        source_ids = self._identity_ids(source)
        target_ids = self._identity_ids(target)
        active = self._active_business(source_ids + target_ids)
        source_active = [a for a in active if a['patient_id'] in source_ids]
        target_active = [a for a in active if a['patient_id'] in target_ids]
        if any(a['kind'] == 'execution' for a in active) or source_active and target_active:
            return active
        return []

    def _request_merge(self, store, source_id, target_id, reason):
        source = self._patient(source_id, canonical=False, active=True)
        target = self._patient(target_id, canonical=False, active=True)
        if source == target or source.ydental_merged_into_id or target.ydental_merged_into_id:
            raise UserError(self.env._('Select two distinct current patient identities for group verification.'))
        reason = self._text(reason, required=True)
        relation = self.env['ydental.patient.relation'].sudo().search_count([
            ('ydental_patient_id', 'in', (source.id, target.id)), ('ydental_store_id', '=', store.id),
            ('ydental_superseded_by_id', '=', False)])
        if not relation:
            raise AccessError(self.env._('access_denied: A merge request must concern a patient related to this store.'))
        record = self.env['ydental.patient.merge'].sudo()._new({'name': source.ydental_number + ' / ' + target.ydental_number,
            'ydental_store_id': store.id, 'ydental_source_id': source.id, 'ydental_target_id': target.id,
            'ydental_source_version': source.ydental_version, 'ydental_target_version': target.ydental_version,
            'ydental_reason': reason, 'ydental_requested_by_id': self.env.uid})
        self._audit('merge.request', record, after={'source_id': source.id, 'target_id': target.id})
        return {'result': 'accepted', 'id': record.id, 'version': record.ydental_version}

    def _merge_request(self, request_id, version):
        record = self.env['ydental.patient.merge'].sudo().browse(self._id(request_id)).exists()
        if not record:
            raise AccessError(self.env._('access_denied: Select an existing merge request.'))
        self._version(record, version)
        if record.state not in ('requested', 'blocked'):
            raise UserError(self.env._('This merge request already has a final decision.'))
        stores = self.env['ydental.patient.relation'].sudo().search([
            ('ydental_patient_id', 'in', (record.ydental_source_id.id, record.ydental_target_id.id))]).ydental_store_id
        if not self.env.su and not set((stores | record.ydental_store_id).company_id.ids) <= set(self.env.user.company_ids.ids):
            raise AccessError(self.env._('access_denied: Group verification must cover all affected companies.'))
        return record

    def _refresh_merge(self, store, request_id, version, reason):
        record = self._merge_request(request_id, version)
        self._text(reason, required=True)
        source, target = record.ydental_source_id, record.ydental_target_id
        if source.ydental_merged_into_id or target.ydental_merged_into_id or not source.active or not target.active:
            raise UserError(self.env._('Patient identity changed. Submit a new merge request.'))
        record._save({'ydental_source_version': source.ydental_version, 'ydental_target_version': target.ydental_version,
                      'ydental_decision_reason': reason, 'state': 'requested', 'ydental_conflicts': []})
        self._audit('merge.refresh', record, after={'version': record.ydental_version})
        return {'result': 'accepted', 'id': record.id, 'version': record.ydental_version}

    def _reject(self, store, request_id, version, reason):
        record = self._merge_request(request_id, version)
        record._save({'state': 'rejected', 'ydental_decision_reason': self._text(reason, required=True),
                      'ydental_confirmed_by_id': self.env.uid})
        self._audit('merge.reject', record, after={'version': record.ydental_version})
        return {'result': 'accepted', 'id': record.id, 'version': record.ydental_version}

    def _reference_counts(self, source_ids):
        return {entity: self.env['ydental.patient.' + entity].sudo().with_context(active_test=False).search_count([
            ('ydental_patient_id', 'in', source_ids)]) for entity in ('number', 'relation', 'contact', 'clinical')}

    def _confirm(self, store, request_id, version, reason):
        record = self._merge_request(request_id, version)
        reason = self._text(reason, required=True)
        source, target = record.ydental_source_id, record.ydental_target_id
        self._version(source, record.ydental_source_version)
        self._version(target, record.ydental_target_version)
        if source.ydental_merged_into_id or target.ydental_merged_into_id or not source.active or not target.active:
            raise UserError(self.env._('Patient identity changed. Submit a new merge request.'))
        conflicts = self._merge_conflicts(source, target)
        if conflicts:
            record._save({'state': 'blocked', 'ydental_conflicts': conflicts, 'ydental_decision_reason': reason})
            self._audit('merge.blocked', record, after={'conflict_count': len(conflicts), 'version': record.ydental_version})
            return {'result': 'conflict_requires_resolution', 'id': record.id, 'version': record.ydental_version,
                    'conflicts': conflicts}
        source_ids = self._identity_ids(source)
        before = self._reference_counts(source_ids)
        # Keep each original identity, snapshot and arrival record. Consolidate
        # only the current relationship, retaining superseded rows as evidence.
        relations = self.env['ydental.patient.relation'].sudo().search([
            ('ydental_patient_id', 'in', source_ids), ('ydental_superseded_by_id', '=', False)])
        for relation in relations:
            existing = self.env['ydental.patient.relation'].sudo().search([
                ('ydental_patient_id', '=', target.id), ('ydental_store_id', '=', relation.ydental_store_id.id),
                ('ydental_superseded_by_id', '=', False)], limit=1)
            if existing:
                if relation.ydental_first_arrival and (not existing.ydental_first_arrival or
                        relation.ydental_first_arrival < existing.ydental_first_arrival):
                    existing._save({key: relation[key] for key in (
                        'ydental_first_arrival', 'ydental_first_business_date', 'ydental_arrival_recorded_at',
                        'ydental_arrival_reason')} | {'ydental_arrival_actor_id': relation.ydental_arrival_actor_id.id})
                relation._save({'ydental_superseded_by_id': existing.id})
            else:
                relation._save({'ydental_patient_id': target.id})
        for entity in ('number', 'contact', 'clinical'):
            records = self.env['ydental.patient.' + entity].sudo().with_context(active_test=False).search([
                ('ydental_patient_id', 'in', source_ids)])
            records._save({'ydental_patient_id': target.id})
        moved = self._migrate_business(source_ids, target)
        source._save({'ydental_merged_into_id': target.id, 'active': False})
        target._save({})
        record._save({'state': 'confirmed', 'ydental_confirmed_by_id': self.env.uid,
            'ydental_decision_reason': reason, 'ydental_conflicts': [],
            'ydental_reference_counts': {'source_before': before, 'source_after': self._reference_counts(source_ids),
                                         'downstream_moved': moved}})
        self._audit('merge.confirm', record, after={'source_id': source.id, 'target_id': target.id,
                                                  'counts': record.ydental_reference_counts})
        return {'result': 'accepted', 'id': record.id, 'patient_id': target.id, 'version': record.ydental_version}
