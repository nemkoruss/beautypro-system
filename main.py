import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import config
from client import start, handle_message, get_phone, cancel, PHONE
from admin import (
    admin_panel, admin_handler, admin_cancel, ADMIN_MAIN,
    edit_category_handler, edit_service_select_handler, edit_service_details_handler,
    delete_category_handler, delete_service_select_handler, delete_service_confirm_handler,
    add_category_handler, add_service_name_handler, add_service_price_handler, add_service_duration_handler,
    edit_channel_handler, edit_website_handler, edit_location_lat_handler, edit_location_lon_handler,
    edit_welcome_handler, send_message_handler,
    EDIT_CATEGORY, EDIT_SERVICE_SELECT, EDIT_SERVICE_DETAILS,
    DELETE_CATEGORY, DELETE_SERVICE_SELECT, DELETE_SERVICE_CONFIRM,
    ADD_CATEGORY, ADD_SERVICE_NAME, ADD_SERVICE_PRICE, ADD_SERVICE_DURATION,
    EDIT_CHANNEL, EDIT_WEBSITE, EDIT_LOCATION_LAT, EDIT_LOCATION_LON,
    EDIT_WELCOME, SEND_MESSAGE
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot.log'
)

# Глобальная переменная для доступа к application из других модулей
application = None

def main():
    global application
    
    if not config.BOT_TOKEN:
        logging.error("BOT_TOKEN not found!")
        return
    
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # ConversationHandler для клиентов
    client_conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
        states={
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # ConversationHandler для администраторов
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_panel)],
        states={
            ADMIN_MAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_handler)],
            
            # Редактирование услуг
            EDIT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_category_handler)],
            EDIT_SERVICE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_service_select_handler)],
            EDIT_SERVICE_DETAILS: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_service_details_handler)],
            
            # Удаление услуг
            DELETE_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_category_handler)],
            DELETE_SERVICE_SELECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_service_select_handler)],
            DELETE_SERVICE_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_service_confirm_handler)],
            
            # Добавление услуг
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_handler)],
            ADD_SERVICE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_name_handler)],
            ADD_SERVICE_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_price_handler)],
            ADD_SERVICE_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service_duration_handler)],
            
            # Редактирование настроек
            EDIT_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_channel_handler)],
            EDIT_WEBSITE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_website_handler)],
            EDIT_LOCATION_LAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_location_lat_handler)],
            EDIT_LOCATION_LON: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_location_lon_handler)],
            EDIT_WELCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_welcome_handler)],
            SEND_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_message_handler)],
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )
    
    # Добавляем обработчики
    application.add_handler(CommandHandler('start', start))
    application.add_handler(client_conv_handler)
    application.add_handler(admin_conv_handler)
    
    # Запускаем бота
    application.run_polling()

if __name__ == '__main__':
    main()