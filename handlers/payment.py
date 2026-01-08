from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
    get_main_menu_keyboard
)

router = Router()

# File ID видео-примера
EXAMPLE_VIDEO_FILE_ID = "BAACAgIAAxkBAAIBIGlW5FgkfH7gptZL7Da37J-Ysa9xAAJRjwACUHW4SlLZdBj5RB-uOAQ"

# Словарь для хранения информации о том, откуда пользователь пришёл на пополнение
user_balance_context = {}


@router.callback_query(F.data == "top_up_balance_photo")
async def top_up_balance_photo_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из раздела 'Оживление фото'"""
    user_balance_context[callback.from_user.id] = "photo_animation"
    
    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="photo_animation")
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
        f"🎨 Редактирование 1 фото = 25₽</blockquote>"
    )
    
    # Удаляем старое сообщение
    try:
        await callback.message.delete()
    except:
        pass
    
    # Отправляем новое с видео
    from handlers.image_editing import EXAMPLE_VIDEO_FILE_ID
    await callback.message.answer_video(
        video=EXAMPLE_VIDEO_FILE_ID,
        caption=text,
        parse_mode="HTML",
        reply_markup=get_image_editing_keyboard()
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
    
    from keyboards.inline import get_cabinet_keyboard
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cabinet_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("amount_"))
async def select_amount_handler(callback: CallbackQuery):
    """Обработчик выбора суммы пополнения"""
    amount = int(callback.data.split("_")[1])
    
    text = (
        f"💳 Сумма к оплате: {amount}₽\n\n"
        f"Как только оплата пройдёт успешно, сумма мгновенно и автоматически появится на вашем балансе ✨"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_keyboard(amount)
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_amounts")
async def back_to_amounts_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Назад' из страницы оплаты к выбору суммы"""
    user_id = callback.from_user.id
    back_to = user_balance_context.get(user_id, "personal_cabinet")  # По умолчанию личный кабинет
    
    await callback.message.edit_text(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to=back_to)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_") & ~F.data.startswith("pay_card_"))
async def process_payment_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Оплатить'"""
    from utils.yookassa_client import YooKassaClient
    
    amount = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    
    # Получаем контекст (откуда пришёл пользователь)
    back_to = user_balance_context.get(user_id, "main_menu")
    
    # Создаём платёж через YooKassa
    yookassa = YooKassaClient()
    payment_data = await yookassa.create_payment(
        amount=amount,
        description=f"Пополнение баланса на {amount}₽",
        user_id=user_id
    )
    
    if payment_data and payment_data.get("confirmation_url"):
        # Создаём инлайн-кнопку для оплаты
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_data["confirmation_url"])],
                [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_payment_{payment_data['payment_id']}")],
                [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
            ]
        )
        
        await callback.message.edit_text(
            f"💳 Счёт на оплату {amount}₽ создан!\n\n"
            f"Нажмите кнопку «Оплатить» для перехода на страницу оплаты.\n"
            f"После успешной оплаты нажмите «Я оплатил».",
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Не удалось создать счёт на оплату. Попробуйте позже."
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_handler(callback: CallbackQuery):
    """Обработчик проверки платежа"""
    from utils.yookassa_client import YooKassaClient
    from database.database import Database
    import json
    
    payment_id = callback.data.replace("check_payment_", "")
    user_id = callback.from_user.id
    
    # Проверяем статус платежа
    yookassa = YooKassaClient()
    payment_status = await yookassa.check_payment(payment_id)
    
    if payment_status and payment_status.get("status") == "succeeded" and payment_status.get("paid"):
        # Платёж успешен
        amount = payment_status.get("amount")
        
        # Пополняем баланс
        db = Database()
        
        # Проверяем существует ли пользователь, если нет - создаём
        user = db.get_user(user_id)
        if not user:
            # Создаём пользователя если его нет
            db.add_user(user_id)
            user = db.get_user(user_id)
        
        # Пополняем баланс
        db.add_to_balance(user_id, amount)

        # Начисляем реферальный бонус
        user = db.get_user(user_id)
        if user and user.get('referrer_id'):
            referrer_id = user['referrer_id']
            referral_amount = amount * 0.15  # 15%
    
            # Начисляем сразу на основной баланс
            db.add_to_balance(referrer_id, referral_amount)
            db.add_referral_earning(referrer_id, user_id, referral_amount, amount)
    
            print(f"💎 Начислено {referral_amount}₽ рефералу {referrer_id} на основной баланс")
    
            # Уведомляем реферера
            try:
                referrer_user = db.get_user(referrer_id)
                new_balance = referrer_user['balance']
                await callback.bot.send_message(
                    referrer_id,
                    f"💎 Ваш друг пополнил баланс!\n\n"
                    f"Вам начислено: {referral_amount:.2f}₽\n"
                    f"Ваш баланс: {new_balance:.2f}₽"
            )
            except Exception as e:
                print(f"Не удалось отправить уведомление реферу: {e}")
        
        # Получаем обновлённый баланс СРАЗУ ПОСЛЕ пополнения
        user = db.get_user(user_id)
        new_balance = user['balance'] if user else amount
        
        print(f"✅ Баланс пополнен! User ID: {user_id}, Amount: {amount}, New Balance: {new_balance}")
        
        # Ищем ЛЮБОЙ pending action (не только payment_info)
        pending = db.get_pending_action(user_id)
        
        print(f"🔍 Найден pending action: {pending}")
        
        # Если есть pending action для генерации - показываем подтверждение
        if pending and pending['action_type'] in ["image_editing_pending", "photo_animation_pending", "video_generation_pending"]:
            action_data = json.loads(pending['action_data'])
            back_to = action_data.get("back_to", "main_menu")
            
            print(f"📋 Pending action type: {pending['action_type']}, back_to: {back_to}")
            
            # Определяем текст в зависимости от раздела
            if back_to == "image_editing" or pending['action_type'] == "image_editing_pending":
                text = (
                    "🎨 Мы готовы начинать редактирование фото\n\n"
                    "Стартуем?\n\n"
                    f"<blockquote>💰 Ваш баланс: {new_balance:.2f} ₽\n"
                    f"🎨 Редактирование 1 фото = 25₽</blockquote>"
                )
            elif back_to == "photo_animation" or pending['action_type'] == "photo_animation_pending":
                text = (
                    "📸 Мы готовы начинать оживление фото\n\n"
                    "Стартуем?\n\n"
                    f"<blockquote>💰 Ваш баланс: {new_balance:.2f} ₽\n"
                    f"📸 Оживление 1 фото = 40₽</blockquote>"
                )
            elif back_to == "video_generation" or pending['action_type'] == "video_generation_pending":
                text = (
                    "📹 Мы готовы начинать генерацию видео\n\n"
                    "Стартуем?\n\n"
                    f"<blockquote>💰 Ваш баланс: {new_balance:.2f} ₽\n"
                    f"📹 Генерация 1 видео = 65₽\n"
                    f"📹 Генерация 1 видео (высокое качество) = 115₽</blockquote>"
                )
            else:
                text = f"✅ Баланс успешно пополнен на {amount}₽!\n\nВаш текущий баланс: {new_balance:.2f} ₽"
            
            await callback.message.edit_text(
                text,
                parse_mode="HTML",
                reply_markup=get_start_action_keyboard(back_to if back_to != "main_menu" else "image_editing")
            )
        else:
            # Нет pending action - просто показываем успешное пополнение
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
                ]
            )
            
            await callback.message.edit_text(
                f"🎉 Баланс успешно пополнен на {amount}₽!\n\n"
                f"<blockquote>💰 Ваш баланс: {new_balance:.2f} ₽</blockquote>",
                parse_mode="HTML",
                reply_markup=keyboard
            )
    elif payment_status and payment_status.get("status") == "pending":
        await callback.answer(
            "⏳ Платёж ещё обрабатывается. Пожалуйста, подождите немного.",
            show_alert=True
        )
    else:
        await callback.answer(
            "❌ Платёж не найден или не был выполнен.",
            show_alert=True
        )


