import os

import psycopg2

from datetime import datetime

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


def _is_allowed_synthetic_target(enabled, database, oid, cluster, store_id):
    return (enabled == '1' and database == 'ydental_s11_synth_20261023_01'
            and oid == 2171423 and cluster == '7694897083368259627'
            and store_id in (541, 542))


class YDentalSettlementSyntheticSetup(models.AbstractModel):
    _inherit = 'ydental.settlement.service'

    def _synthetic_setup_allowed(self, store):
        user = self.env.user
        if (self.env.su or os.environ.get('YDENTAL_E2E_ISOLATED_FINANCE') != '1'
                or not store or store.id not in (541, 542)
                or not user.active or not user.has_group('base.group_system')
                or not user.has_group('ydental_access.ydental_group_manager')
                or not user.has_group('ydental_access.ydental_system_manager')):
            return False
        access = self.env['ydental.access.service']
        member = access._membership(user.id, store.id)
        if (not store.active or store.company_id not in user.company_ids
                or not member or not member.ydental_employee_id.active
                or access._get_execution_store_id() not in (False, store.id)):
            return False
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute("""SELECT current_database(),
                    (SELECT oid FROM pg_database WHERE datname=current_database()),
                    (pg_control_system()).system_identifier::text""")
                identity = self.env.cr.fetchone()
        except psycopg2.Error:
            return False
        return _is_allowed_synthetic_target(os.environ.get('YDENTAL_E2E_ISOLATED_FINANCE'),
                                            *identity, store.id)

    def _lock_synthetic_actor(self, access):
        # Follow the existing print/access order. The same-value session fence
        # prevents a waiting repeatable-read transaction using an old snapshot.
        access._lock_user(self.env.uid)
        session = access._scope(write=True)
        self.env.cr.execute('UPDATE ydental_access_session SET ydental_revision=ydental_revision WHERE id=%s',
                            [session.id])
        self.env['res.users'].sudo().browse(self.env.uid).lock_for_update(allow_referencing=True)
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        if member:
            member.lock_for_update(allow_referencing=True)
            grants = self.env['ydental.access.grant'].sudo().search([('ydental_membership_id', '=', member.id)])
            for grant in grants.sorted('id'):
                grant.lock_for_update(allow_referencing=True)
            member.ydental_employee_id.sudo().lock_for_update(allow_referencing=True)
        return session

    def _create_synthetic_finance(self, confirmed):
        access = self.env['ydental.access.service']
        store = self._lock_synthetic_actor(access).ydental_store_id
        if not self._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic finance setup is unavailable.'))
        if confirmed is not True:
            raise ValidationError(self.env._('Confirm this isolated synthetic accounting setup.'))
        # Serialize with membership changes and queue execution before finance.
        self.env['ydental.intake.service']._all_locks()
        if access._scope(write=True).ydental_store_id != store:
            raise UserError(self.env._('version_conflict: The store changed. Refresh this page.'))
        if not self._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic finance setup is unavailable.'))
        self._lock()
        if access._scope(write=True).ydental_store_id != store:
            raise UserError(self.env._('version_conflict: The store changed. Refresh this page.'))
        if not self._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic finance setup is unavailable.'))
        Config = self._model('config')
        if Config.search_count([('ydental_store_id', '=', store.id)]):
            raise UserError(self.env._('Synthetic finance setup cannot replace an existing policy.'))
        company = store.company_id
        suffix = str(store.id)
        account_codes = ['E2E%s%s' % (suffix, code) for code in ('I', 'P', 'X', 'C', 'W', 'A', 'D', 'LC', 'LW', 'LA', 'LD')]
        journal_codes = ['T%s%s' % (suffix, code) for code in ('S', 'G', 'C', 'W', 'A', 'D')]
        name = 'E2ER1-20261027-%s synthetic' % suffix
        account_names = [name + ' income', name + ' cash gain', name + ' cash loss'] + [
            name + ' ' + channel + ' outstanding' for channel in ('cash', 'wechat', 'alipay', 'card')] + [
            name + ' ' + channel + ' liquidity' for channel in ('cash', 'wechat', 'alipay', 'card')]
        journal_names = [name + ' sales', name + ' adjustments'] + [name + ' ' + channel
            for channel in ('cash', 'wechat', 'alipay', 'card')]
        # The administrator who prepared these exact test objects has native
        # accounting access; this actor may read only the fixed bounded set.
        Account = self.env['account.account'].sudo().with_company(company).with_context(active_test=False)
        Journal = self.env['account.journal'].sudo().with_company(company).with_context(active_test=False)
        accounts = Account.search([('code', 'in', account_codes), ('company_ids', 'in', company.id)])
        journals = Journal.search([('company_id', '=', company.id), ('code', 'in', journal_codes)])
        accounts_by_code = {account.code: account for account in accounts}
        journals_by_code = {journal.code: journal for journal in journals}
        if len(accounts) != len(account_codes) or set(accounts_by_code) != set(account_codes):
            raise UserError(self.env._('The fixed synthetic accounts have not been prepared.'))
        if len(journals) != len(journal_codes) or set(journals_by_code) != set(journal_codes):
            raise UserError(self.env._('The fixed synthetic journals have not been prepared.'))
        accounts = Account.browse([accounts_by_code[code].id for code in account_codes])
        journals = Journal.browse([journals_by_code[code].id for code in journal_codes])
        # Lock only the fixed synthetic sources, in a stable order, before
        # validating them. Default FOR UPDATE also prevents new FK references.
        for source in accounts.sorted('id'):
            source.lock_for_update()
        for source in journals.sorted('id'):
            source.lock_for_update()
        Method = self.env['account.payment.method.line'].sudo().with_context(active_test=False)
        methods = Method.search([('journal_id', 'in', journals.ids)])
        for source in methods.sorted('id'):
            source.lock_for_update()
        accounts.invalidate_recordset()
        journals.invalidate_recordset()
        methods.invalidate_recordset()
        if access._scope(write=True).ydental_store_id != store:
            raise UserError(self.env._('version_conflict: The store changed. Refresh this page.'))
        if not self._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic finance setup is unavailable.'))
        cutoff = datetime(2026, 10, 27, 14, 0, 0)
        for index, account in enumerate(accounts):
            expected_type = ('income' if index in (0, 1) else 'expense' if index == 2
                             else 'asset_current' if index < 7 else 'asset_cash')
            if (not account.active or account.name != account_names[index] or account.account_type != expected_type
                    or account.create_uid.id != 2 or not account.create_date or account.create_date < cutoff
                    or set(account.company_ids.ids) != {company.id}):
                raise UserError(self.env._('A synthetic account does not match its required source.'))
        for index, journal in enumerate(journals):
            expected_type = 'sale' if index == 0 else 'general' if index == 1 else 'bank'
            if (not journal.active or journal.name != journal_names[index] or journal.type != expected_type
                    or journal.company_id != company or journal.create_uid.id != 2
                    or not journal.create_date or journal.create_date < cutoff or journal.bank_account_id):
                raise UserError(self.env._('A synthetic journal does not match its required source.'))
        if self.env['account.move'].sudo().search_count([('journal_id', 'in', journals.ids)]):
            raise UserError(self.env._('A synthetic journal already has accounting history.'))
        if self.env['account.move.line'].sudo().search_count([('account_id', 'in', accounts.ids)]):
            raise UserError(self.env._('A synthetic account already has accounting history.'))
        if journals[0].default_account_id != accounts[0] or journals[1].default_account_id:
            raise UserError(self.env._('Synthetic sales or adjustment account does not match.'))
        for journal, liquidity in zip(journals[2:], accounts[7:]):
            if (journal.default_account_id != liquidity or journal.profit_account_id != accounts[1]
                    or journal.loss_account_id != accounts[2]):
                raise UserError(self.env._('Synthetic liquidity or difference accounts do not match.'))
        AccountJournal = self.env['account.journal'].sudo().with_context(active_test=False)
        linked = AccountJournal.search(fields.Domain('default_account_id', 'in', accounts.ids)
            | fields.Domain('profit_account_id', 'in', accounts.ids)
            | fields.Domain('loss_account_id', 'in', accounts.ids))
        if set(linked.ids) != set([journals[0].id] + journals[2:].ids):
            raise UserError(self.env._('A synthetic account is assigned to an unexpected journal.'))
        method_lines = self.env['account.payment.method.line'].sudo().with_context(active_test=False).search([
            ('payment_account_id', 'in', accounts.ids),
        ])
        if set(method_lines.mapped('journal_id').ids) != set(journals[2:].ids):
            raise UserError(self.env._('A synthetic payment account is assigned outside its journal.'))
        # A fixed new source may not be associated with any other store policy.
        journal_fields = ('ydental_sales_journal_id', 'ydental_adjustment_journal_id',
                          'ydental_cash_journal_id', 'ydental_wechat_journal_id',
                          'ydental_alipay_journal_id', 'ydental_card_journal_id',
                          'ydental_purchase_journal_id')
        account_fields = ('ydental_income_account_id', 'ydental_expense_account_id')
        existing_sources = fields.Domain.OR(
            [fields.Domain(field, 'in', journals.ids) for field in journal_fields]
            + [fields.Domain(field, 'in', accounts.ids) for field in account_fields])
        if Config.search_count(existing_sources):
            raise UserError(self.env._('A synthetic source is already assigned to another policy.'))
        values = {'ydental_store_id': store.id, 'company_id': company.id,
                  'ydental_policy': 'demo_confirmation', 'ydental_sales_journal_id': journals[0].id,
                  'ydental_adjustment_journal_id': journals[1].id,
                  'ydental_income_account_id': accounts[0].id}
        for channel, journal, account in zip(('cash', 'wechat', 'alipay', 'card'), journals[2:], accounts[3:7]):
            inbound = journal.inbound_payment_method_line_ids.filtered(lambda row: row.payment_method_id.code == 'manual')
            outbound = journal.outbound_payment_method_line_ids.filtered(lambda row: row.payment_method_id.code == 'manual')
            methods = journal.inbound_payment_method_line_ids | journal.outbound_payment_method_line_ids
            if ('payment_provider_id' in methods._fields and methods.mapped('payment_provider_id')):
                raise UserError(self.env._('A synthetic journal cannot have an external payment provider.'))
            if (len(journal.inbound_payment_method_line_ids) != 1
                    or len(journal.outbound_payment_method_line_ids) != 1
                    or len(inbound) != 1 or len(outbound) != 1 or inbound.payment_account_id != account
                    or outbound.payment_account_id != account):
                raise UserError(self.env._('Synthetic manual payment accounts do not match.'))
            values['ydental_' + channel + '_journal_id'] = journal.id
        # This fixed-model creation only links the validated synthetic test objects.
        config = Config._new(values)
        self._config(store)
        access._audit('settlement.synthetic_setup', 'personnel', config, store.id,
                      after={'company_id': company.id, 'account_ids': accounts.ids,
                             'journal_ids': journals.ids, 'policy': 'demo_confirmation'},
                      source='isolated_synthetic_setup')
        return {'config_id': config.id, 'store_id': store.id,
                'account_ids': accounts.ids, 'journal_ids': journals.ids}


class YDentalAccessSyntheticSetup(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _dashboard(self):
        values = super()._dashboard()
        values['can_setup_synthetic_finance'] = self.env['ydental.settlement.service']._synthetic_setup_allowed(
            self._scope().ydental_store_id)
        return values
