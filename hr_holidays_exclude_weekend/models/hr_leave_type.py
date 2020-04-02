# Copyright 2020 Shabeer VPK
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    exclude_weekends = fields.Boolean(
        string='Exclude Weekends',
        default=True,
        help=(
            'If enabled, weekends are skipped in leave days'
            ' calculation.'
        ),
    )
