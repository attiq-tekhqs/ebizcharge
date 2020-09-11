from odoo import fields, models,api


class CustomMessageWizard(models.TransientModel):
    _name = 'message.wizard'

    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False

    message = fields.Text(readonly=True, default=get_default)





