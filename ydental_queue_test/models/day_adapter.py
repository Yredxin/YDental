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
