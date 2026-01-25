from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, URLInputFile, BufferedInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import (
    get_edit_aspect_ratio_keyboard,
    get_images_menu_keyboard
)
from utils.nano_banana_edit_client import NanoBananaEditClient
from utils.texts import TEXTS
import logging
import aiohttp
from PIL import Image
from io import BytesIO
import asyncio

media_group_photos = {}

router = Router()
edit_client = NanoBananaEditClient()
logger = logging.getLogger(__name__)

# File ID вашего видео-примера
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAIP1GlvXQP3IpSzDLkLoAEYxM2exOUtAAIPjgACSD94S2Q60dKRpjJ0OAQ"


# Временное хранилище для обработанных медиа-групп (по user_id)
processed_media_groups_edit = {}

# Словарь для хранения фото из медиа-групп (по user_id)
media_group_photos = {}


class ImageEditingStates(StatesGroup):
    """Состояния для процесса редактирования изображений"""
    waiting_for_aspect_ratio = State()
    waiting_for_photos = State()
    waiting_for_description = State()
    waiting_for_model = State()


async def compress_image(image_url: str, max_size_mb: float = 10.0, quality: int = 85) -> BufferedInputFile:
    """
    Скачивает и сжимает изображение для отправки в Telegram
    
    Args:
        image_url: URL изображения
        max_size_mb: Максимальный размер в МБ (по умолчанию 10 МБ для Telegram фото)
        quality: Качество JPEG (1-100, рекомендуется 85-90)
    
    Returns:
        BufferedInputFile для отправки в Telegram
    """
    print(f"🔧 Начинаем сжатие изображения...")
    print(f"   URL: {image_url}")
    print(f"   Max size: {max_size_mb} MB")
    print(f"   Quality: {quality}")
    
    # Скачиваем изображение
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_data = await response.read()
            original_size_mb = len(image_data) / (1024 * 1024)
            print(f"📦 Скачано: {original_size_mb:.2f} MB")
    
    # Открываем изображение
    img = Image.open(BytesIO(image_data))
    print(f"🖼️ Размер изображения: {img.size[0]}x{img.size[1]}, режим: {img.mode}")
    
    # Конвертируем в RGB если нужно (для JPEG)
    if img.mode in ('RGBA', 'P', 'LA'):
        print(f"🔄 Конвертируем {img.mode} → RGB")
        # Создаем белый фон для прозрачности
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Сжимаем до нужного размера
    output = BytesIO()
    current_quality = quality
    
    while current_quality > 20:  # Не опускаемся ниже 20%
        output.seek(0)
        output.truncate()
        
        img.save(output, format='JPEG', quality=current_quality, optimize=True)
        size_mb = output.tell() / (1024 * 1024)
        
        print(f"   Попытка quality={current_quality}: {size_mb:.2f} MB")
        
        if size_mb <= max_size_mb:
            print(f"✅ Сжатие завершено: {original_size_mb:.2f} MB → {size_mb:.2f} MB (качество {current_quality})")
            break
        
        current_quality -= 5
    
    output.seek(0)
    return BufferedInputFile(output.read(), filename="image.jpg")


@router.callback_query(F.data == "image_editing")
async def image_editing_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Редактирование изображений'"""
    from database.database import Database

    user_id = callback.from_user.id

    # Получаем количество генераций
    db = Database()
    generations = db.get_user_generations(user_id)

    generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций"
    if generations == 1 and not db.has_purchased_generations(user_id):
        generation_text += "\n🎨 Вам доступна 1 бесплатная генерация"
    generation_text += "</blockquote>"

    text = (
        "📐 Выберите соотношение сторон для редактирования:\n\n"
        f"{generation_text}"
    )

    # Пытаемся отредактировать сообщение
    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_edit_aspect_ratio_keyboard()
        )
    except:
        # Если не получилось (например, сообщение с видео), удаляем и отправляем новое
        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_edit_aspect_ratio_keyboard()
        )

    await state.set_state(ImageEditingStates.waiting_for_aspect_ratio)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_aspect_"))
