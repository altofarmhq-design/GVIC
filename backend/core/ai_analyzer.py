"""
GVIC AI Analyzer - 다양한 분석 유형 지원
- 일반 분석
- 코드 분석
- 특허/아이디어 분석
"""
import os
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# ============== 분석 유형별 프롬프트 ==============

# 일반 분석 프롬프트
GENERAL_ANALYSIS_PROMPT = """당신은 GVIC 시그널 분석 전문가입니다.

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
  "analysis_type": "general",
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

# 코드 분석 프롬프트
CODE_ANALYSIS_PROMPT = """당신은 시니어 소프트웨어 엔지니어이자 코드 리뷰 전문가입니다.

사용자가 코드를 분석 요청했습니다.

## 분석 요청 정보
- **질문 목적**: {purpose}
- **기대 결과**: {expected_result}
- **파일 정보**: {file_info}

## 분석할 코드
```
{content}
```

---

위 코드를 철저히 분석하여 다음을 수행하세요:

1. **문법/컴파일 오류 검출**: 코드에서 발견되는 문법 오류나 컴파일 오류
2. **버그 가능성 분석**: 런타임 오류나 논리적 버그가 될 수 있는 부분
3. **코드 품질 평가**: 가독성, 유지보수성, 효율성 평가
4. **개선 제안**: 리팩토링 및 최적화 제안
5. **보안 취약점**: 잠재적 보안 문제

반드시 다음 JSON 형식으로만 응답하세요:
{{
  "analysis_type": "code",
  "analysis_summary": "코드 분석 요약 (2-3문장)",
  
  "syntax_errors": [
    {{
      "line": "라인 번호 또는 위치",
      "error": "오류 내용",
      "suggestion": "수정 제안"
    }}
  ],
  
  "potential_bugs": [
    {{
      "location": "위치",
      "issue": "문제 설명",
      "severity": "high|medium|low",
      "fix": "수정 방법"
    }}
  ],
  
  "code_quality": {{
    "readability_score": 0.0-1.0,
    "maintainability_score": 0.0-1.0,
    "efficiency_score": 0.0-1.0,
    "overall_score": 0.0-1.0,
    "comments": "품질에 대한 종합 의견"
  }},
  
  "improvements": [
    {{
      "category": "refactoring|optimization|style|structure",
      "suggestion": "개선 제안",
      "priority": "high|medium|low",
      "example": "개선된 코드 예시 (선택)"
    }}
  ],
  
  "security_issues": [
    {{
      "vulnerability": "취약점 유형",
      "description": "설명",
      "severity": "critical|high|medium|low",
      "mitigation": "해결 방법"
    }}
  ],
  
  "best_practices": ["준수하고 있는 모범 사례들"],
  
  "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
  
  "signal_category": "wanted",
  "confidence": 0.0-1.0
}}
"""

# 특허/아이디어 분석 프롬프트
PATENT_IDEA_ANALYSIS_PROMPT = """당신은 특허 전문가이자 기술 혁신 컨설턴트입니다.

사용자가 특허 또는 아이디어를 분석 요청했습니다.

## 분석 요청 정보
- **질문 목적**: {purpose}
- **기대 결과**: {expected_result}

## 분석할 특허/아이디어
{content}

---

위 특허/아이디어를 철저히 분석하여 다음을 수행하세요:

1. **핵심 개념 추출**: 이 아이디어의 핵심이 무엇인지
2. **신규성/독창성 평가**: 기존 기술 대비 새로운 점
3. **기술적 실현 가능성**: 현재 기술로 구현 가능한지
4. **시장성 및 응용 분야**: 어디에 활용될 수 있는지
5. **발전 가능성**: 향후 발전 방향

