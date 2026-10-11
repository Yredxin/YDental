from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import request

from odoo.addons.ydental_access.controllers.access import YDentalAccess


class YDentalSyntheticSource(YDentalAccess):

    @http.route('/ydental/s01-synthetic', type='http', auth='user', methods=['GET'])
    def synthetic(self, purpose=None, **kwargs):
        service = self._service().with_context(ydental_purpose='care' if purpose == 'care' else False)
        records = service.env['ydental.access.test.record'].search_fetch([], ['name', 'ydental_text'])
        response = request.render('ydental_access_test.ydental_synthetic_page', {
            'records': records, 'revision': service._scope().ydental_revision,
        })
        response.headers['Cache-Control'] = 'no-store'
        return response

    @http.route('/ydental/s01-synthetic/write', type='http', auth='user', methods=['POST'])
    def synthetic_write(self, revision, record_id, name, **kwargs):
        try:
            service = self._service(int(revision))
            with request.env.cr.savepoint():
                service.env['ydental.access.test.record'].browse(int(record_id)).write({'name': name})
        except (AccessError, UserError) as error:
            return request.make_json_response({'error': str(error)}, status=409 if isinstance(error, UserError) else 403)
        return request.redirect('/ydental/s01-synthetic')
