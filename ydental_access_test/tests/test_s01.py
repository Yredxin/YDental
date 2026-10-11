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
        template.ydental_levels = {'frontdesk': 'read'}
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.a.id)), levels)
        self.assertEqual(self.admin._levels(self.admin._membership(self.operator.id, self.b.id))['space'], 'read')
        manager = self.bound(self.manager, 't09', self.a)
        with self.assertRaises(AccessError):
            manager._template_preview(template.id, [[self.operator.id, self.a.id], [self.operator.id, self.b.id]])
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
        operator = self.bound(self.operator, 't13', self.a).with_context(ydental_purpose='care')
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
