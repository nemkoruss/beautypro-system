from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging
from config import config, logger
from database import db, Service, Master, Client, Order, BotSettings

async def show_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in config.ADMIN_IDS:
        await update.message.reply_text("У вас нет прав доступа к панели администратора.")
        return
    
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

async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    print(f"Админское сообщение: {text}")  # Для отладки
    
    if text == '⬅️ Назад':
        await update.message.reply_text(
            "Возврат в главное меню.",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    elif text == '➕ Добавить услугу':
        await update.message.reply_text(
            "Введите данные услуги в формате:\n"
            "Категория|Название|Цена|Время(мин)|Мастер\n"
            "Например: Маникюр|Гель-лак|2000|90|Анна",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif text == '👩‍💼 Добавить мастера':
        await update.message.reply_text(
            "Введите данные мастера в формате:\n"
            "Имя|Специализация|Телефон\n"
            "Например: Анна|Маникюр|+79991234567",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif text == '💰 Изменить цены':
        await show_services_for_edit(update, 'price')
    
    elif text == '⏰ Изменить время услуги':
        await show_services_for_edit(update, 'duration')
    
    elif text == '📢 Сделать рассылку':
        await update.message.reply_text(
            "Введите сообщение для рассылки:",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif text == '✏️ Редактировать приветствие':
        await update.message.reply_text(
            "Введите новое приветственное сообщение:",
            reply_markup=ReplyKeyboardRemove()
        )
    
    elif text == '👥 Список клиентов':
        await show_clients_list(update)
    
    elif text == '📋 Список заказов':
        await show_orders_list(update)
    
    elif text == '📄 Скачать прайс':
        from create_pdf import generate_price_list
        pdf_path = generate_price_list()
        if pdf_path:
            with open(pdf_path, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption="Текущий прайс-лист"
                )
    
    else:
        # Обработка ввода данных (добавление услуги, мастера и т.д.)
        await process_admin_input(update, context, text)

async def show_services_for_edit(update: Update, edit_type: str):
    session = db.get_session()
    try:
        services = session.query(Service).all()
        
        if not services:
            await update.message.reply_text("Нет доступных услуг.")
            return
        
        keyboard = []
        for service in services:
            if edit_type == 'price':
                keyboard.append([f"💰 {service.name} - {service.price} руб."])
            else:
                keyboard.append([f"⏰ {service.name} - {service.duration} мин."])
        
        keyboard.append(['⬅️ Назад'])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        if edit_type == 'price':
            await update.message.reply_text("Выберите услугу для изменения цены:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Выберите услугу для изменения времени:", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing services for edit: {e}")
        await update.message.reply_text("Произошла ошибка.")
    finally:
        session.close()

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

async def process_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    # Здесь можно добавить обработку введенных данных
    # Например, добавление услуги или мастера
    if '|' in text:
        parts = text.split('|')
        if len(parts) == 5:  # Услуга: Категория|Название|Цена|Время|Мастер
            await add_service(update, parts)
        elif len(parts) == 3:  # Мастер: Имя|Специализация|Телефон
            await add_master(update, parts)
        else:
            await update.message.reply_text("Неверный формат данных. Попробуйте снова.")
    else:
        await update.message.reply_text("Команда не распознана. Используйте меню администратора.")

async def add_service(update: Update, parts: list):
    try:
        category, name, price, duration, master = parts
        price = float(price.strip())
        duration = int(duration.strip())
        
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
        await show_admin_menu(update, None)
        
    except Exception as e:
        logger.error(f"Error adding service: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении услуги. Проверьте формат данных.")

async def add_master(update: Update, parts: list):
    try:
        name, specialization, phone = parts
        
        session = db.get_session()
        master = Master(
            name=name.strip(),
            specialization=specialization.strip(),
            phone=phone.strip()
        )
        session.add(master)
        session.commit()
        
        await update.message.reply_text("✅ Мастер успешно добавлен!")
        await show_admin_menu(update, None)
        
    except Exception as e:
        logger.error(f"Error adding master: {e}")
        await update.message.reply_text("❌ Ошибка при добавлении мастера. Проверьте формат данных.")