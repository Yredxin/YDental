from odoo import models


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {'queue_' + entity: 'ydental.queue.' + entity for entity in ('lease', 'entry', 'execution')}

    def _get_execution_store_id(self):
        queue = self.env['ydental.queue.service']
        execution = queue._actor_execution()
        if execution:
            return execution.ydental_store_id.id
        lease = queue._own()
        return lease.ydental_store_id.id if lease else super()._get_execution_store_id()

    def _grant(self, user_id, store_id, levels, source='manual'):
        # Same anchor as queue mutations closes RR grant-vs-action snapshots.
        # Do not acquire a new user/session lock after the patient fence.
        self._scope(write=True)
        self._lock_user(user_id)
        self.env['ydental.intake.service']._all_locks()
        return super()._grant(user_id, store_id, levels, source)
