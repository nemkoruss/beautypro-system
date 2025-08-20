from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import config, logger
from database import db
from client_handlers import (
    start, handle_message, show_services, select_service, 
    select_master, enter_phone, cancel,
    SELECT_SERVICE, SELECT_MASTER, ENTER_PHONE
)
from admin_handlers import (
    admin_panel, admin_main_handler, add_service, broadcast_message,
    edit_welcome_message, show_clients_list, show_orders_list, admin_cancel,
    ADMIN_MAIN, ADD_SERVICE, BROADCAST_MESSAGE, EDIT_WELCOME_MESSAGE
)

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

    # Обработчик для обычных сообщений (главное меню)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик для клиентов - УПРОЩЕННАЯ ВЕРСИЯ
    client_conversation = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^(💅 Маникюр|🦶 Педикюр)$'), handle_message)],
        states={
            SELECT_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_service)],
            SELECT_MASTER: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_master)],
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_phone)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    # Обработчик для администраторов
    admin_conversation = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            ADMIN_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_main_handler)],
            ADD_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service)],
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message)],
            EDIT_WELCOME_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_welcome_message)]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)],
        allow_reentry=True
    )

    # Добавляем обработчики
    application.add_handler(client_conversation)
    application.add_handler(admin_conversation)
    application.add_handler(CommandHandler('start', start))

    # Запускаем бота
    logger.info("Bot started successfully")
    application.run_polling()

if __name__ == '__main__':
    main()