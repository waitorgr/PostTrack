"""
Генератор штрихкодів для посилок
Окремий модуль для створення штрихкодів у форматі PDF
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


def generate_barcode_pdf(tracking_number):
    """
    Генерує PDF з штрихкодом для трекінг-номера
    
    Args:
        tracking_number: Трекінг-номер посилки
    
    Returns:
        BytesIO buffer з PDF файлом
    """
    buffer = io.BytesIO()
    
    # Створюємо документ (невеликий формат для штрихкоду)
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=(10*cm, 5*cm),
        leftMargin=0.5*cm, 
        rightMargin=0.5*cm,
        topMargin=0.5*cm, 
        bottomMargin=0.5*cm,
    )
    
    elements = []
    
    # Стилі
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'title',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#1A3C6E'),
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica-Bold',
    )
    
    # Заголовок
    elements.append(Paragraph('ШТРИХКОД ПОСИЛКИ', title_style))
    
    # Генеруємо штрихкод
    try:
        import barcode as bc
        from barcode.writer import ImageWriter
        
        bar_buf = io.BytesIO()
        code = bc.get('code128', tracking_number, writer=ImageWriter())
        code.write(bar_buf, options={
            'module_width': 0.3,
            'module_height': 12,
            'quiet_zone': 2,
            'font_size': 10,
            'text_distance': 3,
        })
        bar_buf.seek(0)
        
        # Додаємо зображення штрихкоду
        barcode_img = RLImage(bar_buf, width=8*cm, height=2.5*cm)
        elements.append(barcode_img)
        
    except Exception as e:
        # Якщо не вдалося створити штрихкод, просто виводимо текст
        error_style = ParagraphStyle(
            'error',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER,
            textColor=colors.red,
        )
        elements.append(Paragraph(f'Помилка генерації штрихкоду: {str(e)}', error_style))
        elements.append(Spacer(1, 10))
        
        number_style = ParagraphStyle(
            'number',
            parent=styles['Normal'],
            fontSize=14,
            alignment=TA_CENTER,
            fontName='Courier-Bold',
        )
        elements.append(Paragraph(tracking_number, number_style))
    
    # Будуємо PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


def add_barcode_to_pdf_elements(tracking_number, width=7*cm, height=2*cm):
    """
    Створює елемент штрихкоду для вставки в інші PDF документи
    
    Args:
        tracking_number: Трекінг-номер
        width: Ширина зображення
        height: Висота зображення
    
    Returns:
        RLImage об'єкт або None
    """
    try:
        import barcode as bc
        from barcode.writer import ImageWriter
        
        bar_buf = io.BytesIO()
        code = bc.get('code128', tracking_number, writer=ImageWriter())
        code.write(bar_buf, options={
            'module_width': 0.2,
            'module_height': 10,
            'quiet_zone': 2,
            'font_size': 8,
            'text_distance': 2,
        })
        bar_buf.seek(0)
        
        return RLImage(bar_buf, width=width, height=height)
    except Exception:
        return None
