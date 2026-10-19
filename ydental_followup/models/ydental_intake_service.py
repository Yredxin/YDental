from odoo import models


class YDentalIntakeFollowupBridge(models.AbstractModel):
    _inherit = 'ydental.intake.service'

    def _reschedule(self, store, record_id, version, mapping_id, start, end, reason):
        entitlement = self.env['ydental.intake.entitlement'].sudo().browse(record_id).exists()
        previous_start = entitlement.ydental_claim_id.ydental_slot_id.ydental_start if entitlement else False
        result = super()._reschedule(store, record_id, version, mapping_id, start, end, reason)
        if entitlement:
            entitlement.invalidate_recordset(['ydental_claim_id'])
            self.env['ydental.followup.service']._refresh_appointment_schedule(entitlement, previous_start)
        return result
