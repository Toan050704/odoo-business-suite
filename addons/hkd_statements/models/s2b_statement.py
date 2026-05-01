from odoo import models, fields, api

class S2BStatement(models.Model):
    _name = 's2b.statement'
    _description = 'So S2B'

    so_hieu = fields.Char(string="Số hiệu")
    date = fields.Date(string="Ngày")
    dien_giai = fields.Char(string="Diễn giải")
    # partner_id = fields.Many2one('res.partner', string="Khách hàng")
    amount = fields.Float(string="Số tiền")
    vat = fields.Float(string="Thuế GTGT")
    move_id = fields.Many2one('account.move')

    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id.id)

    @api.model
    def action_load_data(self, date_from=None, date_to=None):
        self.search([]).unlink()

        # ─── Domain theo kỳ ───────────────────────────────────
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ]
        if date_from:
            domain.append(('invoice_date', '>=', date_from))
        if date_to:
            domain.append(('invoice_date', '<=', date_to))

        invoices = self.env['account.move'].search(domain)

        vals_list = []
        for inv in invoices:
            vals_list.append({
                'so_hieu': inv.name,
                'date': inv.invoice_date,
                'dien_giai': f"Bán hàng cho khách hàng {inv.partner_id.name} theo hóa đơn {inv.name}",
                # 'partner_id': inv.partner_id.id,
                'amount': inv.amount_total,
                'vat': inv.amount_tax,
                'move_id': inv.id,
            })

        self.create(vals_list)