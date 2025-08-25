from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config
from database import db

# Состояния для админских ConversationHandler
(
    ADMIN_MAIN, EDIT_CATEGORY, EDIT_SERVICE_SELECT, EDIT_SERVICE_DETAILS,
    DELETE_CATEGORY, DELETE_SERVICE_SELECT, DELETE_SERVICE_CONFIRM,
    ADD_CATEGORY, ADD_SERVICE_NAME, ADD_SERVICE_PRICE, ADD_SERVICE_DURATION,
    EDIT_CHANNEL, EDIT_WEBSITE, EDIT_LOCATION_LAT, EDIT_LOCATION_LON,
    EDIT_WELCOME, SEND_MESSAGE
) = range(17)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("Доступ запрещен.")
        return ConversationHandler.END
    
    # Очищаем временные данные при входе в админ-панель
    for key in list(context.user_data.keys()):
        if key.startswith(('edit_', 'delete_', 'add_', 'new_')):
            context.user_data.pop(key, None)
    
    keyboard = [
        ['Изменить услугу', 'Удалить услугу', 'Добавить услугу'],
        ['Изменить ссылку на канал', 'Изменить ссылку на сайт', 'Изменить адрес'],
        ['Изменить приветствие', 'Рассылка сообщения', 'Посмотреть клиентов'],
        ['Посмотреть все записи', 'Назад']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    if update.message.text == '/admin':
        await update.message.reply_text("Панель администратора:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Панель администратора:", reply_markup=reply_markup)
    
    return ADMIN_MAIN

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Изменить услугу':
        keyboard = [['Маникюр', 'Педикюр', 'Наращивание'], ['Назад']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию для редактирования:", reply_markup=reply_markup)
        return EDIT_CATEGORY
    
    elif text == 'Удалить услугу':
        keyboard = [['Маникюр', 'Педикюр', 'Наращивание'], ['Назад']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию для удаления:", reply_markup=reply_markup)
        return DELETE_CATEGORY
    
    elif text == 'Добавить услугу':
        keyboard = [['Маникюр', 'Педикюр', 'Наращивание'], ['Назад']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите категорию для добавления:", reply_markup=reply_markup)
        return ADD_CATEGORY
    
    elif text == 'Изменить ссылку на канал':
        current_channel = db.get_setting('telegram_channel') or config.TELEGRAM_CHANNEL
        await update.message.reply_text(
            f"Текущая ссылка на канал: {current_channel}\nВведите новую ссылку:",
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_CHANNEL
    
    elif text == 'Изменить ссылку на сайт':
        current_website = db.get_setting('website_url') or config.WEBSITE_URL
        await update.message.reply_text(
            f"Текущая ссылка на сайт: {current_website}\nВведите новую ссылку:",
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_WEBSITE
    
    elif text == 'Изменить адрес':
        current_lat = db.get_setting('location_lat') or config.LOCATION_LAT
        current_lon = db.get_setting('location_lon') or config.LOCATION_LON
        await update.message.reply_text(
            f"Текущие координаты: {current_lat}, {current_lon}\nВведите новую широту:",
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_LOCATION_LAT
    
    elif text == 'Изменить приветствие':
        current_welcome = db.get_setting('welcome_message') or 'Рады Вас видеть в нашей студии маникюра "Ноготочки-Точка"!'
        await update.message.reply_text(
            f"Текущее приветствие: {current_welcome}\nВведите новое приветственное сообщение:",
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_WELCOME
    
    elif text == 'Рассылка сообщения':
        await update.message.reply_text(
            "Введите сообщение для рассылки всем клиентам:",
            reply_markup=ReplyKeyboardRemove()
        )
        return SEND_MESSAGE
    
    elif text == 'Посмотреть клиентов':
        clients = db.get_clients(30)
        await send_clients_list(update, clients, "Клиенты за последние 30 дней:")
        return await admin_panel(update, context)
    
    elif text == 'Посмотреть все записи':
        clients = db.get_clients(None)
        await send_clients_list(update, clients, "Все клиенты:")
        return await admin_panel(update, context)
    
    elif text == 'Назад':
        await update.message.reply_text("Возврат в главное меню.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    else:
        await update.message.reply_text("Неизвестная команда. Используйте кнопки меню.")
        return ADMIN_MAIN

async def send_clients_list(update, clients, title):
    if clients:
        message = f"{title}\n\n"
        for client in clients:
            message += f"ID: {client[0]}, Имя: {client[2]}, Телефон: {client[3]}, Услуга: {client[6] if len(client) > 6 else 'N/A'}, Дата: {client[5]}\n"
        
        # Разбиваем сообщение на части из-за ограничения длины в Telegram
        for i in range(0, len(message), 4000):
            await update.message.reply_text(message[i:i+4000])
    else:
        await update.message.reply_text("Нет данных о клиентах.")

# Редактирование услуг
async def edit_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Назад':
        return await admin_panel(update, context)
    
    if text not in ['Маникюр', 'Педикюр', 'Наращивание']:
        await update.message.reply_text("Пожалуйста, выберите категорию из предложенных вариантов.")
        return EDIT_CATEGORY
    
    context.user_data['edit_category'] = text
    services = db.get_services_by_category(text)
    
    if not services:
        keyboard = [['Назад']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("В этой категории нет услуг.", reply_markup=reply_markup)
        return EDIT_CATEGORY
    
    keyboard = []
    for service in services:
        keyboard.append([f"{service[0]}: {service[1]}"])
    keyboard.append(['Назад'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите услугу для редактирования:", reply_markup=reply_markup)
    return EDIT_SERVICE_SELECT

async def edit_service_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Назад':
        return await admin_panel(update, context)
    
    try:
        service_id = int(text.split(':')[0])
        service = db.get_service_by_id(service_id)
        if service:
            context.user_data['edit_service_id'] = service_id
            await update.message.reply_text(
                f"Текущие данные услуги:\n"
                f"Название: {service[2]}\n"
                f"Цена: {service[3]} руб.\n"
                f"Время: {service[4]}\n\n"
                f"Введите новое название:",
                reply_markup=ReplyKeyboardRemove()
            )
            return EDIT_SERVICE_DETAILS
        else:
            await update.message.reply_text("Услуга не найдена.")
    except (ValueError, IndexError):
        await update.message.reply_text("Неверный формат. Пожалуйста, выберите услугу из списка.")
    
    return EDIT_SERVICE_SELECT

async def edit_service_details_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if 'edit_service_name' not in context.user_data:
        context.user_data['edit_service_name'] = text
        await update.message.reply_text("Введите новую цену (только число):")
        return EDIT_SERVICE_DETAILS
    
    elif 'edit_service_price' not in context.user_data:
        try:
            price = int(text)
            context.user_data['edit_service_price'] = price
            await update.message.reply_text("Введите новое время выполнения (например: 2 часа):")
            return EDIT_SERVICE_DETAILS
        except ValueError:
            await update.message.reply_text("Неверный формат цены. Введите число:")
            return EDIT_SERVICE_DETAILS
    
    else:
        duration = text
        service_id = context.user_data['edit_service_id']
        name = context.user_data['edit_service_name']
        price = context.user_data['edit_service_price']
        
        db.update_service(service_id, name, price, duration)
        
        # Очищаем временные данные
        for key in ['edit_service_id', 'edit_service_name', 'edit_service_price', 'edit_category']:
            context.user_data.pop(key, None)
        
        await update.message.reply_text("✅ Услуга успешно обновлена!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
        return ConversationHandler.END

# Удаление услуг
async def delete_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Назад':
        return await admin_panel(update, context)
    
    if text not in ['Маникюр', 'Педикюр', 'Наращивание']:
        await update.message.reply_text("Пожалуйста, выберите категорию из предложенных вариантов.")
        return DELETE_CATEGORY
    
    context.user_data['delete_category'] = text
    services = db.get_services_by_category(text)
    
    if not services:
        keyboard = [['Назад']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("В этой категории нет услуг.", reply_markup=reply_markup)
        return DELETE_CATEGORY
    
    keyboard = []
    for service in services:
        keyboard.append([f"{service[0]}: {service[1]}"])
    keyboard.append(['Назад'])
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Выберите услугу для удаления:", reply_markup=reply_markup)
    return DELETE_SERVICE_SELECT

async def delete_service_select_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Назад':
        return await admin_panel(update, context)
    
    try:
        service_id = int(text.split(':')[0])
        service = db.get_service_by_id(service_id)
        if service:
            context.user_data['delete_service_id'] = service_id
            keyboard = [['Да, удалить', 'Нет, отменить']]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"Вы уверены, что хотите удалить услугу?\n"
                f"Название: {service[2]}\n"
                f"Цена: {service[3]} руб.\n"
                f"Время: {service[4]}",
                reply_markup=reply_markup
            )
            return DELETE_SERVICE_CONFIRM
        else:
            await update.message.reply_text("Услуга не найдена.")
    except (ValueError, IndexError):
        await update.message.reply_text("Неверный формат. Пожалуйста, выберите услугу из списка.")
    
    return DELETE_SERVICE_SELECT

async def delete_service_confirm_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Да, удалить':
        service_id = context.user_data.get('delete_service_id')
        if service_id:
            db.delete_service(service_id)
            await update.message.reply_text("✅ Услуга успешно удалена!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
        else:
            await update.message.reply_text("❌ Ошибка при удалении услуги.", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    else:
        await update.message.reply_text("❌ Удаление отменено.", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    
    # Очищаем временные данные
    for key in ['delete_category', 'delete_service_id']:
        context.user_data.pop(key, None)
    
    return ConversationHandler.END

# Добавление услуг
async def add_category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == 'Назад':
        return await admin_panel(update, context)
    
    if text not in ['Маникюр', 'Педикюр', 'Наращивание']:
        await update.message.reply_text("Пожалуйста, выберите категорию из предложенных вариантов.")
        return ADD_CATEGORY
    
    context.user_data['add_category'] = text
    await update.message.reply_text("Введите название новой услуги:", reply_markup=ReplyKeyboardRemove())
    return ADD_SERVICE_NAME

async def add_service_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['add_service_name'] = update.message.text
    await update.message.reply_text("Введите цену услуги (только число):")
    return ADD_SERVICE_PRICE

async def add_service_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text)
        context.user_data['add_service_price'] = price
        await update.message.reply_text("Введите время выполнения услуги (например: 2 часа):")
        return ADD_SERVICE_DURATION
    except ValueError:
        await update.message.reply_text("Неверный формат цены. Введите число:")
        return ADD_SERVICE_PRICE

async def add_service_duration_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    duration = update.message.text
    category = context.user_data['add_category']
    name = context.user_data['add_service_name']
    price = context.user_data['add_service_price']
    
    db.add_service(category, name, price, duration)
    
    # Очищаем временные данные
    for key in ['add_category', 'add_service_name', 'add_service_price']:
        context.user_data.pop(key, None)
    
    await update.message.reply_text("✅ Услуга успешно добавлена!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    return ConversationHandler.END

# Редактирование настроек
async def edit_channel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_channel = update.message.text
    db.update_setting('telegram_channel', new_channel)
    await update.message.reply_text("✅ Ссылка на канал успешно обновлена!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    return ConversationHandler.END

async def edit_website_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_website = update.message.text
    db.update_setting('website_url', new_website)
    await update.message.reply_text("✅ Ссылка на сайт успешно обновлена!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    return ConversationHandler.END

async def edit_location_lat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lat = float(update.message.text)
        context.user_data['new_lat'] = lat
        await update.message.reply_text("Введите новую долготу:")
        return EDIT_LOCATION_LON
    except ValueError:
        await update.message.reply_text("Неверный формат широты. Введите число:")
        return EDIT_LOCATION_LAT

async def edit_location_lon_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        lon = float(update.message.text)
        lat = context.user_data['new_lat']
        
        db.update_setting('location_lat', str(lat))
        db.update_setting('location_lon', str(lon))
        
        context.user_data.pop('new_lat', None)
        await update.message.reply_text("✅ Координаты успешно обновлены!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Неверный формат долготы. Введите число:")
        return EDIT_LOCATION_LON

async def edit_welcome_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_welcome = update.message.text
    db.update_setting('welcome_message', new_welcome)
    await update.message.reply_text("✅ Приветственное сообщение успешно обновлено!", reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True))
    return ConversationHandler.END

async def send_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    clients = db.get_clients(None)
    
    sent_count = 0
    failed_count = 0
    
    from main import application
    for client in clients:
        try:
            await application.bot.send_message(client[1], f"📢 Сообщение от администратора:\n\n{message}")
            sent_count += 1
        except Exception as e:
            logging.error(f"Error sending message to client {client[1]}: {e}")
            failed_count += 1
    
    await update.message.reply_text(
        f"✅ Рассылка завершена!\n"
        f"Успешно отправлено: {sent_count}\n"
        f"Не удалось отправить: {failed_count}",
        reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True)
    )
    return ConversationHandler.END

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Очищаем все временные данные
    for key in list(context.user_data.keys()):
        if key.startswith(('edit_', 'delete_', 'add_', 'new_')):
            context.user_data.pop(key, None)
    
    await update.message.reply_text(
        "❌ Действие отменено.",
        reply_markup=ReplyKeyboardMarkup([['/admin']], resize_keyboard=True)
    )
    return ConversationHandler.END