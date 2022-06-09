# -*- coding: utf-8 -*-
# from odoo import http


# class AccountMoveAdvance(http.Controller):
#     @http.route('/account_move_advance/account_move_advance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_move_advance/account_move_advance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_move_advance.listing', {
#             'root': '/account_move_advance/account_move_advance',
#             'objects': http.request.env['account_move_advance.account_move_advance'].search([]),
#         })

#     @http.route('/account_move_advance/account_move_advance/objects/<model("account_move_advance.account_move_advance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_move_advance.object', {
#             'object': obj
#         })
