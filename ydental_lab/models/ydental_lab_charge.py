import uuid

from odoo import api, fields, models
from odoo.exceptions import AccessError


_MUTATION = object()


class YDentalLabCharge(models.Model):
    _name = 'ydental.lab.charge'
    _description = 'Immutable additional-service charge bound to one laboratory cycle'
    _inherit = 'ydental.access.source'
    _order = 'id desc'

    def _source_domain(self, operation):
        domain = super()._source_domain(operation)
        if operation != 'read' or self.env.su or domain.is_false():
            return domain
        # The row contains patient/order identity and the frozen charge. Both
        # medical and price read authority are required; medical-only and
        # price-only users must not enumerate the combined patient/fee source.
        access = self.env['ydental.access.service']
        session = access._scope()
        member = access._membership(self.env.uid, session.ydental_store_id.id)
        if not member or access._levels(member).get('price') not in ('read', 'write'):
            return fields.Domain.FALSE
        return domain

    name = fields.Char(required=True, readonly=True)
    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_order_id = fields.Many2one('ydental.lab.order', required=True, readonly=True, ondelete='restrict', index=True)
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, readonly=True, ondelete='restrict', index=True)
    ydental_catalog_id = fields.Many2one('ydental.intake.catalog', required=True, readonly=True, ondelete='restrict')
    ydental_price_id = fields.Many2one('ydental.intake.price', required=True, readonly=True, ondelete='restrict')
    ydental_price_snapshot_id = fields.Many2one('ydental.intake.snapshot', required=True, readonly=True, ondelete='restrict')
    ydental_quantity = fields.Float(required=True, readonly=True, digits='Product Unit')
    ydental_uom_id = fields.Many2one('uom.uom', required=True, readonly=True, ondelete='restrict')
    ydental_currency_id = fields.Many2one('res.currency', required=True, readonly=True, ondelete='restrict')
    ydental_unit_price = fields.Monetary(required=True, readonly=True, currency_field='ydental_currency_id')
    ydental_amount = fields.Monetary(required=True, readonly=True, currency_field='ydental_currency_id')
    ydental_quoted_at = fields.Datetime(required=True, readonly=True)
    ydental_terms_confirmed_by_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')
    ydental_terms_confirmed_at = fields.Datetime(required=True, readonly=True)
    ydental_confirmation_reference = fields.Char(required=True, readonly=True)
    ydental_reason = fields.Char(required=True, readonly=True)
    ydental_request_key = fields.Char(required=True, readonly=True, index=True)
    ydental_fingerprint = fields.Char(required=True, readonly=True)
    state = fields.Selection([
        ('terms_confirmed', 'Additional terms confirmed'),
        ('performed', 'Actual additional service performed'),
        ('billed', 'Linked to native settlement source'),
    ], required=True, readonly=True, default='terms_confirmed', index=True)
    ydental_performance_evidence_reference = fields.Char(readonly=True)
    ydental_settlement_source_id = fields.Many2one(
        'ydental.settlement.source', readonly=True, ondelete='restrict', index=True)
    ydental_invoice_id = fields.Many2one(
        related='ydental_settlement_source_id.ydental_invoice_id', readonly=True, related_sudo=False)
    ydental_invoice_line_id = fields.Many2one(
        related='ydental_settlement_source_id.ydental_line_id', readonly=True, related_sudo=False)
    ydental_performed_by_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    ydental_performed_at = fields.Datetime(readonly=True)
    ydental_adjustment_ids = fields.One2many(
        'ydental.lab.charge.adjustment', 'ydental_charge_id', readonly=True)

    _cycle_catalog_once = models.Constraint(
        'UNIQUE(ydental_order_id, ydental_catalog_id)',
        'An additional service can be confirmed only once per laboratory cycle and catalog item.')
    _request_once = models.Constraint(
        'UNIQUE(ydental_store_id, ydental_request_key)',
        'An additional-service confirmation key can be used only once per store.')
    _snapshot_once = models.Constraint(
        'UNIQUE(ydental_price_snapshot_id)',
        'A published-price snapshot belongs to one additional-service source.')
    _settlement_once = models.Constraint(
        'UNIQUE(ydental_settlement_source_id)',
        'A native settlement source belongs to one laboratory charge.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_lab_charge_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the cycle charge service.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_lab_charge_mutation') is not _MUTATION:
            raise AccessError(self.env._('history_immutable: Additional-service charge facts are immutable.'))
        allowed = {'state', 'ydental_performed_by_id', 'ydental_performed_at',
                   'ydental_performance_evidence_reference', 'ydental_settlement_source_id'}
        if set(vals) - allowed:
            raise AccessError(self.env._('history_immutable: Confirmed charge terms and price cannot be replaced.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Additional-service charge history cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_lab_charge_mutation=_MUTATION).create(values)

    def _save(self, values):
        for record in self:
            record.sudo().with_context(ydental_lab_charge_mutation=_MUTATION).write(values)

    def action_bill(self):
        self.ensure_one()
        result = self.env['ydental.settlement.service']._operate(
            'bill_lab_charge', {'charge_ids': [self.id], 'reason': self.ydental_reason},
            'lab-charge-bill-%s-v1' % self.id)
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move',
                'res_id': result['invoice_id'], 'view_mode': 'form',
                'views': [(False, 'form')], 'target': 'current'}

    def action_open_credit_wizard(self):
        self.ensure_one()
        if self.state != 'billed':
            raise AccessError(self.env._('access_denied: Only a billed cycle charge can be corrected.'))
        return {'type': 'ir.actions.act_window', 'res_model': 'ydental.lab.charge.credit.wizard',
                'view_mode': 'form', 'views': [(False, 'form')], 'target': 'new',
                'context': {'default_ydental_charge_id': self.id}}


class YDentalSettlementSource(models.Model):
    _inherit = 'ydental.settlement.source'

    ydental_fee_id = fields.Many2one(
        'ydental.treatment.fee', required=False, ondelete='restrict', index=True)

    ydental_lab_charge_id = fields.Many2one(
        'ydental.lab.charge', readonly=True, ondelete='restrict', index=True)
    ydental_lab_charge_adjustment_id = fields.Many2one(
        'ydental.lab.charge.adjustment', readonly=True, ondelete='restrict', index=True)

    _one_source_kind = models.Constraint(
        'CHECK((ydental_fee_id IS NOT NULL)::integer + (ydental_lab_charge_id IS NOT NULL)::integer + '
        '(ydental_lab_charge_adjustment_id IS NOT NULL)::integer = 1)',
        'A settlement source must identify exactly one native fee, laboratory charge or charge adjustment.')

    _lab_charge_once = models.Constraint(
        'UNIQUE(ydental_lab_charge_id)',
        'A laboratory charge can be billed only once.')

    _lab_charge_adjustment_once = models.Constraint(
        'UNIQUE(ydental_lab_charge_adjustment_id)',
        'A laboratory charge adjustment has one immutable native credit source.')


class YDentalLabChargeAdjustment(models.Model):
    _name = 'ydental.lab.charge.adjustment'
    _description = 'Immutable cycle-bound laboratory charge correction'
    _inherit = 'ydental.access.source'
    _order = 'ydental_revision desc, id desc'

    name = fields.Char(required=True, readonly=True)
    ydental_category = fields.Selection(default='medical', readonly=True)
    ydental_charge_id = fields.Many2one('ydental.lab.charge', required=True, readonly=True, ondelete='restrict', index=True)
    ydental_revision = fields.Integer(required=True, readonly=True)
    ydental_store_id = fields.Many2one('ydental.access.store', required=True, readonly=True, ondelete='restrict')
    ydental_patient_id = fields.Many2one('ydental.patient', required=True, readonly=True, ondelete='restrict')
    ydental_currency_id = fields.Many2one('res.currency', required=True, readonly=True, ondelete='restrict')
    ydental_amount = fields.Monetary(required=True, readonly=True, currency_field='ydental_currency_id')
    ydental_reason = fields.Char(required=True, readonly=True)
    ydental_request_key = fields.Char(required=True, readonly=True, index=True)
    ydental_fingerprint = fields.Char(required=True, readonly=True)
    ydental_actor_id = fields.Many2one('res.users', required=True, readonly=True, ondelete='restrict')
    ydental_created_at = fields.Datetime(required=True, readonly=True)
    ydental_credit_move_id = fields.Many2one('account.move', required=True, readonly=True, ondelete='restrict')
    ydental_credit_line_id = fields.Many2one('account.move.line', required=True, readonly=True, ondelete='restrict')
    ydental_settlement_source_id = fields.Many2one('ydental.settlement.source', readonly=True, ondelete='restrict')

    _revision_once = models.Constraint(
        'UNIQUE(ydental_charge_id, ydental_revision)',
        'A cycle charge adjustment revision is unique.')
    _request_once = models.Constraint(
        'UNIQUE(ydental_store_id, ydental_request_key)',
        'A charge adjustment request key can be used once per store.')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('ydental_lab_charge_adjustment_mutation') is not _MUTATION:
            raise AccessError(self.env._('access_denied: Use the native settlement credit action.'))
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('ydental_lab_charge_adjustment_mutation') is not _MUTATION:
            raise AccessError(self.env._('history_immutable: Charge adjustment facts cannot be changed.'))
        if set(vals) != {'ydental_settlement_source_id'} or any(row.ydental_settlement_source_id for row in self):
            raise AccessError(self.env._('history_immutable: Charge adjustment facts are append-only.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Charge adjustment facts cannot be deleted.'))

    @api.model
    def _new(self, values):
        return self.sudo().with_context(ydental_lab_charge_adjustment_mutation=_MUTATION).create(values)

    def _link_source(self, source):
        self.ensure_one()
        if (not source or source._name != 'ydental.settlement.source' or len(source) != 1 or
                source.ydental_lab_charge_adjustment_id != self or
                source.ydental_store_id != self.ydental_store_id or
                source.ydental_patient_id != self.ydental_patient_id or
                source.ydental_invoice_id != self.ydental_credit_move_id or
                source.ydental_line_id != self.ydental_credit_line_id):
            raise AccessError(self.env._('access_denied: Link an exact native settlement source.'))
        self.sudo().with_context(ydental_lab_charge_adjustment_mutation=_MUTATION).write(
            {'ydental_settlement_source_id': source.id})


class YDentalLabChargeCreditWizard(models.TransientModel):
    _name = 'ydental.lab.charge.credit.wizard'
    _description = 'Native credit for a billed cycle charge'

    ydental_charge_id = fields.Many2one('ydental.lab.charge', required=True, readonly=True)
    ydental_amount = fields.Monetary(required=True, currency_field='ydental_currency_id')
    ydental_currency_id = fields.Many2one(related='ydental_charge_id.ydental_currency_id', readonly=True)
    ydental_reason = fields.Char(required=True, size=240)
    ydental_request_key = fields.Char(required=True, readonly=True, default=lambda self: uuid.uuid4().hex)

    def action_apply(self):
        self.ensure_one()
        charge = self.ydental_charge_id
        result = self.env['ydental.settlement.service']._operate(
            'credit_lab_charge', {
                'charge_id': charge.id, 'amount': self.ydental_amount,
                'reason': self.ydental_reason, 'request_key': self.ydental_request_key,
            }, self.ydental_request_key)
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move',
                'res_id': result['credit_note_id'], 'view_mode': 'form',
                'views': [(False, 'form')], 'target': 'current'}
