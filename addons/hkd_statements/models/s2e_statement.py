from odoo import models, fields, api

class S2EStatement(models.Model):
    _name = 's2e.statement'
    _description = 'So S2E - Theo doi tien mat & tien gui'
    _order = 'sequence, id'

    so_hieu = fields.Char(string="Số chứng từ")
    date = fields.Date(string="Ngày")
    dien_giai = fields.Char(string="Diễn giải")
    thu = fields.Float(string="Thu / Gửi vào")
    chi = fields.Float(string="Chi / Rút ra")
    sequence = fields.Integer(string="Thứ tự")
    move_id = fields.Many2one('account.move')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.model
    def _get_opening_balance(self, date_from):
        open_cash = 0
        open_bank = 0

        if not date_from:
            return open_cash, open_bank

        Payment = self.env['account.payment']
        payments_before = Payment.search([
            ('state', '=', 'posted'),
            ('date', '<', date_from),
        ])

        for p in payments_before:
            amount = p.amount if p.payment_type == 'inbound' else -p.amount
            if p.journal_id.type == 'cash':
                open_cash += amount
            else:
                open_bank += amount

        return open_cash, open_bank

    @api.model
    def action_load_data(self, date_from=None, date_to=None):
        self.search([]).unlink()

        Payment = self.env['account.payment']
        lines = []
        sequence = 1

        domain_base = [('state', '=', 'posted')]
        if date_from:
            domain_base.append(('date', '>=', date_from))
        if date_to:
            domain_base.append(('date', '<=', date_to))

        open_cash, open_bank = self._get_opening_balance(date_from)

        # ─── Tiền mặt đầu kỳ ──────────────────────────
        lines.append({
            'dien_giai': 'Tiền mặt đầu kỳ',
            'thu': open_cash, 'chi': 0,
            'sequence': sequence,
        })
        sequence += 1

        cash_payments = Payment.search([
            ('journal_id.type', '=', 'cash'),
        ] + domain_base, order='date asc')

        total_cash_thu = 0
        total_cash_chi = 0

        for p in cash_payments:
            if p.payment_type == 'inbound':
                thu = p.amount
                chi = 0
                total_cash_thu += thu
                dien_giai = f"Thu tiền mặt của {p.partner_id.name or ''}"
            else:
                thu = 0
                chi = p.amount
                total_cash_chi += chi
                dien_giai = f"Chi tiền mặt cho {p.partner_id.name or ''}"

            lines.append({
                'so_hieu': p.name or '',
                'date': p.date,
                'dien_giai': dien_giai,
                'thu': thu,
                'chi': chi,
                'sequence': sequence,
            })
            sequence += 1

        lines.append({
            'dien_giai': 'Tổng tiền thu vào trong kỳ',
            'thu': total_cash_thu, 'chi': 0,
            'sequence': sequence,
        })
        sequence += 1

        lines.append({
            'dien_giai': 'Tổng tiền chi ra trong kỳ',
            'thu': 0, 'chi': total_cash_chi,
            'sequence': sequence,
        })
        sequence += 1

        cash_end = open_cash + total_cash_thu - total_cash_chi
        lines.append({
            'dien_giai': 'Tiền mặt cuối kỳ',
            'thu': cash_end, 'chi': 0,
            'sequence': sequence,
        })
        sequence += 1

        # ─── Tiền gửi đầu kỳ ──────────────────────────
        lines.append({
            'dien_giai': 'Tiền gửi đầu kỳ',
            'thu': open_bank, 'chi': 0,
            'sequence': sequence,
        })
        sequence += 1

        bank_payments = Payment.search([
            ('journal_id.type', '=', 'bank'),
        ] + domain_base, order='date asc')

        total_bank_thu = 0
        total_bank_chi = 0

        for p in bank_payments:
            if p.payment_type == 'inbound':
                thu = p.amount
                chi = 0
                total_bank_thu += thu
                dien_giai = f"Thu tiền chuyển khoản của {p.partner_id.name or ''}"
            else:
                thu = 0
                chi = p.amount
                total_bank_chi += chi
                dien_giai = f"Chuyển tiền chuyển khoản cho {p.partner_id.name or ''}"

            lines.append({
                'so_hieu': p.name or '',
                'date': p.date,
                'dien_giai': dien_giai,
                'thu': thu,
                'chi': chi,
                'sequence': sequence,
            })
            sequence += 1

        lines.append({
            'dien_giai': 'Tổng tiền gửi vào trong kỳ',
            'thu': total_bank_thu, 'chi': 0,
            'sequence': sequence,
        })
        sequence += 1

        lines.append({
            'dien_giai': 'Tổng tiền rút ra trong kỳ',
            'thu': 0, 'chi': total_bank_chi,
            'sequence': sequence,
        })
        sequence += 1

        bank_end = open_bank + total_bank_thu - total_bank_chi
        lines.append({
            'dien_giai': 'Tiền gửi cuối kỳ',
            'thu': bank_end, 'chi': 0,
            'sequence': sequence,
        })

        BATCH_SIZE = 200
        for i in range(0, len(lines), BATCH_SIZE):
            self.create(lines[i:i + BATCH_SIZE])