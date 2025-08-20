from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import logging
from database import db
from config import Config

logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Состояния для администратора
ADMIN_MAIN, ADMIN_SERVICES, ADMIN_MASTERS = range(3)

def create_admin_keyboard():
    keyboard = [
        ['➕ Добавить услугу', '➖ Удалить услугу'],
        ['✏️ Изменить услугу', '👩‍💼 Управление мастерами'],
        ['💰 Изменить цены', '⏱ Изменить время услуг'],
        ['📢 Рекламное сообщение', '✉️ Редактировать приветствие'],
        ['📋 Список клиентов', '📊 Список заказов'],
        ['📄 Скачать прайс', '🔙 Назад']
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id not in Config.ADMIN_IDS:
        await update.message.reply_text("Доступ запрещен.")
        return
    
    await update.message.reply_text(
        "👑 Панель администратора\n\nВыберите действие:",
        reply_markup=create_admin_keyboard()
    )
    
    return ADMIN_MAIN

async def handle_admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text
    
    if action == '🔙 Назад':
        await update.message.reply_text(
            "Возврат в главное меню",
            reply_markup=ReplyKeyboardMarkup([['/start']], resize_keyboard=True)
        )
        return ConversationHandler.END
    
    elif action == '📋 Список клиентов':
        clients = db.get_clients()
        if not clients:
            await update.message.reply_text("Клиентов пока нет.")
            return ADMIN_MAIN
        
        message = "📋 Список клиентов:\n\n"
        for client in clients:
            message += f"👤 {client[3]} {client[4] or ''}\n📞 {client[5] or 'Не указан'}\n📅 {client[6]}\n\n"
        
        await update.message.reply_text(message[:4000])
    
    elif action == '📊 Список заказов':
        orders = db.get_orders()
        if not orders:
            await update.message.reply_text("Заказов пока нет.")
            return ADMIN_MAIN
        
        message = "📊 Список заказов:\n\n"
        for order in orders:
            status = "✅ Выполнен" if order[4] == 'completed' else "⏳ Ожидает"
            message += f"№{order[0]} - {status}\n👤 {order[7]}\n📞 {order[8]}\n💅 {order[9]}\n💰 {order[10]} руб.\n👩‍💼 {order[12]}\n\n"
        
        await update.message.reply_text(message[:4000])
    
    elif action == '👩‍💼 Управление мастерами':
        masters = db.get_masters()
        message = "👩‍💼 Текущие мастера:\n\n"
        for master in masters:
            message += f"ID{master[0]}: {master[1]} - {master[2] or 'Нет специализации'}\n"
        
        message += "\nВыберите действие с мастерами:"
        keyboard = [['➕ Добавить мастера', '➖ Удалить мастера'], ['🔙 Назад']]
        
        await update.message.reply_text(
            message,
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        )
        return ADMIN_MASTERS
    
    else:
        await update.message.reply_text(
            "Функция в разработке. Скоро будет доступна!",
            reply_markup=create_admin_keyboard()
        )
    
    return ADMIN_MAIN

async def handle_masters_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text
    
    if action == '🔙 Назад':
        await update.message.reply_text(
            "Возврат в панель администратора",
            reply_markup=create_admin_keyboard()
        )
        return ADMIN_MAIN
    
    await update.message.reply_text(
        "Функция управления мастерами в разработке.",
        reply_markup=create_admin_keyboard()
    )
    return ADMIN_MAIN

async def admin_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Действие отменено.",
        reply_markup=create_admin_keyboard()
    )
    return ConversationHandler.END