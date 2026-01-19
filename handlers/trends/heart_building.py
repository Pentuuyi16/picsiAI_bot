from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

PHOTO_FILE_ID = "AgACAgIAAxkBAAIDJWluU6dyuIDP1o-S_9p31nOoyS3cAAIvEmsbdZlwS4NpeTTah_7PAQADAgADeQADOAQ"

HEART_BUILDING_PROMPT = (
    "Create a realistic photo without changing your face. "
    "The photo is taken against the backdrop of a building. "
    "The image is done in an urban aesthetic style. "
    "The model, a girl in dark, loose clothing, stands in a snowy wasteland. "
    "A modern multi-story building towers in the background. "
    "The main detail is the building's windows, illuminated with a bright pink light "
    "so that they form the outline of a huge heart. "
    "The photo conveys a melancholic, romantic urban mood"
)


class HeartBuildingStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_aspect = State()


@router.callback_query(F.data == "trend_heart_building")
async def trend_heart_building_handler(callback: CallbackQuery, state: FSMContext):
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
    
    await state.set_state(HeartBuildingStates.waiting_for_photo)
    await callback.answer()


@router.message(HeartBuildingStates.waiting_for_photo, F.photo)
async def process_heart_building_photo(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    print(f"🎨 User {user_id} - Heart Building trend photo: {photo_url}")
    
    await state.update_data(photo_url=photo_url)
    
    from keyboards.inline import get_trend_aspect_ratio_keyboard
    
    await message.answer(
        "📐 Выберите <b>соотношение сторон</b> для вашего фото:",
        parse_mode="HTML",
        reply_markup=get_trend_aspect_ratio_keyboard()
    )
    
    await state.set_state(HeartBuildingStates.waiting_for_aspect)


@router.callback_query(HeartBuildingStates.waiting_for_aspect, F.data.in_(["trend_aspect_16_9", "trend_aspect_9_16", "trend_aspect_1_1"]))
async def process_heart_building_aspect(callback: CallbackQuery, state: FSMContext, bot):
    from utils.nano_banana_edit_client import NanoBananaEditClient
    from aiogram.types import URLInputFile
    
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
    print(f"🎨 User {user_id} - Selected aspect ratio: {aspect_ratio}")
    
    processing_msg = await callback.message.answer(
        "⭐ Начинается редактирование, пожалуйста подождите..."
    )
    
    try:
        edit_client = NanoBananaEditClient()
        
        task_id = await edit_client.create_edit_task(
            prompt=HEART_BUILDING_PROMPT,
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
                    "💡 Совет: используйте обычные фотографии"
                )
            else:
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
                    
                    from keyboards.inline import get_trends_keyboard
                    await callback.message.answer(
                        "Выберите тренд, который лучше всего вам подходит 💫",
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
                "💡 Попробуйте ещё раз через пару минут"
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