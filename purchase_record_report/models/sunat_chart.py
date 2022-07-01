from odoo import fields, models

class SunatCatalog11(models.Model):
    _name = 'sunat.chart.11'
    _description = 'SUNAT Chart 11'
    _rec_name = 'description'

    code = fields.Char(string='Código')
    description = fields.Char(string='Descripción')