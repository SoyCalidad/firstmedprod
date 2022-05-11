# -*- coding: utf-8 -*-

import logging
import requests
from datetime import datetime, date, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class PaymentType(models.Model):
	_name = "payment.type"
	_description = "Payment Type"

	name = fields.Char(string='Nombre', required=True)
	key = fields.Text(string='Descripción')
	

class Company(models.Model):
	_inherit = "res.company"

	p_currency_id = fields.Many2one('res.currency', string='Moneda compra', required=True, default=lambda self: self._default_currency_id())


class ResUsers(models.Model):
	_inherit = "res.users"

	token = fields.Char('Auth token for the API', default=None)


class SaleOrder(models.Model):
	_inherit = "sale.order"

	physician_id = fields.Many2one('res.partner', string='Médico', select=True)
	coupon_id = fields.Many2one('coupon.program', string='Promociones', select=True)
	journal_id = fields.Many2one('account.journal', string="Método de Pago", store=True, readonly=False, domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
	payment_type = fields.Many2one('payment.type', string='Modo de Pago', select=True)


class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	READONLY_STATES = {
		'purchase': [('readonly', True)],
		'done': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	currency_id = fields.Many2one('res.currency', 'Moneda compra', required=True, states=READONLY_STATES, default=lambda self: self.env.company.p_currency_id.id)

	@api.onchange('partner_id', 'company_id')
	def onchange_partner_id(self):
		# Ensures all properties and fiscal positions
		# are taken with the company of the order
		# if not defined, with_company doesn't change anything.
		self = self.with_company(self.company_id)
		if not self.partner_id:
			self.fiscal_position_id = False
			self.currency_id = self.env.company.p_currency_id.id
		else:
			self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(self.partner_id.id)
			self.payment_term_id = self.partner_id.property_supplier_payment_term_id.id
			self.currency_id = self.partner_id.property_purchase_currency_id.id or self.env.company.p_currency_id.id
		return {}


class Picking(models.Model):
	_inherit = "stock.picking"

	def button_validate(self):
		res = super(Picking, self).button_validate()
		# _logger.info("Print ---------------->")
		# _logger.info(self.location_id)
		return res

class StockMove(models.Model):
	_inherit = "stock.move"

	def _action_done(self, cancel_backorder=False):
		res = super(StockMove, self)._action_done(cancel_backorder)
		_logger.info("Print ---------------->")
		for r in self:
			# location = r.location_dest_id or r.location_id  or False
			# pick = r.picking_id
			# if pick:
			# 	if pick.picking_type_code in ('incoming', 'internal'):
			# 		location = r.location_dest_id
			# 	else:
			# 		location = r.location_id
			# _logger.info(location)
			locations = [r.location_dest_id, r.location_id]
			for location in locations:
				if location.usage == 'internal':
					sq = self.env['stock.quant'].search([('location_id','=',location.id),('product_id','=',r.product_id.id)])
					data = {
						'id_producto': r.product_id.id,
						'producto': r.product_id.name,
						'almacen-ubicacion': location.complete_name if location else False,
						'tipo': r.picking_type_id.name if r.picking_type_id else 'Ajuste de inventario',
						'stock': sq[-1].quantity if sq else 0.0,
						'available_stock': sq[-1].available_quantity if sq else 0.0,
						'consumo': r.quantity_done,
						'fecha_modificacion': r.write_date - timedelta(hours=5),
					}
					_logger.info(data)
					requests.post('https://bitrixdemo.site/odoo/productos.php', data=data)
		return res


class SaleOrder(models.Model):
	_inherit = "sale.order"

	def action_confirm(self):
		res = super(SaleOrder, self).action_confirm()
		for order in self:
			data = {
				'id_venta': order.id,
				'correlativo': order.name
			}
			_logger.info(data)
			requests.post('https://bitrixdemo.site/odoo/timbrado.php', data=data)
		return res
