import sqlite3
import logging
from datetime import datetime

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

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
                        price REAL NOT NULL,
                        duration INTEGER NOT NULL,
                        master_id INTEGER,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Таблица мастеров
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS masters (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        specialties TEXT,
                        is_active BOOLEAN DEFAULT TRUE
                    )
                ''')
                
                # Таблица клиентов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clients (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        telegram_id INTEGER UNIQUE,
                        username TEXT,
                        first_name TEXT,
                        last_name TEXT,
                        phone TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Таблица заказов
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_id INTEGER,
                        service_id INTEGER,
                        master_id INTEGER,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (client_id) REFERENCES clients (id),
                        FOREIGN KEY (service_id) REFERENCES services (id),
                        FOREIGN KEY (master_id) REFERENCES masters (id)
                    )
                ''')
                
                # Вставляем начальные данные
                self.insert_initial_data(cursor)
                
                conn.commit()
                logging.info("База данных инициализирована успешно")
                
        except Exception as e:
            logging.error(f"Ошибка инициализации БД: {e}")
    
    def insert_initial_data(self, cursor):
        # Проверяем, есть ли уже мастера
        cursor.execute("SELECT COUNT(*) FROM masters")
        if cursor.fetchone()[0] == 0:
            masters = [
                ('Галина', 'Маникюр,Наращивание'),
                ('Ольга', 'Маникюр,Гель Лак'),
                ('Елена', 'Педикюр'),
            ]
            cursor.executemany(
                "INSERT INTO masters (name, specialties) VALUES (?, ?)",
                masters
            )
        
        # Проверяем, есть ли уже услуги
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            services = [
                ('Маникюр', 'Наращивание', 2500.0, 120, 1),
                ('Маникюр', 'Классический маникюр', 1500.0, 60, 2),
                ('Маникюр', 'Гель Лак', 1800.0, 90, 2),
                ('Педикюр', 'Классический педикюр', 2000.0, 90, 3),
                ('Педикюр', 'Аппаратный педикюр', 2500.0, 120, 3),
            ]
            cursor.executemany(
                "INSERT INTO services (category, name, price, duration, master_id) VALUES (?, ?, ?, ?, ?)",
                services
            )
    
    def add_client(self, telegram_id, username, first_name, last_name, phone):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO clients 
                    (telegram_id, username, first_name, last_name, phone)
                    VALUES (?, ?, ?, ?, ?)
                ''', (telegram_id, username, first_name, last_name, phone))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Ошибка добавления клиента: {e}")
            return None
    
    def add_order(self, client_id, service_id, master_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO orders (client_id, service_id, master_id)
                    VALUES (?, ?, ?)
                ''', (client_id, service_id, master_id))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logging.error(f"Ошибка добавления заказа: {e}")
            return None
    
    def get_services_by_category(self, category):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.*, m.name as master_name 
                    FROM services s 
                    LEFT JOIN masters m ON s.master_id = m.id 
                    WHERE s.category = ? AND s.is_active = TRUE
                ''', (category,))
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения услуг: {e}")
            return []
    
    def get_service_by_id(self, service_id):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT s.*, m.name as master_name 
                    FROM services s 
                    LEFT JOIN masters m ON s.master_id = m.id 
                    WHERE s.id = ?
                ''', (service_id,))
                return cursor.fetchone()
        except Exception as e:
            logging.error(f"Ошибка получения услуги: {e}")
            return None
    
    def get_masters(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM masters WHERE is_active = TRUE")
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения мастеров: {e}")
            return []
    
    def get_clients(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM clients")
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения клиентов: {e}")
            return []
    
    def get_orders(self):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT o.*, c.first_name, c.phone, s.name as service_name, 
                           s.price, s.duration, m.name as master_name
                    FROM orders o
                    JOIN clients c ON o.client_id = c.id
                    JOIN services s ON o.service_id = s.id
                    JOIN masters m ON o.master_id = m.id
                ''')
                return cursor.fetchall()
        except Exception as e:
            logging.error(f"Ошибка получения заказов: {e}")
            return []

# Создаем глобальный экземпляр базы данных
db = Database()