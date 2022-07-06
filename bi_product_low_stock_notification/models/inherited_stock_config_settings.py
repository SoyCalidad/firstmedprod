# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import email
from statistics import mode
from odoo import fields, models, api, _
from ast import literal_eval
from odoo import SUPERUSER_ID
import base64
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = ['res.config.settings']

    @api.model
    def default_get(self, flds):
        result = super(ResConfigSettings, self).default_get(flds)

        context = self._context
        current_uid = context.get('uid')
        su_id = self.env['res.users'].browse(current_uid)
        result['current_user'] = su_id.id
        return result

    notification_product_type = fields.Selection([('template', 'Product'), (
        'variant', 'Product Variant')], related='company_id.notification_product_type', string='Apply On', readonly=False)

    notification_base = fields.Selection([('on_hand', 'On hand quantity'), ('fore_cast', 'Forecast')],
                                         related='company_id.notification_base', string='Notification Based On', readonly=False)
    notification_products = fields.Selection([('for_all', 'Global for all product'), ('fore_product', ' Individual for all products'), (
        'reorder', ' Reorder Rules')], related='company_id.notification_products', string='Min Quantity Based On', readonly=False)
    min_quantity = fields.Float(
        string='Quantity Limit', related='company_id.min_quantity', readonly=False)
    email_user = fields.Char(
        string="Email From", related='company_id.email', readonly=False)
    low_stock_products_ids = fields.One2many(
        'low.stock.transient', 'stock_product_id', store=True)

    value = fields.Char(string="Value", default="Value")
    current_user = fields.Many2one('res.users', string='current')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        context = self._context
        current_uid = context.get('uid')
        su_id = self.env['res.users'].browse(current_uid)
        self.current_user = su_id.id
        self.env['ir.config_parameter'].sudo().set_param(
            'bi_product_low_stock_notification.current_user', self.current_user)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update({
            'current_user': self.env['ir.config_parameter'].sudo().get_param('bi_product_low_stock_notification.current_user'), })
        return res

    def action_list_products_(self):
        products_list = []

        res = self.env['res.config.settings'].search(
            [], order="id desc", limit=1)

        cantidad = dict()
        qty_c = 0
        result_qty = self.env['purchase.order'].search([])
        for compra in result_qty:
            if compra.state == 'purchase':
                _logger.info("Comprado")
                lista = compra.order_line
                for product in lista:
                    ''' _logger.info("--------------------->")
                    _logger.info(product.product_id.id)
                    _logger.info("--------------------->") '''                
                    cantidad[product.product_id.id] = cantidad.get(product.product_id.id,0) + product.product_qty

        _logger.info("--------------------->")
        _logger.info(cantidad)
        _logger.info("--------------------->")

        if res.id:
            products_dlt = [(2, dlt.id, 0)
                            for dlt in res.low_stock_products_ids]
            res.low_stock_products_ids = products_dlt

            if res.notification_base == 'on_hand':
                if res.notification_products == 'for_all':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search(
                            [('qty_available', '<', res.min_quantity)])

                        for product in result:
                            name_att = ' '
                            for attribute in product.product_template_attribute_value_ids:
                                name_att = name_att + attribute.name + '  '

                            name_pro = ' '
                            if product.product_template_attribute_value_ids:
                                name_pro = product.name + ' - ' + name_att + '  '
                            else:
                                name_pro = product.name

                            if product.id in cantidad:
                                qty_c = cantidad[product.id]
                            else:
                                qty_c = 0

                            products_list.append([0, 0, {'name': name_pro,
                                                         'uom_id': product.uom_id.name,
                                                         'category_id': product.categ_id.name if product.categ_id else '',
                                                         'limit_quantity': res.min_quantity,
                                                         'stock_quantity': product.qty_available,
                                                         'cant_compra':qty_c}])
                    else:
                        result = self.env['product.template'].search([])
                        for product in result:
                            if product.id in cantidad:
                                qty_c = cantidad[product.id]
                            else:
                                qty_c = 0

                            if product.qty_available < res.min_quantity:
                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': res.min_quantity,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])

                if res.notification_products == 'fore_product':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search([])

                        for product in result:
                            if product.qty_available < product.min_quantity:
                                name_att = ' '
                                for attribute in product.product_template_attribute_value_ids:
                                    name_att = name_att + attribute.name + '  '

                                name_pro = ' '
                                if product.product_template_attribute_value_ids:
                                    name_pro = product.name + ' - ' + name_att + '  '
                                else:
                                    name_pro = product.name

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': name_pro,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.min_quantity,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])
                    else:
                        result = self.env['product.template'].search([])

                        for product in result:
                            if product.qty_available < product.temp_min_quantity:
                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.temp_min_quantity,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])

                if res.notification_products == 'reorder':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search([])
                        for product in result:
                            if product.qty_available < product.qty_min:
                                name_att = ' '
                                for attribute in product.product_template_attribute_value_ids:
                                    name_att = name_att + attribute.name + '  '

                                name_pro = ' '
                                if product.product_template_attribute_value_ids:
                                    name_pro = product.name + ' - ' + name_att + '  '
                                else:
                                    name_pro = product.name

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0
                                
                                vals = {'name': name_pro,
                                        'uom_id': product.uom_id.name,
                                        'category_id': product.categ_id.name if product.categ_id else '',
                                        'limit_quantity': product.qty_min,
                                        'stock_quantity': product.qty_available,
                                        'cant_compra':qty_c}

                                products_list.append([0, 0, vals])

                    else:
                        result = self.env['product.template'].search([])

                        for product in result:
                            if product.qty_available < product.temp_qty_min:
                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.temp_qty_min,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])

            if res.notification_base == 'fore_cast':
                if res.notification_products == 'for_all':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search(
                            [('virtual_available', '<', res.min_quantity)])
                        for product in result:
                            name_att = ' '
                            for attribute in product.product_template_attribute_value_ids:
                                name_att = name_att + attribute.name + '  '

                            name_pro = ' '
                            if product.product_template_attribute_value_ids:
                                name_pro = product.name + ' - ' + name_att + '  '

                            else:
                                name_pro = product.name

                            if product.id in cantidad:
                                qty_c = cantidad[product.id]
                            else:
                                qty_c = 0

                            products_list.append([0, 0, {'name': name_pro,
                                                         'uom_id': product.uom_id.name,
                                                         'category_id': product.categ_id.name if product.categ_id else '',
                                                         'limit_quantity': res.min_quantity,
                                                         'stock_quantity': product.virtual_available,
                                                         'cant_compra':qty_c}])
                    else:
                        result = self.env['product.template'].search([])

                        for product in result:
                            if product.virtual_available < res.min_quantity:
                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': res.min_quantity,
                                                             'stock_quantity': product.virtual_available,
                                                             'cant_compra':qty_c}])

                if res.notification_products == 'fore_product':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search([])

                        for product in result:
                            if product.virtual_available < product.min_quantity:
                                name_att = ' '
                                for attribute in product.product_template_attribute_value_ids:
                                    name_att = name_att + attribute.name + '  '

                                name_pro = ' '
                                if product.product_template_attribute_value_ids:
                                    name_pro = product.name + ' - ' + name_att + '  '
                                else:
                                    name_pro = product.name

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': name_pro,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.min_quantity,
                                                             'stock_quantity': product.virtual_available,
                                                             'cant_compra':qty_c}])

                    else:
                        result = self.env['product.template'].search([])

                        for product in result:
                            if product.virtual_available < product.temp_min_quantity:

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.temp_min_quantity,
                                                             'stock_quantity': product.virtual_available,
                                                             'cant_compra':qty_c}])

                if res.notification_products == 'reorder':

                    if res.notification_product_type == 'variant':
                        result = self.env['product.product'].search([])
                        for product in result:
                            if product.qty_available < product.qty_min:
                                name_att = ' '
                                for attribute in product.product_template_attribute_value_ids:
                                    name_att = name_att + attribute.name + '  '

                                name_pro = ' '
                                if product.product_template_attribute_value_ids:
                                    name_pro = product.name + ' - ' + name_att + '  '
                                else:
                                    name_pro = product.name

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0
                                products_list.append([0, 0, {'name': name_pro,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.qty_min,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])
                    else:
                        result = self.env['product.template'].search([])

                        for product in result:
                            if product.qty_available < product.temp_qty_min:

                                if product.id in cantidad:
                                    qty_c = cantidad[product.id]
                                else:
                                    qty_c = 0

                                products_list.append([0, 0, {'name': product.name,
                                                             'uom_id': product.uom_id.name,
                                                             'category_id': product.categ_id.name if product.categ_id else '',
                                                             'limit_quantity': product.temp_qty_min,
                                                             'stock_quantity': product.qty_available,
                                                             'cant_compra':qty_c}])

            res.low_stock_products_ids = products_list
            return
        else:
            return

    def action_low_stock_send(self):
        context = self._context
        current_uid = context.get('uid')
        su_id = self.env['res.users'].browse(current_uid)
        self.action_list_products_()
        company = self.env['res.company'].search(
            [('notify_low_stock', '=', True)])
        res = self.env['res.config.settings'].search(
            [], order="id desc", limit=1)
        if su_id:
            current_user = su_id
        else:
            current_user = res['current_user']
        if res.id:
            if res.low_stock_products_ids:
                if company:
                    for company_is in company:
                        template_id = self.env['ir.model.data'].get_object_reference(
                            'bi_product_low_stock_notification', 'low_stock_email_template')[1]
                        email_template_obj = self.env['mail.template'].browse(
                            template_id)
                        if template_id:
                            values = email_template_obj.generate_email(
                                res.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
                            values['email_from'] = current_user.email
                            values['email_to'] = company_is.email
                            values['email_cc'] = company_is.email_cc
                            values['author_id'] = current_user.partner_id.id
                            values['res_id'] = False
                            pdf = self.env.ref(
                                'bi_product_low_stock_notification.action_low_stock_report')._render([res.id])[0]
                            values['attachment_ids'] = [(0, 0, {
                                'name': 'Reporte de Stock Mínimo.pdf',
                                'datas': base64.b64encode(pdf),
                                'res_model': res._name,
                                'res_id': res.id,
                                'mimetype': 'application/x-pdf',
                                'type': 'binary',
                            })]
                            mail_mail_obj = self.env['mail.mail']
                            msg_id = mail_mail_obj.create(values)
                            if msg_id:
                                msg_id.send()

                for partner in self.env['res.users'].search([]):
                    if partner.notify_user:
                        template_id = self.env['ir.model.data'].get_object_reference(
                            'bi_product_low_stock_notification', 'low_stock_email_template')[1]
                        email_template_obj = self.env['mail.template'].browse(
                            template_id)
                        if template_id:
                            values = email_template_obj.generate_email(
                                res.id, ['subject', 'body_html', 'email_from', 'email_to', 'partner_to', 'email_cc', 'reply_to', 'scheduled_date'])
                            values['email_from'] = current_user.email
                            values['email_to'] = partner.email
                            values['author_id'] = current_user.partner_id.id
                            values['res_id'] = False
                            pdf = self.env.ref(
                                'bi_product_low_stock_notification.action_low_stock_report')._render([res.id])[0]
                            values['attachment_ids'] = [(0, 0, {
                                'name': 'Reporte de Stock Mínimo.pdf',
                                'datas': base64.b64encode(pdf),
                                'res_model': res._name,
                                'res_id': res.id,
                                'mimetype': 'application/x-pdf',
                                'type': 'binary',
                            })]
                            mail_mail_obj = self.env['mail.mail']
                            msg_id = mail_mail_obj.create(values)
                            if msg_id:
                                msg_id.send()
        return True


'''     def action_low_stock_send(self):
        list_report_sale = []
        datos_venta = self.env['sale.order']
        res = self.env['res.config.settings'].search(
            [], order="id desc", limit=1)
        context = self._context
        current_uid = context.get('uid')
        datos_usuario = self.env['res.users'].browse(current_uid)
#        for venta in datos_venta:
        list_report_sale.append([0, 0, {'cliente': 'Hola'}])
        res.report_sale_products_ids = list_report_sale '''


class low_stock_product(models.TransientModel):
    _name = 'low.stock.transient'
    ''' _order = 'name asc' '''

    name = fields.Char(string='Product name')
    uom_id = fields.Char(string='Product uom')
    stock_quantity = fields.Float(string='Quantity')
    limit_quantity = fields.Float(string='Quantity limit')
    stock_product_id = fields.Many2one('res.config.settings')
    category_id = fields.Char(string='Category name')
    cant_compra = fields.Float(string="Cantidad comprada")
    

''' class edit_produc_product(models.Model):
    _inherit = 'product.product'
    qty_cantidad_p_p = fields.Many2one('purchase.order')

class edit_produc_template(models.Model):
    _inherit = 'product.template'
    qty_compra = fields.Float(string="Cantidad comprada", default=0) '''


class reporte_venta(models.Model):
    #    _name = "reporte.de.venta"
    _inherit = 'sale.order'
    cliente2 = fields.Char(string='Nombre Cliente')
    transaction_ids = fields.Many2many('payment.transaction', 'report_sale_order_transaction_rel', 'report_sale_order_id', 'transaction_id',
                                        string='Transactions', copy=False, readonly=True)
    tag_ids = fields.Many2many(
        'crm.tag', 'report_sale_order_tag_rel', 'report_order_id', 'tag_id', string='Tags')
    phone = fields.Char(related="partner_id.phone")
#    partner_id = fields.Many2one(string="Nombre")
    email = fields.Char(related="partner_id.email")
    invoice_fecha = fields.Date(
        related="invoice_ids.invoice_date", string="Fecha de factura")
    fecha_actual = fields.Date(default=datetime.today())
