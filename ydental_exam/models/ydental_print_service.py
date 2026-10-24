from odoo import models
from odoo.exceptions import AccessError, UserError

from odoo.addons.ydental_print.models.ydental_print_service import digest, normalized


class YDentalPrintService(models.AbstractModel):
    _inherit = 'ydental.print.service'

    def _original_authorize(self, kind, source_id, version, purpose=None):
        if kind != 'exam':
            return super()._original_authorize(kind, source_id, version, purpose)
        if purpose or type(version) is not int or version < 1:
            raise AccessError(self.env._('source_required: Select a saved examination result version in this store.'))
        exam = self.env['ydental.exam.service']
        result = exam._model('result').browse(self._id(source_id)).exists()
        if not result:
            raise AccessError(self.env._('source_required: The examination result is unavailable.'))
        exam._line(result.ydental_line_id.id)
        selected = exam._model('version').search([('ydental_result_id', '=', result.id), ('ydental_number', '=', version)], limit=1)
        if not selected:
            raise UserError(self.env._('version_conflict: The selected examination version is unavailable.'))
        return self, result, selected, 'exam'

    def _original_source(self, kind, source_id, version, purpose=None):
        if kind != 'exam':
            return super()._original_source(kind, source_id, version, purpose)
        service, result, selected, category = self._original_authorize(kind, source_id, version, purpose)
        patient = self.env['ydental.patient.service']._patient(result.ydental_patient_id.id)
        line = result.ydental_line_id
        event = result.ydental_event_id
        payload = {'kind': kind, 'title': self.env._('Examination result PDF'), 'template': 'YD-S12-EXAM-1',
            'source_id': result.id, 'version': version,
            'identity': [self._pair(self.env._('Patient'), patient.name), self._pair(self.env._('Patient number'), patient.ydental_number),
                self._pair(self.env._('Source store'), result.ydental_store_id.name)],
            'status': dict(result._fields['state']._description_selection(self.env))[result.state],
            'selected_state': self.env._('Confirmed result text') if selected.ydental_kind in ('confirm', 'correction') else self.env._('Draft result text; incomplete'),
            'details': [self._pair(self.env._('Frozen examination line'), line.id),
                self._pair(self.env._('Examination service'), line.ydental_mapping_id.ydental_catalog_id.name),
                self._pair(self.env._('Original author'), result.ydental_original_author_id.name),
                self._pair(self.env._('Selected version author or confirmer'), selected.ydental_actor_id.name),
                self._pair(self.env._('Actual operator'), event.ydental_actor_id.name if event else False),
                self._pair(self.env._('Actual execution UTC'), str(event.ydental_actual_at) if event else False),
                self._pair(self.env._('Source template code / version'), '%s / %s' % (result.ydental_template_code, result.ydental_template_version)),
                self._pair(self.env._('Version correction reason'), selected.ydental_reason)],
            'sections': [{'label': self.env._('Findings'), 'paragraphs': [selected.ydental_findings or self.env._('Not recorded')]},
                {'label': self.env._('Conclusion'), 'paragraphs': [selected.ydental_conclusion or self.env._('Not recorded')]}],
            'teeth': [], 'lines': [], 'events': [],
            'versions': {'result': [result.id, result.ydental_version, result.state],
                'selected': [selected.id, version, selected.ydental_kind, str(selected.ydental_recorded_at)],
                'line': [line.id, line.state], 'event': [event.id, event.state] if event else False,
                'source_patient': result.ydental_patient_id.id, 'canonical_patient': patient.id}}
        for name, measurement in sorted((selected.ydental_measurements or {}).items()):
            payload['details'].append(self._pair(name, '%s %s / %s' % (measurement.get('value'), measurement.get('unit'), measurement.get('status'))))
        if len(normalized(payload).encode()) > 400000:
            raise UserError(self.env._('size_limit: This examination exceeds the document limit.'))
        return service, result, category, payload, digest(normalized(payload))

    def _original_choices(self):
        choices = super()._original_choices()
        try:
            store = self.env['ydental.exam.service']._store()
        except AccessError:
            return choices
        for result in self.env['ydental.exam.result'].sudo().search(self._original_search_domain([
                ('ydental_store_id', '=', store.id), ('ydental_version', '>', 0)]), order='id desc', limit=100):
            try:
                self._original_authorize('exam', result.id, result.ydental_version)
            except (AccessError, UserError):
                continue
            choices.append({'kind': 'exam', 'id': result.id, 'version': result.ydental_version,
                'state': result.state, 'kind_label': self.env._('Examination result')})
        return choices
