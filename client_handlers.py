from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging
from config import config, logger
from database import db, Service, Client, Order, BotSettings

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in config.ADMIN_IDS:
        await update.message.reply_text(
            "Добро пожаловать, администратор! Используйте /admin для управления.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await show_main_menu(update)

async def show_main_menu(update: Update):
    session = db.get_session()
    try:
        settings = session.query(BotSettings).first()
        welcome_message = settings.welcome_message if settings else "Добро пожаловать в нашу студию маникюра!"
        
        keyboard = [
            ['💅 Маникюр', '🦶 Педикюр'],
            ['📢 Перейти в Telegram канал', '🌐 Посетить сайт'],
            ['📞 Позвонить', '📍 Посмотреть адрес на карте'],
            ['📄 Скачать прайс в PDF']
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error in show_main_menu: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"Сообщение: {text}")
    
    # Обработка кнопок главного меню
    if text == '💅 Маникюр':
        await show_services(update, 'Маникюр')
    elif text == '🦶 Педикюр':
        await show_services(update, 'Педикюр')
    elif text == '📢 Перейти в Telegram канал':
        await update.message.reply_text(f"Наш Telegram канал: {config.TELEGRAM_CHANNEL}")
    elif text == '🌐 Посетить сайт':
        await update.message.reply_text(f"Наш сайт: {config.WEBSITE_URL}")
    elif text == '📞 Позвонить':
        await update.message.reply_text(f"Позвоните нам: {config.PHONE_NUMBER}")
    elif text == '📍 Посмотреть адрес на карте':
        await update.message.reply_location(
            latitude=config.LOCATION_LAT,
            longitude=config.LOCATION_LON
        )
    elif text == '📄 Скачать прайс в PDF':
        from create_pdf import generate_price_list
        pdf_path = generate_price_list()
        if pdf_path:
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption="Наш прайс-лист"
                )
        else:
            await update.message.reply_text("Извините, прайс-лист временно недоступен.")
    elif ' - ' in text and ' руб. (' in text:
        service_name = text.split(' - ')[0]
        await show_service_details(update, service_name)
    elif text == '⬅️ Назад':
        await show_main_menu(update)
    elif text.startswith('Выбрать мастера'):
        master_name = text.split('(')[1].split(')')[0]
        await ask_for_phone(update, context, master_name)
    elif 'awaiting_phone' in context.user_data:
        await process_phone_input(update, context)
    else:
        await show_main_menu(update)

# ... остальные функции (show_services, show_service_details, ask_for_phone, process_phone_input)