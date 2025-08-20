from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from database import db
from config import Config

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Состояния разговора
CATEGORY, SERVICE, MASTER, PHONE = range(4)

def create_main_keyboard():
    keyboard = [
        ['💅 Маникюр', '👣 Педикюр'],
        ['📢 Перейти в Telegram канал', '🌐 Посетить сайт'],
        ['📞 Позвонить', '📍 Посмотреть адрес на карте'],
        ['📄 Скачать прайс в PDF']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in Config.ADMIN_IDS:
        await update.message.reply_text(
            "Добро пожаловать, администратор! Используйте /admin для управления.",
            reply_markup=create_main_keyboard()
        )
        return
    
    welcome_message = """
    👋 Добро пожаловать в студию маникюра!
    
    Выберите интересующую вас услугу или воспользуйтесь дополнительными опциями:
    """
    
    await update.message.reply_text(
        welcome_message,
        reply_markup=create_main_keyboard()
    )

async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in Config.ADMIN_IDS:
        return
    
    category = update.message.text.replace('💅 ', '').replace('👣 ', '')
    context.user_data['category'] = category
    
    services = db.get_services_by_category(category)
    if not services:
        await update.message.reply_text(
            "Услуги временно недоступны. Попробуйте позже.",
            reply_markup=create_main_keyboard()
        )
        return ConversationHandler.END
    
    keyboard = [[service[2]] for service in services] + [['Назад']]
    
    await update.message.reply_text(
        f"Выберите услугу для {category.lower()}:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return SERVICE

async def handle_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'Назад':
        await update.message.reply_text(
            "Выберите категорию:",
            reply_markup=create_main_keyboard()
        )
        return CATEGORY
    
    service_name = update.message.text
    services = db.get_services_by_category(context.user_data['category'])
    
    for service in services:
        if service[2] == service_name:
            context.user_data['service'] = service
            break
    else:
        await update.message.reply_text("Услуга не найдена.")
        return SERVICE
    
    service_info = service
    message = (
        f"💅 {service_info[2]}\n"
        f"💰 Цена: {service_info[3]} руб.\n"
        f"⏱ Время: {service_info[4] // 60} час. {service_info[4] % 60} мин.\n"
        f"👩‍💼 Мастер: {service_info[6]}\n\n"
        "Нажмите на цену для выбора мастера или 'Назад' для возврата"
    )
    
    keyboard = [[f"💰 {service_info[3]} руб."], ['Назад']]
    
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    
    return MASTER

async def handle_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == 'Назад':
        category = context.user_data['category']
        services = db.get_services_by_category(category)
        keyboard = [[service[2]] for service in services] + [['Назад']]
        
        await update.message.reply_text(
            f"Выберите услугу для {category.lower()}:",
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return SERVICE
    
    # Запрашиваем номер телефона
    await update.message.reply_text(
        "📞 Пожалуйста, введите ваш номер телефона для связи:",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return PHONE

async def handle_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    user = update.message.from_user
    
    # Сохраняем клиента в базу
    client_id = db.add_client(
        user.id, user.username, user.first_name, user.last_name, phone
    )
    
    service_info = context.user_data['service']
    order_id = db.add_order(client_id, service_info[0], service_info[5])
    
    # Формируем сообщение для администратора
    admin_message = (
        f"🎉 Новый заказ! №{order_id}\n"
        f"👤 Клиент: {user.first_name} {user.last_name or ''}\n"
        f"📞 Телефон: {phone}\n"
        f"📋 Категория: {context.user_data['category']}\n"
        f"💅 Услуга: {service_info[2]}\n"
        f"💰 Стоимость: {service_info[3]} руб.\n"
        f"⏱ Время: {service_info[4] // 60} час. {service_info[4] % 60} мин.\n"
        f"👩‍💼 Мастер: {service_info[6]}\n\n"
        "📞 Свяжитесь с клиентом для согласования дня и времени!"
    )
    
    # Отправляем сообщение всем администраторам
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, admin_message)
        except Exception as e:
            logging.error(f"Ошибка отправки сообщения администратору {admin_id}: {e}")
    
    await update.message.reply_text(
        "✅ Спасибо! Ваша заявка принята. Мы свяжемся с вами в ближайшее время для уточнения деталей!",
        reply_markup=create_main_keyboard()
    )
    
    return ConversationHandler.END

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📞 Наш телефон: {Config.PHONE_NUMBER}")

async def handle_website(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🌐 Наш сайт: {Config.WEBSITE_URL}")

async def handle_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📢 Наш канал: {Config.TELEGRAM_CHANNEL}")

async def handle_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lat, lon = map(float, Config.MAP_COORDINATES.split(','))
    await update.message.reply_location(latitude=lat, longitude=lon)

async def handle_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Здесь будет генерация PDF (заглушка)
    await update.message.reply_text(
        "📄 Функция генерации прайса в разработке. Скоро будет доступна!",
        reply_markup=create_main_keyboard()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=create_main_keyboard()
    )
    return ConversationHandler.END