import hmac
import uuid
from datetime import datetime, timezone
from urllib.parse import urlencode

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


HEADERS = [('Cache-Control', 'no-store, private, max-age=0'),
           ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer')]


class YDentalSettlement(http.Controller):
    def _html_feedback(self, kind):
        token = uuid.uuid4().hex
        request.session['ydental_settlement_feedback'] = {'token': token, 'kind': kind}
        response = request.redirect('/ydental/settlement?' + urlencode({'notice': token}), code=303)
        for name, value in HEADERS:
            response.headers[name] = value
        return response

    def _service(self, revision=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        access = access._bind(session, revision)
        return access.env['ydental.settlement.service']

    @http.route('/ydental/settlement', type='http', auth='user', methods=['GET'])
    def workbench(self, patient_id=None, notice=None, today_page='1', history_page='1',
                  pending_page='1', invoices_page='1', payments_page='1',
                  refunds_page='1', closes_page='1', settled_page='1', **kwargs):
        raw_pages = {'today': today_page, 'history': history_page,
                     'pending': pending_page, 'invoices': invoices_page,
                     'payments': payments_page, 'refunds': refunds_page,
                     'closes': closes_page, 'settled': settled_page}
        if (not isinstance(settled_page, str) or not 1 <= len(settled_page) <= 5
                or not settled_page.isdecimal()
                or patient_id and (not patient_id.isdecimal() or not 1 <= len(patient_id) <= 12)
                or any(not isinstance(value, str) or not value.isdecimal()
                       or not 1 <= int(value) <= 10000 for value in raw_pages.values())):
            return request.make_json_response({'error': 'Invalid workbench page or patient.'},
                                              status=400, headers=HEADERS)
        pages = {name: int(value) for name, value in raw_pages.items()}
        service = self._service()
        number = int(patient_id) if patient_id else None
        context = service._workbench(number, pages)
        feedback = request.session.get('ydental_settlement_feedback')
        message = None
        if (isinstance(feedback, dict) and isinstance(notice, str)
                and isinstance(feedback.get('token'), str)
                and hmac.compare_digest(feedback['token'], notice)):
            request.session.pop('ydental_settlement_feedback', None)
            message = {
                'accepted': '操作已受理，请核对下方业务记录。',
                'already_accepted': '此请求此前已处理，请核对现有记录。',
                'denied': '请求未完成，请核对权限、门店或输入后重试。',
            }.get(feedback.get('kind'))
        def page_url(category, page):
            selected = dict(pages)
            selected[category] = page
            query = {name + '_page': number for name, number in selected.items() if number != 1}
            if patient_id:
                query['patient_id'] = patient_id
            return '/ydental/settlement' + ('?' + urlencode(query) if query else '')
        access = service.env['ydental.access.service']
        member = access._membership(service.env.uid, context['store'].id)
        context.update({'revision': access._scope().ydental_revision,
                        'can_write': access._levels(member)['settlement'] == 'write',
                        'can_export': access._levels(member)['export'] == 'write',
                        'can_approve': access._levels(member)['finance_approval'] == 'write',
                        'can_trade': (access._levels(member)['settlement'] == 'write' and
                                      access._levels(member)['finance_approval'] == 'write' and
                                      access._levels(member)['warehouse'] == 'write'),
                        'new_key': lambda: uuid.uuid4().hex,
                        'page_url': page_url,
                        'now_utc': lambda: datetime.now(timezone.utc).isoformat(),
                        'feedback': message})
        return request.render('ydental_settlement.ydental_settlement_page', context, headers=HEADERS)

    @http.route('/ydental/settlement/action', type='http', auth='user', methods=['POST'], max_content_length=100000)
    def action(self, operation, revision, key, **post):
        html_form = (post.get('output') == 'html'
                     and request.httprequest.mimetype == 'application/x-www-form-urlencoded')
        def ids(name):
            values = request.httprequest.form.getlist(name)
            return [int(value) for value in values]

        try:
            service = self._service(int(revision))
            payloads = {
                'bill': lambda: {'fee_ids': ids('fee_ids'), 'discount': float(post.get('discount') or 0),
                                 'reason': post.get('reason') or ''},
                'pay': lambda: {'invoice_ids': ids('invoice_ids'), 'amount': float(post['amount']),
                                'channel': post['channel'], 'actual_utc': post['actual_utc'], 'proof': post['proof']},
                'refund_request': lambda: {'payment_id': int(post['payment_id']), 'amount': float(post['amount']),
                                           'reason': post['reason'], 'request_key': key},
                'refund_approve': lambda: {'refund_id': int(post['refund_id']), 'reason': post['reason']},
                'refund_reject': lambda: {'refund_id': int(post['refund_id']), 'reason': post['reason']},
                'refund_execute': lambda: {'refund_id': int(post['refund_id']),
                                           'actual_utc': post['actual_utc'], 'proof': post['proof']},
                'refund_uncertain': lambda: {'refund_id': int(post['refund_id']), 'outcome': post['outcome'],
                                             'reason': post['reason']},
                'refund_recover': lambda: {'refund_id': int(post['refund_id']),
                                           'verified_not_paid': post.get('verified_not_paid') == '1',
                                           'reason': post['reason']},
                'refund_cancel': lambda: {'refund_id': int(post['refund_id']),
                                          'verified_not_paid': post.get('verified_not_paid') == '1',
                                          'evidence': post['evidence'], 'reason': post['reason']},
                'close': lambda: {'business_date': post['business_date'], 'channel': post['channel']},
                'unlock': lambda: {'close_id': int(post['close_id']), 'reason': post['reason']},
                'reclassify': lambda: {'payment_id': int(post['payment_id']),
                                       'new_channel': post['new_channel'], 'reason': post['reason']},
                'waive': lambda: {'invoice_id': int(post['invoice_id']),
                                  'amount': float(post['amount']), 'reason': post['reason']},
                'trade': lambda: {'target_store_id': int(post['target_store_id']),
                                  'source_lot_id': int(post['source_lot_id']),
                                  'target_lot_id': int(post['target_lot_id']),
                                  'quantity': float(post['quantity']), 'uom_id': int(post['uom_id']),
                                  'unit_price': float(post['unit_price']),
                                  'source_key': post['source_key'], 'reason': post['reason']},
            }
            if operation not in payloads:
                raise ValidationError(request.env._('Unknown settlement operation.'))
            result = service._operate(operation, payloads[operation](), key)
            if html_form:
                return self._html_feedback('already_accepted' if result.get('result') == 'already_accepted'
                                           else 'accepted')
            return request.make_json_response(result, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('settlement.action')
            if html_form:
                return self._html_feedback('denied')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/settlement/pdf/<string:kind>/<int:source_id>', type='http', auth='user', methods=['GET'])
    def pdf(self, kind, source_id, **kwargs):
        try:
            raw, digest = self._service().with_context(lang='zh_CN')._pdf(kind, source_id)
            return request.make_response(raw, headers=HEADERS + [('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="ydental-settlement-demo.pdf"'),
                ('X-YDental-PDF-SHA256', digest)])
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('settlement.report')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/settlement/other-stores/<int:patient_id>', type='http', auth='user', methods=['GET'])
    def other_stores(self, patient_id, **kwargs):
        try:
            return request.make_json_response(self._service()._other_store_summary(patient_id), headers=HEADERS)
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('settlement.other_store_summary')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)
