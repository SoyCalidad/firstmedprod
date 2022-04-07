# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
	_inherit = "res.users"

	token = fields.Char('Auth token for the API', default=None)
