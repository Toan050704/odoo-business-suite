# -*- coding: utf-8 -*-


def post_init_hook(cr, registry):
    from odoo import api, SUPERUSER_ID

    env = api.Environment(cr, SUPERUSER_ID, {})
    env['res.company'].hkd_load_branding_from_module_static(force=False)
