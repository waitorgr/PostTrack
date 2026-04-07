"""
PDF генератор — ReportLab.
Всі звіти мають спільний стиль: шапка, підвал, таблиці.
Підтримує кирилицю через DejaVuSans.
"""

import io
from datetime import datetime
from pathlib import Path

from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable,
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.utils import ImageReader

# Кольори
NAVY = colors.HexColor("#1A3C6E")
BLUE = colors.HexColor("#2563EB")
GRAY = colors.HexColor("#475569")
LGRAY = colors.HexColor("#F1F5F9")
GREEN = colors.HexColor("#16A34A")
RED = colors.HexColor("#DC2626")
WHITE = colors.white
BLACK = colors.black

FONT_REGULAR = "DejaVuSans"
FONT_BOLD = "DejaVuSans-Bold"


def _register_fonts():
    """
    Реєстрація Unicode-шрифтів для коректного відображення кирилиці.
    Очікується, що файли лежать у reports/fonts/.
    """
    registered = pdfmetrics.getRegisteredFontNames()
    if FONT_REGULAR in registered and FONT_BOLD in registered:
        return

    fonts_dir = Path(settings.BASE_DIR) / "reports" / "fonts"
    regular_path = fonts_dir / "DejaVuSans.ttf"
    bold_path = fonts_dir / "DejaVuSans-Bold.ttf"

    if not regular_path.exists() or not bold_path.exists():
        raise FileNotFoundError(
            "Не знайдено шрифти для PDF.\n"
            f"Очікувались файли:\n"
            f" - {regular_path}\n"
            f" - {bold_path}\n"
            "Додай DejaVuSans.ttf і DejaVuSans-Bold.ttf у reports/fonts/"
        )

    pdfmetrics.registerFont(TTFont(FONT_REGULAR, str(regular_path)))
    pdfmetrics.registerFont(TTFont(FONT_BOLD, str(bold_path)))


def _city_name(location):
    if not location or not getattr(location, "city", None):
        return "—"
    city = location.city
    return getattr(city, "name", str(city))


def _styles():
    _register_fonts()
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title",
            parent=base["Title"],
            fontName=FONT_BOLD,
            fontSize=16,
            textColor=NAVY,
            spaceAfter=6,
            alignment=TA_LEFT,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=11,
            textColor=GRAY,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "heading",
            parent=base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=12,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "normal",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            textColor=BLACK,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "small",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=9,
            textColor=GRAY,
        ),
        "bold": ParagraphStyle(
            "bold",
            parent=base["Normal"],
            fontName=FONT_BOLD,
            fontSize=10,
            textColor=BLACK,
        ),
        "center": ParagraphStyle(
            "center",
            parent=base["Normal"],
            fontName=FONT_REGULAR,
            fontSize=10,
            alignment=TA_CENTER,
        ),
    }


def _table_style(header_bg=NAVY):
    _register_fonts()
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LGRAY]),
        ("FONTNAME", (0, 1), (-1, -1), FONT_REGULAR),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])


