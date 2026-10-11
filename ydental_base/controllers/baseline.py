from werkzeug.exceptions import NotFound

from odoo import http
from odoo.exceptions import AccessError
from odoo.http import request


class YDentalBaseline(http.Controller):

    def _check_access(self):
        if not request.env.user._is_internal() or not request.env.user.has_group(
            'ydental_base.ydental_base_group_user'
        ):
            raise AccessError(request.env._('YDental application access is required.'))

    @http.route('/ydental', type='http', auth='user', methods=['GET'], readonly=True)
    def baseline(self, **kwargs):
        self._check_access()
        response = request.render('ydental_base.baseline_page', {
            'title': request.env._('Dental | YDental'),
        })
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route('/ydental/sample/<paper>', type='http', auth='user', methods=['GET'], readonly=True)
    def sample(self, paper, **kwargs):
        self._check_access()
        if paper not in ('a4', 'narrow'):
            raise NotFound()
        pdf, _output_type = request.env['ir.actions.report'].with_context(
            force_report_rendering=True,
        )._render_qweb_pdf('ydental_base.ydental_sample_report_' + paper)
        return request.make_response(pdf, headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', 'attachment; filename="ydental-synthetic-%s.pdf"' % paper),
            ('Cache-Control', 'no-store'),
        ])
