from odoo import fields, models

class AccountMove(models.Model):
    _inherit = "account.move"

    dua_year = fields.Char(string='Año de emisión de la DUA o DSI')
    customs_dependency = fields.Many2one(
        'sunat.chart.11', string='Dependencia ADUANERA')