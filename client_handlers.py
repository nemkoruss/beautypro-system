from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, FSInputFile
import phonenumbers
from database import get_services, get_masters_by_service, add_order, add_user, generate_price_pdf
from config import ADMIN_IDS
import logging
import os

logger = logging.getLogger(__name__)

router = Router()

class OrderForm(StatesGroup):
    choosing_service = State()
    choosing_master = State()
    entering_phone = State()

@router.message(Command("start"))
async def start_command(message: types.Message, state: FSMContext):
    await state.clear()
    await add_user(message.from_user.id, message.from_user.username, 
                  message.from_user.first_name, message.from_user.last_name)
    
    keyboard = [
        [types.KeyboardButton(text="Маникюр")],
        [types.KeyboardButton(text="Педикюр")],
        [types.KeyboardButton(text="Скачать прайс")],
        [types.KeyboardButton(text="Перейти на сайт")]
    ]
    
    await message.answer(
        "Добро пожаловать в студию маникюра! Выберите категорию услуг:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "Для записи на услугу нажмите /start и следуйте инструкциям.\n\n"
        "Если у вас возникли проблемы, свяжитесь с нами по телефону: +7 (XXX) XXX-XX-XX"
    )

@router.message(F.text == "Маникюр")
@router.message(F.text == "Педикюр")
async def choose_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    services = await get_services(message.text)
    
    if not services:
        await message.answer("В этой категории пока нет услуг.")
        return
    
    keyboard = [[types.KeyboardButton(text=f"{service[1]} - {service[2]} руб.")] for service in services]
    keyboard.append([types.KeyboardButton(text="Назад")])
    
    await message.answer(
        "Выберите услугу:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )
    await state.set_state(OrderForm.choosing_service)

@router.message(OrderForm.choosing_service, F.text == "Назад")
async def back_to_categories(message: types.Message, state: FSMContext):
    await state.clear()
    keyboard = [
        [types.KeyboardButton(text="Маникюр")],
        [types.KeyboardButton(text="Педикюр")],
        [types.KeyboardButton(text="Скачать прайс")],
        [types.KeyboardButton(text="Перейти на сайт")]
    ]
    
    await message.answer(
        "Выберите категорию услуг:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )

@router.message(OrderForm.choosing_service)
async def choose_service(message: types.Message, state: FSMContext):
    try:
        data = await state.get_data()
        services = await get_services(data['category'])
        
        # Ищем выбранную услугу
        selected_service = None
        for service in services:
            if message.text.startswith(service[1]):
                selected_service = service
                break
        
        if not selected_service:
            await message.answer("Пожалуйста, выберите услугу из списка.")
            return
        
        await state.update_data(
            service=selected_service[1],
            price=selected_service[2],
            service_id=selected_service[0]
        )
        
        masters = await get_masters_by_service(selected_service[0])
        
        if not masters:
            await message.answer("К сожалению, сейчас нет доступных мастеров для этой услуги.")
            return
        
        keyboard = [[types.KeyboardButton(text=master[1])] for master in masters]
        keyboard.append([types.KeyboardButton(text="Назад")])
        
        await message.answer(
            f"Вы выбрали: {selected_service[1]}\nЦена: {selected_service[2]} руб.\n\nВыберите мастера:",
            reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
        )
        await state.set_state(OrderForm.choosing_master)
    except Exception as e:
        logger.error(f"Error in choose_service: {e}")
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
        await state.clear()

@router.message(OrderForm.choosing_master, F.text == "Назад")
async def back_to_services(message: types.Message, state: FSMContext):
    data = await state.get_data()
    services = await get_services(data['category'])
    
    keyboard = [[types.KeyboardButton(text=f"{service[1]} - {service[2]} руб.")] for service in services]
    keyboard.append([types.KeyboardButton(text="Назад")])
    
    await message.answer(
        "Выберите услугу:",
        reply_markup=types.ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )
    await state.set_state(OrderForm.choosing_service)

@router.message(OrderForm.choosing_master)
async def choose_master(message: types.Message, state: FSMContext):
    await state.update_data(master=message.text)
    await message.answer(
        "Введите ваш номер телефона для связи:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(OrderForm.entering_phone)

@router.message(OrderForm.entering_phone)
async def enter_phone(message: types.Message, state: FSMContext):
    try:
        # Валидация номера телефона
        phone_number = phonenumbers.parse(message.text, "RU")
        if not phonenumbers.is_valid_number(phone_number):
            await message.answer("Пожалуйста, введите корректный номер телефона.")
            return
        
        formatted_phone = phonenumbers.format_number(phone_number, phonenumbers.PhoneNumberFormat.E164)
        
        data = await state.get_data()
        order_id = await add_order(
            message.from_user.full_name,
            formatted_phone,
            data['category'],
            data['service'],
            data['price'],
            data['master']
        )
        
        if order_id:
            # Отправка уведомления администраторам
            for admin_id in ADMIN_IDS:
                try:
                    await message.bot.send_message(
                        admin_id,
                        f"Новая заявка №{order_id}:\n"
                        f"Имя: {message.from_user.full_name}\n"
                        f"Телефон: {formatted_phone}\n"
                        f"Категория: {data['category']}\n"
                        f"Услуга: {data['service']}\n"
                        f"Стоимость: {data['price']} руб.\n"
                        f"Мастер: {data['master']}\n\n"
                        "Свяжитесь с клиентом для согласования даты и времени!"
                    )
                except Exception as e:
                    logger.error(f"Error sending notification to admin {admin_id}: {e}")
            
            await message.answer(
                "Ваша заявка принята! Наш администратор свяжется с вами в ближайшее время для уточнения деталей.\n\n"
                "Для нового заказа нажмите /start"
            )
        else:
            await message.answer("Произошла ошибка при оформлении заказа. Попробуйте еще раз.")
        
        await state.clear()
    except phonenumbers.NumberParseException:
        await message.answer("Пожалуйста, введите корректный номер телефона.")
    except Exception as e:
        logger.error(f"Error in enter_phone: {e}")
        await message.answer("Произошла ошибка. Попробуйте еще раз.")
        await state.clear()

# Добавляем обработчик для кнопки "Скачать прайс"
@router.message(F.text == "Скачать прайс")
async def download_price_client(message: types.Message):
    try:
        # Генерируем PDF с прайсом
        pdf_buffer = await generate_price_pdf()
        
        if not pdf_buffer:
            await message.answer("В настоящее время прайс-лист недоступен. Попробуйте позже.")
            return
        
        # Сохраняем временный файл
        with open("price_list.pdf", "wb") as f:
            f.write(pdf_buffer.getvalue())
        
        # Отправляем файл
        await message.answer_document(
            FSInputFile("price_list.pdf", filename="price_list.pdf"),
            caption="Прайс-лист услуг нашей студии"
        )
        
        # Удаляем временный файл
        os.remove("price_list.pdf")
        
    except Exception as e:
        logger.error(f"Error generating price list: {e}")
        await message.answer("Произошла ошибка при генерации прайс-листа. Попробуйте позже.")

# Добавляем обработчик для кнопки "Перейти на сайт"
@router.message(F.text == "Перейти на сайт")
async def go_to_website(message: types.Message):
    website_url = "https://ноготочки-точка.рф/"
    await message.answer(
        f"🌐 Перейдите на наш сайт: {website_url}\n\n"
        "Там вы найдете:\n"
        "• Больше информации о наших услугах\n"
        "• Галерею наших работ\n"
        "• Специальные предложения и акции\n"
        "• Контактную информацию и график работы\n\n"
        "Мы всегда рады видеть вас! ✨"
    )

@router.message(F.text == "Отмена")
@router.message(Command("cancel"))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Действие отменено. Для нового заказа нажмите /start",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик для любых других сообщений
@router.message()
async def other_messages(message: types.Message):
    await message.answer(
        "Используйте кнопки меню для навигации или нажмите /start для начала работы с ботом."
    )