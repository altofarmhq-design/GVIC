"""
B: CALC - 산출 특허 모듈
가치 계산 및 점수 산출
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/b", tags=["B:CALC"])
logger = logging.getLogger(__name__)

# ==================== 가치 계산 ====================

@router.post("/calculate-value")
async def calculate_asset_value(
    content: str,
    keywords: List[str] = [],
    category: str = "general"
):
    """자산 가치 계산 (다차원 스코어링)"""
    from gvic_analyzer import evaluate_asset_value
    
    result = await evaluate_asset_value(
        content=content,
        keywords=keywords,
        category=category
    )
    
    return result

@router.post("/calculate-module-price")
async def calculate_module_price(
    asset_ids: List[str],
    pricing_strategy: str = "average"
):
    """모듈 가격 계산"""
    from server import db
    
    assets = await db.indexed_assets.find(
        {"asset_id": {"$in": asset_ids}},
        {"_id": 0}
    ).to_list(100)
    
    if not assets:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다")
    
    value_scores = [a.get("value_score", 0.5) for a in assets]
    
    if pricing_strategy == "average":
        base_price = sum(value_scores) / len(value_scores) * 1000
    elif pricing_strategy == "max":
        base_price = max(value_scores) * 1000
    elif pricing_strategy == "sum":
        base_price = sum(value_scores) * 500
    else:
        base_price = sum(value_scores) / len(value_scores) * 1000
    
    # 자산 개수 보너스
    count_bonus = len(assets) * 100
    
    final_price = base_price + count_bonus
    
    return {
        "success": True,
        "asset_count": len(assets),
        "avg_value_score": sum(value_scores) / len(value_scores),
        "base_price": round(base_price, 2),
        "count_bonus": count_bonus,
        "final_price": round(final_price, 2),
        "pricing_strategy": pricing_strategy
    }

@router.post("/calculate-reward")
async def calculate_reward_distribution(
    total_amount: float,
    contributor_ids: List[str]
):
    """보상 분배 계산 (5:3:2 결이론)"""
    from patents.h_core import PUBLIC_RATIO, OPERATION_RATIO, MANAGEMENT_RATIO
    
    public_share = total_amount * PUBLIC_RATIO
    operation_share = total_amount * OPERATION_RATIO
    management_share = total_amount * MANAGEMENT_RATIO
    
    # 공공 몫을 기여자들에게 균등 분배
    per_contributor = public_share / len(contributor_ids) if contributor_ids else 0
    
    return {
        "success": True,
        "total_amount": total_amount,
        "distribution_532": {
            "public": {
                "amount": round(public_share, 2),
                "per_contributor": round(per_contributor, 2),
                "contributor_count": len(contributor_ids)
            },
            "operation": {
                "amount": round(operation_share, 2),
                "destination": "플랫폼 운영"
            },
            "management": {
                "amount": round(management_share, 2),
                "destination": "GVIC 운영자"
            }
        }
    }

@router.get("/pricing-strategies")
async def get_pricing_strategies():
    """가격 책정 전략 목록"""
    strategies = [
        {"key": "average", "name": "평균 가치", "description": "자산들의 평균 가치 점수 기반"},
        {"key": "max", "name": "최고 가치", "description": "가장 높은 가치 점수 기반"},
        {"key": "sum", "name": "합산 가치", "description": "모든 가치 점수 합산"}
    ]
    return {"success": True, "strategies": strategies}

@router.get("/calc-stats")
async def get_calc_stats():
    """계산 통계"""
    from server import db
    
    # 자산 가치 통계
    assets = await db.indexed_assets.find({}, {"_id": 0, "value_score": 1}).to_list(1000)
    
    if assets:
        value_scores = [a.get("value_score", 0.5) for a in assets]
        avg_value = sum(value_scores) / len(value_scores)
        max_value = max(value_scores)
        min_value = min(value_scores)
    else:
        avg_value = max_value = min_value = 0
    
    return {
        "success": True,
        "stats": {
            "total_assets": len(assets),
            "avg_value_score": round(avg_value, 3),
            "max_value_score": round(max_value, 3),
            "min_value_score": round(min_value, 3)
        }
    }
