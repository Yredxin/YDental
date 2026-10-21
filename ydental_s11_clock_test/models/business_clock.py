from datetime import datetime, timezone

from odoo import fields, models

from .clock import Clock, app_now, guard


class QueueClock(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _now(self):
        return app_now(self, super()._now)


class IntakeClock(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _now(self):
        return app_now(self, super()._now)


class SupplyClock(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _now(self):
        return app_now(self, super()._now)


class PatientClock(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _now(self):
        return app_now(self, super()._now)


class InventoryClock(models.AbstractModel):
    _inherit = 'ydental.inventory.service'

    def _now(self):
        return app_now(self, super()._now)


class TreatmentClock(models.AbstractModel):
    _inherit = 'ydental.treatment.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class ExamClock(models.AbstractModel):
    _inherit = 'ydental.exam.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class LabClock(models.AbstractModel):
    _inherit = 'ydental.lab.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class LabChargeClock(models.AbstractModel):
    _inherit = 'ydental.lab.charge.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class SettlementClock(models.AbstractModel):
    _inherit = 'ydental.settlement.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class FollowupClock(models.AbstractModel):
    _inherit = 'ydental.followup.service'

    def _now(self):
        return app_now(self, lambda: fields.Datetime.now())


class AccessAuditClock(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _audit(self, event, category, target, store_id=False, before=None, after=None,
               result='accepted', reason=False, source='interactive'):
        clock = self.env.context.get('ydental_s11_clock')
        if type(clock) is Clock:
            guard(self.env)
            after = dict(after or {})
            after['_s11_synthetic_business_time'] = {
                'run_id': clock.run_id,
                'simulated_utc': clock.now.isoformat().replace('+00:00', 'Z'),
                'physical_audit_utc': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            }
            source = 's11_synthetic_clock:' + source
        return super()._audit(event, category, target, store_id, before, after, result, reason, source)
