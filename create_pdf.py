from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from database import db, Service
from config import config

def generate_price_list():
    try:
        # Регистрируем шрифты
        fonts_dir = 'fonts'
        bold_font_path = os.path.join(fonts_dir, 'DejaVuSans-Bold.ttf')
        regular_font_path = os.path.join(fonts_dir, 'DejaVuSans.ttf')
        
        # Проверяем существование шрифтов
        if not os.path.exists(bold_font_path) or not os.path.exists(regular_font_path):
            print("Font files not found. Using default fonts.")
            # Используем стандартные шрифты если наши не найдены
            bold_font = 'Helvetica-Bold'
            regular_font = 'Helvetica'
        else:
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bold_font_path))
            pdfmetrics.registerFont(TTFont('DejaVuSans', regular_font_path))
            bold_font = 'DejaVuSans-Bold'
            regular_font = 'DejaVuSans'
        
        # Создаем PDF
        filename = "price_list.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        width, height = A4
        
        # Заголовок
        c.setFont(bold_font, 16)
        c.drawString(50, height - 50, "Прайс-лист студии маникюра")
        c.line(50, height - 55, width - 50, height - 55)
        
        # Получаем услуги из базы данных
        session = db.get_session()
        services = session.query(Service).all()
        session.close()
        
        # Группируем услуги по категориям
        categories = {}
        for service in services:
            if service.category not in categories:
                categories[service.category] = []
            categories[service.category].append(service)
        
        y_position = height - 80
        
        # Добавляем услуги в PDF
        c.setFont(regular_font, 12)
        
        for category, category_services in categories.items():
            c.setFont(bold_font, 14)
            c.drawString(50, y_position, f"🎀 {category}")
            y_position -= 25
            
            c.setFont(regular_font, 12)
            for service in category_services:
                if y_position < 100:  # Оставляем место для нижнего колонтитула
                    c.showPage()
                    y_position = height - 50
                    c.setFont(regular_font, 12)
                
                service_text = f"• {service.name}"
                price_text = f"{service.price} руб."
                duration_text = f"{service.duration} мин."
                master_text = f"Мастер: {service.master}"
                
                c.drawString(70, y_position, service_text)
                c.drawString(width - 150, y_position, price_text)
                c.drawString(width - 80, y_position, duration_text)
                y_position -= 20
                c.setFont(regular_font, 10)
                c.drawString(70, y_position, master_text)
                y_position -= 25
                c.setFont(regular_font, 12)
            
            y_position -= 15
        
        # Контактная информация на последней странице
        if y_position < 150:
            c.showPage()
            y_position = height - 50
        
        c.setFont(bold_font, 16)
        c.drawString(50, y_position, "📞 Контактная информация")
        y_position -= 30
        
        c.setFont(regular_font, 12)
        contacts = [
            f"📞 Телефон: {config.PHONE_NUMBER}",
            f"🌐 Сайт: {config.WEBSITE_URL}",
            f"📢 Telegram канал: {config.TELEGRAM_CHANNEL}",
            f"📍 Адрес: ул. Примерная, д. 123"
        ]
        
        for contact in contacts:
            if y_position < 50:
                c.showPage()
                y_position = height - 50
                c.setFont(regular_font, 12)
            
            c.drawString(50, y_position, contact)
            y_position -= 25
        
        # Футер
        c.setFont(regular_font, 10)
        c.drawString(50, 30, f"Прайс-лист сгенерирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        c.save()
        print(f"PDF generated: {filename}")
        return filename
        
    except Exception as e:
        print(f"Error generating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

# Для тестирования
if __name__ == "__main__":
    from datetime import datetime
    generate_price_list()