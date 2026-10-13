from odoo import models
from odoo.addons.ydental_patient.models.res_partner import _PARTNER_MUTATION


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def write(self, vals):
        # Odoo accounting increases these native classification counters when
        # posting a patient invoice.  Reuse the existing patient mutation token
        # only for that exact server-side update; all identity fields remain
        # behind the original patient service guard.
        if self.env.su and vals and set(vals) <= {'customer_rank', 'supplier_rank'}:
            return super(ResPartner, self.with_context(
                ydental_patient_partner_mutation=_PARTNER_MUTATION)).write(vals)
        return super().write(vals)
