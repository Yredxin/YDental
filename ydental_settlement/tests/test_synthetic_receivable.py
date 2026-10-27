from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError
from odoo.tests import TransactionCase, new_test_user, tagged

from odoo.addons.ydental_settlement.models import ydental_synthetic_receivable as binding


@tagged('post_install', '-at_install', 's13_synthetic_receivable')
class TestSyntheticReceivable(TransactionCase):
    def setUp(self):
        super().setUp()
        self.actor = new_test_user(self.env, login='s13_receivable_manager',
            groups='base.group_user,base.group_system,ydental_base.ydental_base_group_user,'
                   'ydental_access.ydental_group_manager,ydental_access.ydental_system_manager')
        self.store = self.env['ydental.access.store'].sudo().create({
            'name': 'Synthetic receivable store', 'company_id': self.env.company.id, 'ydental_timezone': 'UTC',
        })
        access = self.env['ydental.access.service'].with_user(self.actor)
        session = access._session_for_key('s13-receivable-manager')
        access = access._bind(session)
        access._join(self.actor.id, self.store.id)
        access._grant(self.actor.id, self.store.id, {'medical': 'write', 'patient': 'write'})
        access._switch(self.store.id)
        self.access = access._bind(session)
        self.service = self.access.env['ydental.patient.service']
        result = self.service._operate('create', {
            'values': {'name': 'E2ER1-20261027-SYNTH-PATIENT-04'},
        }, 's13-receivable-patient')
        patient = self.env['ydental.patient'].sudo().browse(result['id'])
        partner = patient.ydental_partner_id
        self.patient = patient
        self.partner = partner
        self.account = self.env['account.account'].with_user(2).create({
            'name': 'E2ER1-20261027-541 synthetic receivable', 'code': 'E2E541R',
            'account_type': 'asset_receivable', 'reconcile': True,
            'company_ids': [Command.link(self.env.company.id)],
        })
        self.patches = patch.multiple(binding, _E2E_PATIENT_ID=patient.id, _E2E_PARTNER_ID=partner.id,
            _E2E_ACTOR_ID=self.actor.id, _E2E_CREATOR_ID=self.actor.id, _E2E_STORE_ID=self.store.id,
            _E2E_PATIENT_NUMBER=patient.ydental_number)
        self.patches.start()
        self.addCleanup(self.patches.stop)
        finance = type(self.env['ydental.settlement.service'])
        self.scope_patch = patch.object(finance, '_synthetic_setup_allowed', return_value=True)
        self.scope_patch.start()
        self.addCleanup(self.scope_patch.stop)

    def test_bind_once_and_preserve_contact_guard(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.partner.with_user(self.actor).write({'name': 'Unauthorized'})
        result = self.service._bind_e2e_synthetic_receivable(True)
        self.assertEqual(result['account_id'], self.account.id)
        self.assertEqual(self.partner.with_company(self.env.company).property_account_receivable_id, self.account)
        self.assertTrue(self.env['ydental.access.audit'].sudo().search_count([
            ('ydental_event', '=', 'patient.synthetic_receivable_bound'), ('ydental_user_id', '=', self.actor.id)]))
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)

    def test_existing_explicit_receivable_is_not_overwritten(self):
        self.partner._ydental_patient_save({'property_account_receivable_id': self.account.id})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        self.assertEqual(self.partner.with_company(self.env.company).property_account_receivable_id, self.account)

    def test_disabled_and_wrong_actor_do_not_bind(self):
        finance = type(self.env['ydental.settlement.service'])
        with patch.object(finance, '_synthetic_setup_allowed', return_value=False):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.service._bind_e2e_synthetic_receivable(True)
        with patch.object(binding, '_E2E_ACTOR_ID', -1):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.service._bind_e2e_synthetic_receivable(True)
        self.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [self.partner.id])
        self.assertIsNone(self.cr.fetchone()[0])
        self.assertFalse(self.env['ydental.access.audit'].sudo().search_count([
            ('ydental_event', '=', 'patient.synthetic_receivable_bound')]))

    def test_shared_contact_or_account_is_rejected(self):
        child = self.env['res.partner'].with_user(2).create({'name': 'Synthetic child', 'parent_id': self.partner.id})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        child.with_user(2).unlink()
        other = self.env['res.partner'].with_user(2).create({'name': 'Synthetic other'})
        other.with_company(self.env.company).write({'property_account_receivable_id': self.account.id})
        other.flush_recordset(['property_account_receivable_id'])
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        self.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [self.partner.id])
        self.assertIsNone(self.cr.fetchone()[0])
        self.assertFalse(self.env['ydental.access.audit'].sudo().search_count([
            ('ydental_event', '=', 'patient.synthetic_receivable_bound')]))

    def test_existing_draft_accounting_and_invalid_account_are_rejected(self):
        self.account.with_user(2).write({'name': 'Wrong synthetic source'})
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        self.account.with_user(2).write({'name': 'E2ER1-20261027-541 synthetic receivable'})
        journal = self.env['account.journal'].with_user(2).create({
            'name': 'Synthetic draft journal', 'code': 'SRDJ', 'type': 'general', 'company_id': self.env.company.id,
        })
        self.env['account.move'].with_user(2).create({
            'move_type': 'entry', 'journal_id': journal.id, 'date': fields.Date.today(), 'partner_id': self.partner.id,
        })
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        self.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [self.partner.id])
        self.assertIsNone(self.cr.fetchone()[0])
        self.assertFalse(self.env['ydental.access.audit'].sudo().search_count([
            ('ydental_event', '=', 'patient.synthetic_receivable_bound')]))

    def test_other_company_property_is_not_overwritten(self):
        other_company = self.env['res.company'].sudo().create({'name': 'Other synthetic company'})
        other_account = self.env['account.account'].sudo().with_company(other_company).create({
            'name': 'Other synthetic receivable', 'code': 'E2OTHERR',
            'account_type': 'asset_receivable', 'reconcile': True,
            'company_ids': [Command.link(other_company.id)],
        })
        self.partner.sudo().with_company(other_company)._ydental_patient_save({
            'property_account_receivable_id': other_account.id,
        })
        self.partner.flush_recordset(['property_account_receivable_id'])
        self.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [self.partner.id])
        before = self.cr.fetchone()[0]
        with self.assertRaises(UserError), self.cr.savepoint():
            self.service._bind_e2e_synthetic_receivable(True)
        self.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [self.partner.id])
        self.assertEqual(self.cr.fetchone()[0], before)
        self.assertFalse(self.env['ydental.access.audit'].sudo().search_count([
            ('ydental_event', '=', 'patient.synthetic_receivable_bound')]))
