from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging

router = Router()
logger = logging.getLogger(__name__)

# File ID примеров
EXAMPLE_PHOTO_FILE_ID = "AgACAgIAAxkBAAIF-Gl1-zo9bkw5wjD2wi9Pw56h2wxNAAI9DWsbdrexS4Ys4lAko2MjAQADAgADdwADOAQ"
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAIF9ml1-zMsBAYVqGFe0z-CPD4z6lI2AAI9oAACdrexSwQmgr_uVOIdOAQ"


class MotionControlStates(StatesGroup):
    """Состояния для процесса управления движением"""
    waiting_for_photo = State()
    waiting_for_video = State()
    waiting_for_quality = State()


@router.callback_query(F.data == "motion_control")
async def motion_control_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Управление движением'"""
    user_id = callback.from_user.id
    logger.info(f"User {user_id} opened motion control")

    text = (
        "📷 <b>Пример фото для управления движением</b>\n\n"
        "Теперь <b><i>загрузите ваше фото</i></b>, которое хотите анимировать:"
    )

    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass

    # Отправляем фото-пример
    await callback.message.answer_photo(
        photo=EXAMPLE_PHOTO_FILE_ID,
        caption=text,
        parse_mode="HTML"
    )

    await state.set_state(MotionControlStates.waiting_for_photo)
    await callback.answer()


@router.message(MotionControlStates.waiting_for_photo, F.photo)
async def process_motion_photo(message: Message, state: FSMContext):
    """Обработчик получения фото"""
    user_id = message.from_user.id

    # Получаем URL фото
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{message.bot.token}/{file.file_path}"

    logger.info(f"User {user_id} uploaded photo: {file_url}")

    # Сохраняем URL фото
    await state.update_data(motion_photo=file_url)

    text = (
        "📹 <b>Пример видео для управления движением</b>\n\n"
        "Теперь <b><i>загрузите ваше видео-пример</i></b> для управления движением:"
    )

    # Отправляем видео-пример
    await message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML"
    )

    await state.set_state(MotionControlStates.waiting_for_video)


@router.message(MotionControlStates.waiting_for_video, F.video)
async def process_motion_video(message: Message, state: FSMContext, bot):
    """Обработчик получения видео"""
    from keyboards.inline import get_motion_quality_keyboard

    user_id = message.from_user.id

    logger.info(f"\n{'='*70}")
    logger.info(f"🎬 MOTION CONTROL - VIDEO UPLOAD")
    logger.info(f"User ID: {user_id}")

    # Получаем URL видео
    video = message.video
    file = await bot.get_file(video.file_id)
    video_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    video_duration = video.duration

    # Детальная информация о файле
    logger.info(f"===== FILE INFO =====")
    logger.info(f"File ID: {video.file_id}")
    logger.info(f"File unique ID: {video.file_unique_id}")
    logger.info(f"File name: {video.file_name if hasattr(video, 'file_name') else 'N/A'}")
    logger.info(f"MIME type: {video.mime_type}")
    logger.info(f"File size: {video.file_size} bytes ({video.file_size / (1024*1024):.2f} MB)")
    logger.info(f"File path from Telegram: {file.file_path}")
    logger.info(f"Full file URL: {video_url}")
    logger.info(f"=====================")

    # Проверяем разрешение видео
    video_width = video.width
    video_height = video.height

    logger.info(f"Video URL: {video_url}")
    logger.info(f"Video duration: {video_duration} seconds")
    logger.info(f"Video resolution: {video_width}x{video_height}")

    # Проверяем минимальное разрешение
    if video_width < 720 or video_height < 720:
        logger.warning(f"Video resolution too low: {video_width}x{video_height}")
        await message.answer(
            f"❌ Разрешение видео слишком низкое!\n\n"
            f"<b>Минимальные требования:</b>\n"
            f"• Ширина: минимум 720 пикселей\n"
            f"• Высота: минимум 720 пикселей\n\n"
            f"<b>Ваше видео:</b> {video_width}x{video_height}\n\n"
            f"💡 Загрузите видео с более высоким разрешением",
            parse_mode="HTML"
        )
        return

    # Определяем максимальную длительность
    max_duration = 30

    # Проверяем длительность видео
    if video_duration > max_duration:
        logger.warning(f"Video too long: {video_duration}s > {max_duration}s")
        await message.answer(
            f"❌ Видео слишком длинное!\n\n"
            f"Максимальная длительность: <b>{max_duration} секунд</b>\n"
            f"Ваше видео: <b>{video_duration} секунд</b>\n\n"
            f"Пожалуйста, загрузите видео покороче.",
            parse_mode="HTML"
        )
        return

    # Сохраняем URL видео
    await state.update_data(motion_video=video_url, video_duration=video_duration)

    # Просим выбрать качество
    await message.answer(
        "🎨 Выберите <b><i>качество</i></b> генерации:",
        parse_mode="HTML",
        reply_markup=get_motion_quality_keyboard()
    )
    await state.set_state(MotionControlStates.waiting_for_quality)