@router.callback_query(F.data.startswith("start_action_"))
async def start_action_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки 'Да' - продолжение генерации после оплаты"""
    from database.database import Database
    from utils.api_client import KieApiClient
    from utils.veo_api_client import VeoApiClient
    from utils.image_edit_client import ImageEditClient
    from utils.texts import TEXTS
    from aiogram.types import URLInputFile
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    user_id = callback.from_user.id
    
    # ВАЖНО: Сначала отвечаем на callback, чтобы избежать timeout
    await callback.answer()
    
    db = Database()
    pending = db.get_pending_action(user_id)
    
    if not pending:
        await callback.message.answer("❌ Действие не найдено")
        return
    
    # Парсим данные действия
    action_data = json.loads(pending['action_data'])
    action_type = pending['action_type']
    
    # Очищаем pending action
    db.clear_pending_action(user_id)
    
    # Получаем текущий баланс
    user = db.get_user(user_id)
    balance = user['balance']
    
    await callback.message.delete()
    
    # Продолжаем генерацию в зависимости от типа действия
    if action_type == "image_editing_pending":
        # Редактирование изображения
        state_data = action_data.get("state_data", {})
        prompt = action_data.get("prompt")
        
        aspect_ratio = state_data.get("edit_aspect_ratio", "1:1")
        resolution = state_data.get("edit_quality", "1K")
        photos = state_data.get("edit_photos", [])
        
        required_amount = 25.00
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для редактирования")
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
                        # Списываем средства
                        new_balance = balance - required_amount
                        db.update_user_balance(user_id, new_balance)
                        
                        # Отправляем изображение
                        try:
                            image_file = URLInputFile(image_url)
                            await callback.bot.send_photo(
                                chat_id=callback.message.chat.id,
                                photo=image_file,
                                caption="✨ Ваше изображение готово!",
                                request_timeout=180
                            )
                            await processing_msg.delete()
                            # Сохраняем генерацию в БД
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
            logger.error(f"Ошибка: {e}")
            try:
                await processing_msg.edit_text("❌ Произошла ошибка при редактировании.")
            except:
                await callback.message.answer("❌ Произошла ошибка при редактировании.")
    
    elif action_type == "photo_animation_pending":
        # Оживление фото
        photo_url = action_data.get("photo_url")
        prompt = action_data.get("prompt")
        
        print(f"📸 Начинаем оживление: photo_url={photo_url}, prompt={prompt}")
        
        required_amount = 40.00
        
        if balance < required_amount:
            await callback.message.answer("❌ Недостаточно средств для оживления фото")
            return
        
        processing_msg = await callback.message.answer(
            "⭐ Начинается генерация, совсем скоро пришлем готовое видео"
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