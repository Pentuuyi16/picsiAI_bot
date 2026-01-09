from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import get_video_generation_keyboard, get_video_format_keyboard, get_aspect_ratio_keyboard, get_main_menu_keyboard
from utils.veo_api_client import VeoApiClient
from utils.texts import TEXTS
import logging

router = Router()
veo_client = VeoApiClient()
logger = logging.getLogger(__name__)

# File ID вашего видео-примера (можете использовать тот же или другой)
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAPxaWGA8YZkOBaGRPMEY8sMl8GnCP0AAiSZAALy1QhLS_xA10bOT5c4BA"

# Временное хранилище для обработанных медиа-групп
processed_media_groups = {}


class VideoGenerationStates(StatesGroup):
    """Состояния для процесса создания видео"""
    waiting_for_photos = State()
    waiting_for_description = State()


@router.callback_query(F.data == "video_generation")
async def video_generation_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Создание видео'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    
    # Получаем баланс из БД
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "<b>✨ Наш Бот превращает ваши идеи и фотографии в яркие видеосюжеты!</b>\n\n"
        "<b>Как создать своё видео?</b>\n\n"
        "1️⃣ <b><i>Отправьте текст</i></b> с идеей или загрузите фотографию\n"
        "2️⃣ <b><i>Опишите</i></b> настроение, сюжет или пару ключевых слов\n"
        "3️⃣ <b><i>Подождите несколько минут</i></b> — бот создаст стильный видеоролик\n\n"
        "<b>🔥 Доступны два способа создания видео:</b>\n\n"
        "• <b><i>По тексту</i></b> — напишите свою задумку, и бот соберёт по ней уникальный видеосюжет.\n"
        "• <b><i>По фото</i></b> — загрузите изображение, и бот создаст видео, вдохновлённое вашим кадром.\n\n"
        "Любую <b><i>мысль</i></b> можно превратить в историю 💫\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
        f"📹 Генерация 1 видео = 65₽\n"
        f"📹 Генерация 1 видео (высокое качество) = 115₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    await callback.message.delete()
    
    # Отправляем новое с видео
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_video_generation_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data == "generate_video")
async def generate_video_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Сгенерировать видео'"""
    await callback.message.answer(
        "🚀 <b><i>Выберите</i></b> удобный формат генерации",
        parse_mode="HTML",
        reply_markup=get_video_format_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "video_fast_photo")
