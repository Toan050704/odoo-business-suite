# -*- coding: utf-8 -*-
import logging
from collections import defaultdict

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    # SO chỉ xem được đối tác 
    partner_id = fields.Many2one(
        domain="['&', ('hkd_pos_walkin', '=', False), '&', ('type', '!=', 'private'), ('company_id', 'in', (False, company_id))]",
    )

    def _action_confirm(self):
        to_check = self.filtered(lambda o: o.state in ('draft', 'sent'))
        if to_check:
            to_check._hkd_assert_sale_stock()
        res = super()._action_confirm()
        self.filtered(lambda o: o.state in ('sale', 'done'))._hkd_auto_validate_delivery_after_confirm()
        return res

    def _hkd_auto_validate_delivery_after_confirm(self):
        """Sau khi xác nhận đơn bán: tự tạo và hoàn tất phiếu giao hàng nếu đủ điều kiện."""
        for order in self.filtered(lambda o: o.state in ('sale', 'done')):
            pickings = order._hkd_open_outgoing_pickings()
            if not pickings:
                lines = order.order_line.filtered(
                    lambda l: l.product_id.type == 'product' and not l.display_type
                )
                if lines:
                    lines.sudo()._action_launch_stock_rule()
                pickings = order._hkd_open_outgoing_pickings()
            for picking in pickings.sudo():
                order._hkd_try_validate_picking(picking, order)

    def _hkd_open_outgoing_pickings(self):
        return self.picking_ids.filtered(
            lambda p: p.state not in ('done', 'cancel')
            and p.picking_type_id.code == 'outgoing'
        )

    def _hkd_assert_sale_stock(self):
        """Chặn xác nhận đơn khi tổng SL hàng tồn kho vượt free_qty (kho đơn hàng)."""
        for order in self:
            if not order.company_id:
                continue
            wh = order.warehouse_id
            if not wh:
                wh = self.env['stock.warehouse'].search(
                    [('company_id', '=', order.company_id.id)],
                    limit=1,
                    order='sequence asc, id asc',
                )
            if not wh:
                raise UserError(
                    _('Đơn hàng %s không có kho (warehouse); không thể kiểm tra tồn kho.')
                    % (order.display_name,)
                )
            need_by_product = defaultdict(float)
            for line in order.order_line:
                if line.display_type or not line.product_id:
                    continue
                if line.product_id.type != 'product':
                    continue
                qty = line.product_uom._compute_quantity(
                    line.product_uom_qty,
                    line.product_id.uom_id,
                )
                need_by_product[line.product_id] += qty
            errors = []
            for product, need in need_by_product.items():
                free = product.sudo().with_context(warehouse=wh.id).free_qty
                if float_compare(need, free, precision_rounding=product.uom_id.rounding) > 0:
                    errors.append(
                        _('• %s: cần %s, khả dụng %s (%s)')
                        % (product.display_name, need, free, wh.display_name)
                    )
            if errors:
                raise UserError(
                    _('Không đủ tồn kho để xác nhận đơn %s:\n%s')
                    % (order.name, '\n'.join(errors))
                )

    def _hkd_auto_validate_delivery_after_invoice(self, invoice):
        self.ensure_one()
        if self.state not in ('sale', 'done'):
            return

        pickings = self._hkd_open_outgoing_pickings()
        if not pickings:
            lines = self.order_line.filtered(
                lambda l: l.product_id.type == 'product' and not l.display_type
            )
            if lines:
                lines.sudo()._action_launch_stock_rule()
            pickings = self._hkd_open_outgoing_pickings()
        for picking in pickings.sudo():
            self._hkd_try_validate_picking(picking, invoice)

    def _hkd_try_validate_picking(self, picking, invoice):
        self.ensure_one()
        try:
            if picking.state == 'draft':
                picking.action_confirm()
            if picking.state in ('waiting', 'confirmed'):
                picking.action_assign()
            if picking.state == 'assigned':
                for sm in picking.move_ids.filtered(
                    lambda m: m.state not in ('done', 'cancel')
                ):
                    sm.quantity_done = sm.product_uom_qty
                res = picking.button_validate()
                if isinstance(res, dict):
                    self.message_post(
                        body=_(
                            'Hóa đơn %(inv)s: phiếu %(pick)s cần xác nhận thủ công trên kho (wizard).'
                        )
                        % {'inv': invoice.name, 'pick': picking.name}
                    )
        except UserError as err:
            _logger.warning(
                'HKD auto delivery: SO %s picking %s — %s',
                self.name,
                picking.name,
                err,
            )
            self.message_post(
                body=_('Hóa đơn %s — không tự hoàn tất giao hàng: %s')
                % (invoice.name, str(err))
            )


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._hkd_assert_sale_lines_stock()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if any(k in vals for k in ('product_uom_qty', 'product_id', 'product_uom')):
            self._hkd_assert_sale_lines_stock()
        return res

    def _hkd_assert_sale_lines_stock(self):
        orders = self.mapped('order_id').filtered(
            lambda o: o.state in ('draft', 'sent')
        )
        if orders:
            orders._hkd_assert_sale_stock()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted._hkd_auto_validate_sale_delivery()
        return posted

    def _hkd_auto_validate_sale_delivery(self):
        """Sau khi post hóa đơn bán: tạo (nếu cần) và hoàn tất phiếu giao hàng liên quan đơn bán."""
        for move in self.filtered(
            lambda m: m.move_type == 'out_invoice' and m.state == 'posted'
        ):
            lines = move.invoice_line_ids.filtered(
                lambda l: l.display_type == 'product' and l.sale_line_ids
            )
            orders = lines.sale_line_ids.mapped('order_id')
            for order in orders:
                order._hkd_auto_validate_delivery_after_invoice(move)
