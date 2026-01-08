import aiohttp
import asyncio
import json
from typing import Optional
from config import KIE_API_KEY, KIE_API_BASE_URL


class KieApiClient:
    """Клиент для работы с Kie.ai API для оживления фото (Grok Image-to-Video)"""
    
    def __init__(self):
        self.api_key = KIE_API_KEY
        self.base_url = KIE_API_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_task(self, image_url: str, prompt: str, mode: str = "normal") -> Optional[str]:
        """
        Создаёт задачу на оживление фото через Grok Image-to-Video
        """
        url = f"{self.base_url}/api/v1/jobs/createTask"
        
        payload = {
            "model": "grok-imagine/image-to-video",
            "input": {
                "image_urls": [image_url],  # Массив URL изображений
                "prompt": prompt,
                "mode": mode
            }
        }
        
        print(f"📤 Отправка запроса на создание задачи оживления фото:")
        print(f"   URL: {url}")
        print(f"   Model: grok-imagine/image-to-video")
        print(f"   Image URLs: {[image_url]}")
        print(f"   Prompt: {prompt}")
        print(f"   Mode: {mode}")
        print(f"   Full payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
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
                        print(f"❌ Ошибка API: {data}")
                        return None
        except Exception as e:
            print(f"❌ Исключение при создании задачи: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Получает статус задачи"""
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
    
    async def wait_for_completion(self, task_id: str, max_attempts: int = 60, delay: int = 5) -> Optional[str]:
        """
        Ожидает завершения задачи на оживление фото
        
        Args:
            task_id: ID задачи
            max_attempts: Максимальное количество попыток проверки
            delay: Задержка между проверками в секундах
            
        Returns:
            URL видео если успешно, None если ошибка или таймаут
        """
        print(f"⏳ Ожидание завершения задачи {task_id}...")
        
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
                print("🎉 Оживление фото завершено!")
                
                # Парсим resultJson
                result_json_str = status_data.get("resultJson")
                
                if result_json_str:
                    try:
                        if isinstance(result_json_str, str):
                            result_json = json.loads(result_json_str)
                        else:
                            result_json = result_json_str
                        
                        # Получаем URL видео
                        result_urls = result_json.get("resultUrls", [])
                        
                        if result_urls and len(result_urls) > 0:
                            video_url = result_urls[0]
                            print(f"🎬 Видео готово: {video_url}")
                            return video_url
                        else:
                            print("⚠️ resultUrls пуст")
                            print(f"Full resultJson: {result_json}")
                    except Exception as e:
                        print(f"⚠️ Ошибка парсинга resultJson: {e}")
                        print(f"resultJson value: {result_json_str}")
                
                print("⚠️ Видео готово, но URL не найден")
                return None
            
            elif state == "fail":
                fail_code = status_data.get("failCode", "")
                fail_msg = status_data.get("failMsg", "")
                print(f"❌ Ошибка при оживлении фото: [{fail_code}] {fail_msg}")
    
                # Проверяем ошибки модерации
                fail_msg_lower = fail_msg.lower()
                if ("prominent people" in fail_msg_lower or 
                    "violating content policies" in fail_msg_lower or
                    "inappropriate content" in fail_msg_lower or
                    fail_code in ["400", "500"]):
                    print(f"🚫 Контент заблокирован модерацией")
                    return "MODERATION_ERROR"
    
        return None