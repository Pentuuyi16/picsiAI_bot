from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# File ID видео-примера для управления движением
EXAMPLE_VIDEO_FILE_ID = "ТВОЙ_FILE_ID_СЮДА"  # Загрузи видео и получи file_id


class MotionControlStates(StatesGroup):
    """Состояния для процесса управления движением"""
    waiting_for_quality = State()
    waiting_for_photo = State()
    waiting_for_video = State()


@router.callback_query(F.data == "motion_control")
async def motion_control_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Управление движением'"""
    from database.database import Database
    from keyboards.inline import get_motion_control_keyboard
    
    user_id = callback.from_user.id
    
    # Получаем баланс из БД
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "<b>✨ Наш бот умеет управлять движением</b>\n\n"
        "<b>Готовы создать видео, которое удивляет?</b>\n\n"
        "1️⃣ <b><i>Выберите качество</i></b> — 720p или 1080p.\n"
        "2️⃣ <b><i>Загрузите фото</i></b> в бот — быстро и просто.\n"
        "3️⃣ <b><i>Отправьте видео-пример</i></b> для управления движением.\n"
        "4️⃣ <b><i>Подождите</i></b> 5–10 минут — и получите своё уникальное видео!\n\n"
        "<b><i>Создавайте контент</i></b>, который цепляет и выделяет вас 💫\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
        f"📹 Генерация видео 720p 1 секунда = 5₽\n"
        f"📹 Генерация видео 1080p 1 секунда = 7₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое с видео (если есть)
    try:
        await callback.message.answer_video(
            video=EXAMPLE_VIDEO_FILE_ID,
            caption=text,
            parse_mode="HTML",
            reply_markup=get_motion_control_keyboard()
        )
    except:
        # Если видео не загружено, отправляем просто текст
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_motion_control_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data == "control_motion")
async def control_motion_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Управлять движением'"""
    from keyboards.inline import get_motion_quality_keyboard
    
    await callback.message.answer(
        "🎨 Выберите <b><i>качество</i></b> генерации:",
        parse_mode="HTML",
        reply_markup=get_motion_quality_keyboard()
    )
    await state.set_state(MotionControlStates.waiting_for_quality)
    await callback.answer()


