import aiohttp
import json
import base64
from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
import uuid


class YooKassaClient:
    """Клиент для работы с YooKassa API"""
    
    def __init__(self):
        self.shop_id = YOOKASSA_SHOP_ID
        self.secret_key = YOOKASSA_SECRET_KEY
        self.base_url = "https://api.yookassa.ru/v3"
        
        # Создаём Basic Auth заголовок
        credentials = f"{self.shop_id}:{self.secret_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())
        }
    
    async def create_payment(self, amount: float, description: str, user_id: int) -> dict:
        """
        Создаёт платёж в YooKassa
        
        Args:
            amount: Сумма платежа
            description: Описание платежа
            user_id: ID пользователя Telegram
            
        Returns:
            Словарь с данными платежа (payment_id, confirmation_url)
        """
        url = f"{self.base_url}/payments"
        
        payload = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/YOUR_BOT_USERNAME"  # Замените на username вашего бота
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id)
            }
        }
        
        try:
            # Генерируем новый Idempotence-Key для каждого запроса
            headers = self.headers.copy()
            headers["Idempotence-Key"] = str(uuid.uuid4())
            
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        return {
                            "payment_id": data.get("id"),
                            "confirmation_url": data.get("confirmation", {}).get("confirmation_url"),
                            "status": data.get("status")
                        }
                    else:
                        print(f"Ошибка создания платежа: {data}")
                        return None
        except Exception as e:
            print(f"Ошибка при создании платежа: {e}")
            return None
    
    async def check_payment(self, payment_id: str) -> dict:
        """
        Проверяет статус платежа
        
        Args:
            payment_id: ID платежа в YooKassa
            
        Returns:
            Словарь с данными платежа
        """
        url = f"{self.base_url}/payments/{payment_id}"
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers) as response:
                    data = await response.json()
                    
                    if response.status == 200:
                        return {
                            "status": data.get("status"),
                            "paid": data.get("paid"),
                            "amount": float(data.get("amount", {}).get("value", 0)),
                            "metadata": data.get("metadata", {})
                        }
                    else:
                        print(f"Ошибка проверки платежа: {data}")
                        return None
        except Exception as e:
            print(f"Ошибка при проверке платежа: {e}")
            return None