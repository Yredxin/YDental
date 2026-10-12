from dataclasses import dataclass
from datetime import datetime
import os
import re

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError


def guard(env):
    if not re.fullmatch(r'ydental_s06a_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or not os.environ.get('YDENTAL_S06A_RUN_DIR'):
        raise AccessError('S06-A synthetic adapter refused outside the isolated validation run.')


@dataclass(frozen=True)
class Clock:
    now: datetime


@dataclass(frozen=True)
class DocumentSource:
    key: str
    lease_id: int
    token: str


@dataclass(frozen=True)
class QualificationSource:
    actor_id: int
    task_id: int
    station_id: int
    requirement: str
    satisfied: bool


QUALIFICATION_MUTATION = object()


class SyntheticQualification(models.Model):
    _name = 'ydental.queue.test.qualification'
    _description = 'Guarded synthetic service qualification provider, not staff qualification business'

    ydental_actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_station_id = fields.Many2one('ydental.space.station', required=True, ondelete='restrict')
    ydental_requirement = fields.Char(required=True)
    ydental_satisfied = fields.Boolean()

    _one_source = models.Constraint('UNIQUE(ydental_actor_id, ydental_task_id, ydental_station_id, ydental_requirement)',
                                   'One synthetic qualification fact per fixed source.')

    @api.model_create_multi
    def create(self, vals_list):
        guard(self.env)
        if self.env.context.get('ydental_queue_test_qualification') is not QUALIFICATION_MUTATION:
            raise AccessError('A frozen server qualification source is required.')
        return super().create(vals_list)

    def write(self, vals):
        guard(self.env)
        if self.env.context.get('ydental_queue_test_qualification') is not QUALIFICATION_MUTATION:
            raise AccessError('A frozen server qualification source is required.')
        return super().write(vals)


class SyntheticDocumentLock(models.Model):
    _name = 'ydental.queue.test.document'
    _description = 'Synthetic independent document lock source, never a clinical document'

    ydental_key = fields.Char(required=True)
    ydental_lease_id = fields.Many2one('ydental.queue.lease', required=True, ondelete='restrict')
    ydental_active = fields.Boolean(default=True)

    _one_editor = models.UniqueIndex('(ydental_key) WHERE ydental_active')


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _test_qualification(self, source):
        guard(self.env)
        if type(source) is not QualificationSource or type(source.satisfied) is not bool:
            raise AccessError('A frozen server qualification source is required.')
        Provider = self.env['ydental.queue.test.qualification'].sudo().with_context(
            ydental_queue_test_qualification=QUALIFICATION_MUTATION)
        values = {'ydental_actor_id': source.actor_id, 'ydental_task_id': source.task_id,
                  'ydental_station_id': source.station_id, 'ydental_requirement': source.requirement}
        fact = Provider.search(list((key, '=', value) for key, value in values.items()), limit=1)
        if fact:
            fact.write({'ydental_satisfied': source.satisfied})
        else:
            Provider.create(dict(values, ydental_satisfied=source.satisfied))

    def _qualification_satisfied(self, task, station, actor):
        guard(self.env)
        fact = self.env['ydental.queue.test.qualification'].sudo().search([
            ('ydental_actor_id', '=', actor.id), ('ydental_task_id', '=', task.id),
            ('ydental_station_id', '=', station.id),
            ('ydental_requirement', '=', task.ydental_mapping_id.ydental_catalog_id.ydental_qualification)], limit=1)
        return bool(fact and fact.ydental_satisfied) or super()._qualification_satisfied(task, station, actor)

    def _now(self):
        clock = self.env.context.get('ydental_queue_test_clock')
        if type(clock) is Clock:
            guard(self.env)
            return clock.now
        return super()._now()

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
