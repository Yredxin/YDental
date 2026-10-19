import hashlib
import json
from datetime import datetime, timezone

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


class YDentalLabChargeService(models.AbstractModel):
    _name = 'ydental.lab.charge.service'
    _description = 'Cycle-bound published-price laboratory additional service'

    def _model(self):
        return self.env['ydental.lab.charge'].sudo()

    def _text(self, value, label, maximum=240):
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            raise ValidationError(self.env._('Enter a valid %s.', label))
        return value.strip()

    def _authorized_order(self, order, *, draft=False):
        if not order or order._name != 'ydental.lab.order' or len(order) != 1:
            raise AccessError(self.env._('access_denied: Select one laboratory cycle through the authorized workflow.'))
        store = self.env['ydental.access.service']._check('medical', 'write', write=True).ydental_store_id
        if order.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: This laboratory cycle is outside the current store.'))
        lab = self.env['ydental.lab.service']
        checked = lab._get_order(order.id, store)
        if checked != order:
            raise AccessError(self.env._('access_denied: The laboratory cycle could not be verified.'))
        if (not order.ydental_parent_order_id or order.ydental_rework_no <= 0 or
                order.ydental_rework_kind != 'additional'):
            raise UserError(self.env._('additional_cycle_required: Patient charges require a true additional-charge rework child.'))
        parent = order.ydental_parent_order_id
        if (parent.ydental_store_id != store or parent.ydental_patient_id != order.ydental_patient_id or
                parent.ydental_source_event_id != order.ydental_source_event_id or
                parent.ydental_source_document_id != order.ydental_source_document_id or
                not order.ydental_source_event_id or order.ydental_source_event_id.state != 'confirmed' or
                order.ydental_source_event_id.ydental_kind != 'treatment' or
                order.ydental_source_event_id.ydental_patient_id != order.ydental_patient_id):
            raise AccessError(self.env._('source_mismatch: The child cycle must preserve its actual original clinical source.'))
        if draft and order.state != 'draft':
            raise UserError(self.env._('version_conflict: Freeze additional-service terms before laboratory dispatch.'))
        return store

    def _prepare_terms(self, order, catalog_id, quantity, confirmation_reference, reason):
        """Freeze explicit terms on a genuine draft child cycle; return the charge row."""
        store = self._authorized_order(order, draft=True)
        # Serialize approvals by real cycle so exact retries recover the same
        # immutable source and competing terms cannot create another charge.
        self.env.cr.execute('SELECT id FROM ydental_lab_order WHERE id = %s FOR UPDATE', [order.id])
        order.invalidate_recordset()
        store = self._authorized_order(order, draft=True)
        if type(catalog_id) is not int or catalog_id <= 0 or type(quantity) not in (int, float):
            raise ValidationError(self.env._('invalid_charge_terms: Select a catalog service and positive quantity.'))
        price_store = self.env['ydental.access.service']._check('price', 'write', write=True).ydental_store_id
        if price_store != store:
            raise AccessError(self.env._('access_denied: Published charge approval requires price authority at this same store.'))
        reference = self._text(confirmation_reference, 'explicit confirmation reference', 120)
        reason = self._text(reason, 'additional-service reason')
        existing = self._model().search([
            ('ydental_order_id', '=', order.id), ('ydental_catalog_id', '=', catalog_id)], limit=1)
        if existing:
            if (existing.ydental_quantity == quantity and
                    existing.ydental_confirmation_reference == reference and
                    existing.ydental_reason == reason and
                    existing.ydental_terms_confirmed_by_id.id == self.env.uid):
                return existing
            raise UserError(self.env._('version_conflict: This cycle already has different immutable additional-service terms.'))
        if order.ydental_additional_terms_frozen:
            raise UserError(self.env._('history_immutable: This cycle already has frozen additional terms.'))
        catalog = self.env['ydental.intake.catalog'].sudo().browse(catalog_id).exists()
        if not catalog or not catalog.active or catalog.ydental_kind not in ('care', 'procedure'):
            raise AccessError(self.env._('access_denied: Select an active patient-service catalog item.'))
        mapping = self.env['ydental.intake.mapping'].sudo().search([
            ('ydental_store_id', '=', store.id), ('ydental_catalog_id', '=', catalog.id), ('active', '=', True)], limit=2)
        if len(mapping) != 1:
            raise UserError(self.env._('service_unavailable: The exact service must be active at the originating store.'))
        intake = self.env['ydental.intake.service']
        currency = store.company_id.currency_id
        now = fields.Datetime.now()
        price, values = intake._quote(store, catalog.id, currency.id, quantity, instant=now)
        if price.ydental_store_id != store or price.ydental_currency_id != currency or price.ydental_catalog_id != catalog:
            raise UserError(self.env._('price_mismatch: The published price must match this store, service and company currency.'))
        fingerprint = hashlib.sha256(json.dumps([
            order.id, store.id, order.ydental_patient_id.id, catalog.id, quantity,
            reference, reason, price.id, self.env.uid,
        ], sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        snapshot_source = 's11-lab-charge-%s-%s' % (order.id, catalog.id)
        previous_snapshot = intake._model('snapshot').search([
            ('ydental_store_id', '=', store.id), ('ydental_source', '=', snapshot_source)], limit=1)
        if previous_snapshot:
            if (previous_snapshot.ydental_catalog_id != catalog or
                    previous_snapshot.ydental_quantity != quantity or
                    previous_snapshot.ydental_price_id != price):
                raise UserError(self.env._('version_conflict: Existing price snapshot does not match this charge.'))
            snapshot = previous_snapshot
        else:
            snapshot = intake._new('snapshot', store, dict(
                values, name=snapshot_source, ydental_source=snapshot_source,
                ydental_policy='demo_confirmation', ydental_actor_id=self.env.uid))
        charge = self._model()._new({
            'name': '%s / %s' % (order.name, catalog.name),
            'ydental_store_id': store.id, 'ydental_category': 'medical',
            'ydental_order_id': order.id, 'ydental_patient_id': order.ydental_patient_id.id,
            'ydental_catalog_id': catalog.id, 'ydental_price_id': price.id,
            'ydental_price_snapshot_id': snapshot.id, 'ydental_quantity': quantity,
            'ydental_uom_id': snapshot.ydental_uom_id.id, 'ydental_currency_id': currency.id,
            'ydental_unit_price': snapshot.ydental_unit_price, 'ydental_amount': snapshot.ydental_amount,
            'ydental_quoted_at': snapshot.ydental_quoted_at,
            'ydental_terms_confirmed_by_id': self.env.uid, 'ydental_terms_confirmed_at': now,
            'ydental_confirmation_reference': reference, 'ydental_reason': reason,
            'ydental_request_key': 'cycle-%s-catalog-%s-v1' % (order.id, catalog.id),
            'ydental_fingerprint': fingerprint, 'state': 'terms_confirmed',
        })
        self.env['ydental.lab.service']._audit('additional_terms_confirmed', order, store,
            after={'charge_id': charge.id, 'catalog_id': catalog.id, 'price_id': price.id,
                   'snapshot_id': snapshot.id, 'amount': charge.ydental_amount}, reason=reason)
        return charge

    def _confirm_performed(self, charge, performed_at, evidence_reference):
        if not charge or charge._name != 'ydental.lab.charge' or len(charge) != 1:
            raise AccessError(self.env._('access_denied: Select a cycle charge through its laboratory action.'))
        charge = self._model().browse(charge.id).exists()
        if not charge or charge.state != 'terms_confirmed':
            raise UserError(self.env._('version_conflict: Only a not-yet-performed confirmed cycle charge can be completed.'))
        store = self._authorized_order(charge.ydental_order_id)
        if charge.ydental_store_id != store or charge.ydental_patient_id != charge.ydental_order_id.ydental_patient_id:
            raise AccessError(self.env._('access_denied: Charge identity no longer matches its cycle.'))
        if charge.ydental_order_id.state not in ('sent', 'processing', 'received', 'available'):
            raise UserError(self.env._('service_not_performed: Confirm only an actual service in an active laboratory cycle.'))
        if not isinstance(performed_at, str) or len(performed_at) > 40:
            raise ValidationError(self.env._('Provide the actual performed UTC time.'))
        try:
            moment = datetime.fromisoformat(performed_at.replace('Z', '+00:00'))
        except ValueError as error:
            raise ValidationError(self.env._('Provide the actual performed UTC time.')) from error
        if moment.tzinfo is None or moment.utcoffset().total_seconds() != 0:
            raise ValidationError(self.env._('Provide a timezone-explicit UTC time.'))
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
        if moment > fields.Datetime.now():
            raise ValidationError(self.env._('A performed service cannot have a future timestamp.'))
        evidence = self._text(evidence_reference, 'performed-service evidence reference', 160)
        self.env.cr.execute('SELECT id FROM ydental_lab_charge WHERE id = %s FOR UPDATE', [charge.id])
        charge.invalidate_recordset()
        if charge.state == 'performed':
            if charge.ydental_performance_evidence_reference == evidence and charge.ydental_performed_at == moment:
                return charge
            raise UserError(self.env._('version_conflict: This cycle charge already has a different performed fact.'))
        if charge.state != 'terms_confirmed':
            raise UserError(self.env._('version_conflict: The charge state changed; refresh before retrying.'))
        charge._save({
            'state': 'performed', 'ydental_performed_by_id': self.env.uid,
            'ydental_performed_at': moment, 'ydental_performance_evidence_reference': evidence,
        })
        self.env['ydental.lab.service']._audit('additional_service_performed', charge.ydental_order_id, store,
            after={'charge_id': charge.id, 'performed_at': fields.Datetime.to_string(moment),
                   'performed_by_id': self.env.uid, 'evidence_reference': evidence},
            reason=charge.ydental_reason)
        return charge
