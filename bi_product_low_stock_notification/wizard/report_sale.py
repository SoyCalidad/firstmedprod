''' from odoo import fields, models, api


class report_pos_sale(models.TransientModel):
    _name = "report.pos.sale"
    cliente = fields.Char(string='nombre de cliente')
#    report_pos_sale_ids = fields.One2many('sale.order', 'report_pos_sale_id')



#    report_pos_sale_id = fields.Many2one('report.pos.sale')
 '''