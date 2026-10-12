from odoo import models

from .adapter import Clock, guard


def now(service, fallback):
    clock = service.env.context.get('ydental_day_test_clock')
    if type(clock) is Clock:
        guard(service.env)
        return clock.now
    return fallback()


class QueueClock(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _now(self):
        return now(self, super()._now)


class IntakeClock(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _now(self):
        return now(self, super()._now)


class SupplyClock(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _now(self):
        return now(self, super()._now)


from dataclasses import dataclass
from odoo import api, fields
from odoo.exceptions import AccessError


CLOCK_MUTATION = object()


@dataclass(frozen=True)
class DaySource:
    store_id: int
    instant: object


class SyntheticDayClock(models.Model):
    _name = 'ydental.queue.test.day.clock'
    _description = 'Guarded store clock fixture, never a production time source'

    ydental_store_id = fields.Many2one('ydental.access.store', required=True, ondelete='restrict')
    ydental_now = fields.Datetime(required=True)
    _one_store = models.Constraint('UNIQUE(ydental_store_id)', 'One synthetic clock per store.')

    @api.model_create_multi
    def create(self, vals_list):
        guard(self.env)
        if self.env.context.get('ydental_day_clock_mutation') is not CLOCK_MUTATION:
            raise AccessError('Frozen server clock source required.')
        return super().create(vals_list)

    def write(self, vals):
        guard(self.env)
        if self.env.context.get('ydental_day_clock_mutation') is not CLOCK_MUTATION:
            raise AccessError('Frozen server clock source required.')
        return super().write(vals)


def stored_now(service, fallback):
    clock = service.env.context.get('ydental_day_test_clock')
    if type(clock) is Clock:
        guard(service.env)
        return clock.now
    binding = service.env.context.get('ydental_binding')
    from odoo.addons.ydental_access.models.ydental_access_service import Binding
    if type(binding) is Binding:
        store = service.env['ydental.access.session'].sudo().browse(binding.session_id).ydental_store_id
        fact = service.env['ydental.queue.test.day.clock'].sudo().search([('ydental_store_id', '=', store.id)], limit=1)
        if fact:
            guard(service.env)
            return fact.ydental_now
    return fallback()


class QueueStoredClock(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _now(self):
        return stored_now(self, super()._now)

    def _test_day_clock(self, source):
        guard(self.env)
        if type(source) is not DaySource:
            raise AccessError('Frozen server clock source required.')
        model = self.env['ydental.queue.test.day.clock'].sudo().with_context(ydental_day_clock_mutation=CLOCK_MUTATION)
        row = model.search([('ydental_store_id', '=', source.store_id)], limit=1)
        if row:
            row.write({'ydental_now': source.instant})
        else:
            row = model.create({'ydental_store_id': source.store_id, 'ydental_now': source.instant})
        return row.id

    def _local_now(self, store):
        fact = self.env['ydental.queue.test.day.clock'].sudo().search([('ydental_store_id', '=', store.id)], limit=1)
        if fact and type(self.env.context.get('ydental_day_test_clock')) is not Clock:
            guard(self.env)
            return self.with_context(ydental_day_test_clock=Clock(fact.ydental_now))._local_now(store)
        return super()._local_now(store)

    def _area_snapshot(self, store, area):
        fact = self.env['ydental.queue.test.day.clock'].sudo().search([('ydental_store_id', '=', store.id)], limit=1)
        if fact:
            guard(self.env)
            return super(QueueStoredClock, self.with_context(ydental_day_test_clock=Clock(fact.ydental_now)))._area_snapshot(store, area)
        return super()._area_snapshot(store, area)


class IntakeStoredClock(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _now(self):
        return stored_now(self, super()._now)


class SupplyStoredClock(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _now(self):
        return stored_now(self, super()._now)
