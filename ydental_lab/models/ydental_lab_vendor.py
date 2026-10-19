from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .ydental_lab_record import MUTATION


class YDentalLabVendor(models.Model):
    _name = 'ydental.lab.vendor'
    _description = 'Qualified external dental laboratory'
    _rec_name = 'name'
    _order = 'name'

    partner_id = fields.Many2one('res.partner', required=True, ondelete='restrict', index=True)
    name = fields.Char(related='partner_id.name', store=True, readonly=True)
    company_ids = fields.Many2many('res.company', required=True, string='Authorized companies')
    category = fields.Selection([
        ('crown', 'Crown or bridge'),
        ('denture', 'Removable prosthesis'),
        ('implant', 'Implant prosthesis'),
        ('orthodontic', 'Orthodontic appliance'),
        ('other', 'Other'),
    ], required=True)
    qualification_reference = fields.Char(required=True)
    qualification_evidence = fields.Binary(attachment=True, groups='ydental_access.ydental_group_manager',
                                           string='Qualification evidence')
    qualification_evidence_name = fields.Char(groups='ydental_access.ydental_group_manager')
    valid_until = fields.Date(required=True)
    state = fields.Selection([
        ('draft', 'Not reviewed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], required=True, default='draft', readonly=True)
    qualification_version = fields.Integer(default=1, required=True, readonly=True)
    reviewed_by_id = fields.Many2one('res.users', readonly=True, ondelete='restrict')
    reviewed_at = fields.Datetime(readonly=True)
    review_reason = fields.Char()

    _partner_category_unique = models.Constraint(
        'UNIQUE(partner_id, category)', 'A vendor has one qualification record per service category.')

    @api.model_create_multi
    def create(self, vals_list):
        access = self.env['ydental.access.service']
        access._require_internal()
        if not access._is_group_manager():
            raise AccessError(self.env._('access_denied: Group governance authority is required.'))
        for vals in vals_list:
            partner = self.env['res.partner'].sudo().browse(vals.get('partner_id', 0)).exists()
            if not partner or partner.ydental_patient_owner_id:
                raise AccessError(self.env._('access_denied: Select an external laboratory partner, not a patient contact.'))
            company_ids = vals.get('company_ids', [fields.Command.set(self.env.user.company_ids.ids)])
            if 'qualification_version' in vals:
                raise AccessError(self.env._('access_denied: Qualification version is assigned by the workflow.'))
            if (not isinstance(company_ids, list) or len(company_ids) != 1 or
                    not isinstance(company_ids[0], (tuple, list)) or len(company_ids[0]) != 3 or
                    company_ids[0][0] != fields.Command.SET or not isinstance(company_ids[0][2], list)):
                raise ValidationError(self.env._('Company scope must be an explicit authorized company set.'))
            ids = company_ids[0][2]
            if not ids or not set(ids) <= set(self.env.user.sudo().company_ids.ids):
                raise AccessError(self.env._('access_denied: Vendor qualification is outside allowed companies.'))
            vals.setdefault('company_ids', company_ids)
            if vals.get('state') not in (None, False, 'draft'):
                raise ValidationError(self.env._('Qualification must be reviewed through its action.'))
            vals['state'] = 'draft'
        records = super().create(vals_list)
        for vendor in records:
            access._audit('lab.vendor.create', 'personnel', vendor,
                          after={'state': 'draft', 'category': vendor.category}, source='dental_laboratory')
        return records

    def write(self, vals):
        if self.env.context.get('ydental_lab_mutation') is MUTATION:
            return super().write(vals)
        if {'state', 'reviewed_by_id', 'reviewed_at'} & vals.keys():
            raise AccessError(self.env._('access_denied: Use the qualification review action.'))
        if 'qualification_version' in vals:
            raise AccessError(self.env._('access_denied: Qualification version is controlled by the workflow.'))
        access = self.env['ydental.access.service']
        if not access._is_group_manager():
            raise AccessError(self.env._('access_denied: Group governance authority is required.'))
        self.check_access('write')
        if 'company_ids' in vals:
            commands = vals['company_ids']
            if (not isinstance(commands, list) or len(commands) != 1 or
                    not isinstance(commands[0], (tuple, list)) or len(commands[0]) != 3 or
                    commands[0][0] != fields.Command.SET or not isinstance(commands[0][2], list)):
                raise ValidationError(self.env._('Company scope changes must replace the full authorized company set.'))
            ids = commands[0][2]
            if not ids or not set(ids) <= set(self.env.user.sudo().company_ids.ids):
                raise AccessError(self.env._('access_denied: Vendor qualification is outside allowed companies.'))
        qualification_fields = {'partner_id', 'company_ids', 'category', 'qualification_reference',
                                'qualification_evidence', 'qualification_evidence_name', 'valid_until'}
        updated = dict(vals)
        if qualification_fields & vals.keys():
            if 'partner_id' in vals:
                partner = self.env['res.partner'].sudo().browse(vals['partner_id']).exists()
                if not partner or partner.ydental_patient_owner_id:
                    raise AccessError(self.env._('access_denied: Select an external laboratory partner, not a patient contact.'))
            updated.update({
                'state': 'draft', 'reviewed_by_id': False, 'reviewed_at': False, 'review_reason': False,
                'qualification_version': max(vendor.qualification_version for vendor in self) + 1,
            })
        result = self.with_context(ydental_lab_mutation=MUTATION).write(updated)
        for vendor in self:
            access._audit('lab.vendor.modify', 'personnel', vendor,
                          after={'fields': sorted(updated), 'state': vendor.state}, source='dental_laboratory')
            self.env['ydental.lab.service']._queue_vendor_expiry(vendor)
        return result

    def unlink(self):
        raise AccessError(self.env._('history_immutable: Vendor qualification history cannot be deleted.'))

    def action_approve(self):
        self.ensure_one()
        self.env['ydental.lab.service']._review_vendor(self, 'approved', self.review_reason or 'Qualification reviewed')
        return True

    def action_reject(self):
        self.ensure_one()
        self.env['ydental.lab.service']._review_vendor(self, 'rejected', self.review_reason or 'Qualification rejected')
        return True
