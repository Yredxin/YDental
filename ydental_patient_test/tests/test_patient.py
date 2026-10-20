import secrets
from datetime import datetime

from odoo import fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import TransactionCase

from .common import bind, clinical, create, merge, setup_patient


class TestPatient(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup_patient(cls)

    def test_t01_shared_identity_relationship_and_real_arrival(self):
        other = bind(self, self.manager, 'b-create', self.stores[1])
        person = create(self, service=other)
        found = self.service._search(person['number'])
        self.assertEqual(found.ids, [person['id']])
        result = self.service._operate('relation', {'patient_id': person['id']}, 'rel-a')
        self.service._operate('relation', {'patient_id': person['id']}, 'rel-a-repeat')
        relation = self.root['ydental.patient.relation'].browse(result['id'])
        self.assertFalse(relation.ydental_first_arrival)
        self.assertEqual(self.root['ydental.patient.relation'].search_count([('ydental_patient_id', '=', person['id'])]), 2)
        self.service._operate('arrival', {'patient_id': person['id'], 'occurred_at': '2026-01-01 20:00:00',
            'reason': 'Synthetic actual arrival supplement'}, 'arrival')
        self.assertEqual(relation.ydental_first_business_date, fields.Date.to_date('2026-01-02'))
        self.assertEqual(relation.ydental_first_arrival, datetime(2026, 1, 1, 20))
        self.assertGreater(relation.ydental_arrival_recorded_at, relation.ydental_first_arrival)
        self.assertEqual(relation.ydental_arrival_actor_id, self.users['frontdesk'])
        self.service._operate('arrival', {'patient_id': person['id']}, 'arrival-repeat')
        self.assertEqual(relation.ydental_first_arrival, datetime(2026, 1, 1, 20))
        with self.assertRaises(UserError):
            self.service._operate('arrival', {'patient_id': person['id'], 'occurred_at': '2026-01-01 19:00:00', 'reason': 'different'}, 'arrival-change')

    def test_t02_duplicate_hints_do_not_merge_shared_phone(self):
        one = create(self, name='Synthetic Parent', phone='+1 202 555 0100')
        two = create(self, name='Synthetic Child', phone='202-555-0100', phone_region='US')
        self.assertIn(one['id'], [hint['id'] for hint in two['duplicates']])
        self.assertNotEqual(one['id'], two['id'])
        self.assertFalse(self.root['ydental.patient'].browse(one['id']).ydental_merged_into_id)
        three = create(self, name='Synthetic Same Name', birth_date='2000-01-02')
        four = create(self, name='Synthetic Same Name', birth_date='2000-01-02')
        self.assertIn(three['id'], [r['id'] for r in four['duplicates']])

    def test_t02_phone_unknown_invalid_extension_and_no_country_guess(self):
        for phone, region, status, normalized in [
            ('2025550100', '', 'review', ''), ('short?', '', 'review', ''),
            ('2025550100', 'US', 'normalized', '+12025550100'),
            ('+1 202 555 0100 ext 2', '', 'review', ''), ('', '', 'empty', ''),
        ]:
            person = create(self, phone=phone, phone_region=region)
            record = self.root['ydental.patient'].browse(person['id'])
            self.assertEqual(record.ydental_phone or '', phone)
            self.assertEqual(record.ydental_phone_status, status)
            self.assertEqual(record.ydental_phone_normalized or '', normalized)
        with self.assertRaises(ValidationError):
            create(self, phone='2025550100', phone_region='ZZ')

    def test_t02_contact_phone_and_email_also_hint_without_identity_merge(self):
        a, b = create(self, name='Synthetic Family A'), create(self, name='Synthetic Family B')
        for patient in (a, b):
            self.service._operate('contact', {'patient_id': patient['id'], 'name': 'Synthetic Common Guardian',
                'relation': 'guardian', 'relationship': 'Declared parent', 'phone': '+1 202 555 0198'},
                'family-contact-' + str(patient['id']))
        self.assertIn(a['id'], [hint['id'] for hint in self.service._duplicates(b['id'])])
        self.assertFalse(self.root['ydental.patient'].browse(a['id']).ydental_merged_into_id)

    def test_t03_only_group_confirms_mapping_and_partner_is_not_merged(self):
        source, target = create(self), create(self)
        request = merge(self, source['id'], target['id'])
        args = {'request_id': request['id'], 'version': request['version'], 'reason': 'Synthetic group checked identity'}
        with self.assertRaises(AccessError):
            self.service._operate('confirm', args, 'frontdesk-confirm')
        old_partner = self.root['ydental.patient'].browse(source['id']).ydental_partner_id
        self.group._operate('confirm', args, 'group-confirm')
        self.assertEqual(self.service._patient(source['id']).id, target['id'])
        self.assertIn(target['id'], self.service._search(source['number']).ids)
        self.assertTrue(old_partner.exists())
        self.assertEqual(self.root['ydental.patient.number'].search([('name', '=', source['number'])]).ydental_origin_patient_id.id, source['id'])
        self.assertEqual(self.root['ydental.patient.merge'].browse(request['id']).state, 'confirmed')

    def test_t04_retries_version_conflict_rejection_and_idempotency_key_binding(self):
        person = create(self, key='create-retry')
        again = create(self, key='create-retry')
        self.assertEqual(person['id'], again['id'])
        self.assertEqual(again['result'], 'already_accepted')
        with self.assertRaises(UserError):
            create(self, name='Different', key='create-retry')
        target = create(self)
        request = merge(self, person['id'], target['id'])
        self.service._operate('edit', {'patient_id': person['id'], 'version': 1, 'values': {'name': 'Changed'}}, 'edit')
        args = {'request_id': request['id'], 'version': 1, 'reason': 'Checked'}
        with self.assertRaises(UserError):
            self.group._operate('confirm', args, 'stale-confirm')
        refreshed = self.group._operate('refresh_merge', args, 'refresh')
        args['version'] = refreshed['version']
        result = self.group._operate('confirm', args, 'confirm-new')
        self.assertEqual(self.group._operate('confirm', args, 'confirm-new')['result'], 'already_accepted')
        self.assertEqual(result['patient_id'], target['id'])
        a, b = create(self), create(self)
        request = merge(self, a['id'], b['id'])
        self.group._operate('reject', {'request_id': request['id'], 'version': 1, 'reason': 'Identity not established'}, 'reject')
        self.assertEqual(self.service._patient(a['id']).id, a['id'])

    def test_t04_partial_migration_failure_rolls_back_all_references_and_receipt(self):
        source, target = create(self), create(self)
        activity = self.service._synthetic_start(source['id'], fail_migration=True)
        old_snapshot = dict(activity.ydental_identity_snapshot)
        request = merge(self, source['id'], target['id'])
        args = {'request_id': request['id'], 'version': 1, 'reason': 'Synthetic rollback verification'}
        before = self.group._reference_counts([source['id']])
        with self.assertRaises(UserError):
            self.group._operate('confirm', args, 'failed-merge')
        self.assertEqual(self.group._reference_counts([source['id']]), before)
        self.assertEqual(activity.ydental_patient_id.id, source['id'])
        self.assertEqual(activity.ydental_identity_snapshot, old_snapshot)
        self.assertEqual(self.root['ydental.patient.merge'].browse(request['id']).state, 'requested')
        self.assertFalse(self.root['ydental.patient.operation'].search([('ydental_key', '=', 'failed-merge')]))
        activity._save({'ydental_fail_migration': False})
        self.group._operate('confirm', args, 'failed-merge')
        self.assertEqual(activity.ydental_patient_id.id, target['id'])
        self.assertEqual(activity.ydental_identity_snapshot, old_snapshot)

    def test_t05_frontdesk_search_export_aggregate_and_clinical_attachment_denied(self):
        person = create(self)
        record_id = clinical(self, person['id'])['id']
        protected = self.service.env['ydental.patient.clinical'].browse(record_id)
        for action in [lambda: protected.read(['ydental_allergies']), lambda: protected.export_data(['ydental_allergies']),
                       lambda: protected.search_read([], ['ydental_allergies']), lambda: protected.search_count([]),
                       lambda: protected.name_search(''), lambda: protected._read_group([], [], ['__count'])]:
            try:
                result = action()
            except AccessError:
                continue
            self.assertIn(result, ([], 0, [(0,)]))
        attachment = self.root['ir.attachment'].create({'name': 'S04 clinical synthetic.txt',
            'res_model': 'ydental.patient.clinical', 'res_id': record_id, 'raw': b'S04 synthetic clinical', 'public': True})
        with self.assertRaises(AccessError):
            self.service.env['ir.attachment'].browse(attachment.id)._can_return_content('raw')
        with self.assertRaises(AccessError):
            self.service.env['ir.attachment'].browse(attachment.id).read(['raw'])

    def test_t05_partner_chatter_notes_reverse_export_and_untyped_attachment(self):
        person = create(self)
        clinical(self, person['id'])
        patient = self.root['ydental.patient'].browse(person['id'])
        partner = self.service.env['res.partner'].browse(patient.ydental_partner_id.id)
        safe = partner.read(['name', 'phone', 'email', 'comment'])[0]
        self.assertFalse(safe['comment'])
        self.assertNotIn('S04 SYNTHETIC CLINICAL ONLY', str(safe))
        self.assertNotIn('ydental_allergies', partner.fields_get())
        for action in [lambda: partner.write({'comment': 'clinical text'}),
                       lambda: partner.write({'ydental_patient_owner_id': False}),
                       lambda: partner.message_post(body='clinical text'), lambda: partner.unlink(),
                       lambda: partner.export_data(['ydental_patient_owner_id/ydental_allergies'])]:
            with self.assertRaises((AccessError, ValueError, KeyError)):
                action()
        attachment = self.root['ir.attachment'].create({'name': 'S04 blocked partner.txt', 'res_model': 'res.partner',
            'res_id': partner.id, 'raw': b'Synthetic untyped data', 'public': True})
        with self.assertRaises(AccessError):
            self.service.env['ir.attachment'].browse(attachment.id)._can_return_content('raw')
        self.assertFalse(self.service.env['ir.attachment'].search([('id', '=', attachment.id)]))

    def test_t06_real_patient_care_scope_cross_store_read_audit_and_write_finance_denied(self):
        person, other = create(self), create(self, name='Other Synthetic Patient')
        b = clinical(self, person['id'], self.stores[1])['id']
        c = clinical(self, other['id'], self.stores[2])['id']
        access = self.doctor.env['ydental.access.service']._patient_care(person['id'], 'diagnosis')
        records = access.env['ydental.patient.clinical'].search_read([], ['ydental_allergies'])
        self.assertEqual([r['id'] for r in records], [b])
        with self.assertRaises(AccessError):
            access.env['ydental.patient.clinical'].browse(c).read(['ydental_allergies'])
        with self.assertRaises(AccessError):
            self.doctor._operate('clinical', {'patient_id': person['id'], 'record_id': b, 'version': 1,
                'values': {'allergies': 'Attempted cross-store edit'}}, 'cross-write')
        finance = self.root['ydental.patient.test.source']._new({'name': 'Synthetic finance original',
            'ydental_store_id': self.stores[1].id, 'ydental_category': 'settlement', 'ydental_patient_id': person['id'],
            'ydental_origin_patient_id': person['id'], 'ydental_identity_snapshot': {'synthetic': True}, 'ydental_text': 'Finance original'})
        with self.assertRaises(AccessError):
            access.env['ydental.patient.test.source'].browse(finance.id).read(['ydental_text'])
        self.assertTrue(self.root['ydental.access.audit'].search([('ydental_event', '=', 'patient.care.open'),
            ('ydental_user_id', '=', self.users['doctor'].id), ('ydental_target_id', '=', person['id'])]))
        self.assertFalse(self.doctor.env['ydental.access.service']._membership(self.users['doctor'].id, self.stores[1].id))

    def test_t05_default_context_attachment_relink_and_limited_token_audit(self):
        from odoo.tools.misc import limited_field_access_token

        person = create(self)
        patient = self.root['ydental.patient'].browse(person['id'])
        partners = self.service.env['res.partner']
        with self.assertRaises(AccessError):
            partners.with_context(default_ydental_patient_owner_id=patient.id).create({'name': 'Forged owner'})
        files = self.service.env['ir.attachment']
        with self.assertRaises(AccessError):
            files.with_context(default_res_model='res.partner', default_res_id=patient.ydental_partner_id.id).create(
                {'name': 'Forged default source', 'raw': b'Synthetic only'})
        ordinary = self.root['ir.attachment'].create({'name': 'Synthetic ordinary file', 'raw': b'Synthetic only',
            'create_uid': self.users['frontdesk'].id})
        with self.assertRaises(AccessError):
            files.browse(ordinary.id).write({'res_model': 'res.partner', 'res_id': patient.ydental_partner_id.id})
        record_id = clinical(self, person['id'])['id']
        attachment = self.root['ir.attachment'].create({'name': 'Synthetic token download',
            'res_model': 'ydental.patient.clinical', 'res_id': record_id, 'raw': b'Synthetic only'})
        token = limited_field_access_token(attachment, 'raw', scope='binary')
        record = self.doctor.env['ir.binary']._find_record(res_model='ir.attachment', res_id=attachment.id,
            access_token=token, field='raw')
        self.assertEqual(record.id, attachment.id)
        self.assertTrue(self.root['ydental.access.audit'].search([('ydental_event', '=', 'source.download'),
            ('ydental_user_id', '=', self.users['doctor'].id), ('ydental_target_id', '=', record_id)]))

    def test_t06_context_forgery_permission_revocation_and_other_session_denied(self):
        person = create(self)
        b = clinical(self, person['id'], self.stores[1])['id']
        access = self.doctor.env['ydental.access.service']
        forged = access.with_context(ydental_patient_care={'patient_id': person['id'], 'purpose': 'diagnosis'},
                                     ydental_purpose='care', ydental_patient_id=person['id'])
        with self.assertRaises(AccessError):
            forged.env['ydental.patient.clinical'].browse(b).read(['ydental_allergies'])
        care = access._patient_care(person['id'], 'history_review')
        self.assertEqual(care.env['ydental.patient.clinical'].browse(b).read(['ydental_allergies'])[0]['id'], b)
        another = bind(self, self.users['doctor'], 'another-session').env['ydental.access.service']
        with self.assertRaises(AccessError):
            another.with_context(ydental_patient_care=care.env.context['ydental_patient_care']).env['ydental.patient.clinical'].browse(b).read(['ydental_allergies'])
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none'})
        with self.assertRaises(AccessError):
            care.env['ydental.patient.clinical'].browse(b).read(['ydental_allergies'])

    def test_t07_rename_and_merge_preserve_identity_snapshot_and_authors(self):
        source, target = create(self, name='Original Synthetic Name'), create(self)
        result = clinical(self, source['id'])
        record = self.root['ydental.patient.clinical'].browse(result['id'])
        snapshot, actor = dict(record.ydental_identity_snapshot), record.ydental_actor_id
        self.service._operate('edit', {'patient_id': source['id'], 'version': 1, 'values': {'name': 'Renamed Synthetic'}}, 'rename')
        self.assertEqual(record.ydental_identity_snapshot, snapshot)
        request = merge(self, source['id'], target['id'])
        self.group._operate('confirm', {'request_id': request['id'], 'version': 1, 'reason': 'Verified same synthetic person'}, 'merge')
        self.assertEqual(record.ydental_patient_id.id, target['id'])
        self.assertEqual(record.ydental_origin_patient_id.id, source['id'])
        self.assertEqual(record.ydental_identity_snapshot, snapshot)
        self.assertEqual(record.ydental_actor_id, actor)

    def test_t08_number_stable_forbidden_raw_crud_no_user_or_notification(self):
        user_count = self.root['res.users'].search_count([])
        mail_count = self.root['mail.mail'].search_count([])
        person = create(self)
        self.service._operate('edit', {'patient_id': person['id'], 'version': 1, 'values': {'name': 'New Name'}}, 'stable')
        record = self.service.env['ydental.patient'].browse(person['id'])
        self.assertEqual(record.ydental_number, person['number'])
        for action in [lambda: record.write({'ydental_number': 'FAKE'}), lambda: record.unlink(),
                       lambda: record.create({'name': 'Fake', 'ydental_number': 'FAKE'}),
                       lambda: self.reader._operate('create', {'values': {'name': 'Fake'}}, 'reader-create')]:
            with self.assertRaises(AccessError):
                action()
        self.assertEqual(self.root['res.users'].search_count([]), user_count)
        self.assertEqual(self.root['mail.mail'].search_count([]), mail_count)
        self.assertFalse(record.sudo().ydental_partner_id.user_ids)

    def test_t09_store_policy_missing_text_and_no_other_store_signing_inheritance(self):
        person = create(self)
        self.assertEqual(self.service._prompts(person['id'])[0]['status'], 'pending_configuration')
        b = bind(self, self.manager, 'policy-b', self.stores[1])
        b._operate('policy', {'code': 'consent', 'name': 'Synthetic B policy', 'body_reference': 'synthetic-policy-b-v1',
                             'approved': True}, 'b-policy')
        old_signed = self.root['ydental.patient.test.source']._new({'name': 'S04 synthetic B signed fact',
            'ydental_store_id': self.stores[1].id, 'ydental_category': 'medical', 'ydental_patient_id': person['id'],
            'ydental_origin_patient_id': person['id'], 'ydental_identity_snapshot': {'synthetic': True},
            'ydental_signed_fact': True, 'ydental_text': 'Synthetic prior-store fact, not a signature or PDF'})
        self.assertEqual(self.service._prompts(person['id'])[0]['status'], 'pending_configuration')
        self.group._operate('policy', {'code': 'consent', 'name': 'Synthetic A policy', 'approved': True}, 'a-empty')
        self.assertEqual(self.service._prompts(person['id'])[0]['status'], 'pending_configuration')
        self.group._operate('policy', {'code': 'consent', 'name': 'Synthetic A policy', 'approved': True,
                                      'body_reference': 'synthetic-policy-a-v1'}, 'a-ready')
        self.assertEqual(self.service._prompts(person['id'])[0]['status'], 'pending_verification')
        self.assertTrue(old_signed.ydental_signed_fact)
        self.assertFalse(self.root['ydental.patient.test.source'].search([
            ('ydental_store_id', '=', self.stores[0].id), ('ydental_signed_fact', '=', True)]))
        with self.assertRaises(AccessError):
            self.service._operate('policy', {'code': 'forged', 'name': 'Fake approved', 'approved': True}, 'front-policy')
        self.assertTrue(create(self)['id'])

    def test_t10_active_reference_conflict_and_execution_requires_resolution(self):
        for kind in ('reservation', 'queue', 'execution'):
            source, target = create(self), create(self)
            left = self.service._synthetic_start(source['id'], kind)
            right = self.service._synthetic_start(target['id'], kind)
            request = merge(self, source['id'], target['id'])
            args = {'request_id': request['id'], 'version': 1, 'reason': 'Check active synthetic conflict'}
            blocked = self.group._operate('confirm', args, 'block-' + kind)
            self.assertEqual(blocked['result'], 'conflict_requires_resolution')
            self.assertEqual(left.ydental_patient_id.id, source['id'])
            self.assertEqual(right.ydental_patient_id.id, target['id'])
            left._save({'ydental_active': False})
            right._save({'ydental_active': False})
            args['version'] = blocked['version']
            self.group._operate('confirm', args, 'resolved-' + kind)
            self.assertEqual(self.service._patient(source['id']).id, target['id'])
            self.assertEqual(left.ydental_patient_id.id, source['id'])

    def test_t10_single_active_execution_blocks_merge_and_archive(self):
        source, target = create(self), create(self)
        self.service._synthetic_start(source['id'], 'execution')
        request = merge(self, source['id'], target['id'])
        result = self.group._operate('confirm', {'request_id': request['id'], 'version': 1, 'reason': 'Execution protection'}, 'single-execution')
        self.assertEqual(result['result'], 'conflict_requires_resolution')
        with self.assertRaises(UserError):
            self.service._operate('archive', {'patient_id': source['id'], 'version': 1, 'reason': 'Invalid active archive'}, 'archive')

    def test_contact_guardian_no_age_or_identity_gate_and_verification_explicit(self):
        person = create(self)
        result = self.service._operate('contact', {'patient_id': person['id'], 'name': 'Synthetic Guardian',
            'relation': 'guardian', 'relationship': 'Declared parent', 'phone': '2025550100'}, 'guardian')
        contact = self.root['ydental.patient.contact'].browse(result['id'])
        self.assertFalse(contact.ydental_verified)
        self.assertEqual(contact.ydental_phone_status, 'review')
        self.assertFalse(contact.ydental_partner_id.comment)
        self.assertFalse(contact.ydental_partner_id.user_ids)
        self.service._operate('contact', {'patient_id': person['id'], 'contact_id': contact.id,
            'version': 1, 'name': 'Verified Synthetic Guardian', 'relation': 'guardian', 'relationship': 'Declared parent',
            'verified': True, 'verification_note': 'Synthetic documents reviewed', 'phone': '+1 202 555 0100'}, 'guardian-edit')
        self.assertEqual(contact.ydental_version, 2)
        self.assertTrue(contact.ydental_verified)
        self.assertEqual(contact.ydental_partner_id.name, 'Verified Synthetic Guardian')
        with self.assertRaises(UserError):
            self.service._operate('contact', {'patient_id': person['id'], 'contact_id': contact.id,
                'version': 1, 'name': 'Stale', 'relation': 'contact', 'relationship': 'Other'}, 'guardian-stale')

    def test_relation_merge_retains_earliest_arrival_and_history(self):
        source, target = create(self), create(self)
        a = self.service._operate('arrival', {'patient_id': source['id'], 'occurred_at': '2026-01-01 10:00:00', 'reason': 'Synthetic earlier'}, 'source-arrive')
        b = self.service._operate('arrival', {'patient_id': target['id'], 'occurred_at': '2026-01-02 10:00:00', 'reason': 'Synthetic later'}, 'target-arrive')
        request = merge(self, source['id'], target['id'])
        self.group._operate('confirm', {'request_id': request['id'], 'version': 1, 'reason': 'Verified'}, 'arrival-merge')
        first = self.root['ydental.patient.relation'].browse(a['id'])
        current = self.root['ydental.patient.relation'].browse(b['id'])
        self.assertEqual(first.ydental_superseded_by_id, current)
        self.assertEqual(current.ydental_first_arrival, datetime(2026, 1, 1, 10))
        self.assertEqual(first.ydental_first_arrival, datetime(2026, 1, 1, 10))

    def test_chain_merge_old_numbers_canonical_business_and_cycle_rejection(self):
        a, b, c = create(self), create(self), create(self)
        for source, target in ((a, b), (b, c)):
            request = merge(self, source['id'], target['id'])
            self.group._operate('confirm', {'request_id': request['id'], 'version': 1, 'reason': 'Verified chain'}, secrets.token_hex(8))
        self.assertEqual(self.service._patient(a['id']).id, c['id'])
        self.assertEqual(self.service._business_patient(a['id']).id, c['id'])
        for number in (a['number'], b['number'], c['number']):
            self.assertEqual(self.root['ydental.patient.number'].search([('name', '=', number)]).ydental_patient_id.id, c['id'])
        with self.assertRaises(UserError):
            merge(self, c['id'], a['id'])
