from odoo import models
from odoo.tools import consteq
from odoo.exceptions import AccessError

from .ydental_treatment_service import InventorySource


class YDentalInventoryService(models.AbstractModel):
    _inherit = 'ydental.inventory.service'

    def _source_action(self, source):
        if type(source) is InventorySource:
            self._authorize_source(source)
            return super(YDentalInventoryService, self.with_context(
                _ydental_actual_inventory_source=source))._source_action(source)
        return super()._source_action(source)

    def _event(self, store, namespace, source_key, *args, **kwargs):
        source = self.env.context.get('_ydental_actual_inventory_source')
        if type(source) is InventorySource:
            payload = self._authorize_source(source)
            if (namespace, source_key) != (payload['namespace'], payload['source_key']):
                raise AccessError(self.env._('source_required: Inventory must retain the original clinical source.'))
            row = self.env['ydental.treatment.service']._model('consumption').browse(source.consumption_id)
            kwargs['actual_at'] = row.ydental_event_id.ydental_actual_at
        return super()._event(store, namespace, source_key, *args, **kwargs)

    def _authorize_source(self, source):
        if type(source) is not InventorySource:
            return super()._authorize_source(source)
        service = self.env['ydental.treatment.service']
        row = service._model('consumption').browse(source.consumption_id).exists()
        event = row.ydental_event_id
        category = 'pharmacy' if row.ydental_kind == 'prescription' else 'medical'
        store = service._access(category)
        if not row or (source.actor_id, source.store_id) != (self.env.uid, store.id) or (
                event.ydental_store_id != store or event.ydental_actor_id.id != self.env.uid or
                event.ydental_category != category or not event.ydental_source or
                not event.ydental_execution_id or not event.ydental_reason):
            raise AccessError(self.env._('source_required: Only the immutable actual clinical source can derive inventory.'))
        price = service._price_values(event)
        if not price:
            raise AccessError(self.env._('missing_price: Verify the original historical price before inventory bookkeeping.'))
        if not event.ydental_already_performed:
            execution = event.ydental_execution_id
            lease = execution.ydental_lease_id
            session, connection = self.env['ydental.queue.service']._connection()
            if execution.state != 'serving' or lease.ydental_actor_id.id != self.env.uid or not lease.ydental_active or (
                    lease.ydental_session_id != session or lease.ydental_revision != session.ydental_revision or
                    not consteq(lease.ydental_connection_hash, connection.key_hash) or lease.ydental_expires_at <= self._now()):
                raise AccessError(self.env._('execution_required: Current actual execution and holding connection are required.'))
        return {'kind': row.ydental_kind, 'lot_id': row.ydental_lot_id.id,
            'quantity': row.ydental_quantity, 'uom_id': row.ydental_uom_id.id,
            'namespace': 's08b-clinical', 'source_key': 'consumption-' + str(row.id),
            'reason': event.ydental_reason, 'summary': 'clinical-event-' + str(event.id),
            'price_snapshot': price, 'synthetic': False, 'fee_reference': 'clinical-event-' + str(event.id),
            'already_performed': event.ydental_already_performed}
