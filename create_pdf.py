from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import os
from database import db
from config import config

def generate_price_list():
    try:
        # Регистрируем шрифты
        fonts_dir = 'fonts'
        bold_font_path = os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')
        regular_font_path = os.path.join(fonts_dir, 'DejaVuSans.ttf')
        
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
        pdfmetrics.registerFont(TTFont('DejaVuSans', regular_font_path))
        
        # Создаем PDF
        filename = "price_list.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Заголовок
        c.setFont("DejaVuSans-Bold", 16)
        c.drawString(50, height - 50, "Прайс-лист студии маникюра")
        
        # Получаем услуги из базы данных
        session = db.get_session()
        services = session.query(Service).all()
        
        # Группируем услуги по категориям
        categories = {}
        for service in services:
            if service.category not in categories:
                categories[service.category] = []
            categories[service.category].append(service)
        
        y_position = height - 80
        
        # Добавляем услуги в PDF
        c.setFont("DejaVuSans", 12)
        
        for category, category_services in categories.items():
            c.setFont("DejaVuSans-Bold", 14)
            c.drawString(50, y_position, category)
            y_position -= 25
            
            c.setFont("DejaVuSans", 12)
            for service in category_services:
                if y_position < 50:
                    c.showPage()
                    y_position = height - 50
                    c.setFont("DejaVuSans", 12)
                
                service_text = f"{service.name} - {service.price} руб. ({service.duration} мин.) - {service.master}"
                c.drawString(70, y_position, service_text)
                y_position -= 20
            
            y_position -= 10
        
        # Контактная информация
        c.showPage()
        c.setFont("DejaVuSans-Bold", 16)
        c.drawString(50, height - 50, "Контактная информация")
        
        c.setFont("DejaVuSans", 12)
        contacts = [
            f"Телефон: {config.PHONE_NUMBER}",
            f"Сайт: {config.WEBSITE_URL}",
            f"Telegram канал: {config.TELEGRAM_CHANNEL}"
        ]
        
        y_contact = height - 80
        for contact in contacts:
            c.drawString(50, y_contact, contact)
            y_contact -= 20
        
        c.save()
        return filename
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return None