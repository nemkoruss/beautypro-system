from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes
import logging
from config import config, logger
from database import db, Service, Master, Client, Order, BotSettings

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
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