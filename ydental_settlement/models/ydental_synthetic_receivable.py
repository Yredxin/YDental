from datetime import datetime

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


_E2E_PATIENT_ID = 1647
_E2E_PARTNER_ID = 3372
_E2E_ACTOR_ID = 1541
_E2E_CREATOR_ID = 1543
_E2E_STORE_ID = 541
_E2E_PATIENT_NAME = 'E2ER1-20261027-SYNTH-PATIENT-04'
_E2E_PATIENT_NUMBER = 'P00001647'


class YDentalPatientSyntheticReceivable(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _bind_e2e_synthetic_receivable(self, confirmed):
        """Bind only the fixed E2E patient through the protected patient service."""
        access = self.env['ydental.access.service']
        finance = self.env['ydental.settlement.service']
        store = finance._lock_synthetic_actor(access).ydental_store_id
        if self.env.uid != _E2E_ACTOR_ID or store.id != _E2E_STORE_ID or not finance._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic patient receivable setup is unavailable.'))
        if confirmed is not True:
            raise ValidationError(self.env._('Confirm this isolated synthetic patient receivable binding.'))
        self.env['ydental.intake.service']._all_locks()
        finance._lock()
        if access._scope(write=True).ydental_store_id != store or not finance._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic patient receivable setup is unavailable.'))
        company = store.company_id
        if company.id != 1:
            raise AccessError(self.env._('access_denied: Synthetic patient company is unavailable.'))
        Patient = self.env['ydental.patient'].sudo().with_context(active_test=False)
        Partner = self.env['res.partner'].sudo().with_context(active_test=False)
        Account = self.env['account.account'].sudo().with_company(company).with_context(active_test=False)
        patient = Patient.browse(_E2E_PATIENT_ID).exists()
        partner = Partner.browse(_E2E_PARTNER_ID).exists()
        accounts = Account.search([('code', '=', 'E2E541R'), ('company_ids', 'in', company.id)])
        if not patient or not partner or len(accounts) != 1:
            raise UserError(self.env._('The fixed synthetic patient and receivable source are required.'))
        account = accounts[0]
        for record in (patient, partner, account):
            record.lock_for_update()
            record.invalidate_recordset()
        if access._scope(write=True).ydental_store_id != store or not finance._synthetic_setup_allowed(store):
            raise AccessError(self.env._('access_denied: Synthetic patient receivable setup is unavailable.'))
        self._current_relation(patient, store)
        if (patient.name != _E2E_PATIENT_NAME
                or patient.ydental_number != _E2E_PATIENT_NUMBER or patient.create_uid.id != _E2E_CREATOR_ID
                or partner.name != patient.name or partner.create_uid.id != _E2E_CREATOR_ID
                or patient.ydental_partner_id != partner or partner.ydental_patient_owner_id != patient
                or Patient.search_count([('ydental_partner_id', '=', partner.id)]) != 1
                or patient.ydental_merged_into_id or partner.parent_id or partner.commercial_partner_id != partner
                or Partner.search_count([('parent_id', '=', partner.id)])
                or Partner.search_count([('commercial_partner_id', '=', partner.id), ('id', '!=', partner.id)])
                or self.env['res.users'].sudo().with_context(active_test=False).search_count([('partner_id', '=', partner.id)])):
            raise UserError(self.env._('The synthetic patient contact is shared or has an incompatible identity.'))
        if (not account.active or account.name != 'E2ER1-20261027-541 synthetic receivable'
                or account.create_uid.id != 2 or not account.create_date
                or account.create_date < datetime(2026, 10, 27, 14, 0, 0)
                or set(account.company_ids.ids) != {company.id}
                or account.account_type != 'asset_receivable' or not account.reconcile):
            raise UserError(self.env._('The synthetic receivable account is invalid.'))
        # Read all company-dependent JSON keys, including other companies. ORM
        # access by one company alone would miss a pre-existing property.
        self.env.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [partner.id])
        property_value = self.env.cr.fetchone()[0]
        if property_value is not None:
            raise UserError(self.env._('An existing patient receivable cannot be replaced.'))
        self.env.cr.execute("""SELECT count(*) FROM res_partner p
            CROSS JOIN LATERAL jsonb_each_text(COALESCE(p.property_account_receivable_id, '{}'::jsonb)) v
            WHERE v.value = %s""", [str(account.id)])
        if self.env.cr.fetchone()[0]:
            raise UserError(self.env._('The synthetic receivable is already assigned.'))
        if (self.env['account.move'].sudo().search_count([('partner_id', '=', partner.id)])
                or self.env['account.move.line'].sudo().search_count(
                    fields.Domain('partner_id', '=', partner.id) | fields.Domain('account_id', '=', account.id))
                or self.env['account.journal'].sudo().with_context(active_test=False).search_count(
                    fields.Domain('default_account_id', '=', account.id)
                    | fields.Domain('profit_account_id', '=', account.id)
                    | fields.Domain('loss_account_id', '=', account.id))
                or self.env['account.payment.method.line'].sudo().with_context(active_test=False).search_count(
                    [('payment_account_id', '=', account.id)])):
            raise UserError(self.env._('The synthetic patient or receivable has accounting history.'))
        # Keep the real actor and normal ORM authorization. Only the patient
        # service can reach the protected contact mutation hook.
        self.env['res.partner'].browse(partner.id).with_company(company)._ydental_patient_save({
            'property_account_receivable_id': account.id,
        })
        self.env['res.partner'].browse(partner.id).flush_recordset(['property_account_receivable_id'])
        self.env.cr.execute('SELECT property_account_receivable_id FROM res_partner WHERE id=%s', [partner.id])
        stored = self.env.cr.fetchone()[0]
        if not isinstance(stored, dict) or set(stored) != {'1'} or int(stored['1']) != account.id:
            raise UserError(self.env._('The synthetic patient receivable binding was not stored as expected.'))
        access._audit('patient.synthetic_receivable_bound', 'patient', patient, store.id,
            before={'explicit_receivable': False},
            after={'partner_id': partner.id, 'account_id': account.id, 'company_id': company.id},
            source='isolated_synthetic_setup')
        return {'patient_id': patient.id, 'partner_id': partner.id, 'account_id': account.id}