@router.callback_query(F.data.startswith("motion_quality_"))
async def motion_quality_handler(callback: CallbackQuery, state: FSMContext, bot):
    """Обработчик выбора качества - запускает генерацию"""
    from database.database import Database
    from keyboards.inline import get_payment_methods_keyboard, get_video_menu_keyboard
    from utils.texts import TEXTS
    from utils.motion_control_client import MotionControlClient
    from aiogram.types import URLInputFile
    import json

    quality = callback.data.replace("motion_quality_", "")
    user_id = callback.from_user.id

    logger.info(f"User {user_id} selected quality: {quality}")

    # Получаем данные
    data = await state.get_data()
    photo_url = data.get("motion_photo")
    video_url = data.get("motion_video")
    video_duration = data.get("video_duration")

    logger.info(f"Quality: {quality}")
    logger.info(f"Photo URL: {photo_url}")
    logger.info(f"Video URL: {video_url}")
    logger.info(f"Video duration: {video_duration}")

    # Рассчитываем стоимость
    price_per_second = 5.00 if quality == "720p" else 7.00
    required_amount = price_per_second * video_duration

    logger.info(f"Price per second: {price_per_second}₽")
    logger.info(f"Required amount: {required_amount}₽")

    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00

    logger.info(f"User balance: {balance}₽")
    logger.info(f"{'='*70}\n")

    # Проверяем баланс
    if balance < required_amount:
        logger.info(f"Insufficient balance. Saving pending action...")

        # Сохраняем текущее состояние для продолжения после оплаты
        action_data = json.dumps({
            "back_to": "motion_control",
            "state_data": {
                "motion_quality": quality,
                "motion_photo": photo_url,
                "motion_video": video_url,
                "video_duration": video_duration
            }
        })
        db.save_pending_action(user_id, "motion_control_pending", action_data)

        await callback.message.answer(
            "Похоже, средств сейчас немного не хватает\n\n"
            f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
            f"📹 Длительность видео: {video_duration} сек\n"
            f"💵 Стоимость: {required_amount:.2f} ₽</blockquote>\n\n"
            "Выберите способ оплаты ⤵️",
            parse_mode="HTML",
            reply_markup=get_payment_methods_keyboard(back_to="motion_control")
        )
        await state.clear()
        await callback.answer()
        return

    # Баланс достаточен - начинаем генерацию
    logger.info(f"✅ Balance sufficient. Starting generation...")

    processing_msg = await callback.message.answer(
        "⭐ Начинается генерация, пожалуйста подождите 5-10 минут, так как процесс довольно трудоемкий"
    )
    await callback.answer()

    try:
        motion_client = MotionControlClient()

        logger.info(f"Creating motion control task...")

        # Создаем задачу
        task_id = await motion_client.create_task(
            image_url=photo_url,
            video_url=video_url,
            prompt="",
            character_orientation="video",
            mode=quality
        )

        if not task_id:
            logger.error(f"Failed to create task")
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return

        logger.info(f"Task created: {task_id}")
        logger.info(f"Waiting for result...")

        # Ожидаем результат (макс 20 минут)
        result_url = await motion_client.wait_for_result(task_id, max_attempts=120, delay=10)

        if result_url:
            if result_url == "MODERATION_ERROR":
                logger.warning(f"Moderation error for task {task_id}")

                await processing_msg.edit_text(
                    "😔 Упс! Не получилось создать видео\n\n"
                    "Система безопасности заблокировала запрос.\n\n"
                    "Частые причины:\n"
                    "• На фото известная личность\n"
                    "• В видео неподходящий контент\n\n"
                    "💡 Совет: используйте обычные фотографии и нейтральные видео\n\n"
                    "💛 Не переживайте, баланс не пострадал"
                )
            elif result_url == "FORMAT_ERROR":
                logger.warning(f"Format error for task {task_id}")

                await processing_msg.edit_text(
                    "😅 Упс, Kling не поддерживает формат этого видео и поэтому не может его обработать 😅\n\n"
                    "Можешь скинуть другое?"
                )
            else:
                logger.info(f"✅ Generation successful! Result URL: {result_url}")

                # Успешная генерация - списываем средства
                new_balance = balance - required_amount
                db.update_user_balance(user_id, new_balance)

                logger.info(f"💰 Charged {required_amount}₽. New balance: {new_balance}₽")

                # Отправляем видео
                try:
                    logger.info(f"Sending video to user...")

                    video_file = URLInputFile(result_url)
                    await bot.send_video(
                        chat_id=callback.message.chat.id,
                        video=video_file,
                        caption="✨ Ваше видео с управлением движением готово!",
                        request_timeout=180
                    )
                    await processing_msg.delete()

                    logger.info(f"✅ Video sent successfully!")

                    db.save_generation(user_id, "motion_control", result_url, "")

                    logger.info(f"💾 Generation saved to database")

                except Exception as e:
                    logger.error(f"❌ Error sending video: {e}")
                    await processing_msg.edit_text(
                        "❌ Не удалось отправить видео. Попробуйте позже."
                    )

            await callback.message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_video_menu_keyboard(),
                parse_mode="HTML"
            )
        else:
            logger.error(f"❌ Result URL is None")

            await processing_msg.edit_text(
                "😔 Что-то пошло не так\n\n"
                "Не удалось создать видео. Возможные причины:\n"
                "• Превышено время ожидания\n"
                "• Временные проблемы с сервером\n\n"
                "💡 Попробуйте ещё раз через пару минут\n\n"
                "💛 Не переживайте, баланс не пострадал"
            )

            await callback.message.answer(
                TEXTS['welcome_message'],
                reply_markup=get_video_menu_keyboard(),
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()

        await processing_msg.edit_text(
            "❌ Произошла ошибка при генерации. Попробуйте позже."
        )

    await state.clear()


