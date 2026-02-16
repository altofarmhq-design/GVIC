"""
GVIC Signal Detector - AI 기반 시그널 유형 감지 및 특징 추출
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
from local_llm import LlmChat, UserMessage

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("OPENAI_API_KEY", "")

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
    """GVIC AI 기반 시그널 감지기"""
    
    def __init__(self):
        self.api_key = EMERGENT_LLM_KEY
        if not self.api_key:
            raise ValueError("EMERGENT_LLM_KEY not found in environment")
    
    async def detect_and_extract(self, text: str, session_id: str = "gvic_detector") -> Dict[str, Any]:
        """
        텍스트에서 시그널 유형 감지 및 특징 추출
        
        Args:
            text: 분석할 텍스트
            session_id: 세션 ID
            
        Returns:
            감지된 시그널 정보
        """
        try:
            chat = LlmChat(
                api_key=self.api_key,
                session_id=session_id,
                system_message=SYSTEM_PROMPT
            ).with_model("gemini", "gemini-3-flash-preview")
            
            user_message = UserMessage(
                text=f"다음 텍스트를 분석해주세요:\n\n{text}"
            )
            
            response = await chat.send_message(user_message)
            
            # JSON 파싱 시도
            try:
                # 응답에서 JSON 추출
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                
                result = json.loads(json_str.strip())
                result["raw_response"] = response
                result["success"] = True
                return result
                
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 텍스트 응답 반환
                return {
                    "success": False,
                    "error": "JSON 파싱 실패",
                    "raw_response": response,
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
            chat = LlmChat(
                api_key=self.api_key,
                session_id="gvic_type_detect",
                system_message="""입력 텍스트의 유형을 판단하세요.
반드시 JSON으로만 응답:
{"type": "product_review|requirement|complaint|inquiry|news|feedback|conversation|data|unknown", "confidence": 0.0-1.0, "reason": "이유"}"""
            ).with_model("gemini", "gemini-3-flash-preview")
            
            user_message = UserMessage(text=text[:500])  # 앞부분만 사용
            response = await chat.send_message(user_message)
            
            try:
                json_str = response
                if "```" in response:
                    json_str = response.split("```")[1].split("```")[0]
                    if json_str.startswith("json"):
                        json_str = json_str[4:]
                return json.loads(json_str.strip())
            except:
                return {"type": "unknown", "confidence": 0, "reason": "파싱 실패"}
                
        except Exception as e:
            return {"type": "unknown", "confidence": 0, "reason": str(e)}


# 테스트용 함수
async def test_detector():
    detector = GVICSignalDetector()
    
    test_cases = [
        "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요.",
        "실제 시그널이 어떻게 gvic에서 가공되고 결과를 얻게 되는 구나를 알 수 있어야 겠지.",
        "두 번째 구매할 때 2kg를 주문했는데 키로 수도 맛도 믿음이 안 갔는데. 사장님께서 직접 전화 주시고 친절하게 대응하시기에 미안함도 있고. 맛은 맛있어요. 그냥 그것에 만족할게요."
    ]
    
    for text in test_cases:
        print(f"\n{'='*60}")
        print(f"입력: {text[:50]}...")
        print("="*60)
        
        result = await detector.detect_and_extract(text)
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_detector())
