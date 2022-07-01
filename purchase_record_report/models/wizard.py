# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api


class PurchaseReport(models.TransientModel):
    _name = "wizard.account.history"
    _description = "Registro de compras"

    def _default_month(self):
        return str(datetime.now().month)

    def _default_year(self):
        return str(datetime.now().year)

    month = fields.Selection(string="Mes", selection=[
        ('1', 'ENERO'),
        ('2', 'FEBRERO'),
        ('3', 'MARZO'),
        ('4', 'ABRIL'),
        ('5', 'MAYO'),
        ('6', 'JUNIO'),
        ('7', 'JULIO'),
        ('8', 'AGOSTO'),
        ('9', 'SETIEMBRE'),
        ('10', 'OCTUBRE'),
        ('11', 'NOVIEMBRE'),
        ('12', 'DICIEMBRE')], default=_default_month)

    year = fields.Char(
        string=u'Año',
        limit=4,
        default=_default_year,
        required=True,
    )

    start_date = fields.Date(string="Fecha Inicial",
                             required=True, copy=False, default=datetime.now())
    end_date = fields.Date(string="Fecha Final",
                           required=True, copy=False, default=datetime.now())

    company_id = fields.Many2one(
        string=u'Compañia',
        comodel_name='res.company', required=True,
        domain=lambda self: [('id', 'in', self.env.user.company_ids.ids)],
        default=lambda self: self.env.user.company_id.id,
    )
    type_report = fields.Selection(
        string=u'Tipo de reporte',
        selection=[('sale', 'sale'), ('purchase', 'purchase'),
                   ('invoice', 'invoice')],
        required=True, default='purchase'
    )

    def export_xls(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'wizard.account.history'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        if context.get('xls_export'):
            return self.env.ref('purchase_record_report.purchase_record_xlsx').report_action(self, data=datas)
