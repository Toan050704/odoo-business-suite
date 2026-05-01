# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AccountMoveLineHKD(models.Model):
    _inherit = 'account.move.line'

    hkd_tax_id = fields.Many2one(
        'account.tax',
        string='Chính sách thuế HKD',
        ondelete='set null',
        compute='_compute_hkd_tax_amounts',
        store=True,
    )
    hkd_tncn_amount = fields.Monetary(
        string='Tiền thuế TNCN',
        currency_field='currency_id',
        compute='_compute_hkd_tax_amounts',
        store=True,
    )
    hkd_vat_amount = fields.Monetary(
        string='Tiền thuế GTGT',
        currency_field='currency_id',
        compute='_compute_hkd_tax_amounts',
        store=True,
    )

    @api.depends('product_id', 'price_total', 'move_id.move_type')
    def _compute_hkd_tax_amounts(self):
        for line in self:
            tax = line.product_id.product_tmpl_id.hkd_tax_id
            base = line.price_total or 0.0
            if tax and line.move_id.move_type in ('out_invoice', 'out_refund'):
                line.hkd_tax_id = tax
                line.hkd_tncn_amount = base * (tax.hkd_pit_rate or 0.0) / 100.0
                line.hkd_vat_amount = base * (tax.amount or 0.0) / 100.0
            else:
                line.hkd_tax_id = False
                line.hkd_tncn_amount = 0.0
                line.hkd_vat_amount = 0.0