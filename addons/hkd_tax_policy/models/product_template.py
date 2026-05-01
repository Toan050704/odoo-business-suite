from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hkd_policy_id = fields.Many2one(
        'hkd.tax.policy',
        string='Tax Policy',
    )
    hkd_tax_id = fields.Many2one(
        'account.tax',
        string='Thuế con HKD',
        domain="[('hkd_tax_policy_id', '=', hkd_policy_id)]",
        help='Chọn đúng dòng thuế con theo chính sách thuế HKD đã gán cho sản phẩm.',
    )

    @api.onchange('hkd_policy_id')
    def _onchange_hkd_policy_id(self):
        self.hkd_tax_id = False
        self.taxes_id = [(5, 0, 0)]
    @api.onchange('hkd_tax_id')
    def _onchange_hkd_tax_id(self):
        if self.hkd_tax_id:
            self.taxes_id = [(6, 0, [self.hkd_tax_id.id])]
        else:
            self.taxes_id = [(5, 0, 0)]