async def edit_aspect_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора соотношения сторон"""
    from database.database import Database
    from keyboards.inline import get_trend_model_selection_keyboard

    # Проверяем текущее состояние
    current_state = await state.get_state()

    # Обрабатываем только если мы в состоянии редактирования
    if current_state != ImageEditingStates.waiting_for_aspect_ratio:
        return

    aspect_ratio_raw = callback.data.replace("edit_aspect_", "")

    # Преобразуем формат: "9_16" -> "9:16"
    aspect_ratio = aspect_ratio_raw.replace("_", ":")

    # Сохраняем выбранное соотношение
    await state.update_data(edit_aspect_ratio=aspect_ratio)

    # Получаем количество генераций для показа в выборе модели
    user_id = callback.from_user.id
    db = Database()
    generations = db.get_user_generations(user_id)

    # Показываем выбор модели
    await callback.message.edit_text(
        "<b>🤖 Выбор модели генерации</b>\n\n"
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

    # Переходим к ожиданию выбора модели
    await state.set_state(ImageEditingStates.waiting_for_model)
    await callback.answer()


@router.callback_query(ImageEditingStates.waiting_for_model, F.data.in_(["trend_model_standard", "trend_model_pro"]))
async def edit_model_selection_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора модели ДО загрузки фото"""
    model_type = "standard" if callback.data == "trend_model_standard" else "pro"

    # Сохраняем выбранную модель
    await state.update_data(edit_model=model_type)

    # Получаем сохраненное соотношение
    data = await state.get_data()
    aspect_ratio = data.get("edit_aspect_ratio", "1:1")
    aspect_name = "квадратное" if aspect_ratio == "1:1" else "вертикальное" if aspect_ratio == "9:16" else "горизонтальное"

    model_name = "Nano Banana" if model_type == "standard" else "Nano Banana Pro"

    await callback.message.edit_text(
        f"<b>✨ Всё настроено!</b>\n\n"
        f"<blockquote>📐 Соотношение: {aspect_name}\n"
        f"🤖 Модель: {model_name}</blockquote>\n\n"
        f"📷 Теперь <b><i>загрузите фото</i></b>, которое хотите отредактировать (можно до 8 фото)",
        parse_mode="HTML"
    )

    # Переходим к ожиданию фото
    await state.set_state(ImageEditingStates.waiting_for_photos)
    await callback.answer()


@router.message(ImageEditingStates.waiting_for_photos, F.photo)
async def handle_edit_photos(message: Message, state: FSMContext, bot: Bot):
    """Обработчик загрузки фото для редактирования"""
    user_id = message.from_user.id
    
    # Получаем URL фото
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    photo_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    # Если это часть медиа-группы
    if message.media_group_id:
        # Инициализируем список для этого пользователя, если его нет
        if user_id not in media_group_photos:
            media_group_photos[user_id] = []
        
        # Добавляем фото в список
        media_group_photos[user_id].append(photo_url)
        
        # Проверяем, обрабатывали ли мы эту медиа-группу
        if message.media_group_id in processed_media_groups_edit.get(user_id, set()):
            return
        
        # Помечаем медиа-группу как обработанную
        if user_id not in processed_media_groups_edit:
            processed_media_groups_edit[user_id] = set()
        processed_media_groups_edit[user_id].add(message.media_group_id)
        
        # Ждём немного, чтобы все фото из группы успели загрузиться
        await asyncio.sleep(1)
        
        # Получаем все фото из медиа-группы
        photos = media_group_photos.get(user_id, [])
        
        # Очищаем временное хранилище
        if user_id in media_group_photos:
            del media_group_photos[user_id]
        
    else:
        # Одиночное фото
        photos = [photo_url]
    
    # Сохраняем фото в состоянии
    await state.update_data(edit_photos=photos)

    # Запрашиваем описание редактирования
    await message.answer(
        f"📷 Фото получено! ({len(photos)} шт.)\n\n"
        f"✍️ Теперь <b><i>опишите</i></b>, как вы хотите отредактировать изображение:",
        parse_mode="HTML"
    )

    await state.set_state(ImageEditingStates.waiting_for_description)