@router.callback_query(F.data.startswith("motion_quality_"))
async def motion_quality_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора качества"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    quality = callback.data.replace("motion_quality_", "")
    
    # Сохраняем качество
    await state.update_data(motion_quality=quality)
    
    quality_name = "720p" if quality == "720p" else "1080p"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="motion_control")]
        ]
    )
    
    await callback.message.edit_text(
        f"<b>✨ Отлично!</b>\n\n"
        f"<blockquote>🎨 Качество: {quality_name}</blockquote>\n\n"
        f"📷 Теперь <b><i>загрузите фото</i></b>, которое хотите анимировать",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(MotionControlStates.waiting_for_photo)
    await callback.answer()


@router.message(MotionControlStates.waiting_for_photo, F.photo)
async def process_motion_photo(message: Message, state: FSMContext):
    """Обработчик получения фото"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Получаем URL фото
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"
    
    # Сохраняем URL фото
    await state.update_data(motion_photo=file_url)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="motion_control")]
        ]
    )
    
    await message.answer(
        "📹 Отлично! Теперь <b><i>отправьте видео-пример</i></b> для управления движением",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(MotionControlStates.waiting_for_video)


@router.message(MotionControlStates.waiting_for_video, F.video)
async def process_motion_video(message: Message, state: FSMContext, bot):
    """Обработчик получения видео"""
    from database.database import Database
    from keyboards.inline import get_payment_methods_keyboard, get_main_menu_keyboard
    from utils.texts import TEXTS
    from utils.motion_control_client import MotionControlClient
    from aiogram.types import URLInputFile
    import json
    
    # Получаем URL видео
    video = message.video
    file = await bot.get_file(video.file_id)
    video_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    video_duration = video.duration  # Длительность в секундах
    
    # Сохраняем URL видео
    await state.update_data(motion_video=video_url, video_duration=video_duration)
    
    # Получаем данные
    data = await state.get_data()
    quality = data.get("motion_quality", "720p")
    photo_url = data.get("motion_photo")
    
    # Определяем character_orientation и максимальную длительность
    character_orientation = "video"
    max_duration = 30 if character_orientation == "video" else 10
    
    # Проверяем длительность видео
    if video_duration > max_duration:
        await message.answer(
            f"❌ Видео слишком длинное!\n\n"
            f"Максимальная длительность: <b>{max_duration} секунд</b>\n"
            f"Ваше видео: <b>{video_duration} секунд</b>\n\n"
            f"Пожалуйста, загрузите видео покороче.",
            parse_mode="HTML"
        )
        return
    
    # Рассчитываем стоимость
    price_per_second = 5.00 if quality == "720p" else 7.00
    required_amount = price_per_second * video_duration
    
    db = Database()
    user = db.get_user(message.from_user.id)
    balance = user['balance'] if user else 0.00
    
    # Проверяем баланс
    if balance < required_amount:
        # Сохраняем текущее состояние для продолжения после оплаты
        action_data = json.dumps({
            "back_to": "motion_control",
            "state_data": data
        })
        db.save_pending_action(message.from_user.id, "motion_control_pending", action_data)
        
        await message.answer(
            "Похоже, средств сейчас немного не хватает\n\n"
            f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
            f"📹 Длительность видео: {video_duration} сек\n"
            f"💵 Стоимость: {required_amount:.2f} ₽</blockquote>\n\n"
            "Выберите способ оплаты ⤵️",
            parse_mode="HTML",
            reply_markup=get_payment_methods_keyboard(back_to="motion_control")
        )
        await state.clear()
        return
    
    # Баланс достаточен - начинаем генерацию
    processing_msg = await message.answer(
        "⭐ Начинается генерация видео подождите 10-15 минут,так как процесс довольно трудоемкий"
    )
    
    try:
        motion_client = MotionControlClient()
        
        # Создаем задачу
        task_id = await motion_client.create_task(
            image_url=photo_url,
            video_url=video_url,
            prompt="",
            character_orientation=character_orientation,
            mode=quality
        )
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        # Ожидаем результат (макс 20 минут)
        result_url = await motion_client.wait_for_result(task_id, max_attempts=120, delay=10)
        
        if result_url:
            if result_url == "MODERATION_ERROR":
                # Ошибка модерации - баланс НЕ списывается
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось создать видео\n\n"
                    "Система безопасности заблокировала запрос.\n\n"
                    "Частые причины:\n"
                    "• На фото известная личность\n"
                    "• В видео неподходящий контент\n\n"
                    "💡 Совет: используйте обычные фотографии и нейтральные видео\n\n"
                    "💛 Не переживайте, баланс не пострадал"
                )
            else:
                # Успешная генерация - списываем средства
                new_balance = balance - required_amount
                db.update_user_balance(message.from_user.id, new_balance)
                
                # Отправляем видео
                try:
                    video_file = URLInputFile(result_url)
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption="✨ Ваше видео с управлением движением готово!",
                        request_timeout=180
                    )
                    await processing_msg.delete()
                    
                    db.save_generation(message.from_user.id, "motion_control", result_url, "")
                except Exception as e:
                    print(f"❌ Ошибка отправки видео: {e}")
                    await processing_msg.edit_text(
                        "❌ Не удалось отправить видео. Попробуйте позже."
                    )
            
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
            
            await message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_main_menu_keyboard(),
                parse_mode="HTML"
            )
    
    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        import traceback
        traceback.print_exc()
        
        await processing_msg.edit_text(
            "❌ Произошла ошибка при генерации. Попробуйте позже."
        )
    
    await state.clear()


@router.callback_query(F.data == "video_instruction_motion")
async def video_instruction_motion_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Видео-инструкция' в разделе управления движением"""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="motion_control")]
        ]
    )
    
    await callback.message.answer_video(
        video="ТВОЙ_FILE_ID_ИНСТРУКЦИИ",  # Загрузи видео-инструкцию
        caption="<b>📹 Видео-инструкция по управлению движением</b>\n\n"
                "Всего пару минут — и вы узнаете, как добиться качественного и эффектного результата ✨",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_motion")
async def top_up_balance_motion_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из раздела управления движением"""
    from keyboards.inline import get_balance_amounts_keyboard
    
    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="motion_control")
    )
    await callback.answer()