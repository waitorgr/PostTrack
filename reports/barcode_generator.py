"""
Генератор штрихкодів для посилок
Окремий модуль для створення штрихкодів у форматі PDF
"""
import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from .pdf_generator import FONT_BOLD, FONT_REGULAR, _register_fonts


def _build_barcode_image(tracking_number, max_width, max_height):
    """
    Повертає акуратно відмасштабоване зображення штрихкоду без тексту під ним.
    Текст трек-номера додається окремо, інакше при сильному масштабуванні він
    накладається на смуги штрихкоду.
    """
    import barcode as bc
    from barcode.writer import ImageWriter

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
    barcode_img.hAlign = "CENTER"
    return barcode_img



def generate_barcode_pdf(tracking_number):
    """
    Генерує PDF з штрихкодом для трекінг-номера

    Args:
        tracking_number: Трекінг-номер посилки

    Returns:
        BytesIO buffer з PDF файлом
    """
    _register_fonts()

    buffer = io.BytesIO()

    # Даємо трохи більший формат, щоб нічого не злипалось і не обрізалось.
    doc = SimpleDocTemplate(
        buffer,
        pagesize=(12 * cm, 6 * cm),
        leftMargin=0.7 * cm,
        rightMargin=0.7 * cm,
        topMargin=0.6 * cm,
        bottomMargin=0.6 * cm,
    )

    elements = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "title",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#1A3C6E"),
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName=FONT_BOLD,
    )
    number_style = ParagraphStyle(
        "number",
        parent=styles["Normal"],
        fontSize=13,
        alignment=TA_CENTER,
        fontName=FONT_REGULAR,
        leading=15,
    )

    elements.append(Paragraph("Штрихкод посилки", title_style))
    elements.append(Spacer(1, 0.15 * cm))

    try:
        barcode_img = _build_barcode_image(
            tracking_number,
            max_width=10.4 * cm,
            max_height=2.2 * cm,
        )
        elements.append(barcode_img)
        elements.append(Spacer(1, 0.18 * cm))
        elements.append(Paragraph(tracking_number, number_style))
    except Exception as e:
        error_style = ParagraphStyle(
            "error",
            parent=styles["Normal"],
            fontSize=11,
            alignment=TA_CENTER,
            textColor=colors.red,
            fontName=FONT_REGULAR,
        )
        elements.append(Paragraph(f"Помилка генерації штрихкоду: {str(e)}", error_style))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(tracking_number, number_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer



def add_barcode_to_pdf_elements(tracking_number, width=7 * cm, height=2 * cm):
    """
    Створює елемент штрихкоду для вставки в інші PDF документи

    Args:
        tracking_number: Трекінг-номер
        width: Максимальна ширина зображення
        height: Максимальна висота зображення

    Returns:
        RLImage об'єкт або None
    """
    try:
        return _build_barcode_image(tracking_number, max_width=width, max_height=height)
    except Exception:
        return None
