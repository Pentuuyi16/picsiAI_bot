import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import BotCommand, Message
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, photo_animation, video_generation, payment, image_editing, referral, cabinet, support, motion_control, generation_purchase,image_generation
from handlers.trends import router as trends_router
from webhook_server import start_webhook_server

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# ВРЕМЕННЫЙ ОБРАБОТЧИК ДЛЯ ПОЛУЧЕНИЯ FILE_ID
async def get_file_id_handler(message: Message):
    """Временный обработчик для получения file_id фото и видео"""
    
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "PHOTO"
    elif message.video:
        file_id = message.video.file_id
        file_type = "VIDEO"
    else:
        return
    
    await message.answer(
        f"<b>📎 {file_type} FILE_ID:</b>\n\n"
        f"<code>{file_id}</code>\n\n"
        f"<i>Скопируйте этот ID для использования в коде</i>",
        parse_mode="HTML"
    )
    
    print(f"\n{'='*70}")
    print(f"📎 {file_type} FILE_ID")
    print(f"{'='*70}")
    print(f"{file_id}")
    print(f"{'='*70}\n")


async def main():
    """Главная функция запуска бота"""
    # Создаём бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # РЕГИСТРИРУЕМ ВРЕМЕННЫЙ ОБРАБОТЧИК
    dp.message.register(get_file_id_handler, F.photo | F.video)
    
    # Настраиваем команды бота (меню)
    commands = [
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="pay", description="Пополнить счёт"),
        BotCommand(command="lk", description="Личный кабинет"),
        BotCommand(command="help", description="Поддержка")
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды бота настроены")
    
    # Подключаем роутеры из handlers
    dp.include_router(start.router)
    dp.include_router(motion_control.router)
    dp.include_router(photo_animation.router)
    dp.include_router(video_generation.router)
    dp.include_router(image_generation.router)  # Должен быть перед image_editing!
    dp.include_router(image_editing.router) 
    dp.include_router(payment.router)
    dp.include_router(referral.router)
    dp.include_router(cabinet.router)
    dp.include_router(support.router)
    dp.include_router(trends_router)
    dp.include_router(generation_purchase.router)
    logger.info("🚀 Бот запущен")
    
    # Запускаем webhook сервер
    webhook_runner = await start_webhook_server(bot, host='127.0.0.1', port=8080)
    logger.info("✅ Webhook сервер запущен на 127.0.0.1:8080")


    # Запускаем polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await webhook_runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⛔ Бот остановлен")