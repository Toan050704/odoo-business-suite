# -*- coding: utf-8 -*-
import json
from odoo import api, fields, models, _


class VendorDebtDashboard(models.TransientModel):
    _name = 'vendor.debt.dashboard'
    _description = 'Công nợ Nhà cung cấp & Tiểu thương'
    _rec_name = 'name'

    name = fields.Char(default='Công nợ Nhà cung cấp')
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
        rec._refresh_vendor_lines()
        return rec

    #  HELPER: trả về (supplier_invoices, trader_invoices)                #
    def _fetch_invoices(self):
        """
        NCC  → in_invoice / in_refund  (HKD nợ nhà cung cấp)
        Tiểu thương → out_invoice / out_refund (tiểu thương nợ HKD)
        """
        self.ensure_one()

        base = [
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('company_id', 'in', self.env.companies.ids),
        ]
        supplier_invoices = self.env['account.move'].search(
            [('move_type', 'in', ['in_invoice', 'in_refund'])] + base
        )
        trader_invoices = self.env['account.move'].search(
            [('move_type', 'in', ['out_invoice', 'out_refund'])] + base
        )
        return supplier_invoices, trader_invoices

    # KPI
    @api.depends_context('allowed_company_ids')
    def _compute_kpi(self):
        today = fields.Date.today()

        for rec in self:
            rec.currency_id = rec.env.company.currency_id

            supplier_invoices, trader_invoices = rec._fetch_invoices()

            supplier_total = sum(supplier_invoices.mapped('amount_residual'))
            trader_total   = sum(trader_invoices.mapped('amount_residual'))
            total          = supplier_total + trader_total

            all_invoices = supplier_invoices + trader_invoices
            overdue = sum(
                m.amount_residual for m in all_invoices
                if m.invoice_date_due and m.invoice_date_due < today
            )

            pos = rec.env['purchase.order'].search([
                ('state', 'in', ['purchase', 'done']),
                ('invoice_status', 'in', ['to invoice', 'nothing']),
                ('company_id', 'in', rec.env.companies.ids),
            ])

            rec.total_debt    = total
            rec.supplier_debt = supplier_total
            rec.trader_debt   = trader_total
            rec.overdue_debt  = overdue
            rec.not_due_debt  = total - overdue
            rec.po_pending    = sum(pos.mapped('amount_total'))

    # CHART
    @api.depends_context('allowed_company_ids')
    def _compute_chart_data(self):
        today = fields.Date.today()

        for rec in self:
            supplier_invoices, trader_invoices = rec._fetch_invoices()

            supplier_map = {}
            for inv in supplier_invoices:
                name = inv.partner_id.name or 'Không tên'
                supplier_map[name] = supplier_map.get(name, 0) + inv.amount_residual

            trader_map = {}
            for inv in trader_invoices:
                name = inv.partner_id.name or 'Không tên'
                trader_map[name] = trader_map.get(name, 0) + inv.amount_residual

            def _top10(data):
                return sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]

            top_suppliers = _top10(supplier_map)
            top_traders   = _top10(trader_map)

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

            all_invoices = supplier_invoices + trader_invoices
            overdue = sum(
                m.amount_residual for m in all_invoices
                if m.invoice_date_due and m.invoice_date_due < today
            )
            not_due = sum(all_invoices.mapped('amount_residual')) - overdue

            rec.chart_overdue_vs_notdue = json.dumps({
                'overdue':  round(overdue, 0),
                'not_due':  round(not_due, 0),
            })

    def _refresh_vendor_lines(self):
        today = fields.Date.today()

        for rec in self:
            supplier_invoices, trader_invoices = rec._fetch_invoices()

            rec.vendor_line_ids.unlink()
            lines_vals = []
            for inv in (supplier_invoices + trader_invoices).sorted('invoice_date_due'):
                partner_type = 'Nhà cung cấp' if inv.move_type in ('in_invoice', 'in_refund') else 'Tiểu thương'
                lines_vals.append({
                    'dashboard_id':     rec.id,
                    'vendor_name':      inv.partner_id.name or '',
                    'partner_type':     partner_type,
                    'invoice_ref':      inv.name or '',
                    'amount_total':     inv.amount_total,
                    'amount_residual':  inv.amount_residual,
                    'invoice_date_due': inv.invoice_date_due,
                    'is_overdue':       bool(inv.invoice_date_due and inv.invoice_date_due < today),
                    'move_id':          inv.id,
                })

            if lines_vals:
                self.env['vendor.debt.line'].create(lines_vals)

    # ACTIONS
    def action_refresh(self):
        self._refresh_vendor_lines()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_open_overdue_invoices(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hóa đơn quá hạn'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [
                ('move_type', 'in', ['in_invoice', 'in_refund', 'out_invoice', 'out_refund']),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', fields.Date.today()),
                ('company_id', 'in', self.env.companies.ids),
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
                ('company_id', 'in', self.env.companies.ids),
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
