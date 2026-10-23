"""Authenticated native cancellation and follow-up UI boundaries (HTTP sources)."""

import json
import re

from lxml import etree

from odoo.tests import HttpCase, tagged

from odoo.addons.ydental_treatment_test.tests.common import key

from .test_lab_cancellation import TestLabCancellation


@tagged('post_install', '-at_install')
class TestLabCancellationHTTP(TestLabCancellation, HttpCase):
    allow_inherited_tests_method = False

    def _select(self, role):
        self.authenticate(self.users[role].login, 's05-test-password')
        page = self.url_open('/ydental/access')
        self.assertEqual(page.status_code, 200)
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text)
        self.assertTrue(csrf)
        self.assertTrue(revision)
        self.csrf = csrf.group(1)
        selected = self.url_open('/ydental/access/action', data={
            'csrf_token': self.csrf, 'revision': revision.group(1), 'operation': 'switch',
            'payload': json.dumps({'store_id': self.stores[0].id}), 'output': 'json',
        })
        self.assertEqual(selected.status_code, 200, selected.text)
        self.revision = selected.json()['revision']

    def _rpc(self, model, method, args):
        response = self.url_open('/web/dataset/call_kw/' + model + '/' + method,
            data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'call', 'params': {
                'model': model, 'method': method, 'args': args,
                'kwargs': {'context': {'ydental_revision': self.revision}},
            }}), headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _followup_action(self, operation, args):
        return self.url_open('/ydental/followups/action', data={
            'csrf_token': self.csrf, 'revision': self.revision,
            'operation': operation, 'payload': json.dumps(args),
        })

    def test_http_real_reservation_pending_native_cancel_and_assigned_task_feedback(self):
        order = self._new_order()
        self._policy()
        reservation = self._reservation(order)
        row = order.ydental_followup_id
        self._send_receive(order)
        self._select('manager')
        linked = self._followup_action('link_appointment', {
            'followup_id': row.id, 'appointment_id': reservation['id'],
        })
        self.assertEqual(linked.status_code, 200, linked.text)
        self.env.invalidate_all()
        pending = self._jobs(order).filtered(lambda job: job.ydental_state == 'pending').ensure_one()
        self.assertEqual(pending.ydental_event_type, 'appointment_reminder')
        self._select('frontdesk')
        self.assertIn('result', self._rpc('ydental.lab.order', 'write', [[order.id], {
            'ydental_exception_reason': 'Received synthetic package retained for explicit review',
        }]))
        cancelled = self._rpc('ydental.lab.order', 'action_cancel', [[order.id]])
        self.assertIn('result', cancelled, cancelled)
        self.env.invalidate_all()
        self.assertEqual((order.state, row.ydental_lab_contact_stage, pending.ydental_state),
                         ('cancelled', 'stopped', 'cancelled'))
        self.assertTrue(order.ydental_receipt_at)
        self.assertFalse(order.ydental_inventory_event_id)
        tasks = self._rpc('mail.activity', 'search_read', [[
            ['res_model', '=', 'ydental.lab.order'], ['res_id', '=', order.id],
            ['user_id', '=', self.users['frontdesk'].id], ['active', '=', True],
        ], ['id', 'summary', 'note']])
        self.assertIn('result', tasks, tasks)
        self.assertEqual(len(tasks['result']), 1)
        task = tasks['result'][0]
        self.assertNotIn('42.75', task['note'])
        self.assertNotIn('137.25', task['note'])
        feedback = self._rpc('mail.activity', 'action_feedback', [[task['id']], 'Synthetic package location recorded; no financial reversal'])
        self.assertIn('result', feedback, feedback)
        self._select('manager')
        page = self.url_open('/ydental/followups')
        self.assertEqual(page.status_code, 200, page.text)
        document = etree.HTML(page.text)
        summaries = document.xpath('//tr[@id="followup-%s"]//summary/text()' % row.id)
        self.assertNotIn('Reopen with reason', summaries)
        self.assertNotIn('Record contact', summaries)
        self.assertNotIn('Complete from actual treatment', summaries)
        denied = self._followup_action('reopen', {'followup_id': row.id, 'reason': 'Cannot revive cancelled cycle'})
        self.assertEqual(denied.status_code, 409, denied.text)

    def test_http_order_direct_messaging_cannot_bypass_internal_activity_boundary(self):
        order = self._new_order()
        self._select('manager')
        before_mail = self.root['mail.mail'].search_count([])
        before_sms = self.root['sms.sms'].search_count([])
        external = order.ydental_vendor_id.partner_id
        for method, args in (
            ('message_post', [order.ids]),
            ('message_notify', [order.ids]),
            ('message_mail_with_source', [order.ids, 'mail.mail_notification_layout']),
        ):
            with self.subTest(method=method):
                denied = self._rpc('ydental.lab.order', method, args)
                self.assertIn('error', denied)
        response = self.url_open('/web/dataset/call_kw/ydental.lab.order/message_post',
            data=json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'call', 'params': {
                'model': 'ydental.lab.order', 'method': 'message_post', 'args': [order.ids],
                'kwargs': {'body': 'Client context cannot enable external sends', 'partner_ids': external.ids,
                    'context': {'ydental_revision': self.revision, 'ydental_lab_order_activity_done': True}},
            }}), headers={'Content-Type': 'application/json'})
        self.assertIn('error', response.json())
        self.env.invalidate_all()
        self.assertEqual(self.root['mail.mail'].search_count([]), before_mail)
        self.assertEqual(self.root['sms.sms'].search_count([]), before_sms)

    def test_http_no_warehouse_authority_and_client_stage_forgery_are_denied(self):
        order = self._new_order()
        row = order.ydental_followup_id
        self._select('doctor')
        forged = self._rpc('ydental.followup', 'write', [[row.id], {'ydental_lab_contact_stage': 'ready'}])
        self.assertIn('error', forged)
        self.assertIn('error', self._rpc('ydental.lab.order', 'action_cancel', [[order.id]]))
        self.env.invalidate_all()
        self.assertEqual((order.state, row.ydental_lab_contact_stage), ('draft', 'waiting'))
        self._select('manager')
        denied = self._followup_action('contact', {
            'followup_id': row.id, 'method': 'phone', 'outcome': 'delivered', 'request_key': key(),
        })
        self.assertEqual(denied.status_code, 409, denied.text)
        self.assertFalse(self._jobs(order))