반드시 다음 JSON 형식으로만 응답하세요:
{{
  "analysis_type": "patent_idea",
  "analysis_summary": "특허/아이디어 분석 요약 (2-3문장)",
  
  "core_concept": {{
    "main_idea": "핵심 아이디어 (한 문장)",
    "key_elements": ["핵심 요소1", "핵심 요소2", "핵심 요소3"],
    "technical_domain": "기술 분야",
    "problem_solved": "해결하고자 하는 문제"
  }},
  
  "novelty_assessment": {{
    "novelty_score": 0.0-1.0,
    "innovative_aspects": ["혁신적인 부분1", "혁신적인 부분2"],
    "similar_technologies": ["유사 기술1", "유사 기술2"],
    "differentiation": "기존 기술과의 차별점"
  }},
  
  "feasibility": {{
    "technical_feasibility_score": 0.0-1.0,
    "current_technology_fit": "현재 기술 수준과의 적합성",
    "implementation_challenges": ["구현 시 도전과제1", "도전과제2"],
    "required_resources": ["필요 자원1", "필요 자원2"],
    "timeline_estimate": "예상 개발 기간"
  }},
  
  "market_potential": {{
    "market_score": 0.0-1.0,
    "target_markets": ["타겟 시장1", "타겟 시장2"],
    "application_areas": ["응용 분야1", "응용 분야2"],
    "competitive_advantage": "경쟁 우위",
    "monetization_potential": "수익화 가능성"
  }},
  
  "future_development": {{
    "evolution_paths": ["발전 방향1", "발전 방향2"],
    "enhancement_suggestions": ["개선 제안1", "개선 제안2"],
    "collaboration_opportunities": ["협력 기회1", "협력 기회2"]
  }},
  
  "risks_and_challenges": [
    {{
      "risk": "위험 요소",
      "impact": "high|medium|low",
      "mitigation": "완화 방안"
    }}
  ],
  
  "overall_evaluation": {{
    "innovation_score": 0.0-1.0,
    "viability_score": 0.0-1.0,
    "recommendation": "종합 추천 의견",
    "next_steps": ["다음 단계1", "다음 단계2"]
  }},
  
  "key_points": ["핵심 포인트1", "핵심 포인트2", "핵심 포인트3"],
  
  "signal_category": "wanted",
  "confidence": 0.0-1.0
}}
"""

# 분석 유형 정의
ANALYSIS_TYPES = {
    "general": {
        "name": "일반 분석",
        "icon": "📝",
        "description": "텍스트, 문서 등 일반적인 시그널 분석",
        "prompt": GENERAL_ANALYSIS_PROMPT
    },
    "code": {
        "name": "코드 분석",
        "icon": "💻",
        "description": "프로그램 코드 오류 검출 및 품질 분석",
        "prompt": CODE_ANALYSIS_PROMPT
    },
    "patent_idea": {
        "name": "특허/아이디어 분석",
        "icon": "💡",
        "description": "특허, 아이디어의 신규성 및 실현 가능성 평가",
        "prompt": PATENT_IDEA_ANALYSIS_PROMPT
    }
}

class GVICAnalyzer:
    """GVIC AI 분석기 - 다양한 분석 유형 지원"""
    
    def __init__(self):
        self.llm = None
        if EMERGENT_LLM_KEY:
            self.llm = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id="gvic-analyzer",
                system_message="You are a GVIC signal analysis expert who provides detailed analysis in JSON format."
            ).with_model("gemini", "gemini-2.0-flash")
    
    async def analyze(
        self, 
        content: str, 
        purpose: str = "", 
        expected_result: str = "",
        analysis_type: str = "general",
        file_info: str = ""
    ) -> Dict[str, Any]:
        """시그널 분석 수행"""
        
        if not self.llm:
            return {
                "success": False,
                "error": "AI 분석 서비스가 설정되지 않았습니다",
                "analysis_summary": "AI 분석을 수행할 수 없습니다."
            }
        
        # 분석 유형 검증
        if analysis_type not in ANALYSIS_TYPES:
            analysis_type = "general"
        
        # 기본값 설정
        if not purpose:
            if analysis_type == "code":
                purpose = "이 코드의 오류와 개선점을 파악하고 싶습니다"
            elif analysis_type == "patent_idea":
                purpose = "이 아이디어의 가치와 실현 가능성을 평가하고 싶습니다"
            else:
                purpose = "이 시그널의 의미와 특징을 파악하고 싶습니다"
        
        if not expected_result:
            if analysis_type == "code":
                expected_result = "코드 오류 수정 및 품질 개선 방안"
            elif analysis_type == "patent_idea":
                expected_result = "아이디어의 신규성과 시장성 평가"
            else:
                expected_result = "시그널에 대한 종합적인 분석 결과"
        
        # 프롬프트 생성
        prompt_template = ANALYSIS_TYPES[analysis_type]["prompt"]
        prompt = prompt_template.format(
            purpose=purpose,
            expected_result=expected_result,
            content=content[:8000],  # 코드는 더 길 수 있으므로 8000자
            file_info=file_info or "정보 없음"
        )
        
        try:
            response = await self.llm.send_message(
                UserMessage(text=prompt)
            )
            
            # JSON 파싱
            response_text = response.strip()
            
            # ```json ``` 블록 제거
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                # 첫 줄이 ```json 또는 ``` 형태인 경우
                start_idx = 1
                end_idx = -1
                if lines[-1].strip() == "```":
                    end_idx = -1
                response_text = "\n".join(lines[start_idx:end_idx])
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
            
            result = json.loads(response_text)
            result["success"] = True
            result["analysis_type"] = analysis_type
            result["analysis_type_info"] = ANALYSIS_TYPES[analysis_type]
            return result
            
        except json.JSONDecodeError as e:
            # JSON 파싱 실패 시 텍스트 응답 반환
            return {
                "success": True,
                "analysis_type": analysis_type,
                "analysis_summary": response_text[:500] if 'response_text' in dir() else "분석 완료",
                "raw_response": response_text if 'response_text' in dir() else None,
                "parse_error": str(e)
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

def get_analysis_types() -> Dict:
    """사용 가능한 분석 유형 반환"""
    return {
        k: {
            "name": v["name"],
            "icon": v["icon"],
            "description": v["description"]
        }
        for k, v in ANALYSIS_TYPES.items()
    }

async def analyze_signal(
    content: str, 
    purpose: str = "", 
    expected_result: str = "",
    analysis_type: str = "general",
    file_info: str = ""
) -> Dict[str, Any]:
    """시그널 분석 (편의 함수)"""
    analyzer = get_analyzer()
    return await analyzer.analyze(content, purpose, expected_result, analysis_type, file_info)
