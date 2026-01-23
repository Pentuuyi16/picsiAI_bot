from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from keyboards.inline import (
    get_balance_amounts_keyboard, 
    get_payment_keyboard, 
    get_photo_animation_keyboard, 
    get_video_generation_keyboard,
    get_image_editing_keyboard,
    get_start_action_keyboard,
    get_edit_aspect_ratio_keyboard,
    get_video_format_keyboard,
    get_main_menu_keyboard,
    get_cabinet_keyboard,
    get_motion_control_keyboard
)
import aiohttp
from PIL import Image
from io import BytesIO

router = Router()

# File ID видео-примера
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAIBIGlW5FgkfH7gptZL7Da37J-Ysa9xAAJRjwACUHW4SlLZdBj5RB-uOAQ"

# Словарь для хранения информации о том, откуда пользователь пришёл на пополнение
user_balance_context = {}


async def compress_image(image_url: str, max_size_mb: float = 9.0, quality: int = 85) -> BufferedInputFile:
    """
    Скачивает и сжимает изображение для отправки в Telegram
    
    Args:
        image_url: URL изображения
        max_size_mb: Максимальный размер в МБ
        quality: Качество JPEG (1-100)
    
    Returns:
        BufferedInputFile для отправки в Telegram
    """
    print(f"🔧 Начинаем сжатие изображения...")
    print(f"   URL: {image_url}")
    print(f"   Max size: {max_size_mb} MB")
    
    # Скачиваем изображение
    async with aiohttp.ClientSession() as session:
        async with session.get(image_url) as response:
            image_data = await response.read()
            original_size_mb = len(image_data) / (1024 * 1024)
            print(f"📦 Скачано: {original_size_mb:.2f} MB")
    
    # Открываем изображение
    img = Image.open(BytesIO(image_data))
    print(f"🖼️ Размер: {img.size[0]}x{img.size[1]}, режим: {img.mode}")
    
    # Конвертируем в RGB если нужно
    if img.mode in ('RGBA', 'P', 'LA'):
        print(f"🔄 Конвертируем {img.mode} → RGB")
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    
    # Сжимаем
    output = BytesIO()
    current_quality = quality
    
    while current_quality > 20:
        output.seek(0)
        output.truncate()
        
        img.save(output, format='JPEG', quality=current_quality, optimize=True)
        size_mb = output.tell() / (1024 * 1024)
        
        print(f"   Quality={current_quality}: {size_mb:.2f} MB")
        
        if size_mb <= max_size_mb:
            print(f"✅ Сжато: {original_size_mb:.2f} MB → {size_mb:.2f} MB")
            break
        
        current_quality -= 5
    
    output.seek(0)
    return BufferedInputFile(output.read(), filename="image.jpg")


@router.callback_query(F.data == "top_up_balance_photo")
async def top_up_balance_photo_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из раздела 'Оживление фото'"""
    user_balance_context[callback.from_user.id] = "photo_animation"
    
    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="photo_animation")
    )
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_video_menu")
async def top_up_balance_video_menu_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из меню видео-контент"""
    user_balance_context[callback.from_user.id] = "video_menu"

    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="video_menu")
    )
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_video")
async def top_up_balance_video_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из раздела 'Создание видео'"""
    user_balance_context[callback.from_user.id] = "video_generation"

    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="video_generation")
    )
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_editing")
async def top_up_balance_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из раздела 'Редактирование изображений'"""
    user_balance_context[callback.from_user.id] = "image_editing"
    
    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="image_editing")
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_card_"))
async def pay_card_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Оплата картой'"""
    # Извлекаем откуда пришёл пользователь
    back_to = callback.data.replace("pay_card_", "")
    
    # Сохраняем контекст
    user_balance_context[callback.from_user.id] = back_to
    
    await callback.message.edit_text(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to=back_to)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_photo_animation")
