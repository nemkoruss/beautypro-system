import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(','))) if os.getenv("ADMIN_IDS") else []
DB_NAME = "nail_studio.db"

# Добавим проверку для отладки
print(f"BOT_TOKEN loaded: {bool(BOT_TOKEN)}")
print(f"ADMIN_IDS: {ADMIN_IDS}")