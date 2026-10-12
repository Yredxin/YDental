from dataclasses import dataclass

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .adapter import guard


MUTATION = object()


@dataclass(frozen=True)
class ReturnSource:
    execution_id: int
    target_task_id: int = 0
    save_ok: bool = False
    document_key: str = ''


@dataclass(frozen=True)
class ReturnPlan:
    task_id: int
    target_task_id: int
    save_ok: bool


class SyntheticReturnPlan(models.Model):
    _name = 'ydental.queue.test.return.plan'
    _description = 'Guarded synthetic source prepared before an HTTP execution'

    ydental_task_id = fields.Many2one('ydental.intake.task', required=True, ondelete='restrict')
    ydental_target_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    ydental_save_ok = fields.Boolean()
    _one_task = models.Constraint('UNIQUE(ydental_task_id)', 'One frozen synthetic plan per task.')

    @api.model_create_multi
    def create(self, vals_list):
        guard(self.env)
        if self.env.context.get('ydental_return_test_source') is not MUTATION:
            raise AccessError('Frozen test source required.')
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError('Synthetic return plans are immutable.')


class SyntheticReturnSource(models.Model):
    _name = 'ydental.queue.test.return.source'
    _description = 'Guarded frozen external order and draft-save test source'

    ydental_execution_id = fields.Many2one('ydental.queue.execution', required=True, ondelete='restrict')
    ydental_target_task_id = fields.Many2one('ydental.intake.task', ondelete='restrict')
    ydental_save_ok = fields.Boolean()
    ydental_document_key = fields.Char()
    ydental_saved = fields.Integer(default=0)

    _one_execution = models.Constraint('UNIQUE(ydental_execution_id)', 'One synthetic source per segment.')

    @api.model_create_multi
    def create(self, vals_list):
        guard(self.env)
        if self.env.context.get('ydental_return_test_source') is not MUTATION:
            raise AccessError('Frozen test source required.')
        return super().create(vals_list)

    def write(self, vals):
        guard(self.env)
        if self.env.context.get('ydental_return_test_source') is not MUTATION:
            raise AccessError('Frozen test source required.')
        return super().write(vals)


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _test_return_plan(self, plan):
        guard(self.env)
        if type(plan) is not ReturnPlan or type(plan.save_ok) is not bool:
            raise AccessError('Frozen test plan required.')
        return self.env['ydental.queue.test.return.plan'].sudo().with_context(ydental_return_test_source=MUTATION).create({
            'ydental_task_id': plan.task_id, 'ydental_target_task_id': plan.target_task_id or False, 'ydental_save_ok': plan.save_ok}).id

    def _test_source_for_execution(self, execution):
        guard(self.env)
        Provider = self.env['ydental.queue.test.return.source'].sudo()
        source = Provider.search([('ydental_execution_id', '=', execution.id)], limit=1)
        if not source:
            plan = self.env['ydental.queue.test.return.plan'].sudo().search([('ydental_task_id', '=', execution.ydental_task_id.id)], limit=1)
            if plan:
                source = Provider.browse(self._test_return_source(ReturnSource(execution.id, plan.ydental_target_task_id.id, plan.ydental_save_ok)))
        return source

    def _test_return_source(self, source):
        guard(self.env)
        if type(source) is not ReturnSource or type(source.save_ok) is not bool:
            raise AccessError('Frozen test source required.')
        Provider = self.env['ydental.queue.test.return.source'].sudo().with_context(ydental_return_test_source=MUTATION)
        row = Provider.search([('ydental_execution_id', '=', source.execution_id)], limit=1)
        values = {'ydental_execution_id': source.execution_id, 'ydental_target_task_id': source.target_task_id or False,
                  'ydental_save_ok': source.save_ok, 'ydental_document_key': source.document_key}
        if row:
            row.write(values)
        else:
            row = Provider.create(values)
        return row.id

    def _external_target_authorized(self, execution, target_task):
        guard(self.env)
        source = self._test_source_for_execution(execution)
        return bool(source and source.ydental_target_task_id == target_task) or super()._external_target_authorized(execution, target_task)

    def _save_before_handover(self, execution):
        guard(self.env)
        source = self._test_source_for_execution(execution)
        if not source:
            return super()._save_before_handover(execution)
        if not source.ydental_save_ok:
            raise UserError('save_required: Synthetic latest draft save failed.')
        source.with_context(ydental_return_test_source=MUTATION).write({'ydental_saved': source.ydental_saved + 1})
        return True

    def _release_execution_documents(self, execution):
        guard(self.env)
        source = self.env['ydental.queue.test.return.source'].sudo().search([('ydental_execution_id', '=', execution.id)], limit=1)
        if source and source.ydental_document_key:
            self.env['ydental.queue.test.document'].sudo().search([
                ('ydental_key', '=', source.ydental_document_key), ('ydental_lease_id', '=', execution.ydental_lease_id.id),
                ('ydental_active', '=', True)]).write({'ydental_active': False})
        return super()._release_execution_documents(execution)
