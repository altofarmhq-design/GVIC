"""
GVIC 고유 분석 엔진
- AI 원시 결과를 5:3:2 결이론으로 재가공
- 크로스 분석: 기존 자산과 비교/연결
- 인사이트 도출: 패턴 발견
- 가치 평가: 다차원 스코어링
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import os

router = APIRouter(prefix="/api/gvic", tags=["gvic-analyzer"])
logger = logging.getLogger(__name__)

# ==================== 5:3:2 결이론 상수 ====================
PUBLIC_RATIO = 0.5      # 공공 환원 (5/10)
OPERATION_RATIO = 0.3   # 운영 (3/10)
MANAGEMENT_RATIO = 0.2  # 기획/관리 (2/10)

# ==================== Models ====================

class GVICAnalysisRequest(BaseModel):
    """GVIC 분석 요청"""
    signal_id: str
    content: str
    ai_analysis: Dict[str, Any]  # AI 원시 분석 결과
    purpose: str = ""
    context: str = ""

class ValueBreakdown532(BaseModel):
    """5:3:2 가치 분해"""
    public_value: float = Field(description="공공 기여 가치 (5)")
    operation_value: float = Field(description="운영 활용 가치 (3)")
    management_value: float = Field(description="기획/관리 가치 (2)")
    total_value: float = Field(description="총 가치")

class GVICInterpretation(BaseModel):
    """GVIC 결이론 해석"""
    # 공공 관점 (5)
    public_contribution: str = Field(description="공공 기여 분석")
    public_beneficiaries: List[str] = Field(description="혜택 받을 대상")
    public_score: float = Field(description="공공 기여 점수 0-100")
    
    # 운영 관점 (3)
    operation_utility: str = Field(description="운영 활용 분석")
    operation_applications: List[str] = Field(description="활용 가능 영역")
    operation_score: float = Field(description="운영 활용 점수 0-100")
    
    # 기획/관리 관점 (2)
    management_potential: str = Field(description="기획 가치 분석")
    management_opportunities: List[str] = Field(description="기획 기회")
    management_score: float = Field(description="기획 가치 점수 0-100")

class GVICAnalysisResult(BaseModel):
    """GVIC 분석 결과"""
    signal_id: str
    original_ai_summary: str
    gvic_interpretation: GVICInterpretation
    value_breakdown: ValueBreakdown532
    gvic_insight: str  # GVIC 관점 종합 인사이트
    recommended_actions: List[str]  # 추천 액션

# ==================== GVIC 분석 엔진 ====================

async def analyze_with_gvic_lens(
    content: str,
    ai_analysis: Dict[str, Any],
    purpose: str = ""
) -> Dict[str, Any]:
    """
    AI 분석 결과를 GVIC 결이론(5:3:2) 관점으로 재해석
    
    5 (공공): 이 정보가 커뮤니티/이용자들에게 어떤 가치를 줄 수 있는가?
    3 (운영): 플랫폼 운영/발전에 어떻게 활용될 수 있는가?
    2 (기획): 새로운 서비스/비즈니스 기획에 어떤 기회를 제공하는가?
    """
    
    # AI 원시 결과 추출
    ai_summary = ai_analysis.get("analysis_summary", "")
    ai_confidence = ai_analysis.get("confidence", 0.5)
    ai_keywords = ai_analysis.get("keywords", [])
    ai_category = ai_analysis.get("signal_category", "general")
    
    # LLM을 사용하여 GVIC 관점 분석
    from core.ai_analyzer import get_llm_client
    
    gvic_prompt = f"""
당신은 GVIC(결이론 기반 가치 분석) 전문가입니다.
다음 콘텐츠와 AI 분석 결과를 5:3:2 결이론 관점에서 재해석해주세요.

[원본 콘텐츠]
{content[:2000]}

[AI 분석 결과]
{ai_summary}

[분석 목적]
{purpose or "일반 분석"}

=== 5:3:2 결이론 관점 분석 ===

