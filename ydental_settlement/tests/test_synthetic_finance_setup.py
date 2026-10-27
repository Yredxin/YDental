from types import SimpleNamespace
from unittest.mock import patch

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged

from odoo.addons.ydental_settlement.models.ydental_settlement_synthetic_setup import _is_allowed_synthetic_target


@tagged('post_install', '-at_install', 's13_synthetic_finance')
class TestSyntheticFinanceSetup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.actor = new_test_user(cls.env, login='s13_synthetic_finance_manager',
            groups='base.group_user,base.group_system,ydental_base.ydental_base_group_user,'
                   'ydental_access.ydental_group_manager,ydental_access.ydental_system_manager')
        cls.company = cls.env.company
        cls.store = cls.env['ydental.access.store'].sudo().create({
            'name': 'Synthetic finance setup store', 'company_id': cls.company.id, 'ydental_timezone': 'UTC',
        })
        cls.service = cls.env['ydental.settlement.service'].with_user(cls.actor)

    def _sources(self):
        Account = self.env['account.account'].with_user(2).with_company(self.company).with_context(
            skip_auto_account_journal_creation=True)
        Journal = self.env['account.journal'].with_user(2).with_company(self.company)
        suffix = str(self.store.id)
        name = 'E2ER1-20261027-%s synthetic' % suffix
        accounts = Account.create([{
            'name': name + ' income', 'code': 'E2E%sI' % suffix,
            'account_type': 'income', 'company_ids': [Command.link(self.company.id)],
        }, {
            'name': name + ' cash gain', 'code': 'E2E%sP' % suffix,
            'account_type': 'income', 'company_ids': [Command.link(self.company.id)],
        }, {
            'name': name + ' cash loss', 'code': 'E2E%sX' % suffix,
            'account_type': 'expense', 'company_ids': [Command.link(self.company.id)],
        }] + [{
            'name': name + ' ' + channel + ' outstanding', 'code': 'E2E%s%s' % (suffix, letter),
            'account_type': 'asset_current', 'company_ids': [Command.link(self.company.id)],
        } for channel, letter in zip(('cash', 'wechat', 'alipay', 'card'), ('C', 'W', 'A', 'D'))] + [{
            'name': name + ' ' + channel + ' liquidity', 'code': 'E2E%sL%s' % (suffix, letter),
            'account_type': 'asset_cash', 'company_ids': [Command.link(self.company.id)],
        } for channel, letter in zip(('cash', 'wechat', 'alipay', 'card'), ('C', 'W', 'A', 'D'))])
        journals = Journal.create([{
            'name': name + ' sales', 'code': 'T%sS' % suffix, 'type': 'sale', 'company_id': self.company.id,
            'default_account_id': accounts[0].id,
        }, {
            'name': name + ' adjustments', 'code': 'T%sG' % suffix, 'type': 'general', 'company_id': self.company.id,
        }] + [{
            'name': name + ' ' + channel, 'code': 'T%s%s' % (suffix, letter),
            'type': 'bank', 'company_id': self.company.id, 'default_account_id': liquidity.id,
            'profit_account_id': accounts[1].id, 'loss_account_id': accounts[2].id,
        } for channel, letter, liquidity in zip(('cash', 'wechat', 'alipay', 'card'), ('C', 'W', 'A', 'D'), accounts[7:])])
        for journal, account in zip(journals[2:], accounts[3:7]):
            methods = (journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids).filtered(
                lambda row: row.payment_method_id.code == 'manual')
            methods.write({'payment_account_id': account.id})
        return accounts, journals

    def test_identity_guard_requires_every_exact_component(self):
        args = ('1', 'ydental_s11_synth_20261023_01', 2171423, '7694897083368259627', 541)
        self.assertTrue(_is_allowed_synthetic_target(*args))
        for index, value in enumerate(('0', 'other', 1, 'other', 1)):
            candidate = list(args)
            candidate[index] = value
            self.assertFalse(_is_allowed_synthetic_target(*candidate))

    def test_default_closed_and_explicit_confirmation(self):
        self.assertFalse(self.service._synthetic_setup_allowed(self.store))
        access = type(self.env['ydental.access.service'])
        setup = type(self.service)
        with patch.object(setup, '_lock_synthetic_actor', return_value=SimpleNamespace(ydental_store_id=self.store)):
            with self.assertRaises(AccessError), self.cr.savepoint():
                self.service._create_synthetic_finance(True)
            with patch.object(setup, '_synthetic_setup_allowed', return_value=True):
                with self.assertRaises(ValidationError), self.cr.savepoint():
                    self.service._create_synthetic_finance(False)

    def test_stale_scope_rejected_before_setup(self):
        session = self.env['ydental.access.session'].sudo().create({
            'ydental_key_hash': 's13-synthetic-finance-stale-scope',
            'ydental_user_id': self.actor.id, 'ydental_store_id': self.store.id, 'ydental_revision': 0,
        })
        access = self.env['ydental.access.service'].with_user(self.actor)._bind(session)
        service = access.env['ydental.settlement.service']
        session.sudo().write({'ydental_revision': 1})
        with patch.object(type(service), '_synthetic_setup_allowed', return_value=True):
            with self.assertRaisesRegex(UserError, 'version_conflict'), self.cr.savepoint():
                service._create_synthetic_finance(True)
        self.assertFalse(self.env['ydental.settlement.config'].sudo().search([
            ('ydental_store_id', '=', self.store.id),
        ]))

    def test_fixed_sources_create_once_and_reject_replacement(self):
        accounts, journals = self._sources()
        linked = self.env['account.journal'].sudo().with_context(active_test=False).search(
            fields.Domain('default_account_id', 'in', accounts.ids)
            | fields.Domain('profit_account_id', 'in', accounts.ids)
            | fields.Domain('loss_account_id', 'in', accounts.ids))
        self.assertEqual(set(linked.ids), set([journals[0].id] + journals[2:].ids),
                         'Unexpected synthetic fixture journal associations.')
        access = type(self.env['ydental.access.service'])
        setup = type(self.service)
        with patch.object(access, '_scope', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_lock_synthetic_actor', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_synthetic_setup_allowed', return_value=True):
            result = self.service._create_synthetic_finance(True)
            self.assertEqual(result['account_ids'], accounts.ids)
            self.assertEqual(result['journal_ids'], journals.ids)
            config = self.env['ydental.settlement.config'].sudo().browse(result['config_id'])
            self.assertEqual(config.ydental_policy, 'demo_confirmation')
            self.assertTrue(self.env['ydental.access.audit'].sudo().search_count([
                ('ydental_event', '=', 'settlement.synthetic_setup'),
                ('ydental_user_id', '=', self.actor.id), ('ydental_target_id', '=', config.id),
            ]))
            with self.assertRaises(UserError), self.cr.savepoint():
                self.service._create_synthetic_finance(True)
            self.assertEqual(self.env['ydental.settlement.config'].sudo().search_count([
                ('ydental_store_id', '=', self.store.id),
            ]), 1)

    def test_wrong_manual_account_rejected_before_config(self):
        accounts, journals = self._sources()
        inbound = journals[2].inbound_payment_method_line_ids.filtered(lambda row: row.payment_method_id.code == 'manual')
        inbound.with_user(2).write({'payment_account_id': accounts[4].id})
        access = type(self.env['ydental.access.service'])
        setup = type(self.service)
        with patch.object(access, '_scope', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_lock_synthetic_actor', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_synthetic_setup_allowed', return_value=True):
            with self.assertRaises(UserError), self.cr.savepoint():
                self.service._create_synthetic_finance(True)
        self.assertFalse(self.env['ydental.settlement.config'].sudo().search([
            ('ydental_store_id', '=', self.store.id),
        ]))

    def test_reject_mismatched_liquidity_and_existing_policy_use(self):
        accounts, journals = self._sources()
        access = type(self.env['ydental.access.service'])
        setup = type(self.service)
        with patch.object(access, '_scope', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_lock_synthetic_actor', return_value=SimpleNamespace(ydental_store_id=self.store)), \
                patch.object(setup, '_synthetic_setup_allowed', return_value=True):
            with self.cr.savepoint():
                journals[2].with_user(2).write({'default_account_id': accounts[8].id})
                with self.assertRaises(UserError), self.cr.savepoint():
                    self.service._create_synthetic_finance(True)
            journals[2].with_user(2).write({'default_account_id': accounts[7].id})
            other = self.env['ydental.access.store'].sudo().create({
                'name': 'Other synthetic finance store', 'company_id': self.company.id, 'ydental_timezone': 'UTC',
            })
            self.env['ydental.settlement.config']._new({
                'ydental_store_id': other.id, 'company_id': self.company.id,
                'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': journals[0].id,
                'ydental_adjustment_journal_id': journals[1].id, 'ydental_income_account_id': accounts[0].id,
                'ydental_cash_journal_id': journals[2].id, 'ydental_wechat_journal_id': journals[3].id,
                'ydental_alipay_journal_id': journals[4].id, 'ydental_card_journal_id': journals[5].id,
            })
            with self.assertRaises(UserError), self.cr.savepoint():
                self.service._create_synthetic_finance(True)
        self.assertFalse(self.env['ydental.settlement.config'].sudo().search([
            ('ydental_store_id', '=', self.store.id),
        ]))


@tagged('post_install', '-at_install', 's13_synthetic_finance_http')
class TestSyntheticFinanceSetupHTTP(HttpCase):
    def test_default_closed_route_rejects_authenticated_user(self):
        user = new_test_user(self.env, login='s13_finance_http_user',
                             groups='base.group_user,ydental_base.ydental_base_group_user')
        count = self.env['ydental.settlement.config'].sudo().search_count([])
        self.authenticate(user.login, user.login)
        response = self.url_open('/ydental/settlement/synthetic-setup', allow_redirects=False)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.env['ydental.settlement.config'].sudo().search_count([]), count)
