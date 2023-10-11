from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, pytz
from pytz import timezone
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, _


class InventoryStockDifferenceReport(models.AbstractModel):
    _name = 'report.xlsx_stock_summary.xlsx_stock_difference_report'
    _description = 'Inventory and Accounting stock difference XLS Report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_user_time_offset(self):
        user = self.env.user
        tz = pytz.timezone(user.tz or 'GMT') or pytz.utc
        utcnow = timezone('utc').localize(datetime.utcnow())  # generic time
        utc_time = utcnow.astimezone(pytz.utc).replace(tzinfo=None)
        user_time = utcnow.astimezone(tz).replace(tzinfo=None)
        offset = relativedelta(utc_time, user_time)  # Difference between two time zones
        return offset

    def generate_xlsx_report(self, workbook, data, docs):
        sheet = workbook.add_worksheet("Inventory & Accounting stock Difference Report")

        date = docs.date
        company_id = docs.company_id
        account_id = docs.account_id
        create_date = datetime.strptime(date.strftime('%Y-%m-%d 23:59:59'), DEFAULT_SERVER_DATETIME_FORMAT) + self._get_user_time_offset()

        format_head = workbook.add_format({
            'font_size': 18, 'align': 'center', 'bold': True, 'color': '#00A09D', 'font_name': 'Times New Roman',
            'bg_color': '#f9f9f9'
        })

        format1 = workbook.add_format(
            {'align': 'center', 'font_size': 10, 'bold': True})
        format2 = workbook.add_format(
            {'align': 'left', 'font_size': 10})
        format3 = workbook.add_format(
            {'align': 'right', 'font_size': 10})
        format4 = workbook.add_format({
            'font_size': 14, 'align': 'center', 'bold': True, 'color': '#666666', 'font_name': 'Times New Roman',
            'bg_color': '#f9f9f9'
        })
        format5 = workbook.add_format({
            'font_size': 12, 'align': 'vcenter', 'bold': True, 'font_color': 'white', 'bg_color': '#875A7B',
            'font_name': 'Times New Roman'
        })
        format4.set_align('vcenter')

        sheet.merge_range('A1:J2', 'Inventory-Accounting Stock Difference', format_head)
        sheet.merge_range('A3:J4', company_id.name, format4)
        sheet.merge_range('A5:J6', 'Date: %s' % date, format4)

        sheet.merge_range('A7:A8', 'Product ID', format5)
        sheet.merge_range('B7:B8', 'Product Name', format5)
        sheet.merge_range('C7:C8', 'Archived', format5)
        sheet.merge_range('D7:D8', 'Unit', format5)
        sheet.merge_range('E7:F7', 'Inventory Part', format5)
        sheet.write('E8', 'Qty', format1)
        sheet.write('F8', 'Value', format1)
        sheet.merge_range('G7:H7', 'Accounting Part', format5)
        sheet.write('G8', 'Qty', format1)
        sheet.write('H8', 'Value', format1)
        sheet.merge_range('I7:J7', 'Difference', format5)
        sheet.write('I8', 'Qty', format1)
        sheet.write('J8', 'Value', format1)

        query = """
            SELECT * FROM (
            WITH product_info AS (
                SELECT
                    p.id AS product_id,
                    p.barcode,
                    uom.name as uom,
                    p.active 
                FROM
                    product_product AS p
                    JOIN product_template AS t ON p.product_tmpl_id = t.id
                    JOIN uom_uom AS uom ON t.uom_id = uom.id
                WHERE
                    t.company_id = %s
            ),
            stock_info AS (
                SELECT
                    layer.product_id,
                    SUM(layer.quantity) AS stock_quantity,
                    SUM(layer.value) AS stock_value
                FROM
                    stock_valuation_layer AS layer
                WHERE
                    layer.create_date <= %s
                GROUP BY
                    layer.product_id
            ),
            account_info AS (
                SELECT
                    line.product_id,
                    SUM(line.quantity) AS account_quantity,
                    (SUM(line.debit) - SUM(line.credit)) AS account_value
                FROM
                    account_move_line AS line
                    JOIN account_move AS move ON line.move_id = move.id
                WHERE
                    line.account_id = %s
                    AND move.company_id = %s
                    AND move.state = 'posted'
                    AND move.date <= %s
                GROUP BY
                    line.product_id
            )
            SELECT
                pi.product_id,
                pi.barcode,
                pi.uom,
                pi.active, 
                COALESCE(si.stock_quantity, 0) AS stock_quantity,
                COALESCE(si.stock_value, 0) AS stock_value,
                COALESCE(ai.account_quantity, 0) AS account_quantity,
                COALESCE(ai.account_value, 0) AS account_value,
                ROUND(COALESCE(si.stock_quantity, 0) - COALESCE(ai.account_quantity, 0)) AS stock_difference,
                ROUND(COALESCE(si.stock_value, 0) - COALESCE(ai.account_value, 0)) AS value_difference
            FROM
                product_info AS pi
                LEFT JOIN stock_info AS si ON pi.product_id = si.product_id
                LEFT JOIN account_info AS ai ON pi.product_id = ai.product_id
            ) AS t1 WHERE t1.stock_difference != 0 OR t1.value_difference != 0
        """
        params = (company_id.id, create_date, account_id.id, company_id.id, date)

        self.env.cr.execute(query, params)
        result = self.env.cr.dictfetchall()

        available_product_obj = self.env['product.product'].browse([item['product_id'] for item in result])
        product_name_list = available_product_obj.read(['display_name'])

        row = 9
        for line in result:
            row_no = str(row)
            product_id = line['product_id']
            product_name = next(item['display_name'] for item in product_name_list if item['id'] == product_id)
            uom = line['uom']
            active = line['active']
            stock_quantity = line['stock_quantity']
            stock_value = line['stock_value']
            account_quantity = line['account_quantity']
            account_value = line['account_value']
            stock_difference = line['stock_difference']
            value_difference = line['value_difference']

            sheet.write('A' + row_no, product_id, format2)
            sheet.write('B' + row_no, product_name, format2)
            sheet.write('C' + row_no, True if not active else '', format2)
            sheet.write('D' + row_no, uom, format2)
            sheet.write('E' + row_no, stock_quantity, format3)
            sheet.write('F' + row_no, stock_value, format3)
            sheet.write('G' + row_no, account_quantity, format3)
            sheet.write('H' + row_no, account_value, format3)
            sheet.write('I' + row_no, stock_difference, format3)
            sheet.write('J' + row_no, value_difference, format3)

            row += 1

        # SET WIDTH AND HEIGHT FOR ROWS AND COLUMNS
        sheet.set_row(0, 30)
        sheet.set_column('A:A', 10)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 10)
        sheet.set_column('D:D', 10)
        sheet.set_column('E:E', 15)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:H', 20)
        sheet.set_column('I:I', 15)
        sheet.set_column('J:J', 20)
