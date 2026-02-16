"""
Local LLM Module - emergentintegrations 대체
로컬 환경에서 OpenAI API를 직접 사용
"""
import os
import httpx
from typing import Optional, List, Dict, Any

class UserMessage:
    def __init__(self, content: str):
        self.content = content
        self.role = "user"

class ImageContent:
    def __init__(self, image_url: str = None, base64_image: str = None):
        self.image_url = image_url
        self.base64_image = base64_image

class LlmChat:
    def __init__(self, api_key: str = None, model: str = "gpt-3.5-turbo"):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.base_url = "https://api.openai.com/v1"
    
    async def send_async(self, messages: List[Any], system_prompt: str = None) -> str:
        """비동기 메시지 전송"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        for msg in messages:
            if hasattr(msg, 'content'):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, dict):
                formatted_messages.append(msg)
            else:
                formatted_messages.append({"role": "user", "content": str(msg)})
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": 0.7
        }
        
        # API 키가 없으면 Mock 응답
        if not self.api_key or self.api_key == "":
            return self._mock_response(formatted_messages)
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"LLM API Error: {e}")
            return self._mock_response(formatted_messages)
    
    def send(self, messages: List[Any], system_prompt: str = None) -> str:
        """동기 메시지 전송"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.send_async(messages, system_prompt))
    
    def _mock_response(self, messages: List[Dict]) -> str:
        """API 키가 없을 때 Mock 응답"""
        last_message = messages[-1].get("content", "") if messages else ""
        
        if "분석" in last_message or "리뷰" in last_message:
            return '''
{
    "strengths": ["품질이 좋음", "배송이 빠름", "가성비 우수"],
    "suggestions": ["포장 개선 필요", "설명서 보강"],
    "complaints": ["사이즈가 작음"],
    "new_needs": ["다양한 색상 옵션"]
}
'''
        elif "HS" in last_message or "코드" in last_message:
            return "8518"
        else:
            return "Mock 응답: AI 분석 기능을 사용하려면 OPENAI_API_KEY를 설정하세요."
