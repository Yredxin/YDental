import os
import re

from odoo import fields, models
from odoo.exceptions import AccessError, UserError


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
