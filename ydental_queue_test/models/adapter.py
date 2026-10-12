from dataclasses import dataclass
import os
import re

from odoo import fields, models
from odoo.exceptions import AccessError, UserError


def guard(env):
    if not re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not os.environ.get('YDENTAL_S06A_RUN_DIR'):
        raise AccessError('S06-A synthetic adapter refused outside the isolated validation run.')


@dataclass(frozen=True)
class DocumentSource:
    key: str
    lease_id: int
    token: str


class SyntheticDocumentLock(models.Model):
    _name = 'ydental.queue.test.document'
    _description = 'Synthetic independent document lock source, never a clinical document'

    ydental_key = fields.Char(required=True)
    ydental_lease_id = fields.Many2one('ydental.queue.lease', required=True, ondelete='restrict')
    ydental_active = fields.Boolean(default=True)

    _one_editor = models.UniqueIndex('(ydental_key) WHERE ydental_active')


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _document_lock(self, source, operation):
        guard(self.env)
        if type(source) is not DocumentSource or operation not in ('acquire', 'release'):
            raise AccessError('A fixed synthetic document source is required.')
        self._connection()
        with self.env.cr.savepoint():
            self._locks()
            self._expire()
            lease = self._held(source.lease_id, source.token)
            Lock = self.env['ydental.queue.test.document'].sudo()
            Lock.search([('ydental_active', '=', True), ('ydental_lease_id.ydental_active', '=', False)]).write({'ydental_active': False})
            existing = Lock.search([('ydental_key', '=', source.key), ('ydental_active', '=', True)], limit=1)
            if existing and existing.ydental_lease_id != lease:
                raise UserError('Synthetic independent document already has an editor.')
            if operation == 'release':
                existing.write({'ydental_active': False})
                return {'released': True}
            if not existing:
                existing = Lock.create({'ydental_key': source.key, 'ydental_lease_id': lease.id})
            return {'id': existing.id}


class YDentalIntakeService(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _queue_accept(self, task, previous):
        guard(self.env)
        result = super()._queue_accept(task, previous)
        if self.env['ir.config_parameter'].sudo().get_str('ydental_queue_test.refuse_task') == str(task.id):
            raise UserError('Synthetic fault after real queue accept, test rollback only.')
        return result


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _allow_demo_supply(self):
        guard(self.env)
        return True
