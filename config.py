import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Токен бота
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Username бота (без @)
BOT_USERNAME = os.getenv("BOT_USERNAME")

# API ключ для KIE API
KIE_API_KEY = os.getenv("KIE_API_KEY")

# KIE API Base URL
KIE_API_BASE_URL = "https://api.kie.ai"

# YooKassa настройки
YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

# Путь к базе данных
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_database.db")