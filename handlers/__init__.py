from handlers.start import router as start_router
from handlers.photo_animation import router as photo_animation_router
from handlers.video_generation import router as video_generation_router
from handlers.image_editing import router as image_editing_router
from handlers.referral import router as referral_router
from handlers.cabinet import router as cabinet_router
from handlers.support import router as support_router
from handlers.payment import router as payment_router

__all__ = [
    'start_router',
    'photo_animation_router',
    'video_generation_router',
    'image_editing_router',
    'referral_router',
    'cabinet_router',
    'support_router',
    'payment_router'
]