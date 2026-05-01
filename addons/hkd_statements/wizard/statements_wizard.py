from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

class StatementsWizard(models.TransientModel):
    _name = 'statements.wizard'
    _description = 'Chọn tham số xem sổ S2D'

    product_id = fields.Many2one('product.product', string="Sản phẩm")

    target_model = fields.Selection([
        ('s2b.statement', 'Sổ S2B'),
        ('s2c.statement', 'Sổ S2C'),
        ('s2d.statement', 'Sổ S2D'),
        ('s2e.statement', 'Sổ S2E'),
    ], string="Model")

    ky_bao_cao = fields.Selection([
        ('nam', 'Theo năm'),
        ('quy', 'Theo quý'),
        ('thang', 'Theo tháng'),        
        ('tuy_chon', 'Tuỳ chọn'),
    ], string="Kỳ báo cáo", default='nam', required=True)

    thang = fields.Selection([
        ('1', 'Tháng 1'), ('2', 'Tháng 2'), ('3', 'Tháng 3'),
        ('4', 'Tháng 4'), ('5', 'Tháng 5'), ('6', 'Tháng 6'),
        ('7', 'Tháng 7'), ('8', 'Tháng 8'), ('9', 'Tháng 9'),
        ('10', 'Tháng 10'), ('11', 'Tháng 11'), ('12', 'Tháng 12'),
    ], string="Tháng")

    quy = fields.Selection([
        ('1', 'Quý 1'), ('2', 'Quý 2'),
        ('3', 'Quý 3'), ('4', 'Quý 4'),
    ], string="Quý")

    nam = fields.Char(string="Năm", default=lambda self: fields.Date.today().year)

    date_from = fields.Date(string="Từ ngày")
    date_to = fields.Date(string="Đến ngày")

    @api.onchange('ky_bao_cao', 'thang', 'quy', 'nam')
    def _onchange_ky_bao_cao(self):
        today = fields.Date.today()
        nam = self.nam or today.year

        if self.ky_bao_cao == 'thang' and self.thang:
            thang = int(self.thang)
            self.date_from = fields.Date.from_string(f'{nam}-{thang:02d}-01')
            self.date_to = self.date_from + relativedelta(months=1, days=-1)

        elif self.ky_bao_cao == 'quy' and self.quy:
            quy = int(self.quy)
            thang_dau = (quy - 1) * 3 + 1
            self.date_from = fields.Date.from_string(f'{nam}-{thang_dau:02d}-01')
            self.date_to = self.date_from + relativedelta(months=3, days=-1)

        elif self.ky_bao_cao == 'nam':
            self.date_from = fields.Date.from_string(f'{nam}-01-01')
            self.date_to = fields.Date.from_string(f'{nam}-12-31')

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'target_model' not in res or not res['target_model']:
            res['target_model'] = self.env.context.get('default_target_model', 's2d.statement')
        
        # raise UserError(f"target_model = {res.get('target_model')} | context = {self.env.context}")
        return res

    def action_load(self):
        action = None

        if self.target_model == 's2d.statement':
            if not self.product_id:
                raise UserError("Vui lòng chọn sản phẩm!")
            self.env['s2d.statement'].action_load_data(
                product_id=self.product_id.id,
                date_from=self.date_from,
                date_to=self.date_to,
            )
            action = self.env.ref('hkd_statements.action_s2d_statement').read()[0]
            action['domain'] = [('product_id', '=', self.product_id.id)]
            action['name'] = f'Sổ S2D - {self.product_id.display_name}'

        elif self.target_model == 's2c.statement':
            self.env['s2c.statement'].action_load_data(
                date_from=self.date_from,
                date_to=self.date_to,
            )
            action = self.env.ref('hkd_statements.action_s2c_statement').read()[0]

        elif self.target_model == 's2b.statement':
            self.env['s2b.statement'].action_load_data(
                date_from=self.date_from,
                date_to=self.date_to,
            )
            action = self.env.ref('hkd_statements.action_s2b_statement').read()[0]

        elif self.target_model == 's2e.statement':
            self.env['s2e.statement'].action_load_data(
                date_from=self.date_from,
                date_to=self.date_to,
            )
            action = self.env.ref('hkd_statements.action_s2e_statement').read()[0]

        if not action:
            raise UserError("Không xác định được sổ cần xem!")

        action['target'] = 'main'

        return action