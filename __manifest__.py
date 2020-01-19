# -*- coding: utf-8 -*-
{
    'name': "Financial Statement Indonesia",

    'summary': """
        Laporan Keuangan Indonesia Full""",

    'description': """
        Long description of module's purpose
    """,

    
    'author': 'firmanrizaldiyusup@gmail.com',
    'website': 'http://www.vitraining.com',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/template.xml',
        'views/assets.xml',
        'data/vit_financial_statements.csv',
        'data2/vit_financial_statements.csv',
    ],
}