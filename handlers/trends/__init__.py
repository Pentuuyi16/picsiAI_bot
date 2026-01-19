from aiogram import Router
from .handler import router as handler_router
from .macbook import router as macbook_router
from .bouquet import router as bouquet_router
from .snow_angel import router as snow_angel_router
from .snowboard import router as snowboard_router  # ← ИЗМЕНЕНО
from .wall_portrait import router as wall_portrait_router
from .loving_gaze import router as loving_gaze_router
from .swords import router as swords_router
from .heart_building import router as heart_building_router
from .car import router as car_router
from .scream import router as scream_router

# Главный роутер для трендов
router = Router()

# Подключаем все роутеры
router.include_router(handler_router)
router.include_router(macbook_router)
router.include_router(bouquet_router)
router.include_router(snow_angel_router)
router.include_router(snowboard_router)  # ← ИЗМЕНЕНО
router.include_router(wall_portrait_router)
router.include_router(loving_gaze_router)
router.include_router(swords_router)
router.include_router(heart_building_router)
router.include_router(car_router)
router.include_router(scream_router)