from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from config import Config, check_config
from client_handlers import *
from admin_handlers import *
import logging

# Настройка логирования
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    # Проверка конфигурации
    check_config()
    
    if not Config.TOKEN_LOADED:
        logger.error("BOT_TOKEN не загружен! Проверьте .env файл.")
        return
    
    # Создание приложения
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Обработчик для клиентов
    client_conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^(💅 Маникюр|👣 Педикюр)$'), handle_category)
        ],
        states={
            CATEGORY: [
                MessageHandler(filters.Regex('^(💅 Маникюр|👣 Педикюр)$'), handle_category)
            ],
            SERVICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_service)
            ],
            MASTER: [
                MessageHandler(filters.Regex(r'^💰 \d+ руб\.$'), handle_master),
                MessageHandler(filters.Regex('^Назад$'), handle_service)
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Обработчик для администраторов
    admin_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            ADMIN_MAIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_actions)
            ],
            ADMIN_MASTERS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_masters_management)
            ]
        },
        fallbacks=[CommandHandler('cancel', admin_cancel)]
    )
    
    # Добавление обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(client_conv_handler)
    application.add_handler(admin_conv_handler)
    
    # Обработчики дополнительных кнопок
    application.add_handler(MessageHandler(filters.Regex('^📞 Позвонить$'), handle_contact))
    application.add_handler(MessageHandler(filters.Regex('^🌐 Посетить сайт$'), handle_website))
    application.add_handler(MessageHandler(filters.Regex('^📢 Перейти в Telegram канал$'), handle_channel))
    application.add_handler(MessageHandler(filters.Regex('^📍 Посмотреть адрес на карте$'), handle_location))
    application.add_handler(MessageHandler(filters.Regex('^📄 Скачать прайс в PDF$'), handle_price))
    
    # Запуск бота
    logger.info("Бот запущен")
    print("Бот запущен. Нажмите Ctrl+C для остановки.")
    
    application.run_polling()

if __name__ == '__main__':
    main()