from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

router = Router()


@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Написать в поддержку'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    await callback.message.edit_text(
        "<b>💬 Поддержка</b>\n\n"
        "Возникли вопросы? Напишите нам — разберёмся вместе\n"
        "https://t.me/PicsiSupport",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()