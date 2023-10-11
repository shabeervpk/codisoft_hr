# -*- coding: utf-8 -*-
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Excel Stock Summary",
    "summary": "Report to get stock summary",
    "version": "15.0.0.1",
    "author": "Akhilesh N S",
    "license": "LGPL-3",
    "category": "Warehouse",
    "depends": ['report_xlsx', 'stock', 'stock_account'],
    "data": [
        'security/ir.model.access.csv',
        'wizard/report.xml',
        'wizard/view_stock_summary.xml',
        'wizard/view_stock_difference.xml',
    ],
    "installable": True,
}