import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]
    PHONE_NUMBER = os.getenv('PHONE_NUMBER', '')
    WEBSITE_URL = os.getenv('WEBSITE_URL', '')
    TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL', '')
    MAP_COORDINATES = os.getenv('MAP_COORDINATES', '')
    
    # Проверка загрузки переменных
    TOKEN_LOADED = bool(BOT_TOKEN)
    ADMIN_IDS_LOADED = bool(ADMIN_IDS)
    PHONE_LOADED = bool(PHONE_NUMBER)
    WEBSITE_LOADED = bool(WEBSITE_URL)
    CHANNEL_LOADED = bool(TELEGRAM_CHANNEL)
    MAP_LOADED = bool(MAP_COORDINATES)

def check_config():
    print("Конфигурация загружена:")
    print(f"BOT_TOKEN: {'TRUE' if Config.TOKEN_LOADED else 'FALSE'}")
    print(f"ADMIN_IDS: {'TRUE' if Config.ADMIN_IDS_LOADED else 'FALSE'}")
    print(f"PHONE_NUMBER: {'TRUE' if Config.PHONE_LOADED else 'FALSE'}")
    print(f"WEBSITE_URL: {'TRUE' if Config.WEBSITE_LOADED else 'FALSE'}")
    print(f"TELEGRAM_CHANNEL: {'TRUE' if Config.CHANNEL_LOADED else 'FALSE'}")
    print(f"MAP_COORDINATES: {'TRUE' if Config.MAP_LOADED else 'FALSE'}")

if __name__ == "__main__":
    check_config()