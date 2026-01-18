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
        """Создает задачу на генерацию с управлением движением"""
        url = f"{self.base_url}/createTask"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        logger.info(f"📤 Создание задачи Motion Control...")
        logger.info(f"Image URL: {image_url}")
        logger.info(f"Video URL: {video_url}")
        
        payload = {
            "model": self.model,
            "input": {
                "input_urls": [image_url],
                "video_urls": [video_url],
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
                fail_msg = data.get('failMsg', '')
                logger.error(f"❌ Провал: {fail_msg}")
                
                # Проверяем разные типы ошибок
                fail_msg_lower = fail_msg.lower()
                if "moderation" in fail_msg_lower:
                    return "MODERATION_ERROR"
                elif "format" in fail_msg_lower or "unsupported" in fail_msg_lower:
                    return "FORMAT_ERROR"
                
                return None
            
            await asyncio.sleep(delay)
        
        logger.error("⏱️ Timeout")
        return None