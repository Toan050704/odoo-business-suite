# -*- coding: utf-8 -*-
import base64
import logging
import os

from odoo import api, fields, models
from odoo.modules.module import get_module_resource

_logger = logging.getLogger(__name__)

_IMG_NAMES = {
    'company_logo': ('company_logo.png', 'company_logo.jpg', 'company_logo.jpeg'),
    'pos_logo': ('pos_logo.png', 'pos_logo.jpg', 'pos_logo.jpeg'),
    'apps_menu_background': (
        'apps_menu_background.png',
        'apps_menu_background.jpg',
        'apps_menu_background.jpeg',
    ),
}


def _read_static_img_b64(module, filenames):
    for name in filenames:
        path = get_module_resource(module, 'static/img', name)
        if path and os.path.isfile(path):
            with open(path, 'rb') as f:
                return base64.b64encode(f.read()).decode('ascii')
    return None


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def hkd_load_branding_from_module_static(self, force=False, companies=None):
        """Đọc ảnh trong addons/hkd_sales/static/img/ và ghi vào công ty + POS.

        Tên file (thử theo thứ tự .png → .jpg → .jpeg):
          - company_logo.*  → Logo công ty (login, v.v.)
          - apps_menu_background.* → Nền menu app (cần MuK: trường background_image)
          - pos_logo.* → Logo POS (pos.config thuộc các công ty được chọn)

        companies=None: chỉ công ty chính (post_init_hook).
        force=False: chỉ ghi ô đang trống.
        force=True: ghi đè (Hành động trên form công ty).
        """
        module = 'hkd_sales'
        if companies is None:
            companies = self.env.ref('base.main_company', raise_if_not_found=False)
        if not companies:
            _logger.warning('HKD branding: không có công ty mục tiêu')
            return True
        companies = companies.sudo()

        b64_company = _read_static_img_b64(module, _IMG_NAMES['company_logo'])
        b64_bg = _read_static_img_b64(module, _IMG_NAMES['apps_menu_background'])
        b64_pos = _read_static_img_b64(module, _IMG_NAMES['pos_logo'])

        if not any((b64_company, b64_bg, b64_pos)):
            _logger.info(
                'HKD branding: bỏ qua — chưa có file trong static/img '
                '(company_logo.png / apps_menu_background.png / pos_logo.png).'
            )
            return True

        for company in companies:
            if b64_company and (force or not company.logo):
                company.write({'logo': b64_company})
                _logger.info('HKD branding: company_logo.* → công ty %s', company.id)

            if b64_bg and 'background_image' in company._fields:
                if force or not company.background_image:
                    company.write({'background_image': b64_bg})
                    _logger.info('HKD branding: apps_menu_background.* → công ty %s (MuK)', company.id)

        if b64_pos:
            configs = self.env['pos.config'].sudo().search(
                [('company_id', 'in', companies.ids)]
            )
            to_write = configs if force else configs.filtered(lambda c: not c.hkd_pos_logo)
            if to_write:
                to_write.write({'hkd_pos_logo': b64_pos})
                _logger.info('HKD branding: pos_logo.* → %s cấu hình POS', len(to_write))

        return True


class ResPartner(models.Model):
    _inherit = 'res.partner'

    hkd_pos_walkin = fields.Boolean(
        string='Khách vãng lai POS (HKD)',
        default=False,
        copy=False,
        help='Contact do POS tự tạo (đánh dấu nội bộ).',
    )
