"""
LL: INTELLIGENCE - 의도 특허 모듈
AI 분석 및 의도 추출
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/ll", tags=["LL:INTELLIGENCE"])
logger = logging.getLogger(__name__)

class IntentAnalysisRequest(BaseModel):
    """의도 분석 요청"""
    content: str
    context: str = ""
    analysis_depth: str = "standard"  # quick, standard, deep

class ExtractedIntent(BaseModel):
    """추출된 의도"""
    primary_intent: str
    secondary_intents: List[str]
    confidence: float
    keywords: List[str]
    sentiment: str
    urgency: str

# ==================== 의도 분석 ====================

@router.post("/analyze")
async def analyze_intent(request: IntentAnalysisRequest):
    """시그널에서 의도 추출 및 분석"""
    from core.ai_analyzer import analyze_signal
    
    # AI 분석 수행
    ai_result = await analyze_signal(
        content=request.content,
        purpose=request.context,
        expected_result="의도 분석",
        analysis_type="general"
    )
    
    # 의도 추출
    intent_data = {
        "primary_intent": ai_result.get("signal_category", "general"),
        "secondary_intents": [],
        "confidence": ai_result.get("confidence", 0.5),
        "keywords": ai_result.get("keywords", []),
        "sentiment": ai_result.get("sentiment", "neutral"),
        "urgency": "normal",
        "analysis_summary": ai_result.get("analysis_summary", ""),
        "purpose_interpretation": ai_result.get("purpose_interpretation", "")
    }
    
    # 긴급도 판단
    urgent_keywords = ["긴급", "급함", "즉시", "빨리", "urgent", "asap"]
    if any(kw in request.content.lower() for kw in urgent_keywords):
        intent_data["urgency"] = "high"
    
    return {
        "success": True,
        "intent": intent_data,
        "raw_analysis": ai_result
    }

@router.post("/classify")
async def classify_signal(request: IntentAnalysisRequest):
    """시그널 분류 (wanted/unwanted/null)"""
    from core.ai_analyzer import analyze_signal
    
    ai_result = await analyze_signal(
        content=request.content,
        purpose="시그널 분류",
        expected_result="wanted/unwanted/null 분류",
        analysis_type="general"
    )
    
    category = ai_result.get("signal_category", "wanted")
    
    return {
        "success": True,
        "classification": category,
        "confidence": ai_result.get("confidence", 0.5),
        "reasoning": ai_result.get("analysis_summary", "")
    }

@router.get("/intent-types")
async def get_intent_types():
    """지원하는 의도 유형 목록"""
    intent_types = [
        {"type": "wanted", "name": "원하는 것", "description": "직접 분석 대상", "color": "blue"},
        {"type": "unwanted", "name": "자산화 대상", "description": "가치 추출 대상", "color": "amber"},
        {"type": "null", "name": "Null", "description": "무시 대상", "color": "gray"},
        {"type": "question", "name": "질문", "description": "답변 필요", "color": "green"},
        {"type": "request", "name": "요청", "description": "액션 필요", "color": "purple"},
        {"type": "feedback", "name": "피드백", "description": "개선 의견", "color": "orange"}
    ]
    return {"success": True, "types": intent_types}

@router.get("/stats")
async def get_intelligence_stats():
    """의도 분석 통계"""
    from server import db
    
    # 카테고리별 통계
    pipeline = [
        {"$group": {
            "_id": "$category",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.pipeline_signals.aggregate(pipeline).to_list(100)
    category_stats = {r["_id"]: r["count"] for r in results if r["_id"]}
    
    # 감성 분석 통계
    sentiment_pipeline = [
        {"$group": {
            "_id": "$metadata.ai_analysis.sentiment",
            "count": {"$sum": 1}
        }}
    ]
    
    sentiment_results = await db.pipeline_signals.aggregate(sentiment_pipeline).to_list(100)
    sentiment_stats = {r["_id"]: r["count"] for r in sentiment_results if r["_id"]}
    
    return {
        "success": True,
        "category_distribution": category_stats,
        "sentiment_distribution": sentiment_stats
    }
