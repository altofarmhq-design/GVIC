"""
A: GATE - 게이트 특허 모듈
시그널 평가 및 필터링
5:3:2 분류 게이트
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/a", tags=["A:GATE"])
logger = logging.getLogger(__name__)

class GateRule(BaseModel):
    """게이트 규칙"""
    rule_id: str
    name: str
    condition: str
    action: str  # pass, block, route
    priority: int = 0

class SignalEvaluation(BaseModel):
    """시그널 평가 요청"""
    signal_id: str
    content: str
    metadata: Dict[str, Any] = {}

# ==================== 게이트 규칙 ====================

@router.get("/rules")
async def get_gate_rules():
    """게이트 규칙 목록"""
    rules = [
        {"rule_id": "r1", "name": "빈 콘텐츠 필터", "condition": "content.length < 5", "action": "block", "priority": 100},
        {"rule_id": "r2", "name": "스팸 필터", "condition": "spam_score > 0.8", "action": "block", "priority": 90},
        {"rule_id": "r3", "name": "중복 필터", "condition": "duplicate_score > 0.9", "action": "block", "priority": 80},
        {"rule_id": "r4", "name": "고가치 라우팅", "condition": "value_score > 0.7", "action": "route:priority", "priority": 50},
        {"rule_id": "r5", "name": "기본 통과", "condition": "true", "action": "pass", "priority": 0}
    ]
    return {"success": True, "rules": rules}

@router.post("/evaluate")
async def evaluate_signal(request: SignalEvaluation):
    """시그널 게이트 평가"""
    from server import db
    from gvic_analyzer import cross_analyze_signal
    
    evaluations = []
    passed = True
    route_to = None
    
    # 1. 빈 콘텐츠 체크
    if len(request.content.strip()) < 5:
        evaluations.append({"rule": "빈 콘텐츠 필터", "result": "blocked", "reason": "내용이 너무 짧음"})
        passed = False
    else:
        evaluations.append({"rule": "빈 콘텐츠 필터", "result": "passed"})
    
    # 2. 중복 체크 (크로스 분석 활용)
    if passed:
        try:
            cross_result = await cross_analyze_signal(
                signal_id=request.signal_id,
                content=request.content,
                keywords=[],
                category="general",
                max_related=5
            )
            
            duplicates = cross_result.get("potential_duplicates", [])
            if duplicates and duplicates[0].get("similarity_score", 0) > 0.9:
                evaluations.append({"rule": "중복 필터", "result": "warning", "reason": f"유사 자산 발견: {duplicates[0]['asset_id']}"})
            else:
                evaluations.append({"rule": "중복 필터", "result": "passed"})
        except:
            evaluations.append({"rule": "중복 필터", "result": "skipped", "reason": "분석 오류"})
    
    # 3. 가치 평가
    if passed:
        try:
            from gvic_analyzer import evaluate_asset_value
            valuation = await evaluate_asset_value(
                content=request.content,
                keywords=[],
                category="general"
            )
            
            total_score = valuation.get("total_score", 50)
            if total_score > 70:
                route_to = "priority"
                evaluations.append({"rule": "고가치 라우팅", "result": "routed", "destination": "priority", "score": total_score})
            else:
                evaluations.append({"rule": "가치 평가", "result": "passed", "score": total_score})
        except:
            evaluations.append({"rule": "가치 평가", "result": "skipped"})
    
    return {
        "success": True,
        "signal_id": request.signal_id,
        "passed": passed,
        "route_to": route_to,
        "evaluations": evaluations,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.get("/stats")
async def get_gate_stats():
    """게이트 통계"""
    from server import db
    
    # 통과/차단 통계
    total = await db.pipeline_signals.count_documents({})
    blocked = await db.pipeline_signals.count_documents({"status": "blocked"})
    passed = total - blocked
    
    return {
        "success": True,
        "stats": {
            "total_processed": total,
            "passed": passed,
            "blocked": blocked,
            "pass_rate": (passed / total * 100) if total > 0 else 0
        }
    }

@router.post("/manual-override")
async def manual_override(signal_id: str, action: str, reason: str = ""):
    """수동 게이트 오버라이드"""
    from server import db
    
    if action not in ["pass", "block"]:
        raise HTTPException(status_code=400, detail="action은 'pass' 또는 'block'이어야 합니다")
    
    result = await db.pipeline_signals.update_one(
        {"signal_id": signal_id},
        {"$set": {
            "gate_override": {
                "action": action,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }}
    )
    
    return {
        "success": result.modified_count > 0,
        "signal_id": signal_id,
        "action": action
    }