@router.message(ImageEditingStates.waiting_for_description, F.text)
async def process_edit_description(message: Message, state: FSMContext, bot: Bot):
    """Обработчик описания редактирования - сразу запускает генерацию"""
    from database.database import Database
    import json

    prompt = message.text
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Получаем данные состояния
    data = await state.get_data()
    model_type = data.get('edit_model', 'standard')
    aspect_ratio = data.get("edit_aspect_ratio", "1:1")
    photos = data.get("edit_photos", [])

    generations_cost = 1 if model_type == "standard" else 4

    db = Database()
    generations = db.get_user_generations(user_id)

    # Проверяем количество генераций
    if generations < generations_cost:
        action_data = json.dumps({
            "back_to": "image_editing",
            "state_data": data,
            "prompt": prompt,
            "model_type": model_type
        })
        db.save_pending_action(user_id, "image_editing_pending", action_data)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations_from_editing")],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )

        await message.answer(
            "У вас закончились генерации 😔\n\n"
            f"<blockquote>⚡ Доступно: {generations} генераций\n"
            f"🎨 Выбранная модель требует: {generations_cost} генерации</blockquote>\n\n"
            "Купите пакет генераций, чтобы продолжить!",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        await state.clear()
        return

    logger.info(f"Получен промпт: {prompt}")
    logger.info(f"Соотношение: {aspect_ratio}, Фото: {len(photos)}, Модель: {model_type}")

    processing_msg = await bot.send_message(
        chat_id=chat_id,
        text="⭐ Начинается редактирование изображения, совсем скоро пришлем результат"
    )

    try:
        if model_type == "standard":
            from utils.nano_banana_edit_client import NanoBananaEditClient
            edit_client_instance = NanoBananaEditClient()
            task_id = await edit_client_instance.create_edit_task(
                prompt=prompt, image_urls=photos, image_size=aspect_ratio, output_format="png"
            )
        else:
            from utils.image_edit_client import ImageEditClient
            edit_client_instance = ImageEditClient()
            task_id = await edit_client_instance.create_edit_task(
                prompt=prompt, image_urls=photos, aspect_ratio=aspect_ratio, resolution="2K", output_format="png"
            )

        if not task_id:
            await processing_msg.edit_text("❌ Произошла ошибка при создании задачи. Попробуйте позже.")
            await state.clear()
            return

        if model_type == "pro":
            async def update_progress(elapsed_min, remaining_min):
                try:
                    await processing_msg.edit_text(
                        f"⭐ Идет генерация в высоком качестве...\n\n"
                        f"⏱️ Прошло: {elapsed_min} мин\n⏳ Осталось примерно: {remaining_min} мин\n\n"
                        f"💡 Профессиональная модель создает изображения в 4K"
                    )
                except:
                    pass
            image_url = await edit_client_instance.wait_for_result(task_id, max_attempts=240, delay=5, progress_callback=update_progress)
        else:
            image_url = await edit_client_instance.wait_for_result(task_id, max_attempts=120, delay=5)

        if image_url:
            if image_url == "MODERATION_ERROR":
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось отредактировать изображение\n\n"
                    "Система безопасности заблокировала запрос.\n\n💛 Не переживайте, генерация не списана"
                )
            else:
                db.subtract_generations(user_id, generations_cost)
                compressed_image = await compress_image(image_url, max_size_mb=9.5, quality=85)
                await bot.send_photo(chat_id=chat_id, photo=compressed_image, caption="✨ Ваше изображение готово!", request_timeout=180)
                await processing_msg.delete()
                db.save_generation(user_id, "image_editing", image_url, prompt)

            generations = db.get_user_generations(user_id)
            generation_text = f"<blockquote>⚡ У вас осталось: {generations} генераций</blockquote>"
            await bot.send_message(chat_id=chat_id, text=f"<b>🖼️ Работа с изображениями</b>\n\n✨ <b>Создать фото</b> — генерация изображений с нуля\n🎨 <b>Отредактировать фото</b> — изменить изображение по описанию\n\n{generation_text}", reply_markup=get_images_menu_keyboard(), parse_mode="HTML")
    except Exception as e:
        logger.error(f"Ошибка: {e}", exc_info=True)
        await processing_msg.edit_text("❌ Произошла ошибка при редактировании.")

    await state.clear()


@router.callback_query(F.data == "back_to_edit_aspect")
async def back_to_edit_aspect_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Назад' - возврат к выбору соотношения сторон"""
    await callback.message.edit_text(
        "📐 Выберите соотношение сторон для редактирования:",
        reply_markup=get_edit_aspect_ratio_keyboard()
    )
    await state.set_state(ImageEditingStates.waiting_for_aspect_ratio)
    await callback.answer()


@router.callback_query(F.data == "video_instruction_editing")
async def video_instruction_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Видео-инструкция' в разделе редактирования"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="image_editing")]
        ]
    )
    
    await callback.message.answer_video(
        video="BAACAgIAAxkBAAIEm2lj89wQUbrn5anGqPd_m0MfSz8OAAIunQACHSMgSwihmsAAAVHFmzgE",
        caption="<b>📹 Видео-инструкция по редактированию изображений</b>\n\n"
                "Всего пару минут — и вы узнаете, как добиться качественного и эффектного результата ✨",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_editing")
async def top_up_balance_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Купить генерации' из раздела редактирования"""
    # Перенаправляем на покупку генераций
    from handlers.generation_purchase import buy_generations_handler
    await buy_generations_handler(callback)