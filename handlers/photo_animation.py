from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, URLInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards.inline import get_photo_animation_keyboard, get_main_menu_keyboard
from utils.api_client import KieApiClient
from utils.texts import TEXTS
import os

router = Router()
api_client = KieApiClient()

# File ID вашего видео-примера
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAMsaWFDoPpwOC_2il_QcVDQMEwVq4YAAm2WAAImVwlLwcjD6DkwMzE4BA"


class PhotoAnimationStates(StatesGroup):
    """Состояния для процесса оживления фото"""
    waiting_for_photo = State()
    waiting_for_prompt = State()


@router.callback_query(F.data == "photo_animation")
async def photo_animation_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Оживление фото'"""
    from database.database import Database
    
    db = Database()
    user = db.get_user(callback.from_user.id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "✨ <b>Наш Бот превращает старые фото в живые истории!</b>\n\n"
        "<b>Как оживить фото?</b>\n\n"
        "1️⃣ <b><i>Загрузите фото в бот</i></b> — любое, от старых снимков до современных портретов.\n"
        "2️⃣ <b><i>Опишите</i></b>, что хотите видеть в анимации — движение, эмоцию, действие.\n"
        "3️⃣ <b><i>Подождите пару минут</i></b> — и получите своё уникальное видео, созданное специально для вас!\n\n"
        "Ваши воспоминания <b><i>заслуживают</i></b> нового дыхания 💫\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
        f"📹 Оживление 1 фото = 40₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    await callback.message.delete()
    
    # Отправляем новое с видео
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_photo_animation_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data == "animate_photo")
async def animate_photo_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Оживить фото'"""
    # Путь к примеру фото (положите файл пример.jpg в корень проекта)
    example_photo_path = "example_photo.jpg"
    
    # Проверяем существует ли файл
    if os.path.exists(example_photo_path):
        photo = FSInputFile(example_photo_path)
        await callback.message.answer_photo(
            photo=photo,
            caption="<b>Пример ⤴️</b>\n\nПришлите <b><i>фотографию</i></b>, которую хотите оживить ✨🎬",
            parse_mode="HTML"
        )
    else:
        # Если файла нет, отправляем просто текст
        await callback.message.answer(
            "<b>Пример ⤴️</b>\n\n"
            "Пришлите <b><i>фотографию</i></b>, которую хотите оживить ✨🎬",
            parse_mode="HTML"
        )
    
    await state.set_state(PhotoAnimationStates.waiting_for_photo)
    await callback.answer()


