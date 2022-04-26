# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from werkzeug.exceptions import BadRequest, NotFound
from datetime import datetime

import jwt

from .utils import ISSUER, get_secret, token_protected


class OdooController(http.Controller):
	@http.route('/odoo-controller/odoo-controller/', auth='public')
	def index(self, **kw):
		return "Hello, world!"

	@http.route('/api/login', type="json", auth='none')
	def authenticate(self, **post):
		db = post['db']
		login = post['login']
		password = post['password']

		# request.session.authenticate(db, login, password)
		# return request.env['ir.http'].session_info()

		auth_successful = request.session.authenticate(db, login, password)
		if not auth_successful:
			raise BadRequest(description='Either the login or the password fields are wrong.')
		
		Users = request.env['res.users']
		user_match = Users.sudo().search([('login', '=', login)], limit=1)
		payload = {'iss': ISSUER, 'email': login, 'sub': 'authentication', 'iat': datetime.utcnow()}
		jwt_token = jwt.encode(payload, get_secret(request.env), algorithm='HS256')
		user_match.token = jwt_token
		request.cr.commit()
		request.session.logout()

		return {'token': jwt_token,}
		

	def get_client(self, client):
		client1 = request.env['res.partner'].sudo().search([('vat', '=', client['code'])], limit=1)
		identification_type = request.env['l10n_latam.identification.type'].sudo().search([('name', '=', client['identification_type'])], limit=1)
		name = client['name']
		if identification_type.l10n_pe_vat_code == '1':
			name = str(request.env['res.partner'].l10n_pe_dni_connection(client['code'])['nombre'] or '').strip()
		if not client1:
			client1 = request.env['res.partner'].sudo().create({
				'lang': 'es_PE',
				'name': name,
				'vat': client['code'],
				'l10n_latam_identification_type_id': identification_type.id
			})

		return client1

	def get_prepare_lines(self, lines):
		order_lines = list()
		for l in lines:
			params = list()
			if 'id' in l and l['id']:
				params = [('id', '=', l['id'])]
			else:
				if 'product_code' in l:
					params = [('default_code', '=', l['product_code'])]
			product = request.env['product.product'].sudo().search(params)
			if not product:
				raise NotFound(description='Producto no encontrado con el codigo {}'.format(l['product_code']))
			tax = request.env['account.tax'].sudo().search([
				('name', '=', l['tax_code']), ('type_tax_use', '=', 'sale')], limit=1)
			if not tax:
				raise NotFound(description='Impuesto no encontrado con el codigo {}'.format(l['tax_code']))
			order_lines.append([0, 0, {
				'product_uom_qty': l['qty'],
				'price_unit': l['price_unit'],
				'product_id': product.id,
				'tax_id': [[6, False, [tax.id]]],
			}])
			
		return order_lines


	@token_protected
	@http.route('/api/saleRegister', auth='public', type='json', cors='*')
	def create_sale_order(self, **post):
		# return "Hello, world!"
		client = self.get_client(post['cliente'])
		lines = self.get_prepare_lines(post['lines'])
		medico = request.env['res.partner'].sudo().search([('name', '=',  post['medico']), ('is_physician', '=', True)], limit=1)
		coupon = request.env['coupon.program'].sudo().search([('name', '=',  post['promocion'])], limit=1)
		data = [{
			# 'name': 'Pedido{}'.format(order_uid),
			# 'amount_paid': post['amount_total'],
			# 'amount_total': post['amount_total'],
			# 'amount_tax': post['amount_tax'],
			# 'amount_return': 0,
			'order_line': lines,
			# 'statement_ids': [],
			# 'pos_session_id': session.id,
			# 'pricelist_id': session.config_id.pricelist_id.id,
			'partner_id': client.id,
			'user_id': request.env['res.users'].sudo().search([('name', '=', post['vendedor'])]).id,
			# 'uid': order_uid,
			# 'sequence_number': session.sequence_number,
			# 'creation_date': datetime.today(),
			'date_order': datetime.today(),
			# 'fiscal_position_id': False,
			# 'table_id': False,
			# 'floor': False,
			# 'floor_id': False,
			# 'customer_count': 1,
			# 'operation_code': post['operation_code'],
			# 'payment_code': post['payment_code'],
			# 'observation': post['observation'],
			'note': '',
			# 'elimination_reason': False,
			'physician_id': medico.id,
			'coupon_id': coupon.id,
		}]
		# payments = self.get_payments(post['payments'], session)
		# data[0]['data']['statement_ids'] = payments
		# session.sudo().write({'sequence_number': session.sequence_number + 1})
		request.env['sale.order'].sudo().create(data)
		# order = request.env['pos.order'].sudo().browse(order[0])
		# request.env['pos.order'].sudo().send_invoice_mail(
		# 	order.invoice_id.id, order.partner_id.email)

		return {
			"status_code": "200",
			"state": "success",
			"message": "Orden Creada"
		}