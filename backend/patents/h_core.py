"""
H: CORE - 코어 특허 모듈
시그마(Σ) 설정 및 핵심 파라미터 관리
5:3:2 결이론 기반 가치 분배
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/h", tags=["H:CORE"])
logger = logging.getLogger(__name__)

# 5:3:2 결이론 상수
PUBLIC_RATIO = 0.5      # 공공 환원 (5/10)
OPERATION_RATIO = 0.3   # 운영 (3/10)
MANAGEMENT_RATIO = 0.2  # 기획/관리 (2/10)

class SigmaConfig(BaseModel):
    """시그마 설정"""
    public_weight: float = 0.5     # 공공 (5)
    operation_weight: float = 0.3   # 운영 (3)
    management_weight: float = 0.2  # 기획/관리 (2)

class OmegaConfig(BaseModel):
    """오메가 경계 조건"""
    min_value: float = 0.0
    max_value: float = 100.0
    threshold: float = 50.0

# ==================== 5:3:2 결이론 ====================

@router.get("/532-theory")
async def get_532_theory():
    """5:3:2 결이론 설명"""
    return {
        "success": True,
        "theory": {
            "name": "5:3:2 결이론",
            "description": "가치/수익 분배 원칙",
            "components": [
                {
                    "code": "5",
                    "name": "공공 환원",
                    "ratio": 0.5,
                    "percentage": "50%",
                    "beneficiaries": "이용자, 주주, 구성원",
                    "description": "커뮤니티와 이해관계자에게 기여 환원"
                },
                {
                    "code": "3",
                    "name": "플랫폼 운영",
                    "ratio": 0.3,
                    "percentage": "30%",
                    "beneficiaries": "GVIC 시스템",
                    "description": "시스템 유지, 발전, 재투자"
                },
                {
                    "code": "2",
                    "name": "기획/관리",
                    "ratio": 0.2,
                    "percentage": "20%",
                    "beneficiaries": "GVIC 운영자",
                    "description": "기획자 및 관리자 보상"
                }
            ],
            "example": {
                "total": 10000,
                "public": 5000,
                "operation": 3000,
                "management": 2000
            }
        }
    }

@router.post("/calculate-532")
async def calculate_532_distribution(total_value: float):
    """5:3:2 가치 분배 계산"""
    distribution = {
        "total_value": total_value,
        "public": {
            "ratio": PUBLIC_RATIO,
            "amount": total_value * PUBLIC_RATIO,
            "label": "공공 환원 (5)"
        },
        "operation": {
            "ratio": OPERATION_RATIO,
            "amount": total_value * OPERATION_RATIO,
            "label": "플랫폼 운영 (3)"
        },
        "management": {
            "ratio": MANAGEMENT_RATIO,
            "amount": total_value * MANAGEMENT_RATIO,
            "label": "기획/관리 (2)"
        }
    }
    
    return {"success": True, "distribution": distribution}

# ==================== 시그마 설정 ====================

@router.get("/sigma")
async def get_sigma_config():
    """현재 시그마 설정 조회"""
    from server import db
    
    config = await db.system_config.find_one({"type": "sigma"}, {"_id": 0})
    
    if not config:
        config = {
            "type": "sigma",
            "public_weight": PUBLIC_RATIO,
            "operation_weight": OPERATION_RATIO,
            "management_weight": MANAGEMENT_RATIO,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    return {"success": True, "sigma": config}

@router.put("/sigma")
async def update_sigma_config(config: SigmaConfig):
    """시그마 설정 업데이트"""
    from server import db
    
    # 합계 검증
    total = config.public_weight + config.operation_weight + config.management_weight
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"가중치 합계가 1이어야 합니다 (현재: {total})")
    
    sigma_doc = {
        "type": "sigma",
        "public_weight": config.public_weight,
        "operation_weight": config.operation_weight,
        "management_weight": config.management_weight,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.system_config.update_one(
        {"type": "sigma"},
        {"$set": sigma_doc},
        upsert=True
    )
    
    return {"success": True, "sigma": sigma_doc}

# ==================== 오메가 설정 ====================

@router.get("/omega")
async def get_omega_config():
    """현재 오메가 경계 조건 조회"""
    from server import db
    
    config = await db.system_config.find_one({"type": "omega"}, {"_id": 0})
    
    if not config:
        config = {
            "type": "omega",
            "min_value": 0.0,
            "max_value": 100.0,
            "threshold": 50.0,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    
    return {"success": True, "omega": config}

@router.put("/omega")
async def update_omega_config(config: OmegaConfig):
    """오메가 경계 조건 업데이트"""
    from server import db
    
    if config.min_value >= config.max_value:
        raise HTTPException(status_code=400, detail="min_value는 max_value보다 작아야 합니다")
    
    omega_doc = {
        "type": "omega",
        "min_value": config.min_value,
        "max_value": config.max_value,
        "threshold": config.threshold,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.system_config.update_one(
        {"type": "omega"},
        {"$set": omega_doc},
        upsert=True
    )
    
    return {"success": True, "omega": omega_doc}

@router.get("/core-stats")
async def get_core_stats():
    """코어 시스템 통계"""
    from server import db
    
    # 전체 시그널 수
    total_signals = await db.pipeline_signals.count_documents({})
    
    # 전체 자산 수
    total_assets = await db.indexed_assets.count_documents({})
    
    # 플랫폼 펀드
    operation_fund = await db.platform_funds.find_one({"fund_type": "operation"}, {"_id": 0})
    management_fund = await db.platform_funds.find_one({"fund_type": "management"}, {"_id": 0})
    
    return {
        "success": True,
        "stats": {
            "total_signals": total_signals,
            "total_assets": total_assets,
            "operation_fund": operation_fund.get("total_amount", 0) if operation_fund else 0,
            "management_fund": management_fund.get("total_amount", 0) if management_fund else 0
        }
    }
