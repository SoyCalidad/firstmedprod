# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
	_inherit = "res.users"

	token = fields.Char('Auth token for the API', default=None)


class SaleOrder(models.Model):
	_inherit = "sale.order"

	physician_id = fields.Many2one('res.partner', string='Médico', select=True)
	coupon_id = fields.Many2one('coupon.program', string='Promociones', select=True)
	