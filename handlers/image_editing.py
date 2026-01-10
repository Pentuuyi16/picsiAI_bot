from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import (
    get_image_editing_keyboard, 
    get_edit_aspect_ratio_keyboard, 
    get_photo_quality_keyboard,
    get_main_menu_keyboard
)
from utils.image_edit_client import ImageEditClient
from utils.texts import TEXTS
import logging

media_group_photos = {}

router = Router()
edit_client = ImageEditClient()
logger = logging.getLogger(__name__)

# File ID вашего видео-примера
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAICO2liyr_MOOoghDYiIXaVhGJ5lzr4AAKjlQACHwgRSxI0RKJUQwH6OAQ"


# Временное хранилище для обработанных медиа-групп (по user_id)
processed_media_groups_edit = {}

# Словарь для хранения фото из медиа-групп (по user_id)
media_group_photos = {}


class ImageEditingStates(StatesGroup):
    """Состояния для процесса редактирования изображений"""
    waiting_for_aspect_ratio = State()
    waiting_for_quality = State()
    waiting_for_photos = State()
    waiting_for_description = State()


@router.callback_query(F.data == "image_editing")
async def image_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Редактирование изображений'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    
    # Получаем баланс из БД
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "✨ <b>Наш бот помогает преобразить изображения и раскрыть их по-новому!</b>\n\n"
        "<b>Как отредактировать изображение?</b>\n\n"
        "1️⃣ <b><i>Загрузите фото</i></b>, которое хотите изменить.\n"
        "2️⃣ <b><i>Опишите желаемые правки</i></b> — улучшение качества, изменение деталей или общего настроения.\n"
        "3️⃣ <b><i>Подождите всего пару минут</i></b> — и получите изображение с качественным редактированием.\n\n"
        "Ваши <b><i>фото</i></b> могут выглядеть ещё лучше 💫\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
        f"🎨 Редактирование 1 фото = 25₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    await callback.message.delete()
    
    # Отправляем новое с видео
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_image_editing_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data == "edit_photo")
async def edit_image_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Редактировать изображение'"""
    await callback.message.answer(
        "📐 Выберите <b><i>соотношение</i></b> сторон для редактирования:",
        parse_mode="HTML",
        reply_markup=get_edit_aspect_ratio_keyboard()
    )
    await state.set_state(ImageEditingStates.waiting_for_aspect_ratio)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_aspect_"))
async def edit_aspect_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора соотношения сторон"""
    aspect_ratio_raw = callback.data.replace("edit_aspect_", "")
    
    # Преобразуем формат: "9_16" -> "9:16"
    aspect_ratio = aspect_ratio_raw.replace("_", ":")
    
    # Сохраняем выбранное соотношение
    await state.update_data(edit_aspect_ratio=aspect_ratio)
    
    aspect_name = "квадратное" if aspect_ratio == "1:1" else "вертикальное" if aspect_ratio == "9:16" else "горизонтальное"
    
    await callback.message.edit_text(
        f"📐 Соотношение сторон: {aspect_name}\n\n"
        f"🎨 Теперь <b><i>выберите</i></b> качество редактирования:",
        parse_mode="HTML",
        reply_markup=get_photo_quality_keyboard()
    )
    await state.set_state(ImageEditingStates.waiting_for_quality)
    await callback.answer()


@router.callback_query(F.data.startswith("quality_"))
async def edit_quality_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора качества"""
    quality = callback.data.replace("quality_", "").upper()
    
    # Сохраняем выбранное качество
    await state.update_data(edit_quality=quality)
    
    data = await state.get_data()
    aspect_ratio = data.get("edit_aspect_ratio", "1:1")
    aspect_name = "квадратное" if aspect_ratio == "1:1" else "вертикальное" if aspect_ratio == "9:16" else "горизонтальное"
    
    await callback.message.edit_text(
        f"<b>✨ Всё настроено!</b>\n\n"
        f"<blockquote>📐 Соотношение: {aspect_name}\n"
        f"🎨 Качество: {quality}</blockquote>\n\n"
        f"📷 Теперь <b><i>загрузите фото</i></b>, которое хотите отредактировать (можно до 8 фото)",
        parse_mode="HTML"
    )
    await state.set_state(ImageEditingStates.waiting_for_photos)
    await callback.answer()


# Словарь для хранения фото из медиа-групп
media_group_photos = {}

