from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import config

Base = declarative_base()

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), nullable=False)  # Маникюр, Педикюр
    name = Column(String(100), nullable=False)     # Наращивание, Гель-лак и т.д.
    price = Column(Float, nullable=False)
    duration = Column(Integer, nullable=False)     # Время в минутах
    master = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Master(Base):
    __tablename__ = 'masters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    specialization = Column(String(100))
    phone = Column(String(20))
    created_at = Column(DateTime, default=datetime.now)

class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, nullable=False)
    first_name = Column(String(100))
    phone = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, nullable=False)
    service_id = Column(Integer, nullable=False)
    master_name = Column(String(100), nullable=False)
    status = Column(String(20), default='pending')  # pending, confirmed, completed, cancelled
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class BotSettings(Base):
    __tablename__ = 'bot_settings'
    
    id = Column(Integer, primary_key=True)
    welcome_message = Column(Text, default='Добро пожаловать в нашу студию маникюра!')
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class Database:
    def __init__(self):
        self.engine = create_engine(config.DATABASE_URL)
        self.Session = sessionmaker(bind=self.engine)
        
    def init_db(self):
        Base.metadata.create_all(self.engine)
        self._create_default_data()
    
    def _create_default_data(self):
        session = self.Session()
        try:
            # Проверяем, есть ли уже данные
            if not session.query(Service).first():
                # Добавляем стандартные услуги
                default_services = [
                    Service(category='Маникюр', name='Классический маникюр', price=1500, duration=60, master='Анна'),
                    Service(category='Маникюр', name='Гель-лак', price=2000, duration=90, master='Мария'),
                    Service(category='Маникюр', name='Наращивание', price=2500, duration=120, master='Елена'),
                    Service(category='Педикюр', name='Классический педикюр', price=1800, duration=75, master='Ольга'),
                    Service(category='Педикюр', name='Мужской педикюр', price=2000, duration=90, master='Иван')
                ]
                session.add_all(default_services)
            
            if not session.query(Master).first():
                default_masters = [
                    Master(name='Анна', specialization='Маникюр', phone='+79991234561'),
                    Master(name='Мария', specialization='Гель-лак', phone='+79991234562'),
                    Master(name='Елена', specialization='Наращивание', phone='+79991234563'),
                    Master(name='Ольга', specialization='Педикюр', phone='+79991234564'),
                    Master(name='Иван', specialization='Мужской педикюр', phone='+79991234565')
                ]
                session.add_all(default_masters)
            
            if not session.query(BotSettings).first():
                session.add(BotSettings())
            
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_session(self):
        return self.Session()

# Создаем экземпляр базы данных
db = Database()