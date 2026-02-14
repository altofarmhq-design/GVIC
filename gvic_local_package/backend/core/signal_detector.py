"""
GVIC Signal Detector - AI 기반 시그널 유형 감지 및 특징 추출
로컬 환경용 (OpenAI API 사용)
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

# OpenAI API 키 (로컬 환경용)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 시그널 유형 정의
SIGNAL_TYPES = {
    "product_review": "상품/서비스 후기",
    "requirement": "요구사항/기능요청",
    "complaint": "불만/클레임",
    "inquiry": "문의/질문",
    "news": "뉴스/기사",
    "feedback": "피드백/제안",
    "conversation": "일상대화",
    "data": "데이터/수치",
    "unknown": "분류불가"
}

SYSTEM_PROMPT = """당신은 GVIC 시그널 분석 엔진입니다.
입력된 텍스트를 분석하여 다음을 수행합니다:

1. 시그널 유형 감지: 이 텍스트가 무엇인지 파악
2. 시그널 특징 추출: 텍스트에서 발견되는 모든 의미있는 시그널을 추출
3. 감성 및 맥락 분석: 각 시그널의 감성과 숨겨진 의미 파악

반드시 다음 JSON 형식으로만 응답하세요:
{
  "signal_type": "product_review|requirement|complaint|inquiry|news|feedback|conversation|data|unknown",
  "signal_type_confidence": 0.0-1.0,
  "signal_type_reason": "왜 이 유형으로 판단했는지",
  
  "discovered_signals": [
    {
      "text": "원문에서 발견된 시그널 텍스트",
      "type": "시그널 종류 (예: 효과, 가격, 서비스, 품질, 요청, 불만 등)",
      "sentiment": "positive|negative|neutral|mixed",
      "intensity": 0.0-1.0,
      "context": "이 시그널의 맥락 설명",
      "hidden_meaning": "표면적 의미 외에 숨겨진 의미 (있다면)"
    }
  ],
  
  "overall_sentiment": "positive|negative|neutral|mixed",
  "key_themes": ["주요 테마1", "주요 테마2"],
  "summary": "전체 내용 요약 (1-2문장)",
  
  "applicable_perspectives": {
    "society": true|false,
    "production": true|false,
    "consumer": true|false
  },
  "perspective_relevance": "3관점 분석이 적합한지와 그 이유"
}"""


class GVICSignalDetector:
    """GVIC AI 기반 시그널 감지기 (로컬 환경용 - OpenAI API)"""
    
    def __init__(self):
        self.api_key = OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment. Please add it to .env file.")
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def detect_and_extract(self, text: str, session_id: str = "gvic_detector") -> Dict[str, Any]:
        """
        텍스트에서 시그널 유형 감지 및 특징 추출
        """
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"다음 텍스트를 분석해주세요:\n\n{text}"}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            try:
                json_str = response_text
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0]
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                
                result = json.loads(json_str.strip())
                result["raw_response"] = response_text
                result["success"] = True
                return result
                
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "error": "JSON 파싱 실패",
                    "raw_response": response_text,
                    "signal_type": "unknown",
                    "discovered_signals": []
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "signal_type": "unknown",
                "discovered_signals": []
            }
    
    async def detect_type_only(self, text: str) -> Dict[str, Any]:
        """시그널 유형만 빠르게 감지"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": """입력 텍스트의 유형을 판단하세요.
반드시 JSON으로만 응답:
{"type": "product_review|requirement|complaint|inquiry|news|feedback|conversation|data|unknown", "confidence": 0.0-1.0, "reason": "이유"}"""},
                    {"role": "user", "content": text[:500]}
                ],
                temperature=0.2,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content
            
            try:
                json_str = response_text
                if "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                return json.loads(json_str.strip())
            except:
                return {"type": "unknown", "confidence": 0, "reason": "파싱 실패"}
                
        except Exception as e:
            return {"type": "unknown", "confidence": 0, "reason": str(e)}


async def test_detector():
    detector = GVICSignalDetector()
    test_cases = [
        "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요.",
    ]
    for text in test_cases:
        print(f"\n입력: {text[:50]}...")
        result = await detector.detect_and_extract(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_detector())