async def back_to_photo_animation_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в раздел оживления фото"""
    from database.database import Database
    from keyboards.inline import get_photo_animation_keyboard
    
    user_id = callback.from_user.id
    
    # Получаем баланс из БД
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "<b>✨ Наш Бот превращает старые фото в живые истории!</b>\n\n"
        "<b>Как оживить фото?</b>\n\n"
        "1️⃣ <b><i>Загрузите фото в бот</i></b> — любое, от старых снимков до современных портретов.\n"
        "2️⃣ <b><i>Опишите</i></b>, что хотите видеть в анимации — движение, эмоцию, действие.\n"
        "3️⃣ <b><i>Подождите пару минут</i></b> — и получите своё уникальное видео, созданное специально для вас!\n\n"
        "Ваши воспоминания <b><i>заслуживают</i></b> нового дыхания 💫\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽\n"
        f"📹 Оживление 1 фото = 40₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое с видео
    from handlers.photo_animation import EXAMPLE_VIDEO_FILE_ID
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_photo_animation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_video_menu")
async def back_to_video_menu_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в меню видео-контент"""
    from database.database import Database
    from keyboards.inline import get_video_menu_keyboard

    user_id = callback.from_user.id
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00

    text = (
        "<b>🎬 Видео-контент</b>\n\n"
        "Создавайте видеоконтент с помощью ИИ:\n\n"
        "📸 <b>Оживить фото</b> — превратите фотографию в короткое видео\n"
        "🎥 <b>Создать видео</b> — сгенерируйте видео по описанию или фото\n"
        "🕺 <b>Управление движением</b> — добавьте движение на фото (Kling)\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽</blockquote>"
    )

    try:
        await callback.message.delete()
    except:
        pass

    await callback.message.answer(
        text,
        reply_markup=get_video_menu_keyboard(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_video_generation")
async def back_to_video_generation_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в раздел создания видео"""
    from database.database import Database
    from keyboards.inline import get_video_generation_keyboard
    
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
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое с видео
    from handlers.video_generation import EXAMPLE_VIDEO_FILE_ID
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_video_generation_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_image_editing")
async def back_to_image_editing_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в раздел редактирования изображений"""
    from database.database import Database
    from keyboards.inline import get_image_editing_keyboard
    
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
        f"🎨 Редактирование 1 изображения = 15₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое с видео
    from handlers.image_editing import EXAMPLE_VIDEO_FILE_ID
    await callback.bot.send_video(
        chat_id=callback.message.chat.id,
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_image_editing_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_motion_control")
async def back_to_motion_control_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в управление движением"""
    from database.database import Database
    
    user_id = callback.from_user.id
    
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
    
    try:
        await callback.message.delete()
    except:
        pass
    
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_motion_control_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_personal_cabinet")
async def back_to_personal_cabinet_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' - возврат в личный кабинет"""
    from database.database import Database
    
    user_id = callback.from_user.id
    
    # Получаем баланс из БД
    db = Database()
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    text = (
        "<b>✨ Личный кабинет</b>\n\n"
        "В этом разделе собраны все важные инструменты и информация, связанные с вашим профилем.\n\n"
        "<b>📁 Файлы</b>\n"
        "Все ваши готовые и созданные материалы 🔥\n\n"
        "<b>💰 Баланс</b>\n"
        "Пополнение и управление средствами 💳\n\n"
        "<b>📑 Юридическая информация</b>\n"
        "Политика конфиденциальности\n"
        "Согласие на ОПД\n"
        "Договор оферты 🛡️\n\n"
        f"<blockquote>💰 Ваш баланс: {balance:.2f} ₽</blockquote>"
    )
    
    # Редактируем сообщение
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cabinet_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "amount_80")
async def amount_80_handler(callback: CallbackQuery):
    """Обработчик выбора суммы 80₽"""
    from utils.yookassa_client import YooKassaClient
    from database.database import Database
    
    user_id = callback.from_user.id
    amount = 80.00
    
    # Создаём платёж через YooKassa
    yookassa = YooKassaClient()
    payment_data = await yookassa.create_payment(
        amount=amount,
        description=f"Пополнение баланса на {int(amount)}₽",
        user_id=user_id
    )
    
    # Сохраняем платёж в БД
    if payment_data and payment_data.get("payment_id"):
        db = Database()
        db.save_payment(payment_data["payment_id"], user_id, amount)
    
    if payment_data and payment_data.get("confirmation_url"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_data["confirmation_url"])],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            f"<b>Сумма к оплате {int(amount)}₽</b>\n\n"
            f"  ✨ Подтверждение об успешной оплате приходит в течение нескольких минут (в некоторых случаях в течение часа)",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data == "amount_160")
