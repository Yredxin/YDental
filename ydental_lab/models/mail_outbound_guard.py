from odoo import models
from odoo.exceptions import AccessError


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def _check_vendor_outbound(self):
        if any(wizard.model == 'ydental.lab.vendor' for wizard in self):
            raise AccessError(self.env._('access_denied: External messages are disabled for laboratory vendors.'))
        if any(wizard.model == 'ydental.lab.order' for wizard in self):
            raise AccessError(self.env._('access_denied: External messages are disabled for laboratory orders.'))

    def _action_send_mail(self, auto_commit=False):
        self._check_vendor_outbound()
        return super()._action_send_mail(auto_commit=auto_commit)

    def _action_schedule_message(self):
        self._check_vendor_outbound()
        return super()._action_schedule_message()


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    def _check_vendor_outbound(self):
        if any(template.model == 'ydental.lab.vendor' for template in self):
            raise AccessError(self.env._('access_denied: External messages are disabled for laboratory vendors.'))
        if any(template.model == 'ydental.lab.order' for template in self):
            raise AccessError(self.env._('access_denied: External messages are disabled for laboratory orders.'))

    def send_mail(self, *args, **kwargs):
        self._check_vendor_outbound()
        return super().send_mail(*args, **kwargs)

    def send_mail_batch(self, *args, **kwargs):
        self._check_vendor_outbound()
        return super().send_mail_batch(*args, **kwargs)
