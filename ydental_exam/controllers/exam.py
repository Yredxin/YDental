import json

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from odoo.addons.ydental_exam.models.ydental_exam_service import TEMPLATES, fingerprint


HEADERS = [('Cache-Control', 'no-store, private, max-age=0'),
           ('X-Content-Type-Options', 'nosniff'), ('Referrer-Policy', 'no-referrer')]
PENDING_LABELS = {
    'missing_price': '缺少有效价格，请联系价目人员核对。',
    'inventory_pending': '库存待核对，请联系仓库处理。',
    'material_evidence_missing': '耗材依据待核对，请由原操作人员补充。',
}
EXECUTION_LABELS = {
    'serving': '进行中', 'completed': '已完成', 'verify': '待现场核实',
    'interrupted': '已中断', 'reserved': '已保留并转外部服务', 'handover': '已交还',
}


class YDentalExam(http.Controller):
    def _service(self, revision=None, connection=None):
        access = request.env['ydental.access.service']
        session = access._session_for_key(request.session.sid[:42])
        access = access._bind(session, revision)
        if connection:
            access = access.env['ydental.queue.service']._bind_connection(connection)
        return access.env['ydental.exam.service']

    @http.route('/ydental/exam/check-submission', type='http', auth='user', methods=['POST'], max_content_length=7500000)
    def check_submission(self, operation, payload, key):
        try:
            if operation not in ('draft', 'perform', 'confirm', 'correct', 'abort', 'finish',
                                  'reconcile', 'verify_materials', 'attach'):
                raise ValidationError(request.env._('Invalid examination action.'))
            args = json.loads(payload)
            if not isinstance(args, dict) or not isinstance(key, str) or not 1 <= len(key) <= 120:
                raise ValidationError(request.env._('Invalid examination action.'))
            line_id = args.get('line_id')
            if type(line_id) is not int or not 0 < line_id <= 2147483647:
                raise ValidationError(request.env._('Invalid examination source.'))
            service = self._service()
            service._view(line_id)
            line = service._line(line_id)
            receipt = service._model('receipt').search([
                ('ydental_actor_id', '=', request.env.uid), ('ydental_store_id', '=', line.ydental_store_id.id),
                ('name', '=', operation), ('ydental_key', '=', key)], limit=1)
            committed = bool(receipt and receipt.ydental_fingerprint == fingerprint([operation, args]))
            return request.make_json_response({'status': 'committed' if committed else 'unknown'}, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError):
            request.env['ydental.access.service']._denial('exam.view')
            return request.make_json_response({'status': 'unavailable'}, status=403, headers=HEADERS)

    @http.route('/ydental/exam', type='http', auth='user', methods=['GET'])
    def workbench(self, **kwargs):
        service = self._service()
        store = service._store()
        queue = service.env['ydental.queue.service']
        execution = queue._actor_execution()
        if execution and execution.ydental_store_id != store:
            execution = False
        area_id = int(kwargs.get('area_id') or 0) if str(kwargs.get('area_id') or '').isdigit() else 0
        care_areas = service.env['ydental.space.area'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_purpose', '=', 'care'), ('active', '=', True)])
        if area_id and area_id not in care_areas.ids:
            raise AccessError(request.env._('access_denied: Select a current medical area in this store.'))
        continuation_tasks = service.env['ydental.intake.task'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_source_kind', '=', 'continuation'),
            ('state', 'in', ('pending', 'accepted', 'started')),
            ('ydental_mapping_id.ydental_area_id', '=', area_id)], order='id desc', limit=100) if area_id else service.env['ydental.intake.task']
        candidates = service.env['ydental.treatment.line'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_order_id.ydental_kind', '=', 'exam'),
            ('ydental_order_id.state', '=', 'issued')], order='id desc', limit=100)
        if execution and execution.state == 'serving' and execution.ydental_category == 'medical':
            candidates |= service.env['ydental.treatment.line'].sudo().search([
                ('ydental_store_id', '=', store.id), ('ydental_order_id.ydental_kind', '=', 'exam'),
                ('ydental_patient_id', '=', execution.ydental_patient_id.id)])
        if continuation_tasks:
            candidates |= service.env['ydental.treatment.line'].sudo().search([
                ('ydental_store_id', '=', store.id), ('ydental_order_id.ydental_kind', '=', 'exam'),
                ('ydental_patient_id', 'in', continuation_tasks.ydental_patient_id.ids)])
        lines = service.env['ydental.treatment.line'].sudo()
        for candidate in candidates:
            try:
                service._line(candidate.id)
            except (AccessError, UserError):
                continue
            lines |= candidate
        results = service._model('result').search([('ydental_line_id', 'in', lines.ids)])
        events = service.env['ydental.treatment.event'].sudo().browse(results.ydental_event_id.ids)
        for result in results:
            service._audit('view', result, {'version': result.ydental_version})
        access = service.env['ydental.access.service']
        member = access._membership(service.env.uid, store.id)
        levels = access._levels(member)
        can_grant_qualification = access._get_execution_store_id() in (False, store.id) and (
            access._is_group_manager() or member.ydental_is_manager or levels['personnel'] == 'write')
        qualification_members = access.env['ydental.access.membership']
        if can_grant_qualification:
            qualification_members = qualification_members.sudo().search([
                ('ydental_store_id', '=', store.id), ('active', '=', True),
                ('ydental_user_id.active', '=', True), ('ydental_user_id', '!=', service.env.uid),
                ('ydental_employee_id.active', '=', True)], order='id')
        medical_document = service.env['ydental.clinical.document'].sudo().search([
            ('ydental_current_execution_id', '=', execution.id)], limit=1) if (
                execution and execution.ydental_category == 'medical' and execution.state == 'serving') else False
        mappings = service.env['ydental.intake.mapping'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_catalog_id.ydental_kind', '=', 'exam')])
        bound_catalogs = service._model('template').search([
            ('ydental_store_id', '=', store.id)]).ydental_catalog_id.ids
        catalog_fields = {}
        for line in lines:
            template = service._model('template').search([
                ('ydental_store_id', '=', store.id),
                ('ydental_catalog_id', '=', line.ydental_mapping_id.ydental_catalog_id.id)], limit=1)
            catalog_fields[line.id] = TEMPLATES.get(template.ydental_code, {}).get('measurements', {})
        attachments = service.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'ydental.exam.result'), ('res_id', 'in', results.ids), ('public', '=', False)])
        material_lots = service.env['stock.lot'].sudo().search([
            ('ydental_store_id', '=', store.id), ('product_id.ydental_inventory_kind', '=', 'material'),
            ('product_id.active', '=', True)], order='name, id', limit=100)
        capability_options = service.env['ydental.access.capability'].sudo().search([
            ('id', 'in', mappings.ydental_catalog_id.ydental_capability_id.ids),
            ('ydental_exam_family', '=', False), ('active', '=', True)])
        current_lines = lines.filtered(lambda line: execution and execution.state == 'serving' and
            execution.ydental_category == 'medical' and line.ydental_patient_id == execution.ydental_patient_id)
        handoff_rows = []
        def source_task(task):
            seen = set()
            while task and task.ydental_source_kind == 'continuation' and task.ydental_parent_task_id:
                if task.id in seen:
                    raise UserError(request.env._('source_required: Continuation task ancestry is invalid.'))
                seen.add(task.id)
                task = task.ydental_parent_task_id
            return task.id if task else 0
        for task in continuation_tasks:
            related = lines.filtered(lambda line: line.ydental_patient_id == task.ydental_patient_id and
                source_task(line.ydental_task_id.ydental_parent_task_id) == source_task(task))
            if related:
                handoff_rows.append((task, related))
        return request.render('ydental_exam.ydental_exam_page', {
            'store': store, 'revision': access._scope().ydental_revision,
            'execution': execution if execution and execution.state == 'serving' else False,
            'lines': lines, 'results': results, 'events': events,
            'can_write': levels['exam'] == 'write',
            'can_medical_write': levels['medical'] == 'write',
            'can_grant_qualification': can_grant_qualification,
            'qualification_members': qualification_members,
            'actor_id': service.env.uid,
            'medical_document': medical_document,
            'business_date': service.env['ydental.supply.service']._date(store),
            'unbound_mappings': mappings.filtered(lambda mapping: mapping.ydental_catalog_id.id not in bound_catalogs),
            'line_labels': dict(lines._fields['state']._description_selection(service.env)),
            'result_labels': dict(results._fields['state']._description_selection(service.env)),
            'catalog_fields': catalog_fields, 'attachments': attachments, 'material_lots': material_lots,
            'capability_options': capability_options,
            'can_review_capability': levels['exam'] == 'write' and
                levels['medical'] == 'write' and
                request.env.user.has_group('ydental_access.ydental_group_manager'),
            'current_lines': current_lines, 'care_areas': care_areas,
            'selected_area_id': area_id, 'handoff_rows': handoff_rows,
            'pending_labels': PENDING_LABELS,
        }, headers=HEADERS)

    @http.route('/ydental/exam/action', type='http', auth='user', methods=['POST'], max_content_length=7500000)
    def action(self, operation, revision, connection, payload, key):
        try:
            service = self._service(int(revision), connection)
            args = json.loads(payload)
            response = service._operate(operation, args, key)
            return request.make_json_response(response, headers=HEADERS)
        except (AccessError, UserError, ValidationError, ValueError, TypeError, KeyError) as error:
            request.env['ydental.access.service']._denial('exam.action')
            return request.make_json_response({'error': str(error)},
                status=403 if isinstance(error, AccessError) else 409, headers=HEADERS)

    @http.route('/ydental/exam/result/<int:line_id>', type='http', auth='user', methods=['GET'])
    def result(self, line_id, **kwargs):
        try:
            return request.make_json_response(self._service()._view(line_id), headers=HEADERS)
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.view')
            return request.make_json_response({'error': str(error)}, status=403, headers=HEADERS)

    @http.route('/ydental/exam/result-view/<int:line_id>', type='http', auth='user', methods=['GET'])
    def result_view(self, line_id, **kwargs):
        try:
            service = self._service().with_context(lang='zh_CN')
            snapshot = service._view(line_id)
            line = service._line(line_id)
            result = service._result(line)
            event = result.ydental_event_id if result else False
            execution = result.ydental_execution_id if result else False
            if execution and (execution.ydental_store_id != line.ydental_store_id or
                              execution.ydental_patient_id != line.ydental_patient_id):
                raise AccessError(request.env._('access_denied: The examination execution is unavailable.'))
            attachments = service.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'ydental.exam.result'), ('res_id', '=', result.id), ('public', '=', False)],
                order='id') if result else service.env['ir.attachment']
            return request.render('ydental_exam.ydental_exam_result_view', {
                'patient': line.ydental_patient_id, 'line': line, 'result': result,
                'snapshot': snapshot, 'event': event, 'execution': execution, 'attachments': attachments,
                'line_labels': dict(line._fields['state']._description_selection(service.env)),
                'result_labels': dict(service._model('result')._fields['state']._description_selection(service.env)),
                'execution_labels': EXECUTION_LABELS,
                'pending_labels': PENDING_LABELS,
            }, headers=HEADERS)
        except (AccessError, UserError, ValidationError):
            request.env['ydental.access.service']._denial('exam.view')
            return request.render('ydental_exam.ydental_exam_result_unavailable', {}, status=403, headers=HEADERS)

    @http.route('/ydental/exam/report/<int:line_id>/<int:version>', type='http', auth='user', methods=['GET'])
    def report(self, line_id, version, **kwargs):
        try:
            service = self._service().with_context(lang='zh_CN')
            pdf, digest = service._pdf(line_id, version)
            return request.make_response(pdf, headers=HEADERS + [('Content-Type', 'application/pdf'),
                ('Content-Disposition', 'attachment; filename="ydental-examination-demo.pdf"'),
                ('X-YDental-PDF-SHA256', digest)])
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.report')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=HEADERS)

    @http.route('/ydental/exam/attachment/<int:line_id>/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def attachment(self, line_id, attachment_id, **kwargs):
        try:
            raw, mimetype, name = self._service()._attachment_download(line_id, attachment_id)
            return request.make_response(raw, headers=HEADERS + [('Content-Type', mimetype),
                ('Content-Disposition', 'attachment; filename="examination-evidence"')])
        except (AccessError, UserError, ValidationError) as error:
            request.env['ydental.access.service']._denial('exam.attachment')
            return request.make_json_response({'error': str(error)}, status=403 if isinstance(error, AccessError) else 409,
                headers=HEADERS)
