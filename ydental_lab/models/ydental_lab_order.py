from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .ydental_lab_record import MUTATION


class YDentalLabOrder(models.Model):
    _name = 'ydental.lab.order'
    _description = 'Controlled external dental laboratory work order and cycle'
    _inherit = 'ydental.lab.record'
    _order = 'id desc'

    ydental_patient_id = fields.Many2one('ydental.patient', required=True, ondelete='restrict', index=True, readonly=True)
    ydental_source_event_id = fields.Many2one('ydental.treatment.event', required=True, ondelete='restrict', index=True, readonly=True)
    ydental_source_document_id = fields.Many2one('ydental.clinical.document', required=True, ondelete='restrict', readonly=True)
    ydental_source_fee_id = fields.Many2one('ydental.treatment.fee', ondelete='restrict', readonly=True)
    ydental_purchase_line_id = fields.Many2one('purchase.order.line', ondelete='restrict', string='Confirmed vendor processing cost', groups='purchase.group_purchase_user')
    ydental_vendor_id = fields.Many2one('ydental.lab.vendor', required=True, ondelete='restrict')
    ydental_cooperation_id = fields.Many2one(
        'ydental.lab.cooperation', ondelete='restrict', readonly=True, string='Cooperation authorized at dispatch')
    ydental_vendor_qualification_version = fields.Integer(
        readonly=True, string='Vendor qualification version at dispatch')
    ydental_vendor_qualification_valid_until = fields.Date(
        readonly=True, string='Qualification expiry date at dispatch')
    ydental_cooperation_active_at_dispatch = fields.Boolean(
        readonly=True, string='Cooperation active at dispatch')
    ydental_product_id = fields.Many2one('product.product', required=True, ondelete='restrict')
    ydental_lot_id = fields.Many2one('stock.lot', ondelete='restrict', string='Receiving lot')
    ydental_quantity = fields.Float(required=True, default=1.0, digits='Product Unit')
    ydental_teeth = fields.Json(required=True, default=list)
    ydental_material = fields.Char(required=True)
    ydental_shade = fields.Char()
    ydental_instructions = fields.Char(required=True)
    ydental_responsible_id = fields.Many2one('res.users', required=True, ondelete='restrict', default=lambda self: self.env.uid)
    ydental_planned_at = fields.Datetime(required=True, default=fields.Datetime.now)
    ydental_external_mode = fields.Selection([
        ('physical', 'Physical package'),
        ('digital', 'External digital platform'),
    ], required=True, default='physical')
    ydental_external_reference = fields.Char()
    ydental_external_url = fields.Char()
    ydental_external_actor = fields.Char(string='External platform operator')
    ydental_external_evidence = fields.Binary(attachment=True, string='External action screenshot')
    ydental_external_evidence_name = fields.Char(string='Screenshot filename')
    ydental_internal_code = fields.Char(required=True, index=True)
    ydental_package_code = fields.Char(index=True, readonly=True)
    ydental_parent_order_id = fields.Many2one('ydental.lab.order', ondelete='restrict', index=True, string='Rework of')
    ydental_repair_order_ids = fields.One2many(
        'ydental.lab.order', 'ydental_parent_order_id', string='Linked repair cycles', readonly=True)
    ydental_rework_no = fields.Integer(default=0, readonly=True)
    ydental_post_fit_repair = fields.Boolean(default=False, readonly=True)
    ydental_rework_kind = fields.Selection([
        ('free', 'No additional charge recorded'),
        ('additional', 'Additional commercial terms recorded separately'),
    ])
    ydental_additional_service_id = fields.Many2one(
        'ydental.intake.catalog', ondelete='restrict', string='Additional service')
    ydental_additional_service_quantity = fields.Float(
        digits='Product Unit', string='Additional service quantity')
    ydental_additional_consent_reference = fields.Char(string='Explicit terms confirmation reference')
    ydental_additional_terms_reason = fields.Char(string='Additional terms reason')
    ydental_additional_terms_frozen = fields.Boolean(readonly=True, default=False)
    ydental_additional_performed_at = fields.Datetime(string='Additional service performed at')
    ydental_additional_performance_evidence_reference = fields.Char(string='Additional service performance evidence reference')
    ydental_additional_performance_recorded = fields.Boolean(readonly=True, default=False)
    ydental_zero_supplier_cost_confirmed = fields.Boolean(readonly=True, default=False)
    ydental_zero_supplier_cost_reason = fields.Char(readonly=True)
    ydental_zero_supplier_cost_actor_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    ydental_zero_supplier_cost_at = fields.Datetime(readonly=True)
    ydental_zero_supplier_cost_confirmation_reason = fields.Char(string='Reason for no additional vendor cost')
    ydental_no_patient_fee_declaration = fields.Boolean(string='No patient fee will be charged')
    ydental_no_patient_fee_confirmation_reason = fields.Char(string='Reason no patient fee will be charged')
    ydental_no_patient_fee_confirmed = fields.Boolean(readonly=True, default=False)
    ydental_no_patient_fee_reason = fields.Char(readonly=True)
    ydental_no_patient_fee_actor_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    ydental_no_patient_fee_at = fields.Datetime(readonly=True)
    ydental_fit_event_id = fields.Many2one('ydental.treatment.event', ondelete='restrict')
    ydental_followup_id = fields.Many2one('ydental.followup', ondelete='restrict', readonly=True)
    ydental_receipt_at = fields.Datetime(readonly=True)
    ydental_receipt_actor_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    ydental_inventory_event_id = fields.Many2one('ydental.inventory.event', readonly=True, ondelete='restrict')
    ydental_fit_inventory_event_id = fields.Many2one('ydental.inventory.event', readonly=True, ondelete='restrict')
    ydental_event_ids = fields.One2many('ydental.lab.event', 'ydental_order_id', readonly=True)
    ydental_exception_disposition = fields.Selection([
        ('supplier_return', 'Physically returned to supplier'),
        ('discard', 'Physically written off'),
    ])
    ydental_exception_reason = fields.Char()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent to laboratory'),
        ('processing', 'Processing'),
        ('received', 'Physically received'),
        ('available', 'Put away and awaiting fit'),
        ('rework_returned', 'Returned for rework'),
        ('done', 'Actually fitted'),
        ('cancelled', 'Cancelled before receipt'),
        ('exception', 'Exception closed'),
    ], required=True, default='draft', readonly=True, index=True)

    _internal_code_unique = models.Constraint('UNIQUE(ydental_store_id, ydental_internal_code)', 'Internal work order code is unique per store.')
    _source_initial_unique = models.UniqueIndex("(ydental_source_event_id) WHERE ydental_parent_order_id IS NULL", 'One initial laboratory order is allowed per clinical source.')
    _repair_cycle_unique = models.Constraint('UNIQUE(ydental_parent_order_id, ydental_rework_no)', 'Each laboratory order has one child cycle number.')
    _package_code_unique = models.Constraint('UNIQUE(ydental_package_code)', 'An external package code can identify only one laboratory order.')
    _purchase_line_unique = models.Constraint('UNIQUE(ydental_purchase_line_id)', 'A vendor purchase line can fund only one laboratory cycle.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_lab_mutation') is MUTATION:
            return super().create(vals_list)
        service = self.env['ydental.lab.service']
        store = service._access(write=True)
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            if vals.get('state') not in (None, False, 'draft'):
                raise ValidationError(self.env._('A new laboratory order must start as a draft.'))
            vals.update(service._order_identity(vals.get('ydental_source_event_id'), vals, store))
            vals['ydental_store_id'] = store.id
            vals['ydental_category'] = 'medical'
            if vals.get('ydental_purchase_line_id'):
                if not self.env.user.has_group('purchase.group_purchase_user'):
                    raise AccessError(self.env._('access_denied: Purchase authority is required to link a vendor cost source.'))
                service._validate_purchase_line(
                    self.env['ydental.lab.order'].new(vals), self.env['purchase.order.line'].sudo().browse(vals['ydental_purchase_line_id']))
            vals['state'] = 'draft'
            prepared.append(vals)
        return super(YDentalLabOrder, self.with_context(ydental_lab_mutation=MUTATION)).create(prepared)

    def write(self, vals):
        if self.env.context.get('ydental_lab_mutation') is MUTATION:
            return super().write(vals)
        draft_fields = {
            'name', 'ydental_vendor_id', 'ydental_product_id', 'ydental_lot_id', 'ydental_quantity',
            'ydental_teeth', 'ydental_material', 'ydental_shade', 'ydental_instructions',
            'ydental_responsible_id', 'ydental_planned_at', 'ydental_external_mode',
            'ydental_external_reference', 'ydental_external_url', 'ydental_internal_code',
            'ydental_external_actor', 'ydental_external_evidence', 'ydental_external_evidence_name',
            'ydental_purchase_line_id', 'ydental_additional_service_id',
            'ydental_additional_service_quantity', 'ydental_additional_consent_reference',
            'ydental_additional_terms_reason',
            'ydental_zero_supplier_cost_confirmation_reason',
            'ydental_no_patient_fee_declaration', 'ydental_no_patient_fee_confirmation_reason',
        }
        stage_fields = {'ydental_lot_id', 'ydental_rework_kind', 'ydental_fit_event_id',
                        'ydental_exception_disposition', 'ydental_exception_reason',
                        'ydental_additional_performed_at', 'ydental_additional_performance_evidence_reference'}
        if not vals or set(vals) - (draft_fields | stage_fields) or not (
                set(vals) <= draft_fields or set(vals) <= stage_fields):
            raise AccessError(self.env._('access_denied: Only documented laboratory work fields can be edited.'))
        terms_fields = {
            'ydental_additional_service_id', 'ydental_additional_service_quantity',
            'ydental_additional_consent_reference', 'ydental_additional_terms_reason',
        }
        serialized_fields = terms_fields | {
            'ydental_purchase_line_id', 'ydental_zero_supplier_cost_confirmation_reason',
            'ydental_no_patient_fee_declaration', 'ydental_no_patient_fee_confirmation_reason',
        }
        if serialized_fields & vals.keys():
            # Approval and zero-cost attestation use this row lock too.
            # Serialize their source edits before validation so a competing
            # action cannot freeze a quote/cost fact against stale order data.
            self.env.cr.execute(
                'SELECT id FROM ydental_lab_order WHERE id = ANY(%s) ORDER BY id FOR UPDATE',
                [self.ids],
            )
            self.invalidate_recordset([
                'state', 'ydental_parent_order_id', 'ydental_rework_kind',
                'ydental_additional_terms_frozen', 'ydental_purchase_line_id',
                'ydental_zero_supplier_cost_confirmed', *terms_fields,
                'ydental_no_patient_fee_declaration', 'ydental_no_patient_fee_confirmed',
                'ydental_no_patient_fee_confirmation_reason',
            ])
        if set(vals) <= draft_fields and any(order.state != 'draft' for order in self):
            raise AccessError(self.env._('access_denied: Only draft order details can be edited.'))
        if set(vals) <= stage_fields and any(order.state not in ('draft', 'sent', 'processing', 'received', 'available') for order in self):
            raise AccessError(self.env._('access_denied: Completed laboratory history cannot be edited.'))
        stage_access = False
        if set(vals) <= stage_fields:
            service = self.env['ydental.lab.service']
            stage_access = service._access(write=True)
        for order in self:
            if set(vals) <= draft_fields:
                order._check_edit_authority(vals)
                service = self.env['ydental.lab.service']
                if {'ydental_additional_service_id', 'ydental_additional_service_quantity',
                        'ydental_additional_consent_reference', 'ydental_additional_terms_reason'} & vals.keys():
                    if not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional':
                        raise AccessError(self.env._('access_denied: Additional patient terms apply only to an additional-charge rework cycle.'))
                    if order.ydental_additional_terms_frozen:
                        raise AccessError(self.env._('history_immutable: Approved additional terms cannot be edited.'))
                    if (order.ydental_no_patient_fee_declaration or order.ydental_no_patient_fee_confirmed or
                            vals.get('ydental_no_patient_fee_declaration')):
                        raise AccessError(self.env._('version_conflict: Patient charge terms and no-patient-fee declaration are mutually exclusive.'))
                    if vals.get('ydental_additional_service_id'):
                        catalog = self.env['ydental.intake.catalog'].sudo().browse(
                            vals['ydental_additional_service_id']).exists()
                        if not catalog or not catalog.active:
                            raise ValidationError(self.env._('Select an active published service catalog entry.'))
                    if 'ydental_additional_service_quantity' in vals:
                        service._validate_positive_quantity(vals['ydental_additional_service_quantity'])
                    if vals.get('ydental_additional_consent_reference'):
                        service._text(vals['ydental_additional_consent_reference'], 'Explicit terms confirmation reference', 120)
                    if vals.get('ydental_additional_terms_reason'):
                        service._text(vals['ydental_additional_terms_reason'], 'Additional terms reason', 240)
                if 'ydental_zero_supplier_cost_confirmation_reason' in vals:
                    if not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional':
                        raise AccessError(self.env._('access_denied: Zero supplier-cost confirmation applies only to an additional rework cycle.'))
                    if order.ydental_zero_supplier_cost_confirmed:
                        raise AccessError(self.env._('history_immutable: Zero supplier-cost confirmation is already recorded.'))
                    service._text(vals['ydental_zero_supplier_cost_confirmation_reason'], 'Zero added supplier cost reason')
                if {'ydental_no_patient_fee_declaration', 'ydental_no_patient_fee_confirmation_reason'} & vals.keys():
                    if not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional':
                        raise AccessError(self.env._('access_denied: No-patient-fee confirmation applies only to an additional rework cycle.'))
                    if order.ydental_no_patient_fee_confirmed:
                        raise AccessError(self.env._('history_immutable: No-patient-fee confirmation is already recorded.'))
                    if order.ydental_additional_terms_frozen:
                        raise AccessError(self.env._('history_immutable: Frozen priced terms cannot be replaced by a no-patient-fee declaration.'))
                    price_store = self.env['ydental.access.service']._check(
                        'price', 'write', write=True).ydental_store_id
                    if price_store != order.ydental_store_id:
                        raise AccessError(self.env._('access_denied: No-patient-fee declaration requires commercial authority at this same store.'))
                    declared_no_fee = vals.get(
                        'ydental_no_patient_fee_declaration', order.ydental_no_patient_fee_declaration)
                    if declared_no_fee and (
                            vals.get('ydental_additional_service_id', order.ydental_additional_service_id.id) or
                            vals.get('ydental_additional_service_quantity', order.ydental_additional_service_quantity) or
                            vals.get('ydental_additional_consent_reference', order.ydental_additional_consent_reference) or
                            vals.get('ydental_additional_terms_reason', order.ydental_additional_terms_reason)):
                        raise AccessError(self.env._('version_conflict: Clear patient charge inputs before declaring no patient fee.'))
                    if ('ydental_no_patient_fee_declaration' in vals and
                            type(vals['ydental_no_patient_fee_declaration']) is not bool):
                        raise ValidationError(self.env._('Make an explicit yes/no declaration for patient fees.'))
                    if vals.get('ydental_no_patient_fee_confirmation_reason'):
                        service._text(vals['ydental_no_patient_fee_confirmation_reason'], 'No-patient-fee reason')
                if vals.get('ydental_purchase_line_id'):
                    if order.ydental_zero_supplier_cost_confirmed:
                        raise AccessError(self.env._('history_immutable: A confirmed zero supplier cost cannot be replaced by a purchase line.'))
                    if not self.env.user.has_group('purchase.group_purchase_user'):
                        raise AccessError(self.env._('access_denied: Purchase authority is required to link a vendor cost source.'))
                    service._validate_purchase_line(order, self.env['purchase.order.line'].sudo().browse(vals['ydental_purchase_line_id']))
            else:
                if order.ydental_store_id != stage_access:
                    raise AccessError(self.env._('access_denied: Laboratory stage data is outside the current store.'))
                self.env['ydental.access.service']._check('medical', 'write', write=True)
                if 'ydental_lot_id' in vals:
                    self.env['ydental.lab.service']._warehouse_write(stage_access)
                    if order.state not in ('draft', 'received'):
                        raise AccessError(self.env._('access_denied: Assign the receiving lot only before put-away.'))
                    store = self.env['ydental.lab.service']._access(write=True)
                    lot = self.env['ydental.inventory.service']._lot(vals['ydental_lot_id'], store) if vals['ydental_lot_id'] else False
                    if lot and lot.product_id != order.ydental_product_id:
                        raise ValidationError(self.env._('The receiving lot must match the ordered prosthesis product.'))
                if 'ydental_rework_kind' in vals:
                    selecting_available_rework = order.state == 'available'
                    selecting_post_fit_terms = bool(
                        order.state == 'draft' and order.ydental_parent_order_id and
                        order.ydental_post_fit_repair and not order.ydental_rework_kind)
                    if not (selecting_available_rework or selecting_post_fit_terms):
                        raise AccessError(self.env._('access_denied: Select repair terms only for an available item or an unclassified post-fit repair draft.'))
                    if vals['ydental_rework_kind'] not in ('free', 'additional'):
                        raise ValidationError(self.env._('Choose free or additional terms for this repair cycle.'))
                    self.env['ydental.lab.service']._warehouse_write(stage_access)
                if 'ydental_fit_event_id' in vals and order.state != 'available':
                    raise AccessError(self.env._('access_denied: Link the fitting event only for an available item.'))
                if 'ydental_fit_event_id' in vals and vals['ydental_fit_event_id']:
                    event = self.env['ydental.treatment.event'].sudo().browse(vals['ydental_fit_event_id']).exists()
                    if not event or event.state != 'confirmed' or event.ydental_kind != 'treatment' or (
                            event.ydental_store_id != stage_access or event.ydental_patient_id != order.ydental_patient_id or
                            event.ydental_execution_id.ydental_patient_id != order.ydental_patient_id):
                        raise AccessError(self.env._('access_denied: Fit event must be an actual confirmed treatment for this order patient and store.'))
                if 'ydental_exception_disposition' in vals and order.state != 'available':
                    raise AccessError(self.env._('access_denied: Select exception disposition only after put-away.'))
                if 'ydental_exception_reason' in vals:
                    allowed_states = ('draft', 'sent', 'processing', 'received', 'available')
                    if order.state not in allowed_states:
                        raise AccessError(self.env._('access_denied: Completed laboratory history cannot be edited.'))
                    self.env['ydental.lab.service']._text(vals['ydental_exception_reason'], 'Disposition or cancellation reason')
                if {'ydental_additional_performed_at', 'ydental_additional_performance_evidence_reference'} & vals.keys():
                    if (not order.ydental_parent_order_id or order.ydental_rework_kind != 'additional' or
                            not order.ydental_additional_terms_frozen or order.ydental_additional_performance_recorded or
                            order.state not in ('sent', 'processing', 'received', 'available')):
                        raise AccessError(self.env._('access_denied: Record additional service evidence only for an approved active rework cycle.'))
                    if vals.get('ydental_additional_performance_evidence_reference'):
                        self.env['ydental.lab.service']._text(
                            vals['ydental_additional_performance_evidence_reference'],
                            'Additional service performance evidence reference', 160)
                    if vals.get('ydental_additional_performed_at'):
                        performed_at = fields.Datetime.to_datetime(vals['ydental_additional_performed_at'])
                        if not performed_at or performed_at > self.env['ydental.lab.service']._now():
                            raise ValidationError(self.env._('Enter a valid actual service time that is not in the future.'))
        return super(YDentalLabOrder, self.with_context(ydental_lab_mutation=MUTATION)).write(vals)

    def _check_edit_authority(self, vals):
        service = self.env['ydental.lab.service']
        store = service._access(write=True)
        if self.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Order is outside the selected store.'))
        product = self.env['product.product'].sudo().browse(vals.get('ydental_product_id', self.ydental_product_id.id)).exists()
        if not product or product.ydental_inventory_kind != 'prosthesis' or product.company_id and product.company_id != store.company_id:
            raise ValidationError(self.env._('Select an active prosthesis product in the store company.'))
        vendor = self.env['ydental.lab.vendor'].sudo().browse(vals.get('ydental_vendor_id', self.ydental_vendor_id.id)).exists()
        service._check_vendor(vendor, store, product)
        if vals.get('ydental_lot_id'):
            lot = self.env['ydental.inventory.service']._lot(vals['ydental_lot_id'], store)
            if lot.product_id != product:
                raise ValidationError(self.env._('The receiving lot must match the ordered prosthesis product.'))
        for field_name, label, maximum in (('name', 'Work order name', 240), ('ydental_material', 'Material', 120),
                ('ydental_instructions', 'Clinical instructions', 1200), ('ydental_internal_code', 'Internal order code', 80),
                ('ydental_external_actor', 'External platform operator', 120), ('ydental_external_reference', 'External reference', 120)):
            if field_name in vals:
                service._text(vals[field_name], label, maximum)
        if 'ydental_quantity' in vals:
            service._validate_positive_quantity(vals['ydental_quantity'])
        if 'ydental_teeth' in vals:
            teeth = vals['ydental_teeth']
            if not isinstance(teeth, list) or not teeth or len(teeth) > 32 or any(
                    type(tooth) is not int or tooth not in range(11, 49) or tooth % 10 not in range(1, 9)
                    for tooth in teeth) or len(set(teeth)) != len(teeth):
                raise ValidationError(self.env._('Select distinct FDI teeth for this laboratory order.'))
        if 'ydental_external_url' in vals and vals['ydental_external_url']:
            service._external_link(vals['ydental_external_url'])
        if 'ydental_shade' in vals and vals['ydental_shade']:
            service._text(vals['ydental_shade'], 'Shade', 80)
        if 'ydental_responsible_id' in vals:
            self.env['ydental.followup.service']._responsible(vals['ydental_responsible_id'], store)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Laboratory work orders cannot be deleted.'))

    def action_send(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('send', {'order_id': self.id}, self.env['ydental.lab.service']._new_key())
        return True

    def action_start_processing(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('processing', {'order_id': self.id}, self.env['ydental.lab.service']._new_key())
        return True

    def action_receive(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('receive', {'order_id': self.id}, self.env['ydental.lab.service']._new_key())
        return True

    def action_putaway(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('putaway', {'order_id': self.id}, self.env['ydental.lab.service']._new_key())
        return True

    def action_rework(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('rework', {'order_id': self.id}, self.env['ydental.lab.service']._new_key())
        return True

    def action_open_post_fit_repair_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Open linked post-fit repair'),
            'res_model': 'ydental.lab.post.fit.repair',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }

    def action_cancel(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('cancel', {'order_id': self.id, 'reason': self.ydental_exception_reason}, self.env['ydental.lab.service']._new_key())
        return True

    def action_close_exception(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('exception', {
            'order_id': self.id, 'disposition': self.ydental_exception_disposition,
            'reason': self.ydental_exception_reason,
        }, self.env['ydental.lab.service']._new_key())
        return True

    def action_fit(self):
        self.ensure_one()
        self.env['ydental.lab.service']._operate('fit', {
            'order_id': self.id, 'fit_event_id': self.ydental_fit_event_id.id,
        }, self.env['ydental.lab.service']._new_key())
        return True

    def action_approve_additional_terms(self):
        self.ensure_one()
        key = 'lab-charge-terms-%s-v1' % self.id
        self.env['ydental.lab.service']._operate(
            'approve_charge_terms', {'order_id': self.id}, key)
        return True

    def action_confirm_additional_service_performed(self):
        self.ensure_one()
        key = 'lab-charge-performed-%s-v1' % self.id
        self.env['ydental.lab.service']._operate(
            'confirm_charge_performed', {'order_id': self.id}, key)
        return True

    def action_confirm_zero_supplier_cost(self):
        self.ensure_one()
        key = 'lab-zero-supplier-cost-%s-v1' % self.id
        self.env['ydental.lab.service']._operate('confirm_zero_supplier_cost', {
            'order_id': self.id, 'reason': self.ydental_zero_supplier_cost_confirmation_reason,
        }, key)
        return True

    def action_confirm_no_patient_fee(self):
        self.ensure_one()
        key = 'lab-no-patient-fee-%s-v1' % self.id
        self.env['ydental.lab.service']._operate('confirm_no_patient_fee', {
            'order_id': self.id,
        }, key)
        return True

    def action_bind_package_code(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Bind external package code'),
            'res_model': 'ydental.lab.code.bind',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id},
        }
