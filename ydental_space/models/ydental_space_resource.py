import base64
import binascii

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

from .svg import sanitize_svg


class YDentalSpaceResource(models.Model):
    _name = 'ydental.space.resource'
    _description = 'Controlled common or store-private space artwork'
    _inherit = 'ydental.space.version'

    ydental_store_id = fields.Many2one('ydental.access.store', ondelete='restrict', index=True,
                                     help='Empty means group-maintained common artwork.', string='Store')
    ydental_kind = fields.Selection([
        ('chair', 'Dental chair'), ('imaging', 'Imaging device'), ('pharmacy', 'Pharmacy desk'),
        ('settlement', 'Settlement desk'), ('door', 'Door'), ('wall', 'Wall'), ('waiting', 'Waiting sign'),
    ], required=True, string='Workstation or artwork type')
    ydental_category = fields.Selection([('space', 'Space')], default='space', readonly=True, required=True, string='Business category')
    ydental_capability_ids = fields.Many2many('ydental.access.capability', string='Capabilities')
    ydental_svg = fields.Text(required=True, string='Safe SVG source')
    ydental_upload = fields.Binary(string='Upload SVG', attachment=False, store=False,
                                   compute='_compute_upload', readonly=False,
                                   help='Only the sanitized SVG is retained, never the original upload.')

    def _compute_upload(self):
        for resource in self:
            resource.ydental_upload = False

    def _space_floors(self):
        # Fixed-model reverse references include archived placements.
        return self.env['ydental.space.item'].sudo().with_context(active_test=False).search([
            ('ydental_resource_id', 'in', self.ids),
        ]).ydental_floor_id

    def _check_space_change(self, values):
        super()._check_space_change(values)
        self.env['ydental.space.item'].sudo().with_context(active_test=False).search([
            ('ydental_resource_id', 'in', self.ids),
        ]).ydental_station_id._check_space_change({'resource_definition': values})

    def _resource_domain(self, operation):
        service = self.env['ydental.access.service']
        session = service._scope(write=operation != 'read')
        try:
            service._check('space', 'read' if operation == 'read' else 'write', write=operation != 'read')
        except AccessError:
            return fields.Domain.FALSE
        domain = fields.Domain('ydental_store_id', '=', session.ydental_store_id.id)
        if operation == 'read' or service._is_group_manager():
            domain |= fields.Domain('ydental_store_id', '=', False)
        return domain if operation != 'unlink' else fields.Domain.FALSE

    def _access_domain(self, operation):
        domain = super()._access_domain(operation)
        return domain if self.env.su else domain & self._resource_domain(operation)

    def check_access(self, operation):
        if not self.env.su:
            domain = self._resource_domain(operation)
            if domain.is_false() or self and self.sudo().filtered_domain(domain).ids != self.ids:
                raise AccessError(self.env._('access_denied: Artwork is outside the authorized space scope.'))
        return super().check_access(operation)

    def _prepare_svg(self, values):
        values = dict(values)
        uploaded = values.pop('ydental_upload', None)
        if isinstance(uploaded, dict):
            if not set(uploaded) <= {'filename', 'content'} or 'content' not in uploaded:
                raise ValidationError(self.env._('Invalid SVG upload payload.'))
            uploaded = uploaded['content']
        if uploaded or 'ydental_svg' in values:
            setting = self.env['ir.config_parameter'].sudo().get_str('ydental_space.svg_max_bytes', '1048576')
            try:
                limit = int(setting)
                if not 1024 <= limit <= 4194304:
                    raise ValueError('configuration')
                if uploaded:
                    if not isinstance(uploaded, (str, bytes)) or len(uploaded) > 4 * ((limit + 2) // 3):
                        raise ValueError('size')
                    values['ydental_svg'] = base64.b64decode(uploaded, validate=True).decode('utf-8')
                values['ydental_svg'] = sanitize_svg(values['ydental_svg'], limit)
            except (ValueError, binascii.Error) as error:
                raise ValidationError(self.env._('Unsafe SVG: use bounded basic shapes with a viewBox and finite dimensions.')) from error
        return values

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            service = self.env['ydental.access.service']
            service._check('space', 'write', write=True)
            store_id = service._scope().ydental_store_id.id
            for values in vals_list:
                if values.get('ydental_store_id') not in (False, None, store_id) or (
                    not values.get('ydental_store_id') and not service._is_group_manager()
                ):
                    raise AccessError(self.env._('access_denied: Common artwork requires group administration.'))
        records = super().create([self._prepare_svg(values) for values in vals_list])
        records._resource_audit('space.resource.create')
        return records

    def write(self, vals):
        self.check_access('write')
        result = super().write(self._prepare_svg(vals))
        self._resource_audit('space.resource.modify')
        return result

    def _resource_audit(self, event):
        if not self.env.su:
            service = self.env['ydental.access.service']
            for resource in self:
                service._audit(event, 'space', resource, resource.ydental_store_id.id,
                               after={'version': resource.ydental_version,
                                      'capability_ids': resource.ydental_capability_ids.ids}, source='resource_model')

    def export_data(self, fields_to_export):
        self.env['ydental.access.service']._check('export', 'write')
        self.check_access('read')
        result = super().export_data(fields_to_export)
        self._resource_audit('space.resource.export')
        return result
