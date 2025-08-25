import sqlite3
import logging
from datetime import datetime

class Database:
    def __init__(self, db_name='beauty_bot.db'):
        self.db_name = db_name
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_name)
    
    def init_db(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Таблица услуг
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS services (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        name TEXT NOT NULL,
                        price INTEGER NOT NULL,
                        duration TEXT NOT NULL,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Таблица клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER NOT NULL,
                        first_name TEXT NOT NULL,
                        phone_number TEXT NOT NULL,
                        service_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (service_id) REFERENCES services (id)
                    )
                ''')
                
                # Таблица настроек
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT NOT NULL
                    )
                ''')
                
                # Добавляем начальные услуги
                initial_services = [
                    ('Маникюр', 'Классический', 1500, '3 часа'),
                    ('Маникюр', 'Гель-лак', 2500, '5 часов'),
                    ('Маникюр', 'Аппаратный', 3500, '2 часа'),
                    ('Педикюр', 'Аппаратный', 1000, '30 минут'),
                    ('Наращивание', 'Верхние формы', 3000, '2 часа'),
                    ('Наращивание', 'Типсы', 1500, '1.5 часа')
                ]
                
                for service in initial_services:
                    cursor.execute('''
                        INSERT OR IGNORE INTO services (category, name, price, duration)
                        VALUES (?, ?, ?, ?)
                    ''', service)
                
                # Добавляем начальные настройки
                initial_settings = [
                    ('welcome_message', 'Рады Вас видеть в нашей студии маникюра "Ноготочки-Точка"!'),
                    ('telegram_channel', 'https://t.me/your_channel'),
                    ('website_url', 'https://your-website.com'),
                    ('phone_number', '+79991234567'),
                    ('location_lat', '55.7558'),
                    ('location_lon', '37.6173')
                ]
                
                for key, value in initial_settings:
                    cursor.execute('''
                        INSERT OR IGNORE INTO settings (key, value)
                        VALUES (?, ?)
                    ''', (key, value))
                
                conn.commit()
                
        except Exception as e:
            logging.error(f"Error initializing database: {e}")
    
    def get_services_by_category(self, category):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, price, duration FROM services 
                WHERE category = ? AND is_active = TRUE
            ''', (category,))
            return cursor.fetchall()
    
    def get_service_by_id(self, service_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM services WHERE id = ?', (service_id,))
            return cursor.fetchone()
    
    def add_client(self, telegram_id, first_name, phone_number, service_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO clients (telegram_id, first_name, phone_number, service_id)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, first_name, phone_number, service_id))
            conn.commit()
            return cursor.lastrowid
    
    def get_clients(self, days=30):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if days:
                cursor.execute('''
                    SELECT c.*, s.name as service_name, s.category 
                    FROM clients c 
                    LEFT JOIN services s ON c.service_id = s.id 
                    WHERE date(c.created_at) >= date('now', ?)
                    ORDER BY c.created_at DESC
                ''', (f'-{days} days',))
            else:
                cursor.execute('''
                    SELECT c.*, s.name as service_name, s.category 
                    FROM clients c 
                    LEFT JOIN services s ON c.service_id = s.id 
                    ORDER BY c.created_at DESC
                ''')
            return cursor.fetchall()
    
    def update_service(self, service_id, name, price, duration):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE services SET name = ?, price = ?, duration = ?
                WHERE id = ?
            ''', (name, price, duration, service_id))
            conn.commit()
    
    def delete_service(self, service_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE services SET is_active = FALSE WHERE id = ?', (service_id,))
            conn.commit()
    
    def add_service(self, category, name, price, duration):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO services (category, name, price, duration)
                VALUES (?, ?, ?, ?)
            ''', (category, name, price, duration))
            conn.commit()
            return cursor.lastrowid
    
    def get_setting(self, key):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def update_setting(self, key, value):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
            conn.commit()
    
    def get_all_services(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM services WHERE is_active = TRUE ORDER BY category, name')
            return cursor.fetchall()
    
    def get_all_client_ids(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT DISTINCT telegram_id FROM clients')
            return [row[0] for row in cursor.fetchall()]

db = Database()