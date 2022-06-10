from email.policy import strict
from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model): 
	_inherit = 'account.move'  

	def sale_invoice_link(self):
		return {
			'name': 'Vincular Orden de Venta',
			'res_model': 'account.sale.invoice',
			'view_mode': 'form',
			'context': {
				'active_model': 'account.move',
				'active_ids': self.ids,
			},
			'target': 'new',
			'type': 'ir.actions.act_window',
		}

class AccountPaymentRegister(models.TransientModel):
	_name = 'account.sale.invoice'
	_description = 'Vincular Orden de Venta'

	def default_move_id(self):
		# _logger.info("--------------------->")
		# _logger.info(self._context)
		if self._context.get('active_model') == 'account.move':
			return self.env['account.move'].browse(self._context.get('active_id')).id
		return False

	# == Business fields ==
	move_id = fields.Many2one('account.move', string="Comprobante", default=default_move_id)
	order_id = fields.Many2one('sale.order', string="Orden de Venta")

	def action_link_invoice(self):
		msg = "Hay incosistencia entre el comprobante y la orden de venta"
		invoice_lines = []
		order_lines = []
		invoice_ids = []
		order_ids = []
		for mline in self.move_id.invoice_line_ids:
			invoice_lines.append([mline.product_id.id, mline.quantity, mline.product_uom_id.id])
			invoice_ids.append(mline.id)
		for oline in self.order_id.order_line:
			order_lines.append([oline.product_id.id, oline.product_uom_qty, oline.product_uom.id])
			order_ids.append(oline.id)
		# _logger.info("--------------------->")
		# _logger.info(invoice_lines)
		# _logger.info(order_lines)
		# _logger.info(invoice_ids)
		# _logger.info(order_ids)

		if invoice_lines == order_lines:
			for i in range(len(invoice_ids)):
				self.env['sale.order.line'].browse(order_ids[i]).write({'qty_invoiced': self.env['account.move.line'].browse(invoice_ids[i]).quantity})
				self.env.cr.execute("""insert into sale_order_line_invoice_rel values (%s, %s)""", (str(invoice_ids[i]), str(order_ids[i])))				
			msg = "Orden de Venta enlaza correctamente"
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': 'Estado',
				'message': msg,
				'sticky': False,
			}
		}