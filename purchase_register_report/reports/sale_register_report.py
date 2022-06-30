from odoo import api, fields, models, tools


class PurchaseRegister(models.Model):
    _name = 'sale.register.report'
    _auto = False
    _description = 'Registro de Compras'
    _rec_name = 'id'

    name = fields.Char(string='Código Único de Operación', readonly=True)
    date = fields.Date(string='Fecha de Emisión', readonly=True)
    date_due = fields.Date(string='Fecha de Vencimiento', readonly=True)
    type_document_id = fields.Many2one(
        'einvoice.catalog.01', string='Tipo de Documento', readonly=True)
    # numero = fields.Char(string='Número', readonly=True)
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', readonly=True)
    amount_untaxed = fields.Float(
        string='Base imponible', digits=(16, 4), readonly=True)
    amount_tax = fields.Float(string='IGV', digits=(16, 4), readonly=True)
    amount_total = fields.Float(
        string='Importe Total', digits=(16, 4), readonly=True)
    l_name = fields.Char(string='Razón Social', readonly=True)
    vat = fields.Char(string='Documento de Identidad', readonly=True)
    catalog_06_id = fields.Many2one(
        'einvoice.catalog.06', string='Tipo', readonly=True)
    reversed_entry_id = fields.Many2one('account.move', string='Documento Modificado')

    def generate_ple(self):
        print('Aiudaaaa')

    def _select(self):
        return """
            SELECT
                m.id,
                m.name,
                m.date,
                m.invoice_date_due,
                m.type_document_id,
                m.partner_id,
                m.amount_untaxed,
                m.amount_tax,
                m.amount_total,
                l.id as l_id,
                l.name as l_name,
                l.vat,
                m.reversed_entry_id
        """

    def _from(self):
        return """
            FROM account_move AS m
        """

    def _join(self):
        return """
            LEFT JOIN res_partner AS l ON m.partner_id = l.id
        """

    def _where(self):
        return """
            WHERE
                (m.type = 'out_invoice' OR m.type = 'out_refund')
                AND m.state in ('open', 'paid') AND
                date_part('year', m.date) = date_part('year', CURRENT_DATE)
        """

    def _group_by(self):
        return """
            GROUP BY
                m.id,
                l_id
        """

    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by())
        )
