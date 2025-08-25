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
    if update.message.from_user.id in config.ADMIN_IDS:
        return
    
    text = update.message.text
    
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
    
    # Обработка кнопок услуг
    elif ' - ' in text and ' руб. (' in text:
        service_name = text.split(' - ')[0]
        await show_service_details(update, service_name)
    
    # Обработка кнопки "Назад" из меню услуг
    elif text == '⬅️ Назад':
        await show_main_menu(update)
    
    # Обработка выбора мастера
    elif text.startswith('Выбрать мастера'):
        master_name = text.split('(')[1].split(')')[0]
        await ask_for_phone(update, context, master_name)
    
    # Обработка ввода телефона (если ожидаем телефон)
    elif 'awaiting_phone' in context.user_data:
        await process_phone_input(update, context)

async def show_services(update: Update, category: str):
    session = db.get_session()
    try:
        services = session.query(Service).filter_by(category=category).all()
        
        if not services:
            await update.message.reply_text("Услуги временно недоступны.")
            return
        
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

async def show_service_details(update: Update, service_name: str):
    session = db.get_session()
    try:
        service = session.query(Service).filter_by(name=service_name).first()
        
        if service:
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
            
    except Exception as e:
        logger.error(f"Error showing service details: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")
    finally:
        session.close()

async def ask_for_phone(update: Update, context: ContextTypes.DEFAULT_TYPE, master_name: str):
    # Сохраняем данные о мастере в context
    context.user_data['awaiting_phone'] = True
    context.user_data['master'] = master_name
    
    # Находим услугу по имени мастера
    session = db.get_session()
    try:
        service = session.query(Service).filter_by(master=master_name).first()
        if service:
            context.user_data['service'] = service.name
            context.user_data['category'] = service.category
            context.user_data['price'] = service.price
            context.user_data['duration'] = service.duration
            
    except Exception as e:
        logger.error(f"Error finding service: {e}")
    finally:
        session.close()
    
    await update.message.reply_text(
        "Пожалуйста, введите ваш номер телефона для связи:",
        reply_markup=ReplyKeyboardRemove()
    )

async def process_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    
    # Проверяем, не является ли это командой "Назад"
    if phone == '⬅️ Назад':
        await show_main_menu(update)
        context.user_data.pop('awaiting_phone', None)
        return
    
    # Валидация номера телефона
    if not any(char.isdigit() for char in phone) or len(phone) < 5:
        await update.message.reply_text("Пожалуйста, введите корректный номер телефона:")
        return
    
    session = db.get_session()
    try:
        # Сохраняем клиента
        client = Client(
            telegram_id=update.message.from_user.id,
            first_name=update.message.from_user.first_name,
            phone=phone
        )
        session.add(client)
        session.flush()
        
        # Находим услугу по сохраненным данным
        service_name = context.user_data.get('service')
        service = session.query(Service).filter_by(name=service_name).first()
        
        if service:
            # Сохраняем заказ
            order = Order(
                client_id=client.id,
                service_id=service.id,
                master_name=context.user_data.get('master'),
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
                             f"Категория услуг - {context.user_data.get('category')}\n"
                             f"Услуга - {service.name}\n"
                             f"Стоимость - {service.price} руб.\n"
                             f"Время оказания услуги - {service.duration} мин.\n"
                             f"Мастер - {context.user_data.get('master')}\n\n"
                             f"Свяжитесь с клиентом для согласования дня и времени!"
                    )
                except Exception as e:
                    logger.error(f"Error sending notification to admin {admin_id}: {e}")
            
            await update.message.reply_text(
                "✅ Спасибо за заявку! Наш администратор свяжется с вами в ближайшее время для уточнения деталей.",
                reply_markup=ReplyKeyboardRemove()
            )
            
            # Очищаем данные
            context.user_data.clear()
            await show_main_menu(update)
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving order: {e}")
        await update.message.reply_text("Произошла ошибка при сохранении заказа. Пожалуйста, попробуйте позже.")
    finally:
        session.close()
        context.user_data.pop('awaiting_phone', None)