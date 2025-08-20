from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from database import (
    get_services, add_service, update_service, delete_service,
    get_masters, add_master, update_master, delete_master,
    get_orders, update_order_status, get_users, get_service_by_id, get_master_by_id
)
from config import ADMIN_IDS
import logging
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
import io

logger = logging.getLogger(__name__)

router = Router()

# Определяем StatesGroup в самом начале
class AdminForm(StatesGroup):
    add_service_category = State()
    add_service_name = State()
    add_service_price = State()
    add_service_duration = State()
    edit_service_select = State()
    edit_service_details = State()
    delete_service_select = State()
    add_master_name = State()
    add_master_services = State()
    edit_master_select = State()
    edit_master_details = State()
    delete_master_select = State()
    broadcast_message = State()

# Регистрируем шрифты для поддержки кириллицы
try:
    # Попробуем зарегистрировать шрифты с поддержкой кириллицы
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'fonts/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'fonts/DejaVuSans-Bold.ttf'))
    logger.info("Шрифты DejaVuSans успешно зарегистрированы")
except Exception as e:
    logger.error(f"Ошибка при регистрации шрифтов: {e}")
    logger.warning("Используются стандартные шрифты, кириллица может отображаться некорректно")

# Фильтр для проверки администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Команда /admin - обрабатываем без фильтра, проверяем внутри функции
@router.message(Command("admin"))
async def admin_panel(message: types.Message, state: FSMContext):
    # Проверяем, является ли пользователь администратором
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для доступа к админ-панели.")
        return
    
    # Очищаем состояние на случай, если были активные процессы
    await state.clear()
    
    keyboard = [
        [types.KeyboardButton(text="Управление услугами")],
        [types.KeyboardButton(text="Управление мастерами")],
        [types.KeyboardButton(text="Рассылка")],
        [types.KeyboardButton(text="Список клиентов")],
        [types.KeyboardButton(text="Список заказов")],
        [types.KeyboardButton(text="Скачать прайс")],
        [types.KeyboardButton(text="Выйти из админки")]
    ]
    
    await message.answer(
        "Админ-панель:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

# Вспомогательная функция для проверки прав администратора
async def check_admin(message: types.Message) -> bool:
    if not is_admin(message.from_user.id):
        await message.answer("У вас нет прав для выполнения этой команды.")
        return False
    return True

# Выход из админки
@router.message(F.text == "Выйти из админки")
async def exit_admin(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.clear()
    await message.answer(
        "Вы вышли из админ-панели.",
        reply_markup=ReplyKeyboardRemove()
    )

# Управление услугами
@router.message(F.text == "Управление услугами")
async def manage_services(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    keyboard = [
        [types.KeyboardButton(text="Добавить услугу")],
        [types.KeyboardButton(text="Редактировать услугу")],
        [types.KeyboardButton(text="Удалить услугу")],
        [types.KeyboardButton(text="Назад в админ-панель")]
    ]
    
    await message.answer(
        "Управление услугами:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

# Добавление услуги
@router.message(F.text == "Добавить услугу")
async def add_service_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    keyboard = [
        [types.KeyboardButton(text="Маникюр")],
        [types.KeyboardButton(text="Педикюр")],
        [types.KeyboardButton(text="Отмена")]
    ]
    
    await message.answer(
        "Выберите категорию для новой услуги:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )
    await state.set_state(AdminForm.add_service_category)

@router.message(AdminForm.add_service_category, F.text.in_(["Маникюр", "Педикюр"]))
async def add_service_category(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.update_data(category=message.text)
    await message.answer(
        "Введите название услуги:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminForm.add_service_name)

@router.message(AdminForm.add_service_name)
async def add_service_name(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.update_data(name=message.text)
    await message.answer("Введите цену услуги (только число):")
    await state.set_state(AdminForm.add_service_price)

@router.message(AdminForm.add_service_price)
async def add_service_price(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        price = int(message.text)
        await state.update_data(price=price)
        await message.answer("Введите продолжительность услуги в минутах:")
        await state.set_state(AdminForm.add_service_duration)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную цену (только число):")

@router.message(AdminForm.add_service_duration)
async def add_service_duration(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        duration = int(message.text)
        data = await state.get_data()
        
        success = await add_service(data['category'], data['name'], data['price'], duration)
        
        if success:
            await message.answer("Услуга успешно добавлена!")
        else:
            await message.answer("Произошла ошибка при добавлении услуги.")
        
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer("Пожалуйста, введите корректную продолжительность (только число):")

# Редактирование услуги
@router.message(F.text == "Редактировать услугу")
async def edit_service_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    services = await get_services()
    if not services:
        await message.answer("Услуг пока нет.")
        return
    
    services_text = "\n".join([f"{s[0]}. {s[2]} - {s[3]} руб. ({s[1]})" for s in services])
    await message.answer(
        f"Введите ID услуги для редактирования:\n\n{services_text}"
    )
    await state.set_state(AdminForm.edit_service_select)

@router.message(AdminForm.edit_service_select)
async def edit_service_select(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        service_id = int(message.text)
        service = await get_service_by_id(service_id)
        if not service:
            await message.answer("Услуга с таким ID не найдена.")
            return
        
        await state.update_data(service_id=service_id)
        
        await message.answer(
            f"Редактирование услуги:\n"
            f"ID: {service[0]}\n"
            f"Категория: {service[1]}\n"
            f"Название: {service[2]}\n"
            f"Цена: {service[3]} руб.\n"
            f"Длительность: {service[4]} мин.\n\n"
            f"Введите новые данные в формате:\n"
            f"категория, название, цена, длительность\n\n"
            f"Пример: Маникюр, Классический маникюр, 1500, 60"
        )
        await state.set_state(AdminForm.edit_service_details)
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID:")

@router.message(AdminForm.edit_service_details)
async def edit_service_details(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        data = await state.get_data()
        service_id = data['service_id']
        
        parts = message.text.split(',')
        if len(parts) != 4:
            await message.answer("Неверный формат. Нужно ввести 4 значения через запятую.")
            return
        
        category = parts[0].strip()
        name = parts[1].strip()
        price = int(parts[2].strip())
        duration = int(parts[3].strip())
        
        success = await update_service(service_id, category, name, price, duration)
        
        if success:
            await message.answer("Услуга успешно обновлена!")
        else:
            await message.answer("Произошла ошибка при обновлении услуги.")
        
        await state.clear()
        await admin_panel(message)
    except ValueError:
        await message.answer("Пожалуйста, введите корректные числовые значения для цены и длительности.")

# Удаление услуги
@router.message(F.text == "Удалить услугу")
async def delete_service_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    services = await get_services()
    if not services:
        await message.answer("Услуг пока нет.")
        return
    
    services_text = "\n".join([f"{s[0]}. {s[2]} - {s[3]} руб. ({s[1]})" for s in services])
    await message.answer(
        f"Введите ID услуги для удаления:\n\n{services_text}"
    )
    await state.set_state(AdminForm.delete_service_select)

@router.message(AdminForm.delete_service_select)
async def delete_service_confirm(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        service_id = int(message.text)
        service = await get_service_by_id(service_id)
        if not service:
            await message.answer("Услуга с таким ID не найдена.")
            return
        
        keyboard = [
            [types.KeyboardButton(text="Да")],
            [types.KeyboardButton(text="Нет")]
        ]
        
        await state.update_data(service_id=service_id)
        await message.answer(
            f"Вы уверены, что хотите удалить услугу?\n"
            f"{service[2]} - {service[3]} руб. ({service[1]})",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        )
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID:")

@router.message(AdminForm.delete_service_select, F.text.in_(["Да", "Нет"]))
async def delete_service_final(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    if message.text == "Нет":
        await message.answer("Удаление отменено.")
        await state.clear()
        await admin_panel(message)
        return
    
    data = await state.get_data()
    service_id = data['service_id']
    
    success = await delete_service(service_id)
    if success:
        await message.answer("Услуга успешно удалена!")
    else:
        await message.answer("Произошла ошибка при удалении услуги.")
    
    await state.clear()
    await admin_panel(message)

# Управление мастерами
@router.message(F.text == "Управление мастерами")
async def manage_masters(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    keyboard = [
        [types.KeyboardButton(text="Добавить мастера")],
        [types.KeyboardButton(text="Редактировать мастера")],
        [types.KeyboardButton(text="Удалить мастера")],
        [types.KeyboardButton(text="Назад в админ-панель")]
    ]
    
    await message.answer(
        "Управление мастерами:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

# Добавление мастера
@router.message(F.text == "Добавить мастера")
async def add_master_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await message.answer(
        "Введите имя мастера:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminForm.add_master_name)

@router.message(AdminForm.add_master_name)
async def add_master_name(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.update_data(name=message.text)
    
    services = await get_services()
    services_text = "\n".join([f"{s[0]}. {s[2]} ({s[1]})" for s in services])
    
    await message.answer(
        f"Введите ID услуг, которые предоставляет мастер (через запятую):\n\n{services_text}"
    )
    await state.set_state(AdminForm.add_master_services)

@router.message(AdminForm.add_master_services)
async def add_master_services(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        services = [s.strip() for s in message.text.split(',')]
        # Проверяем, что все ID действительны
        all_services = await get_services()
        valid_services = [str(s[0]) for s in all_services]
        
        for service_id in services:
            if service_id not in valid_services:
                await message.answer(f"ID {service_id} не существует. Пожалуйста, введите корректные ID услуг:")
                return
        
        data = await state.get_data()
        services_str = ','.join(services)
        success = await add_master(data['name'], services_str)
        
        if success:
            await message.answer("Мастер успешно добавлен!")
        else:
            await message.answer("Произошла ошибка при добавлении мастера.")
        
        await state.clear()
        await admin_panel(message)
    except Exception as e:
        logger.error(f"Error adding master: {e}")
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
        await state.clear()

# Редактирование мастера
@router.message(F.text == "Редактировать мастера")
async def edit_master_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    masters = await get_masters()
    if not masters:
        await message.answer("Мастеров пока нет.")
        return
    
    masters_text = "\n".join([f"{m[0]}. {m[1]} (услуги: {m[2]})" for m in masters])
    await message.answer(
        f"Введите ID мастера для редактирования:\n\n{masters_text}"
    )
    await state.set_state(AdminForm.edit_master_select)

@router.message(AdminForm.edit_master_select)
async def edit_master_select(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        master_id = int(message.text)
        master = await get_master_by_id(master_id)
        if not master:
            await message.answer("Мастер с таким ID не найден.")
            return
        
        await state.update_data(master_id=master_id)
        
        services = await get_services()
        services_text = "\n".join([f"{s[0]}. {s[2]} ({s[1]})" for s in services])
        
        await message.answer(
            f"Редактирование мастера:\n"
            f"ID: {master[0]}\n"
            f"Имя: {master[1]}\n"
            f"Услуги: {master[2]}\n\n"
            f"Введите новые данные в формате:\n"
            f"имя, ID услуг через запятую\n\n"
            f"Пример: Анна, 1,2,3\n\n"
            f"Доступные услуги:\n{services_text}"
        )
        await state.set_state(AdminForm.edit_master_details)
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID:")

@router.message(AdminForm.edit_master_details)
async def edit_master_details(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        data = await state.get_data()
        master_id = data['master_id']
        
        parts = message.text.split(',')
        if len(parts) < 2:
            await message.answer("Неверный формат. Нужно ввести имя и хотя бы один ID услуги.")
            return
        
        name = parts[0].strip()
        services = [s.strip() for s in parts[1:]]
        
        # Проверяем, что все ID действительны
        all_services = await get_services()
        valid_services = [str(s[0]) for s in all_services]
        
        for service_id in services:
            if service_id not in valid_services:
                await message.answer(f"ID {service_id} не существует. Пожалуйста, введите корректные ID услуг:")
                return
        
        services_str = ','.join(services)
        success = await update_master(master_id, name, services_str)
        
        if success:
            await message.answer("Мастер успешно обновлен!")
        else:
            await message.answer("Произошла ошибка при обновлении мастера.")
        
        await state.clear()
        await admin_panel(message)
    except Exception as e:
        logger.error(f"Error editing master: {e}")
        await message.answer("Произошла ошибка. Попробуйте еще раз.")

# Удаление мастера
@router.message(F.text == "Удалить мастера")
async def delete_master_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    masters = await get_masters()
    if not masters:
        await message.answer("Мастеров пока нет.")
        return
    
    masters_text = "\n".join([f"{m[0]}. {m[1]} (услуги: {m[2]})" for m in masters])
    await message.answer(
        f"Введите ID мастера для удаления:\n\n{masters_text}"
    )
    await state.set_state(AdminForm.delete_master_select)

@router.message(AdminForm.delete_master_select)
async def delete_master_confirm(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    try:
        master_id = int(message.text)
        master = await get_master_by_id(master_id)
        if not master:
            await message.answer("Мастер с таким ID не найден.")
            return
        
        keyboard = [
            [types.KeyboardButton(text="Да")],
            [types.KeyboardButton(text="Нет")]
        ]
        
        await state.update_data(master_id=master_id)
        await message.answer(
            f"Вы уверены, что хотите удалить мастера?\n{master[1]} (услуги: {master[2]})",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        )
    except ValueError:
        await message.answer("Пожалуйста, введите числовой ID:")

@router.message(AdminForm.delete_master_select, F.text.in_(["Да", "Нет"]))
async def delete_master_final(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    if message.text == "Нет":
        await message.answer("Удаление отменено.")
        await state.clear()
        await admin_panel(message)
        return
    
    data = await state.get_data()
    master_id = data['master_id']
    
    success = await delete_master(master_id)
    if success:
        await message.answer("Мастер успешно удален!")
    else:
        await message.answer("Произошла ошибка при удалении мастера.")
    
    await state.clear()
    await admin_panel(message)

# Рассылка
@router.message(F.text == "Рассылка")
async def broadcast_start(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await message.answer(
        "Введите сообщение для рассылки:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminForm.broadcast_message)

@router.message(AdminForm.broadcast_message)
async def broadcast_message(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    users = await get_users()
    success_count = 0
    fail_count = 0
    
    for user in users:
        try:
            await message.send_copy(user[0])
            success_count += 1
        except Exception as e:
            logger.error(f"Error sending message to user {user[0]}: {e}")
            fail_count += 1
    
    await message.answer(
        f"Рассылка завершена.\nУспешно: {success_count}\nНе удалось: {fail_count}"
    )
    await state.clear()

# Список клиентов
@router.message(F.text == "Список клиентов")
async def clients_list(message: types.Message):
    if not await check_admin(message):
        return
    
    orders = await get_orders()
    
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    
    # Группируем заказы по телефону клиента
    clients = {}
    for order in orders:
        phone = order[2]
        if phone not in clients:
            clients[phone] = {
                'name': order[1],
                'orders': []
            }
        clients[phone]['orders'].append(order)
    
    response = "Список клиентов:\n\n"
    for i, (phone, data) in enumerate(clients.items(), 1):
        response += f"{i}. {data['name']} - {phone}\n"
        response += f"   Заказов: {len(data['orders'])}\n\n"
    
    # Разбиваем сообщение на части, если оно слишком длинное
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await message.answer(response[x:x+4096])
    else:
        await message.answer(response)

# Список заказов
@router.message(F.text == "Список заказов")
async def orders_list(message: types.Message):
    if not await check_admin(message):
        return
    
    orders = await get_orders()
    
    if not orders:
        await message.answer("Заказов пока нет.")
        return
    
    response = "Список заказов:\n\n"
    for order in orders:
        response += (f"Заказ №{order[0]}\n"
                    f"Клиент: {order[1]}\n"
                    f"Телефон: {order[2]}\n"
                    f"Категория: {order[3]}\n"
                    f"Услуга: {order[4]}\n"
                    f"Цена: {order[5]} руб.\n"
                    f"Мастер: {order[6]}\n"
                    f"Статус: {order[7]}\n"
                    f"Дата: {order[8]}\n\n")
    
    # Разбиваем сообщение на части, если оно слишком длинное
    if len(response) > 4096:
        for x in range(0, len(response), 4096):
            await message.answer(response[x:x+4096])
    else:
        await message.answer(response)

# Генерация PDF прайса с поддержкой кириллицы и кодировкой UTF-8
@router.message(F.text == "Скачать прайс")
async def download_price(message: types.Message):
    if not await check_admin(message):
        return
    
    services = await get_services()
    
    if not services:
        await message.answer("Услуг пока нет.")
        return
    
    try:
        # Создаем PDF в памяти с правильной кодировкой
        buffer = io.BytesIO()
        
        # Используем SimpleDocTemplate для лучшей поддержки UTF-8
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Создаем стили для текста
        styles = getSampleStyleSheet()
        
        # Создаем собственные стили с поддержкой кириллицы
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            spaceBefore=12
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=6
        )
        
        # Пытаемся использовать шрифты с поддержкой кириллицы
        try:
            title_style.fontName = 'DejaVuSans-Bold'
            heading_style.fontName = 'DejaVuSans-Bold'
            normal_style.fontName = 'DejaVuSans'
        except:
            # Если шрифты не найдены, используем стандартные
            logger.warning("Используются стандартные шрифты")
        
        # Собираем содержимое PDF
        story = []
        
        # Заголовок
        title = Paragraph("Прайс-лист студии маникюра", title_style)
        story.append(title)
        
        # Группируем услуги по категориям
        categories = {}
        for service in services:
            category = service[1]
            if category not in categories:
                categories[category] = []
            categories[category].append(service)
        
        # Добавляем услуги в PDF
        for category, services_in_category in categories.items():
            # Заголовок категории
            category_heading = Paragraph(category, heading_style)
            story.append(category_heading)
            
            # Услуги в категории
            for service in services_in_category:
                service_text = f"{service[2]} - {service[3]} руб. ({service[4]} мин.)"
                service_paragraph = Paragraph(service_text, normal_style)
                story.append(service_paragraph)
            
            # Добавляем отступ между категориями
            story.append(Spacer(1, 12))
        
        # Генерируем PDF
        doc.build(story)
        buffer.seek(0)
        
        # Сохраняем временный файл
        with open("price_list.pdf", "wb") as f:
            f.write(buffer.getvalue())
        
        # Отправляем файл
        await message.answer_document(
            FSInputFile("price_list.pdf", filename="price_list.pdf"),
            caption="Прайс-лист услуг"
        )
        
        # Удаляем временный файл
        os.remove("price_list.pdf")
        
    except Exception as e:
        logger.error(f"Ошибка при генерации PDF: {e}")
        await message.answer("Произошла ошибка при генерации прайс-листа.")

# Обработка кнопки "Назад в админ-панель"
@router.message(F.text == "Назад в админ-панель")
async def back_to_admin(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.clear()
    await admin_panel(message)

# Обработка отмены
@router.message(F.text == "Отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    if not await check_admin(message):
        return
    
    await state.clear()
    await message.answer(
        "Действие отменено.",
        reply_markup=ReplyKeyboardRemove()
    )
    await admin_panel(message)

# Обработчик для любых других сообщений в админке
@router.message()
async def admin_other_messages(message: types.Message):
    # Проверяем, является ли пользователь администратором
    if not is_admin(message.from_user.id):
        return  # Не отвечаем на сообщения не-администраторов
    
    await message.answer("Используйте меню админ-панели для навигации.")