from dataclasses import dataclass

from odoo import fields, models


@dataclass(frozen=True)
class SyntheticCareScope:
    user_id: int
    session_id: int
    revision: int
    record_ids: tuple[int, ...]


class YDentalAccessService(models.AbstractModel):
    _inherit = 'ydental.access.service'

    def _get_sources(self):
        return super()._get_sources() | {'s01_synthetic': 'ydental.access.test.record'}

    def _get_default_store_id(self):
        return self.env.user.sudo().ydental_test_default_store_id.id or super()._get_default_store_id()

    def _synthetic_care_scope(self):
        """Fixed server fixtures only. No patient/task or client ID is accepted."""
        self._check('medical', 'read')
        session = self._scope()
        records = self.env['ydental.access.test.record'].sudo().search([
            ('ydental_test_care_target', '=', True), ('ydental_category', 'in', ['medical', 'exam']),
        ])
        return self.with_context(ydental_test_care_scope=SyntheticCareScope(
            self.env.uid, session.id, session.ydental_revision, tuple(records.ids),
        ))

    def _get_care_domain(self, model_name):
        scope = self.env.context.get('ydental_test_care_scope')
        session = self._scope()
        if model_name == 'ydental.access.test.record' and isinstance(scope, SyntheticCareScope) and (
            scope.user_id, scope.session_id, scope.revision
        ) == (self.env.uid, session.id, session.ydental_revision):
            return fields.Domain('id', 'in', scope.record_ids)
        return super()._get_care_domain(model_name)
