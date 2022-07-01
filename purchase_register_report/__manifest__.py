{
    'name': 'Registro de Compras y Ventas',
    'version': '1.0',
    'description': 'Reporte de Registro de Compras y Ventas en Formato SUNAT',
    'summary': 'Muestra el Registro de Compras y Ventas como un reporte en ODOO',
    'author': 'Luis Vargas',
    'website': '',
    'license': 'LGPL-3',
    'category': 'accounting',
    'depends': [
        'account',
        'financial_state_report',
    ],
    'data': [ 'security/ir.model.access.csv',
        'reports/purchase_register_report_views.xml',
        'reports/sale_register_report_views.xml'
    ],
    'demo': [
        ''
    ],
    'auto_install': True,
    'application': True,
}