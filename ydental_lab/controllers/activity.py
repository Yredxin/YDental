from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.ydental_inventory.controllers.inventory import YDentalInventoryDataSet


class YDentalLabDataSet(YDentalInventoryDataSet):
    """Retain the real workspace when native activity RPC replaces context."""

    _activity_read_methods = {
        'read', 'search', 'search_read', 'search_fetch', 'search_count', 'fields_get',
        'get_views', 'web_read', 'web_search_read', 'name_search', 'read_group',
        'formatted_read_group', 'formatted_read_grouping_sets', 'get_activity_data',
    }

    def _activity_kwargs(self, method, kwargs, *, button=False):
        context = dict(kwargs.get('context') or {})
        context.pop('ydental_binding', None)
        kwargs = dict(kwargs, context=context)
        if request.env.user.has_group('ydental_base.ydental_base_group_user'):
            access = request.env['ydental.access.service']
            session = access._existing_session_for_key(request.session.sid[:42])
            if session:
                if (button or method not in self._activity_read_methods) and type(context.get('ydental_revision')) is not int:
                    raise AccessError(request.env._('access_denied: A page revision is required for activity actions.'))
                # Existing helper derives user/session from SID and validates any
                # supplied revision. Native activity ACLs and source domains run
                # afterward without sudo or additional grants.
                kwargs = self._bind_kwargs(kwargs)
        return kwargs

    @http.route()
    def call_kw(self, model, method, args, kwargs, path=None):
        if model == 'mail.activity':
            kwargs = self._activity_kwargs(method, kwargs)
        return super().call_kw(model, method, args, kwargs, path=path)

    @http.route()
    def call_button(self, model, method, args, kwargs, path=None):
        if model == 'mail.activity':
            kwargs = self._activity_kwargs(method, kwargs, button=True)
        return super().call_button(model, method, args, kwargs, path=path)
