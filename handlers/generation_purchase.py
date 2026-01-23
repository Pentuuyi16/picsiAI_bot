from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from utils.yookassa_client import YooKassaClient
import logging

router = Router()
logger = logging.getLogger(__name__)

GENERATION_PACKAGES = {
    "gen_10": {"count": 10, "price": 99.0},
    "gen_25": {"count": 25, "price": 199.0},
    "gen_50": {"count": 50, "price": 399.0},
    "gen_100": {"count": 100, "price": 799.0}
}

# Словарь для хранения контекста откуда пришел пользователь
user_gen_context = {}


def show_generation_packages(back_to: str = "images_menu"):
    """Создает клавиатуру с пакетами генераций"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="10 генераций - 99₽", callback_data="select_gen_10")],
            [InlineKeyboardButton(text="🔥 25 генераций - 199₽", callback_data="select_gen_25")],
            [InlineKeyboardButton(text="50 генераций - 399₽", callback_data="select_gen_50")],
            [InlineKeyboardButton(text="🔥 100 генераций - 799₽", callback_data="select_gen_100")],
            [InlineKeyboardButton(text="Назад", callback_data=f"back_gen_{back_to}")]
        ]
    )


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Купить генерации' из меню изображений"""
    user_id = callback.from_user.id
    user_gen_context[user_id] = "images_menu"

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "Выберите пакет генераций и начните создавать прямо сейчас ✨",
        reply_markup=show_generation_packages("images_menu")
    )
    await callback.answer()


@router.callback_query(F.data == "buy_generations_from_editing")
async def buy_generations_from_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Купить генерации' из редактирования"""
    user_id = callback.from_user.id
    user_gen_context[user_id] = "image_editing"

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "Выберите пакет генераций и начните создавать прямо сейчас ✨",
        reply_markup=show_generation_packages("image_editing")
    )
    await callback.answer()


@router.callback_query(F.data == "buy_generations_from_trends")
async def buy_generations_from_trends_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Купить генерации' из трендов"""
    user_id = callback.from_user.id
    user_gen_context[user_id] = "trends"

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "Выберите пакет генераций и начните создавать прямо сейчас ✨",
        reply_markup=show_generation_packages("trends")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("select_gen_"))
async def select_generation_package_handler(callback: CallbackQuery):
    """Обработчик выбора пакета генераций - сразу создает платеж"""
    package_key = callback.data.replace("select_", "")
    package = GENERATION_PACKAGES.get(package_key)
    
    if not package:
        await callback.answer("❌ Ошибка выбора пакета", show_alert=True)
        return
    
    user_id = callback.from_user.id
    amount = package['price']
    generations_count = package['count']
    
    logger.info(f"💳 User {user_id} покупает пакет {package_key}: {generations_count} генераций за {amount}₽")
    
    yookassa_client = YooKassaClient()
    payment_data = await yookassa_client.create_payment(
        amount=amount,
        description=f"Покупка {generations_count} генераций",
        user_id=user_id
    )
    
    if not payment_data:
        await callback.answer("❌ Ошибка создания платежа. Попробуйте позже.", show_alert=True)
        return
    
    payment_id = payment_data['payment_id']
    confirmation_url = payment_data['confirmation_url']
    
    db = Database()
    db.save_generation_purchase(
        payment_id=payment_id,
        user_id=user_id,
        package_size=generations_count,
        amount=amount
    )
    
    logger.info(f"✅ Платёж создан: payment_id={payment_id}, user={user_id}, package={generations_count} gens")
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=confirmation_url)],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        f"<b>Сумма к оплате: {amount:.0f}₽</b>\n\n"
        f"<blockquote>⚡ {generations_count} генераций</blockquote>\n\n"
        f"✨ Подтверждение об успешной оплате приходит в течение нескольких минут\n",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data == "back_gen_images_menu")
async def back_gen_images_menu_handler(callback: CallbackQuery):
    """Назад в меню изображений"""
    from keyboards.inline import get_images_menu_keyboard
    from database.database import Database

    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)

    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
    if generations == 1 and not db.has_purchased_generations(user_id):
        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
    generation_text += "</blockquote>"

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        "<b>🖼️ Работа с изображениями</b>\n\n"
        "✨ <b>Создать фото</b> — генерация изображений с нуля\n"
        "🎨 <b>Отредактировать фото</b> — изменить изображение по описанию\n\n"
        f"{generation_text}",
        parse_mode="HTML",
        reply_markup=get_images_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_gen_image_editing")
async def back_gen_image_editing_handler(callback: CallbackQuery):
    """Назад в редактирование"""
    from handlers.image_editing import image_editing_handler
    await image_editing_handler(callback)


@router.callback_query(F.data == "back_gen_trends")
async def back_gen_trends_handler(callback: CallbackQuery):
    """Назад в тренды"""
    from handlers.trends import trends_handler
    await trends_handler(callback)