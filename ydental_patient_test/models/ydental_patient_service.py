import os
import re

from odoo import models
from odoo.exceptions import AccessError, UserError


class YDentalPatientService(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _synthetic_guard(self):
        if not re.fullmatch(r'ydental_s04_test_[0-9]{14}_[a-f0-9]{8}', self.env.cr.dbname) or not os.environ.get('YDENTAL_S04_RUN_DIR'):
            raise AccessError('Synthetic patient activity refused outside isolated S04 validation.')

    def _synthetic_start(self, patient_id, kind='queue', fail_migration=False):
        self._synthetic_guard()
        store = self._access(write=True)
        patient = self._business_patient(patient_id)
        if kind not in ('reservation', 'queue', 'execution'):
            raise UserError('Unknown synthetic reference kind.')
        if self._active_business(self._identity_ids(patient)):
            raise UserError('Synthetic active reference already exists for the canonical patient.')
        return self.env['ydental.patient.test.activity'].sudo()._new({
            'name': 'S04 synthetic ' + kind, 'ydental_store_id': store.id,
            'ydental_patient_id': patient.id, 'ydental_origin_patient_id': patient.id,
            'ydental_identity_snapshot': self._identity_snapshot(patient), 'ydental_kind': kind,
            'ydental_fail_migration': fail_migration})

    def _active_business(self, patient_ids):
        self._synthetic_guard()
        records = self.env['ydental.patient.test.activity'].sudo().search([
            ('ydental_patient_id', 'in', patient_ids), ('ydental_active', '=', True)])
        return super()._active_business(patient_ids) + [
            {'patient_id': r.ydental_patient_id.id, 'kind': r.ydental_kind, 'reference': r.id} for r in records]

    def _migrate_business(self, source_ids, target):
        self._synthetic_guard()
        counts = super()._migrate_business(source_ids, target)
        records = self.env['ydental.patient.test.activity'].sudo().search([
            ('ydental_patient_id', 'in', source_ids), ('ydental_active', '=', True)])
        for record in records:
            record._save({'ydental_patient_id': target.id})
            if record.ydental_fail_migration:
                raise UserError('Synthetic migration failed after a reference write.')
        return counts | {'synthetic_active_references': len(records)}
