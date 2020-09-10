# -*- coding: utf-8 -*-

{
    'name': 'EBizCharge Payment Acquirer',
    'category': 'Accounting',
    'summary': 'Payment Acquirer: EBizCharge Implementation',
    'version': '1.0',
    'description': """EBizCharge Payment Acquirer""",
    'depends': ['payment'],
    'qweb': [
        'static/src/xml/custom.xml',
    ],
    'data': [
        'views/payment_views.xml',
        'views/payment_ebizcharge_templates.xml',
        # 'views/button.xml',
        'data/payment_acquirer_data.xml',
        'wizard/message_wizard.xml'
    ],
    'installable': True,
    'post_init_hook': 'create_missing_journal_for_acquirers',
}
