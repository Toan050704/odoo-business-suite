# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DashboardLauncher(models.TransientModel):
    _name = 'dashboard.launcher'
    _description = 'HKD dashboard period filter and report shortcuts'
    _rec_name = 'name'

    name = fields.Char(
        string='Tiêu đề',
        default=lambda self: self._default_display_name(),
        readonly=True,
    )
    date_from = fields.Date(
        string='Từ ngày',
        required=True,
        default=lambda self: fields.Date.today().replace(day=1),
    )
    date_to = fields.Date(
        string='Đến ngày',
        required=True,
        default=fields.Date.today,
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Tiền tệ',
        compute='_compute_summary_totals',
    )
    revenue_total = fields.Monetary(
        string='Tổng doanh thu',
        currency_field='currency_id',
        compute='_compute_summary_totals',
    )
    expense_total = fields.Monetary(
        string='Tổng chi phí hợp lệ',
        currency_field='currency_id',
        compute='_compute_summary_totals',
    )

    expense_invalid_total = fields.Monetary(
        string='Chi phí không hợp lệ',
        currency_field='currency_id',
        compute='_compute_summary_totals',
    )

    net_result = fields.Monetary(
        string='Lợi nhuận (Doanh thu - Chi phí)',
        currency_field='currency_id',
        compute='_compute_summary_totals',
    )

    tax_revenue_tncn = fields.Monetary(
        string='Tổng thuế TNCN phải nộp (DT)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_revenue_vat = fields.Monetary(
        string='Tổng thuế GTGT phải nộp (DT)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_revenue_total = fields.Monetary(
        string='Tổng thuế (DT)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_profit_tncn = fields.Monetary(
        string='Tổng thuế TNCN phải nộp (LN)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_profit_vat = fields.Monetary(
        string='Tổng thuế GTGT phải nộp (LN)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_profit_total = fields.Monetary(
        string='Tổng thuế (LN)',
        currency_field='currency_id',
        compute='_compute_tax_comparison',
    )
    tax_compare_note = fields.Html(
        string='Kết luận so sánh thuế',
        compute='_compute_tax_comparison',
        sanitize=False,
    )

    @api.model
    def _default_display_name(self):
        return _('Báo cáo & Thống kê Thuế Hộ Kinh Doanh')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self._default_display_name()
        return super().create(vals_list)

    def name_get(self):
        label = _('Báo cáo & Thống kê Thuế Hộ Kinh Doanh')
        return [(rec.id, label) for rec in self]

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_from > rec.date_to:
                raise UserError(_('Từ ngày phải nhỏ hơn hoặc bằng Đến ngày.'))

    def _read_group_balance_sum(self, domain):
        rows = self.env['account.move.line'].read_group(domain, ['balance:sum'], [])
        if not rows:
            return 0.0
        row = rows[0]
        val = row.get('balance_sum', row.get('balance'))
        return float(val or 0.0)

    @api.depends('date_from', 'date_to')
    def _compute_summary_totals(self):
        for rec in self:
            rec.currency_id = rec.env.company.currency_id

            domain_invoice = [
                ('state', '=', 'posted'),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ('paid', 'in_payment')),  
            ]
            if rec.date_from:
                domain_invoice.append(('invoice_date', '>=', rec.date_from))
            if rec.date_to:
                domain_invoice.append(('invoice_date', '<=', rec.date_to))

            invoices = rec.env['account.move'].search(domain_invoice)
            rec.revenue_total = sum(invoices.mapped('amount_total'))

            rec.expense_total, rec.expense_invalid_total = rec._compute_cost_of_goods_sold()
            rec.net_result = rec.revenue_total - rec.expense_total

    def _get_cash_payment_amount(self, move):
        """Tổng tiền đã thanh toán bằng tiền mặt cho hóa đơn này."""
        payment_lines = move.line_ids.filtered(
            lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable')
                    and l.reconciled
        )
        cash_amount = 0.0
        for partial in payment_lines.mapped('matched_debit_ids') + payment_lines.mapped('matched_credit_ids'):
            counterpart = (
                partial.debit_move_id
                if partial.credit_move_id in payment_lines
                else partial.credit_move_id
            )
            if counterpart.journal_id.type == 'cash':
                cash_amount += partial.amount
        return cash_amount

    def _compute_cost_of_goods_sold(self):
        self.ensure_one()
        domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', 'in_invoice'),
        ]
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))

        bills = self.env['account.move'].search(domain)

        valid_total = 0.0
        invalid_total = 0.0

        for bill in bills:
            has_ref = bill.ref and bill.ref.strip()
            cash_amount = self._get_cash_payment_amount(bill)
            paid_amount = bill.amount_total - bill.amount_residual

            if not has_ref:
                invalid_total += paid_amount
            elif cash_amount >= 5_000_000:
                invalid_total += paid_amount
            else:
                valid_total += paid_amount

        return valid_total, invalid_total

    @api.depends('date_from', 'date_to', 'revenue_total', 'expense_total')
    def _compute_tax_comparison(self):
        profit_rate = 15.0
        for rec in self:
            domain = rec._move_line_period_domain()
            lines = self.env['account.move.line'].search(domain)
            profit_base = max((rec.revenue_total or 0.0) - (rec.expense_total or 0.0), 0.0)

            tncn_total = sum(line.hkd_tncn_amount for line in lines)
            vat_total = sum(line.hkd_vat_amount for line in lines)

            rec.tax_revenue_tncn = tncn_total
            rec.tax_revenue_vat = vat_total
            rec.tax_revenue_total = tncn_total + vat_total

            rec.tax_profit_tncn = profit_base * profit_rate / 100.0
            rec.tax_profit_vat = vat_total
            rec.tax_profit_total = rec.tax_profit_tncn + rec.tax_profit_vat

            # FIX: cả 2 nhánh đều có đủ 2 dòng công thức
            if rec.tax_profit_total < rec.tax_revenue_total:
                rec.tax_compare_note = _(
                    '<p><strong>Khuyến nghị: tính thuế theo lợi nhuận.</strong></p>'
                    '<p>Tổng thuế ước tính theo phương án này thấp hơn: %(profit)s so với %(revenue)s.</p>'
                    '<p><em>Phương pháp doanh thu = Doanh thu × %%TNCN + Doanh thu × %%GTGT.</em></p>'
                    '<p><em>Phương pháp lợi nhuận = (Doanh thu - Chi phí) × 15%% + Doanh thu × %%GTGT.</em></p>'
                ) % {
                    'profit': format(rec.tax_profit_total, ',.0f'),
                    'revenue': format(rec.tax_revenue_total, ',.0f'),
                }
            elif rec.tax_revenue_total < rec.tax_profit_total:
                rec.tax_compare_note = _(
                    '<p><strong>Khuyến nghị: tính thuế theo doanh thu.</strong></p>'
                    '<p>Tổng thuế ước tính theo phương án này thấp hơn: %(revenue)s so với %(profit)s.</p>'
                    '<p><em>Phương pháp doanh thu = Doanh thu × %%TNCN + Doanh thu × %%GTGT.</em></p>'
                    '<p><em>Phương pháp lợi nhuận = (Doanh thu - Chi phí) × 15%% + Doanh thu × %%GTGT.</em></p>'
                ) % {
                    'revenue': format(rec.tax_revenue_total, ',.0f'),
                    'profit': format(rec.tax_profit_total, ',.0f'),
                }
            else:
                rec.tax_compare_note = _(
                    '<p><strong>Hai phương án đang tương đương.</strong></p>'
                    '<p>Doanh nghiệp có thể chọn phương án phù hợp nhất với hồ sơ thực tế và khả năng giải trình.</p>'
                )

    def _company_domain_leaf(self):
        return ('company_id', 'in', self.env.companies.ids)

    def _move_line_period_domain(self):
        self.ensure_one()
        return [
            ('parent_state', '=', 'posted'),
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            self._company_domain_leaf(),
        ]

    def _open_account_move_list(self, title, extra_domain, extra_context=None):
        self.ensure_one()
        domain = [
            ('state', '=', 'posted'),
        ] + list(extra_domain)
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        ctx = dict(self.env.context)
        if extra_context:
            ctx.update(extra_context)
        return {
            'type': 'ir.actions.act_window',
            'name': title,
            'res_model': 'account.move',
            'view_mode': 'tree,form,pivot,graph',
            'domain': domain,
            'context': ctx,
        }

    def action_open_revenue(self):
        self.ensure_one()
        return self._open_account_move_list(
            _('Doanh thu'),
            [
                ('move_type', '=', 'out_invoice'),
                ('payment_state', 'in', ('paid', 'in_payment')),
            ],
        )

    def action_open_expense(self):
        self.ensure_one()
        bills = self._get_period_vendor_bills()
        valid_ids = []
        for bill in bills:
            has_ref = bill.ref and bill.ref.strip()
            cash_amount = self._get_cash_payment_amount(bill)
            if has_ref and cash_amount < 5_000_000:
                valid_ids.append(bill.id)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Chi phí hợp lệ'),
            'res_model': 'account.move',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('id', 'in', valid_ids)],
        }

    # chi phí không hợp lệ
    def action_open_expense_invalid(self):
        self.ensure_one()
        bills = self._get_period_vendor_bills()

        invalid_ids = []
        for bill in bills:
            has_ref = bill.ref and bill.ref.strip()
            cash_amount = self._get_cash_payment_amount(bill)
            if not has_ref or cash_amount >= 5_000_000:
                invalid_ids.append(bill.id)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Chi phí không hợp lệ'),
            'res_model': 'account.move',
            'view_mode': 'tree,form,pivot,graph',
            'domain': [('id', 'in', invalid_ids)],
        }

    def _get_period_vendor_bills(self):
        self.ensure_one()
        domain = [
            ('state', '=', 'posted'),
            ('move_type', '=', 'in_invoice'),
        ]
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))
        return self.env['account.move'].search(domain)
