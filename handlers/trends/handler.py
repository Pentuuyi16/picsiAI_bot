from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.database import Database
from keyboards.inline import get_trends_keyboard

router = Router()


@router.callback_query(F.data == "trends")
async def trends_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)
    
    try:
        await callback.message.delete()
    except:
        pass
    
    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
    if generations == 1:
        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
    generation_text += "</blockquote>"
    
    await callback.message.answer(
        f"Выберите тренд, который лучше всего вам подходит 💫\n\n"
        f"{generation_text}",
        parse_mode="HTML",
        reply_markup=get_trends_keyboard(page=1)
    )
    await callback.answer()


# Если есть пагинация трендов, добавьте обработчик для второй страницы
@router.callback_query(F.data == "trends_page_2")
async def trends_page_2_handler(callback: CallbackQuery):
    """Обработчик второй страницы трендов"""
    user_id = callback.from_user.id
    
    # Получаем количество генераций
    db = Database()
    generations = db.get_user_generations(user_id)
    
    # Здесь добавьте клавиатуру для второй страницы трендов (если есть)
    # Пока возвращаем на первую страницу
    await callback.message.edit_text(
        f"Выберите тренд, который лучше всего вам подходит 💫\n\n"
        f"<blockquote>⚡ У вас осталось: {generations} генераций</blockquote>",
        parse_mode="HTML",
        reply_markup=get_trends_keyboard(page=1)
    )
    await callback.answer()