# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class PosConfigImmediate(models.Model):
    _inherit = 'pos.config'

    immediate_invoice = fields.Boolean(
        string='Immediate Invoice',
        default=True,
        help='Automatically create and confirm invoice when customer pays, '
             'without waiting for cash close.'
    )


class PosOrderImmediate(models.Model):
    _inherit = 'pos.order'

    immediate_invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Immediate Invoice',
        readonly=True,
        copy=False,
    )

    def _hkd_pos_warehouse_for_session(self, pos_session):
        wh = pos_session.config_id.warehouse_id
        if not wh:
            wh = self.env['stock.warehouse'].search(
                [('company_id', '=', pos_session.company_id.id)],
                limit=1,
                order='sequence asc, id asc',
            )
        return wh

    def _hkd_pos_need_by_product_from_line_commands(self, line_commands):
        """Cộng SL theo product.product từ payload POS (0,0,vals)."""
        need_by_product = defaultdict(float)
        for cmd in line_commands or []:
            if not cmd or len(cmd) < 3 or not isinstance(cmd[2], dict):
                continue
            vals = cmd[2]
            pid = vals.get('product_id')
            qty = vals.get('qty') or 0.0
            if qty <= 0 or not pid:
                continue
            product = self.env['product.product'].browse(pid).exists()
            if not product or product.type != 'product':
                continue
            uom = (
                self.env['uom.uom'].browse(vals['product_uom_id']).exists()
                if vals.get('product_uom_id')
                else product.uom_id
            )
            if not uom:
                uom = product.uom_id
            qty_product_uom = uom._compute_quantity(qty, product.uom_id)
            need_by_product[product] += qty_product_uom
        return need_by_product

    def _hkd_pos_raise_if_insufficient(self, need_by_product, wh, session_label=''):
        if not wh:
            raise UserError(
                _('Không có kho (warehouse) để kiểm tra tồn kho%s.')
                % (' (%s)' % session_label if session_label else '')
            )
        errors = []
        for product, need in need_by_product.items():
            free = product.sudo().with_context(warehouse=wh.id).free_qty
            if float_compare(need, free, precision_rounding=product.uom_id.rounding) > 0:
                errors.append(
                    _('• %s: bán %s, khả dụng %s')
                    % (product.display_name, need, free)
                )
        if errors:
            raise UserError(
                _('Không đủ tồn kho để thanh toán đơn POS:\n%s')
                % '\n'.join(errors)
            )

    def _hkd_assert_pos_stock_ui(self, data, pos_session):
        """Chạy trước super()._process_order — Odoo core nuốt UserError trong action_pos_order_paid."""
        wh = self._hkd_pos_warehouse_for_session(pos_session)
        need = self._hkd_pos_need_by_product_from_line_commands(data.get('lines'))
        self._hkd_pos_raise_if_insufficient(
            need, wh, session_label=pos_session.display_name
        )

    @api.model
    def _process_order(self, order, draft, existing_order):
        data = order['data']
        pos_session = self.env['pos.session'].browse(data['pos_session_id'])
        if pos_session.state in ('closing_control', 'closed'):
            data['pos_session_id'] = self._get_valid_session(data).id
            pos_session = self.env['pos.session'].browse(data['pos_session_id'])
        if not draft:
            self._hkd_assert_pos_stock_ui(data, pos_session)
        return super()._process_order(order, draft, existing_order)

    def action_pos_order_paid(self):
        self._hkd_assert_pos_stock()
        res = super().action_pos_order_paid()
        for order in self:
            if order.config_id.immediate_invoice:
                order._create_immediate_invoice()
        return res

    def _hkd_assert_pos_stock(self):
        """Khong cho thanh toán khi số lượng ở pos lớn hơn tồn kho."""
        for order in self:
            wh = order.config_id.warehouse_id
            if not wh:
                wh = self.env['stock.warehouse'].search(
                    [('company_id', '=', order.company_id.id)],
                    limit=1,
                    order='sequence asc, id asc',
                )
            need_by_product = defaultdict(float)
            for line in order.lines:
                if not line.product_id or line.product_id.type != 'product':
                    continue
                if line.qty <= 0:
                    continue
                uom = line.product_uom_id or line.product_id.uom_id
                qty = uom._compute_quantity(line.qty, line.product_id.uom_id)
                need_by_product[line.product_id] += qty
            self._hkd_pos_raise_if_insufficient(
                need_by_product, wh, session_label=order.display_name
            )

    def _create_immediate_invoice(self):
        self.ensure_one()
        if self.immediate_invoice_id:          # ←  check immediate_invoice_id
            _logger.info('POS Order %s đã có invoice, bỏ qua.', self.name)
            return
        if not self.lines:
            return
        self._ensure_pos_walk_in_partner()
        try:
            invoice_vals = self._prepare_immediate_invoice_vals()
            invoice = self.env['account.move'].sudo().create(invoice_vals)
            invoice.action_post()
            self._reconcile_immediate_payment(invoice)
            self.immediate_invoice_id = invoice
            _logger.info('Đã tạo invoice %s cho POS Order %s.', invoice.name, self.name)
        except Exception as e:
            _logger.error('Lỗi tạo invoice cho POS Order %s: %s', self.name, str(e))
            raise UserError(
                _('Không thể tạo hóa đơn cho đơn %s.\nLỗi: %s') % (self.name, str(e))
            )

    def _ensure_pos_walk_in_partner(self):
        """Tạo res.partner mới thay cho Public user / không chọn khách."""
        self.ensure_one()
        public = self.env.ref('base.public_partner', raise_if_not_found=False)
        if self.partner_id and (not public or self.partner_id.id != public.id):
            return
        seq_rec = self.env.ref('hkd_sales.seq_pos_walkin_partner', raise_if_not_found=False)
        if not seq_rec:
            raise UserError(
                _('Thiếu chuỗi số "POS Khách lẻ (HKD)" (hkd_sales.seq_pos_walkin_partner).')
            )
        seq_rec = seq_rec.sudo()
        if seq_rec.prefix != 'KH-':
            seq_rec.write({'prefix': 'KH-'})
        seq_name = seq_rec.next_by_id()
        trace = (self.pos_reference or self.name or '').strip()
        vals = {
            'name': seq_name,
            'customer_rank': 1,
            'hkd_pos_walkin': True,
        }
        if trace:
            vals['comment'] = _('Đơn POS: %s') % trace
        partner = self.env['res.partner'].sudo().create(vals)
        self.write({'partner_id': partner.id})

    def _prepare_immediate_invoice_vals(self):
        self.ensure_one()
        partner = self.partner_id
        if not partner:
            self._ensure_pos_walk_in_partner()
            partner = self.partner_id
        if not partner:
            partner = self.env.ref('base.public_partner', raise_if_not_found=False)
        if not partner:
            raise UserError(_('Không thể xác định khách hàng cho hóa đơn POS.'))
        journal = self.env['account.journal'].search(
            [
                ('type', '=', 'sale'),
                ('company_id', '=', self.company_id.id)
            ],
            limit=1
        )

        if not journal:
            raise UserError(_('Không tìm thấy Sales Journal. Vui lòng cấu hình trong Accounting.'))

        invoice_lines = [
            (0, 0, self._prepare_immediate_invoice_line_vals(line))
            for line in self.lines
        ]

        return {
            'move_type': 'out_invoice',
            'partner_id': partner.id,

            'journal_id': journal.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'ref': self.name,
            'narration': f'POS Order: {self.name}',
            'currency_id': self.currency_id.id,
            'invoice_line_ids': invoice_lines,
        }

    def _prepare_immediate_invoice_line_vals(self, line):
        product = line.product_id
        account = (
            product.property_account_income_id
            or product.categ_id.property_account_income_categ_id
        )
        line_taxes = line.tax_ids.filtered(
            lambda t: t.company_id == self.company_id
        )
        product_taxes = product.taxes_id.filtered(
            lambda t: t.company_id == self.company_id
        )
        taxes = line_taxes or product_taxes
        return {
            'product_id': product.id,
            'name': line.full_product_name or product.name,
            'quantity': line.qty,
            'price_unit': line.price_unit,
            'discount': line.discount,
            'account_id': account.id if account else False,
            'tax_ids': [(6, 0, taxes.ids)],
            'hkd_tax_id': (product.hkd_tax_id.id if product.hkd_tax_id else False),
        }

    def _reconcile_immediate_payment(self, invoice):
        self.ensure_one()
        if not self.payment_ids:
            return
        for payment in self.payment_ids:
            journal = payment.payment_method_id.journal_id
            if not journal:
                continue
            acc_payment = self.env['account.payment'].sudo().create({
                'amount': payment.amount,
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'partner_id': invoice.partner_id.id,
                'journal_id': journal.id,
                'date': fields.Date.today(),
                'ref': f'POS {self.name} - {payment.payment_method_id.name}',
                'currency_id': self.currency_id.id,
            })
            acc_payment.action_post()

            lines_to_reconcile = (
                invoice.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable'
                )
                | acc_payment.line_ids.filtered(
                    lambda l: l.account_id.account_type == 'asset_receivable'
                )
            )
            lines_to_reconcile.reconcile()

    def action_view_immediate_invoice(self):
        self.ensure_one()
        if not self.immediate_invoice_id:
            raise UserError(_('Đơn hàng này chưa có hóa đơn.'))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Hóa đơn'),
            'res_model': 'account.move',
            'res_id': self.immediate_invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
