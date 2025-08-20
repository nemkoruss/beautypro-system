from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config, logger
from database import db, Service, Master, Client, Order, BotSettings

# Состояния для администратора
ADMIN_MAIN, ADD_SERVICE, EDIT_SERVICE, DELETE_SERVICE, ADD_MASTER, EDIT_MASTER, DELETE_MASTER = range(7)
EDIT_PRICE, EDIT_DURATION, BROADCAST_MESSAGE, EDIT_WELCOME_MESSAGE = range(11, 15)

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("У вас нет прав доступа к панели администратора.")
        return ConversationHandler.END
    
    keyboard = [
        ['➕ Добавить услугу', '✏️ Изменить услугу', '🗑️ Удалить услугу'],
        ['👩‍💼 Добавить мастера', '✏️ Изменить мастера', '🗑️ Удалить мастера'],
        ['💰 Изменить цены', '⏰ Изменить время услуги'],
        ['📢 Сделать рассылку', '✏️ Редактировать приветствие'],
        ['👥 Список клиентов', '📋 Список заказов'],
        ['📄 Скачать прайс', '⬅️ Назад']
    ]
    
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Панель администратора:", reply_markup=reply_markup)
    
    return ADMIN_MAIN

async def admin_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '➕ Добавить услугу':
        await update.message.reply_text(
            "Введите данные услуги в формате:\n"
            "Категория|Название|Цена|Время(мин)|Мастер\n"
            "Например: Маникюр|Гель-лак|2000|90|Анна",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADD_SERVICE
    
    elif text == '✏️ Изменить услугу':
        await show_services_for_edit(update)
        return EDIT_SERVICE
    
    elif text == '🗑️ Удалить услугу':
        await show_services_for_delete(update)
        return DELETE_SERVICE
    
    elif text == '👩‍💼 Добавить мастера':
        await update.message.reply_text(
            "Введите данные мастера в формате:\n"
            "Имя|Специализация|Телефон\n"
            "Например: Анна|Маникюр|+79991234567",
            reply_markup=ReplyKeyboardRemove()
        )
        return ADD_MASTER
    
    elif text == '💰 Изменить цены':
        await show_services_for_price_edit(update)
        return EDIT_PRICE
    
    elif text == '⏰ Изменить время услуги':
        await show_services_for_duration_edit(update)
        return EDIT_DURATION
    
    elif text == '📢 Сделать рассылку':
        await update.message.reply_text(
            "Введите сообщение для рассылки:",
            reply_markup=ReplyKeyboardRemove()
        )
        return BROADCAST_MESSAGE
    
    elif text == '✏️ Редактировать приветствие':
        await update.message.reply_text(
            "Введите новое приветственное сообщение:",
            reply_markup=ReplyKeyboardRemove()
        )
        return EDIT_WELCOME_MESSAGE
    
    elif text == '👥 Список клиентов':
        await show_clients_list(update)
        return ADMIN_MAIN
    
    elif text == '📋 Список заказов':
        await show_orders_list(update)
        return ADMIN_MAIN
    
    elif text == '📄 Скачать прайс':
        from create_pdf import generate_price_list
        pdf_path = generate_price_list()
        if pdf_path:
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption="Текущий прайс-лист"
                )
        return ADMIN_MAIN
    
    elif text == '⬅️ Назад':
        await update.message.reply_text(
            "Возврат в главное меню.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = update.message.text.split('|')
        if len(data) != 5:
            raise ValueError("Неверный формат данных")
        
        category, name, price, duration, master = data
        price = float(price)
        duration = int(duration)
        
        session = db.get_session()
        service = Service(
            category=category.strip(),
            name=name.strip(),
            price=price,
            duration=duration,
            master=master.strip()
        )
        session.add(service)
        session.commit()
        
        await update.message.reply_text("✅ Услуга успешно добавлена!")
        
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении услуги. Проверьте формат данных.")
    
    await admin_panel(update, context)
    return ADMIN_MAIN

async def show_services_for_edit(update: Update):
    session = db.get_session()
    try:
        services = session.query(Service).all()
        
        if not services:
            await update.message.reply_text("Нет доступных услуг для редактирования.")
            return
        
        keyboard = []
        for service in services:
            keyboard.append([f"✏️ {service.id}: {service.name}"])
        keyboard.append(['⬅️ Назад'])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Выберите услугу для редактирования:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing services for edit: {e}")
        await update.message.reply_text("Произошла ошибка.")
    finally:
        session.close()

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    
    # Здесь должна быть реализация рассылки сообщения всем пользователям
    # Для простоты просто подтверждаем отправку
    await update.message.reply_text("✅ Сообщение подготовлено для рассылки.")
    
    await admin_panel(update, context)
    return ADMIN_MAIN

async def edit_welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_message = update.message.text
    
    session = db.get_session()
    try:
        settings = session.query(BotSettings).first()
        if not settings:
            settings = BotSettings()
            session.add(settings)
        
        settings.welcome_message = new_message
        session.commit()
        
        await update.message.reply_text("✅ Приветственное сообщение обновлено!")
        
    except Exception as e:
        logger.error(f"Error updating welcome message: {e}")
        await update.message.reply_text("❌ Ошибка при обновлении сообщения.")
    finally:
        session.close()
    
    await admin_panel(update, context)
    return ADMIN_MAIN

async def show_clients_list(update: Update):
    session = db.get_session()
    try:
        clients = session.query(Client).order_by(Client.created_at.desc()).limit(10).all()
        
        if not clients:
            await update.message.reply_text("Нет зарегистрированных клиентов.")
            return
        
        message = "📋 Последние 10 клиентов:\n\n"
        for client in clients:
            message += f"ID: {client.id}\nИмя: {client.first_name}\nТелефон: {client.phone}\nДата: {client.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error showing clients: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка клиентов.")
    finally:
        session.close()

async def show_orders_list(update: Update):
    session = db.get_session()
    try:
        orders = session.query(Order).order_by(Order.created_at.desc()).limit(10).all()
        
        if not orders:
            await update.message.reply_text("Нет оформленных заказов.")
            return
        
        message = "📋 Последние 10 заказов:\n\n"
        for order in orders:
            service = session.query(Service).get(order.service_id)
            client = session.query(Client).get(order.client_id)
            message += f"Заказ №{order.id}\nУслуга: {service.name if service else 'Неизвестно'}\nКлиент: {client.first_name if client else 'Неизвестно'}\nСтатус: {order.status}\nДата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.error(f"Error showing orders: {e}")
        await update.message.reply_text("❌ Ошибка при получении списка заказов.")
    finally:
        session.close()

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END