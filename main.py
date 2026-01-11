import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import start, photo_animation, video_generation, payment, image_editing, referral, cabinet, support
from webhook_server import start_webhook_server

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота"""
    # Создаём бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Настраиваем команды бота (меню)
    commands = [
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="pay", description="Пополнить счёт"),
        BotCommand(command="cabinet", description="Личный кабинет"),
        BotCommand(command="help", description="Поддержка")
    ]
    await bot.set_my_commands(commands)
    logger.info("✅ Команды бота настроены")
    
    # Подключаем роутеры из handlers
    dp.include_router(start.router)
    dp.include_router(photo_animation.router)
    dp.include_router(video_generation.router)
    dp.include_router(image_editing.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)
    dp.include_router(cabinet.router)
    dp.include_router(support.router)
    
    # Временный обработчик для получения file_id видео
    from aiogram import F
    from aiogram.types import Message
    
    @dp.message(F.video)
    async def get_video_file_id(message: Message):
        """Временный обработчик для получения file_id видео"""
        file_id = message.video.file_id
        await message.answer(f"Video File ID:\n`{file_id}`", parse_mode="Markdown")
        print(f"📹 Video File ID: {file_id}")
    
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