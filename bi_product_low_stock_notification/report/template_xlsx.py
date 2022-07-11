from odoo import models
import logging
_logger = logging.getLogger(__name__)


class PosReportXlsx(models.AbstractModel):

    _name = 'report.bi_product_low_stock_notification.reporte_venta_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, sales):
        sheet = workbook.add_worksheet('Reporte de Ventas')
        bold_n = workbook.add_format({'bold': True})
        bold_sn = workbook.add_format({'bold': False})
        date_style = workbook.add_format({'text_wrap': True, 'num_format': 'dd-mm-yyyy'})
        format_title = workbook.add_format({'bold':True, 'align':'center'})
        
        row = 3

        sheet.merge_range(0, 0, 0, 6, 'REPORTE DE VENTA', format_title)

        sheet.write(2, 0, 'FECHA DE PEDIDO', bold_n)
        sheet.write(2, 1, 'FECHA DE FACTURA', bold_n)
        sheet.write(2, 2, 'CLIENTE', bold_n)
        sheet.write(2, 3, 'EMAIL', bold_n)
        sheet.write(2, 4, 'TELEFONO', bold_n)
        sheet.write(2, 5, 'PRODUCTOS', bold_n)
        sheet.write(2, 6, 'CANTIDAD', bold_n)

        for obj in sales:
            ''' _logger.info("Fecha de factura")
            _logger.info(obj.invoice_fecha)
            print("Fecha de factura: ", obj.invoice_fecha) '''

            sheet.write(row, 0, obj.date_order, date_style)
            sheet.write(row, 1, obj.invoice_fecha, date_style)
            sheet.write(row, 2, obj.partner_id.name, bold_sn)
            sheet.write(row, 3, obj.email, bold_sn)
            sheet.write(row, 4, obj.phone, bold_sn)
            for line in obj.order_line:
                sheet.write(row, 5, line.product_id.name, bold_sn)
                sheet.write(row, 6, line.product_uom_qty, bold_sn)
                ''' print(row, ": ", line.product_uom_qty) '''
                row = row + 1
