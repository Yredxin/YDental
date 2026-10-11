import json
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user


class TestS01(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env['res.company'].create({'name': 'S01 Synthetic Company A'})
        cls.company_b = cls.env['res.company'].create({'name': 'S01 Synthetic Company B'})
        cls.stores = cls.env['ydental.access.store'].create([
            {'name': 'S01 Synthetic A', 'company_id': cls.company_a.id, 'ydental_timezone': 'Asia/Shanghai'},
            {'name': 'S01 Synthetic B', 'company_id': cls.company_a.id, 'ydental_timezone': 'Asia/Shanghai'},
            {'name': 'S01 Synthetic C', 'company_id': cls.company_b.id, 'ydental_timezone': 'UTC'},
        ])
        cls.a, cls.b, cls.c = cls.stores
        groups = 'ydental_base.ydental_base_group_user'
        cls.operator = new_test_user(cls.env, login='s01_operator', groups=groups)
        cls.manager = new_test_user(cls.env, login='s01_manager', groups=groups)
        cls.personnel = new_test_user(cls.env, login='s01_personnel', groups=groups)
        cls.group_admin = new_test_user(
            cls.env, login='s01_group', groups=groups + ',ydental_access.ydental_group_manager',
            company_ids=[fields.Command.set([cls.env.company.id, cls.company_a.id, cls.company_b.id])],
        )
        cls.service = cls.env['ydental.access.service']
        cls.admin = cls.bound(cls.group_admin, 'setup')
        for user in (cls.operator, cls.manager, cls.personnel, cls.group_admin):
            for store in cls.stores:
                cls.admin._join(user.id, store.id)
        cls.admin._membership(cls.manager.id, cls.a.id).write({'ydental_is_manager': True})
        for store, level in ((cls.a, 'write'), (cls.b, 'read')):
            cls.admin._grant(cls.operator.id, store.id, {'space': level})
        cls.admin._grant(cls.personnel.id, cls.a.id, {'personnel': 'write', 'space': 'read'})
        cls.records = cls.env['ydental.access.test.record'].create([
            {'name': 'Synthetic ' + store.name, 'ydental_store_id': store.id, 'ydental_category': category,
             'ydental_text': 'SYNTHETIC_' + category.upper()}
            for store in cls.stores for category in ('space', 'medical', 'settlement')
        ])

    @classmethod
    def bound(cls, user, key, store=None):
        service = cls.service.with_user(user)
        session = service._session_for_key(key)
        bound = service._bind(session)
        if store:
            bound._switch(store.id)
            bound = service._bind(session)
        return bound

    def source(self, service, store, category='space'):
        record = self.records.filtered(lambda r: r.ydental_store_id == store and r.ydental_category == category)
        return record.with_env(service.env)

    def test_t01_store_levels_and_batch(self):
        a = self.bound(self.operator, 't01-a', self.a)
        self.source(a, self.a).write({'name': 'Changed in A'})
        b = self.bound(self.operator, 't01-b', self.b)
        self.assertTrue(self.source(b, self.b).read(['name']))
        with self.assertRaises(AccessError):
            self.source(b, self.b).write({'name': 'Denied'})
        c = self.bound(self.operator, 't01-c', self.c)
        with self.assertRaises(AccessError):
            self.source(c, self.c).read(['name'])
        pair = (self.source(a, self.a) | self.source(a, self.b))
        old = self.source(a, self.a).sudo().name
        with self.assertRaises(AccessError):
            pair.write({'name': 'Denied batch'})
        self.assertEqual(self.source(a, self.a).sudo().name, old)
        forged = self.records.with_user(self.operator).with_context(ydental_binding={'user_id': self.operator.id}, is_system=True)
        with self.assertRaises(AccessError):
            forged.search([])

    def test_t02_store_manager_exception(self):
        manager = self.bound(self.manager, 't02', self.a)
        manager._grant(self.operator.id, self.a.id, {'finance_approval': 'write'})
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id))['finance_approval'], 'write')
        with self.assertRaises(AccessError):
            manager._grant(self.operator.id, self.b.id, {'finance_approval': 'write'})
        self.assertFalse(self.manager.has_group('base.group_system'))

    def test_t03_scope_independence_and_old_revision(self):
        first = self.bound(self.operator, 't03-first', self.a)
        second = self.bound(self.operator, 't03-second', self.b)
        self.assertEqual(first._scope().ydental_store_id, self.a)
        second._switch(self.c.id)
        self.assertEqual(first._scope().ydental_store_id, self.a)
        first._switch(self.b.id)
        with self.assertRaises(UserError):
            self.source(first, self.a).write({'name': 'Stale page'})

    def test_t04_revocation_and_attachment(self):
        operator = self.bound(self.operator, 't04', self.a)
        record = self.source(operator, self.a)
        attachment = self.env['ir.attachment'].create({
            'name': 'S01 synthetic attachment', 'raw': b'SYNTHETIC',
            'res_model': record._name, 'res_id': record.id,
        })
        self.assertTrue(record.read(['name']))
        attachment.with_env(operator.env).check_access('read')
        self.admin._grant(self.operator.id, self.a.id, {'space': 'none'})
        with self.assertRaises(AccessError):
            record.read(['name'])
        with self.assertRaises(AccessError):
            attachment.with_env(operator.env).check_access('read')
        attachment.write({'public': True})
        with self.assertRaises(AccessError):
            attachment.with_env(operator.env)._can_return_content('raw', access_token='untrusted')

    def test_t05_removal_and_departure(self):
        member = self.admin._membership(self.operator.id, self.a.id)
        employee_a = member.ydental_employee_id
        employee_c = self.admin._membership(self.operator.id, self.c.id).ydental_employee_id
        self.admin._remove(self.operator.id, self.a.id)
        self.assertTrue(employee_a.active)
        self.admin._remove(self.operator.id, self.b.id)
        self.assertFalse(employee_a.active)
        self.assertTrue(employee_c.active)
        self.assertTrue(self.operator.active)
        self.admin._depart(self.operator.id)
        self.assertFalse(self.operator.active)
        self.assertFalse(employee_c.active)
        self.assertTrue(self.env['ydental.access.membership'].with_context(active_test=False).search_count([
            ('ydental_user_id', '=', self.operator.id),
        ]))

    def test_t06_common_and_private_employee_fields(self):
        a = self.admin._membership(self.operator.id, self.a.id).ydental_employee_id
        b = self.admin._membership(self.operator.id, self.b.id).ydental_employee_id
        c = self.admin._membership(self.operator.id, self.c.id).ydental_employee_id
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        department_a = self.env['hr.department'].create({'name': 'Private A', 'company_id': self.company_a.id})
        department_c = self.env['hr.department'].create({'name': 'Private C', 'company_id': self.company_b.id})
        a.department_id = department_a
        c.department_id = department_c
        capability = self.env['ydental.access.capability'].create({'name': 'Synthetic skill', 'ydental_code': 'synthetic'})
        self.admin._update_profile(self.operator.id, 'Synthetic common role', [capability.id])
        self.assertEqual(a.ydental_job_title, c.ydental_job_title)
        self.assertEqual(a.ydental_capability_ids, c.ydental_capability_ids)
        self.assertEqual(a.department_id, department_a)
        self.assertEqual(c.department_id, department_c)
        with self.assertRaises(AccessError):
            a.write({'ydental_job_title': 'Forbidden local override'})

    def test_t07_minimal_information(self):
        operator = self.bound(self.operator, 't07', self.a)
        self.assertFalse(self.env['ydental.access.test.record'].with_env(operator.env).search([
            ('ydental_category', '=', 'medical'),
        ]))
        self.assertFalse(self.env['res.partner'].with_user(self.operator).fields_get().get('ydental_text'))
        self.assertNotIn('ydental_text', json.dumps(operator._dashboard(), default=str))

    def test_t08_idempotent_membership_and_account(self):
        before = self.env['hr.employee'].with_context(active_test=False).search_count([('user_id', '=', self.operator.id)])
        first = self.admin._join(self.operator.id, self.a.id)
        second = self.admin._join(self.operator.id, self.a.id)
        self.assertEqual(first, second)
        self.assertEqual(before, self.env['hr.employee'].with_context(active_test=False).search_count([('user_id', '=', self.operator.id)]))
        result = self.admin._create_account('Synthetic new staff', 's01_new@example.invalid', self.a.id)
        again = self.admin._create_account('Ignored duplicate name', 's01_new@example.invalid', self.a.id)
        self.assertEqual(result['user_id'], again['user_id'])
        new_user = self.env['res.users'].browse(result['user_id'])
        self.assertFalse(new_user.has_group('hr.group_hr_user'))
        self.assertFalse(new_user.has_group('base.group_system'))

    def test_t09_template_replace_detach_and_atomic_batch(self):
        self.admin._grant(self.operator.id, self.a.id, {'warehouse': 'read'})
        template = self.env['ydental.access.template'].create({'name': 'Synthetic front desk', 'ydental_levels': {'frontdesk': 'write'}})
        targets = [[self.operator.id, self.a.id]]
        preview = self.admin._template_preview(template.id, targets)
        self.admin._apply_template(template.id, targets, preview['receipt'])
        levels = self.admin._levels(self.admin._membership(self.operator.id, self.a.id))
        self.assertEqual(levels['warehouse'], 'none')
        self.assertEqual(levels['medical'], 'none')
        self.assertEqual(levels['frontdesk'], 'write')
        grants = self.env['ydental.access.grant'].search_count([])
        changes = self.env['ydental.access.audit'].search_count([('ydental_event', '=', 'authorization.change')])
        repeated = self.admin._template_preview(template.id, targets)
        self.admin._apply_template(template.id, targets, repeated['receipt'])
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id)), levels)
        self.assertEqual(self.env['ydental.access.grant'].search_count([]), grants)
        self.assertEqual(self.env['ydental.access.audit'].search_count([('ydental_event', '=', 'authorization.change')]), changes)
        template.ydental_levels = {'frontdesk': 'read'}
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id)), levels)
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.b.id))['space'], 'read')
        manager = self.bound(self.manager, 't09', self.a)
        with self.assertRaises(AccessError):
            manager._template_preview(template.id, [[self.operator.id, self.a.id], [self.operator.id, self.b.id]])
        with self.assertRaises(AccessError):
            manager._apply_template(template.id, [[self.operator.id, self.a.id], [self.operator.id, self.b.id]], preview['receipt'])
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id)), levels)

    def test_t10_personnel_ceiling_and_identity(self):
        personnel = self.bound(self.personnel, 't10', self.a)
        for user_id, levels in ((self.operator.id, {'space': 'write'}),
                                (self.operator.id, {'finance_approval': 'write'}),
                                (self.personnel.id, {'personnel': 'write'})):
            with self.assertRaises(AccessError):
                personnel._grant(user_id, self.a.id, levels)
        personnel._grant(self.operator.id, self.a.id, {'space': 'read'})
        with self.assertRaises(AccessError):
            self.admin._membership(self.operator.id, self.a.id).with_user(self.personnel).write({'ydental_is_manager': True})

    def test_t11_events_and_immutable_audit(self):
        operator = self.bound(self.operator, 't11', self.a)
        record = self.source(operator, self.a)
        record.read(['ydental_text'])
        record.write({'ydental_text': 'SYNTHETIC_EDIT'})
        self.admin._grant(self.operator.id, self.a.id, {'export': 'write'})
        record.export_data(['name'])
        rows = self.env['ydental.access.audit'].search([('ydental_target_model', '=', record._name), ('ydental_target_id', '=', record.id)])
        self.assertTrue({'source.view', 'source.modify', 'source.export'} <= set(rows.mapped('ydental_event')))
        self.assertNotIn('SYNTHETIC_EDIT', str(rows.read()))
        with self.assertRaises(AccessError):
            rows.with_user(self.operator).write({'ydental_result': 'accepted'})
        with self.assertRaises(AccessError):
            rows.with_user(self.operator).unlink()
        with self.assertRaises(AccessError):
            rows.with_user(self.operator).read()

    def test_t12_export_requires_both_permissions(self):
        operator = self.bound(self.operator, 't12', self.a)
        record = self.source(operator, self.a)
        with self.assertRaises(AccessError):
            record.export_data(['name'])
        self.admin._grant(self.operator.id, self.a.id, {'space': 'none', 'export': 'write'})
        with self.assertRaises(AccessError):
            record.export_data(['name'])
        self.admin._grant(self.operator.id, self.a.id, {'space': 'read'})
        self.assertTrue(record.export_data(['name'])['datas'])
        self.admin._grant(self.operator.id, self.a.id, {'export': 'read'})
        with self.assertRaises(AccessError):
            record.export_data(['name'])

    def test_t13_care_history_and_execution_hook(self):
        self.admin._grant(self.operator.id, self.a.id, {'medical': 'read'})
        self.source(self.admin, self.c, 'medical').sudo().write({'ydental_test_care_target': True})
        operator = self.bound(self.operator, 't13', self.a)._synthetic_care_scope()
        medical = self.source(operator, self.c, 'medical')
        self.assertTrue(medical.read(['ydental_text']))
        with self.assertRaises(AccessError):
            medical.write({'ydental_text': 'Denied cross-store'})
        with self.assertRaises(AccessError):
            self.source(operator, self.c, 'settlement').read()
        c = self.bound(self.operator, 't13-c', self.c).with_context(ydental_purpose='care')
        with self.assertRaises(AccessError):
            self.source(c, self.c, 'medical').read()
        # Explicit test double, not an implemented S06 execution lease.
        with patch.object(type(operator), '_get_execution_store_id', return_value=self.b.id):
            with self.assertRaises(AccessError):
                self.source(operator, self.a).write({'name': 'Denied while executing in B'})

    def test_manager_policy_configuration_and_last_manager(self):
        with self.assertRaises(UserError):
            self.admin._set_manager(self.operator.id, self.a.id, True)
        tech = new_test_user(self.env, login='s01_technical', groups='ydental_access.ydental_system_manager')
        technical = self.bound(tech, 'technical-policy')
        # Synthetic test values only, not an approved production release.
        technical._configure_policy('group_with_replacement', 12, 15, True)
        self.admin._set_manager(self.operator.id, self.a.id, True)
        self.admin._set_manager(self.manager.id, self.a.id, False)
        with self.assertRaises(UserError):
            self.admin._set_manager(self.operator.id, self.a.id, False)
        ordinary = self.bound(self.personnel, 'policy-denial', self.a)
        with self.assertRaises(AccessError):
            ordinary._set_manager(self.personnel.id, self.a.id, True)
        with self.assertRaises(AccessError):
            ordinary._configure_policy('group_with_replacement', 12, 15, True)
        self.assertEqual(self.env['ir.config_parameter'].get_int('auth_password_policy.minlength'), 12)
        self.assertEqual(self.env['ir.config_parameter'].get_str('auth_totp.policy'), 'employee_required')
        self.assertEqual(self.env.ref('ydental_base.ydental_base_group_user').lock_timeout_inactivity, 15)
        with self.assertRaises(UserError):
            self.operator.password = 'short'
        with self.assertRaises(UserError):
            self.admin._depart(tech.id)

    def test_native_export_gate_and_template_stale_preview(self):
        operator = self.bound(self.operator, 'native-export', self.a)
        stores = self.a.with_env(operator.env)
        with self.assertRaises(AccessError):
            stores.export_data(['name'])
        self.admin._grant(self.operator.id, self.a.id, {'export': 'write'})
        self.assertTrue(stores.export_data(['name'])['datas'])
        template = self.env['ydental.access.template'].create({'name': 'Changing template', 'ydental_levels': {'space': 'read'}})
        targets = [[self.operator.id, self.a.id]]
        preview = self.admin._template_preview(template.id, targets)
        template.ydental_levels = {'space': 'none'}
        with self.assertRaises(UserError):
            self.admin._apply_template(template.id, targets, preview['receipt'])

    def test_group_administration_stays_within_allowed_companies(self):
        limited = new_test_user(
            self.env, login='s01_limited_group', groups='ydental_access.ydental_group_manager',
            company_id=self.company_a.id, company_ids=[fields.Command.set(self.company_a.ids)],
        )
        service = self.bound(limited, 'limited-group')
        with self.assertRaises(AccessError):
            service._grant(self.operator.id, self.c.id, {'settlement': 'write'})
        with self.assertRaises(AccessError):
            service._join(self.personnel.id, self.c.id)
        self.env['ir.config_parameter'].set_str('ydental_access.manager_policy', 'group_with_replacement')
        with self.assertRaises(AccessError):
            service._set_manager(self.operator.id, self.c.id, True)

    def test_rework_care_scope_is_server_trusted_and_targeted(self):
        self.admin._grant(self.operator.id, self.a.id, {'medical': 'read'})
        service = self.bound(self.operator, 'rework-care', self.a)
        other = self.source(service, self.c, 'medical')
        with self.assertRaises(AccessError):
            other.with_context(ydental_purpose='care').read(['name'])
        forged = service.with_context(ydental_purpose='care', ydental_test_care_scope={
            'user_id': self.operator.id, 'record_ids': other.ids,
        })
        self.assertEqual(forged.env[other._name].search([('ydental_store_id', '=', self.c.id)]).ids, [])
        other.sudo().ydental_test_care_target = True
        excluded = self.env[other._name].create({'name': 'Unrelated clinical history',
            'ydental_text': 'SYNTHETIC_UNRELATED', 'ydental_store_id': self.c.id, 'ydental_category': 'medical'})
        trusted = service._synthetic_care_scope()
        self.assertEqual(trusted.env[other._name].search([('ydental_store_id', '=', self.c.id)]).ids, other.ids)
        with self.assertRaises(AccessError):
            excluded.with_env(trusted.env).read()
        with self.assertRaises(AccessError):
            other.with_env(trusted.env).write({'name': 'Cross-store mutation'})
        with self.assertRaises(AccessError):
            self.source(trusted, self.c, 'settlement').read()
        changed = self.bound(self.operator, 'rework-care', self.b)
        with self.assertRaises(AccessError):
            other.with_env(changed.with_context(ydental_test_care_scope=trusted.env.context['ydental_test_care_scope']).env).read()

    def test_rework_default_store_consumed_once_and_validated(self):
        original = (self.operator.company_id.id, self.operator.group_ids.ids)
        self.operator.ydental_test_default_store_id = self.b
        first = self.service.with_user(self.operator)._session_for_key('default-first')
        second = self.service.with_user(self.operator)._session_for_key('default-second')
        self.assertEqual(first.ydental_store_id, self.b)
        self.assertEqual(second.ydental_store_id, self.b)
        self.service.with_user(self.operator)._bind(first)._switch(self.a.id)
        self.assertEqual(self.service.with_user(self.operator)._session_for_key('default-first').ydental_store_id, self.a)
        self.assertEqual(second.ydental_store_id, self.b)
        self.assertEqual((self.operator.company_id.id, self.operator.group_ids.ids), original)
        self.c.active = False
        self.operator.ydental_test_default_store_id = self.c
        self.assertFalse(self.service.with_user(self.operator)._session_for_key('default-inactive-store').ydental_store_id)
        self.operator.ydental_test_default_store_id = self.b
        self.admin._membership(self.operator.id, self.b.id).ydental_employee_id.active = False
        self.assertFalse(self.service.with_user(self.operator)._session_for_key('default-inactive-employee').ydental_store_id)
        unassigned = self.env['ydental.access.store'].create({'name': 'Unassigned default',
            'company_id': self.company_a.id, 'ydental_timezone': 'UTC'})
        self.operator.ydental_test_default_store_id = unassigned
        self.assertFalse(self.service.with_user(self.operator)._session_for_key('default-unassigned').ydental_store_id)

    def test_rework_direct_master_data_writes_are_audited(self):
        Audit = self.env['ydental.access.audit']
        Store = self.env['ydental.access.store'].with_user(self.group_admin)
        store = Store.create({'name': 'Direct audited store', 'company_id': self.company_a.id, 'ydental_timezone': 'UTC'})
        store.write({'name': 'Modified audited store'})
        Cap = self.env['ydental.access.capability'].with_user(self.group_admin)
        cap = Cap.create({'name': 'Direct capability', 'ydental_code': 'direct-rework'})
        cap.write({'name': 'Modified capability'})
        for target, event in ((store, 'store.modify'), (cap, 'capability.modify')):
            row = Audit.search([('ydental_target_model', '=', target._name), ('ydental_target_id', '=', target.id),
                                ('ydental_event', '=', event)])
            self.assertEqual(len(row), 1)
            self.assertEqual(row.ydental_user_id, self.group_admin)
            self.assertNotEqual(row.ydental_before['name'], row.ydental_after['name'])
        self.assertEqual(Audit.search_count([('ydental_event', '=', 'store.create'), ('ydental_target_id', '=', store.id)]), 1)
        self.assertEqual(Audit.search_count([('ydental_event', '=', 'capability.create'), ('ydental_target_id', '=', cap.id)]), 1)
        # Native res.users ACL remains authoritative. Our group has no native
        # user-write permission: direct common writes must be denied, not widened.
        before = self.operator.ydental_job_title
        with self.assertRaises(AccessError):
            self.operator.with_user(self.group_admin).write({'ydental_job_title': 'Direct common profile'})
        self.assertEqual(self.operator.ydental_job_title, before)
        # This separate synthetic actor already has the native user-manager
        # role. Production application roles and ACLs remain unchanged.
        native = new_test_user(self.env, login='s01_native_group',
            groups='ydental_access.ydental_group_manager,base.group_erp_manager',
            company_ids=[fields.Command.set(self.group_admin.company_ids.ids)])
        self.group_admin.with_user(native).write({'ydental_job_title': 'Direct audited profile'})
        row = Audit.search([('ydental_event', '=', 'profile.change'),
                            ('ydental_target_id', '=', self.group_admin.id)])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.ydental_user_id, native)
        self.assertNotEqual(row.ydental_before['job_title'], row.ydental_after['job_title'])
        self.admin._update_profile(self.operator.id, 'Audited service profile', cap.ids)
        self.assertTrue(Audit.search([('ydental_event', '=', 'profile.change'),
                                     ('ydental_target_id', '=', self.operator.id)]))
        with self.assertRaises(AccessError):
            Store.with_user(self.operator).create({'name': 'Forbidden master',
                'company_id': self.company_a.id, 'ydental_timezone': 'UTC'})

    def test_rework_query_reads_have_one_minimal_audit(self):
        service = self.bound(self.operator, 'rework-query', self.a)
        Source = service.env['ydental.access.test.record']
        Audit = self.env['ydental.access.audit']
        domain = [('ydental_text', '=', 'SYNTHETIC_SPACE')]
        operations = (
            lambda: Source.read_group(domain, ['ydental_category'], ['__count']),
            lambda: Source.formatted_read_group(domain, ['ydental_category'], ['__count']),
            lambda: Source.formatted_read_grouping_sets(domain, [['ydental_category'], []], ['__count']),
            lambda: Source.search_count(domain),
            lambda: Source.name_search('Synthetic', domain),
        )
        for operation in operations:
            previous = Audit.search([], limit=1).id
            self.assertTrue(operation())
            rows = Audit.search([('id', '>', previous)])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows.ydental_event, 'source.query')
            self.assertEqual(rows.ydental_target_id, 0)
            self.assertEqual(rows.ydental_user_id, self.operator)
            payload = json.dumps(rows.read(['ydental_before', 'ydental_after']))
            self.assertNotIn('SYNTHETIC_SPACE', payload)
            self.assertNotIn('ydental_text', payload)
            self.assertIn(rows.id, [row['id'] for row in service._audit_rows()])
        denied = self.bound(self.operator, 'rework-query-denied', self.c)
        with self.assertRaises(AccessError):
            denied.env[Source._name].read_group([], ['ydental_category'], ['__count'])

    def test_rework_company_scope_for_account_actions_and_audits(self):
        limited = new_test_user(self.env, login='s01_rework_limited', groups='ydental_access.ydental_group_manager',
            company_id=self.company_a.id, company_ids=[fields.Command.set(self.company_a.ids)])
        foreign = new_test_user(self.env, login='s01_rework_foreign', groups='ydental_base.ydental_base_group_user',
            company_id=self.company_b.id, company_ids=[fields.Command.set(self.company_b.ids)])
        self.admin._join(foreign.id, self.c.id)
        service = self.bound(limited, 'rework-limited')
        for target in (foreign, self.operator):
            with self.assertRaises(AccessError):
                service._update_profile(target.id, 'Forbidden global change', [])
            with self.assertRaises(AccessError):
                service._depart(target.id)
            with self.assertRaises(AccessError):
                target.with_user(limited).write({'ydental_job_title': 'Forbidden direct profile'})
            self.assertTrue(target.active)
            self.assertNotEqual(target.ydental_job_title, 'Forbidden global change')
        foreign_row = self.admin._audit('foreign.personnel.fixture', 'personnel', foreign, self.c.id)
        global_row = self.admin._audit('foreign.profile.fixture', 'personnel', foreign)
        shared_row = self.admin._audit('shared.profile.fixture', 'personnel', self.operator)
        allowed_row = self.admin._audit('allowed.personnel.fixture', 'personnel', self.a, self.a.id)
        visible = {row['id'] for row in service._audit_rows()}
        self.assertFalse({foreign_row.id, global_row.id, shared_row.id} & visible)
        self.assertIn(allowed_row.id, visible)
        self.assertTrue(self.admin._membership(foreign.id, self.c.id).ydental_employee_id.active)
