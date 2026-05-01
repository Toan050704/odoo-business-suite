from odoo import fields, models

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_quick_produce(self):
        for rec in self:

            rec.qty_producing = rec.product_qty

            for move in rec.move_raw_ids:
                move.quantity_done = move.product_uom_qty

            for move in rec.move_finished_ids:
                move.quantity_done = rec.product_qty

            rec.button_mark_done()