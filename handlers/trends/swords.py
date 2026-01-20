from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

PHOTO_FILE_ID = "AgACAgIAAxkBAAIOGmluokFN3Ojk5DfeepD-ZVVYb7HhAAItFWsbSD9wS6-RY6BVyNO0AQADAgADeQADOAQ"

SWORDS_PROMPT = (
    "Grassy hill covered with short wild grass, flat gray overcast sky, soft dramatic clouds, "
    "heavy cinematic atmosphere. Three-quarter side low-angle shot, slightly rotated perspective "
    "for dynamic composition. Dozens of giant matte metal swords planted vertically across the hill, "
    "creating an epic battlefield memorial scene, some close, some fading into the foggy distance. "
    "One massive sword directly behind the woman, towering above her. "
    "Woman sitting on the slope with her back resting against the giant sword, knees slightly bent, "
    "legs angled downhill. One arm resting on her knee, the other touching the grass for balance. "
    "Head slightly tilted and turned sideways, calm but powerful expression. "
    "Long dark hair blown backward by wind, strong motion flow. "
    "Light translucent veil trailing behind, flowing in the wind. "
    "Warm ivory structured dress, matte fabric, elegant heroic silhouette. "
    "Cinematic lighting, soft contrast, subtle rim light outlining the figure. "
    "Depth of field with foreground focus, background softly blurred. "
    "Ultra realistic film still look, near-RAW photo style, slightly warm cinematic color grading, "
    "high dynamic range."
)


class SwordsStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_aspect = State()


@router.callback_query(F.data == "trend_swords")
async def trend_swords_handler(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="trends")]
        ]
    )
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer_photo(
        photo=PHOTO_FILE_ID,
        caption=(
            "<b>Пример того, что у вас получится ⤴️</b>\n\n"
            "Если вы готовы — <b><i>присылайте свою фотографию</i></b>, и мы с радостью её отредактируем 💫"
        ),
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(SwordsStates.waiting_for_photo)
    await callback.answer()


@router.message(SwordsStates.waiting_for_photo, F.photo)
async def process_swords_photo(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    print(f"🎨 User {user_id} - Swords trend photo: {photo_url}")
    
    await state.update_data(photo_url=photo_url)
    
    from keyboards.inline import get_trend_aspect_ratio_keyboard
    
    await message.answer(
        "📐 Выберите <b>соотношение сторон</b> для вашего фото:",
        parse_mode="HTML",
        reply_markup=get_trend_aspect_ratio_keyboard()
    )
    
    await state.set_state(SwordsStates.waiting_for_aspect)


@router.callback_query(SwordsStates.waiting_for_aspect, F.data.in_(["trend_aspect_16_9", "trend_aspect_9_16", "trend_aspect_1_1"]))
async def process_swords_aspect(callback: CallbackQuery, state: FSMContext, bot):
    from utils.nano_banana_edit_client import NanoBananaEditClient
    from aiogram.types import URLInputFile
    from database.database import Database
    
    aspect_map = {
        "trend_aspect_16_9": "16:9",
        "trend_aspect_9_16": "9:16",
        "trend_aspect_1_1": "1:1"
    }
    
    aspect_ratio = aspect_map[callback.data]
    
    data = await state.get_data()
    photo_url = data.get("photo_url")
    
    if not photo_url:
        await callback.message.answer("❌ Ошибка: фото не найдено. Попробуйте заново.")
        await state.clear()
        return
    
    user_id = callback.from_user.id
    
    # ========== ПРОВЕРКА ГЕНЕРАЦИЙ ==========
    db = Database()
    generations = db.get_user_generations(user_id)
    
    if generations < 1:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations")],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            "У вас закончились генерации 😔\n\n"
            f"<blockquote>⚡ Доступно: {generations} генераций\n"
            f"🎨 Один тренд = 1 генерация</blockquote>\n\n"
            "Купите пакет генераций, чтобы продолжить!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await state.clear()
        await callback.answer()
        return
    # ========================================
    
    print(f"🎨 User {user_id} - Selected aspect ratio: {aspect_ratio}")
    
    processing_msg = await callback.message.answer(
        "⭐ Начинается редактирование, пожалуйста подождите..."
    )
    
    try:
        edit_client = NanoBananaEditClient()
        
        task_id = await edit_client.create_edit_task(
            prompt=SWORDS_PROMPT,
            image_urls=[photo_url],
            image_size=aspect_ratio,
            output_format="png"
        )
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        print(f"✅ Task created: {task_id}")
        
        result_url = await edit_client.wait_for_result(task_id, max_attempts=120, delay=5)
        
        if result_url:
            if result_url == "MODERATION_ERROR":
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось отредактировать фото\n\n"
                    "Система безопасности заблокировала запрос.\n\n"
                    "Частые причины:\n"
                    "• На фото известная личность\n"
                    "• Неподходящий контент\n\n"
                    "💡 Совет: используйте обычные фотографии\n\n"
                    "💛 Не переживайте, генерация не списана"
                )
            else:
                # ========== СПИСАНИЕ ГЕНЕРАЦИИ ==========
                db.subtract_generations(user_id, 1)
                # ========================================
                
                print(f"✅ Generation successful! Result URL: {result_url}")
                
                try:
                    photo_file = URLInputFile(result_url)
                    await bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=photo_file,
                        caption="✨ Ваше фото готово!",
                        request_timeout=180
                    )
                    await processing_msg.delete()
                    
                    print(f"✅ Photo sent successfully!")
                    
                    db.save_generation(user_id, "trend_swords", result_url, SWORDS_PROMPT)
                    
                    from keyboards.inline import get_trends_keyboard
                    generations = db.get_user_generations(user_id)
                    
                    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
                    if generations == 1:
                        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
                    generation_text += "</blockquote>"
                    
                    await bot.send_message(
                        chat_id=callback.message.chat.id,
                        text=f"Выберите тренд, который лучше всего вам подходит 💫\n\n{generation_text}",
                        parse_mode="HTML",
                        reply_markup=get_trends_keyboard(page=1)
                    )
                    
                except Exception as e:
                    print(f"❌ Error sending photo: {e}")
                    await processing_msg.edit_text(
                        "❌ Не удалось отправить фото. Попробуйте позже."
                    )
        else:
            await processing_msg.edit_text(
                "😔 Что-то пошло не так\n\n"
                "Не удалось отредактировать фото. Возможные причины:\n"
                "• Превышено время ожидания\n"
                "• Временные проблемы с сервером\n\n"
                "💡 Попробуйте ещё раз через пару минут\n\n"
                "💛 Не переживайте, генерация не списана"
            )
    
    except Exception as e:
        print(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        
        await processing_msg.edit_text(
            "❌ Произошла ошибка при редактировании. Попробуйте позже."
        )
    
    await state.clear()
    await callback.answer()