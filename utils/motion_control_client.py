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
    
    async def upload_to_telegraph(self, file_url: str, file_name: str = "file") -> str:
        """
        Скачивает файл из Telegram и загружает на telegra.ph
        
        Args:
            file_url: URL файла из Telegram
            file_name: Имя файла
        
        Returns:
            Публичный URL файла на telegra.ph
        """
        try:
            logger.info(f"📥 Скачиваем файл из Telegram: {file_url}")
            
            # Скачиваем файл из Telegram
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания: HTTP {response.status}")
                        return file_url
                    
                    file_data = await response.read()
                    file_size_mb = len(file_data) / (1024 * 1024)
                    logger.info(f"✅ Файл скачан: {file_size_mb:.2f} MB")
            
            # Загружаем на telegra.ph
            logger.info(f"📤 Загружаем на telegra.ph...")
            
            upload_url = "https://telegra.ph/upload"
            
            form_data = aiohttp.FormData()
            # Определяем content type по расширению
            content_type = "video/mp4"  # По умолчанию
            if file_name.lower().endswith('.mov'):
                content_type = "video/quicktime"
            elif file_name.lower().endswith('.jpg') or file_name.lower().endswith('.jpeg'):
                content_type = "image/jpeg"
            elif file_name.lower().endswith('.png'):
                content_type = "image/png"
            
            form_data.add_field('file',
                              file_data,
                              filename=file_name,
                              content_type=content_type)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка загрузки на telegraph: HTTP {response.status}")
                        return file_url
                    
                    result = await response.json()
                    
                    if isinstance(result, list) and len(result) > 0:
                        # telegra.ph возвращает массив с путями
                        file_path = result[0].get('src', '')
                        if file_path:
                            public_url = f"https://telegra.ph{file_path}"
                            logger.info(f"✅ Файл загружен на telegra.ph: {public_url}")
                            return public_url
                    
                    logger.warning(f"Не удалось получить URL с telegra.ph: {result}")
                    return file_url
        
        except Exception as e:
            logger.error(f"❌ Ошибка при загрузке на telegra.ph: {e}", exc_info=True)
            return file_url
    
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
        
        # ИСПРАВЛЕНИЕ: Загружаем файлы на публичный хостинг
        logger.info(f"📤 Загружаем файлы на публичный хостинг (telegra.ph)...")
        
        # Определяем имена файлов из URL
        image_filename = image_url.split('/')[-1] if '/' in image_url else 'image.jpg'
        video_filename = video_url.split('/')[-1] if '/' in video_url else 'video.mov'
        
        public_image_url = await self.upload_to_telegraph(image_url, image_filename)
        public_video_url = await self.upload_to_telegraph(video_url, video_filename)
        
        logger.info(f"🔗 Public Image URL: {public_image_url}")
        logger.info(f"🔗 Public Video URL: {public_video_url}")
        
        payload = {
            "model": self.model,
            "input": {
                "input_urls": [public_image_url],
                "video_urls": [public_video_url],
                "character_orientation": character_orientation,
                "mode": mode
            }
        }
        
        # Добавляем prompt если есть
        if prompt:
            payload["input"]["prompt"] = prompt[:2500]  # Максимум 2500 символов
        
        try:
            logger.info(f"="*70)
            logger.info(f"🎯 СОЗДАНИЕ ЗАДАЧИ MOTION CONTROL")
            logger.info(f"Image URL (original): {image_url}")
            logger.info(f"Image URL (public): {public_image_url}")
            logger.info(f"Video URL (original): {video_url}")
            logger.info(f"Video URL (public): {public_video_url}")
            logger.info(f"Orientation: {character_orientation}")
            logger.info(f"Mode: {mode}")
            logger.info(f"Prompt: {prompt[:100] if prompt else 'None'}")
            logger.info(f"Full Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            logger.info(f"="*70)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    # Читаем raw response
                    response_text = await response.text()
                    
                    logger.info(f"📥 RAW API RESPONSE:")
                    logger.info(f"Status Code: {response.status}")
                    logger.info(f"Response Body: {response_text}")
                    
                    # Пытаемся распарсить JSON
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Ошибка парсинга JSON: {e}")
                        logger.error(f"Response text: {response_text}")
                        return None
                    
                    logger.info(f"📊 PARSED API Response:")
                    logger.info(f"Code: {result.get('code')}")
                    logger.info(f"Message: {result.get('message')}")
                    logger.info(f"Data: {result.get('data')}")
                    
                    if result.get("code") == 200 and result.get("data", {}).get("taskId"):
                        task_id = result["data"]["taskId"]
                        logger.info(f"✅ Task ID создан: {task_id}")
                        return task_id
                    else:
                        logger.error(f"❌ Ошибка создания задачи!")
                        logger.error(f"Full API Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
                        return None
        
        except Exception as e:
            logger.error(f"❌ Exception при создании задачи: {e}", exc_info=True)
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
        logger.info(f"="*70)
        logger.info(f"⏳ ОЖИДАНИЕ ЗАВЕРШЕНИЯ ГЕНЕРАЦИИ")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Max attempts: {max_attempts} (макс. {max_attempts * delay // 60} минут)")
        logger.info(f"="*70)
        
        for attempt in range(max_attempts):
            try:
                data = await self.get_task_status(task_id)
                
                if not data:
                    logger.warning(f"Попытка {attempt + 1}/{max_attempts}: Не удалось получить статус")
                    await asyncio.sleep(delay)
                    continue
                
                state = data.get("state")
                logger.info(f"🔄 Попытка {attempt + 1}/{max_attempts}: State = {state}")
                
                if state == "success":
                    # Парсим результат
                    result_json = data.get("resultJson")
                    if result_json:
                        try:
                            result_data = json.loads(result_json)
                            video_urls = result_data.get("resultUrls", [])
                            
                            if video_urls:
                                video_url = video_urls[0]
                                logger.info(f"="*70)
                                logger.info(f"✅ ГЕНЕРАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
                                logger.info(f"Video URL: {video_url}")
                                logger.info(f"Время генерации: {data.get('costTime', 0) // 1000} сек")
                                logger.info(f"="*70)
                                return video_url
                        except json.JSONDecodeError as e:
                            logger.error(f"Ошибка парсинга resultJson: {e}")
                    
                    logger.warning("Задача завершена, но нет URL видео")
                    return None
                
                elif state == "fail":
                    fail_code = data.get("failCode", "")
                    fail_msg = data.get("failMsg", "")
                    
                    logger.error(f"="*70)
                    logger.error(f"❌ ГЕНЕРАЦИЯ ПРОВАЛИЛАСЬ")
                    logger.error(f"Fail Code: {fail_code}")
                    logger.error(f"Fail Message: {fail_msg}")
                    logger.error(f"="*70)
                    
                    # Проверяем на ошибку модерации
                    if "moderation" in fail_msg.lower() or fail_code in ["403", "451"]:
                        return "MODERATION_ERROR"
                    
                    return None
                
                elif state in ["waiting", "queuing", "generating"]:
                    # Продолжаем ждать
                    await asyncio.sleep(delay)
                    continue
                
                else:
                    logger.warning(f"Неизвестный статус: {state}")
                    await asyncio.sleep(delay)
                    continue
            
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса (попытка {attempt + 1}): {e}")
                await asyncio.sleep(delay)
                continue
        
        logger.error(f"="*70)
        logger.error(f"⏱️ ПРЕВЫШЕНО ВРЕМЯ ОЖИДАНИЯ")
        logger.error(f"Задача не завершилась за {max_attempts * delay // 60} минут")
        logger.error(f"="*70)
        return None