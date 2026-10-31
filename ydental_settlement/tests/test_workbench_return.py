from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse
import json
import re

from lxml import html
from odoo.exceptions import AccessError, UserError
from odoo.tests import HttpCase, TransactionCase, new_test_user, tagged

from odoo.addons.ydental_settlement.controllers.settlement import YDentalSettlement


@tagged('post_install', '-at_install', 's13_settlement_return')
class TestSettlementReturn(TransactionCase):
    def setUp(self):
        super().setUp()
        self.controller = YDentalSettlement()
        self.service = MagicMock()
        self.service.env.cr.savepoint.return_value = nullcontext()
        self.service._access.return_value = SimpleNamespace(id=4)
        self.service._patient.return_value = SimpleNamespace(id=37)

    def test_return_hint_requires_current_relation_and_accepts_only_decimal(self):
        relation = self.service.env.__getitem__.return_value._current_relation
        self.assertEqual(self.controller._return_patient(self.service, '37'), 37)
        relation.assert_called_once_with(self.service._patient.return_value, self.service._access.return_value)
        for value in (None, '', '-1', '0', '1x', '2147483648', '999999999999', '1' * 13, 37):
            self.assertIsNone(self.controller._return_patient(self.service, value))
        relation.side_effect = AccessError('not in this store')
        self.assertIsNone(self.controller._return_patient(self.service, '37'))
        self.service._access.side_effect = UserError('revoked')
        self.assertIsNone(self.controller._return_patient(self.service, '37'))

    def _action(self, post, operation_result=None, feedback_error=None):
        fake_request = MagicMock()
        fake_request.httprequest.mimetype = 'application/x-www-form-urlencoded'
        fake_request.httprequest.form.getlist.return_value = ['5']
        fake_request.make_json_response.return_value = 'json-response'
        self.service._operate.side_effect = operation_result if isinstance(operation_result, Exception) else None
        self.service._operate.return_value = operation_result or {'result': 'accepted'}
        with patch('odoo.addons.ydental_settlement.controllers.settlement.request', fake_request), \
                patch.object(self.controller, '_service', return_value=self.service), \
                patch.object(self.controller, '_return_patient', return_value=37) as hint, \
                patch.object(self.controller, '_html_feedback', return_value='redirect', side_effect=feedback_error) as feedback, \
                patch('odoo.addons.ydental_settlement.controllers.settlement.record_exception'):
            result = self.controller.action.__wrapped__.__wrapped__(self.controller, 'bill', '2', 'test-key', **post)
            return result, hint.call_count, feedback.call_args, fake_request

    def test_html_keeps_context_on_success_and_business_denial(self):
        result, calls, feedback, _request = self._action({'output': 'html', 'return_patient_id': '37'})
        self.assertEqual((result, calls, feedback.args), ('redirect', 1, ('accepted', 37)))
        result, calls, feedback, _request = self._action({'output': 'html', 'return_patient_id': '37'}, AccessError('denied'))
        self.assertEqual((result, calls, feedback.args), ('redirect', 1, ('denied', 37)))

    def test_json_ignores_return_hint(self):
        result, calls, feedback, request = self._action({'return_patient_id': '37'})
        self.assertEqual((result, calls, feedback), ('json-response', 0, None))
        self.assertEqual(request.make_json_response.call_args.args[0], {'result': 'accepted'})

    def test_response_failure_does_not_become_business_denial(self):
        with self.assertRaisesRegex(UserError, 'redirect failed'):
            self._action({'output': 'html', 'return_patient_id': '37'}, feedback_error=UserError('redirect failed'))
        self.service._operate.assert_called_once()


