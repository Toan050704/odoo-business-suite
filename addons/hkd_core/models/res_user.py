from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    is_hkd_owner = fields.Boolean(
        string='Là chủ HKD',
        compute='_compute_is_hkd_owner',
    )

    def _compute_is_hkd_owner(self):
        group = self.env.ref('hkd_core.group_hkd_owner')
        for user in self:
            user.is_hkd_owner = group in user.groups_id