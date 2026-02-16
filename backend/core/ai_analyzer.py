"""
GVIC AI Analyzer - 질문 목적과 기대 결과에 맞춘 AI 분석
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

ANALYSIS_PROMPT = """당신은 GVIC 시그널 분석 전문가입니다.

사용자가 특정 목적으로 시그널(텍스트/문서)을 분석 요청했습니다.

## 분석 요청 정보
- **질문 목적**: {purpose}
- **기대 결과**: {expected_result}

## 분석할 시그널
{content}

---

위 시그널을 분석하여 다음을 수행하세요:

1. **질문 목적에 맞는 분석**: 사용자가 왜 이 질문을 하는지 이해하고, 그에 맞는 관점에서 분석
2. **기대 결과 제공**: 사용자가 원하는 형태의 결과를 구체적으로 제공
3. **추가 인사이트**: 사용자가 요청하지 않았지만 알면 도움이 될 정보

반드시 다음 JSON 형식으로만 응답하세요:
{{
  "analysis_summary": "분석 요약 (2-3문장)",
  
  "purpose_analysis": {{
    "interpretation": "질문 목적에 대한 해석",
    "findings": "목적에 맞는 분석 결과 (상세히)",
    "perspective": "이 자료가 취하고 있는 관점 분석"
  }},
  
  "expected_result": {{
    "answer": "기대 결과에 대한 직접적인 답변 (상세히)",
    "evidence": ["근거1", "근거2", "근거3"],
    "objectivity_score": 0.0-1.0,
    "objectivity_reason": "객관성 평가 이유"
  }},
  
  "additional_insights": [
    {{
      "insight": "추가 인사이트",
      "relevance": "왜 이 정보가 도움이 되는지"
    }}
  ],
  
  "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
  
  "signal_category": "wanted|unwanted|null",
  "confidence": 0.0-1.0
}}
"""

class GVICAnalyzer:
    """GVIC AI 분석기"""
    
    def __init__(self):
        self.llm = None
        if EMERGENT_LLM_KEY:
            self.llm = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id="gvic-analyzer",
                system_message="You are a GVIC signal analysis expert."
            ).with_model("gemini", "gemini-2.0-flash")
    
    async def analyze(self, content: str, purpose: str = "", expected_result: str = "") -> Dict[str, Any]:
        """시그널 분석 수행"""
        
        if not self.llm:
            return {
                "success": False,
                "error": "AI 분석 서비스가 설정되지 않았습니다",
                "analysis_summary": "AI 분석을 수행할 수 없습니다."
            }
        
        # 목적과 기대 결과가 없으면 기본값 설정
        if not purpose:
            purpose = "이 시그널의 의미와 특징을 파악하고 싶습니다"
        if not expected_result:
            expected_result = "시그널에 대한 종합적인 분석 결과"
        
        prompt = ANALYSIS_PROMPT.format(
            purpose=purpose,
            expected_result=expected_result,
            content=content[:5000]  # 최대 5000자
        )
        
        try:
            response = await self.llm.send_async(
                message=UserMessage(text=prompt)
            )
            
            # JSON 파싱
            response_text = response.text.strip()
            
            # ```json ``` 블록 제거
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            result = json.loads(response_text)
            result["success"] = True
            return result
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"AI 응답 파싱 오류: {str(e)}",
                "raw_response": response_text if 'response_text' in dir() else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"AI 분석 오류: {str(e)}"
            }

# 싱글톤 인스턴스
_analyzer = None

def get_analyzer() -> GVICAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = GVICAnalyzer()
    return _analyzer

async def analyze_signal(content: str, purpose: str = "", expected_result: str = "") -> Dict[str, Any]:
    """시그널 분석 (편의 함수)"""
    analyzer = get_analyzer()
    return await analyzer.analyze(content, purpose, expected_result)
