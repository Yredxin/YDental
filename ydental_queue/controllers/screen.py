from odoo import http
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


class YDentalQueueScreen(http.Controller):
    @http.route('/ydental/queue/screen', type='http', auth='public', methods=['GET'])
    def screen(self, lang=None):
        # Credential is held in the URL fragment/sessionStorage, never query,
        # server page HTML, access logs or a third-party Referer.
        if lang in ('en_US', 'zh_CN'):
            request.update_context(lang=lang)
        return request.render('ydental_queue.ydental_queue_screen', {}, headers=[
            ('Cache-Control', 'no-store'), ('Referrer-Policy', 'no-referrer')])

    @http.route('/ydental/queue/screen/data', type='http', auth='public', methods=['GET'])
    def data(self, last_id=None):
        try:
            authorization = request.httprequest.headers.get('Authorization', '')
            token = authorization[7:] if authorization.startswith('Bearer ') else ''
            queue = request.env['ydental.queue.service']
            result = queue._screen_snapshot(token) if last_id is None else queue._screen_events(token, int(last_id))
            return request.make_json_response(result, headers=[('Cache-Control', 'no-store')])
        except (AccessError, ValidationError, ValueError):
            return request.make_json_response({'error': request.env._('Screen access denied.')}, status=403,
                                              headers=[('Cache-Control', 'no-store')])
