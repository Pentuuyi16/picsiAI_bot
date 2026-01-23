from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import Database
from keyboards.inline import get_trends_keyboard
from .handler import router as handler_router
from .macbook import router as macbook_router
from .bouquet import router as bouquet_router
from .snow_angel import router as snow_angel_router
from .snowboard import router as snowboard_router
from .wall_portrait import router as wall_portrait_router
from .loving_gaze import router as loving_gaze_router
from .swords import router as swords_router
from .heart_building import router as heart_building_router
from .car import router as car_router
from .scream import router as scream_router
from .avatar import router as avatar_router

# Главный роутер для трендов
router = Router()

# Подключаем все роутеры
router.include_router(handler_router)
router.include_router(macbook_router)
router.include_router(bouquet_router)
router.include_router(snow_angel_router)
router.include_router(snowboard_router)
router.include_router(wall_portrait_router)
router.include_router(loving_gaze_router)
router.include_router(swords_router)
router.include_router(heart_building_router)
router.include_router(car_router)
router.include_router(scream_router)
router.include_router(avatar_router)


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
    
    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
    if generations == 1 and not db.has_purchased_generations(user_id):
        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
    generation_text += "</blockquote>"
    
    await callback.message.answer(
        f"Выберите тренд, который лучше всего вам подходит 💫\n\n"
        f"{generation_text}",
        parse_mode="HTML",
        reply_markup=get_trends_keyboard(page=1)
    )
    await callback.answer()

@router.callback_query(F.data == "trends_page_2")
async def trends_page_2_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Следующая страница' в трендах"""
    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)

    try:
        await callback.message.delete()
    except:
        pass

    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
    if generations == 1 and not db.has_purchased_generations(user_id):
        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
    generation_text += "</blockquote>"

    await callback.message.answer(
        f"Выберите тренд, который лучше всего вам подходит 💫\n\n"
        f"{generation_text}",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Я аватар", callback_data="trend_avatar")],
                [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations")],
                [InlineKeyboardButton(text="← Предыдущая страница", callback_data="trends")],
                [InlineKeyboardButton(text="← Назад", callback_data="images_menu")]
            ]
        )
    )
    await callback.answer()