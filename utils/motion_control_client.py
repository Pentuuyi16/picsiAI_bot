import aiohttp
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


class MotionControlClient:
    """Клиент для работы с Kling Motion Control API"""
    
    def __init__(self):
        self.api_key = "f078fb587349fe3c4745de8cbc6b1f5f"
        self.base_url = "https://api.kie.ai/api/v1/jobs"
        self.model = "kling-2.6/motion-control"
    
    async def create_task(self, image_url: str, video_url: str, prompt: str = "", 
                          character_orientation: str = "video", mode: str = "720p"):
        """
        Создает задачу на генерацию с управлением движением
        
        Args:
            image_url: URL изображения
            video_url: URL видео для управления движением
            prompt: Текстовое описание (опционально)
            character_orientation: "image" (max 10s) или "video" (max 30s)
            mode: "720p" или "1080p"
        
        Returns:
            task_id или None в случае ошибки
        """
        url = f"{self.base_url}/createTask"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "input": {
                "input_urls": [image_url],
                "video_urls": [video_url],
                "character_orientation": character_orientation,
                "mode": mode
            }
        }
        
        # Добавляем prompt если есть
        if prompt:
            payload["input"]["prompt"] = prompt[:2500]  # Максимум 2500 символов
        
        try:
            print(f"\n{'='*70}")
            print(f"🎯 СОЗДАНИЕ ЗАДАЧИ MOTION CONTROL")
            print(f"Image URL: {image_url}")
            print(f"Video URL: {video_url}")
            print(f"Orientation: {character_orientation}")
            print(f"Mode: {mode}")
            print(f"Prompt: {prompt[:100] if prompt else 'None'}")
            print(f"\n📦 Full Payload:")
            print(json.dumps(payload, indent=2, ensure_ascii=False))
            print(f"{'='*70}\n")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    # ДОБАВЛЕНО: Читаем raw response
                    response_text = await response.text()
                    print(f"\n📥 RAW API RESPONSE:")
                    print(f"Status Code: {response.status}")
                    print(f"Response Body: {response_text}")
                    print(f"{'='*50}\n")
                    
                    # Пытаемся распарсить JSON
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        print(f"❌ Ошибка парсинга JSON: {e}")
                        print(f"Response text: {response_text}")
                        return None
                    
                    print(f"📊 PARSED API Response:")
                    print(f"   Code: {result.get('code')}")
                    print(f"   Message: {result.get('message')}")
                    print(f"   Data: {result.get('data')}")
                    
                    if result.get("code") == 200 and result.get("data", {}).get("taskId"):
                        task_id = result["data"]["taskId"]
                        print(f"\n✅ Task ID создан: {task_id}\n")
                        return task_id
                    else:
                        print(f"\n❌ Ошибка создания задачи!")
                        print(f"Full API Response:")
                        print(json.dumps(result, indent=2, ensure_ascii=False))
                        print()
                        return None
        
        except Exception as e:
            logger.error(f"Ошибка при создании задачи: {e}", exc_info=True)
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_task_status(self, task_id: str):
        """
        Получает статус задачи
        
        Args:
            task_id: ID задачи
        
        Returns:
            dict с данными задачи или None
        """
        url = f"{self.base_url}/recordInfo"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        params = {
            "taskId": task_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as response:
                    result = await response.json()
                    
                    if result.get("code") == 200 and result.get("data"):
                        return result["data"]
                    else:
                        logger.error(f"Ошибка получения статуса: {result}")
                        return None
        
        except Exception as e:
            logger.error(f"Ошибка при получении статуса: {e}", exc_info=True)
            return None
    
    async def wait_for_result(self, task_id: str, max_attempts: int = 120, delay: int = 10):
        """
        Ожидает завершения генерации
        
        Args:
            task_id: ID задачи
            max_attempts: Максимальное количество попыток (120 * 10сек = 20 минут)
            delay: Задержка между проверками в секундах
        
        Returns:
            video_url если успешно, "MODERATION_ERROR" при ошибке модерации, None при других ошибках
        """
        print(f"\n{'='*70}")
        print(f"⏳ ОЖИДАНИЕ ЗАВЕРШЕНИЯ ГЕНЕРАЦИИ")
        print(f"Task ID: {task_id}")
        print(f"Max attempts: {max_attempts} (макс. {max_attempts * delay // 60} минут)")
        print(f"{'='*70}\n")
        
        for attempt in range(max_attempts):
            try:
                data = await self.get_task_status(task_id)
                
                if not data:
                    print(f"⚠️ Попытка {attempt + 1}/{max_attempts}: Не удалось получить статус")
                    await asyncio.sleep(delay)
                    continue
                
                state = data.get("state")
                print(f"🔄 Попытка {attempt + 1}/{max_attempts}: State = {state}")
                
                if state == "success":
                    # Парсим результат
                    result_json = data.get("resultJson")
                    if result_json:
                        try:
                            result_data = json.loads(result_json)
                            video_urls = result_data.get("resultUrls", [])
                            
                            if video_urls:
                                video_url = video_urls[0]
                                print(f"\n{'='*70}")
                                print(f"✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
                                print(f"Video URL: {video_url}")
                                print(f"Время генерации: {data.get('costTime', 0) // 1000} сек")
                                print(f"{'='*70}\n")
                                return video_url
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга resultJson: {e}")
                    
                    print("⚠️ Задача завершена, но нет URL видео")
                    return None
                
                elif state == "fail":
                    fail_code = data.get("failCode", "")
                    fail_msg = data.get("failMsg", "")
                    
                    print(f"\n{'='*70}")
                    print(f"❌ ГЕНЕРАЦИЯ ПРОВАЛИЛАСЬ")
                    print(f"Fail Code: {fail_code}")
                    print(f"Fail Message: {fail_msg}")
                    print(f"{'='*70}\n")
                    
                    # Проверяем на ошибку модерации
                    if "moderation" in fail_msg.lower() or fail_code in ["403", "451"]:
                        return "MODERATION_ERROR"
                    
                    return None
                
                elif state in ["waiting", "queuing", "generating"]:
                    # Продолжаем ждать
                    await asyncio.sleep(delay)
                    continue
                
                else:
                    print(f"⚠️ Неизвестный статус: {state}")
                    await asyncio.sleep(delay)
                    continue
            
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса (попытка {attempt + 1}): {e}")
                await asyncio.sleep(delay)
                continue
        
        print(f"\n{'='*70}")
        print(f"⏱️ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ")
        print(f"Задача не завершилась за {max_attempts * delay // 60} минут")
        print(f"{'='*70}\n")
        return None