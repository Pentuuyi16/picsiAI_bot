from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

PHOTO_FILE_ID = "AgACAgIAAxkBAAIOI2luol9rNO9bvPBp1SGe5j5NgEpQAAIwFWsbSD9wS3qnSJ7HUI4-AQADAgADeQADOAQ"

SNOW_ANGEL_PROMPT = (
    "A young angelic woman kneeling in fresh snow in a dark winter forest at night. "
    "She has long blonde hair, slightly wavy, softly framing her face. "
    "She wears a white satin corset dress with lace sleeves, elegant and delicate. "
    "She has large white feathered wings attached to her back. "
    "Knees are on the snow, arms relaxed, one hand lightly touching her hair. "
    "Soft, serene, slightly melancholic expression, eyes gently closed or looking down. "
    "Snow gently falling around, soft light illuminating her from the front and back, "
    "creating a subtle glow on the wings and hair. "
    "High-detail, realistic skin and fabric textures, cinematic lighting, "
    "slightly cool blue tones with high contrast. "
    "Soft shadows, depth of field to emphasize subject, ultra-realistic, photo-realistic style."
)


class SnowAngelStates(StatesGroup):
    waiting_for_photo = State()
    waiting_for_aspect = State()
    waiting_for_model = State()


@router.callback_query(F.data == "trend_snow_angel")
async def trend_snow_angel_handler(callback: CallbackQuery, state: FSMContext):
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
    
    await state.set_state(SnowAngelStates.waiting_for_photo)
    await callback.answer()


@router.message(SnowAngelStates.waiting_for_photo, F.photo)
async def process_snow_angel_photo(message: Message, state: FSMContext, bot):
    user_id = message.from_user.id
    
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    print(f"🎨 User {user_id} - Snow Angel trend photo: {photo_url}")
    
    await state.update_data(photo_url=photo_url)
    
    from keyboards.inline import get_trend_aspect_ratio_keyboard
    
    await message.answer(
        "📐 Выберите <b>соотношение сторон</b> для вашего фото:",
        parse_mode="HTML",
        reply_markup=get_trend_aspect_ratio_keyboard()
    )
    
    await state.set_state(SnowAngelStates.waiting_for_aspect)


@router.callback_query(SnowAngelStates.waiting_for_aspect, F.data.in_(["trend_aspect_16_9", "trend_aspect_9_16", "trend_aspect_1_1"]))
async def process_snow_angel_aspect(callback: CallbackQuery, state: FSMContext):
    from database.database import Database
    
    aspect_map = {
        "trend_aspect_16_9": "16:9",
        "trend_aspect_9_16": "9:16",
        "trend_aspect_1_1": "1:1"
    }
    
    aspect_ratio = aspect_map[callback.data]
    await state.update_data(aspect_ratio=aspect_ratio)
    
    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)
    
    from keyboards.inline import get_trend_model_selection_keyboard
    
    await callback.message.answer(
        "<b>🤖 Выбор модели генерации</b>\n\n"
        "<b>Активная модель: Стандартная</b>\n\n"
        "<b>🌟 Стандартная (Nano Banana)</b>\n"
        "• Цена: <b><i>1 генерация</i></b>\n"
        "• Качество: <b><i>стабильно хорошее</i></b>\n"
        "• Скорость: <b><i>молниеносная ⚡</i></b>\n\n"
        "<b>🚀 Профессиональная (Nano Banana Pro)</b>\n"
        "• Цена: <b><i>4 генерации</i></b>\n"
        "• Разрешение: <b><i>ультра-чёткое 4K</i></b>\n"
        "• Качество: <b><i>максимальный уровень детализации</i></b>\n"
        "• Промты до <b><i>5000 символов</i></b>\n"
        "• <b><i>Продвинутое понимание текста</i></b> для точных результатов\n\n"
        f"<blockquote>⚡ У вас осталось: {generations} генераций</blockquote>",
        parse_mode="HTML",
        reply_markup=get_trend_model_selection_keyboard(generations)
    )
    
    await state.set_state(SnowAngelStates.waiting_for_model)
    await callback.answer()


