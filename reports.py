import io
import csv
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def export_transactions_excel(transactions):
    """
    خروجی Excel با قالب‌بندی رنگی، هدرهای بولد، جهت راست‌به‌چپ و ستون عنوان
    ارائه به صورت بافر رم موقت برای دانلود از مرورگر
    """
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    ws.title = "Transactions"
    ws.sheet_view.rightToLeft = True  # نمایش راست‌به‌چپ شیت

    headers = ["شناسه", "عنوان", "نوع", "مبلغ (تومان)", "دسته‌بندی", "توضیحات", "تاریخ"]

    # استایل هدر سفارشی
    header_fill = PatternFill(start_color="2F5597", end_color="2F5597", fill_type="solid")
    header_font = Font(name="Tahoma", size=11, bold=True, color="FFFFFF")
    align_center = Alignment(horizontal="center", vertical="center")

    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center

    # درج داده‌های تراکنش کاربر
    for t in transactions:
        t_type = "درآمد" if t.get("type") == "income" else "هزینه"
        row = [
            t.get("id", "-"),
            t.get("title", "-"),
            t_type,
            t.get("amount", 0),
            t.get("category", "-"),
            t.get("note", "-"),
            str(t.get("date", "-"))[:19]
        ]
        ws.append(row)

    # تنظیم خودکار عرض ستون‌ها و تراز وسط سلول‌ها
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 5, 14)
        for cell in col:
            if cell.row != 1:
                cell.alignment = align_center

    wb.save(output)
    output.seek(0)
    return output


def export_transactions_csv(transactions):
    """
    خروجی CSV سازگار با UTF-8-SIG جهت جلوگیری از به‌هم‌ریختگی حروف فارسی در اکسل
    """
    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["شناسه", "عنوان", "نوع", "مبلغ (تومان)", "دسته‌بندی", "توضیحات", "تاریخ"]
    writer.writerow(headers)

    for t in transactions:
        t_type = "درآمد" if t.get("type") == "income" else "هزینه"
        writer.writerow([
            t.get("id", "-"),
            t.get("title", "-"),
            t_type,
            t.get("amount", 0),
            t.get("category", "-"),
            t.get("note", "-"),
            str(t.get("date", "-"))[:19]
        ])

    bytes_output = io.BytesIO()
    bytes_output.write(output.getvalue().encode("utf-8-sig"))
    bytes_output.seek(0)
    return bytes_output


def export_transactions_pdf(transactions, username="User"):
    """
    تولید گزارش جدول PDF با ReportLab در حافظه موقت
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    elements = []

    title_style = styles["Heading1"]
    title_style.alignment = 1
    elements.append(Paragraph(f"Transaction Report - {username}", title_style))
    elements.append(Spacer(1, 20))

    table_data = [["ID", "Title", "Type", "Amount", "Category", "Date"]]
    for t in transactions:
        table_data.append([
            str(t.get("id")),
            str(t.get("title", "-"))[:15],
            str(t.get("type")),
            f"{int(t.get('amount', 0)):,}",
            str(t.get("category")),
            str(t.get("date"))[:10]
        ])

    table = Table(table_data, colWidths=[35, 120, 60, 80, 100, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2F5597')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
