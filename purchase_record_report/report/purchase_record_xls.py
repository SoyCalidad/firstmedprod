# -*- coding: utf-8 -*-
import calendar
import time
from collections import defaultdict
from datetime import datetime, timedelta

import pytz
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import models


class InvoiceReportXls(models.AbstractModel):
    _name = 'report.purchase_report_sunat_xls.xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):

        if lines.type_report == 'purchase':
            self.purchase_report(workbook, data, lines)
        elif lines.type_report == 'sale':
            self.sale_report(workbook, data, lines)
        elif lines.type_report == 'invoice':
            self.invoice_report(workbook, data, lines)

    def purchase_report(self, workbook, data, lines):
        comp = lines.company_id.name

        sheet = workbook.add_worksheet('Registro de Compras')

        sheet.set_column(0, 2, 9)  # corr y fechas
        sheet.set_column(3, 3, 10)  # tipo
        sheet.set_column(4, 5, 8)  # serie numero
        sheet.set_column(6, 6, 10)  # tipo
        sheet.set_column(7, 7, 15)  # prov numero
        sheet.set_column(8, 8, 40)  # prov razon social
        sheet.set_column(9, 15, 12)  # base imponible igv y total

        format21 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'text_wrap': True, 'valign': 'vcenter'})
        format21_left = workbook.add_format(
            {'font_size': 10, 'align': 'left', 'bold': True})

        format21_blue = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': '#68a3fc'})
        format21_green = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'bold': True, 'fg_color': '#85de8e'})

        font_size_8_c = workbook.add_format(
            {'font_size': 8, 'align': 'center'})
        font_size_8_l = workbook.add_format({'font_size': 8, 'align': 'left'})
        font_size_8_r_b = workbook.add_format(
            {'font_size': 8, 'align': 'right', 'bold': True})
        monetary_size_8_r = workbook.add_format(
            {'num_format': '"S/." #,##0.00', 'font_size': 8, 'align': 'right', 'valign': 'vcenter'})

        user = self.env['res.users'].browse(self.env.uid)
        tz = pytz.timezone(user.tz)
        time = pytz.utc.localize(datetime.now()).astimezone(tz)

        format21.set_border()
        format21_blue.set_border()
        format21_green.set_border()
        font_size_8_c.set_border()

        prod_row = 6
        prod_col = 0

        sheet.merge_range(0, 0, 0, 1, 'REGISTRO DE COMPRAS', format21_left)
        sheet.write(2, 0, 'PERIODO', format21_left)
        sheet.write(2, 1, str(lines.month) + '/' +
                    str(lines.year), format21_left)
        sheet.write(3, 0, 'RUC', format21_left)
        sheet.write(3, 1, lines.company_id.vat, format21_left)
        sheet.write(4, 0, 'RAZÓN SOCIAL', format21_left)
        sheet.write(4, 1, lines.company_id.partner_id.name, format21_left)

        sheet.merge_range(
            6, 0, 8, 0, 'NÚMERO CORRELATIVO DEL REGISTRO O CÓDIGO ÚNICO DE LA OPERACIÓN', format21)
        sheet.merge_range(
            6, 1, 8, 1, 'FECHA DE EMISIÓN DEL COMPROBANTE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(
            6, 2, 8, 2, 'FECHA DE VENCIMIENTO DEL COMPROBATE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(
            6, 3, 6, 5, 'COMPROBANTE DE PAGO O DOCUMENTO', format21)
        sheet.merge_range(7, 3, 8, 3, 'TIPO', format21)
        sheet.merge_range(
            7, 4, 8, 4, 'SERIE O CÓDIGO DE LA DEPENDENCIA ADUANERA', format21)
        sheet.merge_range(
            7, 5, 8, 5, 'AÑO DE EMISIÓN DE LA DUA O DSI', format21)
        sheet.merge_range(6, 6, 8, 6, 'N° DE COMPROBANTE DE PAGO, DOCUMENTO, N° DE ORDEN DEL FORMULARIO FÍSICO O VIRTUAL, N° DE DUA, DSI O LIQUIDACIÓN DE COBRANZA U OTROS DOCUMENTOS EMITIDOS POR SUNAT PARA ACREDITAR EL CRÉDITO FISCAL DE IMPORTACIÓN', format21)
        sheet.merge_range(6, 7, 6, 9, 'INFORMACIÓN DEL PROVEEDOR', format21)
        sheet.merge_range(7, 7, 7, 8, 'DOCUMENTO DE IDENTIDAD', format21)
        sheet.write(8, 7, 'TIPO', format21)
        sheet.write(8, 8, 'NÚMERO', format21)
        sheet.merge_range(
            7, 9, 8, 9, 'APELLIDOS Y NOMBRES, DENOMINACIÓN O RAZÓN SOCIAL', format21)
        sheet.merge_range(
            6, 10, 6, 11, ' ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACIÓN', format21)
        sheet.merge_range(7, 10, 8, 10, 'BASE IMPONIBLE', format21)
        sheet.merge_range(7, 11, 8, 11, 'IGV', format21)
        sheet.merge_range(
            6, 12, 6, 13, ' ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES GRAVADAS Y/O DE EXPORTACIÓN Y A OPERACIONES NO GRAVADAS', format21)
        sheet.merge_range(7, 12, 8, 12, 'BASE IMPONIBLE', format21)
        sheet.merge_range(7, 13, 8, 13, 'IGV', format21)
        sheet.merge_range(
            6, 14, 6, 15, ' ADQUISICIONES GRAVADAS DESTINADAS A OPERACIONES NO GRAVADAS', format21)
        sheet.merge_range(7, 14, 8, 14, 'BASE IMPONIBLE', format21)
        sheet.merge_range(7, 15, 8, 15, 'IGV', format21)
        sheet.merge_range(
            6, 16, 8, 16, 'VALOR DE LAS ADQUISICIONES NO GRAVADAS', format21)
        sheet.merge_range(6, 17, 8, 17, 'ISC', format21)
        sheet.merge_range(6, 18, 8, 18, 'OTROS TRIBUTOS Y CARGOS', format21)
        sheet.merge_range(6, 19, 8, 19, 'IMPORTE TOTAL', format21)
        sheet.merge_range(
            6, 20, 8, 20, 'N° DE COMPROBANTE DE PAGO EMITIDO POR SUJETO NO DOMICILIADO', format21)
        sheet.merge_range(
            6, 21, 6, 22, 'CONSTANCIA DE DEPOSITO DE DETRACCIÓN', format21)
        sheet.merge_range(7, 21, 8, 21, 'NÚMERO', format21)
        sheet.merge_range(7, 22, 8, 22, 'FECHA DE EMISIÓN', format21)
        sheet.merge_range(6, 23, 8, 23, 'TIPO DE CAMBIO', format21)
        sheet.merge_range(
            6, 24, 6, 27, 'REFERENCIA DE COMPROBANTE DE PAGO O DOCUMENTO ORIGINAL QUE MODIFICA', format21)
        sheet.merge_range(7, 24, 8, 24, 'FECHA', format21)
        sheet.merge_range(7, 25, 8, 25, 'TIPO', format21)
        sheet.merge_range(7, 26, 8, 26, 'SERIE', format21)
        sheet.merge_range(
            7, 27, 8, 27, 'N° DE COMPROBANTE DE PAGO O DOCUMENTO', format21)

        # Data
        month = int(lines.month)
        year = int(lines.year)
        days = calendar.monthrange(year, month)
        init_date = datetime(year, month, 1)
        end_date = datetime(year, month, days[1])

        invoices = self.env['account.move'].search([
            ('move_type', 'in', ('in_invoice', 'in_refund')),
            ('date', '>=', init_date),
            ('date', '<=', end_date),
            ('state', 'in', ['posted', 'cancel']),
            ('company_id', '=', lines.company_id.id),
        ], order="date asc")

        # Data Render

        entrie_row = 9
        total_untaxed = total_igv = total_isc = total_total = 0

        for invoice in invoices:
            currency_rate = invoice.env['res.currency.rate'].search([
                ('name', '<=', invoice.date),
                ('currency_id', '=', invoice.currency_id.id),
            ], order='name desc', limit=1)
            res = ''
            refund_date = ''
            refund_document_type_code = ''
            refund_number = ''
            refund_serie = ''
            if currency_rate:
                res = "{0:.3f}".format(currency_rate.rate)
            else:
                res = "{0:.3f}".format(invoice.currency_id.rate)
            
            try:
                serie, numero = invoice.name.split('-')
            except:
                serie = numero = '-'

            refund = invoice.reversed_entry_id
            if refund:
                refund_date = refund.invoice_date.strftime(
                    '%d/%m/%Y') if refund.invoice_date else ''
                # 'refund.type_document_id.code'
                refund_document_type_code = refund.l10n_pe_edi_reversal_type_id.name
                try:
                    refund_serie, refund_number = refund.name.split('-')
                except:
                    refund_serie = refund_number = '-'
                
            invoice_date = invoice.invoice_date.strftime(
                '%d/%m/%Y') if invoice.invoice_date else ''
            invoice_date_due = invoice.invoice_date_due.strftime(
                '%d/%m/%Y') if invoice.invoice_date_due else ''

            sheet.write(entrie_row, 0, invoice.id, font_size_8_c)
            sheet.write(entrie_row, 1, invoice_date, font_size_8_c)
            sheet.write(entrie_row, 2, invoice_date_due, font_size_8_c)
            sheet.write(entrie_row, 3, invoice.l10n_latam_document_type_id.name, font_size_8_c)
            sheet.write(entrie_row, 4,
                        invoice.customs_dependency.code, font_size_8_c)
            sheet.write(entrie_row, 5, invoice.dua_year, font_size_8_c)
            sheet.write(entrie_row, 6, invoice.name, font_size_8_c)
            partner_identification_type = invoice.partner_id.l10n_latam_identification_type_id.name if invoice.state == 'posted' else '0'
            partner_vat = invoice.partner_id.vat if invoice.state == 'posted' else '0'
            partner_name = invoice.partner_id.name if invoice.state == 'posted' else 'COMPROBANTE ANULADO'
            sheet.write(entrie_row, 7, partner_identification_type, font_size_8_c)
            sheet.write(entrie_row, 8, partner_vat, font_size_8_c)
            sheet.write(entrie_row, 9, partner_name, font_size_8_c)
            if invoice.move_type == 'in_refund':
                multiplier = -1
            elif invoice.state == 'cancel':
                multiplier = 0
            else:
                multiplier = 1
            amount_untaxed = invoice.amount_untaxed * multiplier
            l10n_pe_edi_amount_isc = invoice.l10n_pe_edi_amount_isc * multiplier
            l10n_pe_edi_amount_igv = invoice.l10n_pe_edi_amount_igv * multiplier
            amount_total = invoice.amount_total * multiplier
            total_untaxed += amount_untaxed
            total_igv += l10n_pe_edi_amount_igv
            total_isc += l10n_pe_edi_amount_isc
            total_total += amount_total
            sheet.write(entrie_row, 10, amount_untaxed, font_size_8_c)
            sheet.write(entrie_row, 11, '', font_size_8_c)
            sheet.write(entrie_row, 12, '', font_size_8_c)
            sheet.write(entrie_row, 13, '', font_size_8_c)
            sheet.write(entrie_row, 14, '', font_size_8_c)
            sheet.write(entrie_row, 15, '', font_size_8_c)
            sheet.write(entrie_row, 16, '', font_size_8_c)
            sheet.write(entrie_row, 17, l10n_pe_edi_amount_isc, font_size_8_c)
            sheet.write(entrie_row, 18, '', font_size_8_c)
            sheet.write(entrie_row, 19, amount_total, font_size_8_c)
            sheet.write(entrie_row, 20, '', font_size_8_c)
            sheet.write(entrie_row, 21, '', font_size_8_c)
            sheet.write(entrie_row, 22, '', font_size_8_c)
            sheet.write(entrie_row, 23, res, font_size_8_c)
            sheet.write(entrie_row, 24, refund_date, font_size_8_c)
            sheet.write(entrie_row, 25,
                        refund_document_type_code, font_size_8_c)
            sheet.write(entrie_row, 26, refund_serie, font_size_8_c)
            sheet.write(entrie_row, 27, refund_number, font_size_8_c)
            entrie_row += 1

        # Format

        sheet.set_column('A:AB', 30)
