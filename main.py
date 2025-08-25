from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config, logger
from database import db
from client_handlers import start, handle_message  # Импортируем из client_handlers.py
from admin_menu import show_admin_menu, handle_admin_message  # Импортируем из admin_menu.py

def main():
    # Инициализация базы данных
    try:
        db.init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return

    # Создаем приложение
    application = Application.builder().token(config.BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('admin', show_admin_menu))
    
    # Обработчик для всех сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    # Запускаем бота
    logger.info("Bot started successfully")
    application.run_polling()

async def handle_all_messages(update, context):
    user_id = update.message.from_user.id
    
    if user_id in config.ADMIN_IDS:
        await handle_admin_message(update, context)
    else:
        await handle_message(update, context)  # Используем handle_message из client_handlers

if __name__ == '__main__':
    main()