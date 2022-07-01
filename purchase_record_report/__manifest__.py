{
    'name': 'Registro de compras',
    'version': '13.0.1.0.0',
    'summary': "Registro de Compras (Formato SUNAT)",
    'category': 'Account',
    'author': 'Soy Calidad',
    'maintainer': 'Soy Calidad',
    'company': 'Soy Calidad',
    'depends': [
            'account',
            'report_xlsx',
            'l10n_pe_edi_odoofact'
    ],
    'data': [
        'data/sunat_chart_11.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
