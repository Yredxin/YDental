import base64
import json
import os
import re
from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import HttpCase, tagged
from odoo.addons.ydental_treatment_test.tests.common import key, make_slot, price, handover_args, queue_bind, lease_args
from odoo.addons.ydental_treatment_test.tests.treatment_common import setup, opened_actual


@tagged('post_install', '-at_install')
class TestExamResultView(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        setup(cls)
        cls.users['second'] = cls.second
        cls.admin._join(cls.second.id, cls.stores[1].id)
        cls.admin._grant(cls.second.id, cls.stores[1].id, {'medical': 'write', 'exam': 'write'})
        cls.env.cr.execute("SELECT current_database(), (SELECT oid FROM pg_database WHERE datname=current_database()), (pg_control_system()).system_identifier::text")
        db, oid, cluster = cls.env.cr.fetchone()
        target = json.dumps({'database': db, 'oid': oid, 'cluster': cluster, 'store_id': cls.stores[0].id})
        cls.scope = patch.dict(os.environ, {'YDENTAL_E2E_ISOLATED_SUPPLY': '1', 'YDENTAL_E2E_ISOLATED_TARGET': target})
        cls.scope.start()
        cls.addClassCleanup(cls.scope.stop)
        supply = cls.group.env['ydental.supply.service']
        supply._operate('policy', {'name': 'Synthetic exact-target policy', 'mode': 'isolated_test',
            'station_id': cls.stations[0][0].id, 'rounding': 'floor', 'phone_pool': 'reservation',
            'cutoff_minutes': 0, 'reason': 'Isolated examination integration fixture',
            'isolated_test_approved': True}, key())
        cls.start = cls.end + timedelta(minutes=10)
        cls.end = cls.start + timedelta(hours=1)
        make_slot(cls, cls.group, cls.stations[0][0], cls.start, cls.end)
        cls.admin._grant(cls.users['manager'].id, cls.stores[0].id, {'exam': 'write'})
        exam = cls.group.env['ydental.exam.service']
        catalog = cls.catalogs[2]
        exam._operate('review_capability', {'capability_id': catalog.ydental_capability_id.id,
            'family': 'panorama', 'reason': 'Synthetic examination capability'}, key())
        exam._operate('bind_template', {'catalog_id': catalog.id, 'code': 'panorama-demo-1',
            'reason': 'Synthetic examination template'}, key())
        price(cls, 80, catalog=catalog)

    def _select(self, role, store=None):
        self.authenticate(self.users[role].login, 's05-test-password')
        page = self.url_open('/ydental/access')
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        revision = re.search(r'name="revision" value="([0-9]+)"', page.text).group(1)
        response = self.url_open('/ydental/access/action', data={'csrf_token': csrf, 'revision': revision,
            'operation': 'switch', 'payload': json.dumps({'store_id': (store or self.stores[0]).id}), 'output': 'json'})
        self.assertEqual(response.status_code, 200, response.text)

    def _line(self):
        treatment, clinical, queue, lease, execution, document, args = opened_actual(self)
        line = {'mapping_id': self.mappings[0][2].id, 'quantity': 1, 'uom_id': self.uom.id,
            'product_id': False, 'specification': '', 'usage': '', 'frequency': '', 'course': ''}
        order = treatment._operate('order', args | {'kind': 'exam', 'purpose': 'Synthetic result view', 'lines': [line]}, key())
        issued = treatment._operate('issue', args | {'order_id': order['order_id'], 'version': order['version']}, key())
        return issued['line_ids'][0], treatment, clinical, queue, lease, execution, document

    def test_html_result_and_json_contract_are_authorized(self):
        line_id, *_ = self._line()
        self._select('doctor')
        html = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(html.status_code, 200, html.text)
        self.assertIn('检查结果与办理状态', html.text)
        self.assertIn('尚无结果草稿', html.text)
        self.assertNotIn('result_id', html.text)
        raw = self.url_open('/ydental/exam/result/%s' % line_id)
        self.assertEqual(raw.status_code, 200)
        self.assertEqual(raw.json()['line_id'], line_id)
        self.assertEqual(raw.json()['version'], 0)
        self._select('none')
        self.assertEqual(self.url_open('/ydental/exam/result-view/%s' % line_id).status_code, 403)
        self._select('doctor', self.stores[1])
        self.assertEqual(self.url_open('/ydental/exam/result-view/%s' % line_id).status_code, 403)

    def test_revocation_removes_detail_access(self):
        line_id, *_ = self._line()
        self._select('doctor')
        self.assertEqual(self.url_open('/ydental/exam/result-view/%s' % line_id).status_code, 200)
        self.admin._grant(self.users['doctor'].id, self.stores[0].id, {'medical': 'none', 'exam': 'none'})
        self.assertEqual(self.url_open('/ydental/exam/result-view/%s' % line_id).status_code, 403)
        self.assertEqual(self.url_open('/ydental/exam/result/%s' % line_id).status_code, 403)

    def test_receipt_check_is_same_actor_store_source_and_payload(self):
        line_id, _line, service, args = self._start_exam()
        args = args | {'version': 0, 'findings': 'Synthetic receipt', 'measurements': {}, 'conclusion': ''}
        receipt_key = key()
        service._operate('draft', args, receipt_key)
        self._select('second')
        page = self.url_open('/ydental/access')
        csrf = re.search(r'name="csrf_token" value="([^"]+)"', page.text).group(1)
        data = {'operation': 'draft', 'payload': json.dumps(args), 'key': receipt_key, 'csrf_token': csrf}
        def check(changes=None):
            return self.url_open('/ydental/exam/check-submission', data=dict(data, **(changes or {})))
        response = check()
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {'status': 'committed'})
        self.assertEqual(check({'key': key()}).json(), {'status': 'unknown'})
        self.assertEqual(check({'payload': json.dumps(dict(args, findings='changed'))}).json(), {'status': 'unknown'})
        self.assertEqual(check({'operation': 'finish'}).json(), {'status': 'unknown'})
        self.assertEqual(check({'payload': json.dumps(dict(args, line_id=2147483647))}).status_code, 403)
        self.assertEqual(check({'payload': json.dumps(dict(args, line_id=2147483648))}).status_code, 403)
        self.assertEqual(check({'csrf_token': 'invalid'}).status_code, 400)
        self._select('doctor')
        csrf2 = re.search(r'name="csrf_token" value="([^"]+)"', self.url_open('/ydental/access').text).group(1)
        self.assertEqual(check({'csrf_token': csrf2}).json(), {'status': 'unknown'})
        self._select('second', self.stores[1])
        csrf3 = re.search(r'name="csrf_token" value="([^"]+)"', self.url_open('/ydental/access').text).group(1)
        self.assertEqual(check({'csrf_token': csrf3}).status_code, 403)
        self._select('second')
        csrf4 = re.search(r'name="csrf_token" value="([^"]+)"', self.url_open('/ydental/access').text).group(1)
        self.admin._grant(self.users['second'].id, self.stores[0].id, {'medical': 'none', 'exam': 'none'})
        self.assertEqual(check({'csrf_token': csrf4}).status_code, 403)

    def _start_exam(self):
        line_id, _treatment, clinical, _queue, lease, _execution, document = self._line()
        clinical._operate('handover', handover_args(document, lease))
        line = self.root['ydental.treatment.line'].browse(line_id)
        task = line.ydental_task_id
        self.front._operate('report', {'task_id': task.id, 'version': task.ydental_version}, key())
        queue = queue_bind(self, self.second)
        exam_lease = queue._operate('enter', {'station_id': self.stations[0][2].id})
        called = queue._operate('call', lease_args(exam_lease))
        self.assertEqual(called['task_id'], task.id)
        execution = queue._operate('start', lease_args(exam_lease) | {'entry_id': called['entry_id']})
        service = queue.env['ydental.exam.service']
        args = {'line_id': line_id, 'execution_id': execution['execution_id'],
                'lease_id': exam_lease['lease_id'], 'lease_token': exam_lease['token'], 'inline': False}
        return line_id, line, service, args

    def test_partial_result_retains_actual_fact_and_escapes_text(self):
        line_id, line, service, args = self._start_exam()
        draft = service._operate('draft', args | {'version': 0, 'findings': '<script>synthetic</script>',
            'measurements': {}, 'conclusion': ''}, key())
        self._select('doctor')
        before_attachment = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(before_attachment.status_code, 200)
        self.assertIn('当前结果没有附件', before_attachment.text)
        service._operate('attach', {'line_id': line_id, 'version': draft['version'],
            'filename': '<synthetic>.pdf', 'mimetype': 'application/pdf',
            'encoded': base64.b64encode(b'%PDF-synthetic').decode()}, key())
        self.root['ir.attachment'].create({'name': 'unrelated-private.pdf', 'raw': b'%PDF-private',
            'res_model': 'res.partner', 'res_id': self.env.company.partner_id.id, 'public': False})
        actual = service._operate('perform', args | {'reason': 'Synthetic actual examination', 'materials': []}, key())
        partial = service._operate('abort', args | {'reason': 'Synthetic partial result'}, key())
        self.assertEqual(partial['state'], 'partial')
        self.assertEqual(line.state, 'partial')
        self.assertEqual(self.root['ydental.treatment.fee'].search_count([('ydental_event_id', '=', actual['event_id'])]), 1)
        self._select('doctor')
        page = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(page.status_code, 200, page.text)
        self.assertIn('&lt;script&gt;synthetic&lt;/script&gt;', page.text)
        self.assertNotIn('<script>synthetic</script>', page.text)
        self.assertIn('实际检查已记录', page.text)
        self.assertIn('&lt;synthetic&gt;.pdf', page.text)
        self.assertNotIn('unrelated-private.pdf', page.text)
        self.assertIn('同名同大小附件可能无法区分', page.text)
        self.assertIn('不能单凭序号确认本次提交', page.text)
        self.assertIn('结果变更序号', page.text)
        self.assertIn('检查接诊状态', page.text)
        self.assertIn('>进行中<', page.text)
        raw = self.url_open('/ydental/exam/result/%s' % line_id).json()
        self.assertEqual((raw['result_state'], raw['version']), ('partial', draft['version']))
        self.assertEqual(raw['findings'], '<script>synthetic</script>')
        with self.assertRaisesRegex(UserError, 'version_conflict'), self.cr.savepoint():
            service._operate('draft', args | {'version': 0, 'findings': 'stale overwrite',
                'measurements': {}, 'conclusion': ''}, key())
        self.assertEqual(service._operate('finish', args | {'reason': 'Synthetic finish'}, key())['state'], 'completed')
        page = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(page.status_code, 200)
        self.assertIn('>已完成<', page.text)
        self.assertIn('&lt;synthetic&gt;.pdf', page.text)

    def test_confirm_and_correction_show_the_changed_result_number(self):
        line_id, _line, service, args = self._start_exam()
        draft = service._operate('draft', args | {'version': 0, 'findings': 'Synthetic original',
            'measurements': {}, 'conclusion': ''}, key())
        service._operate('perform', args | {'reason': 'Synthetic actual examination', 'materials': []}, key())
        confirmed = service._operate('confirm', {'line_id': line_id, 'version': draft['version'],
            'reason': 'Synthetic review'}, key())
        self._select('doctor')
        before = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertIn('结果变更序号：<strong>%s</strong>' % confirmed['version'], before.text)
        corrected = service._operate('correct', {'line_id': line_id, 'version': confirmed['version'],
            'findings': 'Synthetic corrected', 'measurements': {}, 'conclusion': '',
            'reason': 'Synthetic correction'}, key())
        after = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertIn('结果变更序号：<strong>%s</strong>' % corrected['version'], after.text)
        self.assertIn('Synthetic corrected', after.text)

    def test_inline_finish_does_not_claim_the_medical_segment_ended(self):
        station = self.stations[0][0]
        station.write({'ydental_version': station.ydental_version,
            'ydental_add_capability_ids': [fields.Command.link(self.capabilities[2].id)]})
        line_id, _treatment, _clinical, queue, lease, execution, _document = self._line()
        service = queue.env['ydental.exam.service']
        args = {'line_id': line_id, 'execution_id': execution.id, 'lease_id': lease['lease_id'],
                'lease_token': lease['token'], 'inline': True}
        service._operate('draft', args | {'version': 0, 'findings': 'Inline synthetic result',
            'measurements': {}, 'conclusion': ''}, key())
        service._operate('perform', args | {'reason': 'Inline synthetic examination', 'materials': []}, key())
        self._select('doctor')
        before = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(before.status_code, 200)
        self.assertIn('原医疗接诊状态', before.text)
        self.assertIn('同工位检查结束不会改变该状态', before.text)
        self.assertIn('不能据此确认本次结束是否提交', before.text)
        self.assertEqual(service._operate('finish', args | {'reason': 'Inline synthetic finish'}, key())['state'],
                         'medical_continues')
        after = self.url_open('/ydental/exam/result-view/%s' % line_id)
        self.assertEqual(after.status_code, 200)
        self.assertIn('原医疗接诊状态', after.text)
        self.assertIn('不能据此确认本次结束是否提交', after.text)
