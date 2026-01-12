from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.message(Command("start"))
async def start_handler(message: Message):
    """Обработчик команды /start"""
    from database.database import Database
    from keyboards.inline import get_agreement_keyboard, get_main_menu_keyboard
    from utils.texts import TEXTS
    
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    db = Database()
    
    # Проверяем есть ли реферальный параметр
    args = message.text.split()
    referral_code = None
    if len(args) > 1 and args[1].startswith("ref_"):
        referral_code = args[1].replace("ref_", "")
    
    # Проверяем, есть ли пользователь в базе
    user = db.get_user(user_id)
    
    if not user:
        # Новый пользователь - добавляем в БД
        db.add_user(user_id, username, first_name, last_name)
        
        # Генерируем реферальный код
        db.generate_referral_code(user_id)
        
        # Если есть реферальный код - привязываем
        if referral_code:
            referrer_id = db.get_user_by_referral_code(referral_code)
            if referrer_id and referrer_id != user_id:
                db.set_referrer(user_id, referrer_id)
                print(f"✅ Пользователь {user_id} зарегистрирован по реферальной ссылке от {referrer_id}")
        
        # Показываем соглашение
        await message.answer(
            TEXTS['agreement_text'],
            parse_mode="HTML",
            reply_markup=get_agreement_keyboard()
        )
    else:
        # Пользователь уже есть
        if db.user_agreed_to_terms(user_id):
            # Уже согласился - показываем главное меню
            await message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            # Ещё не согласился - показываем соглашение
            await message.answer(
                TEXTS['agreement_text'],
                parse_mode="HTML",
                reply_markup=get_agreement_keyboard()
            )


@router.callback_query(lambda c: c.data == "confirm_agreement")
async def confirm_agreement_handler(callback):
    """Обработчик подтверждения согласия"""
    from database.database import Database
    from keyboards.inline import get_main_menu_keyboard
    from utils.texts import TEXTS
    
    user_id = callback.from_user.id
    
    db = Database()
    db.update_user_agreement(user_id)
    
    await callback.message.delete()
    await callback.message.answer(
        TEXTS['welcome_message'],
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "main_menu")
async def main_menu_handler(callback):
    """Обработчик кнопки 'Главное меню'"""
    from keyboards.inline import get_main_menu_keyboard
    from utils.texts import TEXTS
    
    # Пытаемся отредактировать сообщение
    try:
        await callback.message.edit_text(
            TEXTS['welcome_message'],
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    except:
        # Если не получилось (например, сообщение с видео), удаляем и отправляем новое
        try:
            await callback.message.delete()
        except:
            pass
        
        await callback.message.answer(
            TEXTS['welcome_message'],
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    
    await callback.answer()


@router.message(Command("menu"))
async def menu_command_handler(message: Message):
    """Обработчик команды /menu"""
    from keyboards.inline import get_main_menu_keyboard
    from utils.texts import TEXTS
    
    await message.answer(
        TEXTS['welcome_message'],
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )


@router.message(Command("pay"))
async def pay_command_handler(message: Message):
    """Обработчик команды /pay"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="80₽", callback_data="amount_80"),
                InlineKeyboardButton(text="160₽", callback_data="amount_160"),
                InlineKeyboardButton(text="320₽", callback_data="amount_320"),
                InlineKeyboardButton(text="640₽", callback_data="amount_640")
            ],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    await message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=keyboard
    )


@router.message(Command("cabinet"))
async def lk_command_handler(message: Message):
    """Обработчик команды cabinet (личный кабинет)"""
    from database.database import Database
    from keyboards.inline import get_cabinet_keyboard
    
    user_id = message.from_user.id
    
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "<b>✨ Личный кабинет</b>\n\n"
        "В этом разделе собраны все важные инструменты и информация, связанные с вашим профилем.\n\n"
        "<b>📁 Файлы</b>\n"
        "Все ваши готовые и созданные материалы 🔥\n\n"
        "<b>💰 Баланс</b>\n"
        "Пополнение и управление средствами 💳\n\n"
        "<b>📑 Юридическая информация</b>\n"
        "Политика конфиденциальности\n"
        "Согласие на ОПД\n"
        "Договор оферты 🛡️\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽</blockquote>"
    )
    
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_cabinet_keyboard()
    )


@router.message(Command("help"))
async def help_command_handler(message: Message):
    """Обработчик команды /help (поддержка)"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    await message.answer(
        "<b>💬 Поддержка</b>\n\n"
        "Возникли вопросы? Напишите нам — разберёмся вместе\n"
        "https://t.me/PicsiSupport",
        parse_mode="HTML",
        reply_markup=keyboard
    )

@router.message(Command("stats"))
async def stats_command_handler(message: Message):
    """Обработчик команды /stats - статистика бота (только для админов)"""
    from database.database import Database
    
    # Список ID администраторов (замени на свой)
    ADMIN_IDS = [6397535545]  # Твой user_id
    
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет доступа к статистике")
        return
    
    db = Database()
    
    # Собираем статистику
    total_users = db.get_total_users_count()
    new_users_7d = db.get_new_users_count(days=7)
    active_users_7d = db.get_active_users_count(days=7)
    
    total_generations = db.get_total_generations_count()
    generations_by_type = db.get_generations_by_type()
    
    total_payments = db.get_payments_count()
    total_earnings = db.get_total_payments_sum()
    earnings_7d = db.get_recent_payments_sum(days=7)
    
    referral_stats = db.get_referral_stats_total()
    
    # Генерации по типам
    photo_count = generations_by_type.get('photo_animation', 0)
    video_count = generations_by_type.get('video_generation', 0)
    edit_count = generations_by_type.get('image_editing', 0)
    
    text = (
        "<b>📊 Статистика бота</b>\n\n"
        "<b>👥 Пользователи:</b>\n"
        f"  • Всего: <b>{total_users}</b>\n"
        f"  • Новых за 7 дней: <b>{new_users_7d}</b>\n"
        f"  • Активных за 7 дней: <b>{active_users_7d}</b>\n\n"
        "<b>🎨 Генерации:</b>\n"
        f"  • Всего: <b>{total_generations}</b>\n"
        f"  • Оживление фото: <b>{photo_count}</b>\n"
        f"  • Генерация видео: <b>{video_count}</b>\n"
        f"  • Редактирование: <b>{edit_count}</b>\n\n"
        "<b>💰 Платежи:</b>\n"
        f"  • Всего платежей: <b>{total_payments}</b>\n"
        f"  • Всего заработано: <b>{total_earnings:.2f} ₽</b>\n"
        f"  • За 7 дней: <b>{earnings_7d:.2f} ₽</b>\n\n"
        "<b>🔗 Рефералы:</b>\n"
        f"  • Всего приглашено: <b>{referral_stats['total_referrals']}</b>\n"
        f"  • Выплачено рефералам: <b>{referral_stats['total_earnings']:.2f} ₽</b>"
    )
    
    await message.answer(text, parse_mode="HTML")