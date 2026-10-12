from dataclasses import dataclass

import os
import re

from odoo import fields, models
from odoo.exceptions import AccessError, UserError
from odoo.addons.ydental_intake.models.ydental_intake_service import fingerprint



@dataclass(frozen=True)
class SyntheticReferralPermit:
    actor_id: int
    store_id: int
    operation: str
    fingerprint: str
    category: str


def guard(env):
    if not re.fullmatch(r'ydental_s05_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not os.environ.get('YDENTAL_S05_RUN_DIR'):
        raise AccessError('Synthetic intake adapter refused outside isolated S05 validation.')


class SyntheticQueue(models.Model):
    _name = 'ydental.intake.test.queue'
    _description = 'Test-only waiting/calling adapter, never a production queue'

    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict')
    ydental_active = fields.Boolean(default=True)
    state = fields.Selection([('waiting', 'Synthetic waiting'), ('calling', 'Synthetic calling'), ('void', 'Synthetic revoked')], default='waiting')


class YDentalIntakeService(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _synthetic_referral_action(self, operation, payload, key):
        guard(self.env)
        store, category = self._referral_access()
        task = self._get('task', payload['source_task_id'], store)
        category = 'exam' if task.ydental_mapping_id.ydental_catalog_id.ydental_kind == 'exam' else 'medical'
        self._referral_access(category)
        permit = SyntheticReferralPermit(self.env.uid, store.id, operation, fingerprint(payload), category)
        return self._referral_action(operation, payload, key, permit=permit)

    def _authorize_referral(self, operation, payload, permit):
        guard(self.env)
        if type(permit) is not SyntheticReferralPermit:
            raise AccessError('Synthetic referral requires an exact, server-created clinical permit.')
        store, category = self._referral_access(permit.category)
        if (
            permit.actor_id, permit.store_id, permit.operation, permit.fingerprint
        ) != (self.env.uid, store.id, operation, fingerprint(payload)):
            raise AccessError('Synthetic referral requires an exact, server-created clinical permit.')
        task = self._get('task', payload['source_task_id'], store)
        self._version(task, payload['version'])
        if task.state not in ('started', 'done'):
            raise AccessError('Synthetic referral requires a fixed actual encounter stand-in.')
        expected = 'exam' if task.ydental_mapping_id.ydental_catalog_id.ydental_kind == 'exam' else 'medical'
        if category != expected:
            raise AccessError('Synthetic source category does not match the encounter stand-in.')
        return category

    def _queue_accept(self, task, previous):
        guard(self.env)
        config = self.env['ir.config_parameter'].sudo()
        if config.get_str('ydental_intake_test.refuse_task') == str(task.id):
            raise UserError('Synthetic target queue refusal after qualification acquisition.')
        self.env['ydental.intake.test.queue'].sudo().create({'ydental_task_id': task.id, 'ydental_patient_id': task.ydental_patient_id.id})
        return {'queue_status': 'synthetic_waiting', 'queue_contract': 'test_only'}

    def _queue_void(self, position, reason):
        guard(self.env)
        self.env['ydental.intake.test.queue'].sudo().search([
            ('ydental_task_id', '=', position.ydental_task_id.id), ('ydental_active', '=', True)]).write({'ydental_active': False, 'state': 'void'})

    def _authorize_downstream(self, operation, payload):
        guard(self.env)
        return self.env['ydental.access.service']._check('medical', 'write', write=True).ydental_store_id


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _allow_demo_supply(self):
        guard(self.env)
        return True

    def _check_queue_empty(self, business):
        guard(self.env)
        if self.env['ydental.intake.test.queue'].sudo().search_count([
            ('ydental_task_id.ydental_store_id', '=', business.ydental_store_id.id),
            ('ydental_task_id.ydental_mapping_id.ydental_area_id', '=', business.ydental_area_id.id),
            ('ydental_active', '=', True)]):
            raise UserError('Synthetic waiting/calling remains in target area.')


class YDentalPatientService(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _migrate_business(self, source_ids, target):
        guard(self.env)
        counts = super()._migrate_business(source_ids, target)
        rows = self.env['ydental.intake.test.queue'].sudo().search([
            ('ydental_patient_id', 'in', source_ids), ('ydental_active', '=', True)])
        rows.write({'ydental_patient_id': target.id})
        return counts | {'synthetic_queue': len(rows)}
