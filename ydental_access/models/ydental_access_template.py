from odoo import api, fields, models


class YDentalAccessTemplate(models.Model):
    _name = 'ydental.access.template'
    _description = 'YDental authorization template'

    name = fields.Char(required=True)
    ydental_levels = fields.Json(required=True, default=dict)
    active = fields.Boolean(default=True)

    @api.constrains('ydental_levels')
    def _check_levels(self):
        for template in self:
            self.env['ydental.access.service']._validate_levels(template.ydental_levels)

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        self.env['ydental.access.audit'].sudo().create([
            self.env['ydental.access.service']._audit_values(
                'template.create', 'personnel', template, after={'levels': template.ydental_levels},
            ) for template in templates
        ])
        return templates

    def write(self, vals):
        before = {template.id: template.ydental_levels for template in self}
        result = super().write(vals)
        self.env['ydental.access.audit'].sudo().create([
            self.env['ydental.access.service']._audit_values(
                'template.modify', 'personnel', template, before={'levels': before[template.id]},
                after={'levels': template.ydental_levels, 'fields': sorted(vals)},
            ) for template in self
        ])
        return result