async def video_fast_photo_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора быстрой модели с фото"""
    await state.update_data(
        model_type="fast_photo",
        model_name="быстрая с фото",
        veo_model="veo3_fast",
        photos=[],
        is_prompt_model=False
    )
    
    text = (
        "⚡️ Быстрая модель с <b><i>фото</i></b> выбрана\n\n"
        "📐 Выберите <b><i>соотношение</i></b> сторон видео:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_aspect_ratio_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "video_quality_photo")
async def video_quality_photo_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора модели высокого качества с фото"""
    await state.update_data(
        model_type="quality_photo",
        model_name="высокое качество с фото",
        veo_model="veo3",
        photos=[],
        is_prompt_model=False
    )
    
    text = (
        "⚡️ Модель высокого качества с <b><i>фото</i></b> выбрана\n\n"
        "📐 Выберите <b><i>соотношение</i></b> сторон видео:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_aspect_ratio_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "video_fast_prompt")
async def video_fast_prompt_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора быстрой модели с промтом"""
    await state.update_data(
        model_type="fast_prompt",
        model_name="быстрая с текстовым запросом",
        veo_model="veo3_fast",
        photos=[],
        is_prompt_model=True
    )
    
    text = (
        "⚡️ Быстрая модель с <b><i>текстовым запросом</i></b> выбрана\n\n"
        "📐 Выберите <b><i>соотношение</i></b> сторон видео:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_aspect_ratio_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "video_quality_prompt")
async def video_quality_prompt_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора модели высокого качества с промтом"""
    await state.update_data(
        model_type="quality_prompt",
        model_name="высокое качество с текстовым запросом",
        veo_model="veo3",
        photos=[],
        is_prompt_model=True
    )
    
    text = (
        "⚡️ Модель высокого качества с <b><i>текстовым запросом</i></b> выбрана\n\n"
        "📐 Выберите <b><i>соотношение</i></b> сторон видео:"
    )
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_aspect_ratio_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "aspect_9_16")
async def aspect_9_16_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора вертикального соотношения сторон 9:16"""
    data = await state.get_data()
    model_name = data.get("model_name", "быстрая с фото")
    is_prompt_model = data.get("is_prompt_model", False)
    
    await state.update_data(aspect_ratio="9:16", aspect_name="вертикальное")
    
    logger.info(f"Выбрано соотношение 9:16, is_prompt_model={is_prompt_model}")
    
    if is_prompt_model:
        # Если модель с промтом - сразу просим описание
        text = (
            "<b>✨ Всё настроено!</b>\n\n"
            "📝 Отправьте <b><i>текстовое описание</i></b> видео\n\n"
            f"<blockquote>⚡️ Модель: {model_name}\n\n"
            f"📐 Соотношение сторон: вертикальное</blockquote>"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await state.set_state(VideoGenerationStates.waiting_for_description)
        logger.info("Установлено состояние waiting_for_description")
    else:
        # Если модель с фото - просим фото
        text = (
            "<b>✨ Всё настроено!</b>\n\n"
            "📷 <b><i>Загрузите 1–2 фото</i></b> — именно с них начнётся магия. "
            "Если фото два, первое станет началом, второе — концом ролика\n\n"
            f"<blockquote>⚡️ Модель: {model_name}\n\n"
            f"📐 Соотношение сторон: вертикальное</blockquote>"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await state.set_state(VideoGenerationStates.waiting_for_photos)
        logger.info("Установлено состояние waiting_for_photos")
    
    await callback.answer()


@router.callback_query(F.data == "aspect_16_9")
async def aspect_16_9_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора горизонтального соотношения сторон 16:9"""
    data = await state.get_data()
    model_name = data.get("model_name", "быстрая с фото")
    is_prompt_model = data.get("is_prompt_model", False)
    
    await state.update_data(aspect_ratio="16:9", aspect_name="горизонтальное")
    
    logger.info(f"Выбрано соотношение 16:9, is_prompt_model={is_prompt_model}")
    
    if is_prompt_model:
        # Если модель с промтом - сразу просим описание
        text = (
            "<b>✨ Всё настроено!</b>\n\n"
            "📝 Отправьте <b><i>текстовое описание</i></b> видео\n\n"
            f"<blockquote>⚡️ Модель: {model_name}\n\n"
            f"📐 Соотношение сторон: горизонтальное</blockquote>"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await state.set_state(VideoGenerationStates.waiting_for_description)
        logger.info("Установлено состояние waiting_for_description")
    else:
        # Если модель с фото - просим фото
        text = (
            "<b>✨ Всё настроено!</b>\n\n"
            "📷 <b><i>Загрузите 1–2 фото</i></b> — именно с них начнётся магия. "
            "Если фото два, первое станет началом, второе — концом ролика\n\n"
            f"<blockquote>⚡️ Модель: {model_name}\n\n"
            f"📐 Соотношение сторон: горизонтальное</blockquote>"
        )
        await callback.message.edit_text(
            text,
            parse_mode="HTML"
        )
        await state.set_state(VideoGenerationStates.waiting_for_photos)
        logger.info("Установлено состояние waiting_for_photos")
    
    await callback.answer()


@router.message(VideoGenerationStates.waiting_for_photos, F.photo)
async def process_video_photos(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения фотографий для создания видео"""
    
    user_id = message.from_user.id
    
    # Получаем данные состояния
    data = await state.get_data()
    photos = data.get("photos", [])
    
    # Добавляем текущее фото
    photo = message.photo[-1]
    
    # Получаем URL фото
    file = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    photos.append(file_url)
    
    # Если это медиа-группа
    if message.media_group_id:
        media_group_id = message.media_group_id
        
        # Инициализируем set для пользователя если его нет
        if user_id not in processed_media_groups:
            processed_media_groups[user_id] = set()
        
        # Если эта медиа-группа уже обработана, игнорируем
        if media_group_id in processed_media_groups[user_id]:
            return
        
        # Сохраняем обновлённый список фото
        await state.update_data(photos=photos)
        
        # Помечаем медиа-группу как обработанную
        processed_media_groups[user_id].add(media_group_id)
        
        # Отправляем запрос на описание
        await message.answer(
            "📝 Теперь отправьте текстовое описание видео"
        )
        await state.set_state(VideoGenerationStates.waiting_for_description)
    else:
        # Одиночное фото
        await state.update_data(photos=photos)
        
        await message.answer(
            "📝 Теперь отправьте текстовое описание видео"
        )
        await state.set_state(VideoGenerationStates.waiting_for_description)


@router.message(VideoGenerationStates.waiting_for_description, F.text)
async def process_video_description(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения описания видео"""
    from database.database import Database
    from keyboards.inline import get_payment_methods_keyboard
    import json
    
    db = Database()
    user = db.get_user(message.from_user.id)
    
    # Получаем данные о выбранной модели
    data = await state.get_data()
    veo_model = data.get("veo_model", "veo3_fast")
    
    # Проверяем баланс в зависимости от модели
    balance = user['balance'] if user else 0.00
    required_amount = 65.00 if veo_model == "veo3_fast" else 115.00
    
    if balance < required_amount:
        # Сохраняем текущее состояние для продолжения после оплаты
        prompt = message.text
        action_data = json.dumps({
            "back_to": "video_generation",
            "state_data": data,  # Сохраняем ВСЁ: модель, соотношение, фото
            "prompt": prompt
        })
        db.save_pending_action(message.from_user.id, "video_generation_pending", action_data)
        
        print(f"💾 Сохранено состояние для генерации видео:")
        print(f"   Model: {veo_model}")
        print(f"   Aspect ratio: {data.get('aspect_ratio')}")
        print(f"   Photos: {len(data.get('photos', []))} шт")
        print(f"   Prompt: {prompt}")
        
        await message.answer(
            "Похоже, средств сейчас немного не хватает\n\n"
            f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
            f"📹 Генерация 1 видео = 65₽\n"
            f"📹 Генерация 1 видео (высокое качество) = 115₽</blockquote>\n\n"
            "Выберите способ оплаты ⤵️",
            parse_mode="HTML",
            reply_markup=get_payment_methods_keyboard(back_to="video_generation")
        )
        # НЕ очищаем состояние!
        return
    
    prompt = message.text
    aspect_ratio = data.get("aspect_ratio", "16:9")
    photos = data.get("photos", [])
    
    logger.info(f"Получен промпт: {prompt}")
    logger.info(f"Модель: {veo_model}, Соотношение: {aspect_ratio}, Фото: {len(photos)}")
    
    # Отправляем сообщение о начале генерации
    processing_msg = await message.answer(
        "⭐ Начинается генерация видео, совсем скоро пришлем результат"
    )
    
    try:
        # Создаём задачу на генерацию видео
        if photos:
            # Image-to-video
            logger.info("Создание задачи image-to-video")
            task_id = await veo_client.generate_video(
                prompt=prompt,
                model=veo_model,
                aspect_ratio=aspect_ratio,
                image_urls=photos
            )
        else:
            # Text-to-video
            logger.info("Создание задачи text-to-video")
            task_id = await veo_client.generate_video(
                prompt=prompt,
                model=veo_model,
                aspect_ratio=aspect_ratio
            )
        
        logger.info(f"Task ID: {task_id}")
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        # Ожидаем завершения генерации
        logger.info("Ожидание завершения генерации...")
        video_url = await veo_client.wait_for_video(task_id, max_attempts=180, delay=10)
        
        logger.info(f"Video URL: {video_url}")
        
        if video_url:
            if video_url == "MODERATION_ERROR":
                # Ошибка модерации - баланс НЕ списывается
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось сгенерировать\n\n"
                    "Система безопасности заблокировала запрос. Частые причины:\n"
                    "• На фото известная личность\n"
                    "• В описании есть неподходящий контент\n\n"
                    "💡 Совет: используйте обычные фотографии и нейтральные описания\n\n"
                    "💛 Не переживайте, баланс не пострадал"
                )
            else:
                # Успешная генерация - списываем средства
                new_balance = balance - required_amount
                db.update_user_balance(message.from_user.id, new_balance)
                
                # Отправляем видео пользователю
                try:
                    video_file = URLInputFile(video_url)
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption="✨ Ваше видео готово!",
                        request_timeout=180
                    )
                    logger.info("Видео успешно отправлено")
                    
                    # Удаляем сообщение о генерации ТОЛЬКО после успешной отправки видео
                    await processing_msg.delete()

                    # Сохраняем генерацию в БД
                    db.save_generation(message.from_user.id, "video_generation", video_url, prompt)
                except Exception as e:
                    logger.error(f"Ошибка отправки видео: {e}")
                    await processing_msg.edit_text(
                        "❌ Не удалось отправить видео. Попробуйте позже."
                    )
            
            # Автоматически открываем главное меню
            await message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            await processing_msg.edit_text(
                "😔 Что-то пошло не так\n\n"
                "Не удалось создать видео. Возможные причины:\n"
                "• Превышено время ожидания\n"
                "• Временные проблемы с сервером\n\n"
                "💡 Попробуйте ещё раз через пару минут\n\n"
                "💛 Не переживайте, баланс не пострадал"
        )
    
            # Автоматически открываем главное меню
            await message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Ошибка при генерации видео: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ Произошла ошибка при генерации. Попробуйте позже."
        )
    
    # Очищаем состояние
    await state.clear()


@router.callback_query(F.data == "back_to_video_format")
async def back_to_video_format_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат к выбору формата"""
    await callback.message.edit_text(
        "Выберите лучший формат генерации 🚀",
        reply_markup=get_video_format_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "video_instruction_generation")
async def video_instruction_generation_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Видео-инструкция' в разделе создания видео"""
    await callback.message.answer(
        "📹 Видео-инструкция\n\n"
        "Здесь будет видео-инструкция по созданию видео."
    )
    await callback.answer()