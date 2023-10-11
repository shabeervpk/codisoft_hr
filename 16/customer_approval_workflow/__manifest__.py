# -*- coding: utf-8 -*-
{
    "name": "Contact Approval Workflow",
    'summary': 'Contact Approval workflow',
    "description": "This module will allows you to approve or refuse Contact (Customer/Supplier) only by Contact Manager.",

    'author': 'iPredict IT Solutions Pvt. Ltd.',
    'website': 'http://ipredictitsolutions.com',
    "support": "ipredictitsolutions@gmail.com",

    "version": "16.0.0.1.0",
    "category": "Extra Tools",
    "depends": ['contacts', 'mail'],

    "data": [
        'security/res_partner_security.xml',
        'data/customer_approval_mail_template.xml',
        'views/partner_view.xml',
    ],

    'license': "OPL-1",
    "currency": "EUR",
    "price": 20.00,
    "installable": True,
    "images": ['static/description/main.png'],
}