def _build_pdf(elements, title, subtitle=""):
    _register_fonts()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2 * cm,
        title=title,
    )

    s = _styles()

    def on_page(canvas, doc):
        canvas.saveState()

        # Шапка
        canvas.setFillColor(NAVY)
        canvas.rect(2 * cm, A4[1] - 1.8 * cm, A4[0] - 4 * cm, 0.8 * cm, fill=1, stroke=0)

        canvas.setFillColor(WHITE)
        canvas.setFont(FONT_BOLD, 11)
        canvas.drawString(2.3 * cm, A4[1] - 1.4 * cm, "PostTrack")

        canvas.setFont(FONT_REGULAR, 9)
        canvas.drawRightString(A4[0] - 2 * cm, A4[1] - 1.4 * cm, title)

        # Підвал
        canvas.setFillColor(GRAY)
        canvas.setFont(FONT_REGULAR, 8)
        canvas.drawString(2 * cm, 1.2 * cm, f'Згенеровано: {datetime.now().strftime("%d.%m.%Y %H:%M")}')
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Сторінка {doc.page}")

        canvas.restoreState()

    header = [Paragraph(title, s["title"])]
    if subtitle:
        header.append(Paragraph(subtitle, s["subtitle"]))
    header.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=12))

    doc.build(header + elements, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
# Допоміжний рендер штрихкоду без накладання тексту на смуги
# ─────────────────────────────────────────────
def _build_barcode_image(tracking_number, max_width, max_height):
    import barcode as bc
    from barcode.writer import ImageWriter
    from reportlab.platypus import Image as RLImage

    bar_buf = io.BytesIO()
    code = bc.get("code128", tracking_number, writer=ImageWriter())
    code.write(
        bar_buf,
        options={
            "module_width": 0.22,
            "module_height": 16,
            "quiet_zone": 2.5,
            "write_text": False,
        },
    )
    bar_buf.seek(0)

    image_reader = ImageReader(bar_buf)
    img_width, img_height = image_reader.getSize()
    scale = min(max_width / img_width, max_height / img_height)

    barcode_img = RLImage(bar_buf, width=img_width * scale, height=img_height * scale)
    barcode_img.hAlign = "LEFT"
    return barcode_img


# ─────────────────────────────────────────────
# 1. Звіт прийому посилки (створення)
# ─────────────────────────────────────────────
def generate_shipment_receipt(shipment):
    s = _styles()
    elements = []

    # Трекінг і штрих-код
    try:
        elements.append(_build_barcode_image(shipment.tracking_number, max_width=7 * cm, max_height=1.8 * cm))
        elements.append(Spacer(1, 4))
    except Exception:
        pass

    elements.append(Paragraph(f"Трекінг-номер: {shipment.tracking_number}", s["heading"]))
    elements.append(Spacer(1, 8))

    # Відправник / Отримувач
    info_data = [
        ["", "ВІДПРАВНИК", "ОТРИМУВАЧ"],
        ["ПІБ", shipment.sender_full_name, shipment.receiver_full_name],
        ["Телефон", shipment.sender_phone, shipment.receiver_phone],
        ["Email", shipment.sender_email or "—", shipment.receiver_email or "—"],
        ["Відділення", shipment.origin.name, shipment.destination.name],
        ["Місто", _city_name(shipment.origin), _city_name(shipment.destination)],
    ]
    t = Table(info_data, colWidths=[3.5 * cm, 8 * cm, 8 * cm])
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 12))

    # Параметри посилки
    params_data = [
        ["Параметр", "Значення"],
        ["Вага", f"{shipment.weight} кг"],
        ["Ціна доставки", f"{shipment.price} грн"],
        ["Тип оплати", shipment.get_payment_type_display()],
        ["Опис", shipment.description or "—"],
        ["Дата створення", shipment.created_at.strftime("%d.%m.%Y %H:%M")],
        ["Зареєстрував", shipment.created_by.full_name if shipment.created_by else "—"],
    ]
    t2 = Table(params_data, colWidths=[6 * cm, 13.5 * cm])
    t2.setStyle(_table_style())
    elements.append(t2)

    return _build_pdf(
        elements,
        "Квитанція прийому посилки",
        f"Відправлення {shipment.tracking_number}",
    )


# ─────────────────────────────────────────────
# 2. Звіт передачі Dispatch групи водію
# ─────────────────────────────────────────────
def generate_dispatch_depart_report(group, handed_by):
    s = _styles()
    elements = []

    meta = [
        ["Параметр", "Значення"],
        ["Код групи", group.code],
        ["Звідки", f"{group.origin.name} ({_city_name(group.origin)})"],
        ["Куди", f"{group.destination.name} ({_city_name(group.destination)})"],
        ["Передав", handed_by.full_name],
        ["Час відправки", group.departed_at.strftime("%d.%m.%Y %H:%M") if group.departed_at else "—"],
    ]
    t = Table(meta, colWidths=[6 * cm, 13.5 * cm])
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Список посилок у групі", s["heading"]))
    shipments_data = [["#", "Трекінг-номер", "Відправник", "Отримувач", "Вага"]]
    for i, item in enumerate(group.items.select_related("shipment"), start=1):
        sh = item.shipment
        shipments_data.append([
            str(i),
            sh.tracking_number,
            sh.sender_full_name,
            sh.receiver_full_name,
            f"{sh.weight} кг",
        ])
    t2 = Table(shipments_data, colWidths=[1 * cm, 5 * cm, 5 * cm, 5 * cm, 3.5 * cm])
    t2.setStyle(_table_style())
    elements.append(t2)

    return _build_pdf(elements, "Акт передачі Dispatch групи", group.code)


# ─────────────────────────────────────────────
# 3. Звіт прибуття Dispatch групи
# ─────────────────────────────────────────────
def generate_dispatch_arrive_report(group, received_by):
    s = _styles()
    elements = []

    meta = [
        ["Параметр", "Значення"],
        ["Код групи", group.code],
        ["Звідки", f"{group.origin.name} ({_city_name(group.origin)})"],
        ["Прибуло до", f"{group.destination.name} ({_city_name(group.destination)})"],
        ["Прийняв", received_by.full_name],
        ["Час прибуття", group.arrived_at.strftime("%d.%m.%Y %H:%M") if group.arrived_at else "—"],
    ]
    t = Table(meta, colWidths=[6 * cm, 13.5 * cm])
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Список посилок", s["heading"]))
    shipments_data = [["#", "Трекінг-номер", "Відправник", "Отримувач", "Вага"]]
    for i, item in enumerate(group.items.select_related("shipment"), start=1):
        sh = item.shipment
        shipments_data.append([
            str(i),
            sh.tracking_number,
            sh.sender_full_name,
            sh.receiver_full_name,
            f"{sh.weight} кг",
        ])
    t2 = Table(shipments_data, colWidths=[1 * cm, 5 * cm, 5 * cm, 5 * cm, 3.5 * cm])
    t2.setStyle(_table_style())
    elements.append(t2)

    return _build_pdf(elements, "Акт прийому Dispatch групи", group.code)


