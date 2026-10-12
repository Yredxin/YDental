from odoo import models
from odoo.exceptions import AccessError, UserError

from .ydental_clinical_service import DocumentLock, SaveIntent


class YDentalQueueService(models.AbstractModel):
    _inherit = 'ydental.queue.service'

    def _document_lock(self, source, operation):
        if type(source) is not DocumentLock or operation not in ('acquire', 'release'):
            raise AccessError(self.env._('access_denied: A trusted independent clinical document is required.'))
        service = self.env['ydental.clinical.service']
        args = {'document_id': source.document_id}
        if operation == 'acquire':
            args.update(lease_id=source.lease_id, lease_token=source.lease_token)
        else:
            args['editor_token'] = source.token
        return service._operate(operation, args)

    def _save_before_handover(self, execution):
        service = self.env['ydental.clinical.service']
        doc = service._model().search([('ydental_current_execution_id', '=', execution.id)], limit=1)
        if execution.ydental_category != 'medical' or not doc:
            raise AccessError(self.env._('save_required: Open and save the real clinical document before handover.'))
        intent = self.env.context.get('ydental_clinical_save')
        valid = type(intent) is SaveIntent and (intent.actor_id, intent.execution_id, intent.document_id, intent.version) == (
            self.env.uid, execution.id, doc.id, doc.ydental_version)
        # On-site recovery uses the last committed draft only after the old
        # connection is invalid; it cannot confirm text or impersonate its author.
        onsite = execution.state == 'verify' or (execution.state == 'reserved' and not execution.ydental_lease_id.ydental_active)
        if not valid and not (onsite and not service._valid_editor(doc) and not execution.ydental_lease_id.ydental_active):
            raise UserError(self.env._('save_required: Synchronize the latest document in the treatment workbench before handover.'))
        if not doc.ydental_version:
            raise UserError(self.env._('save_required: No persisted clinical draft is available.'))
        version = service._model('version').search([('ydental_document_id', '=', doc.id), ('ydental_number', '=', doc.ydental_version)], limit=1)
        if not version or version.ydental_content != doc.ydental_content:
            raise UserError(self.env._('save_required: The current draft and its immutable version must agree.'))
        doc.flush_recordset()
        version.flush_recordset()
        service._audit('handover_save_verified', doc, after={'version': doc.ydental_version})
        return True

    def _release_execution_documents(self, execution):
        super()._release_execution_documents(execution)
        service = self.env['ydental.clinical.service']
        doc = service._model().search([('ydental_current_execution_id', '=', execution.id)], limit=1)
        if doc:
            service._clear_editor(doc)
            if doc.state != 'confirmed':
                doc._save({'state': 'pending'})
            service._audit('handover_edit_release', doc, after={'version': doc.ydental_version, 'state': doc.state})

    def _restore(self, lease_id, token, hold_id, confirmed):
        result = super()._restore(lease_id, token, hold_id, confirmed)
        hold = self._model('hold').browse(hold_id)
        service = self.env['ydental.clinical.service']
        doc = service._model().search([('ydental_current_execution_id', '=', hold.ydental_execution_id.id)], limit=1)
        if doc:
            doc._save({'ydental_current_execution_id': result['execution_id']})
            service._audit('document_return_restored', doc, after={'execution_id': result['execution_id']})
        return result
