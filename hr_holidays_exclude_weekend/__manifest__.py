# Copyright 2020 Shabeer VPK <shabeer@codisoft.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Holidays Weekend Exclude',
    'version': '12.0.1.',
    'license': 'AGPL-3',
    'category': 'Human Resources',
    'author': "Codisoft",
    'summary': "Add an option to leave type for excluding weekend / rest days.",
    'website': 'http://www.codisoft.com',
    'depends': [
        'hr_holidays',
    ],
    'data': [
        'views/hr_leave_type.xml'
    ],
    'images': ["static/description/banner.jpg"],
    'installable': True,
}
