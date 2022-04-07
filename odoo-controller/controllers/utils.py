import functools
import jwt

from odoo.http import request
from werkzeug.exceptions import BadRequest, NotFound, Conflict

ISSUER = 'api.com'

def get_sys_param(param_key, env):
	'''
	Returns a value from the ir.config_parameter records

	:return: String that represents a system setting
	:param param_key: String that represents a 'key' or 'id' which identifies
					  a system setting.
	:param env: Environment object that would access the system settings.
	'''
	sys = env['ir.config_parameter']
	return sys.sudo().get_param(param_key)


def get_secret(env):
	'''Returns the secret from system settings'''
	return get_sys_param('api.secret', env)


def is_valid_token(decoded_token):
	if 'iss' not in decoded_token.keys() or decoded_token['iss'] != ISSUER:
		return False
	if 'email' not in decoded_token.keys():
		return False
	if 'iat' not in decoded_token.keys():
		return False
	return True
	

def token_protected(func):
	'''
	Decorator for api methods, makes sure the requests are correctly authenticated
	'''
	@functools.wraps(func)
	def decorator(*args, **kwargs):
		headers = request.httprequest.headers
		if 'Authorization' not in headers.keys():
			raise BadRequest(description='No authorization header provided')

		encoded_token = headers['Authorization'].split(' ')[1]
		decoded_token = jwt.decode(encoded_token, get_secret(request.env), algorithms=['HS256'])

		if not is_valid_token(decoded_token):
			raise Conflict(description='Invalid token')

		login = decoded_token['email']
		Users = request.env['res.users']
		user_match = Users.sudo().search([('login', '=', login)], limit=1)

		if not user_match:
			raise NotFound(description='No user found')
		kwargs['user'] = user_match
		return func(*args, **kwargs)

	return decorator