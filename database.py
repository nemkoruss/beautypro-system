import aiosqlite
import logging
from config import DB_NAME
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

logger = logging.getLogger(__name__)

# Регистрируем шрифты для поддержки кириллицы
try:
    # Попробуем зарегистрировать Arial
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'Arial Bold.ttf'))
except:
    try:
        # Попробуем зарегистрировать DejaVuSans (обычно есть в Linux)
        pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    except:
        # Если не удалось зарегистрировать шрифты, будем использовать стандартные (могут не поддерживать кириллицу)
        logger.warning("Шрифты с поддержкой кириллицы не найдены. Кириллица в PDF может отображаться некорректно.")

async def init_db():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            # Таблица услуг
            await db.execute('''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    duration INTEGER NOT NULL
                )
            ''')
            
            # Таблица мастеров
            await db.execute('''
                CREATE TABLE IF NOT EXISTS masters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    services TEXT NOT NULL
                )
            ''')
            
            # Таблица заказов
            await db.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    client_name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    category TEXT NOT NULL,
                    service TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    master TEXT NOT NULL,
                    status TEXT DEFAULT 'new',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица пользователей для рассылки
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    subscribed BOOLEAN DEFAULT TRUE
                )
            ''')
            
            # Добавляем начальные данные, если таблицы пустые
            cursor = await db.execute("SELECT COUNT(*) FROM services")
            count = await cursor.fetchone()
            if count[0] == 0:
                await db.execute('''
                    INSERT INTO services (category, name, price, duration)
                    VALUES 
                    ('Маникюр', 'Классический маникюр', 1500, 60),
                    ('Маникюр', 'Гель-лак', 2000, 90),
                    ('Маникюр', 'Наращивание', 2500, 120),
                    ('Педикюр', 'Классический педикюр', 1800, 60),
                    ('Педикюр', 'Педикюр с покрытием', 2200, 90)
                ''')
            
            cursor = await db.execute("SELECT COUNT(*) FROM masters")
            count = await cursor.fetchone()
            if count[0] == 0:
                await db.execute('''
                    INSERT INTO masters (name, services)
                    VALUES 
                    ('Анна', '1,2,3'),
                    ('Елена', '1,2,4,5'),
                    ('Мария', '2,3,5'),
                    ('Ольга', '1,4,5')
                ''')
            
            await db.commit()
            logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise

async def get_services(category: str = None):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            if category:
                cursor = await db.execute(
                    "SELECT id, name, price, duration FROM services WHERE category = ?", 
                    (category,)
                )
            else:
                cursor = await db.execute("SELECT id, category, name, price, duration FROM services")
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting services: {e}")
        return []

async def get_service_by_id(service_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, category, name, price, duration FROM services WHERE id = ?", 
                (service_id,)
            )
            return await cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting service by ID: {e}")
        return None

async def add_service(category: str, name: str, price: int, duration: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO services (category, name, price, duration) VALUES (?, ?, ?, ?)",
                (category, name, price, duration)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        return False

async def update_service(service_id: int, category: str, name: str, price: int, duration: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE services SET category = ?, name = ?, price = ?, duration = ? WHERE id = ?",
                (category, name, price, duration, service_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating service: {e}")
        return False

async def delete_service(service_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM services WHERE id = ?", (service_id,))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting service: {e}")
        return False

async def get_masters():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute("SELECT id, name, services FROM masters")
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting masters: {e}")
        return []

async def get_master_by_id(master_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, name, services FROM masters WHERE id = ?", 
                (master_id,)
            )
            return await cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting master by ID: {e}")
        return None

async def get_masters_by_service(service_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, name FROM masters WHERE services LIKE ?", 
                (f'%{service_id}%',)
            )
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting masters by service: {e}")
        return []

async def add_master(name: str, services: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT INTO masters (name, services) VALUES (?, ?)",
                (name, services)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding master: {e}")
        return False

async def update_master(master_id: int, name: str, services: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE masters SET name = ?, services = ? WHERE id = ?",
                (name, services, master_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating master: {e}")
        return False

async def delete_master(master_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM masters WHERE id = ?", (master_id,))
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting master: {e}")
        return False

async def add_order(client_name: str, phone: str, category: str, service: str, price: int, master: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "INSERT INTO orders (client_name, phone, category, service, price, master) VALUES (?, ?, ?, ?, ?, ?)",
                (client_name, phone, category, service, price, master)
            )
            await db.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error adding order: {e}")
        return None

async def get_orders():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT id, client_name, phone, category, service, price, master, status, created_at FROM orders ORDER BY created_at DESC"
            )
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return []

async def update_order_status(order_id: int, status: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating order status: {e}")
        return False

async def add_user(user_id: int, username: str, first_name: str, last_name: str):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                (user_id, username, first_name, last_name)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error adding user: {e}")
        return False

async def get_users():
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            cursor = await db.execute(
                "SELECT user_id, username, first_name, last_name FROM users WHERE subscribed = TRUE"
            )
            return await cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting users: {e}")
        return []

async def unsubscribe_user(user_id: int):
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "UPDATE users SET subscribed = FALSE WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
            return True
    except Exception as e:
        logger.error(f"Error unsubscribing user: {e}")
        return False

async def generate_price_pdf():
    """Генерирует PDF с прайс-листом услуг"""
    try:
        services = await get_services()
        
        if not services:
            return None
        
        # Создаем PDF в памяти
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # Пытаемся использовать шрифты с поддержкой кириллицы
        try:
            c.setFont("Arial", 16)
        except:
            try:
                c.setFont("DejaVuSans", 16)
            except:
                c.setFont("Helvetica", 16)  # Фолбэк
        
        # Заголовок
        c.drawString(100, height - 50, "Прайс-лист студии маникюра")
        
        # Текущая позиция Y
        y = height - 80
        
        # Группируем услуги по категориям
        categories = {}
        for service in services:
            category = service[1]
            if category not in categories:
                categories[category] = []
            categories[category].append(service)
        
        # Устанавливаем шрифт для содержимого
        try:
            c.setFont("Arial", 12)
        except:
            try:
                c.setFont("DejaVuSans", 12)
            except:
                c.setFont("Helvetica", 12)  # Фолбэк
        
        # Добавляем услуги в PDF
        for category, services_in_category in categories.items():
            # Заголовок категории
            try:
                c.setFont("Arial-Bold", 14)
            except:
                try:
                    c.setFont("DejaVuSans-Bold", 14)
                except:
                    c.setFont("Helvetica-Bold", 14)  # Фолбэк
            
            c.drawString(100, y, category)
            y -= 25
            
            # Услуги в категории
            try:
                c.setFont("Arial", 12)
            except:
                try:
                    c.setFont("DejaVuSans", 12)
                except:
                    c.setFont("Helvetica", 12)  # Фолбэк
            
            for service in services_in_category:
                service_text = f"{service[2]} - {service[3]} руб. ({service[4]} мин.)"
                c.drawString(120, y, service_text)
                y -= 20
                
                # Если не хватает места на странице, создаем новую
                if y < 50:
                    c.showPage()
                    y = height - 50
                    try:
                        c.setFont("Arial", 12)
                    except:
                        try:
                            c.setFont("DejaVuSans", 12)
                        except:
                            c.setFont("Helvetica", 12)  # Фолбэк
            
            y -= 10  # Отступ между категориями
        
        c.save()
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating price PDF: {e}")
        return None