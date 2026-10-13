from odoo import models

from odoo.addons.ydental_treatment.models.ydental_treatment_service import InventorySource


EXAM_INVENTORY_GUARD = object()


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _check(self, category, level='read', store_id=None, write=False):
        guarded = self.env.context.get('ydental_exam_inventory_source')
        if (category, level, write) == ('medical', 'write', True) and type(guarded) is tuple and (
                len(guarded) == 2 and guarded[0] is EXAM_INVENTORY_GUARD and
                type(guarded[1]) is InventorySource):
            source = guarded[1]
            row = self.env['ydental.treatment.consumption'].sudo().browse(source.consumption_id).exists()
            event = row.ydental_event_id if row else False
            if event and event.ydental_kind == 'exam' and event.ydental_already_performed and (
                    event.ydental_actor_id.id == self.env.uid == source.actor_id and
                    event.ydental_store_id.id == source.store_id and
                    (store_id is None or store_id == source.store_id)):
                return super()._check('exam', level, source.store_id, write)
        return super()._check(category, level, store_id, write)