# ─────────────────────────────────────────────
# 4. Звіт доставки посилки
# ─────────────────────────────────────────────
def generate_delivery_report(shipment, confirmed_by):
    s = _styles()
    elements = []

    data = [
        ["Параметр", "Значення"],
        ["Трекінг-номер", shipment.tracking_number],
        ["Відправник", shipment.sender_full_name],
        ["Отримувач", shipment.receiver_full_name],
        ["Телефон отримувача", shipment.receiver_phone],
        ["Відділення", shipment.destination.name],
        ["Підтвердив", confirmed_by.full_name],
        ["Час доставки", shipment.updated_at.strftime("%d.%m.%Y %H:%M")],
    ]
    t = Table(data, colWidths=[6 * cm, 13.5 * cm])
    t.setStyle(_table_style())
    elements.append(t)

    return _build_pdf(
        elements,
        "Підтвердження доставки",
        f"Посилка {shipment.tracking_number}",
    )


# ─────────────────────────────────────────────
# 5. Звіт оплати
# ─────────────────────────────────────────────
def generate_payment_report(shipment):
    elements = []
    payment = getattr(shipment, "payment", None)

    data = [
        ["Параметр", "Значення"],
        ["Трекінг-номер", shipment.tracking_number],
        ["Відправник", shipment.sender_full_name],
        ["Отримувач", shipment.receiver_full_name],
        ["Сума", f"{shipment.price} грн"],
        ["Тип оплати", shipment.get_payment_type_display()],
        ["Статус оплати", "Оплачено" if (payment and payment.is_paid) else "Не оплачено"],
        ["Час оплати", payment.paid_at.strftime("%d.%m.%Y %H:%M") if (payment and payment.paid_at) else "—"],
        ["Прийняв оплату", payment.received_by.full_name if (payment and payment.received_by) else "—"],
    ]
    t = Table(data, colWidths=[6 * cm, 13.5 * cm])
    t.setStyle(_table_style())
    elements.append(t)

    return _build_pdf(elements, "Звіт про оплату", f"Посилка {shipment.tracking_number}")


# ─────────────────────────────────────────────
# 6. Загальний звіт локації
# ─────────────────────────────────────────────
def generate_location_report(location, shipments, dispatch_groups, date_from=None, date_to=None):
    s = _styles()
    elements = []

    period = ""
    if date_from and date_to:
        period = f"{date_from.strftime('%d.%m.%Y')} — {date_to.strftime('%d.%m.%Y')}"

    total = len(shipments)
    delivered = sum(1 for sh in shipments if sh.status == "delivered")
    in_progress = sum(1 for sh in shipments if sh.status not in ("delivered", "cancelled", "returned"))
    cancelled = sum(1 for sh in shipments if sh.status == "cancelled")

    summary = [
        ["Показник", "Кількість"],
        ["Всього посилок", str(total)],
        ["Доставлено", str(delivered)],
        ["В процесі", str(in_progress)],
        ["Скасовано", str(cancelled)],
        ["Dispatch груп", str(len(dispatch_groups))],
    ]
    elements.append(Paragraph("Зведена статистика", s["heading"]))
    t = Table(summary, colWidths=[10 * cm, 9.5 * cm])
    t.setStyle(_table_style())
    elements.append(t)
    elements.append(Spacer(1, 16))

    if shipments:
        elements.append(Paragraph("Посилки", s["heading"]))
        sh_data = [["Трекінг", "Відправник", "Отримувач", "Вага", "Ціна", "Статус"]]
        for sh in shipments:
            sh_data.append([
                sh.tracking_number,
                sh.sender_last_name,
                sh.receiver_last_name,
                f"{sh.weight} кг",
                f"{sh.price} грн",
                sh.get_status_display(),
            ])
        t2 = Table(sh_data, colWidths=[4.5 * cm, 3.5 * cm, 3.5 * cm, 2 * cm, 2.5 * cm, 3.5 * cm])
        t2.setStyle(_table_style())
        elements.append(t2)
        elements.append(Spacer(1, 16))

    if dispatch_groups:
        elements.append(Paragraph("Dispatch групи", s["heading"]))
        dg_data = [["Код", "Куди", "Статус", "Посилок"]]
        for dg in dispatch_groups:
            dg_data.append([
                dg.code,
                dg.destination.name,
                dg.get_status_display(),
                str(dg.items.count()),
            ])
        t3 = Table(dg_data, colWidths=[3.5 * cm, 7 * cm, 4.5 * cm, 4.5 * cm])
        t3.setStyle(_table_style())
        elements.append(t3)

    subtitle = f"{location.name} ({_city_name(location)})"
    if period:
        subtitle += f" | {period}"

    return _build_pdf(elements, "Загальний звіт локації", subtitle)