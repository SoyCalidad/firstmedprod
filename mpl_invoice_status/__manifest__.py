# -*- coding: utf-8 -*-
###############################################################################
#
#    Meghsundar Private Limited(<https://www.meghsundar.com>).
#
###############################################################################
{
    'name': 'Sale Invoice Status',
    'version': '14.0.1',
    'summary': 'Sale Invoice Status',
    'description': 'Sale Invoice Status',
    'license': 'AGPL-3',
    'author': 'Meghsundar Private Limited',
    'website': 'https://meghsundar.com',
    'category': 'Sale',
    'depends': ['account','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_inherit.xml',
        'wizard/sale_move.xml'
    ],
    'images': ['static/description/banner.gif'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
