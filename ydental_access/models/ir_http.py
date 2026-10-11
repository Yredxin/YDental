from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user.has_group('ydental_base.ydental_base_group_user'):
            service = self.env['ydental.access.service']
            session = service._session_for_key(request.session.sid[:42])
            # Snapshot for this page only; never change the user's global company
            # or the shared server session context to select an operating store.
            result['user_context'] = dict(result['user_context'], ydental_revision=session.ydental_revision)
            result['ydental_store_name'] = session.ydental_store_id.name or ''
            result['ydental_execution_store_id'] = service._get_execution_store_id()
        return result

    @classmethod
    def _pre_dispatch(cls, rule, args):
        super()._pre_dispatch(rule, args)
        if request.env.uid and request.env.user.has_group('ydental_base.ydental_base_group_user'):
            service = request.env['ydental.access.service']
            # The stable SID prefix remains constant during normal cookie rotation.
            session = service._existing_session_for_key(request.session.sid[:42])
            if session:
                request.update_context(ydental_binding=service._bind(session).env.context['ydental_binding'])
