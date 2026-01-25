from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_agreement_keyboard() -> InlineKeyboardMarkup:
    """Создаёт инлайн-клавиатуру для подтверждения согласия"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принимаю", callback_data="confirm_agreement")]
        ]
    )
    return keyboard


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт главное меню с инлайн-кнопками"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔥 Тренды", callback_data="trends")],
            [
                InlineKeyboardButton(text="🖼️ Изображения", callback_data="images_menu"),
                InlineKeyboardButton(text="🎬 Видео-контент", callback_data="video_menu")
            ],
            [InlineKeyboardButton(text="Написать в поддержку", callback_data="support")],
            [InlineKeyboardButton(text="Личный кабинет", callback_data="personal_cabinet")]
        ]
    )
    return keyboard


def get_images_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт подменю 'Изображения'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✨ Создать фото", callback_data="create_photo")],
            [InlineKeyboardButton(text="🎨 Отредактировать фото", callback_data="image_editing")],
            [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations")],
            [InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard


def get_video_menu_keyboard() -> InlineKeyboardMarkup:
    """Создаёт подменю 'Видео-контент'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕺 Управление движением", callback_data="motion_control")],
            [
                InlineKeyboardButton(text="📸 Оживить фото", callback_data="photo_animation"),
                InlineKeyboardButton(text="🎥 Создать видео", callback_data="video_generation")
            ],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_video_menu")],
            [InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")]
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
            [InlineKeyboardButton(text="← Назад", callback_data="video_menu")]
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
            [InlineKeyboardButton(text="← Назад", callback_data="video_menu")]
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

def get_edit_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора соотношения сторон при редактировании"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="16:9 Горизонтальное", callback_data="edit_aspect_16_9")],
            [InlineKeyboardButton(text="9:16 Вертикальное", callback_data="edit_aspect_9_16")],
            [InlineKeyboardButton(text="1:1 Квадратное", callback_data="edit_aspect_1_1")],
            [InlineKeyboardButton(text="← Назад", callback_data="images_menu")]
        ]
    )
    return keyboard

def get_generation_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора соотношения сторон при генерации"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="16:9 Горизонтальное", callback_data="generation_aspect_16_9")],
            [InlineKeyboardButton(text="9:16 Вертикальное", callback_data="generation_aspect_9_16")],
            [InlineKeyboardButton(text="1:1 Квадратное", callback_data="generation_aspect_1_1")],
            [InlineKeyboardButton(text="← Назад", callback_data="images_menu")]
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
            [InlineKeyboardButton(text="🕺 Мои управление движением", callback_data="my_motion_videos")],
            [InlineKeyboardButton(text="💎 Реферальная система", callback_data="referral_system")],
            [InlineKeyboardButton(text="Документы", callback_data="documents")],
            [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_motion_control_keyboard():
    """Создаёт клавиатуру для раздела управления движением"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕺 Управлять движением", callback_data="control_motion")],
            [InlineKeyboardButton(text="Видео-инструкция", callback_data="video_instruction_motion")],
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="top_up_balance_motion")],
            [InlineKeyboardButton(text="← Назад", callback_data="video_menu")]
        ]
    )
    return keyboard


def get_motion_quality_keyboard():
    """Создаёт клавиатуру для выбора качества управления движением"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="720p", callback_data="motion_quality_720p"),
                InlineKeyboardButton(text="1080p", callback_data="motion_quality_1080p")
            ],
            [InlineKeyboardButton(text="Назад", callback_data="motion_control")]
        ]
    )
    return keyboard

def get_trends_keyboard(page: int = 1) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для раздела 'Тренды'"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Фотки с макбука", callback_data="trend_macbook"),
                InlineKeyboardButton(text="Именной букет", callback_data="trend_bouquet")
            ],
            [
                InlineKeyboardButton(text="Снежный ангел", callback_data="trend_snow_angel"),
                InlineKeyboardButton(text="Фотка на сноуборде", callback_data="trend_snowboard")
            ],
            [
                InlineKeyboardButton(text="Портрет на стене", callback_data="trend_wall_portrait"),
                InlineKeyboardButton(text="Влюбленный взгляд", callback_data="trend_loving_gaze")
            ],
            [
                InlineKeyboardButton(text="Фотка с мечами", callback_data="trend_swords"),
                InlineKeyboardButton(text="Сердце на здание", callback_data="trend_heart_building")
            ],
            [
                InlineKeyboardButton(text="Фотка в машине", callback_data="trend_car"),
                InlineKeyboardButton(text="Фотка с криком", callback_data="trend_scream")
            ],
            [InlineKeyboardButton(text="Следующая страница →", callback_data="trends_page_2")],
            [InlineKeyboardButton(text="⚡ Купить генерации", callback_data="buy_generations_from_trends")],
            [InlineKeyboardButton(text="← Главное меню", callback_data="main_menu")]
        ]
    )
    return keyboard

def get_trend_aspect_ratio_keyboard() -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора соотношения сторон для трендов"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="16:9 Горизонтальное", callback_data="trend_aspect_16_9")],
            [InlineKeyboardButton(text="9:16 Вертикальное", callback_data="trend_aspect_9_16")],
            [InlineKeyboardButton(text="1:1 Квадратное", callback_data="trend_aspect_1_1")],
            [InlineKeyboardButton(text="Отмена", callback_data="trends")]
        ]
    )
    return keyboard

def get_trend_model_selection_keyboard(generations: int) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру для выбора модели генерации в трендах"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌟 Стандартная", callback_data="trend_model_standard")],
            [InlineKeyboardButton(text="🚀 Профессиональная", callback_data="trend_model_pro")]
        ]
    )
    return keyboard