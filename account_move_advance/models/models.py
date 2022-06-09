# -*- coding: utf-8 -*-

from odoo import fields,models,api, _
import logging
_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = 'product.template'

	is_advance = fields.Boolean(string='Es anticipo', default=False)

class Product(models.Model):
	_inherit = "product.product"

	is_advance = fields.Boolean(string='Es anticipo', related='product_tmpl_id.is_advance', store=True)


class AccountMove(models.Model):
	_inherit = 'account.move'

	# @api.depends('invoice_line_ids.product_id')
	def _has_advance(self):
		self.has_advances = False
		advances = self.invoice_line_ids.mapped('product_id').filtered(lambda r:r.is_advance == True)
		if advances:
			self.has_advances = True
		# if not self.ids:
		# 	return
		# for invoice in self.filtered('id'):
		# 	advances = invoice.invoice_line_ids.mapped('product_id').filtered(lambda r:r.is_advance == True)
		# 	if advances:
		# 		invoice.has_advances = True

	has_advances = fields.Boolean(compute='_has_advance', string='Tiene anticipos')
	total_advance = fields.Monetary(related='partner_id.total_advance', string="Total Anticipos")

	def get_credits(self, invoice_line):
		advances = self.env['account.move.line'].search([
			('partner_id','=',invoice_line.partner_id.id),
			('l10n_pe_edi_advance_serie','=',invoice_line.move_id.l10n_pe_edi_serie),
			('l10n_pe_edi_advance_number','=',invoice_line.move_id.l10n_pe_edi_number)])
		total = sum([adv.price_total for adv in advances]) if advances else 0.0
		_logger.info(total)
		return invoice_line.price_total + total

	def action_match(self):
		if self.total_advance > 0:
			sum_advances = sum(self.invoice_line_ids.filtered(lambda r:r.product_id.is_advance == False).mapped('price_total'))
			line = self.env['account.move.line']
			advances_ids = line.search([('partner_id','=',self.partner_id.id),('move_id.state','=','posted'),
				('product_id.is_advance','=',True),('price_total','>',0)], order='date asc') 

			product = self.env['product.product'].search([('is_advance','=',True)], limit=1)
			if not product:
				product = self.env['product.product'].create({
					'name': 'Anticipo',
					'is_advance': True,
					'type': 'service',
					'lst_price': 0.0,
				})
			if advances_ids and sum_advances>0:
				residual = sum_advances
				for adv in advances_ids:
					credit = self.get_credits(adv)
					# _logger.info("---------------> Credits %i, %s, %f, %f" %(adv.id, adv.move_id.name, adv.price_total, credit))
					if residual > 0 and credit > 0:
						amount = residual if credit >= residual else credit
						accounts = product.product_tmpl_id.get_product_accounts(fiscal_pos=self.fiscal_position_id)
						line_vals = {
							'name': "Pago anticipado %s\nAnticipo %s" % (str(adv.move_id.invoice_date), adv.move_id.name),
							'product_id': product.id,
							'quantity': -1,
							'price_unit': amount,
							'tax_ids': [(6, 0, product.taxes_id.ids)],
							'account_id': accounts['income'] or False,
							'l10n_pe_edi_advance_serie': adv.move_id.l10n_pe_edi_serie,
							'l10n_pe_edi_advance_number': adv.move_id.l10n_pe_edi_number,
						}
						self.write({'invoice_line_ids': [(0, 0, line_vals)]})
						residual -= amount
	
	def action_msg_advance(self):
		advances_ids = self.env['account.move.line'].search([('partner_id','=',self.partner_id.id),('move_id.state','=','posted'),
			('product_id.is_advance','=',True),('price_total','>',0)], order='date asc') 
		credits = "" if advances_ids else "0.0"
		for adv in advances_ids:
			credits += ("\n%s : %.2f" % (adv.move_id.name, self.get_credits(adv)))
			_logger.info(self.get_credits(adv))	
		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': 'Créditos disponibles',
				'message': credits,
				'sticky': False,
			}
		}

	def action_match_advance(self):
		if self.invoice_line_ids.mapped('product_id').filtered(lambda r:r.is_advance == True):
			return self.action_msg_advance()
		else:
			self.action_match()
			self.button_draft()
	

class ResPartner(models.Model):
	_inherit = 'res.partner'
	
	def _advance_total(self):
		self.total_advance = 0
		# if not self.ids:
		# 	return True

		# all_partners_and_children = {}
		# all_partner_ids = []
		# for partner in self.filtered('id'):
		# 	all_partners_and_children[partner] = self.with_context(active_test=False).search([('id', 'child_of', partner.id)]).ids
		# 	all_partner_ids += all_partners_and_children[partner]

		domain = [
			('partner_id', '=', self.id),
			('move_id.state', 'not in', ['draft', 'cancel']),
			('move_id.move_type', 'in', ('out_invoice', 'out_refund')),
			('product_id.is_advance', '=', True),
		]
		# price_totals = self.env['account.move.line'].read_group(domain, ['price_total'], ['partner_id'])
		# for partner, child_ids in all_partners_and_children.items():
		# 	partner.total_advance = sum(price['price_total'] for price in price_totals if price['partner_id'][0] in child_ids)
		prices = self.env['account.move.line'].search(domain)
		self.total_advance = sum(price.price_total for price in prices) if prices else 0

	# advance_ids = fields.Many2many('product.product', string='Anticipos')
	total_advance = fields.Monetary(compute='_advance_total', string="Total Anticipos",
		groups='account.group_account_invoice,account.group_account_readonly')

	def action_view_partner_advance(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id("account_move_advance.action_move_out_invoice_type_2")
		action['domain'] = [
			'&', '&', ('move_type', 'in', ('out_invoice', 'out_refund')),
			('has_advances', '=', True),
			('partner_id', 'child_of', self.id),
		]
		action['context'] = {'default_move_type':'out_invoice', 'move_type':'out_invoice', 'journal_type': 'sale', 'search_default_unpaid': 1}
		return action