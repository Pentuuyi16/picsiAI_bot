from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from utils.yookassa_client import YooKassaClient
import logging

router = Router()
logger = logging.getLogger(__name__)

GENERATION_PACKAGES = {
    "gen_10": {"count": 10, "price": 100.0},
    "gen_25": {"count": 25, "price": 199.0},
    "gen_50": {"count": 50, "price": 399.0},
    "gen_100": {"count": 100, "price": 799.0}
}


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Купить генерации'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="10 генераций - 100₽", callback_data="select_gen_10")],
            [InlineKeyboardButton(text="25 генераций - 199₽", callback_data="select_gen_25")],
            [InlineKeyboardButton(text="50 генераций - 399₽", callback_data="select_gen_50")],
            [InlineKeyboardButton(text="100 генераций - 799₽", callback_data="select_gen_100")],
            [InlineKeyboardButton(text="Назад", callback_data="back_from_gen_purchase")]
        ]
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        "Выберите пакет генераций и начните создавать прямо сейчас ✨",
        reply_markup=keyboard
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


@router.callback_query(F.data == "back_from_gen_purchase")
async def back_from_gen_purchase_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' из покупки генераций"""
    from utils.texts import TEXTS
    from keyboards.inline import get_main_menu_keyboard
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        TEXTS['welcome_message'],
        parse_mode="HTML",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()