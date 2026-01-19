from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# File ID фотографии примера
PHOTO_FILE_ID = "AgACAgIAAxkBAAIDM2luU8n2zp8HyJmtkAeEHzDEGhyEAAIfEmsbsx1wS9HhlI4_YB_JAQADAgADeQADOAQ"

# Базовый промпт (будет заменено на нужный сериал/актера)
CELEBRITY_SELFIE_PROMPT_TEMPLATE = (
    "Ultra realistic smartphone selfie photo. "
    "The uploaded person taking a selfie together with a group of teenage characters "
    "inspired by the {series_name}. "
    "1980s small town vibe, retro clothes style, bicycles nearby, Hawkins-like atmosphere. "
    "Front-facing camera perspective, close-up framing. "
    "Everyone standing close together, friendly casual poses, natural smiles. "
    "Arm visible holding the phone. Slight wide-angle selfie lens distortion. "
    "Realistic skin texture, natural cinematic lighting, soft shadows. "
    "Warm natural tones. Looks like a real candid social media selfie photo. "
    "Photorealistic, RAW camera look, high detail."
)


class CelebritySelfieStates(StatesGroup):
    """Состояния для тренда Селфи с актерами"""
    waiting_for_photo = State()
    waiting_for_series = State()


@router.callback_query(F.data == "trend_celebrity_selfie")
async def trend_celebrity_selfie_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик тренда 'Селфи с актерами'"""
    
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
    
    await state.set_state(CelebritySelfieStates.waiting_for_photo)
    await callback.answer()


@router.message(CelebritySelfieStates.waiting_for_photo, F.photo)
async def process_celebrity_selfie_photo(message: Message, state: FSMContext, bot):
    """Обработчик фото для тренда Селфи с актерами"""
    
    user_id = message.from_user.id
    
    # Получаем URL фото
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    print(f"🎨 User {user_id} - Celebrity Selfie trend photo: {photo_url}")
    
    # Сохраняем URL фото в FSM
    await state.update_data(photo_url=photo_url)
    
    # Просим написать название сериала/актера
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="trends")]
        ]
    )
    
    await message.answer(
        "🎬 Отлично! Теперь <b><i>напишите название сериала или актера НА АНГЛИЙСКОМ</i></b>, "
        "с которым хотите сделать селфи\n\n"
        "Например:\n"
        "• <code>Stranger Things TV series</code>\n"
        "• <code>Wednesday TV series</code>\n"
        "• <code>Harry Potter cast</code>\n"
        "• <code>Marvel Avengers cast</code>\n\n"
        "⚠️ Важно: используйте только английский язык!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    # Переводим в состояние ожидания названия
    await state.set_state(CelebritySelfieStates.waiting_for_series)


@router.message(CelebritySelfieStates.waiting_for_series, F.text)
async def process_celebrity_selfie_series(message: Message, state: FSMContext, bot):
    """Обработчик названия сериала/актера для тренда Селфи с актерами"""
    from utils.nano_banana_edit_client import NanoBananaEditClient
    from aiogram.types import URLInputFile
    
    user_id = message.from_user.id
    series_name = message.text.strip()
    
    # Получаем сохраненный URL фото
    data = await state.get_data()
    photo_url = data.get("photo_url")
    
    if not photo_url:
        await message.answer("❌ Ошибка: фото не найдено. Попробуйте заново.")
        await state.clear()
        return
    
    print(f"🎨 User {user_id} - Series/Actor: {series_name}")
    
    # Формируем финальный промпт
    final_prompt = CELEBRITY_SELFIE_PROMPT_TEMPLATE.format(series_name=series_name)
    
    print(f"📝 Final prompt: {final_prompt}")
    
    processing_msg = await message.answer(
        "⭐ Начинается редактирование, пожалуйста подождите..."
    )
    
    try:
        edit_client = NanoBananaEditClient()
        
        task_id = await edit_client.create_edit_task(
            prompt=final_prompt,
            image_urls=[photo_url],
            image_size="9:16",
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
                        chat_id=message.chat.id,
                        photo=photo_file,
                        caption="✨ Ваше фото готово!",
                        request_timeout=180
                    )
                    await processing_msg.delete()
                    
                    print(f"✅ Photo sent successfully!")
                    
                    # Возвращаем в меню трендов
                    from keyboards.inline import get_trends_keyboard
                    await message.answer(
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