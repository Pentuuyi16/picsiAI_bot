from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_agreement_keyboard() -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру для подтверждения согласия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_agreement")]
        ]
    )
    return keyboard


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт главное меню с инлайн-кнопками"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Оживление фото", callback_data="photo_animation"),
                InlineKeyboardButton(text="🎬 Создание видео", callback_data="video_generation")
            ],
            [InlineKeyboardButton(text="🎨 Редактирование изображений", callback_data="image_editing")],
            [InlineKeyboardButton(text="💎 Реферальная система", callback_data="referral_system")],
            [InlineKeyboardButton(text="💬 Написать в поддержку", callback_data="support")],
            [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_cabinet")]
        ]
    )
    return keyboard


def get_photo_animation_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для раздела 'Оживление фото'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📸 Оживить фото", callback_data="animate_photo")],
            [InlineKeyboardButton(text="Видео-инструкция", callback_data="video_instruction")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_photo")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def get_video_generation_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для раздела 'Создание видео'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📹 Сгенерировать видео", callback_data="generate_video")],
            [InlineKeyboardButton(text="Видео-инструкция", callback_data="video_instruction_generation")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_video")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def get_video_format_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора формата генерации видео"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Быстрая (с фото)", callback_data="video_fast_photo")],
            [InlineKeyboardButton(text="Высокое качество (с фото)", callback_data="video_quality_photo")],
            [InlineKeyboardButton(text="Быстрая (по тексту)", callback_data="video_fast_prompt")],
            [InlineKeyboardButton(text="Высокое качество (по тексту)", callback_data="video_quality_prompt")],
            
            
        ]
    )
    return keyboard


def get_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора соотношения сторон"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="9:16 Вертикальное", callback_data="aspect_9_16")],
            [InlineKeyboardButton(text="16:9 Горизонтальное", callback_data="aspect_16_9")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_video_format")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def get_balance_amounts_keyboard(back_to: str = "photo_animation") -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с суммами для пополнения"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="80₽", callback_data="amount_80"),
                InlineKeyboardButton(text="160₽", callback_data="amount_160"),
                InlineKeyboardButton(text="320₽", callback_data="amount_320"),
                InlineKeyboardButton(text="640₽", callback_data="amount_640")
            ],
            [InlineKeyboardButton(text="Назад", callback_data=f"back_to_{back_to}")]
        ]
    )
    return keyboard


def get_payment_keyboard(amount: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Оплатить {amount}₽", callback_data=f"pay_{amount}")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_amounts")]
        ]
    )
    return keyboard

def get_image_editing_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для раздела 'Редактирование изображений'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎨 Отредактировать фото", callback_data="edit_photo")],
            [InlineKeyboardButton(text="Видео-инструкция", callback_data="video_instruction_editing")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_editing")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_edit_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора соотношения сторон при редактировании"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="9:16 Вертикальное", callback_data="edit_aspect_9_16")],
            [InlineKeyboardButton(text="16:9 Горизонтальное", callback_data="edit_aspect_16_9")],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_image_editing_menu")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_photo_quality_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора качества фото"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1K", callback_data="quality_1k"),
                InlineKeyboardButton(text="2K", callback_data="quality_2k"),
                InlineKeyboardButton(text="4K", callback_data="quality_4k")
            ],
            [InlineKeyboardButton(text="Назад", callback_data="back_to_edit_aspect")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_payment_methods_keyboard(back_to: str = "main_menu") -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора способа оплаты"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплата картой", callback_data=f"pay_card_{back_to}")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_start_action_keyboard(action_type: str) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для подтверждения начала действия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data=f"start_action_{action_type}")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard 

def get_cabinet_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для личного кабинета"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Мои фото", callback_data="my_photos"),
                InlineKeyboardButton(text="📹 Мои видео", callback_data="my_videos")
            ],
            [InlineKeyboardButton(text="🎨 Мои отредактированные изображения", callback_data="my_edited_images")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_cabinet")],
            [InlineKeyboardButton(text="📑 Документы", callback_data="documents")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard