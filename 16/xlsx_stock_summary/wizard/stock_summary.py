# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockSummary(models.TransientModel):
    _name = 'stock.summary'
    _description = 'Stock Summary in a period'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    company_id = fields.Many2one("res.company",
                                 default=lambda self: self.env.company)

    def action_print_stock(self):
        data = {}
        data = self.read(['from_date',
                          'to_date'])[0]
        return self.env.ref(
            'xlsx_stock_summary.xlsx_stock_summary_report').report_action(
            self, data=data, config=False)
