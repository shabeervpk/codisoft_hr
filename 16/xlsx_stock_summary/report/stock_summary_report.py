from odoo import models
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class InventoryStockReport(models.AbstractModel):
    _name = 'report.xlsx_stock_summary.xlsx_stock_summary_report'
    _description = 'Stock Summary XLS Report'
    _inherit = 'report.report_xlsx.abstract'

    def _get_stock_move_summary(self, company_id, from_date, to_date, next_date):
        stock_summary_query = """
                SELECT
                    stock.product_id,stock.uom,stock.brand,stock.category,
                    ROUND(stock.opening_qty,3) AS opening_qty,
                    ROUND(COALESCE(stock.opening_value / NULLIF(stock.opening_qty, 0), 0),3) AS opening_rate,
                    ROUND(stock.opening_value,3) AS opening_value,
                    ROUND(stock.incoming_qty,3) AS incoming_qty,
                    ROUND(COALESCE(stock.incoming_value / NULLIF(stock.incoming_qty, 0), 0),3) AS incoming_rate,
                    ROUND(stock.incoming_value,3) AS incoming_value,
                    ROUND(stock.outgoing_qty,3) AS outgoing_qty,
                    ROUND(COALESCE(stock.outgoing_value / NULLIF(stock.outgoing_qty, 0), 0),3) AS outgoing_rate,
                    ROUND(stock.outgoing_value, 3) AS outgoing_value,
                    ROUND(stock.exceptional_qty,3) AS exceptional_qty,
                    ROUND(COALESCE(stock.exceptional_value / NULLIF(stock.exceptional_qty, 0), 0),3) AS exceptional_rate,
                    ROUND(stock.exceptional_value, 3) AS exceptional_value,
                    ROUND(stock.closing_qty,3) AS closing_qty,
                    ROUND(COALESCE(stock.closing_value / NULLIF(stock.closing_qty, 0), 0),3) AS closing_rate,
                    ROUND(stock.closing_value, 3) AS closing_value, 
                    ROUND(account.invoice_quantity,3) AS invoice_quantity,
                    ROUND(COALESCE(account.invoice_amount / NULLIF(account.invoice_quantity, 0), 0),3) AS invoice_rate,
                    ROUND(account.invoice_amount, 3) AS invoice_amount
                FROM
                    (
                        SELECT
                            p.id AS product_id, uom.name AS uom, brand.name AS brand, category.complete_name AS category,
                            ROUND(SUM(CASE WHEN layer.create_date::date < %s THEN layer.quantity ELSE 0 END), 3) AS opening_qty,
                            ROUND(SUM(CASE WHEN layer.create_date::date < %s THEN layer.value ELSE 0 END), 3) AS opening_value,
                            ROUND(SUM(CASE WHEN layer.create_date::date BETWEEN %s AND %s AND layer.quantity > 0 THEN layer.quantity ELSE 0 END), 3) AS incoming_qty,
                            ROUND(SUM(CASE WHEN layer.create_date::date between %s AND %s and layer.value > 0 THEN layer.value ELSE 0 END), 3) AS incoming_value,
                            ROUND(SUM(CASE WHEN layer.create_date::date between %s AND %s AND layer.quantity < 0 AND loc.usage != 'inventory' THEN layer.quantity ELSE 0 END), 3) AS outgoing_qty,
                            ROUND(SUM(CASE WHEN layer.create_date::date between %s AND %s AND layer.value < 0 AND loc.usage != 'inventory' THEN layer.value ELSE 0 END), 3) AS outgoing_value,
                            ROUND(SUM(CASE WHEN layer.create_date::date between %s AND %s AND layer.quantity < 0 AND loc.usage = 'inventory' THEN layer.quantity ELSE 0 END), 3) AS exceptional_qty,
                            ROUND(SUM(CASE WHEN layer.create_date::date between %s AND %s AND layer.value < 0 AND loc.usage = 'inventory' THEN layer.value ELSE 0 END), 3) AS exceptional_value,
                            ROUND(SUM(CASE WHEN layer.create_date::date < %s THEN layer.quantity ELSE 0 END), 3) AS closing_qty,
                            ROUND(SUM(CASE WHEN layer.create_date::date < %s THEN layer.value ELSE 0 END), 3) AS closing_value
                        FROM
                            product_product p
                            JOIN product_template t ON t.id=p.product_tmpl_id
                            JOIN uom_uom uom ON t.uom_id=uom.id
                            LEFT JOIN product_brand brand ON t.product_brand_id=brand.id
                            LEFT JOIN product_category category ON t.categ_id=category.id
                            LEFT JOIN stock_valuation_layer layer ON p.id=layer.product_id 
                            LEFT JOIN stock_move sm ON layer.stock_move_id=sm.id 
                            LEFT JOIN stock_location loc on sm.location_dest_id=loc.id 
                        WHERE
                            t.company_id = %s AND t.type = 'product'
                        GROUP BY
                            p.id, uom.name, brand.name, category.complete_name
                    ) AS stock
                    LEFT JOIN 
                    (
                        SELECT 
                            l.product_id, (SUM(l.credit) - SUM(l.debit)) AS invoice_amount, 
                            ROUND(SUM(CASE WHEN m.move_type='out_refund' THEN l.quantity * -1 ELSE l.quantity END), 3) AS invoice_quantity -- considering credit note quantity as -ve because it dicrease income
                        FROM 
                            account_move_line l
                            JOIN account_move m ON l.move_id=m.id
                        WHERE
                            m.company_id=%s AND m.move_type in ('out_invoice', 'out_refund') AND m.state='posted' AND m.date BETWEEN %s AND %s AND l.exclude_from_invoice_tab=false AND l.product_id is not null 
                        GROUP BY 
                            l.product_id
                    ) account 
                    ON stock.product_id =account.product_id
                    """

        params = (
        from_date, from_date, from_date, to_date, from_date, to_date, from_date, to_date, from_date, to_date, from_date,
        to_date, from_date, to_date, next_date, next_date, company_id, company_id, from_date, to_date)
        self.env.cr.execute(stock_summary_query, params)
        stock_query = self.env.cr.dictfetchall()
        return stock_query

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet("Stock Move Summary Report")
        from_date = lines.from_date
        company_id = lines.company_id.id
        to_date = lines.to_date
        next_date = (lines.to_date) + timedelta(days=1)
        # 1. For First Heading
        main_head = workbook.add_format({
            'font_size': 18, 'align': 'center', 'bold': True, 'color': '#00A09D', 'font_name': 'Times New Roman',
            'bg_color': '#f9f9f9'
        })
        # 2. For Second Heading
        sub_head = workbook.add_format({
            'font_size': 14, 'align': 'center', 'bold': True, 'color': '#666666', 'font_name': 'Times New Roman',
            'bg_color': '#f9f9f9'
        })
        sub_head.set_align('vcenter')
        format1 = workbook.add_format(
            {'align': 'center', 'font_size': 10, 'bold': True})
        format_left = workbook.add_format(
            {'align': 'left', 'font_size': 10})
        format_right = workbook.add_format(
            {'align': 'right', 'font_size': 10})
        format4 = workbook.add_format(
            {'align': 'center', 'font_size': 10, 'color': '#744b66', 'bold': True})
        format_neg = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'color': '#ff0000'})
        format_zero = workbook.add_format(
            {'align': 'right', 'font_size': 10, 'color': '#d7d2d2'})

        sheet.merge_range('A1:W1', 'Stock Move Summary', main_head)
        sheet.merge_range('A2:W2', self.env.company.name, sub_head)
        sheet.merge_range('A3:W3', 'Date: %s to %s' % (from_date, to_date), format1)

        sheet.merge_range('A4:A5', 'Prod ID', format1)
        sheet.merge_range('B4:B5', 'Product Name', format1)
        sheet.merge_range('C4:C5', 'Brand', format1)
        sheet.merge_range('D4:D5', 'Category', format1)
        sheet.merge_range('E4:E5', 'Unit', format1)

        sheet.merge_range('F4:H4', 'Opening', format1)
        sheet.write('F5', 'Qty', format4)
        sheet.write('G5', 'Rate', format4)
        sheet.write('H5', 'Value', format4)

        sheet.merge_range('I4:K4', 'Incoming', format1)
        sheet.write('I5', 'Qty', format4)
        sheet.write('J5', 'Rate', format4)
        sheet.write('K5', 'Value', format4)

        sheet.merge_range('L4:N4', 'Outgoing', format1)
        sheet.write('L5', 'Qty', format4)
        sheet.write('M5', 'Rate', format4)
        sheet.write('N5', 'Value', format4)

        sheet.merge_range('O4:Q4', 'Exception', format1)
        sheet.write('O5', 'Qty', format4)
        sheet.write('P5', 'Rate', format4)
        sheet.write('Q5', 'Value', format4)

        sheet.merge_range('R4:T4', 'Closing', format1)
        sheet.write('R5', 'Qty', format4)
        sheet.write('S5', 'Rate', format4)
        sheet.write('T5', 'Value', format4)

        sheet.merge_range('U4:W4', 'Invoice', format1)
        sheet.write('U5', 'Qty', format4)
        sheet.write('V5', 'Rate', format4)
        sheet.write('W5', 'Value', format4)

        stock_move_summary = self._get_stock_move_summary(company_id, from_date, to_date, next_date)

        available_product_obj = self.env['product.product'].browse(
            [item.get('product_id') for item in stock_move_summary])
        product_name_list = available_product_obj.read(['display_name'])

        # Map column positions to corresponding letters
        column_mapping = {
            'product_id': 'A',
            'product_name': 'B',
            'brand': 'C',
            'category': 'D',
            'uom': 'E',
        }
        column_mapping_numbers = {
            'opening_qty': 'F',
            'opening_rate': 'G',
            'opening_value': 'H',
            'incoming_qty': 'I',
            'incoming_rate': 'J',
            'incoming_value': 'K',
            'outgoing_qty': 'L',
            'outgoing_rate': 'M',
            'outgoing_value': 'N',
            'exceptional_qty': 'O',
            'exceptional_rate': 'P',
            'exceptional_value': 'Q',
            'closing_qty': 'R',
            'closing_rate': 'S',
            'closing_value': 'T',
            'invoice_quantity': 'U',
            'invoice_rate': 'V',
            'invoice_amount': 'W',
        }
        column_mapping.update(column_mapping_numbers)

        excel_row = 6
        # Iterate over the data and write to the sheet
        for data in stock_move_summary:

            values = {
                'product_id': data.get('product_id'),
                'product_name': next(
                    item['display_name'] for item in product_name_list if item['id'] == data.get('product_id')),
                'uom': data.get('uom'),
                'brand': data.get('brand'),
                'category': data.get('category'),
                'opening_qty': data.get('opening_qty', 0),
                'opening_rate': data.get('opening_rate', 0),
                'opening_value': data.get('opening_value', 0),
                'incoming_qty': data.get('incoming_qty', 0),
                'incoming_rate': data.get('incoming_rate', 0),
                'incoming_value': data.get('incoming_value', 0),
                'outgoing_qty': data.get('outgoing_qty', 0),
                'outgoing_rate': data.get('outgoing_rate', 0),
                'outgoing_value': data.get('outgoing_value', 0),
                'exceptional_qty': data.get('exceptional_qty', 0),
                'exceptional_rate': data.get('exceptional_rate', 0),
                'exceptional_value': data.get('exceptional_value', 0),
                'closing_qty': data.get('closing_qty', 0),
                'closing_rate': data.get('closing_rate', 0),
                'closing_value': data.get('closing_value', 0),
                'invoice_quantity': data.get('invoice_quantity', 0),
                'invoice_rate': data.get('invoice_rate', 0),
                'invoice_amount': data.get('invoice_amount', 0)
            }

            # Check if any value is non-zero
            if any(values[key] for key in column_mapping_numbers.keys()):
                for key, value in values.items():

                    if not value:
                        style_format = format_zero
                    elif key in list(column_mapping_numbers.keys()) and value < 0:
                        style_format = format_neg
                    elif key in list(column_mapping_numbers.keys()):
                        style_format = format_right
                    else:
                        style_format = format_left

                    column = column_mapping[key]
                    sheet.write(column + str(excel_row), value, style_format)

                excel_row += 1

        # SET WIDTH AND HEIGHT FOR ROWS AND COLUMNS
        sheet.set_row(0, 30)
        sheet.set_column('B:B', 30)
        sheet.set_column('C:C', 20)
        sheet.set_column('D:D', 20)
        sheet.set_column('E:Q', 10)
