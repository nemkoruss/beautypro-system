from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import config, logger
from database import db
from client_handlers import start, handle_message
from admin_handlers import admin_panel  # Импортируем из admin_handlers.py

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
    
    # Обработчик для всех сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))

    # Запускаем бота
    logger.info("Bot started successfully")
    application.run_polling()

async def handle_all_messages(update, context):
    user_id = update.message.from_user.id
    
    if user_id in config.ADMIN_IDS:
        # Для администраторов используем отдельную логику
        await handle_admin_message(update, context)
    else:
        await handle_message(update, context)

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Простая обработка админских сообщений
    text = update.message.text
    
    if text == '⬅️ Назад':
        await update.message.reply_text("Возврат в главное меню.", reply_markup=ReplyKeyboardRemove())
    else:
        # Перенаправляем в админскую панель
        await admin_panel(update, context)

if __name__ == '__main__':
    main()