import uuid
from urllib.parse import urlencode

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .settlement import HEADERS, YDentalSettlement


class YDentalTaxOriginal(YDentalSettlement):
    @http.route('/ydental/settlement/external-originals', type='http', auth='user', methods=['GET'])
    def external_originals(self, **kwargs):
        request.update_context(lang='zh_CN')
        try:
            service = self._service().with_context(lang='zh_CN')
            invoice_id = int(kwargs['invoice_id']) if kwargs.get('invoice_id') else None
            values = service._tax_original_workbench(term=kwargs.get('q', ''),
                bills_page=int(kwargs.get('bills_page', '1')), originals_page=int(kwargs.get('originals_page', '1')),
                invoice_id=invoice_id)
            def page_url(kind, page):
                query = {'q': values['search_term'], 'bills_page': values['invoice_pagination']['page'],
                    'originals_page': values['original_pagination']['page']}
                if invoice_id is not None:
                    query['invoice_id'] = invoice_id
                query[kind + '_page'] = page
                return '/ydental/settlement/external-originals?' + urlencode(query)
            values.update({'revision': service.env['ydental.access.service']._scope().ydental_revision,
                'page_url': page_url, 'key': str(uuid.uuid4())})
            return request.render('ydental_settlement.ydental_external_original_page', values, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError) as error:
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/settlement/external-originals/upload', type='http', auth='user',
                methods=['POST'], max_content_length=11000000)
    def upload_external_original(self, invoice_id, revision, key, material_reference, file=None,
                                 synthetic='true', previous_id=None, **kwargs):
        try:
            service = self._service(int(revision))
            if file is None or synthetic not in ('true', 'false'):
                raise ValidationError(request.env._('Supply original material and its actual classification.'))
            raw = file.read(10000001)
            with request.env.cr.savepoint():
                result = service._tax_original_upload(int(invoice_id), file.filename, raw, key,
                    material_reference, synthetic=synthetic == 'true',
                    previous_id=int(previous_id) if previous_id else None)
            if kwargs.get('output') == 'html' and request.httprequest.mimetype == 'multipart/form-data':
                response = request.redirect('/ydental/settlement/external-originals?' + urlencode({
                    'invoice_id': int(invoice_id)}), code=303)
                for name, value in HEADERS:
                    response.headers[name] = value
                return response
            return request.make_json_response(result, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError) as error:
            request.env['ydental.access.service']._denial('external_original.upload')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/settlement/external-originals/<int:original_id>', type='http', auth='user', methods=['GET'])
    def download_external_original(self, original_id, **kwargs):
        return self._external_original_response(original_id, 'download')

    @http.route('/ydental/settlement/external-originals/<int:original_id>/print-request', type='http',
                auth='user', methods=['POST'])
    def print_external_original(self, original_id, revision, **kwargs):
        return self._external_original_response(original_id, 'print_request', revision)

    def _external_original_response(self, original_id, operation, revision=None):
        try:
            service = self._service(int(revision) if revision is not None else None)
            raw, row = service._tax_original_bytes(original_id, operation)
            extension = {'application/pdf': 'pdf', 'image/png': 'png', 'image/jpeg': 'jpg'}[row.mimetype]
            return request.make_response(raw, headers=HEADERS + [('Content-Type', row.mimetype),
                ('Content-Disposition', 'attachment; filename="external-original-%s.%s"' % (row.id, extension)),
                ('X-YDental-Original-SHA256', row.sha256)])
        except (AccessError, UserError, ValueError, TypeError) as error:
            request.env['ydental.access.service']._denial('external_original.' + operation)
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)
