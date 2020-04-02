# Copyright 20120 Shabeer VPK
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.onchange('holiday_status_id')
    def recompute_no_days(self):
        self._onchange_leave_dates()

    def _get_number_of_days(self, date_from, date_to, employee_id):
        context_data = {'employee_id' : employee_id,
                        'from_leave_request': True,
                        'exclude_weekends' : False}

        if (self.holiday_status_id.exclude_weekends or
                not self.holiday_status_id):
            context_data['exclude_weekends'] = True

        instance = self.with_context(context_data)
        return super(HrLeave, instance)._get_number_of_days(
            date_from,
            date_to,
            employee_id,
        )