다음 JSON 형식으로 응답해주세요:
{{
    "public_analysis": {{
        "contribution": "이 정보가 이용자/주주/구성원에게 줄 수 있는 구체적 가치 (2-3문장)",
        "beneficiaries": ["혜택 받을 대상 목록", "최대 5개"],
        "score": 0-100 (공공 기여 점수)
    }},
    "operation_analysis": {{
        "utility": "플랫폼 운영/발전에 활용할 수 있는 방법 (2-3문장)",
        "applications": ["활용 가능 영역 목록", "최대 5개"],
        "score": 0-100 (운영 활용 점수)
    }},
    "management_analysis": {{
        "potential": "새로운 서비스/비즈니스 기획 기회 (2-3문장)",
        "opportunities": ["기획 기회 목록", "최대 5개"],
        "score": 0-100 (기획 가치 점수)
    }},
    "gvic_insight": "5:3:2 관점을 종합한 GVIC 인사이트 (3-4문장)",
    "recommended_actions": ["GVIC 관점에서 권장하는 액션 목록", "최대 5개"]
}}
"""
    
    try:
        client = get_llm_client()
        response = await client.chat.completions.create(
            model="gemini-2.0-flash",
            messages=[
                {"role": "system", "content": "당신은 GVIC 결이론 전문 분석가입니다. 항상 JSON 형식으로만 응답합니다."},
                {"role": "user", "content": gvic_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # JSON 파싱
        import json
        import re
        
        # JSON 블록 추출
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            gvic_result = json.loads(json_match.group())
        else:
            raise ValueError("JSON not found in response")
        
        # 점수 추출
        public_score = gvic_result.get("public_analysis", {}).get("score", 50)
        operation_score = gvic_result.get("operation_analysis", {}).get("score", 50)
        management_score = gvic_result.get("management_analysis", {}).get("score", 50)
        
        # 5:3:2 가중 평균 계산
        weighted_total = (
            public_score * PUBLIC_RATIO +
            operation_score * OPERATION_RATIO +
            management_score * MANAGEMENT_RATIO
        )
        
        # 가치 분해 계산
        value_breakdown = {
            "public_value": weighted_total * PUBLIC_RATIO,
            "operation_value": weighted_total * OPERATION_RATIO,
            "management_value": weighted_total * MANAGEMENT_RATIO,
            "total_value": weighted_total
        }
        
        return {
            "success": True,
            "original_ai_summary": ai_summary,
            "gvic_interpretation": {
                "public_contribution": gvic_result.get("public_analysis", {}).get("contribution", ""),
                "public_beneficiaries": gvic_result.get("public_analysis", {}).get("beneficiaries", []),
                "public_score": public_score,
                "operation_utility": gvic_result.get("operation_analysis", {}).get("utility", ""),
                "operation_applications": gvic_result.get("operation_analysis", {}).get("applications", []),
                "operation_score": operation_score,
                "management_potential": gvic_result.get("management_analysis", {}).get("potential", ""),
                "management_opportunities": gvic_result.get("management_analysis", {}).get("opportunities", []),
                "management_score": management_score
            },
            "value_breakdown_532": value_breakdown,
            "gvic_insight": gvic_result.get("gvic_insight", ""),
            "recommended_actions": gvic_result.get("recommended_actions", [])
        }
        
    except Exception as e:
        logger.error(f"GVIC analysis error: {e}")
        # 폴백: 기본 분석
        return generate_fallback_gvic_analysis(content, ai_analysis, ai_confidence)


def generate_fallback_gvic_analysis(
    content: str,
    ai_analysis: Dict[str, Any],
    confidence: float
) -> Dict[str, Any]:
    """LLM 실패 시 규칙 기반 GVIC 분석"""
    
    content_lower = content.lower()
    ai_summary = ai_analysis.get("analysis_summary", "")
    
    # 키워드 기반 점수 계산
    public_keywords = ["공유", "커뮤니티", "도움", "정보", "리뷰", "후기", "팁", "가이드"]
    operation_keywords = ["데이터", "분석", "통계", "트렌드", "패턴", "시스템"]
    management_keywords = ["사업", "비즈니스", "기획", "전략", "수익", "시장", "기회"]
    
    public_score = 50 + sum(10 for kw in public_keywords if kw in content_lower)
    operation_score = 50 + sum(10 for kw in operation_keywords if kw in content_lower)
    management_score = 50 + sum(10 for kw in management_keywords if kw in content_lower)
    
    # 점수 정규화 (0-100)
    public_score = min(100, public_score)
    operation_score = min(100, operation_score)
    management_score = min(100, management_score)
    
    weighted_total = (
        public_score * PUBLIC_RATIO +
        operation_score * OPERATION_RATIO +
        management_score * MANAGEMENT_RATIO
    )
    
    return {
        "success": True,
        "original_ai_summary": ai_summary,
        "gvic_interpretation": {
            "public_contribution": "이 콘텐츠는 커뮤니티 구성원들에게 유용한 정보를 제공할 수 있습니다.",
            "public_beneficiaries": ["GVIC 이용자", "관련 분야 관심자"],
            "public_score": public_score,
            "operation_utility": "플랫폼 데이터 풍부화 및 분석 자료로 활용 가능합니다.",
            "operation_applications": ["데이터 축적", "분석 자료"],
            "operation_score": operation_score,
            "management_potential": "향후 서비스 기획을 위한 참고 자료로 활용할 수 있습니다.",
            "management_opportunities": ["서비스 개선", "기능 확장"],
            "management_score": management_score
        },
        "value_breakdown_532": {
            "public_value": weighted_total * PUBLIC_RATIO,
            "operation_value": weighted_total * OPERATION_RATIO,
            "management_value": weighted_total * MANAGEMENT_RATIO,
            "total_value": weighted_total
        },
        "gvic_insight": f"이 시그널은 5:3:2 결이론 관점에서 총 {weighted_total:.1f}점의 가치를 가집니다.",
        "recommended_actions": ["자산으로 등록", "관련 모듈 검토"]
    }


# ==================== API Endpoints ====================

@router.post("/analyze")
async def gvic_analyze_signal(request: GVICAnalysisRequest):
    """
    시그널을 GVIC 결이론(5:3:2)으로 분석
    
    AI 분석 결과를 받아서:
    1. 공공 기여 관점 (5) 분석
    2. 운영 활용 관점 (3) 분석  
    3. 기획/관리 관점 (2) 분석
    4. 종합 인사이트 도출
    """
    result = await analyze_with_gvic_lens(
        content=request.content,
        ai_analysis=request.ai_analysis,
        purpose=request.purpose
    )
    
    result["signal_id"] = request.signal_id
    
    # DB에 GVIC 분석 결과 저장
    from server import db
    
    gvic_record = {
        "signal_id": request.signal_id,
        "analysis_type": "gvic_532",
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.gvic_analyses.update_one(
        {"signal_id": request.signal_id},
        {"$set": gvic_record},
        upsert=True
    )
    
    return result


@router.get("/analysis/{signal_id}")
async def get_gvic_analysis(signal_id: str):
    """저장된 GVIC 분석 결과 조회"""
    from server import db
    
    analysis = await db.gvic_analyses.find_one(
        {"signal_id": signal_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="GVIC 분석 결과가 없습니다")
    
    return analysis


@router.post("/reanalyze/{signal_id}")
async def reanalyze_with_gvic(signal_id: str):
    """기존 시그널을 GVIC 관점으로 재분석"""
    from server import db
    
    # 시그널 조회
    signal = await db.pipeline_signals.find_one(
        {"signal_id": signal_id},
        {"_id": 0}
    )
    
    if not signal:
        raise HTTPException(status_code=404, detail="시그널을 찾을 수 없습니다")
    
    content = signal.get("content", "")
    ai_analysis = signal.get("metadata", {}).get("ai_analysis", {})
    purpose = signal.get("metadata", {}).get("purpose", "")
    
    # GVIC 분석 수행
    result = await analyze_with_gvic_lens(
        content=content,
        ai_analysis=ai_analysis,
        purpose=purpose
    )
    
    result["signal_id"] = signal_id
    
    # 결과 저장
    gvic_record = {
        "signal_id": signal_id,
        "analysis_type": "gvic_532",
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.gvic_analyses.update_one(
        {"signal_id": signal_id},
        {"$set": gvic_record},
        upsert=True
    )
    
    # 시그널에 GVIC 분석 결과 연결
    await db.pipeline_signals.update_one(
        {"signal_id": signal_id},
        {"$set": {"gvic_analysis": result}}
    )
    
    return result
