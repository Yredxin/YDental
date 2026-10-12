from odoo import models


class YDentalPatientService(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _intake_merge_lock(self):
        super()._intake_merge_lock()
        self.env['ydental.queue.service']._lock()

    def _active_business(self, patient_ids):
        result = super()._active_business(patient_ids)
        rows = self.env['ydental.queue.execution'].sudo().search([('ydental_patient_id', 'in', patient_ids), ('state', 'in', ('serving', 'verify'))])
        holds = self.env['ydental.queue.hold'].sudo().search([('ydental_patient_id', 'in', patient_ids), ('state', 'in', ('active', 'verify'))])
        return result + [{'patient_id': r.ydental_patient_id.id, 'kind': 'execution', 'reference': r.id} for r in rows] + [
            {'patient_id': r.ydental_patient_id.id, 'kind': 'hold', 'reference': r.id} for r in holds]

    def _migrate_business(self, source_ids, target):
        result = super()._migrate_business(source_ids, target)
        rows = self.env['ydental.queue.entry'].sudo().search([
            ('ydental_patient_id', 'in', source_ids), ('state', 'in', ['waiting', 'calling'])])
        rows._save({'ydental_patient_id': target.id})
        permits = self.env['ydental.queue.append.permit'].sudo().search([
            ('ydental_patient_id', 'in', source_ids), ('state', '=', 'active')])
        permits._save({'ydental_patient_id': target.id})
        return result | {'queue': len(rows)}

    def _merge_conflicts(self, source, target):
        result = super()._merge_conflicts(source, target)
        # A waiting hold is not actual execution. It nevertheless must be
        # resolved before merging its canonical identity and original chair.
        holds = self.env['ydental.queue.hold'].sudo().search([
            ('ydental_patient_id', 'in', self._identity_ids(source) + self._identity_ids(target)),
            ('state', 'in', ('active', 'verify'))])
        return result + [{'patient_id': r.ydental_patient_id.id, 'kind': 'hold', 'reference': r.id} for r in holds]
