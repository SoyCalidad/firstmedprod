from odoo import api, fields, models


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    @api.depends('order_line.qty_invoiced', 'order_line.product_uom_qty')
    def _sale_order_invoiced_quantity_status(self):
        for rec in self:
            qty_invoice_count = sum(
                rec.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('qty_invoiced'))
            qty_order_count = sum(
                rec.mapped('order_line').filtered(lambda r: r.product_id.type != 'service').mapped('product_uom_qty'))
            if qty_order_count > qty_invoice_count > 0:
                rec.sale_order_invoiced_quantity_status = 'partially_invoiced'
            elif qty_order_count <= qty_invoice_count > 0:
                rec.sale_order_invoiced_quantity_status = 'invoiced'
            else:
                rec.sale_order_invoiced_quantity_status = 'not_invoiced'

    sale_order_invoiced_quantity_status = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('partially_invoiced', 'Partially Invoiced'),
        ('invoiced', 'Complete Invoiced')
    ], string='Invoiced Qty', compute="_sale_order_invoiced_quantity_status", store=True, readonly=True)
