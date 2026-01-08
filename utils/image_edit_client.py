import aiohttp
import asyncio
import json
from typing import Optional
from config import KIE_API_KEY


class ImageEditClient:
    """Клиент для работы с API редактирования изображений (nano-banana-pro)"""
    
    def __init__(self):
        self.api_key = KIE_API_KEY
        self.base_url = "https://api.kie.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_edit_task(
        self,
        prompt: str,
        image_urls: list,
        aspect_ratio: str = "1:1",
        resolution: str = "1K",
        output_format: str = "png"
    ) -> Optional[str]:
        """Создаёт задачу на редактирование изображения"""
        url = f"{self.base_url}/api/v1/jobs/createTask"
        
        payload = {
            "model": "nano-banana-pro",
            "input": {
                "image_input": image_urls,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "output_format": output_format
            }
        }
        
        print(f"📤 Отправка запроса на редактирование изображения:")
        print(f"   URL: {url}")
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
        """Получает статус задачи редактирования"""
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
    
    async def wait_for_result(self, task_id: str, max_attempts: int = 120, delay: int = 5) -> Optional[str]:
        """
        Ожидает завершения редактирования изображения
        
        Args:
            task_id: ID задачи
            max_attempts: Максимальное количество попыток проверки
            delay: Задержка между проверками в секундах
            
        Returns:
            URL изображения если успешно, "MODERATION_ERROR" если ошибка модерации, None если другая ошибка или таймаут
        """
        print(f"⏳ Ожидание завершения редактирования задачи {task_id}...")
        
        for attempt in range(max_attempts):
            status_data = await self.get_task_status(task_id)
            
            if not status_data:
                await asyncio.sleep(delay)
                continue
            
            state = status_data.get("state")
            
            # Выводим прогресс каждые 6 попыток (примерно раз в 30 секунд)
            if attempt % 6 == 0:
                print(f"⏳ Проверка {attempt + 1}/{max_attempts}: {state}...")
            
            if state == "success":
                print("🎉 Редактирование завершено!")
                
                # Парсим resultJson
                result_json_str = status_data.get("resultJson")
                
                if result_json_str:
                    try:
                        if isinstance(result_json_str, str):
                            result_json = json.loads(result_json_str)
                        else:
                            result_json = result_json_str
                        
                        # Получаем URL изображения
                        result_urls = result_json.get("resultUrls", [])
                        
                        if result_urls and len(result_urls) > 0:
                            image_url = result_urls[0]
                            print(f"🖼 Изображение готово: {image_url}")
                            return image_url
                        else:
                            print("⚠️ resultUrls пуст")
                            print(f"Full resultJson: {result_json}")
                    except Exception as e:
                        print(f"⚠️ Ошибка парсинга resultJson: {e}")
                        print(f"resultJson value: {result_json_str}")
                
                print("⚠️ Редактирование завершено, но URL изображения не найден")
                return None
            
            elif state == "fail":
                fail_msg = status_data.get("failMsg", "Неизвестная ошибка")
                fail_code = status_data.get("failCode", "")
                print(f"❌ Ошибка редактирования!")
                print(f"Fail Code: {fail_code}")
                print(f"Fail Message: {fail_msg}")
                
                # Проверяем ошибки модерации
                fail_msg_lower = str(fail_msg).lower()
                if ("nsfw" in fail_msg_lower or 
                    "inappropriate" in fail_msg_lower or
                    "prominent people" in fail_msg_lower or
                    "violating content" in fail_msg_lower or
                    str(fail_code) in ["400", "422", "500"]):
                    print(f"🚫 Контент заблокирован модерацией")
                    return "MODERATION_ERROR"
                
                return None
            
            # Статус "waiting", "queuing", "generating" - продолжаем ждать
            await asyncio.sleep(delay)
        
        print("❌ Превышено время ожидания редактирования")
        return None