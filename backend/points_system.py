"""
GVIC 포인트 시스템
- 사용자별 포인트 관리
- 자산 기여에 따른 포인트 적립
- 포인트:현금 = 1P : ₩0.001 (1000P = ₩1)
- 유료 전환 시 포인트로 대체 가능
- 구매 시 20% 기여자 보상 분배
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging

router = APIRouter(prefix="/api/points", tags=["points"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# 포인트 환율 설정
# 1P = ₩0.001, 즉 현금 1원 = 1000 포인트
POINT_TO_CASH_RATIO = 0.001  # 1 포인트 = 0.001원
CASH_TO_POINT_RATIO = 1000   # 현금 1원 = 1000 포인트

# 구매 보상 설정
PURCHASE_CONTRIBUTOR_SHARE = 0.20  # 구매가의 20%를 기여자에게 분배

# ==================== Models ====================

class PointTransaction(BaseModel):
    type: str  # earn, spend, convert
    amount: float
    description: str
    reference_id: Optional[str] = None  # signal_id, asset_id 등
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class PointBalance(BaseModel):
    user_id: str
    total_points: float
    available_points: float
    pending_points: float
    cash_equivalent: float  # 현금 환산 가치
    last_updated: str

class EarnPointsRequest(BaseModel):
    reason: str = Field(..., description="적립 사유: signal_submit, asset_created, asset_sold, referral")
    reference_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class SpendPointsRequest(BaseModel):
    amount: float = Field(..., gt=0, description="사용할 포인트")
    reason: str = Field(..., description="사용 사유: premium_feature, report_download, api_calls")
    reference_id: Optional[str] = None

class ConvertPointsRequest(BaseModel):
    points_amount: float = Field(..., gt=0, description="전환할 포인트")
    conversion_type: str = Field("to_cash", description="전환 유형: to_cash")

class AssetPurchaseRequest(BaseModel):
    asset_id: str = Field(..., description="구매할 자산 ID")
    purchase_price: float = Field(..., gt=0, description="구매 금액 (원)")

class ContributorReward(BaseModel):
    user_id: str
    signal_id: str
    contribution_ratio: float  # 기여 비율 (0~1)
    reward_points: float
    reward_cash_value: float

# ==================== Helper Functions ====================

async def get_current_user(authorization: str = Header(None)):
    """현재 사용자 정보 가져오기"""
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        if not token or token in ('null', 'undefined', ''):
            raise HTTPException(status_code=401, detail="토큰이 없습니다")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

def calculate_signal_points(signal_data: dict) -> float:
    """시그널 제출에 따른 포인트 계산"""
    base_points = 10.0  # 기본 시그널 제출
    
    # 분석 유형에 따른 보너스
    analysis_type = signal_data.get("metadata", {}).get("analysis_type", "general")
    if analysis_type == "code":
        base_points += 5.0
    elif analysis_type == "patent_idea":
        base_points += 15.0
    
    # 파일 첨부 보너스
    if signal_data.get("metadata", {}).get("file_type"):
        base_points += 5.0
    
    return base_points

def calculate_asset_points(asset_data: dict) -> float:
    """자산화에 따른 포인트 계산"""
    value_analysis = asset_data.get("value_analysis", {})
    
    # 기본 자산화 포인트
    base_points = 50.0
    
    # 가치 점수에 따른 보너스 (0-100점 기준)
    value_score = value_analysis.get("value_score", 0.5) * 100
    novelty_score = value_analysis.get("novelty_score", 0.5) * 100
    
    # 점수 보너스 (최대 50 포인트 추가)
    bonus = (value_score + novelty_score) / 4
    
    return base_points + bonus

def calculate_sale_points(sale_data: dict) -> float:
    """자산 판매에 따른 포인트 계산"""
    sale_price = sale_data.get("final_price", 0)
    contributor_share = sale_data.get("contributor_share", 0.7)
    
    # 판매가의 기여자 몫 * 현금:포인트 비율
    return sale_price * contributor_share * CASH_TO_POINT_RATIO

# ==================== Points API ====================

@router.get("/balance")
async def get_point_balance(current_user: dict = Depends(get_current_user)):
    """현재 사용자 포인트 잔액 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 사용자 포인트 정보 조회
    point_doc = await db.user_points.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not point_doc:
        # 신규 사용자는 기본 포인트 생성
        point_doc = {
            "user_id": user_id,
            "total_points": 100.0,  # 신규 가입 보너스
            "available_points": 100.0,
            "pending_points": 0.0,
            "total_earned": 100.0,
            "total_spent": 0.0,
            "transactions": [{
                "type": "earn",
                "amount": 100.0,
                "description": "신규 가입 보너스",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat()
        }
        await db.user_points.insert_one(point_doc)
        if "_id" in point_doc:
            del point_doc["_id"]
    
    # 현금 환산 가치 계산 (1P = ₩0.001)
    cash_equivalent = point_doc.get("available_points", 0) * POINT_TO_CASH_RATIO
    
    return {
        "user_id": user_id,
        "total_points": point_doc.get("total_points", 0),
        "available_points": point_doc.get("available_points", 0),
        "pending_points": point_doc.get("pending_points", 0),
        "total_earned": point_doc.get("total_earned", 0),
        "total_spent": point_doc.get("total_spent", 0),
        "cash_equivalent": cash_equivalent,
        "cash_to_point_ratio": CASH_TO_POINT_RATIO,
        "last_updated": point_doc.get("last_updated")
    }

@router.get("/transactions")
async def get_point_transactions(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """포인트 거래 내역 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    point_doc = await db.user_points.find_one(
        {"user_id": user_id},
        {"_id": 0, "transactions": 1}
    )
    
    if not point_doc:
        return {"transactions": [], "total": 0}
    
    transactions = point_doc.get("transactions", [])
    
    # 최신순 정렬
    transactions = sorted(
        transactions, 
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )[:limit]
    
    return {
        "transactions": transactions,
        "total": len(transactions)
    }

@router.post("/earn")
async def earn_points(
    request: EarnPointsRequest,
    current_user: dict = Depends(get_current_user)
):
    """포인트 적립"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 적립 사유에 따른 포인트 계산
    points_to_earn = 0.0
    description = ""
    
    if request.reason == "signal_submit":
        points_to_earn = 10.0
        description = "시그널 제출"
    elif request.reason == "asset_created":
        points_to_earn = 50.0
        description = "자산 생성"
    elif request.reason == "asset_sold":
        points_to_earn = 100.0
        description = "자산 판매"
    elif request.reason == "referral":
        points_to_earn = 200.0
        description = "추천인 보너스"
    elif request.reason == "daily_login":
        points_to_earn = 5.0
        description = "일일 출석 보너스"
    else:
        points_to_earn = 10.0
        description = request.reason
    
    # 메타데이터에서 추가 포인트 계산
    if request.metadata.get("value_score"):
        bonus = float(request.metadata["value_score"]) * 50
        points_to_earn += bonus
    
    # 트랜잭션 기록
    transaction = {
        "type": "earn",
        "amount": points_to_earn,
        "description": description,
        "reference_id": request.reference_id,
        "metadata": request.metadata,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # 포인트 업데이트
    result = await db.user_points.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "total_points": points_to_earn,
                "available_points": points_to_earn,
                "total_earned": points_to_earn
            },
            "$push": {"transactions": transaction},
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    logger.info(f"Points earned: {user_id} +{points_to_earn}")
    
    return {
        "success": True,
        "points_earned": points_to_earn,
        "reason": description,
        "message": f"{points_to_earn} 포인트가 적립되었습니다"
    }

@router.post("/spend")
async def spend_points(
    request: SpendPointsRequest,
    current_user: dict = Depends(get_current_user)
):
    """포인트 사용"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 현재 잔액 확인
    point_doc = await db.user_points.find_one(
        {"user_id": user_id},
        {"_id": 0, "available_points": 1}
    )
    
    if not point_doc:
        raise HTTPException(status_code=400, detail="포인트 정보가 없습니다")
    
    available = point_doc.get("available_points", 0)
    
    if available < request.amount:
        raise HTTPException(
            status_code=400, 
            detail=f"포인트가 부족합니다. 현재 잔액: {available}, 필요: {request.amount}"
        )
    
    # 트랜잭션 기록
    transaction = {
        "type": "spend",
        "amount": -request.amount,
        "description": request.reason,
        "reference_id": request.reference_id,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # 포인트 차감
    await db.user_points.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "available_points": -request.amount,
                "total_spent": request.amount
            },
            "$push": {"transactions": transaction},
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    logger.info(f"Points spent: {user_id} -{request.amount}")
    
    return {
        "success": True,
        "points_spent": request.amount,
        "reason": request.reason,
        "remaining_points": available - request.amount,
        "message": f"{request.amount} 포인트가 사용되었습니다"
    }

@router.post("/convert")
async def convert_points(
    request: ConvertPointsRequest,
    current_user: dict = Depends(get_current_user)
):
    """포인트 전환 (유료 전환 시)"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 현재 잔액 확인
    point_doc = await db.user_points.find_one(
        {"user_id": user_id},
        {"_id": 0, "available_points": 1}
    )
    
    if not point_doc:
        raise HTTPException(status_code=400, detail="포인트 정보가 없습니다")
    
    available = point_doc.get("available_points", 0)
    
    if available < request.points_amount:
        raise HTTPException(
            status_code=400,
            detail=f"포인트가 부족합니다. 현재 잔액: {available}"
        )
    
    # 현금 환산 (1P = ₩0.001)
    cash_value = request.points_amount * POINT_TO_CASH_RATIO
    
    # 트랜잭션 기록
    transaction = {
        "type": "convert",
        "amount": -request.points_amount,
        "description": f"현금 전환 (₩{cash_value:,.3f})",
        "cash_value": cash_value,
        "conversion_rate": POINT_TO_CASH_RATIO,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # 포인트 차감
    await db.user_points.update_one(
        {"user_id": user_id},
        {
            "$inc": {
                "available_points": -request.points_amount,
                "total_spent": request.points_amount
            },
            "$push": {"transactions": transaction},
            "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    logger.info(f"Points converted: {user_id} {request.points_amount}P -> ₩{cash_value}")
    
    return {
        "success": True,
        "points_converted": request.points_amount,
        "cash_value": cash_value,
        "conversion_rate": CASH_TO_POINT_RATIO,
        "remaining_points": available - request.points_amount,
        "message": f"{request.points_amount} 포인트가 ₩{cash_value:,.0f}로 전환되었습니다"
    }

# ==================== 자산 통계 ====================

@router.get("/asset-summary")
async def get_asset_summary(current_user: dict = Depends(get_current_user)):
    """사용자 자산 축적 현황 요약"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 사용자가 생성한 시그널 수
    total_signals = await db.pipeline_signals.count_documents({
        "$or": [
            {"user_id": user_id},
            {"metadata.user_id": user_id}
        ]
    })
    
    # 카테고리별 시그널 수
    wanted_signals = await db.pipeline_signals.count_documents({
        "$or": [{"user_id": user_id}, {"metadata.user_id": user_id}],
        "category": "wanted"
    })
    unwanted_signals = await db.pipeline_signals.count_documents({
        "$or": [{"user_id": user_id}, {"metadata.user_id": user_id}],
        "category": "unwanted"
    })
    
    # 자산화된 시그널 (gvic_assets)
    total_assets = await db.gvic_assets.count_documents({
        "$or": [
            {"contributor_id": user_id},
            {"metadata.user_id": user_id}
        ]
    })
    
    # 자산 총 가치 계산
    assets = await db.gvic_assets.find(
        {"$or": [{"contributor_id": user_id}, {"metadata.user_id": user_id}]},
        {"_id": 0, "value_analysis": 1, "module_info": 1}
    ).to_list(100)
    
    total_value_score = 0
    total_estimated_value = 0
    
    for asset in assets:
        value_analysis = asset.get("value_analysis", {})
        module_info = asset.get("module_info", {})
        
        total_value_score += value_analysis.get("value_score", 0.5) * 100
        total_estimated_value += module_info.get("final_price", 0)
    
    avg_value_score = total_value_score / len(assets) if assets else 0
    
    # 포인트 정보
    point_doc = await db.user_points.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    total_points = point_doc.get("total_points", 0) if point_doc else 0
    available_points = point_doc.get("available_points", 0) if point_doc else 0
    
    return {
        "user_id": user_id,
        "signals": {
            "total": total_signals,
            "wanted": wanted_signals,
            "unwanted": unwanted_signals,
            "asset_converted": total_assets
        },
        "assets": {
            "total": total_assets,
            "avg_value_score": round(avg_value_score, 1),
            "total_estimated_value": total_estimated_value
        },
        "points": {
            "total": total_points,
            "available": available_points,
            "cash_equivalent": available_points / CASH_TO_POINT_RATIO
        },
        "evaluation": {
            "contribution_level": get_contribution_level(total_signals, total_assets, available_points),
            "activity_score": min(100, total_signals * 5 + total_assets * 20),
            "rank": get_user_rank(available_points)
        }
    }

def get_contribution_level(signals: int, assets: int, points: float) -> dict:
    """기여 레벨 계산"""
    score = signals * 10 + assets * 50 + points * 0.1
    
    if score >= 10000:
        return {"level": 5, "name": "마스터", "color": "#fbbf24"}
    elif score >= 5000:
        return {"level": 4, "name": "전문가", "color": "#a855f7"}
    elif score >= 2000:
        return {"level": 3, "name": "숙련자", "color": "#3b82f6"}
    elif score >= 500:
        return {"level": 2, "name": "기여자", "color": "#22c55e"}
    else:
        return {"level": 1, "name": "입문자", "color": "#64748b"}

def get_user_rank(points: float) -> str:
    """포인트 기반 등급"""
    if points >= 10000:
        return "Diamond"
    elif points >= 5000:
        return "Platinum"
    elif points >= 2000:
        return "Gold"
    elif points >= 500:
        return "Silver"
    else:
        return "Bronze"

# ==================== 포인트 환율 조회 ====================

@router.get("/exchange-rate")
async def get_exchange_rate():
    """현금:포인트 환율 정보"""
    return {
        "cash_to_point_ratio": CASH_TO_POINT_RATIO,
        "description": f"현금 ₩1 = {CASH_TO_POINT_RATIO} 포인트",
        "inverse": f"포인트 1P = ₩{1/CASH_TO_POINT_RATIO:,.0f}",
        "examples": [
            {"points": 100, "cash": 100 / CASH_TO_POINT_RATIO},
            {"points": 500, "cash": 500 / CASH_TO_POINT_RATIO},
            {"points": 1000, "cash": 1000 / CASH_TO_POINT_RATIO},
        ]
    }

# ==================== 포인트 적립 기준 ====================

@router.get("/earning-rules")
async def get_earning_rules():
    """포인트 적립 기준"""
    return {
        "rules": [
            {"action": "signal_submit", "points": 10, "description": "시그널 제출"},
            {"action": "code_analysis", "points": 15, "description": "코드 분석 시그널"},
            {"action": "patent_idea", "points": 25, "description": "특허/아이디어 분석 시그널"},
            {"action": "file_upload", "points": 5, "description": "파일 첨부 보너스"},
            {"action": "asset_created", "points": 50, "description": "자산 생성됨"},
            {"action": "high_value_asset", "points": "최대 50", "description": "고가치 자산 보너스 (가치 점수에 따라)"},
            {"action": "asset_sold", "points": "구매가 × 20% × 기여비율 × 0.01", "description": "자산 판매 시 기여자 보상"},
            {"action": "daily_login", "points": 5, "description": "일일 출석"},
            {"action": "referral", "points": 200, "description": "추천인 보너스"},
            {"action": "signup_bonus", "points": 100, "description": "신규 가입 보너스"}
        ],
        "conversion": {
            "ratio": CASH_TO_POINT_RATIO,
            "note": "유료 전환 시 포인트를 현금으로 대체 가능"
        },
        "purchase_reward": {
            "contributor_share": f"{PURCHASE_CONTRIBUTOR_SHARE * 100}%",
            "description": "구매가의 20%가 기여자들에게 기여 비율에 따라 분배됩니다"
        }
    }

# ==================== 자산 구매 및 기여자 보상 ====================

@router.post("/purchase/asset")
async def purchase_asset_and_distribute_rewards(
    request: AssetPurchaseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    자산 구매 및 기여자 보상 분배
    
    - 구매가의 20%를 기여자들에게 분배
    - 각 기여자는 해당 모듈(시그널)의 기여 비율만큼 받음
    - 보상은 포인트로 적립됨 (현금 × 0.01)
    """
    from server import db
    
    buyer_id = current_user.get("user_id")
    
    # 자산 조회
    asset = await db.gvic_assets.find_one(
        {"asset_id": request.asset_id},
        {"_id": 0}
    )
    
    if not asset:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다")
    
    # 기여자 보상 금액 계산 (구매가의 20%)
    total_contributor_reward = request.purchase_price * PURCHASE_CONTRIBUTOR_SHARE
    
    # 관련 시그널들 조회 (기여자 정보)
    signal_id = asset.get("signal_id")
    contributors = asset.get("contributors", [])
    
    # 기여자가 없는 경우, 원본 시그널 제출자를 기여자로 설정
    if not contributors and signal_id:
        signal = await db.pipeline_signals.find_one(
            {"signal_id": signal_id},
            {"_id": 0, "user_id": 1, "metadata": 1}
        )
        if signal:
            user_id = signal.get("user_id") or signal.get("metadata", {}).get("user_id")
            if user_id:
                contributors = [{
                    "user_id": user_id,
                    "signal_id": signal_id,
                    "contribution_ratio": 1.0  # 단일 기여자는 100%
                }]
    
    # 기여 비율 정규화 (합이 1이 되도록)
    total_ratio = sum(c.get("contribution_ratio", 0) for c in contributors)
    if total_ratio == 0:
        total_ratio = 1
    
    # 보상 분배 결과
    reward_distribution = []
    
    for contributor in contributors:
        contrib_user_id = contributor.get("user_id")
        contrib_signal_id = contributor.get("signal_id", signal_id)
        raw_ratio = contributor.get("contribution_ratio", 1.0)
        
        # 정규화된 기여 비율
        normalized_ratio = raw_ratio / total_ratio
        
        # 보상 금액 계산
        reward_cash = total_contributor_reward * normalized_ratio
        reward_points = reward_cash * CASH_TO_POINT_RATIO
        
        if contrib_user_id and reward_points > 0:
            # 포인트 적립
            transaction = {
                "type": "earn",
                "amount": reward_points,
                "description": f"자산 구매 보상 (기여도 {normalized_ratio*100:.1f}%)",
                "reference_id": request.asset_id,
                "purchase_price": request.purchase_price,
                "contribution_ratio": normalized_ratio,
                "cash_value": reward_cash,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            await db.user_points.update_one(
                {"user_id": contrib_user_id},
                {
                    "$inc": {
                        "total_points": reward_points,
                        "available_points": reward_points,
                        "total_earned": reward_points
                    },
                    "$push": {"transactions": transaction},
                    "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
                },
                upsert=True
            )
            
            reward_distribution.append({
                "user_id": contrib_user_id,
                "signal_id": contrib_signal_id,
                "contribution_ratio": normalized_ratio,
                "reward_points": reward_points,
                "reward_cash_value": reward_cash
            })
            
            logger.info(f"Contributor reward: {contrib_user_id} +{reward_points}P ({normalized_ratio*100:.1f}%)")
    
    # 구매 기록 저장
    purchase_record = {
        "purchase_id": f"PUR_{uuid.uuid4().hex[:12]}",
        "asset_id": request.asset_id,
        "buyer_id": buyer_id,
        "purchase_price": request.purchase_price,
        "contributor_share": total_contributor_reward,
        "reward_distribution": reward_distribution,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.asset_purchases.insert_one(purchase_record)
    
    # 자산 판매 상태 업데이트
    await db.gvic_assets.update_one(
        {"asset_id": request.asset_id},
        {
            "$set": {
                "sale_status": "sold",
                "sold_at": datetime.now(timezone.utc).isoformat(),
                "buyer_id": buyer_id,
                "sold_price": request.purchase_price
            },
            "$inc": {"sale_count": 1}
        }
    )
    
    return {
        "success": True,
        "purchase_id": purchase_record["purchase_id"],
        "asset_id": request.asset_id,
        "purchase_price": request.purchase_price,
        "contributor_share": total_contributor_reward,
        "contributor_share_percent": f"{PURCHASE_CONTRIBUTOR_SHARE * 100}%",
        "reward_distribution": reward_distribution,
        "total_contributors": len(reward_distribution),
        "message": f"₩{request.purchase_price:,.0f} 구매 완료. 기여자 {len(reward_distribution)}명에게 총 ₩{total_contributor_reward:,.0f} 분배됨"
    }

@router.get("/purchase/history")
async def get_purchase_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """구매 내역 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 내가 구매한 내역
    purchases = await db.asset_purchases.find(
        {"buyer_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # 내가 받은 보상 내역
    rewards_received = await db.asset_purchases.find(
        {"reward_distribution.user_id": user_id},
        {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    # 내 보상만 필터링
    my_rewards = []
    for purchase in rewards_received:
        for reward in purchase.get("reward_distribution", []):
            if reward.get("user_id") == user_id:
                my_rewards.append({
                    "purchase_id": purchase.get("purchase_id"),
                    "asset_id": purchase.get("asset_id"),
                    "purchase_price": purchase.get("purchase_price"),
                    "my_contribution_ratio": reward.get("contribution_ratio"),
                    "my_reward_points": reward.get("reward_points"),
                    "my_reward_cash_value": reward.get("reward_cash_value"),
                    "timestamp": purchase.get("timestamp")
                })
    
    return {
        "purchases": purchases,
        "rewards_received": my_rewards,
        "total_purchases": len(purchases),
        "total_rewards": len(my_rewards)
    }

@router.get("/reward-rules")
async def get_reward_rules():
    """보상 분배 규칙 조회"""
    return {
        "purchase_reward": {
            "contributor_share": PURCHASE_CONTRIBUTOR_SHARE,
            "contributor_share_percent": f"{PURCHASE_CONTRIBUTOR_SHARE * 100}%",
            "description": "구매가의 20%가 기여자들에게 분배됩니다"
        },
        "distribution_method": {
            "method": "contribution_ratio",
            "description": "각 기여자(질문자)는 해당 모듈이 기여한 비율만큼 보상을 받습니다"
        },
        "point_conversion": {
            "ratio": CASH_TO_POINT_RATIO,
            "description": f"보상은 포인트로 적립됩니다 (현금 ₩1 = {CASH_TO_POINT_RATIO}P)"
        },
        "example": {
            "purchase_price": 10000,
            "contributor_share": 10000 * PURCHASE_CONTRIBUTOR_SHARE,
            "single_contributor_reward_cash": 10000 * PURCHASE_CONTRIBUTOR_SHARE * 1.0,
            "single_contributor_reward_points": 10000 * PURCHASE_CONTRIBUTOR_SHARE * 1.0 * CASH_TO_POINT_RATIO,
            "description": "₩10,000 구매 시, 단일 기여자는 ₩2,000 (= 20P) 보상"
        }
    }
