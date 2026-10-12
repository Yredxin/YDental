from odoo import models
from odoo.exceptions import AccessError

from .ydental_intake_service import CapacityPermit, fingerprint


class YDentalSupplyService(models.AbstractModel):
    _inherit = 'ydental.supply.service'

    def _check_capacity_source(self, operation, payload):
        permit = self.env.context.get('ydental_intake_capacity')
        if not isinstance(permit, CapacityPermit):
            return super()._check_capacity_source(operation, payload)
        if (permit.actor_id, permit.operation, permit.fingerprint) != (self.env.uid, operation, fingerprint(payload)):
            raise AccessError(self.env._('access_denied: Capacity permit does not match the validated source.'))
        store = self.env['ydental.access.store'].sudo().browse(permit.store_id).exists()
        if not store or not store.active:
            raise AccessError(self.env._('access_denied: Capacity target is unavailable.'))
        return store


class YDentalPatientService(models.AbstractModel):
    _inherit = 'ydental.patient.service'

    def _intake_merge_lock(self):
        # Called only under S04 patient fence. Never invert this order.
        self.env['ydental.supply.service']._lock()
        self.env['ydental.intake.service']._lock()

    def _active_business(self, patient_ids):
        self._intake_merge_lock()
        result = super()._active_business(patient_ids)
        domains = {
            'entitlement': [('state', 'in', ['held', 'started'])],
            'task': [('state', 'in', ['pending', 'accepted', 'started'])],
            'position': [('ydental_active', '=', True)],
            'referral': [('state', '=', 'pending')],
        }
        for entity, domain in domains.items():
            records = self.env['ydental.intake.' + entity].sudo().search([('ydental_patient_id', 'in', patient_ids)] + domain)
            result += [{'patient_id': r.ydental_patient_id.id,
                'kind': 'execution' if entity == 'task' and r.state == 'started' else 'intake_' + entity,
                'reference': r.id} for r in records]
        return result

    def _migrate_business(self, source_ids, target):
        self._intake_merge_lock()
        counts = super()._migrate_business(source_ids, target)
        # Origin identities, actual actors, mappings, claims, dates and snapshots
        # remain unchanged. Historical rows keep their original canonical link.
        domains = {
            'entitlement': [('state', 'in', ['held', 'started'])],
            'task': [('state', 'in', ['pending', 'accepted', 'started'])],
            'position': [('ydental_active', '=', True)],
            'referral': [('state', '=', 'pending')],
        }
        for entity, domain in domains.items():
            records = self.env['ydental.intake.' + entity].sudo().search([('ydental_patient_id', 'in', source_ids)] + domain)
            records._save({'ydental_patient_id': target.id})
            counts['intake_' + entity] = len(records)
        # Arrival facts remain historical; a canonical lookup includes all old
        # identities rather than collapsing facts or overwriting local dates.
        return counts
