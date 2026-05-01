# models/purchase_order.py
from odoo import models

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        res = super().button_confirm()

        for po in self:
            # lấy picking nhập hàng
            pickings = po.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel')
            )

            for picking in pickings:

                for move in picking.move_ids_without_package:
                    move.quantity_done = move.product_uom_qty

                if picking.state == 'draft':
                    picking.action_confirm()
                if picking.state in ['confirmed', 'waiting']:
                    picking.action_assign()

                picking.button_validate()

        return res