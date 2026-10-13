from odoo import models

from odoo.addons.ydental_treatment.models.ydental_treatment_service import InventorySource

from .ydental_access_service import EXAM_INVENTORY_GUARD


class YDentalInventoryService(models.AbstractModel):
    _inherit = 'ydental.inventory.service'

    def _source_action(self, source):
        if type(source) is InventorySource:
            row = self.env['ydental.treatment.consumption'].sudo().browse(source.consumption_id).exists()
            event = row.ydental_event_id if row else False
            if event and event.ydental_kind == 'exam':
                # S08 verifies the immutable event, actor, store, lot and price.
                # The private guard only maps S07's medical check to exam-write
                # while this one trusted native material action is executing.
                self._authorize_source(source)
                return super(YDentalInventoryService, self.with_context(
                    ydental_exam_inventory_source=(EXAM_INVENTORY_GUARD, source)))._source_action(source)
        return super()._source_action(source)
