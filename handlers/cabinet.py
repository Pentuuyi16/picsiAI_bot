from aiogram import Router, F
from aiogram.types import CallbackQuery, URLInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.inline import get_cabinet_keyboard, get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "personal_cabinet")
async def personal_cabinet_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Личный кабинет'"""
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
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_cabinet_keyboard()
    )
    
    await callback.answer()


@router.callback_query(F.data == "my_photos")
async def my_photos_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Мои фото'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    db = Database()
    
    photos = db.get_user_photos(user_id)
    
    if not photos:
        await callback.answer("У вас пока нет оживлённых фото", show_alert=True)
        return
    
    await callback.message.answer(f"Ваши оживлённые фотографии ({len(photos)})")
    
    for photo_url, prompt, created_at in photos:
        try:
            video_file = URLInputFile(photo_url)
            await callback.bot.send_video(
                chat_id=callback.message.chat.id,
                video=video_file
            )
        except Exception as e:
            print(f"Ошибка отправки фото: {e}")
    
    await callback.answer()


@router.callback_query(F.data == "my_videos")
async def my_videos_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Мои видео'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    db = Database()
    
    videos = db.get_user_videos(user_id)
    
    if not videos:
        await callback.answer("У вас пока нет сгенерированных видео", show_alert=True)
        return
    
    await callback.message.answer(f"Ваши видео ({len(videos)})")
    
    for video_url, prompt, created_at in videos:
        try:
            video_file = URLInputFile(video_url)
            await callback.bot.send_video(
                chat_id=callback.message.chat.id,
                video=video_file
            )
        except Exception as e:
            print(f"Ошибка отправки видео: {e}")
    
    await callback.answer()


@router.callback_query(F.data == "my_edited_images")
async def my_edited_images_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Мои отредактированные изображения'"""
    from database.database import Database
    
    user_id = callback.from_user.id
    db = Database()
    
    images = db.get_user_edited_images(user_id)
    
    if not images:
        await callback.answer("У вас пока нет отредактированных изображений", show_alert=True)
        return
    
    await callback.message.answer(f"Ваши отредактированные изображения ({len(images)})")
    
    for image_url, prompt, created_at in images:
        try:
            image_file = URLInputFile(image_url)
            await callback.bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=image_file
            )
        except Exception as e:
            print(f"Ошибка отправки изображения: {e}")
    
    await callback.answer()


@router.callback_query(F.data == "top_up_balance_cabinet")
async def top_up_balance_cabinet_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Пополнить баланс' из личного кабинета"""
    from keyboards.inline import get_balance_amounts_keyboard
    
    # Сохраняем контекст
    from handlers.payment import user_balance_context
    user_balance_context[callback.from_user.id] = "personal_cabinet"
    
    await callback.message.answer(
        "💰 Выберите сумму для пополнения:",
        reply_markup=get_balance_amounts_keyboard(back_to="personal_cabinet")
    )
    await callback.answer()


@router.callback_query(F.data == "documents")
async def documents_handler(callback: CallbackQuery):
    """Обработчик кнопки 'Документы'"""
    text = (
        "Начав работу с ботом, вы подтверждаете согласие с документами, указанными ниже ⤵️\n\n"
        "📌 <a href='https://docs.google.com/document/d/1a5VvZ6Y9O6dNzEks0FeWaV-ch6u0x_uIj1Tl3fCKkKI/edit?tab=t.0'>Политика конфиденциальности</a>\n\n"
        "📌 <a href='https://docs.google.com/document/d/1X74L-4BtUrrxbuHUIPlw1QfrNV8_c6L92YD0h_Srpug/edit?tab=t.0'>Согласие на обработку персональных данных</a>\n\n"
        "📌 <a href='https://docs.google.com/document/d/1ik6H8r3mc2vLQWqce_Yc9evrd5shACcdr3um8jOYV6o/edit?tab=t.0#heading=h.448sylidj6gd'>Договор оферты</a>"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="personal_cabinet")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()