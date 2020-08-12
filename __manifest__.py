# -*- coding: utf-8 -*-

{
    'name': 'EBizCharge Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: EBizCharge Implementation',
    'version': '1.0',
    'description': """EBizCharge Payment Acquirer""",
    'depends': ['payment'],
    'data': [
        'views/payment_views.xml',
        'views/payment_ebizcharge_templates.xml',
        'data/payment_acquirer_data.xml',
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
