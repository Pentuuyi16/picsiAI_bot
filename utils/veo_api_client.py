import aiohttp
import asyncio
import json
from typing import Optional, Dict, Any, List
from config import KIE_API_KEY


class VeoApiClient:
    """Клиент для работы с Veo 3.1 API"""
    
    def __init__(self):
        self.api_key = KIE_API_KEY
        self.base_url = "https://api.kie.ai/api/v1/veo"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate_video(
        self,
        prompt: str,
        model: str = "veo3_fast",
        aspect_ratio: str = "16:9",
        image_urls: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Создаёт задачу на генерацию видео
        
        Args:
            prompt: Текстовое описание видео
            model: Модель ("veo3_fast" или "veo3")
            aspect_ratio: Соотношение сторон ("16:9" или "9:16")
            image_urls: Список URL изображений (опционально, для image-to-video)
            
        Returns:
            taskId если успешно, None если ошибка
        """
        url = f"{self.base_url}/generate"
        
        payload = {
            "prompt": prompt,
            "model": model,
            "aspectRatio": aspect_ratio,
            "enableTranslation": True
        }
        
        # Если есть изображения, добавляем их и указываем тип генерации
        if image_urls:
            payload["imageUrls"] = image_urls
            payload["generationType"] = "FIRST_AND_LAST_FRAMES_2_VIDEO"
        else:
            payload["generationType"] = "TEXT_2_VIDEO"
        
        print(f"Отправка запроса на генерацию: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    response_text = await response.text()
                    print(f"Raw response: {response_text}")
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        print(f"Ошибка парсинга JSON ответа: {e}")
                        return None
                    
                    print(f"API Generate Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                    
                    if data.get("code") == 200:
                        task_id = data.get("data", {}).get("taskId")
                        print(f"Task created successfully: {task_id}")
                        return task_id
                    else:
                        print(f"Ошибка генерации видео (code: {data.get('code')}): {data.get('msg')}")
                        return None
        except Exception as e:
            print(f"Ошибка при создании задачи: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_video_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает статус задачи генерации видео
        
        Args:
            task_id: ID задачи
            
        Returns:
            Данные о задаче если успешно, None если ошибка
        """
        url = f"{self.base_url}/record-info"
        params = {"taskId": task_id}
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    response_text = await response.text()
                    
                    try:
                        data = json.loads(response_text)
                    except json.JSONDecodeError:
                        print(f"Ошибка парсинга ответа статуса: {response_text}")
                        return None
                    
                    if data.get("code") == 200:
                        return data.get("data")
                    else:
                        print(f"Ошибка получения статуса (code {data.get('code')}): {data.get('msg')}")
                        return None
        except asyncio.TimeoutError:
            print("Таймаут при запросе статуса")
            return None
        except Exception as e:
            print(f"Ошибка при запросе статуса: {e}")
            return None
    
    async def wait_for_video(self, task_id: str, max_attempts: int = 120, delay: int = 10) -> Optional[str]:
        """
        Ожидает завершения генерации видео
        
        Args:
            task_id: ID задачи
            max_attempts: Максимальное количество попыток
            delay: Задержка между проверками в секундах
            
        Returns:
            URL видео если успешно, "MODERATION_ERROR" если ошибка модерации, None если другая ошибка или таймаут
        """
        for attempt in range(max_attempts):
            print(f"\n{'='*50}")
            print(f"Проверка статуса, попытка {attempt + 1}/{max_attempts}")
            print(f"{'='*50}")
            
            status_data = await self.get_video_status(task_id)
            
            if not status_data:
                print("❌ status_data is None, ждём...")
                await asyncio.sleep(delay)
                continue
            
            # Выводим полный ответ для отладки
            print(f"\n📋 Полный ответ API:")
            print(json.dumps(status_data, indent=2, ensure_ascii=False))
            
            # Используем successFlag
            success_flag = status_data.get("successFlag")
            print(f"\n✅ successFlag: {success_flag}")
            
            # successFlag 1 = Success
            if success_flag == 1:
                print("🎉 Генерация завершена успешно!")
                
                # Пробуем получить URL из разных возможных мест
                # Вариант 1: из поля response
                response_field = status_data.get("response")
                if response_field:
                    print(f"📦 response field exists: {response_field}")
                    try:
                        if isinstance(response_field, str):
                            result_json = json.loads(response_field)
                        else:
                            result_json = response_field
                        
                        print(f"📄 Parsed response: {json.dumps(result_json, indent=2, ensure_ascii=False)}")
                        
                        # Ищем resultUrls
                        video_urls = result_json.get("resultUrls", [])
                        if video_urls and len(video_urls) > 0:
                            video_url = video_urls[0]
                            print(f"🎬 Видео URL найден: {video_url}")
                            return video_url
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"⚠️ Ошибка парсинга response: {e}")
                
                # Вариант 2: Может быть в другом поле?
                # Попробуем найти URL в любом поле с "url" или "result"
                for key, value in status_data.items():
                    if "url" in key.lower() or "result" in key.lower():
                        print(f"🔍 Найдено поле {key}: {value}")
                        if isinstance(value, str):
                            try:
                                parsed = json.loads(value)
                                if isinstance(parsed, dict) and "resultUrls" in parsed:
                                    urls = parsed.get("resultUrls", [])
                                    if urls:
                                        print(f"🎬 Видео URL из {key}: {urls[0]}")
                                        return urls[0]
                            except:
                                pass
                
                print("⚠️ successFlag = 1, но URL видео не найден")
                print("Подождём ещё немного...")
                await asyncio.sleep(delay)
                continue
            
            # successFlag 2 или 3 = Failed
            elif success_flag in [2, 3]:
                error_msg = status_data.get("errorMessage", "Неизвестная ошибка")
                error_code = status_data.get("errorCode", "")
                print(f"❌ Генерация видео завершилась с ошибкой!")
                print(f"Error Code: {error_code}")
                print(f"Error Message: {error_msg}")
                
                # Проверяем ошибки модерации
                error_msg_lower = error_msg.lower()
                if ("prominent people" in error_msg_lower or 
                    "violating content policies" in error_msg_lower or 
                    error_code == "400"):
                    print(f"🚫 Контент заблокирован модерацией")
                    return "MODERATION_ERROR"
                
                return None
            
            # successFlag 0 = Generating - продолжаем ждать
            elif success_flag == 0:
                print("⏳ Генерация в процессе...")
                await asyncio.sleep(delay)
            else:
                print(f"⚠️ Неизвестный successFlag: {success_flag}")
                await asyncio.sleep(delay)
        
        # Таймаут
        print("\n❌ Превышено время ожидания генерации видео")
        return None