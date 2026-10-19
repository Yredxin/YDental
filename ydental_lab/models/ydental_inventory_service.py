from odoo import models
from odoo.exceptions import AccessError

from ..source import LabStockSource


class YDentalInventoryService(models.AbstractModel):
    _inherit = 'ydental.inventory.service'

    def _lab_workflow_move(self, source, reason):
        if type(source) is not LabStockSource:
            raise AccessError(self.env._('access_denied: A trusted laboratory stock source is required.'))
        lab = self.env['ydental.lab.service']
        order = lab._authorize_inventory_source(source)
        reason = lab._text(reason, 'Physical stock disposition')
        with self.env.cr.savepoint():
            self._lock()
            order = lab._authorize_inventory_source(source)
            config = self._config(order.ydental_store_id)
            target = config.ydental_supplier_id if source.operation == 'supplier_return' else config.ydental_loss_id
            event = self._event(order.ydental_store_id, 'ydental_lab', '%s-%s' % (source.operation, order.id),
                'transfer',
                order.ydental_lot_id, order.ydental_quantity, order.ydental_product_id.uom_id.id,
                config.ydental_prosthesis_id, target, reason, summary='laboratory-order-%s' % order.id)
            return {'id': event.id, 'move_id': event.ydental_move_id.id, 'state': event.state}
