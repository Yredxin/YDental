from dataclasses import dataclass

from odoo import fields, models
from odoo.exceptions import AccessError, ValidationError


@dataclass(frozen=True)
class PatientCareScope:
    user_id: int
    session_id: int
    revision: int
    store_id: int
    patient_id: int
    purpose: str


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {
            'patient': 'ydental.patient', 'patient_number': 'ydental.patient.number',
            'patient_relation': 'ydental.patient.relation', 'patient_contact': 'ydental.patient.contact',
            'patient_clinical': 'ydental.patient.clinical', 'patient_policy': 'ydental.patient.policy',
            'patient_merge': 'ydental.patient.merge', 'patient_operation': 'ydental.patient.operation',
        }

    def _get_patient_care_sources(self):
        """Upper modules append fixed clinical models and patient field paths."""
        return {'ydental.patient.clinical': 'ydental_patient_id'}

    def _patient_care(self, patient_id, purpose):
        self.env['ydental.patient.service']._access()
        if purpose not in ('diagnosis', 'history_review'):
            raise ValidationError(self.env._('Select an explicit clinical purpose.'))
        session = self._scope()
        member = self._membership(self.env.uid, session.ydental_store_id.id)
        levels = self._levels(member)
        if not any(levels[category] in ('read', 'write') for category in ('medical', 'exam')):
            raise AccessError(self.env._('access_denied: Current-store medical or examination read permission is required.'))
        patient = self.env['ydental.patient.service']._patient(patient_id)
        self.env['ydental.patient.service']._current_relation(patient, session.ydental_store_id)
        scope = PatientCareScope(self.env.uid, session.id, session.ydental_revision,
                                 session.ydental_store_id.id, patient.id, purpose)
        self._audit('patient.care.open', 'medical', patient, session.ydental_store_id.id,
                    source='patient_care', reason=purpose, after={'patient_id': patient.id})
        return self.with_context(ydental_patient_care=scope)

    def _get_care_domain(self, model_name):
        scope = self.env.context.get('ydental_patient_care')
        mapping = self._get_patient_care_sources()
        if model_name not in mapping or not isinstance(scope, PatientCareScope):
            return super()._get_care_domain(model_name)
        session = self._scope()
        if (scope.user_id, scope.session_id, scope.revision, scope.store_id) != (
            self.env.uid, session.id, session.ydental_revision, session.ydental_store_id.id,
        ):
            return fields.Domain.FALSE
        # Revalidate identity and grants on every request/read, including cached
        # environments after revocation or an identity merge.
        self.env['ydental.patient.service']._access()
        member = self._membership(self.env.uid, session.ydental_store_id.id)
        if not any(self._levels(member)[category] in ('read', 'write') for category in ('medical', 'exam')):
            return fields.Domain.FALSE
        patient = self.env['ydental.patient.service']._patient(scope.patient_id)
        if patient.id != scope.patient_id:
            return fields.Domain.FALSE
        if not self.env['ydental.patient.service']._current_relation(patient, session.ydental_store_id, required=False):
            return fields.Domain.FALSE
        return fields.Domain(mapping[model_name], '=', patient.id)
