# -*- coding: utf-8 -*-

from odoo import  fields, models


class StockInvAccountDifference(models.TransientModel):
    _name = 'stock.inv.account.difference'
    _description = 'Difference between stock and account part'

    date = fields.Date('Difference on Date', required=True, default=fields.Date.today())
    account_id = fields.Many2one('account.account', string='Stock Valuation account', default=lambda self: self.env.company.property_stock_valuation_account_id,  required=1)
    company_id = fields.Many2one("res.company",
                                 default=lambda self: self.env.company, required=True)

    def action_print_difference(self):
        data = self.read(['date',
                          'company_id'])[0]
        return self.env.ref(
            'xlsx_stock_summary.action_inv_acc_stock_difference_report').report_action(
            self, data=data, config=False)