async def amount_160_handler(callback: CallbackQuery):
    """Обработчик выбора суммы 160₽"""
    from utils.yookassa_client import YooKassaClient
    from database.database import Database
    
    user_id = callback.from_user.id
    amount = 160.00
    
    # Создаём платёж через YooKassa
    yookassa = YooKassaClient()
    payment_data = await yookassa.create_payment(
        amount=amount,
        description=f"Пополнение баланса на {int(amount)}₽",
        user_id=user_id
    )
    
    # Сохраняем платёж в БД
    if payment_data and payment_data.get("payment_id"):
        db = Database()
        db.save_payment(payment_data["payment_id"], user_id, amount)
    
    if payment_data and payment_data.get("confirmation_url"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_data["confirmation_url"])],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            f"<b>Сумма к оплате {int(amount)}₽</b>\n\n"
            f"  ✨ Подтверждение об успешной оплате приходит в течение нескольких минут (в некоторых случаях в течение часа)",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data == "amount_320")
async def amount_320_handler(callback: CallbackQuery):
    """Обработчик выбора суммы 320₽"""
    from utils.yookassa_client import YooKassaClient
    from database.database import Database
    
    user_id = callback.from_user.id
    amount = 320.00
    
    # Создаём платёж через YooKassa
    yookassa = YooKassaClient()
    payment_data = await yookassa.create_payment(
        amount=amount,
        description=f"Пополнение баланса на {int(amount)}₽",
        user_id=user_id
    )
    
    # Сохраняем платёж в БД
    if payment_data and payment_data.get("payment_id"):
        db = Database()
        db.save_payment(payment_data["payment_id"], user_id, amount)
    
    if payment_data and payment_data.get("confirmation_url"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_data["confirmation_url"])],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            f"<b>Сумма к оплате {int(amount)}₽</b>\n\n"
            f"  ✨ Подтверждение об успешной оплате приходит в течение нескольких минут (в некоторых случаях в течение часа)",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data == "amount_640")
async def amount_640_handler(callback: CallbackQuery):
    """Обработчик выбора суммы 640₽"""
    from utils.yookassa_client import YooKassaClient
    from database.database import Database
    
    user_id = callback.from_user.id
    amount = 640.00
    
    # Создаём платёж через YooKassa
    yookassa = YooKassaClient()
    payment_data = await yookassa.create_payment(
        amount=amount,
        description=f"Пополнение баланса на {int(amount)}₽",
        user_id=user_id
    )
    
    # Сохраняем платёж в БД
    if payment_data and payment_data.get("payment_id"):
        db = Database()
        db.save_payment(payment_data["payment_id"], user_id, amount)
    
    if payment_data and payment_data.get("confirmation_url"):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Перейти к оплате", url=payment_data["confirmation_url"])],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.answer(
            f"<b>Сумма к оплате {int(amount)}₽</b>\n\n"
            f"  ✨ Подтверждение об успешной оплате приходит в течение нескольких минут (в некоторых случаях в течение часа)",
            parse_mode="HTML",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("start_action_"))
