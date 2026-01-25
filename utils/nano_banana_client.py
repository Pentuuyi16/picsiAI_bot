import aiohttp
import asyncio
import json
from typing import Optional, Callable
from config import KIE_API_KEY


class NanoBananaClient:
    """Клиент для работы с API генерации изображений Nano Banana"""
    
    def __init__(self):
        self.api_key = KIE_API_KEY
        self.base_url = "https://api.kie.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_generation_task(
        self,
        prompt: str,
        image_size: str = "1:1",
        output_format: str = "png",
        model: str = "google/nano-banana"
    ) -> Optional[str]:
        """Создаёт задачу на генерацию изображения"""
        url = f"{self.base_url}/api/v1/jobs/createTask"
        
        payload = {
            "model": model,
            "input": {
                "prompt": prompt,
                "image_size": image_size,
                "output_format": output_format
            }
        }
        
        print(f"📤 Отправка запроса на генерацию изображения:")
        print(f"   URL: {url}")
        print(f"   Model: {model}")
        print(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    print(f"📥 Получен ответ: Status {response.status}")
                    
                    response_text = await response.text()
                    print(f"📄 Response body: {response_text}")
                    
                    data = await response.json()
                    
                    if data.get("code") == 200:
                        task_id = data.get("data", {}).get("taskId")
                        print(f"✅ Task ID получен: {task_id}")
                        return task_id
                    else:
                        print(f"❌ Ошибка создания задачи (code: {data.get('code')}): {data.get('msg')}")
                        return None
        except Exception as e:
            print(f"❌ Исключение при создании задачи: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Получает статус задачи генерации"""
        url = f"{self.base_url}/api/v1/jobs/recordInfo"
        
        params = {
            "taskId": task_id
        }
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    data = await response.json()
                    
                    if data.get("code") == 200:
                        return data.get("data")
                    else:
                        print(f"⚠️ Ошибка получения статуса: {data}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка при получении статуса: {e}")
            return None
    
    async def wait_for_result(
        self, 
        task_id: str, 
        max_attempts: int = 240,
        delay: int = 5,
        progress_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        Ожидает завершения генерации изображения
        
        Args:
            task_id: ID задачи
            max_attempts: Максимальное количество попыток проверки
            delay: Задержка между проверками в секундах
            progress_callback: Опциональная функция для отправки прогресса
            
        Returns:
            URL изображения если успешно
            "MODERATION_ERROR" если ошибка модерации
            "TIMEOUT_ERROR" если таймаут от API
            None если другая ошибка
        """
        print(f"⏳ Ожидание завершения генерации задачи {task_id}...")
        print(f"   Максимальное время ожидания: {max_attempts * delay // 60} минут")
        
        for attempt in range(max_attempts):
            status_data = await self.get_task_status(task_id)
            
            if not status_data:
                await asyncio.sleep(delay)
                continue
            
            state = status_data.get("state")
            
            # Выводим прогресс каждые 6 попыток (примерно раз в 30 секунд)
            if attempt % 6 == 0:
                elapsed_minutes = (attempt * delay) // 60
                print(f"⏳ Проверка {attempt + 1}/{max_attempts}: {state} (прошло {elapsed_minutes} мин)")
                
                # Отправляем прогресс пользователю каждую минуту
                if progress_callback and attempt > 0 and attempt % 12 == 0:
                    try:
                        await progress_callback(elapsed_minutes, 5)  # Всегда показываем 5 минут
                    except Exception as e:
                        print(f"⚠️ Ошибка при отправке прогресса: {e}")
            
            if state == "success":
                print("🎉 Генерация завершена!")
                
                result_json_str = status_data.get("resultJson")
                
                if result_json_str:
                    try:
                        if isinstance(result_json_str, str):
                            result_json = json.loads(result_json_str)
                        else:
                            result_json = result_json_str
                        
                        result_urls = result_json.get("resultUrls", [])
                        
                        if result_urls and len(result_urls) > 0:
                            image_url = result_urls[0]
                            print(f"🖼 Изображение готово: {image_url}")
                            return image_url
                        else:
                            print("⚠️ resultUrls пуст")
                    except Exception as e:
                        print(f"⚠️ Ошибка парсинга resultJson: {e}")
                
                return None
            
            elif state == "fail":
                fail_msg = status_data.get("failMsg", "Неизвестная ошибка")
                fail_code = status_data.get("failCode", "")
                print(f"❌ Ошибка генерации!")
                print(f"Fail Code: {fail_code}")
                print(f"Fail Message: {fail_msg}")

                # Проверяем код ошибки 501 (Google модерация)
                if str(fail_code) == "501":
                    print(f"🚫 Контент заблокирован модерацией Google (код 501)")
                    return "MODERATION_ERROR"

                fail_msg_lower = str(fail_msg).lower()
                if ("nsfw" in fail_msg_lower or
                    "inappropriate" in fail_msg_lower or
                    "prominent people" in fail_msg_lower or
                    "violating content" in fail_msg_lower or
                    "violated google" in fail_msg_lower or
                    "prohibited use policy" in fail_msg_lower):
                    print(f"🚫 Контент заблокирован модерацией")
                    return "MODERATION_ERROR"
                
                if ("timeout" in fail_msg_lower or 
                    "timed out" in fail_msg_lower or
                    "upstream api service timed out" in fail_msg_lower or
                    "no results were returned" in fail_msg_lower):
                    print(f"⏱️ Таймаут от API сервиса")
                    return "TIMEOUT_ERROR"
                
                return None
            
            await asyncio.sleep(delay)
        
        print("❌ Превышено время ожидания генерации")
        return "TIMEOUT_ERROR"