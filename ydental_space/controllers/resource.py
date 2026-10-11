from odoo import http
from odoo.http import request


class YDentalSpaceResource(http.Controller):

    @http.route('/ydental/space/resource/<int:resource_id>.svg', type='http', auth='user', methods=['GET'])
    def artwork(self, resource_id):
        resource = request.env['ydental.space.resource'].browse(resource_id)
        resource.check_access('read')
        return request.make_response(resource.ydental_svg, headers=[
            ('Content-Type', 'image/svg+xml; charset=utf-8'), ('Cache-Control', 'no-store'),
            ('Content-Security-Policy', "default-src 'none'; sandbox"), ('X-Content-Type-Options', 'nosniff'),
        ])
