# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

from werkzeug.exceptions import BadRequest, NotFound
from datetime import datetime

import jwt
import pytz

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
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
		query_search = [('name', '=', client['district'])]
		if 'province' in client:
			# l10n_city = request.env['res.city'].search([('name', '=', client['province'])], limit=1)
			query_search.append(('city_id.name', '=', client['province']))
		l10n_pe_district = request.env['l10n_pe.res.city.district'].sudo().search(query_search, limit=1)
		city = l10n_pe_district.city_id
		if client1:
			client1.write({
				'lang': 'es_PE',
				'street': client['address'] if 'address' in client else '',
				'phone': client['phone'] if 'phone' in client else '',
				'email': client['email'] if 'email' in client else '',
				'l10n_pe_district': l10n_pe_district.id if l10n_pe_district else None,
				'city_id': l10n_pe_district.city_id.id if l10n_pe_district.city_id else None,
				'state_id': l10n_pe_district.city_id.state_id.id if l10n_pe_district.city_id.state_id else None,
				'country_id': l10n_pe_district.city_id.state_id.country_id.id if l10n_pe_district.city_id.state_id.country_id else None,
			})
		else:
			identification_type = request.env['l10n_latam.identification.type'].sudo().search([('name', '=', client['identification_type'])], limit=1)
			name = client['name']
			if identification_type.l10n_pe_vat_code == '1':
				result = request.env['res.partner'].l10n_pe_dni_connection(client['code'])
				# name = str(request.env['res.partner'].l10n_pe_dni_connection(client['code'])['nombre'] or '').strip()
				if result:
					name = str(result['nombre']).strip()
				client1 = request.env['res.partner'].sudo().create({
					'lang': 'es_PE',
					'name': name,
					'vat': client['code'],
					'street': client['address'] if 'address' in client else '',
					'phone': client['phone'] if 'phone' in client else '',
					'email': client['email'] if 'email' in client else '',
					'l10n_pe_district': l10n_pe_district.id if l10n_pe_district else None,
					'city_id': l10n_pe_district.city_id.id if l10n_pe_district.city_id else None,
					'state_id': l10n_pe_district.city_id.state_id.id if l10n_pe_district.city_id.state_id else None,
					'country_id': l10n_pe_district.city_id.state_id.country_id.id if l10n_pe_district.city_id.state_id.country_id else None,
					'l10n_latam_identification_type_id': identification_type.id
				})
			elif identification_type.l10n_pe_vat_code == '6':
				# name = str(request.env['res.partner'].l10n_pe_ruc_connection(client['code'])['nombre'] or '').strip()
				result = request.env['res.partner'].l10n_pe_ruc_connection(client['code'])
				if result:
					client1 = request.env['res.partner'].sudo().create({
						'lang': 'es_PE',
						'alert_warning_vat': False,
						'company_type': 'company',
						'name': str(result['business_name']).strip(),
						'commercial_name': str(result['commercial_name'] or result['business_name']).strip(),
						'street': str(result['residence']).strip(),
						'state': 'habido' if result['contributing_condition'] == 'HABIDO' else 'nhabido',
						'vat': client['code'],
						'phone': client['phone'] if 'phone' in client else '',
						'email': client['email'] if 'email' in client else '',
						'l10n_latam_identification_type_id': identification_type.id
					})
					if result['value']:
						client1.l10n_pe_district = result['value']['district_id']
						client1.city_id = result['value']['city_id'] 
						client1.state_id = result['value']['state_id'] 
						client1.country_id = result['value']['country_id']
			else:
				client1 = request.env['res.partner'].sudo().create({
					'lang': 'es_PE',
					'name': client['name'],
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
			elif 'product_code' in l:
				params = [('default_code', '=', l['product_code'])]
			elif 'product_name' in l:
				params = [('name', '=', l['product_name'])]
			product = request.env['product.product'].sudo().search(params, limit=1)
			if not product:
				raise NotFound(description='Producto no encontrado con el nombre {}'.format(l['product_name']))
			tax = request.env['account.tax'].sudo().search([
				('name', '=', l['tax_code']), ('type_tax_use', '=', 'sale')], limit=1)
			if not tax:
				raise NotFound(description='Impuesto no encontrado con el codigo {}'.format(l['tax_code']))
			order_lines.append([0, 0, {
				'product_uom_qty': l['qty'],
				'price_unit': l['price_unit'],
				'product_id': product.id,
				'tax_id': [[6, False, [tax.id]]],
				'discount': l['descuento'] if 'descuento' in l else 0.0,
			}])
			
		return order_lines


	@token_protected
	@http.route('/api/saleRegister', auth='public', type='json', cors='*')
	def create_sale_order(self, **post):
		user_tz = request.env['res.users'].sudo().search([('name', '=', post['vendedor'])]).tz or pytz.utc
		local = pytz.timezone(user_tz)

		client = self.get_client(post['cliente'])
		lines = self.get_prepare_lines(post['lines'])
		medico = request.env['res.partner'].sudo().search([('name', '=',  post['medico']), ('is_physician', '=', True)], limit=1)
		if not medico:
			request.env['res.partner'].sudo().create({'name': post['medico'], 'is_physician': True, 'lang': 'es_PE',})
		payment_type = request.env['payment.type'].sudo().search([('name', '=',  post['modo_pago'])], limit=1)
		coupon = request.env['coupon.program'].sudo().search([('name', '=',  post['promocion'])], limit=1)
		# if not coupon:
		# 	raise NotFound(description='Promoción no encontrado con el nombre {}'.format(post['promocion']))
		carrier = request.env['delivery.carrier'].sudo().search([('name', '=',  post['tipo_entrega'])], limit=1)
		if not carrier:
			raise NotFound(description='Método de envío no encontrado con el nombre {}'.format(post['tipo_entrega']))
		journal = request.env['account.journal'].sudo().search([('name', '=',  post['tipo_pago'])], limit=1)
		if not carrier:
			raise NotFound(description='Método de pago no encontrado con el nombre {}'.format(post['tipo_pago']))
		data = [{
			'order_line': lines,
			'partner_id': client.id,
			'user_id': request.env['res.users'].sudo().search([('name', '=', post['vendedor'])]).id,
			'date_order': datetime.strptime(post['date_order'], "%Y-%m-%d %H:%M:%S") if post['date_order'] else datetime.today(),
			'date_order': datetime.strftime(pytz.utc.localize(datetime.strptime(post['date_order'], DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local), "%Y-%m-%d %H:%M:%S") if post['date_order'] else datetime.today(),
			'note': '',
			'physician_id': medico.id,
			'coupon_id': coupon.id if coupon else None,
			'carrier_id': carrier.id,
			'journal_id': journal.id,
			'payment_type': payment_type.id if payment_type else None,
		}]

		sale_order = request.env['sale.order']
		if 'id' in post:
			order = sale_order.browse(post['id'])
			if order:
				line = data[0].pop('order_line')
				order.sudo().write(data[0])
				return {
					"status_code": "200",
					"state": "success",
					"message": "Orden Modificada",
					"data": {
						"id": order.id
					}
				}

		order = sale_order.sudo().create(data)
		return {
			"status_code": "200",
			"state": "success",
			"message": "Orden Creada",
			"data": {
				"id": order.id
			}
		}