# -*- coding: utf-8 -*-

import logging
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
	_inherit = "res.users"

	token = fields.Char('Auth token for the API', default=None)


class SaleOrder(models.Model):
	_inherit = "sale.order"

	physician_id = fields.Many2one('res.partner', string='Médico', select=True)
	coupon_id = fields.Many2one('coupon.program', string='Promociones', select=True)


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
		location = self.location_id or self.location_dest_id or False
		_logger.info("Print ---------------->")
		_logger.info(location)
		data = {
			'producto': self.product_id.name,
			'almacen-ubicacion': location.name if location else False,
			'tipo': self.picking_type_id.name if self.picking_type_id else False,
			'stock': self.quantity_done,
			'fecha_modificacion': self.write_date
		}
		requests.post('https://bitrixdemo.site/odoo/productos.php', data=data)
		return res