@router.message(ImageEditingStates.waiting_for_photos, F.photo)
async def process_edit_photos(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения фотографий для редактирования"""
    import asyncio
    
    user_id = message.from_user.id
    
    # Получаем URL фото
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    # Если это медиа-группа
    if message.media_group_id:
        media_group_id = message.media_group_id
        
        # Инициализируем словари для пользователя
        if user_id not in media_group_photos:
            media_group_photos[user_id] = {}
        if user_id not in processed_media_groups_edit:
            processed_media_groups_edit[user_id] = set()
        
        # Добавляем фото в словарь медиа-группы
        if media_group_id not in media_group_photos[user_id]:
            media_group_photos[user_id][media_group_id] = []
        media_group_photos[user_id][media_group_id].append(file_url)
        
        # Если группа уже обработана - просто выходим
        if media_group_id in processed_media_groups_edit[user_id]:
            return
        
        # Помечаем как обработанную
        processed_media_groups_edit[user_id].add(media_group_id)
        
        # Ждём чтобы все фото пришли
        await asyncio.sleep(1.0)
        
        # Получаем все фото из этой группы
        all_photos = media_group_photos[user_id].get(media_group_id, [])
        
        # Сохраняем в состояние
        await state.update_data(edit_photos=all_photos)
        
        # Удаляем из словаря
        del media_group_photos[user_id][media_group_id]
        
        # Отправляем запрос на описание
        await message.answer(
            f"📝 Получено фото: {len(all_photos)}\n\n"
            f"Теперь опишите, какие изменения хотите внести в изображение"
        )
        await state.set_state(ImageEditingStates.waiting_for_description)
    else:
        # Одиночное фото
        await state.update_data(edit_photos=[file_url])
        
        await message.answer(
            "📝 Опишите, какие изменения хотите внести в изображение"
        )
        await state.set_state(ImageEditingStates.waiting_for_description)



@router.message(ImageEditingStates.waiting_for_description, F.text)
async def process_edit_description(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения описания для редактирования"""
    from database.database import Database
    from keyboards.inline import get_payment_methods_keyboard
    import json
    
    db = Database()
    user = db.get_user(message.from_user.id)
    
    # Получаем данные состояния
    data = await state.get_data()
    
    # Проверяем баланс
    balance = user['balance'] if user else 0.00
    required_amount = 25.00  # Стоимость редактирования изображения
    
    if balance < required_amount:
        # Сохраняем текущее состояние для продолжения после оплаты
        prompt = message.text
        action_data = json.dumps({
            "back_to": "image_editing",
            "state_data": data,  # Сохраняем ВСЁ: соотношение, качество, фото
            "prompt": prompt
        })
        db.save_pending_action(message.from_user.id, "image_editing_pending", action_data)
        
        print(f"💾 Сохранено состояние для редактирования изображения:")
        print(f"   Aspect ratio: {data.get('edit_aspect_ratio')}")
        print(f"   Quality: {data.get('edit_quality')}")
        print(f"   Photos: {len(data.get('edit_photos', []))} шт")
        print(f"   Prompt: {prompt}")
        
        await message.answer(
            "Похоже, средств сейчас немного не хватает\n\n"
            f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
            f"🎨 Редактирование 1 фото = 25₽</blockquote>\n\n"
            "Выберите способ оплаты ⤵️",
            parse_mode="HTML",
            reply_markup=get_payment_methods_keyboard(back_to="image_editing")
        )
        # НЕ очищаем состояние!
        return
    
    prompt = message.text
    aspect_ratio = data.get("edit_aspect_ratio", "1:1")
    resolution = data.get("edit_quality", "1K")
    photos = data.get("edit_photos", [])
    
    logger.info(f"Получен промпт: {prompt}")
    logger.info(f"Соотношение: {aspect_ratio}, Качество: {resolution}, Фото: {len(photos)}")
    
    # Отправляем сообщение о начале редактирования
    processing_msg = await message.answer(
        "⭐ Начинается редактирование изображения, совсем скоро пришлем результат"
    )
    
    try:
        # Создаём задачу на редактирование
        task_id = await edit_client.create_edit_task(
            prompt=prompt,
            image_urls=photos,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            output_format="png"
        )
        
        logger.info(f"Task ID: {task_id}")
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        # Ожидаем завершения редактирования
        logger.info("Ожидание завершения редактирования...")
        image_url = await edit_client.wait_for_result(task_id, max_attempts=120, delay=5)
        
        logger.info(f"Image URL: {image_url}")
        
        if image_url:
            if image_url == "MODERATION_ERROR":
                # Ошибка модерации - баланс НЕ списывается
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось отредактировать изображение\n\n"
                    "Система безопасности заблокировала запрос.\n\n"
                    "Частые причины:\n"
                    "• На фото известная личность\n"
                    "• В описании есть неподходящий контент\n\n"
                    "💡 Совет: используйте обычные фотографии и нейтральные описания\n\n"
                    "💛 Не переживайте, баланс не пострадал"
                )
            else:
                # Успешная генерация - списываем средства
                new_balance = balance - required_amount
                db.update_user_balance(message.from_user.id, new_balance)
                
                # Отправляем изображение
                try:
                    image_file = URLInputFile(image_url)
                    await bot.send_photo(
                        chat_id=message.chat.id,
                        photo=image_file,
                        caption="✨ Ваше изображение готово!",
                        request_timeout=180
                    )
                    
                    # Удаляем сообщение о генерации ТОЛЬКО после успешной отправки
                    await processing_msg.delete()

                    # Сохраняем генерацию в БД
                    db.save_generation(message.from_user.id, "image_editing", image_url, prompt)
                except Exception as e:
                    await processing_msg.edit_text(
                        "❌ Не удалось отправить изображение. Попробуйте позже."
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
                "Не удалось отредактировать изображение. Возможные причины:\n"
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
        logger.error(f"Ошибка при редактировании изображения: {e}", exc_info=True)
        await processing_msg.edit_text(
            "❌ Произошла ошибка при редактировании. Попробуйте позже."
        )
    
    # Очищаем состояние
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
    await callback.message.answer(
        "📹 Видео-инструкция\n\n"
        "Здесь будет видео-инструкция по редактированию изображений."
    )
    await callback.answer()