from odoo import models, fields, api

class S2CStatement(models.Model):
    _name = 's2c.statement'
    _description = 'So S2C - Doanh thu & Chi phí'

    so_hieu = fields.Char(string="Số chứng từ")
    date = fields.Date(string="Ngày")
    dien_giai = fields.Char(string="Diễn giải")
    partner_id = fields.Many2one('res.partner', string="Nhà cung cấp")
    amount = fields.Float(string="Số tiền")
    sequence = fields.Integer(string="Thứ tự")
    move_id = fields.Many2one('account.move')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

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

    def _get_valid_bills(self, domain_base):
<<<<<<< HEAD
        """Trả về danh sách hóa đơn mua hàng hợp lệ:
        - Đã có số tham chiếu (ref)
        - Tổng tiền mặt thanh toán < 5,000,000
        """
=======
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
        bills = self.env['account.move'].search(
            [('move_type', '=', 'in_invoice')] + domain_base
        )
        valid = []
        for bill in bills:
<<<<<<< HEAD
            has_ref = bill.ref and bill.ref.strip()
            cash_amount = self._get_cash_payment_amount(bill)
            paid_amount = bill.amount_total - bill.amount_residual
            if has_ref and cash_amount < 5_000_000 and paid_amount > 0:
                valid.append(bill)
=======
            if not (bill.ref and bill.ref.strip()):
                continue

            cash_amount = self._get_cash_payment_amount(bill)
            paid_amount = bill.amount_total - bill.amount_residual

            if cash_amount >= 5_000_000:
                # Chỉ ghi phần đã trả không phải cash
                record_amount = paid_amount - cash_amount
            else:
                record_amount = paid_amount

            if record_amount > 0:
                valid.append((bill, record_amount))

>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
        return valid

    @api.model
    def action_load_data(self, date_from=None, date_to=None):
        self.search([]).unlink()

        Move = self.env['account.move']
        vals = []

        domain_base = [('state', '=', 'posted')]
        if date_from:
            domain_base.append(('invoice_date', '>=', date_from))
        if date_to:
            domain_base.append(('invoice_date', '<=', date_to))

        # ─── 1. Doanh thu ─────────────────────────────────────
        invoices = Move.search([('move_type', '=', 'out_invoice')] + domain_base)
        total_income = sum(invoices.mapped('amount_total'))

        vals.append({
            'sequence': 1,
            'dien_giai': 'Tổng doanh thu bán hàng hóa, dịch vụ',
            'amount': total_income,
        })

        # ─── 2. Chi phí ───────────────────────────────────────
        valid_bills = self._get_valid_bills(domain_base)
<<<<<<< HEAD
        total_expense = sum(b.amount_total for b in valid_bills)

        seq = 2
        for bill in valid_bills:
            paid_amount = bill.amount_total - bill.amount_residual  # ← thực trả
=======
        total_expense = sum(amount for _, amount in valid_bills)

        seq = 2
        for bill, record_amount in valid_bills:
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
            vals.append({
                'sequence': seq,
                'so_hieu': bill.ref or bill.name,
                'date': bill.invoice_date,
                'dien_giai': f"Mua hàng của {bill.partner_id.name} theo hóa đơn {bill.ref or bill.name}",
                'partner_id': bill.partner_id.id,
<<<<<<< HEAD
                'amount': paid_amount,  # ← thay amount_total
=======
                'amount': record_amount,
>>>>>>> 36ba606abda1a4370f443768e62d6c4f33df2425
                'move_id': bill.id,
            })
            seq += 1

        # ─── 3. Chênh lệch ────────────────────────────────────
        profit = total_income - total_expense
        vals.append({
            'sequence': seq,
            'dien_giai': 'Chênh lệch',
            'amount': profit,
        })
        seq += 1

        # ─── 4. Thuế TNCN ─────────────────────────────────────
        tax = profit * 0.15 if profit > 0 else 0
        vals.append({
            'sequence': seq,
            'dien_giai': 'Tổng số thuế TNCN phải nộp',
            'amount': tax,
        })

        self.create(vals)