from odoo import models
from odoo.exceptions import AccessError


class SmsComposer(models.TransientModel):
    _inherit = 'sms.composer'

    def _check_vendor_sms(self):
        if any(composer.res_model == 'ydental.lab.vendor' for composer in self):
            raise AccessError(self.env._('access_denied: SMS is disabled for laboratory vendor records.'))
        if any(composer.res_model == 'ydental.lab.order' for composer in self):
            raise AccessError(self.env._('access_denied: SMS is disabled for laboratory order records.'))

    def action_schedule_message(self):
        self._check_vendor_sms()
        return super().action_schedule_message()

    def _action_schedule_message(self):
        self._check_vendor_sms()
        return super()._action_schedule_message()

    def action_send_sms(self):
        self._check_vendor_sms()
        return super().action_send_sms()

    def action_send_sms_mass_now(self):
        self._check_vendor_sms()
        return super().action_send_sms_mass_now()

    def _action_send_sms(self):
        self._check_vendor_sms()
        return super()._action_send_sms()