@router.message(PhotoAnimationStates.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения фотографии"""
    # Сохраняем file_id самого большого размера фото
    photo = message.photo[-1]
    
    # Получаем URL фото
    file = await bot.get_file(photo.file_id)
    file_url = f"https://api.telegram.org/file/bot{bot.token}/{file.file_path}"
    
    await state.update_data(photo_file_id=photo.file_id, photo_url=file_url)
    
    await message.answer(
        "🖼 <b>Опишите, как фотография должна «ожить»</b>\n\n"
        "Расскажите, какие действия выполняют люди на изображении — каждый по отдельности или все вместе\n\n"
        "<b>Примеры действий:</b>\n"
        "- Смотрит в объектив и слегка улыбается, не показывая зубы\n"
        "- Приветственно машет рукой\n"
        "- Аккуратно обнимает другого человека\n"
        "✨ Можно предлагать и другие похожие варианты поведения.\n\n"
        "❗️ <b>Обратите внимание:</b>\n\n"
        "- <b><i>Запросы</i></b> с откровенным или 18+ содержанием не принимаются\n\n"
        "- <b><i>Фотографии в купальнике или нижнем белье допустимы</i></b>, если описание нейтральное, например: «Стоит и позирует перед камерой»",
        parse_mode="HTML"
    )
    await state.set_state(PhotoAnimationStates.waiting_for_prompt)


@router.message(PhotoAnimationStates.waiting_for_photo)
async def process_invalid_photo(message: Message):
    """Обработчик неверного формата (не фото)"""
    await message.answer(
        "⚠️ Пожалуйста, отправьте фотографию."
    )


@router.message(PhotoAnimationStates.waiting_for_prompt, F.text)
async def process_prompt(message: Message, state: FSMContext, bot: Bot):
    """Обработчик получения промпта"""
    from database.database import Database
    from keyboards.inline import get_payment_methods_keyboard
    import json
    
    prompt = message.text
    data = await state.get_data()
    photo_url = data.get('photo_url')
    
    db = Database()
    user = db.get_user(message.from_user.id)
    
    # Проверяем баланс
    balance = user['balance'] if user else 0.00
    required_amount = 40.00  # Стоимость оживления фото
    
    if balance < required_amount:
        # Сохраняем текущее состояние для продолжения после оплаты
        action_data = json.dumps({
            "back_to": "photo_animation",
            "photo_url": photo_url,
            "prompt": prompt
        })
        db.save_pending_action(message.from_user.id, "photo_animation_pending", action_data)
        
        print(f"💾 Сохранено состояние для оживления фото: photo_url={photo_url}, prompt={prompt}")
        
        await message.answer(
            "Похоже, средств сейчас немного не хватает\n\n"
            f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
            f"📸 Оживление 1 фото - 40₽</blockquote>\n\n"
            "Выберите способ оплаты ⤵️",
            parse_mode="HTML",
            reply_markup=get_payment_methods_keyboard(back_to="photo_animation")
        )
        # НЕ очищаем состояние!
        return
    
    # Отправляем сообщение о начале обработки
    processing_msg = await message.answer(
        "⭐ Начинается генерация, совсем скоро пришлем готовое видео"
    )
    
    try:
        # Создаём задачу на оживление фото
        task_id = await api_client.create_task(photo_url, prompt, mode="normal")
        
        if not task_id:
            await processing_msg.edit_text(
                "❌ Произошла ошибка при создании задачи. Попробуйте позже."
            )
            await state.clear()
            return
        
        # Ожидаем завершения задачи
        video_url = await api_client.wait_for_completion(task_id, max_attempts=60, delay=5)
        
        if video_url:
            if video_url == "MODERATION_ERROR":
                # Ошибка модерации - баланс НЕ списывается
                await processing_msg.edit_text(
                    "😔 Упс! Не получилось оживить фотографию\n\n"
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
                
                print(f"🎬 Попытка отправки видео: {video_url}")
                
                # Отправляем видео пользователю
                try:
                    # Способ 1: Пробуем URLInputFile
                    print("📤 Попытка отправки через URLInputFile...")
                    video_file = URLInputFile(video_url)
                    await bot.send_video(
                        chat_id=message.chat.id,
                        video=video_file,
                        caption="✨ Ваше оживлённое фото готово!",
                        request_timeout=300  # Увеличиваем таймаут до 5 минут
                    )
                    print("✅ Видео успешно отправлено через URLInputFile")
                    
                    # Удаляем сообщение о генерации ТОЛЬКО после успешной отправки
                    await processing_msg.delete()
                    # Сохраняем генерацию в БД
                    db.save_generation(message.from_user.id, "photo_animation", video_url, prompt)
                except Exception as e:
                    print(f"❌ Ошибка отправки через URLInputFile: {e}")
                    
                    # Способ 2: Пробуем скачать и отправить как файл
                    try:
                        print("📥 Попытка скачать видео и отправить как файл...")
                        import aiohttp
                        import tempfile
                        
                        async with aiohttp.ClientSession() as session:
                            async with session.get(video_url, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                                if resp.status == 200:
                                    # Создаём временный файл
                                    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                                        tmp_file.write(await resp.read())
                                        tmp_path = tmp_file.name
                                    
                                    print(f"📁 Видео скачано во временный файл: {tmp_path}")
                                    
                                    # Отправляем из файла
                                    video_file = FSInputFile(tmp_path)
                                    await bot.send_video(
                                        chat_id=message.chat.id,
                                        video=video_file,
                                        caption="✨ Ваше оживлённое фото готово!",
                                        request_timeout=300
                                    )
                                    
                                    # Удаляем временный файл
                                    os.unlink(tmp_path)
                                    print("✅ Видео успешно отправлено через файл")
                                    
                                    await processing_msg.delete()
                                else:
                                    print(f"❌ Не удалось скачать видео, status: {resp.status}")
                                    raise Exception(f"HTTP {resp.status}")
                                    
                    except Exception as e2:
                        print(f"❌ Ошибка отправки через файл: {e2}")
                        
                        # Если оба способа не сработали - отправляем ссылку
                        try:
                            await processing_msg.edit_text(
                                f"✨ Ваше оживлённое фото готово!\n\n"
                                f"К сожалению, не удалось отправить видео напрямую, но вы можете скачать его по ссылке:\n\n"
                                f"{video_url}\n\n"
                                f"⚠️ Ссылка временная, сохраните видео в течение 24 часов!"
                            )
                        except:
                            await message.answer(
                                f"✨ Ваше оживлённое фото готово!\n\n"
                                f"Скачайте видео по ссылке:\n{video_url}\n\n"
                                f"⚠️ Ссылка временная, сохраните видео в течение 24 часов!"
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
        print(f"Ошибка при обработке: {e}")
        await processing_msg.edit_text(
            "❌ Произошла ошибка при обработке. Попробуйте позже."
        )
    
    # Очищаем состояние
    await state.clear()


@router.message(PhotoAnimationStates.waiting_for_prompt)
async def process_invalid_prompt(message: Message):
    """Обработчик неверного формата промпта"""
    await message.answer(
        "⚠️ Пожалуйста, отправьте текстовое описание анимации."
    )


@router.callback_query(F.data == "video_instruction")
async def video_instruction_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Видео-инструкция'"""
    await callback.message.answer(
        "📹 Видео-инструкция\n\n"
        "Здесь будет видео-инструкция по использованию бота."
    )
    await callback.answer()