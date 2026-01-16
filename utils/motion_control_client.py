import aiohttp
import asyncio
import json
import logging
import tempfile
import os
import subprocess

logger = logging.getLogger(__name__)


class MotionControlClient:
    """Клиент для работы с Kling Motion Control API"""
    
    def __init__(self):
        self.api_key = "f078fb587349fe3c4745de8cbc6b1f5f"
        self.base_url = "https://api.kie.ai/api/v1/jobs"
        self.model = "kling-2.6/motion-control"
    
    async def convert_and_upload_video(self, video_url: str) -> str:
        """
        Скачивает видео, конвертирует в mp4 (если нужно) и загружает на telegra.ph
        
        Args:
            video_url: URL видео из Telegram
        
        Returns:
            Публичный URL конвертированного видео
        """
        temp_input = None
        temp_output = None
        
        try:
            logger.info(f"🎬 НАЧАЛО КОНВЕРТАЦИИ ВИДЕО")
            logger.info(f"📥 Скачиваем видео из Telegram: {video_url}")
            
            # Скачиваем видео
            async with aiohttp.ClientSession() as session:
                async with session.get(video_url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания: HTTP {response.status}")
                        return video_url
                    
                    video_data = await response.read()
                    video_size_mb = len(video_data) / (1024 * 1024)
                    logger.info(f"✅ Видео скачано: {video_size_mb:.2f} MB")
            
            # Сохраняем во временный файл
            temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.mov')
            temp_input.write(video_data)
            temp_input.close()
            
            logger.info(f"💾 Временный файл создан: {temp_input.name}")
            
            # Конвертируем в mp4
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
            temp_output.close()
            
            logger.info(f"🔄 Конвертируем видео в MP4...")
            logger.info(f"Input: {temp_input.name}")
            logger.info(f"Output: {temp_output.name}")
            
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', temp_input.name,
                '-c:v', 'libx264',           # H.264 кодек
                '-preset', 'fast',            # Быстрая конвертация
                '-crf', '23',                 # Качество (18-28, меньше=лучше)
                '-c:a', 'aac',                # AAC аудио
                '-b:a', '128k',               # Битрейт аудио
                '-movflags', '+faststart',    # Для стриминга
                '-y',                         # Перезаписать файл
                temp_output.name
            ]
            
            logger.info(f"🎬 Запускаем FFmpeg: {' '.join(ffmpeg_cmd)}")
            
            result = subprocess.run(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"❌ FFmpeg error (code {result.returncode}):")
                logger.error(f"STDERR: {result.stderr.decode()}")
                logger.error(f"STDOUT: {result.stdout.decode()}")
                return video_url
            
            logger.info(f"✅ Видео конвертировано в MP4")
            
            # Проверяем что файл создан
            if not os.path.exists(temp_output.name):
                logger.error(f"❌ Выходной файл не создан: {temp_output.name}")
                return video_url
            
            output_size = os.path.getsize(temp_output.name)
            logger.info(f"📦 Размер выходного файла: {output_size / (1024*1024):.2f} MB")
            
            # Читаем конвертированное видео
            with open(temp_output.name, 'rb') as f:
                converted_video_data = f.read()
                converted_size_mb = len(converted_video_data) / (1024 * 1024)
                logger.info(f"✅ Видео прочитано: {converted_size_mb:.2f} MB")
            
            # Загружаем на telegra.ph
            logger.info(f"📤 Загружаем на telegra.ph...")
            
            upload_url = "https://telegra.ph/upload"
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                converted_video_data,
                filename='video.mp4',
                content_type='video/mp4'
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data, timeout=120) as response:
                    logger.info(f"Telegraph response status: {response.status}")
                    
                    if response.status != 200:
                        response_text = await response.text()
                        logger.error(f"Ошибка загрузки на telegraph: HTTP {response.status}")
                        logger.error(f"Response: {response_text}")
                        return video_url
                    
                    result = await response.json()
                    logger.info(f"Telegraph result: {result}")
                    
                    if isinstance(result, list) and len(result) > 0:
                        file_path = result[0].get('src', '')
                        if file_path:
                            public_url = f"https://telegra.ph{file_path}"
                            logger.info(f"✅ Видео загружено на telegra.ph: {public_url}")
                            return public_url
                    
                    logger.warning(f"Не удалось получить URL с telegra.ph: {result}")
                    return video_url
        
        except subprocess.TimeoutExpired:
            logger.error("❌ FFmpeg timeout (>60 sec)")
            return video_url
        except Exception as e:
            logger.error(f"❌ EXCEPTION в convert_and_upload_video: {e}", exc_info=True)
            logger.error(f"Video URL был: {video_url}")
            return video_url
        finally:
            # Удаляем временные файлы
            try:
                if temp_input and os.path.exists(temp_input.name):
                    os.unlink(temp_input.name)
                    logger.info(f"🗑️ Удален temp input: {temp_input.name}")
                if temp_output and os.path.exists(temp_output.name):
                    os.unlink(temp_output.name)
                    logger.info(f"🗑️ Удален temp output: {temp_output.name}")
            except Exception as e:
                logger.error(f"Ошибка удаления временных файлов: {e}")
    
    async def upload_image_to_telegraph(self, image_url: str) -> str:
        """Загружает изображение на telegra.ph"""
        try:
            logger.info(f"📥 Скачиваем изображение: {image_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка скачивания изображения: HTTP {response.status}")
                        return image_url
                    
                    image_data = await response.read()
                    logger.info(f"✅ Изображение скачано: {len(image_data) / 1024:.2f} KB")
            
            logger.info(f"📤 Загружаем изображение на telegra.ph...")
            
            upload_url = "https://telegra.ph/upload"
            
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                image_data,
                filename='image.jpg',
                content_type='image/jpeg'
            )
            
            async with aiohttp.ClientSession() as session:
                async with session.post(upload_url, data=form_data, timeout=30) as response:
                    if response.status != 200:
                        logger.error(f"Ошибка загрузки изображения на telegraph: HTTP {response.status}")
                        return image_url
                    
                    result = await response.json()
                    logger.info(f"Telegraph image result: {result}")
                    
                    if isinstance(result, list) and len(result) > 0:
                        file_path = result[0].get('src', '')
                        if file_path:
                            public_url = f"https://telegra.ph{file_path}"
                            logger.info(f"✅ Изображение загружено: {public_url}")
                            return public_url
                    
                    logger.warning(f"Не удалось получить URL изображения с telegra.ph")
                    return image_url
        
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки изображения: {e}", exc_info=True)
            return image_url
    
    async def create_task(self, image_url: str, video_url: str, prompt: str = "", 
                          character_orientation: str = "video", mode: str = "720p"):
        """Создает задачу на генерацию с управлением движением"""
        url = f"{self.base_url}/createTask"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"📤 Подготовка файлов для Kling API...")
        logger.info(f"Original Image URL: {image_url}")
        logger.info(f"Original Video URL: {video_url}")
        
        # Загружаем изображение
        public_image_url = await self.upload_image_to_telegraph(image_url)
        
        # Конвертируем и загружаем видео
        public_video_url = await self.convert_and_upload_video(video_url)
        
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
        
        if prompt:
            payload["input"]["prompt"] = prompt[:2500]
        
        try:
            logger.info(f"="*70)
            logger.info(f"🎯 СОЗДАНИЕ ЗАДАЧИ MOTION CONTROL")
            logger.info(f"Full Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            logger.info(f"="*70)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=30) as response:
                    response_text = await response.text()
                    
                    logger.info(f"📥 API Response: {response_text}")
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Ошибка парсинга JSON: {e}")
                        return None
                    
                    if result.get("code") == 200 and result.get("data", {}).get("taskId"):
                        task_id = result["data"]["taskId"]
                        logger.info(f"✅ Task ID: {task_id}")
                        return task_id
                    else:
                        logger.error(f"❌ Ошибка создания задачи:")
                        logger.error(f"{json.dumps(result, indent=2)}")
                        return None
        
        except Exception as e:
            logger.error(f"❌ Exception в create_task: {e}", exc_info=True)
            return None
    
    async def get_task_status(self, task_id: str):
        url = f"{self.base_url}/recordInfo"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"taskId": task_id}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params, timeout=30) as response:
                    result = await response.json()
                    if result.get("code") == 200 and result.get("data"):
                        return result["data"]
                    return None
        except Exception as e:
            logger.error(f"Ошибка get_task_status: {e}")
            return None
    
    async def wait_for_result(self, task_id: str, max_attempts: int = 120, delay: int = 10):
        logger.info(f"⏳ Ожидание завершения: Task ID {task_id}")
        
        for attempt in range(max_attempts):
            data = await self.get_task_status(task_id)
            
            if not data:
                await asyncio.sleep(delay)
                continue
            
            state = data.get("state")
            logger.info(f"🔄 {attempt + 1}/{max_attempts}: {state}")
            
            if state == "success":
                result_json = data.get("resultJson")
                if result_json:
                    try:
                        result_data = json.loads(result_json)
                        video_urls = result_data.get("resultUrls", [])
                        if video_urls:
                            logger.info(f"✅ Готово: {video_urls[0]}")
                            return video_urls[0]
                    except:
                        pass
                return None
            
            elif state == "fail":
                logger.error(f"❌ Провал: {data.get('failMsg')}")
                if "moderation" in str(data.get('failMsg')).lower():
                    return "MODERATION_ERROR"
                return None
            
            await asyncio.sleep(delay)
        
        logger.error("⏱️ Timeout")
        return None