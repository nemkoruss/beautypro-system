from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from config import config, logger
from database import db, Service, Client, Order, BotSettings  # Добавили BotSettings

# Состояния для ConversationHandler
SELECT_SERVICE, SELECT_MASTER, ENTER_PHONE = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in config.ADMIN_IDS:
        await update.message.reply_text(
            "Добро пожаловать, администратор! Используйте /admin для управления.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    session = db.get_session()
    try:
        # Получаем приветственное сообщение из настроек
        settings = session.query(BotSettings).first()  # Исправили на BotSettings
        welcome_message = settings.welcome_message if settings else "Добро пожаловать в нашу студию маникюра!"
        
        keyboard = [
            ['💅 Маникюр', '🦶 Педикюр'],
            ['📢 Перейти в Telegram канал', '🌐 Посетить сайт'],
            ['📞 Позвонить', '📍 Посмотреть адрес на карte'],
            ['📄 Скачать прайс в PDF']
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error in start: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()
    
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in config.ADMIN_IDS:
        return
    
    text = update.message.text
    
    if text == '💅 Маникюр' or text == '🦶 Педикюр':
        category = 'Маникюр' if text == '💅 Маникюр' else 'Педикюр'
        context.user_data['category'] = category
        await show_services(update, context, category)
        return SELECT_SERVICE
    
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
    
    return ConversationHandler.END

async def show_services(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    session = db.get_session()
    try:
        services = session.query(Service).filter_by(category=category).all()
        
        if not services:
            await update.message.reply_text("Услуги временно недоступны.")
            return ConversationHandler.END
        
        keyboard = []
        for service in services:
            keyboard.append([f"{service.name} - {service.price} руб. ({service.duration} мин)"])
        keyboard.append(['⬅️ Назад'])
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"Выберите услугу ({category}):", reply_markup=reply_markup)
        
    except Exception as e:
        logger.error(f"Error showing services: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()

async def select_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Назад':
        await start(update, context)
        return ConversationHandler.END
    
    session = db.get_session()
    try:
        # Извлекаем название услуги из текста
        service_name = text.split(' - ')[0]
        service = session.query(Service).filter_by(name=service_name).first()
        
        if service:
            context.user_data['service'] = service
            context.user_data['service_name'] = service.name
            
            keyboard = [
                [f"Выбрать мастера ({service.master})"],
                ['⬅️ Назад']
            ]
            
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                f"Услуга: {service.name}\n"
                f"Цена: {service.price} руб.\n"
                f"Время: {service.duration} мин.\n"
                f"Мастер: {service.master}\n\n"
                f"Выберите действие:",
                reply_markup=reply_markup
            )
            
            return SELECT_MASTER
        else:
            await update.message.reply_text("Услуга не найдена. Пожалуйста, выберите из списка.")
            return SELECT_SERVICE
        
    except Exception as e:
        logger.error(f"Error selecting service: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()
    
    return SELECT_SERVICE

async def select_master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == '⬅️ Назад':
        await show_services(update, context, context.user_data['category'])
        return SELECT_SERVICE
    
    session = db.get_session()
    try:
        service = context.user_data.get('service')
        
        if service:
            context.user_data['master'] = service.master
            
            await update.message.reply_text(
                "Пожалуйста, введите ваш номер телефона для связи:",
                reply_markup=ReplyKeyboardRemove()
            )
            
            return ENTER_PHONE
        
    except Exception as e:
        logger.error(f"Error selecting master: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()
    
    return SELECT_MASTER

async def enter_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    
    # Простая валидация номера телефона
    if not any(char.isdigit() for char in phone) or len(phone) < 5:
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона:")
        return ENTER_PHONE
    
    session = db.get_session()
    try:
        # Сохраняем клиента
        client = Client(
            telegram_id=update.message.from_user.id,
            first_name=update.message.from_user.first_name,
            phone=phone
        )
        session.add(client)
        session.flush()  # Получаем ID клиента
        
        # Сохраняем заказ
        service = context.user_data.get('service')
        order = Order(
            client_id=client.id,
            service_id=service.id,
            master_name=context.user_data.get('master', 'Не указан'),
            status='pending'
        )
        session.add(order)
        
        session.commit()
        
        # Отправляем уведомление администраторам
        for admin_id in config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"🎉 Новый заказ!\n"
                         f"Клиент № {client.id}:\n"
                         f"Имя - {client.first_name}\n"
                         f"Телефон - {client.phone}\n"
                         f"Категория услуг - {context.user_data['category']}\n"
                         f"Услуга - {service.name}\n"
                         f"Стоимость - {service.price} руб.\n"
                         f"Время оказания услуги - {service.duration} мин.\n"
                         f"Мастер - {context.user_data.get('master', 'Не указан')}\n\n"
                         f"Свяжитесь с клиентом для согласования дня и времени!"
                )
            except Exception as e:
                logger.error(f"Error sending notification to admin {admin_id}: {e}")
        
        await update.message.reply_text(
            "✅ Спасибо за заявку! Наш администратор свяжется с вами в ближайшее время для уточнения деталей.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Возвращаем к началу
        await start(update, context)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving order: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении заказа. Пожалуйста, попробуйте позже.")
    finally:
        session.close()
    
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    await start(update, context)
    return ConversationHandler.END