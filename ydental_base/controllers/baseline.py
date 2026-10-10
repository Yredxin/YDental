from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class YDentalBaseline(http.Controller):

    @http.route('/ydental', type='http', auth='user', methods=['GET'], readonly=True)
    def baseline(self, **kwargs):
        if not request.env.user._is_internal() or not request.env.user.has_group(
            'ydental_base.ydental_base_group_user'
        ):
            raise AccessError(request.env._('YDental application access is required.'))
        response = request.render('ydental_base.baseline_page')
        response.headers['Cache-Control'] = 'no-store'
        return response
