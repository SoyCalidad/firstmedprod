# -*- coding: utf-8 -*-

import logging
import requests
from datetime import datetime, date, timedelta
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
	_inherit = "res.users"

	token = fields.Char('Auth token for the API', default=None)


class SaleOrder(models.Model):
	_inherit = "sale.order"

	physician_id = fields.Many2one('res.partner', string='Médico', select=True)
	coupon_id = fields.Many2one('coupon.program', string='Promociones', select=True)
	journal_id = fields.Many2one('account.journal', store=True, readonly=False,
		compute='_compute_journal_id',
		domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")


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
					data = {
						'id_producto': r.product_id.id,
						'producto': r.product_id.name,
						'almacen-ubicacion': location.complete_name if location else False,
						'tipo': r.picking_type_id.name if r.picking_type_id else 'Ajuste de inventario',
						'stock': self.env['stock.quant'].search([('location_id','=',location.id),('product_id','=',r.product_id.id)]).quantity,
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