@router.callback_query(SnowAngelStates.waiting_for_model, F.data.in_(["trend_model_standard", "trend_model_pro"]))
async def process_snow_angel_model(callback: CallbackQuery, state: FSMContext, bot):
    from database.database import Database
    import aiohttp
    from PIL import Image
    from io import BytesIO
    from aiogram.types import URLInputFile, BufferedInputFile
    
    await callback.answer()
    
    try:
        await callback.message.delete()
    except:
        pass
    
    model_type = "standard" if callback.data == "trend_model_standard" else "pro"
    generations_cost = 1 if model_type == "standard" else 4
    
    data = await state.get_data()
    photo_url = data.get("photo_url")
    aspect_ratio = data.get("aspect_ratio")
    
    if not photo_url or not aspect_ratio:
        await callback.message.answer("❌ Ошибка: фото не найдено. Попробуйте заново.")
        await state.clear()
        return
    
    user_id = callback.from_user.id
    
    db = Database()
    generations = db.get_user_generations(user_id)
    
    if generations < generations_cost:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations")],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            "У вас закончились генерации 😔\n\n"
            f"<blockquote>⚡ Доступно: {generations} генераций\n"
            f"🎨 Выбранная модель требует: {generations_cost} генерации</blockquote>\n\n"
            "Купите пакет генераций, чтобы продолжить!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await state.clear()
        return
    
    print(f"🎨 User {user_id} - Selected model: {model_type}, aspect ratio: {aspect_ratio}")
    
    processing_msg = await callback.message.answer(
        "⭐ Начинается редактирование, пожалуйста подождите..."
    )
    
    try:
        if model_type == "standard":
            from utils.nano_banana_edit_client import NanoBananaEditClient
            edit_client = NanoBananaEditClient()
            
            task_id = await edit_client.create_edit_task(
                prompt=SNOW_ANGEL_PROMPT,
                image_urls=[photo_url],
                image_size=aspect_ratio,
                output_format="png"
            )
        else:
            from utils.image_edit_client import ImageEditClient
            edit_client = ImageEditClient()
            
            task_id = await edit_client.create_edit_task(
                prompt=SNOW_ANGEL_PROMPT,
                image_urls=[photo_url],
                aspect_ratio=aspect_ratio,
                resolution="4K",
                output_format="png"
            )
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        print(f"✅ Task created: {task_id}")
        
        if model_type == "pro":
            # Для Pro модели: увеличенный таймаут и показ прогресса
            async def update_progress(elapsed_min, remaining_min):
                """Обновляет сообщение с прогрессом для пользователя"""
                try:
                    await processing_msg.edit_text(
                        f"⭐ Идет генерация в высоком качестве...\n\n"
                        f"⏱️ Прошло: {elapsed_min} мин\n"
                        f"⏳ Осталось примерно: {remaining_min} мин\n\n"
                        f"💡 Профессиональная модель создает изображения в 4K, "
                        f"это требует больше времени, но результат того стоит!"
                    )
                except:
                    pass
            
            result_url = await edit_client.wait_for_result(
                task_id, 
                max_attempts=240,  # 20 минут для Pro
                delay=5,
                progress_callback=update_progress
            )
        else:
            # Для Standard модели: обычный таймаут без прогресса
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
                db.subtract_generations(user_id, generations_cost)
                
                print(f"✅ Generation successful! Result URL: {result_url}")
                
                try:
                    print(f"📤 Отправка изображения: {result_url}")
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(result_url) as response:
                            image_data = await response.read()
                            original_size_mb = len(image_data) / (1024 * 1024)
                            print(f"   Размер: {original_size_mb:.2f} MB")
                    
                    if original_size_mb > 9.0:
                        print(f"   🔧 Сжимаем изображение...")
                        img = Image.open(BytesIO(image_data))
                        
                        if img.mode in ('RGBA', 'P', 'LA'):
                            background = Image.new('RGB', img.size, (255, 255, 255))
                            if img.mode == 'P':
                                img = img.convert('RGBA')
                            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                            img = background
                        
                        output = BytesIO()
                        quality = 85
                        while quality > 20:
                            output.seek(0)
                            output.truncate()
                            img.save(output, format='JPEG', quality=quality, optimize=True)
                            size_mb = output.tell() / (1024 * 1024)
                            if size_mb <= 9.0:
                                break
                            quality -= 5
                        
                        output.seek(0)
                        photo_file = BufferedInputFile(output.read(), filename="image.jpg")
                        print(f"   ✅ Сжато до {size_mb:.2f} MB")
                    else:
                        photo_file = URLInputFile(result_url)
                    
                    await bot.send_photo(
                        chat_id=callback.message.chat.id,
                        photo=photo_file,
                        caption="✨ Ваше фото готово!",
                        request_timeout=180
                    )
                    await processing_msg.delete()
                    
                    print(f"✅ Photo sent successfully!")
                    
                    db.save_generation(user_id, "trend_snow_angel", result_url, SNOW_ANGEL_PROMPT)
                    
                    from keyboards.inline import get_trends_keyboard
                    generations = db.get_user_generations(user_id)
                    
                    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
                    if generations == 1 and not db.has_purchased_generations(user_id):
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