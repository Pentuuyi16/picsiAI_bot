from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

PHOTO_FILE_ID = "AgACAgIAAxkBAAIDJ2luU6s7Rcom5I8T3jK7rp4jQ56YAAISFWsbJvFwS7Mp8xi2styXAQADAgADeQADOAQ"

BOUQUET_PROMPT_TEMPLATE = (
    "A girl sits in an apartment at night, surrounded by large, expensive bouquets of white and red roses. "
    "Each bouquet clearly displays a perfectly formed letter: {name_letters}... "
    "View from above She sits among them. She looks into the camera. "
    "She is wearing a stylish, form-fitting black dress. "
    "Photo taken with a flash on a film camera. Her hair is shiny."
)


class BouquetStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_name = State()
    waiting_for_aspect = State()  # ← НОВОЕ СОСТОЯНИЕ


@router.callback_query(F.data == "trend_bouquet")
async def trend_bouquet_handler(callback: CallbackQuery, state: FSMContext):
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
    
    await state.set_state(BouquetStates.waiting_for_photo)
    await callback.answer()


@router.message(BouquetStates.waiting_for_photo, F.photo)
async def process_bouquet_photo(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    print(f"🎨 User {user_id} - Bouquet trend photo: {photo_url}")
    
    await state.update_data(photo_url=photo_url)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="trends")]
        ]
    )
    
    await message.answer(
        "💐 Отлично! Теперь <b><i>напишите имя</i></b>, которое хотите видеть на букетах\n\n"
        "Имя должно быть обязательно написано на английском языке",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await state.set_state(BouquetStates.waiting_for_name)


@router.message(BouquetStates.waiting_for_name, F.text)
async def process_bouquet_name(message: Message, state: FSMContext):
    """Обработчик имени - сохраняет и просит выбрать соотношение"""
    user_name = message.text.strip()
    
    print(f"🎨 User {message.from_user.id} - Name: {user_name}")
    
    # Сохраняем имя
    await state.update_data(user_name=user_name)
    
    # Просим выбрать соотношение сторон
    from keyboards.inline import get_trend_aspect_ratio_keyboard
    
    await message.answer(
        "📐 Выберите <b>соотношение сторон</b> для вашего фото:",
        parse_mode="HTML",
        reply_markup=get_trend_aspect_ratio_keyboard()
    )
    
    await state.set_state(BouquetStates.waiting_for_aspect)


@router.callback_query(BouquetStates.waiting_for_aspect, F.data.in_(["trend_aspect_16_9", "trend_aspect_9_16", "trend_aspect_1_1"]))
async def process_bouquet_aspect(callback: CallbackQuery, state: FSMContext, bot):
    """Обработчик выбора соотношения сторон"""
    from utils.nano_banana_edit_client import NanoBananaEditClient
    from aiogram.types import URLInputFile
    
    aspect_map = {
        "trend_aspect_16_9": "16:9",
        "trend_aspect_9_16": "9:16",
        "trend_aspect_1_1": "1:1"
    }
    
    aspect_ratio = aspect_map[callback.data]
    
    # Получаем сохраненные данные
    data = await state.get_data()
    photo_url = data.get("photo_url")
    user_name = data.get("user_name")
    
    if not photo_url or not user_name:
        await callback.message.answer("❌ Ошибка: данные не найдены. Попробуйте заново.")
        await state.clear()
        return
    
    user_id = callback.from_user.id
    print(f"🎨 User {user_id} - Selected aspect ratio: {aspect_ratio}")
    
    # Формируем промпт
    name_upper = user_name.upper()
    name_letters = ", ".join([f'"{letter}"' for letter in name_upper])
    final_prompt = BOUQUET_PROMPT_TEMPLATE.format(name_letters=name_letters)
    
    print(f"📝 Final prompt: {final_prompt}")
    
    processing_msg = await callback.message.answer(
        "⭐ Начинается редактирование, пожалуйста подождите..."
    )
    
    try:
        edit_client = NanoBananaEditClient()
        
        task_id = await edit_client.create_edit_task(
            prompt=final_prompt,
            image_urls=[photo_url],
            image_size=aspect_ratio,  # ← ИСПОЛЬЗУЕМ ВЫБРАННОЕ СООТНОШЕНИЕ
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