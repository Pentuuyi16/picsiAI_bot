from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.database import Database
from keyboards.inline import get_trends_keyboard

router = Router()


@router.callback_query(F.data == "trends")
async def trends_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Тренды'"""
    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций</blockquote>"
    
    await callback.message.answer(
        f"Выберите тренд, который лучше всего вам подходит 💫\n\n"
        f"{generation_text}",
        parse_mode="HTML",
        reply_markup=get_trends_keyboard(page=1)
    )
    await callback.answer()