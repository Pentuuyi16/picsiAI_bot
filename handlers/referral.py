from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from config import BOT_USERNAME

router = Router()


@router.callback_query(F.data == "referral_system")
async def referral_system_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Реферальная система'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    db = Database()
    
    # Получаем или генерируем реферальный код
    referral_code = db.get_referral_code(user_id)
    if not referral_code:
        referral_code = db.generate_referral_code(user_id)
    
    # Получаем статистику
    stats = db.get_referral_stats(user_id)
    
    # Формируем реферальную ссылку
    referral_link = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}"
    
    text = (
        "<b>🔥 Приглашайте — зарабатывайте — повторяйте!</b>\n\n"
        "<b>Как это работает?</b>\n\n"
        "👥 <b><i>Приглашайте</i></b> друзей по своей уникальной ссылке.\n"
        "💰 <b><i>Каждый раз</i></b>, когда приглашённый друг совершает покупку, вы получаете 15% от суммы на основной баланс.\n"
        "🔁 <b><i>Бонус начисляется</i></b> с каждой покупки, без ограничений.\n\n"
        f"<blockquote>📊 Приглашено друзей: {stats['referrals_count']}\n"
        f"💎 Всего заработано: {stats['total_earned']:.2f} ₽</blockquote>\n\n"
        f"🔗 <b>Ваша реферальная ссылка:</b>\n"
        f"<code>{referral_link}</code>"
    )
    
    # Кнопки
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Поделиться ссылкой", url=f"https://t.me/share/url?url={referral_link}")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await callback.answer()