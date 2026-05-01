from odoo import models, fields, api

class S2DStatement(models.Model):
    _name = 's2d.statement'
    _description = 'So S2D - Vat tu hang hoa'
    _order = 'date, sequence, id'

    so_hieu = fields.Char(string="Số hiệu")
    date = fields.Date(string="Ngày tháng")
    dien_giai = fields.Char(string="Diễn giải")

    product_id = fields.Many2one('product.product', string="Sản phẩm")
    uom_id = fields.Many2one('uom.uom', string="Đơn vị tính")
    don_gia = fields.Float(string="Đơn giá", digits=(16, 2))

    qty_in = fields.Float(string="SL Nhập")
    amount_in = fields.Float(string="TT Nhập", digits=(16, 2))

    qty_out = fields.Float(string="SL Xuất")
    amount_out = fields.Float(string="TT Xuất", digits=(16, 2))

    qty_balance = fields.Float(string="SL Tồn")
    amount_balance = fields.Float(string="TT Tồn", digits=(16, 2))

    sequence = fields.Integer(string="Thứ tự")
    move_id = fields.Many2one('stock.move')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.model
    def _get_opening_balance(self, product_id, date_from):
        open_qty = 0
        open_amount = 0
        avg_price = 0

        if not date_from:
            return open_qty, open_amount, avg_price

        ValLayer = self.env['stock.valuation.layer']
        moves_before = self.env['stock.move'].search([
            ('state', '=', 'done'),
            ('product_id', '=', product_id),
            ('date', '<', date_from),
        ], order='date asc')

        for m in moves_before:
            val = ValLayer.search([('stock_move_id', '=', m.id)], limit=1)
            don_gia = val.unit_cost if val else 0

            if m.location_dest_id.usage == 'internal':
                qty_in = m.product_uom_qty
                amount_in = qty_in * don_gia
                if (open_qty + qty_in) > 0:
                    avg_price = (open_qty * avg_price + amount_in) / (open_qty + qty_in)
                open_qty += qty_in
                open_amount = open_qty * avg_price

            elif m.location_id.usage == 'internal':
                qty_out = m.product_uom_qty
                open_qty -= qty_out
                open_amount = open_qty * avg_price

        return open_qty, open_amount, avg_price

    @api.model
    def action_load_data(self, product_id=None, date_from=None, date_to=None):
        domain = [('product_id', '=', product_id)] if product_id else []
        self.search(domain).unlink()

        open_qty, open_amount, avg_price = self._get_opening_balance(product_id, date_from)

        product = self.env['product.product'].browse(product_id)
        ValLayer = self.env['stock.valuation.layer']
        lines = []
        sequence = 1

        # ─── Nhập xuất trong kỳ ───────────────────────────────────
        move_domain = [('state', '=', 'done'), ('product_id', '=', product_id)]
        if date_from:
            move_domain.append(('date', '>=', date_from))
        if date_to:
            move_domain.append(('date', '<=', date_to))

        moves = self.env['stock.move'].search(move_domain, order='date asc')

        balance_qty = open_qty
        balance_amount = open_amount

        for m in moves:
            val = ValLayer.search([('stock_move_id', '=', m.id)], limit=1)
            move_date = m.date.date() if hasattr(m.date, 'date') else m.date

            if m.location_dest_id.usage == 'internal':
                don_gia = val.unit_cost if val else 0
                qty_in = m.product_uom_qty
                amount_in = qty_in * don_gia
                if (balance_qty + qty_in) > 0:
                    avg_price = (balance_qty * avg_price + amount_in) / (balance_qty + qty_in)
                balance_qty += qty_in
                balance_amount = balance_qty * avg_price

                # Nhập kho
                lines.append({
                    'so_hieu': getattr(m, 'reference', None) or m.origin or '',
                    'date': move_date,
                    'dien_giai': f"Mua hàng theo mã nội bộ {m.origin or ''}",
                    'product_id': product_id,
                    'uom_id': m.product_uom.id,
                    'don_gia': don_gia,
                    'qty_in': qty_in,
                    'amount_in': amount_in,
                    'qty_balance': balance_qty,
                    'amount_balance': balance_amount,
                    'sequence': sequence,
                    'move_id': m.id,
                })

            elif m.location_id.usage == 'internal':
                don_gia = avg_price
                qty_out = m.product_uom_qty
                amount_out = qty_out * don_gia
                balance_qty -= qty_out
                balance_amount = balance_qty * avg_price

                # Xuất kho
                lines.append({
                    'so_hieu': getattr(m, 'reference', None) or m.origin or '',
                    'date': move_date,
                    'dien_giai': f"Xuất kho theo mã nội bộ {m.origin or ''}",
                    'product_id': product_id,
                    'uom_id': m.product_uom.id,
                    'don_gia': don_gia,
                    'qty_out': qty_out,
                    'amount_out': amount_out,
                    'qty_balance': balance_qty,
                    'amount_balance': balance_amount,
                    'sequence': sequence,
                    'move_id': m.id,
                })

            else:
                continue

            sequence += 1

        # ─── Dòng cộng phát sinh trong kỳ ────────────────────────
        total_qty_in = sum(l.get('qty_in', 0) for l in lines)
        total_amount_in = sum(l.get('amount_in', 0) for l in lines)
        total_qty_out = sum(l.get('qty_out', 0) for l in lines)
        total_amount_out = sum(l.get('amount_out', 0) for l in lines)

        lines.append({
            'so_hieu': '',
            # 'date': date_to,
            'dien_giai': 'Cộng phát sinh trong kỳ',
            'product_id': product_id,
            # 'uom_id': product.uom_id.id,
            # 'don_gia': 0,
            'qty_in': total_qty_in,
            'amount_in': total_amount_in,
            'qty_out': total_qty_out,
            'amount_out': total_amount_out,
            # 'qty_balance': 0, 'amount_balance': 0,
            'sequence': sequence,
        })
        sequence += 1

        # ─── Dòng tồn cuối kỳ ────────────────────────────────────
        lines.append({
            'so_hieu': '',
            # 'date': date_to,
            'dien_giai': 'Tồn cuối kỳ',
            'product_id': product_id,
            # 'uom_id': product.uom_id.id,
            # 'don_gia': avg_price,
            # 'qty_in': 0, 'amount_in': 0,
            # 'qty_out': 0, 'amount_out': 0,
            'qty_balance': balance_qty,
            'amount_balance': balance_amount,
            'sequence': sequence,
        })

        BATCH_SIZE = 200
        for i in range(0, len(lines), BATCH_SIZE):
            self.create(lines[i:i + BATCH_SIZE])