async def start_action_handler(callback: CallbackQuery):
    """Обработчик подтверждения начала действия после оплаты"""
    from database.database import Database
    from utils.texts import TEXTS
    from aiogram.types import URLInputFile
    from utils.api_client import KieApiClient
    from utils.veo_api_client import VeoApiClient
    from utils.image_edit_client import ImageEditClient
    from utils.motion_control_client import MotionControlClient
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    user_id = callback.from_user.id
    action_type = callback.data.replace("start_action_", "")
    
    db = Database()
    
    # Получаем незавершённое действие
    pending = db.get_pending_action(user_id)
    
    if not pending:
        await callback.message.answer("❌ Действие не найдено")
        return
    
    # Получаем баланс
    user = db.get_user(user_id)
    balance = user['balance'] if user else 0.00
    
    # Парсим данные действия
    action_data = json.loads(pending['action_data'])
    
    if action_type == "photo_animation_pending":
        # Оживление фото
        photo_url = action_data.get("photo_url")
        prompt = action_data.get("prompt")
        
        required_amount = 40.00
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для оживления фото")
            return
        
        processing_msg = await callback.message.answer(
            "⭐ Начинается оживление фотографии, совсем скоро пришлем результат"
        )
        
        try:
            # Импортируем api_client из модуля photo_animation
            from handlers.photo_animation import api_client
            
            task_id = await api_client.create_task(photo_url, prompt, mode="normal")
            
            print(f"✅ Task ID создан: {task_id}")
            
            if task_id:
                video_url = await api_client.wait_for_completion(task_id, max_attempts=60, delay=5)
                
                print(f"🎬 Video URL: {video_url}")
                
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
                        db.update_user_balance(user_id, new_balance)
                        
                        print(f"💰 Списано {required_amount}₽, новый баланс: {new_balance}₽")
                        
                        # Отправляем видео
                        try:
                            video_file = URLInputFile(video_url)
                            await callback.bot.send_video(
                                chat_id=callback.message.chat.id,
                                video=video_file,
                                caption="✨ Ваше оживлённое фото готово!",
                                request_timeout=180
                            )
                            await processing_msg.delete()
                            print("✅ Видео успешно отправлено")

                            db.save_generation(user_id, "photo_animation", video_url, prompt)
                        except Exception as e:
                            logger.error(f"Ошибка отправки видео: {e}")
                            await processing_msg.edit_text(
                                "❌ Не удалось отправить видео. Попробуйте позже."
                            )
                    
                    await callback.message.answer(
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
                    
                    await callback.message.answer(
                        TEXTS['welcome_message'],
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="HTML"
                    )
            else:
                await processing_msg.edit_text("❌ Не удалось создать задачу.")
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            try:
                await processing_msg.edit_text("❌ Произошла ошибка при генерации.")
            except:
                await callback.message.answer("❌ Произошла ошибка при генерации.")
    
    elif action_type == "video_generation_pending":
        # Генерация видео
        state_data = action_data.get("state_data", {})
        prompt = action_data.get("prompt")
        
        veo_model = state_data.get("veo_model", "veo3_fast")
        aspect_ratio = state_data.get("aspect_ratio", "16:9")
        photos = state_data.get("photos", [])
        
        required_amount = 65.00 if veo_model == "veo3_fast" else 115.00
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для генерации видео")
            return
        
        processing_msg = await callback.message.answer(
            "⭐ Начинается генерация видео, совсем скоро пришлем результат"
        )
        
        try:
            veo_client = VeoApiClient()
            
            if photos:
                task_id = await veo_client.generate_video(
                    prompt=prompt,
                    model=veo_model,
                    aspect_ratio=aspect_ratio,
                    image_urls=photos
                )
            else:
                task_id = await veo_client.generate_video(
                    prompt=prompt,
                    model=veo_model,
                    aspect_ratio=aspect_ratio
                )
            
            if task_id:
                video_url = await veo_client.wait_for_video(task_id, max_attempts=180, delay=10)
                
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
                        db.update_user_balance(user_id, new_balance)
                        
                        # Отправляем видео
                        try:
                            video_file = URLInputFile(video_url)
                            await callback.bot.send_video(
                                chat_id=callback.message.chat.id,
                                video=video_file,
                                caption="✨ Ваше видео готово!",
                                request_timeout=180
                            )
                            await processing_msg.delete()
                            print("✅ Видео успешно отправлено")
                            
                            db.save_generation(user_id, "video_generation", video_url, prompt)
                        except Exception as e:
                            logger.error(f"Ошибка отправки видео: {e}")
                            await processing_msg.edit_text(
                                "❌ Не удалось отправить видео. Попробуйте позже."
                            )
                    
                    await callback.message.answer(
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
                    
                    await callback.message.answer(
                        TEXTS['welcome_message'],
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="HTML"
                    )
            else:
                await processing_msg.edit_text("❌ Не удалось создать задачу.")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            try:
                await processing_msg.edit_text("❌ Произошла ошибка при генерации.")
            except:
                await callback.message.answer("❌ Произошла ошибка при генерации.")
    
    elif action_type == "image_editing_pending":
        # Редактирование изображения
        state_data = action_data.get("state_data", {})
        prompt = action_data.get("prompt")
        
        aspect_ratio = state_data.get("edit_aspect_ratio", "1:1")
        resolution = state_data.get("edit_quality", "1K")
        photos = state_data.get("edit_photos", [])
        
        required_amount = 15.00
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для редактирования изображения")
            return
        
        processing_msg = await callback.message.answer(
            "⭐ Начинается редактирование изображения, совсем скоро пришлем результат"
        )
        
        try:
            edit_client = ImageEditClient()
            
            task_id = await edit_client.create_edit_task(
                prompt=prompt,
                image_urls=photos,
                aspect_ratio=aspect_ratio,
                resolution=resolution,
                output_format="png"
            )
            
            if task_id:
                image_url = await edit_client.wait_for_result(task_id, max_attempts=120, delay=5)
                
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
                        db.update_user_balance(user_id, new_balance)
                        
                        # Отправляем изображение
                        try:
                            print(f"\n{'='*70}")
                            print(f"📤 ОТПРАВКА ИЗОБРАЖЕНИЯ")
                            print(f"Image URL: {image_url}")
                            print(f"{'='*70}\n")
                            
                            # Сжимаем изображение
                            compressed_image = await compress_image(image_url, max_size_mb=9.0, quality=85)
                            
                            print(f"📤 Отправляем сжатое изображение...")
                            await callback.bot.send_photo(
                                chat_id=callback.message.chat.id,
                                photo=compressed_image,
                                caption="✨ Ваше изображение готово!",
                                request_timeout=180
                            )
                            print(f"✅ Изображение отправлено!")
                            
                            await processing_msg.delete()
                            
                            db.save_generation(user_id, "image_editing", image_url, prompt)
                        except Exception as e:
                            logger.error(f"Ошибка отправки изображения: {e}")
                            await processing_msg.edit_text(
                                "❌ Не удалось отправить изображение. Попробуйте позже."
                            )
                    
                    await callback.message.answer(
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
                    
                    await callback.message.answer(
                        TEXTS['welcome_message'],
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="HTML"
                    )
            else:
                await processing_msg.edit_text("❌ Не удалось создать задачу.")
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            try:
                await processing_msg.edit_text("❌ Произошла ошибка при редактировании.")
            except:
                await callback.message.answer("❌ Произошла ошибка при редактировании.")
    
    elif action_type == "motion_control_pending":
        # Управление движением
        state_data = action_data.get("state_data", {})
        
        quality = state_data.get("motion_quality", "720p")
        photo_url = state_data.get("motion_photo")
        video_url = state_data.get("motion_video")
        video_duration = state_data.get("video_duration", 5)
        
        # Рассчитываем стоимость
        price_per_second = 5.00 if quality == "720p" else 7.00
        required_amount = price_per_second * video_duration
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для генерации видео")
            return
        
        processing_msg = await callback.message.answer(
            "⭐ Начинается генерация видео с управлением движением, совсем скоро пришлем результат"
        )
        
        try:
            motion_client = MotionControlClient()
            
            task_id = await motion_client.create_task(
                image_url=photo_url,
                video_url=video_url,
                prompt="",
                character_orientation="video",
                mode=quality
            )
            
            if task_id:
                result_url = await motion_client.wait_for_result(task_id, max_attempts=120, delay=10)
                
                if result_url:
                    if result_url == "MODERATION_ERROR":
                        await processing_msg.edit_text(
                            "😔 Упс! Не получилось создать видео\n\n"
                            "Система безопасности заблокировала запрос.\n\n"
                            "💛 Не переживайте, баланс не пострадал"
                        )
                    else:
                        # Успешная генерация - списываем средства
                        new_balance = balance - required_amount
                        db.update_user_balance(user_id, new_balance)
                        
                        # Отправляем видео
                        try:
                            video_file = URLInputFile(result_url)
                            await callback.bot.send_video(
                                chat_id=callback.message.chat.id,
                                video=video_file,
                                caption="✨ Ваше видео с управлением движением готово!",
                                request_timeout=180
                            )
                            await processing_msg.delete()
                            
                            db.save_generation(user_id, "motion_control", result_url, "")
                        except Exception as e:
                            logger.error(f"Ошибка отправки видео: {e}")
                            await processing_msg.edit_text(
                                "❌ Не удалось отправить видео. Попробуйте позже."
                            )
                    
                    await callback.message.answer(
                        TEXTS['welcome_message'],
                        reply_markup=get_main_menu_keyboard(),
                        parse_mode="HTML"
                    )
                else:
                    await processing_msg.edit_text(
                        "😔 Что-то пошло не так. Не переживайте, баланс не пострадал"
                    )
            else:
                await processing_msg.edit_text("❌ Не удалось создать задачу.")
        except Exception as e:
            logger.error(f"Ошибка: {e}", exc_info=True)
            try:
                await processing_msg.edit_text("❌ Произошла ошибка при генерации.")
            except:
                await callback.message.answer("❌ Произошла ошибка при генерации.")
    
    # Очищаем pending action после выполнения
    db.clear_pending_action(user_id)