from odoo import api, fields, models
from odoo.exceptions import AccessError

from .ydental_lab_record import MUTATION


class YDentalLabCooperation(models.Model):
    _name = 'ydental.lab.cooperation'
    _description = 'Store cooperation with a qualified dental laboratory'
    _inherit = 'ydental.lab.record'

    ydental_vendor_id = fields.Many2one('ydental.lab.vendor', required=True, ondelete='restrict', index=True)
    active = fields.Boolean(default=True)
    local_reference = fields.Char()
    responsible_id = fields.Many2one('res.users', required=True, ondelete='restrict')

    _store_vendor_unique = models.Constraint(
        'UNIQUE(ydental_store_id, ydental_vendor_id)', 'A store has one cooperation record per laboratory.')

    def _source_domain(self, operation):
        service = self.env['ydental.access.service']
        store = service._scope(write=operation != 'read').ydental_store_id
        service._check('warehouse', 'write' if operation != 'read' else 'read', write=operation != 'read')
        return super()._source_domain(operation) & fields.Domain('ydental_store_id', '=', store.id)

    @api.model_create_multi
    def create(self, vals_list):
        access = self.env['ydental.access.service']
        store = access._check('warehouse', 'write', write=True).ydental_store_id
        prepared = []
        for incoming in vals_list:
            vals = dict(incoming)
            vendor = self.env['ydental.lab.vendor'].sudo().browse(vals.get('ydental_vendor_id', 0)).exists()
            if not vendor or store.company_id not in vendor.company_ids:
                raise AccessError(self.env._('access_denied: Select a vendor in the current company scope.'))
            vals.update({'ydental_store_id': store.id, 'ydental_category': 'warehouse',
                         'responsible_id': self.env.uid,
                         'name': vendor.partner_id.display_name})
            prepared.append(vals)
        records = super(YDentalLabCooperation, self.with_context(ydental_lab_mutation=MUTATION)).create(prepared)
        lab = self.env['ydental.lab.service']
        for cooperation in records:
            self.env['ydental.access.service']._audit(
                'lab.cooperation.enable', 'warehouse', cooperation, store.id,
                after={'vendor_id': cooperation.ydental_vendor_id.id, 'active': cooperation.active},
                source='dental_laboratory')
            lab._queue_vendor_expiry(cooperation.ydental_vendor_id)
        return records

    def write(self, vals):
        if self.env.context.get('ydental_lab_mutation') is not MUTATION:
            raise AccessError(self.env._('access_denied: Use the store laboratory cooperation action.'))
        return super().write(vals)

    def action_toggle(self):
        self.ensure_one()
        store = self.env['ydental.access.service']._check('warehouse', 'write', write=True).ydental_store_id
        if self.ydental_store_id != store:
            raise AccessError(self.env._('access_denied: Cooperation is outside the selected store.'))
        if not self.env['ydental.access.service']._is_group_manager() and not self.env['ydental.access.service']._levels(
                self.env['ydental.access.service']._membership(self.env.uid, store.id))['warehouse'] == 'write':
            raise AccessError(self.env._('access_denied: Store warehouse authority is required.'))
        before = self.active
        self.sudo()._save({'active': not before})
        self.env['ydental.access.service']._audit(
            'lab.cooperation.toggle', 'warehouse', self, store.id,
            before={'active': before}, after={'active': not before}, source='dental_laboratory')
        if not before:
            self.env['ydental.lab.service']._queue_vendor_expiry(self.ydental_vendor_id)
        return True
