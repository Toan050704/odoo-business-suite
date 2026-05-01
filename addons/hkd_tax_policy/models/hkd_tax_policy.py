# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HKDTaxPolicy(models.Model):
    _name = 'hkd.tax.policy'
    _description = 'Chính sách thuế HKD'
    # _parent_name = 'parent_id'
    # _parent_store = True
    _order = 'sequence, id'

    name = fields.Char(
        string='Danh mục ngành nghề',
        required=True,
        translate=True
    )

    description = fields.Text(
        string='Mô tả chi tiết'
    )

    # vat_rate = fields.Float(
    #     string='Tỷ lệ % GTGT',
    #     digits=(16, 4)
    # )

    # pit_rate = fields.Float(
    #     string='Thuế suất TNCN (%)',
    #     digits=(16, 4)
    # )

    active = fields.Boolean(
        default=True
    )

    # parent_id = fields.Many2one(
    #     'hkd.tax.policy',
    #     string='Danh mục cha',
    #     ondelete='restrict',
    #     index=True,
    # )

    # child_ids = fields.One2many(
    #     'hkd.tax.policy',
    #     'parent_id',
    #     string='Chính sách con'
    # )

    # parent_path = fields.Char(
    #     index=True
    # )

    sequence = fields.Integer(
        string='Thứ tự',
        default=10
    )

    # complete_name = fields.Char(
    #     string='Đầy đủ',
    #     compute='_compute_complete_name',
    #     recursive=True,
    #     store=True,
    # )

    tax_ids = fields.One2many(
        'account.tax',
        'hkd_tax_policy_id',
        string='Thuế kế toán gắn',
    )

    tax_count = fields.Integer(
        compute='_compute_tax_count',
        string='Số thuế'
    )

    # @api.depends('name', 'parent_id.complete_name')
    # def _compute_complete_name(self):
    #     for rec in self:
    #         if rec.parent_id:
    #             rec.complete_name = '%s / %s' % (
    #                 rec.parent_id.complete_name,
    #                 rec.name,
    #             )
    #         else:
    #             rec.complete_name = rec.name

    def _compute_tax_count(self):
        for rec in self:
            rec.tax_count = len(rec.tax_ids)

    # def _is_leaf(self):
    #     """
    #     Kiểm tra có phải mục lá không
    #     (không có danh mục con)
    #     """
    #     self.ensure_one()
    #     return not bool(self.child_ids)

    # def _sync_account_tax(self):
    #     """
    #     Đồng bộ account.tax theo logic:

    #     - Nếu là policy lá:
    #         tạo / cập nhật trực tiếp account.tax

    #     - Nếu là policy cha:
    #         tự động cập nhật toàn bộ policy con lá bên dưới

    #     Mục tiêu:
    #     Khi sửa 4 danh mục cha thì toàn bộ thuế con
    #     sẽ tự động ăn theo % GTGT + % TNCN
    #     """

    #     AccountTax = self.env['account.tax']
    #     company = self.env.company

    #     for rec in self:

    #         # Nếu là mục lá -> xử lý chính nó
    #         if rec._is_leaf():
    #             leaf_policies = rec

    #         # Nếu là mục cha -> lấy toàn bộ mục con lá
    #         else:
    #             leaf_policies = rec.child_ids.filtered(
    #                 lambda x: not x.child_ids
    #             )

    #         for leaf in leaf_policies:

    #             existing = AccountTax.search([
    #                 ('hkd_tax_policy_id', '=', leaf.id),
    #                 ('type_tax_use', '=', 'sale'),
    #                 ('company_id', '=', company.id),
    #             ], limit=1)

    #             tax_name = leaf.name

    #             tax_vals = {
    #                 'name': tax_name,
    #                 'amount': leaf.vat_rate,
    #                 'amount_type': 'percent',
    #                 'type_tax_use': 'sale',
    #                 'hkd_tax_policy_id': leaf.id,
    #                 'hkd_pit_rate': leaf.pit_rate or 0.0,
    #                 'company_id': company.id,
    #                 'active': leaf.active,
    #             }

    #             if existing:
    #                 # Cập nhật thuế đã có
    #                 existing.write({
    #                     'name': tax_name,
    #                     'amount': leaf.vat_rate,
    #                     'hkd_pit_rate': leaf.pit_rate or 0.0,
    #                     'active': leaf.active,
    #                 })
    #             else:
    #                 # Tạo mới nếu chưa tồn tại
    #                 AccountTax.create(tax_vals)

    # def write(self, vals):
    #     res = super().write(vals)

    #     # Khi thay đổi:
    #     # - tên
    #     # - % GTGT
    #     # - % TNCN
    #     # - trạng thái active
    #     # => tự sync account.tax
    #     if any(k in vals for k in (
    #         'name',
    #         'vat_rate',
    #         'pit_rate',
    #         'active',
    #     )):
    #         self._sync_account_tax()

    #     return res

    # @api.model_create_multi
    # def create(self, vals_list):
    #     records = super().create(vals_list)

    #     # Tạo mới policy -> sync luôn
    #     records._sync_account_tax()

    #     return records

    # def action_sync_tax(self):
    #     """
    #     Button đồng bộ thủ công
    #     """
    #     self._sync_account_tax()

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': _('Đồng bộ thuế'),
    #             'message': _('Đã tạo/cập nhật account.tax thành công!'),
    #             'type': 'success',
    #         },
    #     }