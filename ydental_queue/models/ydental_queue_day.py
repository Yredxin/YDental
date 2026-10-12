from datetime import timedelta, timezone
from zoneinfo import ZoneInfo

from odoo import fields, models
from odoo.exceptions import UserError


class YDentalQueueCleanup(models.Model):
    _name = 'ydental.queue.cleanup'
    _description = 'Committed local business day cleanup watermark'
    _inherit = 'ydental.queue.record'

    ydental_business_date = fields.Date(required=True, index=True)
    ydental_timezone = fields.Char(required=True)
    ydental_cleanup_type = fields.Char(required=True, default='unstarted_v1')
    ydental_completed_at = fields.Datetime(required=True)
    ydental_entry_ids = fields.Many2many('ydental.queue.entry', readonly=True)
    _one_day = models.Constraint('UNIQUE(ydental_store_id, ydental_business_date, ydental_cleanup_type)',
                                 'A store business day has one final cleanup fact.')


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _local_now(self, store):
        return self._now().replace(tzinfo=timezone.utc).astimezone(ZoneInfo(store.ydental_timezone))

    def _cleanup_cutoff(self, store):
        local = self._local_now(store)
        # Before 00:10 only earlier missed runs are due. No ambiguous wall-time
        # conversion: compare a real UTC instant after projecting into the store.
        return local.date() - timedelta(days=1 if (local.hour, local.minute) >= (0, 10) else 2)

    def _queue_day_expired(self, entry):
        return entry.ydental_business_date <= self._cleanup_cutoff(entry.ydental_store_id)

    def _execution_entry(self, execution):
        while execution.ydental_resumed_from_id:
            execution = execution.ydental_resumed_from_id
        return execution.ydental_entry_id

    def _eligibility(self, entry, station, actor=None):
        if entry.state not in ('waiting', 'calling') or self._queue_day_expired(entry):
            return self.env._('day_closed: This business-day queue segment is terminal.')
        reason = super()._eligibility(entry, station, actor)
        if reason:
            return reason
        business = self.env['ydental.supply.service']._business_record(entry.ydental_store_id, entry.ydental_area_id.id)
        if not business and entry.ydental_business_date == self._local_now(entry.ydental_store_id).date():
            return self.env._('business_closed: Explicitly open the current local business day.')
        return ''

    def _cleanup_day(self, store, business_date):
        # Private, server-selected store/day only; every caller locks preceding
        # patient/supply/intake fences before the queue/day/version fence.
        with self.env.cr.savepoint():
            self._locks()
            if business_date > self._cleanup_cutoff(store):
                raise UserError(self.env._('cleanup_not_due: Wait until the store local 00:10 boundary.'))
            domain = [('ydental_store_id', '=', store.id), ('ydental_business_date', '=', business_date)]
            previous = self._model('cleanup').search(domain + [('ydental_cleanup_type', '=', 'unstarted_v1')], limit=1)
            if previous:
                return {'result': 'already_accepted', 'watermark_id': previous.id, 'ended': previous.ydental_entry_ids.ids}
            rows = self._model('entry').search(domain + [('state', 'in', ('waiting', 'calling'))])
            intake = self.env['ydental.intake.service']
            for entry in rows:
                # Do not route through qualification cancellation or ordinary void.
                positions = intake._model('position').search([('ydental_task_id', '=', entry.ydental_task_id.id),
                                                              ('ydental_active', '=', True)])
                positions._save({'ydental_active': False, 'ydental_reason': 'Local business day queue ended'})
                if entry.ydental_task_id.state == 'accepted':
                    entry.ydental_task_id._save({'state': 'pending'})
                entry._save({'state': 'day_closed', 'ydental_lease_id': False})
                self.env['ydental.access.service'].with_user(self.env.ref('base.user_root'))._audit(
                    'queue.day_closed', entry.ydental_category, entry, store.id,
                    after={'business_date': fields.Date.to_string(business_date), 'queue_id': entry.id},
                    source='local_day_cleanup_v1')
            self._model('append.permit').search(domain + [('state', '=', 'active')])._save({'state': 'expired'})
            watermark = self._model('cleanup')._new({'name': 'unstarted_v1', 'ydental_store_id': store.id,
                'ydental_category': 'capacity', 'ydental_business_date': business_date,
                'ydental_timezone': store.ydental_timezone, 'ydental_completed_at': self._now(),
                'ydental_entry_ids': [fields.Command.set(rows.ids)]})
            return {'result': 'accepted', 'watermark_id': watermark.id, 'ended': rows.ids}

    def _cleanup_due(self):
        # ir.cron calls this same fixed service; no client clock/store arguments.
        results = []
        for store in self.env['ydental.access.store'].sudo().search([]):
            cutoff = self._cleanup_cutoff(store)
            dates = {cutoff}
            dates.update(self._model('entry').search([('ydental_store_id', '=', store.id),
                ('ydental_business_date', '<=', cutoff), ('state', 'in', ('waiting', 'calling'))]).mapped('ydental_business_date'))
            dates.update(self._model('append.permit').search([('ydental_store_id', '=', store.id),
                ('ydental_business_date', '<=', cutoff), ('state', '=', 'active')]).mapped('ydental_business_date'))
            for date in sorted(dates):
                results.append(self._cleanup_day(store, date))
        return results


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _run(self, operation, payload, key, downstream=False):
        if operation != 'business' or downstream:
            return super()._run(operation, payload, key, downstream)
        # S03 owns permissions, validation, facts, idempotency and audit.
        self._access(write=True)
        with self.env.cr.savepoint():
            self.env['ydental.intake.service']._all_locks()
            return super()._run(operation, payload, key, downstream)

    def _check_queue_empty(self, business):
        # Includes all still-live days in this area, and explicit append queues.
        if self.env['ydental.queue.service']._model('entry').search_count([
                ('ydental_store_id', '=', business.ydental_store_id.id),
                ('ydental_area_id', '=', business.ydental_area_id.id), ('state', 'in', ('waiting', 'calling'))]):
            raise UserError(self.env._('queue_not_empty: Clear waiting and calling before closing ordinary calling.'))

    def _business(self, store, payload):
        before = self._business_record(store, payload.get('area_id'))
        state_before = before.state if before else 'absent'
        if state_before == 'closed' and payload.get('state') == 'draining':
            raise UserError(self.env._('business_transition_required: Explicitly reopen before stopping ordinary reporting.'))
        result = super()._business(store, payload)
        business = self._business_record(store, payload['area_id'])
        self.env['ydental.access.service']._audit('queue.business_state', 'capacity', business, store.id,
            before={'state': state_before}, after={'state': business.state, 'area_id': business.ydental_area_id.id,
                'business_date': fields.Date.to_string(business.ydental_date)}, reason=payload['reason'])
        self.env['ydental.queue.service']._publish_scope(store, self.env['ydental.space.area'].sudo().browse(payload['area_id']))
        return result
