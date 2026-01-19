import aiohttp
import asyncio
import json
from typing import Optional
from config import KIE_API_KEY


class NanoBananaEditClient:
    """Клиент для работы с google/nano-banana-edit (для трендов)"""
    
    def __init__(self):
        self.api_key = KIE_API_KEY
        self.base_url = "https://api.kie.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def create_edit_task(self, prompt: str, image_urls: list, image_size: str = "9:16", output_format: str = "png") -> Optional[str]:
        """Создаёт задачу на редактирование через Nano Banana Edit"""
        url = f"{self.base_url}/api/v1/jobs/createTask"
        
        payload = {
            "model": "google/nano-banana-edit",
            "input": {
                "prompt": prompt,
                "image_urls": image_urls,
                "image_size": image_size,
                "output_format": output_format
            }
        }
        
        print(f"📤 Создание задачи Nano Banana Edit")
        print(f"Model: google/nano-banana-edit")
        print(f"Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        try:
            timeout = aiohttp.ClientTimeout(total=60)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, headers=self.headers, json=payload) as response:
                    response_text = await response.text()
                    print(f"Response: {response_text}")
                    
                    data = await response.json()
                    
                    if data.get("code") == 200:
                        task_id = data.get("data", {}).get("taskId")
                        print(f"✅ Task ID: {task_id}")
                        return task_id
                    else:
                        print(f"❌ Error: {data}")
                        return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Получает статус задачи"""
        url = f"{self.base_url}/api/v1/jobs/recordInfo"
        params = {"taskId": task_id}
        
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url, headers=self.headers, params=params) as response:
                    data = await response.json()
                    
                    if data.get("code") == 200:
                        return data.get("data")
                    else:
                        return None
        except Exception as e:
            print(f"❌ Error getting status: {e}")
            return None
    
    async def wait_for_result(self, task_id: str, max_attempts: int = 120, delay: int = 5) -> Optional[str]:
        """Ожидает завершения редактирования"""
        print(f"⏳ Waiting for task {task_id}...")
        
        for attempt in range(max_attempts):
            status_data = await self.get_task_status(task_id)
            
            if not status_data:
                await asyncio.sleep(delay)
                continue
            
            state = status_data.get("state")
            
            if attempt % 6 == 0:
                print(f"⏳ Check {attempt + 1}/{max_attempts}: {state}")
            
            if state == "success":
                print("🎉 Success!")
                
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
                            print(f"🖼 Image: {image_url}")
                            return image_url
                    except Exception as e:
                        print(f"Error parsing result: {e}")
                
                return None
            
            elif state == "fail":
                fail_msg = status_data.get("failMsg", "Unknown error")
                fail_code = status_data.get("failCode", "")
                print(f"❌ Failed: {fail_msg}")
                
                fail_msg_lower = str(fail_msg).lower()
                if ("nsfw" in fail_msg_lower or "inappropriate" in fail_msg_lower or "prominent people" in fail_msg_lower or "violating content" in fail_msg_lower or str(fail_code) in ["400", "422", "500"]):
                    return "MODERATION_ERROR"
                
                return None
            
            await asyncio.sleep(delay)
        
        print("❌ Timeout")
        return None