# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _


class VendorDebtDashboard(models.TransientModel):
    _name = 'vendor.debt.dashboard'
<<<<<<< HEAD
    _description = 'Công nợ nhà cung cấp & tiểu thương'
    _rec_name = 'name'

    name = fields.Char(default='Công nợ nhà cung cấp')
=======
    _description = 'Công nợ Nhà cung cấp & Tiểu thương'
    _rec_name = 'name'

    name = fields.Char(default='Công nợ Nhà cung cấp')
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
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425

    # KPI
    total_debt = fields.Monetary(
        string='Tổng công nợ',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    supplier_debt = fields.Monetary(
        string='Công nợ nhà cung cấp',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    trader_debt = fields.Monetary(
        string='Công nợ tiểu thương',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    overdue_debt = fields.Monetary(
        string='Quá hạn',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    not_due_debt = fields.Monetary(
        string='Chưa đến hạn',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    po_pending = fields.Monetary(
        string='PO chưa xử lý',
        currency_field='currency_id',
        compute='_compute_kpi',
    )
    currency_id = fields.Many2one(
        'res.currency',
        compute='_compute_kpi',
    )

    # CHART
    chart_debt_by_vendor = fields.Char(
        compute='_compute_chart_data',
    )
    chart_overdue_vs_notdue = fields.Char(
        compute='_compute_chart_data',
    )
    chart_widget = fields.Char(string="Chart Widget")
    # TABLE
    vendor_line_ids = fields.One2many(
        'vendor.debt.line',
        'dashboard_id',
        string='Chi tiết công nợ',
    )

    #  AUTO CREATE + LOAD DATA
    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec._load_vendor_lines()
        return rec

    # KPI
<<<<<<< HEAD
    @api.depends()
=======
    @api.depends('date_from', 'date_to')
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
    def _compute_kpi(self):
        today = fields.Date.today()

        for rec in self:
            rec.currency_id = rec.env.company.currency_id

<<<<<<< HEAD
            invoices = rec.env['account.move'].search([
=======
            invoices_domain = [
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('company_id', 'in', rec.env.companies.ids),
<<<<<<< HEAD
            ])
=======
            ]
            if rec.date_from:
                invoices_domain.append(('invoice_date', '>=', rec.date_from))
            if rec.date_to:
                invoices_domain.append(('invoice_date', '<=', rec.date_to))

            invoices = rec.env['account.move'].search(invoices_domain)
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425

            supplier_invoices = invoices.filtered(lambda m: m.partner_id.supplier_rank > 0)
            trader_invoices = invoices.filtered(lambda m: m.partner_id.supplier_rank <= 0)

            total = sum(invoices.mapped('amount_residual'))
            supplier_total = sum(supplier_invoices.mapped('amount_residual'))
            trader_total = sum(trader_invoices.mapped('amount_residual'))

            overdue = sum(
                m.amount_residual for m in invoices
                if m.invoice_date_due and m.invoice_date_due < today
            )

            pos = rec.env['purchase.order'].search([
                ('state', 'in', ['purchase', 'done']),
                ('invoice_status', 'in', ['to invoice', 'nothing']),
                ('company_id', 'in', rec.env.companies.ids),
            ])

            rec.total_debt = total
            rec.supplier_debt = supplier_total
            rec.trader_debt = trader_total
            rec.overdue_debt = overdue
            rec.not_due_debt = total - overdue
            rec.po_pending = sum(pos.mapped('amount_total'))

    # CHART
<<<<<<< HEAD
    @api.depends()
=======
    @api.depends('date_from', 'date_to')
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
    def _compute_chart_data(self):
        today = fields.Date.today()

        for rec in self:
<<<<<<< HEAD
            invoices = rec.env['account.move'].search([
=======
            invoices_domain = [
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('company_id', 'in', rec.env.companies.ids),
<<<<<<< HEAD
            ])
=======
            ]
            if rec.date_from:
                invoices_domain.append(('invoice_date', '>=', rec.date_from))
            if rec.date_to:
                invoices_domain.append(('invoice_date', '<=', rec.date_to))

            invoices = rec.env['account.move'].search(invoices_domain)
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425

            supplier_map = {}
            trader_map = {}
            for inv in invoices:
                name = inv.partner_id.name or 'Không tên'
                target = supplier_map if inv.partner_id.supplier_rank > 0 else trader_map
                target[name] = target.get(name, 0) + inv.amount_residual

            def _top10(data):
                return sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]

            top_suppliers = _top10(supplier_map)
            top_traders = _top10(trader_map)

            rec.chart_debt_by_vendor = json.dumps({
                'supplier': {
                    'labels': [v[0] for v in top_suppliers],
                    'values': [round(v[1], 0) for v in top_suppliers],
                },
                'trader': {
                    'labels': [v[0] for v in top_traders],
                    'values': [round(v[1], 0) for v in top_traders],
                },
            })

            overdue = sum(
                m.amount_residual for m in invoices
                if m.invoice_date_due and m.invoice_date_due < today
            )

            not_due = sum(invoices.mapped('amount_residual')) - overdue

            rec.chart_overdue_vs_notdue = json.dumps({
                'overdue': round(overdue, 0),
                'not_due': round(not_due, 0),
            })

    # LOAD TABLE DATA
    def _load_vendor_lines(self):
        today = fields.Date.today()

        # Xóa dữ liệu cũ
        self.vendor_line_ids.unlink()

<<<<<<< HEAD
        invoices = self.env['account.move'].search([
=======
        domain = [
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('company_id', 'in', self.env.companies.ids),
<<<<<<< HEAD
        ], order='invoice_date_due asc')
=======
        ]
        if self.date_from:
            domain.append(('invoice_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('invoice_date', '<=', self.date_to))

        invoices = self.env['account.move'].search(domain, order='invoice_date_due asc')
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425

        lines = []
        for inv in invoices:
            partner_type = 'Nhà cung cấp' if inv.partner_id.supplier_rank > 0 else 'Tiểu thương'
            lines.append({
                'dashboard_id': self.id,
                'vendor_name': inv.partner_id.name or '',
                'partner_type': partner_type,
                'invoice_ref': inv.name or '',
                'amount_total': inv.amount_total,
                'amount_residual': inv.amount_residual,
                'invoice_date_due': inv.invoice_date_due,
                'is_overdue': bool(inv.invoice_date_due and inv.invoice_date_due < today),
                'move_id': inv.id,
            })

        self.env['vendor.debt.line'].create(lines)

    # ACTIONS
    def action_refresh(self):
        self._load_vendor_lines()

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'vendor.debt.dashboard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_overdue_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hóa đơn quá hạn'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', fields.Date.today()),
            ],
        }

    def action_open_po_pending(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('PO chưa xử lý'),
            'res_model': 'purchase.order',
            'view_mode': 'tree,form',
            'domain': [
                ('state', 'in', ['purchase', 'done']),
                ('invoice_status', 'in', ['to invoice', 'nothing']),
            ],
        }


# LINE MODEL
class VendorDebtLine(models.TransientModel):
    _name = 'vendor.debt.line'
    _description = 'Dòng công nợ NCC'

    dashboard_id = fields.Many2one('vendor.debt.dashboard')
    vendor_name = fields.Char()
    partner_type = fields.Selection([
        ('Nhà cung cấp', 'Nhà cung cấp'),
        ('Tiểu thương', 'Tiểu thương'),
    ])
    invoice_ref = fields.Char()
    amount_total = fields.Monetary(currency_field='currency_id')
    amount_residual = fields.Monetary(currency_field='currency_id')
    invoice_date_due = fields.Date()
    is_overdue = fields.Boolean()
    move_id = fields.Many2one('account.move')

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
    )