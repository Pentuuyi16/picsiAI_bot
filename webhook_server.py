from aiohttp import web
import logging
from database.database import Database
from aiogram import Bot

logger = logging.getLogger(__name__)


async def yookassa_webhook(request):
    """Обработчик webhook от YooKassa"""
    try:
        # Получаем данные от YooKassa
        data = await request.json()
        
        logger.info(f"📨 Получен webhook от YooKassa: {data}")
        
        # Извлекаем информацию о платеже
        event = data.get('event')
        payment_object = data.get('object')
        
        if not payment_object:
            logger.error("⚠️ Нет объекта payment в webhook")
            return web.Response(status=400)
        
        payment_id = payment_object.get('id')
        status = payment_object.get('status')
        amount_value = float(payment_object.get('amount', {}).get('value', 0))
        paid = payment_object.get('paid', False)
        
        logger.info(f"💳 Payment ID: {payment_id}, Status: {status}, Amount: {amount_value}, Paid: {paid}")
        
        # Обрабатываем успешный платёж
        if event == 'payment.succeeded' and paid and status == 'succeeded':
            db = Database()
            
            # Находим платёж в БД
            payment = db.get_payment(payment_id)
            
            if not payment:
                logger.error(f"❌ Платёж {payment_id} не найден в БД")
                return web.Response(status=404)
            
            # Проверяем что платёж ещё не обработан
            if payment['status'] == 'succeeded':
                logger.info(f"⚠️ Платёж {payment_id} уже обработан")
                return web.Response(status=200)
            
            user_id = payment['user_id']
            amount = payment['amount']
            
            logger.info(f"💰 Начисляем баланс: user_id={user_id}, amount={amount}")
            
            # Начисляем баланс пользователю
            db.add_to_balance(user_id, amount)
            
            # Обновляем статус платежа
            db.update_payment_status(payment_id, 'succeeded')
            
            # Проверяем реферала и начисляем бонус
            user = db.get_user(user_id)
            if user and user.get('referrer_id'):
                referrer_id = user['referrer_id']
                referral_bonus = amount * 0.15  # 15% реферальный бонус
                
                logger.info(f"💎 Начисляем реферальный бонус: referrer_id={referrer_id}, bonus={referral_bonus}")
                
                # Начисляем бонус рефереру
                db.add_to_balance(referrer_id, referral_bonus)
                db.add_referral_earning(referrer_id, user_id, referral_bonus, amount)
                
                # Уведомляем реферера
                try:
                    bot = request.app['bot']
                    await bot.send_message(
                        referrer_id,
                        f"🎉 Ваш реферал пополнил баланс!\n\n"
                        f"💰 Вам начислено: {referral_bonus:.2f} ₽"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки уведомления рефереру: {e}")
            
            # Отправляем уведомление пользователю
            try:
                bot = request.app['bot']
                await bot.send_message(
                    user_id,
                    f"✅ Платёж успешно получен!\n\n"
                    f"💰 Начислено: {amount:.2f} ₽\n"
                    f"💳 Ваш новый баланс: {db.get_user(user_id)['balance']:.2f} ₽"
                )
                logger.info(f"✅ Уведомление отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки уведомления пользователю: {e}")
            
            logger.info(f"✅ Платёж {payment_id} успешно обработан")
            
            return web.Response(status=200)
        
        # Другие события
        logger.info(f"ℹ️ Событие {event} - пропускаем")
        return web.Response(status=200)
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки webhook: {e}", exc_info=True)
        return web.Response(status=500)


async def health_check(request):
    """Проверка работоспособности сервера"""
    return web.Response(text="OK")


def create_app(bot: Bot):
    """Создаёт веб-приложение для webhook"""
    app = web.Application()
    app['bot'] = bot
    
    # Маршруты
    app.router.add_post('/webhook/yookassa', yookassa_webhook)
    app.router.add_get('/health', health_check)
    
    return app


async def start_webhook_server(bot: Bot, host='127.0.0.1', port=8080):
    """Запускает webhook сервер"""
    app = create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logger.info(f"🌐 Webhook сервер запущен на {host}:{port}")
    return runner