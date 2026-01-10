from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

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