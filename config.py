import os
from dotenv import load_dotenv
import logging

# Загрузка переменных окружения
load_dotenv()

class Config:
    # Основные настройки
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    
    # Контактная информация
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    WEBSITE_URL = os.getenv('WEBSITE_URL', '')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', '')
    LOCATION_LAT = float(os.getenv('LOCATION_LAT', 0))
    LOCATION_LON = float(os.getenv('LOCATION_LON', 0))
    
    # База данных
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///beauty_salon.db')
    
    # Проверка загрузки переменных
    def check_config(self):
        config_status = {}
        
        config_status['BOT_TOKEN'] = bool(self.BOT_TOKEN)
        config_status['ADMIN_IDS'] = bool(self.ADMIN_IDS)
        config_status['PHONE_NUMBER'] = bool(self.PHONE_NUMBER)
        config_status['WEBSITE_URL'] = bool(self.WEBSITE_URL)
        config_status['TELEGRAM_CHANNEL'] = bool(self.TELEGRAM_CHANNEL)
        config_status['LOCATION_LAT'] = bool(self.LOCATION_LAT)
        config_status['LOCATION_LON'] = bool(self.LOCATION_LON)
        config_status['DATABASE_URL'] = bool(self.DATABASE_URL)
        
        return config_status

# Создаем экземпляр конфигурации
config = Config()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Проверка конфигурации при импорте
if __name__ == "__main__":
    status = config.check_config()
    print("Configuration status:")
    for key, value in status.items():
        print(f"{key}: {'✅' if value else '❌'}")