from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config, logger
from database import db
from client_handlers import start, handle_message
from admin_handlers import admin_panel

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
    application.add_handler(CommandHandler('admin', admin_panel))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем бота
    logger.info("Bot started successfully")
    application.run_polling()

if __name__ == '__main__':
    main()