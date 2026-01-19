from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(F.data == "trends")
async def trends_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Тренды'"""
    from keyboards.inline import get_trends_keyboard
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое
    await callback.message.answer(
        "Выберите тренд, который лучше всего вам подходит 💫",
        reply_markup=get_trends_keyboard(page=1)
    )
    await callback.answer()