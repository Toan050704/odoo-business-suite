# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountTax(models.Model):
    _inherit = 'account.tax'

    hkd_pit_rate = fields.Float(
        string='Thuế suất TNCN',
        digits=(16, 4),
        default=0.0,
    )
    hkd_tax_policy_id = fields.Many2one(
        'hkd.tax.policy',
        string='Chính sách thuế HKD',
        index=True,
        ondelete='set null',
        help='Chỉ chọn mục lá trong cây chính sách thuế (mục cha trung gian không chọn tại đây).',
    )
