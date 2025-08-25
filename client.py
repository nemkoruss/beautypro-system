from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config
from database import db

# Состояния для ConversationHandler
PHONE, SERVICE_SELECTION = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем user_data при каждом старте
    context.user_data.clear()
    
    if update.message.from_user.id in config.ADMIN_IDS:
        # Администраторы видят админ-меню
        keyboard = [['/admin']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Добро пожаловать в панель администратора!",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    # Клиентское меню
    welcome_message = db.get_setting('welcome_message') or 'Рады Вас видеть в нашей студии маникюра "Ноготочки-Точка"!'
    
    keyboard = [
        ['Маникюр', 'Педикюр', 'Наращивание'],
        ['Перейти в телеграм-канал', 'Перейти на сайт', 'Адрес студии']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если пользователь администратор и не в админ-панели, предлагаем перейти в админку
    if update.message.from_user.id in config.ADMIN_IDS and not context.user_data.get('in_admin'):
        keyboard = [['/admin']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Вы администратор. Используйте /admin для доступа к панели управления.",
            reply_markup=reply_markup
        )
        return ConversationHandler.END
    
    text = update.message.text
    
    if text == 'Маникюр':
        services = db.get_services_by_category('Маникюр')
        if not services:
            await update.message.reply_text("В настоящее время услуги маникюра недоступны.")
            return
            
        keyboard = []
        for service in services:
            keyboard.append([f"{service[1]} - {service[2]} руб."])
        keyboard.append(['Назад'])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите тип маникюра:", reply_markup=reply_markup)
    
    elif text == 'Педикюр':
        services = db.get_services_by_category('Педикюр')
        if not services:
            await update.message.reply_text("В настоящее время услуги педикюра недоступны.")
            return
            
        keyboard = []
        for service in services:
            keyboard.append([f"{service[1]} - {service[2]} руб."])
        keyboard.append(['Назад'])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите тип педикюра:", reply_markup=reply_markup)
    
    elif text == 'Наращивание':
        services = db.get_services_by_category('Наращивание')
        if not services:
            await update.message.reply_text("В настоящее время услуги наращивания недоступны.")
            return
            
        keyboard = []
        for service in services:
            keyboard.append([f"{service[1]} - {service[2]} руб."])
        keyboard.append(['Назад'])
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите тип наращивания:", reply_markup=reply_markup)
    
    elif text == 'Перейти в телеграм-канал':
        channel_url = db.get_setting('telegram_channel') or config.TELEGRAM_CHANNEL
        await update.message.reply_text(f"Наш телеграм-канал: {channel_url}")
    
    elif text == 'Перейти на сайт':
        website_url = db.get_setting('website_url') or config.WEBSITE_URL
        await update.message.reply_text(f"Наш сайт: {website_url}")
    
    elif text == 'Адрес студии':
        lat = float(db.get_setting('location_lat') or config.LOCATION_LAT)
        lon = float(db.get_setting('location_lon') or config.LOCATION_LON)
        await update.message.reply_location(latitude=lat, longitude=lon)
        await update.message.reply_text("Наш адрес на карте:")
    
    elif text == 'Назад':
        keyboard = [
            ['Маникюр', 'Педикюр', 'Наращивание'],
            ['Перейти в телеграм-канал', 'Перейти на сайт', 'Адрес студии']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Главное меню:", reply_markup=reply_markup)
    
    else:
        # Проверяем, является ли сообщение выбором услуги
        services = db.get_all_services()
        for service in services:
            service_text = f"{service[2]} - {service[3]} руб."
            if text == service_text:
                context.user_data['selected_service'] = service[0]
                await update.message.reply_text(
                    f"Вы выбрали: {service[2]}\n"
                    f"Цена: {service[3]} руб.\n"
                    f"Время: {service[4]}\n\n"
                    "Пожалуйста, введите ваш номер телефона для записи:",
                    reply_markup=ReplyKeyboardRemove()
                )
                return PHONE

        await update.message.reply_text("Пожалуйста, выберите услугу из меню.")

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone_number = update.message.text
    service_id = context.user_data.get('selected_service')
    
    if service_id:
        service = db.get_service_by_id(service_id)
        client_id = db.add_client(
            update.message.from_user.id,
            update.message.from_user.first_name,
            phone_number,
            service_id
        )
        
        # Отправляем уведомление администраторам
        from main import application
        for admin_id in config.ADMIN_IDS:
            try:
                await application.bot.send_message(
                    admin_id,
                    f"🎉 Новая запись!\n"
                    f"Клиент № {client_id}: {update.message.from_user.first_name}\n"
                    f"Телефон: {phone_number}\n"
                    f"Услуга: {service[2]} ({service[1]})\n"
                    f"Стоимость: {service[3]} руб.\n"
                    f"Время: {service[4]}\n\n"
                    "📞 Свяжитесь с клиентом для согласования времени!"
                )
            except Exception as e:
                logging.error(f"Error sending message to admin {admin_id}: {e}")
        
        keyboard = [['/start']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "✅ Спасибо за запись! Администратор свяжется с вами в ближайшее время для подтверждения времени.",
            reply_markup=reply_markup
        )
    
    # Очищаем временные данные
    context.user_data.pop('selected_service', None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем временные данные
    context.user_data.clear()
    
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
    )
    return ConversationHandler.END