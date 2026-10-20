import hashlib
import inspect
import json
import math
import secrets
from datetime import timezone
from urllib.parse import urlsplit

from psycopg2.errors import UniqueViolation

from odoo import api, fields, models
from odoo.exceptions import AccessError, ConcurrencyError, UserError, ValidationError

from ..source import LabStockSource
from .ydental_lab_record import MUTATION


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


class YDentalLabService(models.AbstractModel):
    _name = 'ydental.lab.service'
    _description = 'Guarded vendor, laboratory order and stock lifecycle'

    def _model(self, entity):
        return self.env['ydental.lab.' + entity].sudo()

    def _new_key(self):
        return secrets.token_hex(16)

    def _access(self, write=False):
        category = 'medical'
        store = self.env['ydental.access.service']._check(category, 'write' if write else 'read', write=write).ydental_store_id
        if not store or store.company_id not in self.env.user.sudo().company_ids:
            raise AccessError(self.env._('access_denied: A store in the current company scope is required.'))
        return store

    def _warehouse_write(self, store):
        warehouse = self.env['ydental.access.service']._check('warehouse', 'write', write=True).ydental_store_id
        if warehouse != store:
            raise AccessError(self.env._('access_denied: Warehouse action is outside the current laboratory store.'))
        return warehouse

    def _text(self, value, label, maximum=240):
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
            raise ValidationError(self.env._('%s is required and must be at most %s characters.', label, maximum))
        return value.strip()

    def _validate_positive_quantity(self, value):
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValidationError(self.env._('Use a positive finite laboratory quantity.'))
        return value

    def _external_link(self, value):
        value = self._text(value, 'External platform link', 500)
        parsed = urlsplit(value)
        if (parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.username or
                parsed.password or parsed.query or parsed.fragment):
            raise ValidationError(self.env._('Use a public http or https reference link without credentials, query tokens or fragments.'))
        return value

    def _audit(self, event, target, store, before=None, after=None, reason=False):
        self.env['ydental.access.service']._audit('lab.' + event, 'medical', target, store.id,
            before=before, after=after, reason=reason, source='dental_laboratory')

    def _purchase_cost_values(self, line):
        purchase = line.order_id
        product = line.product_id
        currency = purchase.currency_id
        return {
            'purchase_id': purchase.id,
            'vendor_id': purchase.partner_id.id, 'company_id': purchase.company_id.id,
            'currency_id': currency.id, 'currency_rounding': currency.rounding,
            'line_id': line.id, 'product_id': product.id, 'product_type': product.type,
            'product_company_id': product.company_id.id or False,
            'uom_id': line.uom_id.id, 'product_uom_id': product.uom_id.id,
            'quantity': line.product_qty, 'unit_price': line.price_unit,
            'discount': line.discount, 'subtotal': line.price_subtotal,
            'tax_total': line.price_tax, 'total': line.price_total,
        }

    def _event(self, order, kind, before, after, reason='', inventory_event=None):
        purchase_line = order.ydental_purchase_line_id if kind == 'sent' else self.env['purchase.order.line']
        fee = order.ydental_source_fee_id if kind == 'sent' and not order.ydental_parent_order_id else self.env['ydental.treatment.fee']
        return self._model('event')._new({
            'name': order.name, 'ydental_store_id': order.ydental_store_id.id,
            'ydental_category': 'medical', 'ydental_order_id': order.id,
            'ydental_cooperation_id': order.ydental_cooperation_id.id,
            'ydental_vendor_qualification_version': order.ydental_vendor_qualification_version,
            'ydental_vendor_qualification_valid_until': order.ydental_vendor_qualification_valid_until,
            'ydental_cooperation_active_at_dispatch': order.ydental_cooperation_active_at_dispatch,
            'ydental_actor_id': self.env.uid, 'ydental_kind': kind,
            'ydental_before_state': before or '', 'ydental_after_state': after,
            'ydental_reason': reason, 'ydental_inventory_event_id': inventory_event.id if inventory_event else False,
            'ydental_purchase_line_id': purchase_line.id,
            'ydental_vendor_cost': purchase_line.price_subtotal if purchase_line else 0.0,
            'ydental_cost_currency_id': purchase_line.order_id.currency_id.id if purchase_line else False,
            'ydental_purchase_cost_snapshot': self._purchase_cost_values(purchase_line) if purchase_line else False,
            'ydental_purchase_state_at_dispatch': purchase_line.order_id.state if purchase_line else False,
            'ydental_patient_fee_id': fee.id,
            'ydental_patient_fee_amount': fee.ydental_amount if fee else 0.0,
            'ydental_fee_currency_id': fee.ydental_currency_id.id if fee else False,
            'ydental_recorded_at': fields.Datetime.now(),
        })

    def _check_purchase_line(self, order):
        line = order.ydental_purchase_line_id
        if order.ydental_parent_order_id and order.ydental_rework_kind == 'free':
            if line:
                raise ValidationError(self.env._('Free rework cannot duplicate the original vendor cost source.'))
            return False
        if order.ydental_zero_supplier_cost_confirmed and line:
            raise UserError(self.env._('history_immutable: A zero supplier-cost attestation cannot be combined with a purchase cost source.'))
        if not line:
            if (order.ydental_parent_order_id and order.ydental_rework_kind == 'additional' and
                    order.ydental_zero_supplier_cost_confirmed):
                return False
            raise ValidationError(self.env._('Link a confirmed native vendor purchase line before dispatch.'))
        line = self._validate_purchase_line(order, line)
        sent = self._model('event').search([
            ('ydental_order_id', '=', order.id), ('ydental_kind', '=', 'sent')], order='id', limit=1)
        if sent and sent.ydental_purchase_cost_snapshot != self._purchase_cost_values(line):
            raise UserError(self.env._('vendor_cost_changed: The confirmed vendor cost line changed after dispatch; reconcile the original cost source.'))
        return line

    def _purchase_cost_snapshot(self, order):
        sent = self._model('event').search([
            ('ydental_order_id', '=', order.id), ('ydental_kind', '=', 'sent')], order='id', limit=1)
        if not sent:
            raise UserError(self.env._('vendor_cost_snapshot_missing: Dispatch has no immutable vendor-cost snapshot.'))
        line = order.ydental_purchase_line_id
        if not line:
            if order.ydental_parent_order_id and order.ydental_rework_kind == 'additional' and order.ydental_zero_supplier_cost_confirmed:
                return False
            if order.ydental_parent_order_id and order.ydental_rework_kind == 'free':
                return False
            raise UserError(self.env._('vendor_cost_snapshot_missing: A vendor cost source is required.'))
        line = self._validate_purchase_line(order, line)
        if sent.ydental_purchase_cost_snapshot != self._purchase_cost_values(line):
            raise UserError(self.env._('vendor_cost_changed: The vendor cost source changed after dispatch.'))
        return line

    def _validate_purchase_line(self, order, line):
        # Read only the specific purchase line already linked to this scoped order.
        line = self.env['purchase.order.line'].sudo().browse(line.id).exists()
        if not line:
            raise ValidationError(self.env._('Select an existing confirmed vendor purchase line.'))
        purchase = line.order_id
        if (purchase.state not in ('purchase', 'done') or purchase.partner_id != order.ydental_vendor_id.partner_id or
                purchase.company_id != order.ydental_store_id.company_id or
                purchase.currency_id != order.ydental_store_id.company_id.currency_id or
                line.product_id.type != 'service' or
                (line.product_id.company_id and line.product_id.company_id != purchase.company_id) or
                not line.uom_id or not line.uom_id._has_common_reference(line.product_id.uom_id) or
                line.product_qty <= 0 or line.price_unit <= 0 or line.price_subtotal <= 0 or
                line.discount < 0 or line.discount >= 100 or
                purchase.currency_id.compare_amounts(
                    line.price_subtotal,
                    purchase.currency_id.round(line.product_qty * line.price_unit * (1 - line.discount / 100.0))) or
                line.price_total < line.price_subtotal or
                purchase.currency_id.compare_amounts(line.price_subtotal, line.price_total - line.price_tax)):
            raise ValidationError(self.env._('Vendor cost must be a nonzero service line on a confirmed purchase for this vendor, store company and currency.'))
        self._assert_purchase_line_exclusive(order, line)
        return line

    def _confirm_zero_supplier_cost(self, store, order_id, reason):
        order = self._get_order(order_id, store)
        self.env.cr.execute(
            'SELECT id FROM ydental_lab_order WHERE id = %s FOR UPDATE', [order.id])
        order.invalidate_recordset([
            'state', 'ydental_parent_order_id', 'ydental_rework_kind',
            'ydental_purchase_line_id', 'ydental_zero_supplier_cost_confirmed',
        ])
        if (not self.env.user.has_group('purchase.group_purchase_user') or
                not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional' or
                order.state != 'draft' or order.ydental_purchase_line_id):
            raise AccessError(self.env._('access_denied: Purchase authority may attest zero added supplier cost only on a draft additional rework cycle without a purchase line.'))
        if order.ydental_zero_supplier_cost_confirmed:
            raise UserError(self.env._('version_conflict: Zero added supplier cost is already recorded for this cycle.'))
        reason = self._text(reason, 'Zero added supplier cost reason')
        self._event(order, 'zero_supplier_cost_confirmed', order.state, order.state, reason)
        order._save({
            'ydental_zero_supplier_cost_confirmed': True,
            'ydental_zero_supplier_cost_reason': reason,
            'ydental_zero_supplier_cost_actor_id': self.env.uid,
            'ydental_zero_supplier_cost_at': fields.Datetime.now(),
        })
        self._audit('zero_supplier_cost_confirmed', order, store,
                    after={'supplier_cost': 0.0, 'patient_terms_separate': True}, reason=reason)
        return {'order_id': order.id, 'zero_supplier_cost_confirmed': True}

    def _confirm_no_patient_fee(self, store, order_id):
        order = self._get_order(order_id, store)
        self.env.cr.execute(
            'SELECT id FROM ydental_lab_order WHERE id = %s FOR UPDATE', [order.id])
        order.invalidate_recordset([
            'state', 'ydental_parent_order_id', 'ydental_rework_kind',
            'ydental_additional_terms_frozen', 'ydental_no_patient_fee_declaration',
            'ydental_no_patient_fee_confirmed', 'ydental_no_patient_fee_confirmation_reason',
            'ydental_purchase_line_id',
        ])
        if (not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional' or
                order.state != 'draft' or order.ydental_additional_terms_frozen or
                order.ydental_no_patient_fee_confirmed):
            raise UserError(self.env._('No-patient-fee terms can be confirmed only once on a draft additional rework cycle.'))
        price_store = self.env['ydental.access.service']._check('price', 'write', write=True).ydental_store_id
        if price_store != store:
            raise AccessError(self.env._('access_denied: No-patient-fee approval requires commercial authority at this same store.'))
        if not order.ydental_no_patient_fee_declaration:
            raise ValidationError(self.env._('Explicitly declare that no patient fee will be charged.'))
        if (order.ydental_additional_service_id or order.ydental_additional_service_quantity or
                order.ydental_additional_consent_reference or order.ydental_additional_terms_reason):
            raise UserError(self.env._('Clear priced-service inputs before confirming a no-patient-fee cycle.'))
        reason = self._text(
            order.ydental_no_patient_fee_confirmation_reason,
            'Reason no patient fee will be charged', 240)
        if order.ydental_charge_ids:
            raise UserError(self.env._('A patient charge source already exists for this cycle; no-patient-fee confirmation is unavailable.'))
        self._event(order, 'no_patient_fee_confirmed', order.state, order.state, reason)
        order._save({
            'ydental_no_patient_fee_confirmed': True,
            'ydental_no_patient_fee_reason': reason,
            'ydental_no_patient_fee_actor_id': self.env.uid,
            'ydental_no_patient_fee_at': fields.Datetime.now(),
        })
        self._audit('no_patient_fee_confirmed', order, store,
                    after={'patient_fee': 0.0, 'supplier_cost_independent': True}, reason=reason)
        return {'order_id': order.id, 'no_patient_fee_confirmed': True}

    def _assert_purchase_line_exclusive(self, order, line):
        domain = [('ydental_purchase_line_id', '=', line.id)]
        if type(order.id) is int and order.id > 0:
            domain.append(('id', '!=', order.id))
        if self._model('order').search(domain, limit=1):
            raise ValidationError(self.env._('A confirmed vendor purchase line can fund only one laboratory cycle.'))
        return True

    def _order_identity(self, event_id, vals, store):
        if type(event_id) is not int or event_id <= 0:
            raise ValidationError(self.env._('Select a confirmed clinical treatment source.'))
        if {'ydental_additional_service_id', 'ydental_additional_service_quantity',
                'ydental_additional_consent_reference', 'ydental_additional_terms_reason',
                'ydental_additional_terms_frozen', 'ydental_additional_performed_at',
                'ydental_additional_performance_evidence_reference',
                'ydental_additional_performance_recorded',
                'ydental_zero_supplier_cost_confirmed', 'ydental_zero_supplier_cost_reason',
                'ydental_zero_supplier_cost_actor_id', 'ydental_zero_supplier_cost_at',
                'ydental_no_patient_fee_declaration', 'ydental_no_patient_fee_confirmation_reason',
                'ydental_no_patient_fee_confirmed', 'ydental_no_patient_fee_reason',
                'ydental_no_patient_fee_actor_id', 'ydental_no_patient_fee_at',
                'ydental_post_fit_repair'} & vals.keys():
            raise AccessError(self.env._('access_denied: Repair-cycle fields can be created only through the guarded laboratory workflow.'))
        event = self.env['ydental.treatment.event'].sudo().browse(event_id).exists()
        if not event or event.ydental_store_id != store or event.ydental_category != 'medical' or event.state != 'confirmed' or event.ydental_kind != 'treatment':
            raise AccessError(self.env._('access_denied: A confirmed treatment source in the selected store is required.'))
        document = event.ydental_document_id
        if not document or document.ydental_patient_id != event.ydental_patient_id:
            raise ValidationError(self.env._('A linked clinical document for the same patient is required.'))
        product = self.env['product.product'].sudo().browse(vals.get('ydental_product_id', 0)).exists()
        if not product or not product.active or product.ydental_inventory_kind != 'prosthesis' or product.company_id and product.company_id != store.company_id:
            raise ValidationError(self.env._('Select an active prosthesis product in the store company.'))
        self._check_vendor_id(vals.get('ydental_vendor_id'), store, product)
        self._validate_positive_quantity(vals.get('ydental_quantity', 1.0))
        if vals.get('ydental_parent_order_id'):
            raise ValidationError(self.env._('Create repair cycles through the guarded rework action.'))
        source_fee = self.env['ydental.treatment.fee'].sudo().search([('ydental_event_id', '=', event.id)], limit=1)
        lot_id = vals.get('ydental_lot_id')
        if lot_id:
            lot = self.env['ydental.inventory.service']._lot(lot_id, store)
            if lot.product_id != product:
                raise ValidationError(self.env._('The receiving lot must match the ordered prosthesis product.'))
        for field_name, label in (('ydental_material', 'Material'), ('ydental_instructions', 'Clinical instructions'),
                                  ('ydental_internal_code', 'Internal order code')):
            vals[field_name] = self._text(vals.get(field_name), label, 1200 if field_name == 'ydental_instructions' else 120)
        if vals.get('ydental_shade'):
            vals['ydental_shade'] = self._text(vals['ydental_shade'], 'Shade', 80)
        responsible_id = vals.get('ydental_responsible_id') or self.env.uid
        self.env['ydental.followup.service']._responsible(responsible_id, store)
        if vals.get('ydental_external_reference'):
            vals['ydental_external_reference'] = self._text(vals['ydental_external_reference'], 'External reference', 120)
        if vals.get('ydental_external_url'):
            vals['ydental_external_url'] = self._external_link(vals['ydental_external_url'])
        if vals.get('ydental_external_actor'):
            vals['ydental_external_actor'] = self._text(vals['ydental_external_actor'], 'External platform operator', 120)
        teeth = vals.get('ydental_teeth', [])
        if not isinstance(teeth, list) or not teeth or len(teeth) > 32 or any(type(tooth) is not int or tooth not in range(11, 49) or tooth % 10 not in range(1, 9) for tooth in teeth) or len(set(teeth)) != len(teeth):
            raise ValidationError(self.env._('Select distinct FDI teeth for this laboratory order.'))
        return {
            'name': self._text(vals.get('name'), 'Work order name'),
            'ydental_patient_id': event.ydental_patient_id.id,
            'ydental_source_document_id': document.id,
            'ydental_source_fee_id': source_fee.id,
            'ydental_responsible_id': responsible_id,
            'ydental_internal_code': self._text(vals.get('ydental_internal_code'), 'Internal order code', 80),
            'ydental_teeth': teeth,
        }

    def _check_vendor_id(self, vendor_id, store, product):
        if type(vendor_id) is not int or vendor_id <= 0:
            raise ValidationError(self.env._('Select an approved and cooperating laboratory.'))
        vendor = self._model('vendor').browse(vendor_id).exists()
        cooperation = self._model('cooperation').search([
            ('ydental_store_id', '=', store.id), ('ydental_vendor_id', '=', vendor.id), ('active', '=', True),
        ], limit=1)
        today = fields.Date.context_today(self)
        if not vendor or store.company_id not in vendor.company_ids or vendor.state != 'approved' or vendor.valid_until < today or not cooperation:
            raise AccessError(self.env._('access_denied: The laboratory must be approved, current and enabled for this store.'))
        return vendor

    def _check_vendor(self, vendor, store, product):
        return self._check_vendor_id(vendor.id, store, product)

    def _get_order(self, order_id, store):
        if type(order_id) is not int or order_id <= 0:
            raise ValidationError(self.env._('Select a valid laboratory order.'))
        order = self._model('order').browse(order_id).exists()
        if not order or order.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Order is outside the selected store.'))
        return order

    def _record_action(self, order, kind, reason='', inventory_event=None, values=None):
        before = order.state
        order._save(dict(values or {}))
        after = order.state
        self._event(order, kind, before, after, reason, inventory_event)
        self._audit(kind, order, order.ydental_store_id, before={'state': before}, after={'state': after}, reason=reason)
        return {'order_id': order.id, 'state': after, 'inventory_event_id': inventory_event.id if inventory_event else False}

    def _review_vendor(self, vendor, decision, reason):
        access = self.env['ydental.access.service']
        access._require_internal()
        if not access._is_group_manager() or decision not in ('approved', 'rejected'):
            raise AccessError(self.env._('access_denied: Group governance authority is required.'))
        vendor.check_access('write')
        if not set(vendor.company_ids.ids) <= set(self.env.user.sudo().company_ids.ids):
            raise AccessError(self.env._('access_denied: Vendor qualification is outside allowed companies.'))
        if not vendor.exists() or vendor.valid_until < fields.Date.context_today(self) or not vendor.qualification_reference.strip():
            raise ValidationError(self.env._('Current qualification evidence and a future expiry date are required.'))
        if decision == 'approved' and not vendor.qualification_evidence:
            raise ValidationError(self.env._('Attach the reviewed vendor qualification evidence before approval.'))
        reason = self._text(reason, 'Review reason')
        before = vendor.state
        vendor.sudo().with_context(ydental_lab_mutation=MUTATION).write({
                'state': decision, 'reviewed_by_id': self.env.uid,
                'reviewed_at': fields.Datetime.now(), 'review_reason': reason,
                'qualification_version': vendor.qualification_version + 1,
            })
        access._audit('lab.vendor.' + decision, 'personnel', vendor, after={'state': decision}, reason=reason, source='dental_laboratory')
        self._queue_vendor_expiry(vendor)
        return {'vendor_id': vendor.id, 'state': decision}

    def _queue_vendor_expiry(self, vendor):
        """Create store-scoped internal review tasks for active vendor cooperations."""
        if not vendor or len(vendor) != 1 or vendor.state != 'approved' or not vendor.valid_until:
            return
        access = self.env['ydental.access.service']
        domain = [
            ('ydental_vendor_id', '=', vendor.id), ('active', '=', True),
        ]
        if not access._is_group_manager():
            session = access._scope()
            if not session.ydental_store_id:
                return
            domain.append(('ydental_store_id', '=', session.ydental_store_id.id))
        cooperations = self._model('cooperation').search(domain)
        for cooperation in cooperations:
            store = cooperation.ydental_store_id
            if store.company_id not in vendor.company_ids:
                continue
            due_at = fields.Datetime.to_datetime(vendor.valid_until)
            due_at = '%sT00:00:00' % vendor.valid_until.isoformat()
            self.env['ydental.followup.service']._queue_supplier_expiry(
                vendor, store, due_at, cooperation.responsible_id.id)

    @api.model
    def _operate(self, operation, payload, key):
        handlers = {
            'send': self._send, 'processing': self._processing, 'receive': self._receive,
            'putaway': self._putaway, 'rework': self._rework, 'cancel': self._cancel,
            'exception': self._exception, 'fit': self._fit, 'bind_code': self._bind_code,
            'post_fit_repair': self._post_fit_repair,
            'approve_charge_terms': self._approve_charge_terms,
            'confirm_charge_performed': self._confirm_charge_performed,
            'confirm_zero_supplier_cost': self._confirm_zero_supplier_cost,
            'confirm_no_patient_fee': self._confirm_no_patient_fee,
        }
        if operation not in handlers or not isinstance(payload, dict) or not isinstance(key, str) or not 16 <= len(key) <= 128:
            raise ValidationError(self.env._('Supply a documented laboratory action and stable request key.'))
        try:
            # Each private handler receives the current store explicitly from
            # this dispatcher; bind a placeholder for that server-owned value
            # while validating only the client-supplied payload here.
            inspect.signature(handlers[operation]).bind(None, **payload)
        except TypeError as error:
            raise ValidationError(self.env._('Unknown or missing laboratory action arguments.')) from error
        store = self._access(write=True)
        digest = fingerprint([operation, store.id, payload])
        with self.env.cr.savepoint():
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s)', [31911])
            if operation in ('putaway', 'rework', 'exception', 'fit'):
                self.env['ydental.inventory.service']._lock()
            self._access(write=True)
            prior = self._model('operation').search([('ydental_store_id', '=', store.id), ('ydental_key', '=', key)], limit=1)
            if prior:
                if prior.ydental_fingerprint != digest:
                    raise UserError(self.env._('version_conflict: This key belongs to a different laboratory action.'))
                return dict(prior.ydental_result, result='already_accepted')
            result = handlers[operation](store, **payload)
            try:
                # Under REPEATABLE READ the losing transaction cannot see the
                # winner's row after waiting on the unique index. Roll back
                # this action's savepoint and let Odoo retry the whole request
                # with a fresh snapshot, where it will return the stored result.
                with self.env.cr.savepoint():
                    self._model('operation')._new({
                        'name': operation, 'ydental_store_id': store.id, 'ydental_category': 'medical',
                        'ydental_key': key, 'ydental_fingerprint': digest, 'ydental_result': result,
                        'ydental_actor_id': self.env.uid,
                    })
            except UniqueViolation as error:
                if error.diag.constraint_name != 'ydental_lab_operation_store_key_unique':
                    raise
                message = 'Concurrent laboratory request key was committed by another transaction.'
                raise ConcurrencyError(message) from error
            return dict(result, result='accepted')

    def _send(self, store, order_id):
        order = self._get_order(order_id, store)
        self.env.cr.execute(
            'SELECT id FROM ydental_lab_order WHERE id = %s FOR UPDATE', [order.id])
        order.invalidate_recordset([
            'state', 'ydental_parent_order_id', 'ydental_rework_kind',
            'ydental_additional_terms_frozen', 'ydental_no_patient_fee_confirmed',
            'ydental_purchase_line_id', 'ydental_zero_supplier_cost_confirmed',
        ])
        if order.state != 'draft':
            raise UserError(self.env._('Only a draft can be sent to the laboratory.'))
        if order.ydental_parent_order_id and order.ydental_rework_kind == 'additional':
            if order.ydental_additional_terms_frozen == order.ydental_no_patient_fee_confirmed:
                raise UserError(self.env._('Confirm either published patient-fee terms or an explicit no-patient-fee declaration before dispatch.'))
        vendor = self._check_vendor(order.ydental_vendor_id, store, order.ydental_product_id)
        cooperation = self._model('cooperation').search([
            ('ydental_store_id', '=', store.id),
            ('ydental_vendor_id', '=', vendor.id),
            ('active', '=', True),
        ], limit=1)
        if not cooperation:
            raise AccessError(self.env._('access_denied: An active store cooperation is required at dispatch.'))
        self._check_purchase_line(order)
        if order.ydental_external_mode == 'digital' and not order.ydental_external_reference:
            raise ValidationError(self.env._('Record the external platform reference before sending.'))
        if order.ydental_external_mode == 'digital' and not order.ydental_external_actor:
            raise ValidationError(self.env._('Record the actual external platform operator before sending.'))
        return self._record_action(order, 'sent', values={
            'state': 'sent',
            'ydental_cooperation_id': cooperation.id,
            'ydental_vendor_qualification_version': vendor.qualification_version,
            'ydental_vendor_qualification_valid_until': vendor.valid_until,
            'ydental_cooperation_active_at_dispatch': True,
        })

    def _approve_charge_terms(self, store, order_id):
        order = self._get_order(order_id, store)
        self.env.cr.execute(
            'SELECT id FROM ydental_lab_order WHERE id = %s FOR UPDATE', [order.id])
        order.invalidate_recordset([
            'state', 'ydental_parent_order_id', 'ydental_rework_kind',
            'ydental_additional_terms_frozen', 'ydental_no_patient_fee_declaration',
            'ydental_no_patient_fee_confirmed', 'ydental_additional_service_id',
            'ydental_additional_service_quantity', 'ydental_additional_consent_reference',
            'ydental_additional_terms_reason',
        ])
        if (order.state != 'draft' or not order.ydental_parent_order_id or
                order.ydental_rework_kind != 'additional'):
            raise UserError(self.env._('Additional-service terms can be approved only for a draft additional-charge rework cycle.'))
        if order.ydental_additional_terms_frozen:
            raise UserError(self.env._('Additional-service terms are already frozen for this cycle.'))
        if order.ydental_no_patient_fee_declaration or order.ydental_no_patient_fee_confirmed:
            raise UserError(self.env._('A no-patient-fee declaration is selected for this cycle; it cannot also create patient charge terms.'))
        catalog = order.ydental_additional_service_id
        if not catalog or not catalog.active:
            raise ValidationError(self.env._('Select an active S05 service before approving additional terms.'))
        quantity = self._validate_positive_quantity(order.ydental_additional_service_quantity)
        confirmation_reference = self._text(
            order.ydental_additional_consent_reference, 'Explicit terms confirmation reference', 120)
        reason = self._text(order.ydental_additional_terms_reason, 'Additional terms reason', 240)
        bridge_model = 'ydental.lab.charge.service'
        if bridge_model not in self.env.registry.models:
            raise UserError(self.env._('The cycle-bound laboratory charge bridge is not installed; no patient charge was created.'))
        charge = self.env[bridge_model]._prepare_terms(
            order, catalog.id, quantity, confirmation_reference, reason)
        if (not charge or charge._name != 'ydental.lab.charge' or len(charge) != 1 or
                charge.ydental_order_id != order or charge.ydental_store_id != store or
                charge.ydental_patient_id != order.ydental_patient_id or
                charge.ydental_catalog_id != catalog or charge.ydental_quantity != quantity or
                charge.state != 'terms_confirmed'):
            raise AccessError(self.env._('access_denied: The native charge bridge returned a source outside this approved cycle.'))
        order._save({'ydental_additional_terms_frozen': True})
        self._event(order, 'additional_terms_approved', order.state, order.state, reason)
        self._audit('additional_terms_approved', order, store,
                    after={'charge_source_id': charge.id, 'catalog_id': catalog.id,
                           'quantity': quantity, 'currency_id': charge.ydental_currency_id.id}, reason=reason)
        return {'order_id': order.id, 'charge_source_id': charge.id, 'terms_frozen': True,
                'state': charge.state}

    def _confirm_charge_performed(self, store, order_id):
        order = self._get_order(order_id, store)
        if (not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional' or
                not order.ydental_additional_terms_frozen or order.ydental_additional_performance_recorded or
                order.state not in ('sent', 'processing', 'received', 'available')):
            raise UserError(self.env._('Actual additional-service confirmation requires an approved active child rework cycle.'))
        if not order.ydental_additional_performed_at:
            raise ValidationError(self.env._('Enter the actual additional-service performance time.'))
        performed_at = fields.Datetime.to_datetime(order.ydental_additional_performed_at)
        if not performed_at or performed_at > fields.Datetime.now():
            raise ValidationError(self.env._('Enter a valid actual service time that is not in the future.'))
        evidence_reference = self._text(
            order.ydental_additional_performance_evidence_reference,
            'Additional service performance evidence reference', 160)
        if 'ydental.lab.charge.service' not in self.env.registry.models:
            raise UserError(self.env._('The cycle-bound laboratory charge bridge is not installed; no performed charge was recorded.'))
        charges = order.ydental_charge_ids
        if len(charges) != 1 or charges.state != 'terms_confirmed':
            raise UserError(self.env._('One cycle-bound approved charge source is required before confirming performed service.'))
        charge = self.env['ydental.lab.charge.service']._confirm_performed(
            charges, performed_at.replace(tzinfo=timezone.utc).isoformat(), evidence_reference)
        if (not charge or charge._name != 'ydental.lab.charge' or len(charge) != 1 or
                charge.ydental_order_id != order or charge.ydental_store_id != store or
                charge.ydental_patient_id != order.ydental_patient_id or
                charge.ydental_catalog_id != order.ydental_additional_service_id or
                charge.ydental_quantity != order.ydental_additional_service_quantity or
                charge.state != 'performed'):
            raise AccessError(self.env._('access_denied: The native charge bridge did not confirm the exact cycle source.'))
        order._save({'ydental_additional_performance_recorded': True})
        self._event(order, 'additional_service_performed', order.state, order.state, evidence_reference)
        self._audit('additional_service_performed', order, store,
                    after={'charge_source_id': charge.id,
                           'performed_at': fields.Datetime.to_string(performed_at)}, reason=evidence_reference)
        return {'order_id': order.id, 'charge_source_id': charge.id,
                'state': charge.state, 'performed_at': fields.Datetime.to_string(performed_at)}

    def _processing(self, store, order_id):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        if order.state != 'sent':
            raise UserError(self.env._('Only a sent order can enter processing.'))
        self._purchase_cost_snapshot(order)
        return self._record_action(order, 'processing', values={'state': 'processing'})

    def _receive(self, store, order_id):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        if order.state not in ('sent', 'processing'):
            raise UserError(self.env._('Only an active external order can be physically received.'))
        self._purchase_cost_snapshot(order)
        if (not order.ydental_cooperation_id or not order.ydental_vendor_qualification_version or
                not order.ydental_vendor_qualification_valid_until or
                not order.ydental_cooperation_active_at_dispatch):
            raise UserError(self.env._('The dispatch authorization snapshot is missing; stop and reconcile the work order.'))
        return self._record_action(order, 'received', values={
            'state': 'received', 'ydental_receipt_at': fields.Datetime.now(),
            'ydental_receipt_actor_id': self.env.uid,
        })

    def _putaway(self, store, order_id):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        if order.state != 'received' or not order.ydental_lot_id or order.ydental_lot_id.product_id != order.ydental_product_id:
            raise UserError(self.env._('Physical receipt and the matching native prosthesis lot are required before put-away.'))
        self._purchase_cost_snapshot(order)
        inventory = self.env['ydental.inventory.service']
        stock = inventory._operate('receive', {
            'lot_id': order.ydental_lot_id.id, 'quantity': order.ydental_quantity,
            'uom_id': order.ydental_product_id.uom_id.id,
            'source_key': 'lab-receipt-%s' % order.id,
            'reason': 'External laboratory work order %s received and put away' % order.ydental_internal_code,
        }, 'lab-putaway-%s' % order.id)
        inventory_event = self.env['ydental.inventory.event'].sudo().browse(stock['id']).exists()
        accessible_order = self.env['ydental.lab.order'].browse(order.id)
        followup = self.env['ydental.followup.service']._create_passive_from_lab_order(
            accessible_order, order.ydental_planned_at, order.ydental_responsible_id.id)
        result = self._record_action(order, 'putaway', inventory_event=inventory_event, values={
            'state': 'available', 'ydental_inventory_event_id': inventory_event.id,
            'ydental_followup_id': followup.id,
        })
        return result

    def _rework(self, store, order_id):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        if order.state != 'available':
            raise UserError(self.env._('Rework requires an actual put-away item that has not been fitted.'))
        if not order.ydental_rework_kind:
            raise ValidationError(self.env._('Select whether this cycle is free or has separately agreed additional terms.'))
        reason = self._text(order.ydental_exception_reason, 'Rework reason')
        self._check_vendor(order.ydental_vendor_id, store, order.ydental_product_id)
        source = LabStockSource(self.env.uid, store.id, order.id, 'supplier_return')
        stock = self.env['ydental.inventory.service']._lab_workflow_move(source, reason)
        inventory_event = self.env['ydental.inventory.event'].sudo().browse(stock['id']).exists()
        self._record_action(order, 'rework_return', reason, inventory_event, {'state': 'rework_returned'})
        child = self._model('order')._new({
            'name': order.name + ' / Rework', 'ydental_store_id': store.id, 'ydental_category': 'medical',
            'ydental_patient_id': order.ydental_patient_id.id,
            'ydental_source_event_id': order.ydental_source_event_id.id,
            'ydental_source_document_id': order.ydental_source_document_id.id,
            'ydental_source_fee_id': order.ydental_source_fee_id.id,
            'ydental_vendor_id': order.ydental_vendor_id.id, 'ydental_product_id': order.ydental_product_id.id,
            'ydental_lot_id': order.ydental_lot_id.id, 'ydental_quantity': order.ydental_quantity,
            'ydental_teeth': order.ydental_teeth, 'ydental_material': order.ydental_material,
            'ydental_shade': order.ydental_shade, 'ydental_instructions': order.ydental_instructions,
            'ydental_responsible_id': order.ydental_responsible_id.id,
            'ydental_planned_at': order.ydental_planned_at,
            'ydental_external_mode': order.ydental_external_mode,
            'ydental_internal_code': '%s-R%s' % (order.ydental_internal_code, order.id),
            'ydental_parent_order_id': order.id, 'ydental_rework_no': 1,
            'ydental_rework_kind': order.ydental_rework_kind,
        })
        self.env['ydental.followup.service']._supersede_lab_followup(
            self.env['ydental.lab.order'].browse(child.id),
            'A new laboratory rework cycle supersedes the pending arrival follow-up.')
        self._event(child, 'rework', '', 'draft', reason, inventory_event)
        self._audit('rework', child, store, after={'parent_order_id': order.id, 'rework_no': child.ydental_rework_no}, reason=reason)
        return {'order_id': order.id, 'repair_order_id': child.id, 'state': order.state, 'inventory_event_id': inventory_event.id}

    def _cancel(self, store, order_id, reason):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        reason = self._text(reason, 'Cancellation reason')
        if order.state not in ('draft', 'sent', 'processing'):
            raise UserError(self.env._('Cancellation is allowed only before physical receipt.'))
        return self._record_action(order, 'cancelled', reason, values={'state': 'cancelled', 'ydental_exception_reason': reason})

    def _exception(self, store, order_id, disposition, reason):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        reason = self._text(reason, 'Exception disposition and reason')
        if order.state != 'available' or disposition not in ('supplier_return', 'discard'):
            raise UserError(self.env._('Put the item into stock first, then close the exception with an actual return or write-off disposition.'))
        inventory_event = self.env['ydental.inventory.event']
        source = LabStockSource(self.env.uid, store.id, order.id, disposition)
        result = self.env['ydental.inventory.service']._lab_workflow_move(source, reason)
        inventory_event = inventory_event.sudo().browse(result['id']).exists()
        result = self._record_action(order, 'exception', reason, inventory_event, {
            'state': 'exception', 'ydental_exception_disposition': disposition,
            'ydental_exception_reason': reason,
        })
        self.env['ydental.followup.service']._close_lab_followup_after_exception(order, reason)
        return result

    def _fit(self, store, order_id, fit_event_id):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        event = self.env['ydental.treatment.event'].sudo().browse(fit_event_id).exists()
        if order.state != 'available' or not event or event.ydental_kind != 'treatment' or event.state != 'confirmed' or (
                event.ydental_store_id != store or event.ydental_patient_id != order.ydental_patient_id or
                event.ydental_execution_id.ydental_patient_id != order.ydental_patient_id):
            raise AccessError(self.env._('access_denied: Fit completion requires a confirmed actual treatment event for this patient and store.'))
        stock = self.env['ydental.inventory.service']._operate('issue', {
            'lot_id': order.ydental_lot_id.id, 'quantity': order.ydental_quantity,
            'uom_id': order.ydental_product_id.uom_id.id,
            'source_key': 'lab-fit-%s' % order.id,
            'reason': 'Actual prosthesis fit, clinical event %s' % event.id,
        }, 'lab-fit-%s' % order.id)
        inventory_event = self.env['ydental.inventory.event'].sudo().browse(stock['id']).exists()
        return self._record_action(order, 'fit', inventory_event=inventory_event, values={
            'state': 'done', 'ydental_fit_event_id': event.id, 'ydental_fit_inventory_event_id': inventory_event.id,
        })

    def _post_fit_repair(self, store, order_id, reason):
        """Open a new draft cycle after a real fit without changing the completed source."""
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        reason = self._text(reason, 'Post-fit repair reason')
        self.env.cr.execute('SELECT id FROM ydental_lab_order WHERE id=%s FOR UPDATE', [order.id])
        order.invalidate_recordset()
        fit_event = order.ydental_fit_event_id
        if (order.state != 'done' or not fit_event or fit_event.state != 'confirmed' or
                fit_event.ydental_kind != 'treatment' or fit_event.ydental_store_id != store or
                fit_event.ydental_patient_id != order.ydental_patient_id or
                fit_event.ydental_execution_id.ydental_patient_id != order.ydental_patient_id or
                not order.ydental_fit_inventory_event_id):
            raise UserError(self.env._('A post-fit repair requires an actually fitted order with its confirmed treatment and stock issue.'))
        open_repair = self._model('order').search([
            ('ydental_parent_order_id', '=', order.id), ('ydental_post_fit_repair', '=', True),
            ('state', 'not in', ('done', 'cancelled', 'exception')),
        ], limit=1)
        if open_repair:
            raise UserError(self.env._('An unfinished post-fit repair cycle is already linked to this completed order.'))
        prior_cycles = self._model('order').search([
            ('ydental_parent_order_id', '=', order.id),
        ], order='ydental_rework_no desc, id desc', limit=1)
        repair_no = prior_cycles.ydental_rework_no + 1 if prior_cycles else 1
        child = self._model('order')._new({
            'name': self.env._('%s / Post-fit repair %s', order.name, repair_no),
            'ydental_store_id': store.id, 'ydental_category': 'medical',
            'ydental_patient_id': order.ydental_patient_id.id,
            'ydental_source_event_id': order.ydental_source_event_id.id,
            'ydental_source_document_id': order.ydental_source_document_id.id,
            # The original fee remains on the completed source order only. A
            # post-fit repair starts with no patient charge or supplier cost.
            'ydental_vendor_id': order.ydental_vendor_id.id,
            'ydental_product_id': order.ydental_product_id.id,
            'ydental_lot_id': order.ydental_lot_id.id,
            'ydental_quantity': order.ydental_quantity,
            'ydental_teeth': order.ydental_teeth,
            'ydental_material': order.ydental_material,
            'ydental_shade': order.ydental_shade,
            'ydental_instructions': order.ydental_instructions,
            'ydental_responsible_id': order.ydental_responsible_id.id,
            'ydental_planned_at': fields.Datetime.now(),
            'ydental_external_mode': order.ydental_external_mode,
            'ydental_internal_code': 'PF-%s-%s-%s' % (order.ydental_internal_code[:32], order.id, repair_no),
            'ydental_parent_order_id': order.id,
            'ydental_rework_no': repair_no,
            'ydental_post_fit_repair': True,
        })
        self.env['ydental.followup.service']._supersede_lab_followup(
            self.env['ydental.lab.order'].browse(child.id),
            'A post-fit repair cycle supersedes the completed order follow-up.')
        self._event(child, 'post_fit_repair', 'done', 'draft', reason)
        self._audit('post_fit_repair_open', child, store,
                    before={'parent_order_id': order.id, 'parent_state': 'done'},
                    after={'repair_order_id': child.id, 'repair_no': repair_no, 'state': 'draft'},
                    reason=reason)
        return {'order_id': order.id, 'repair_order_id': child.id,
                'repair_no': repair_no, 'state': 'draft', 'parent_state': order.state}

    def _bind_code(self, store, order_id, code):
        self._warehouse_write(store)
        order = self._get_order(order_id, store)
        code = self._text(code, 'External package code', 120)
        prior = self._model('order').search([('ydental_package_code', '=', code)], limit=1)
        if prior and prior != order:
            raise UserError(self.env._('code_conflict: This package code is already bound.'))
        if order.ydental_package_code and order.ydental_package_code != code:
            raise UserError(self.env._('version_conflict: A package code cannot be silently rebound.'))
        if order.ydental_package_code == code:
            return {'order_id': order.id, 'code_bound': True}
        before = order.state
        try:
            # Under REPEATABLE READ a concurrent transaction can hold an older
            # snapshot after waiting for the service lock. The unique index is
            # the final arbiter; translate only its package-code collision to
            # the same non-disclosing business conflict as the pre-check.
            with self.env.cr.savepoint():
                order._save({'ydental_package_code': code})
        except UniqueViolation as error:
            if error.diag.constraint_name != 'ydental_lab_order_package_code_unique':
                raise
            raise UserError(self.env._('code_conflict: This package code is already bound.')) from error
        self._event(order, 'code_bound', before, order.state, 'Package identification only; no access authorization')
        self._audit('code_bound', order, store, after={'code_bound': True})
        return {'order_id': order.id, 'code_bound': True}

    def _resolve_package_code(self, store, code):
        code = self._text(code, 'External package code', 120)
        order = self._model('order').search([
            ('ydental_store_id', '=', store.id), ('ydental_package_code', '=', code),
        ], limit=1)
        if not order:
            raise UserError(self.env._('code_unavailable: No accessible laboratory order matches this code.'))
        accessible = self.env['ydental.lab.order'].browse(order.id)
        try:
            accessible.check_access('read')
        except AccessError as error:
            raise UserError(self.env._('code_unavailable: No accessible laboratory order matches this code.')) from error
        if accessible.ydental_store_id != store:
            raise UserError(self.env._('code_unavailable: No accessible laboratory order matches this code.'))
        return accessible

    def _scan_package_code(self, code):
        store = self._access(write=True)
        self._warehouse_write(store)
        order = self._resolve_package_code(store, code)
        # Scanning only resolves the exact authorized work order. The visible
        # receive and put-away actions then record two separate business facts.
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Authorized laboratory work order'),
            'res_model': 'ydental.lab.order',
            'view_mode': 'form',
            'res_id': order.id,
            'target': 'current',
        }

    def _authorize_inventory_source(self, source):
        if not isinstance(source, LabStockSource) or source.actor_id != self.env.uid or source.operation not in ('supplier_return', 'discard'):
            raise AccessError(self.env._('access_denied: A trusted laboratory stock source is required.'))
        store = self._access(write=True)
        order = self._get_order(source.order_id, store)
        if source.store_id != store.id or order.state != 'available' or not order.ydental_inventory_event_id:
            raise AccessError(self.env._('access_denied: Only an available laboratory item can move to a recorded disposition.'))
        self.env['ydental.access.service']._check('warehouse', 'write', write=True)
        return order
