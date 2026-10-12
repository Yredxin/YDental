from dataclasses import dataclass
import os
from pathlib import Path
import re

from odoo import models
from odoo.exceptions import AccessError


def guard(env):
    run = os.environ.get('YDENTAL_S07_RUN_DIR', '')
    if not re.fullmatch(r'ydental_s07_test_[0-9]{14}_[a-f0-9]{8}', env.cr.dbname) or Path(run).name != env.cr.dbname:
        raise AccessError('S07 synthetic adapter refused outside the isolated validation database.')


@dataclass(frozen=True)
class SyntheticSource:
    actor_id: int
    store_id: int
    source_key: str
    kind: str
    lot_id: int
    quantity: float
    uom_id: int
    price_version: str = 'S07-synthetic-price-v1'
    unit_price: float = 20
    already_performed: bool = False
    snapshot_id: int = 0


class YDentalInventoryService(models.AbstractModel):
    _inherit = 'ydental.inventory.service'

    def _authorize_source(self, source):
        guard(self.env)
        if type(source) is not SyntheticSource:
            return super()._authorize_source(source)
        access = self.env['ydental.access.service']
        if source.actor_id != self.env.uid or source.store_id != access._scope(write=True).ydental_store_id.id:
            raise AccessError('Synthetic source actor/store mismatch.')
        snapshot = {'version': source.price_version, 'currency': self.env.company.currency_id.id, 'unit_price': source.unit_price}
        if source.snapshot_id:
            original = self.env['ydental.intake.snapshot'].sudo().browse(source.snapshot_id).exists()
            if not original or original.ydental_store_id.id != source.store_id:
                raise AccessError('Synthetic original price snapshot store mismatch.')
            snapshot = {'snapshot_id': original.id, 'version': str(original.ydental_price_id.id), 'currency': original.ydental_currency_id.id, 'unit_price': original.ydental_unit_price, 'amount': original.ydental_amount}
        return {'kind': source.kind, 'namespace': 's07_synthetic_execution', 'source_key': source.source_key,
            'lot_id': source.lot_id, 'quantity': source.quantity, 'uom_id': source.uom_id,
            'reason': 'S07 explicitly synthetic actual execution source', 'summary': 'Synthetic order summary; no clinical record',
            'price_snapshot': snapshot,
            'fee_reference': 'S07-SYNTHETIC-FEE:' + source.source_key, 'synthetic': True,
            'already_performed': source.already_performed}
