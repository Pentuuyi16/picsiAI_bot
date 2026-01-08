from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "support")
async def support_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Написать в поддержку'"""
    await callback.message.answer(
        "📧 Для связи с поддержкой напишите нам:\n\n"
        "Описание вашего вопроса или проблемы будет передано нашей команде."
    )
    await callback.answer()