@tagged('post_install', '-at_install', 's13_settlement_return_http')
class TestSettlementReturnHTTP(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        root = cls.env['base'].sudo().env
        cls.stores = root['ydental.access.store'].create([
            {'name': 'Return test A', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
            {'name': 'Return test B', 'company_id': root.company.id, 'ydental_timezone': 'UTC'},
        ])
        cls.actor = new_test_user(root, login='s13_settlement_return_http', password='s13-return-test',
            groups='ydental_base.ydental_base_group_user,ydental_access.ydental_group_manager')
        access = root['ydental.access.service'].with_user(cls.actor)
        admin = access._bind(access._session_for_key('s13-return-admin'))
        cls.patient_ids = []
        for index, store in enumerate(cls.stores):
            admin._join(cls.actor.id, store.id)
            admin._grant(cls.actor.id, store.id, {'frontdesk': 'write', 'settlement': 'write', 'finance_approval': 'write'})
            session = access._session_for_key('s13-return-patient-%s' % index)
            scoped = access._bind(session)
            scoped._switch(store.id)
            scoped = access._bind(session)
            cls.patient_ids.append(scoped.env['ydental.patient.service']._operate(
                'create', {'values': {'name': 'Synthetic return context'}}, 's13-return-create-%s' % index)['id'])

    def test_html_context_checks_real_store_relation_and_json_is_compatible(self):
        self.authenticate(self.actor.login, 's13-return-test')
        page = self.url_open('/ydental/access')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text).group(1)
        switch = self.url_open('/ydental/access/action', data={'csrf_token': token, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        revision = switch.json()['revision']
        base = {'csrf_token': token, 'revision': revision, 'operation': 'bill', 'key': 's13-return-http',
                'fee_ids': '99999999'}
        for patient, should_return in ((self.patient_ids[0], True), (self.patient_ids[1], False),
                                       ('bad', False), ('2147483648', False), ('999999999999', False)):
            response = self.url_open('/ydental/settlement/action', data=dict(base, output='html',
                return_patient_id=patient), allow_redirects=False)
            self.assertEqual(response.status_code, 303)
            query = parse_qs(urlparse(response.headers['Location']).query)
            self.assertEqual(query.get('patient_id'), [str(patient)] if should_return else None)
        response = self.url_open('/ydental/settlement/action', data=dict(base, return_patient_id=self.patient_ids[0]),
                                 allow_redirects=False)
        self.assertIn(response.status_code, (403, 409))
        self.assertIn('error', response.json())
        self.assertNotIn('Location', response.headers)
        response = self.url_open('/ydental/settlement/action', data=dict(base, output='html',
            return_patient_id=self.patient_ids[0], discount='invalid'), allow_redirects=False)
        self.assertEqual(response.status_code, 303)
        self.assertEqual(parse_qs(urlparse(response.headers['Location']).query).get('patient_id'),
                         [str(self.patient_ids[0])])
        response = self.url_open('/ydental/settlement/action', data=dict(base,
            return_patient_id=self.patient_ids[0], discount='invalid'), allow_redirects=False)
        self.assertEqual(response.status_code, 409)
        self.assertIn('error', response.json())
        service_type = type(self.env['ydental.settlement.service'])
        with patch.object(service_type, '_operate', return_value={'result': 'accepted'}) as operate:
            response = self.url_open('/ydental/settlement/action', data=dict(base, output='html',
                return_patient_id='2147483648'), allow_redirects=False)
            self.assertEqual(response.status_code, 303)
            self.assertNotIn('patient_id', parse_qs(urlparse(response.headers['Location']).query))
            self.assertEqual(operate.call_count, 1)
            response = self.url_open('/ydental/settlement/action', data=dict(base,
                return_patient_id='999999999999'), allow_redirects=False)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'result': 'accepted'})
            self.assertEqual(operate.call_count, 2)

    def test_bill_original_post_return_hint_and_download_contract(self):
        self.authenticate(self.actor.login, 's13-return-test')
        page = self.url_open('/ydental/access')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text).group(1)
        switch = self.url_open('/ydental/access/action', data={'csrf_token': token, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        base = {'csrf_token': token, 'revision': switch.json()['revision'], 'key': 's13-original-test'}
        service_type = type(self.env['ydental.settlement.service'])
        with patch.object(service_type, '_store_bill_original', return_value={}) as store_original:
            for patient, expected in ((self.patient_ids[0], [str(self.patient_ids[0])]),
                                      (self.patient_ids[1], None), ('2147483648', None), (None, None)):
                data = dict(base)
                if patient is not None:
                    data['return_patient_id'] = patient
                response = self.url_open('/ydental/settlement/bill-original/create/1', data=data,
                                         allow_redirects=False)
                self.assertEqual(response.status_code, 303)
                self.assertEqual(parse_qs(urlparse(response.headers['Location']).query).get('patient_id'), expected)
            self.assertEqual(store_original.call_count, 4)
            response = self.url_open('/ydental/settlement/bill-original/create/1', data=dict(base,
                previous_id='invalid', return_patient_id=self.patient_ids[0]), allow_redirects=False)
            self.assertEqual(response.status_code, 409)
            self.assertIn('error', response.json())
            self.assertEqual(store_original.call_count, 4)
        with patch.object(service_type, '_bill_original_bytes', return_value=(b'%PDF-test', 'test-digest')):
            response = self.url_open('/ydental/settlement/bill-original/1?return_patient_id=2147483648')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b'%PDF-test')
            self.assertEqual(response.headers['Content-Type'], 'application/pdf')
        with patch.object(service_type, '_bill_original_bytes', side_effect=AccessError('denied')):
            response = self.url_open('/ydental/settlement/bill-original/1?return_patient_id=1')
            self.assertEqual(response.status_code, 403)
            self.assertIn('error', response.json())

    def test_refund_template_hides_self_approval_and_carries_patient(self):
        self.authenticate(self.actor.login, 's13-return-test')
        page = self.url_open('/ydental/access')
        token = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text).group(1)
        switch = self.url_open('/ydental/access/action', data={'csrf_token': token, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json'})
        self.assertEqual(switch.status_code, 200)
        service_type = type(self.env['ydental.settlement.service'])
        original = service_type._workbench
        def with_refunds(service, *args, **kwargs):
            result = original(service, *args, **kwargs)
            result['refunds'] = [SimpleNamespace(id=number, create_date='2026-10-31', ydental_reason='synthetic',
                ydental_payment_id=SimpleNamespace(ydental_payment_id=SimpleNamespace(name='synthetic')),
                ydental_amount=1, ydental_currency_id=service.env.company.currency_id,
                ydental_state='requested', ydental_requester_id=SimpleNamespace(id=requester))
                for number, requester in ((701, self.actor.id), (702, self.actor.id + 10000))]
            return result
        with patch.object(service_type, '_workbench', with_refunds):
            response = self.url_open('/ydental/settlement?patient_id=%s' % self.patient_ids[0])
        self.assertEqual(response.status_code, 200, response.text)
        document = html.fromstring(response.content)
        self.assertFalse(document.xpath('//*[@id="refund-701"]//button[@value="refund_approve"]'))
        self.assertTrue(document.xpath('//*[@id="refund-702"]//button[@value="refund_approve"]'))
        self.assertEqual(document.xpath('//*[@id="refund-702"]//input[@name="return_patient_id"]/@value'),
                         [str(self.patient_ids[0]), str(self.patient_ids[0])])
