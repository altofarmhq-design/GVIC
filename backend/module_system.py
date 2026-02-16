"""
GVIC 모듈 및 자산 인덱싱 시스템
- 모듈: 동일 특성의 자산들을 묶은 판매 단위
- 자산: 질문에서 추출된 특성별 자산 (하나의 질문 → 여러 자산)
- 인덱싱: 특성 기반 + 질문자 기반 인덱스
- 보상 분배: 5:3:2 결이론 적용
  - 5 (50%): 공공 - 이용자, 주주, 구성원에게 환원
  - 3 (30%): 운영 - 플랫폼 시스템 유지/발전
  - 2 (20%): 기획/관리 - GVIC 운영자 보상
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging

router = APIRouter(prefix="/api/modules", tags=["modules"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== 5:3:2 결이론 설정 ====================
# 가치/수익 배분 비율
PUBLIC_SHARE = 0.50      # 5/10 = 50% → 공공 (이용자, 주주, 구성원)
OPERATION_SHARE = 0.30   # 3/10 = 30% → 운영 (플랫폼 시스템)
MANAGEMENT_SHARE = 0.20  # 2/10 = 20% → 기획/관리 (GVIC 운영자)

# 환율 설정
POINT_TO_CASH_RATIO = 0.001  # 1P = ₩0.001
CASH_TO_POINT_RATIO = 1000   # ₩1 = 1000P

# ==================== Models ====================

class AssetFeature(BaseModel):
    """자산의 특성 정보"""
    feature_id: str
    feature_name: str
    feature_category: str  # technology, business, design, etc.
    keywords: List[str] = []
    weight: float = 1.0  # 이 특성의 가중치

class AssetFromSignal(BaseModel):
    """시그널에서 추출된 자산"""
    asset_id: str
    signal_id: str
    contributor_id: str  # 원 질문자 ID
    contributor_name: Optional[str] = None
    features: List[AssetFeature]
    content_summary: str
    value_score: float = 0.5
    created_at: str

class Module(BaseModel):
    """동일 특성으로 묶인 자산들의 모듈"""
    module_id: str
    module_name: str
    description: str
    feature_category: str  # 이 모듈의 주요 특성 카테고리
    feature_keywords: List[str]  # 모듈의 키워드
    assets: List[str]  # asset_id 목록
    asset_count: int
    contributors: List[str]  # 기여자 ID 목록 (중복 제거)
    contributor_count: int
    total_value_score: float
    avg_value_score: float
    price: float  # 모듈 가격
    status: str = "available"  # available, sold, archived
    created_at: str
    sale_count: int = 0

class CreateModuleRequest(BaseModel):
    """모듈 생성 요청"""
    module_name: str
    description: str
    feature_category: str
    feature_keywords: List[str]
    asset_ids: List[str]
    price: float = 0

class PurchaseModuleRequest(BaseModel):
    """모듈 구매 요청"""
    module_id: str
    purchase_price: float

class ExtractAssetsRequest(BaseModel):
    """시그널에서 자산 추출 요청"""
    signal_id: str
    extract_multiple: bool = True  # 복합 질문을 여러 자산으로 분리

# ==================== Helper Functions ====================

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    try:
        token = authorization[7:] if authorization.startswith("Bearer ") else authorization
        if not token or token in ('null', 'undefined', ''):
            raise HTTPException(status_code=401, detail="토큰이 없습니다")
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

# ==================== 자산 추출 (시그널 → 여러 자산) ====================

@router.post("/extract-assets")
async def extract_assets_from_signal(
    request: ExtractAssetsRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    하나의 시그널(질문)에서 여러 자산 추출
    
    복합적인 질문을 특징별로 분류하여 여러 자산으로 자산화
    예: "AI 기반 자동화 시스템 특허" → 
        - AI 기술 자산
        - 자동화 프로세스 자산
        - 시스템 아키텍처 자산
    """
    from server import db
    
    # 시그널 조회
    signal = await db.pipeline_signals.find_one(
        {"signal_id": request.signal_id},
        {"_id": 0}
    )
    
    if not signal:
        raise HTTPException(status_code=404, detail="시그널을 찾을 수 없습니다")
    
    contributor_id = signal.get("user_id") or signal.get("metadata", {}).get("user_id") or current_user.get("user_id")
    content = signal.get("content", "")
    ai_analysis = signal.get("metadata", {}).get("ai_analysis", {})
    
    extracted_assets = []
    
    if request.extract_multiple:
        # AI 분석을 통해 특성 추출 (시뮬레이션)
        # 실제로는 LLM을 사용하여 특성 분류
        features_detected = extract_features_from_content(content, ai_analysis)
        
        for idx, feature_set in enumerate(features_detected):
            asset_id = f"AST_{uuid.uuid4().hex[:12]}"
            
            # 자산 가치 계산
            base_value = feature_set.get("value_score", 0.5) * 100  # 기본 가치 점수
            
            # 5:3:2 결이론 기반 가치 분해
            value_breakdown = {
                "total_value": base_value,
                "public_value": base_value * PUBLIC_SHARE,      # 5/10 = 공공
                "operation_value": base_value * OPERATION_SHARE, # 3/10 = 운영
                "management_value": base_value * MANAGEMENT_SHARE # 2/10 = 기획/관리
            }
            
            asset_doc = {
                "asset_id": asset_id,
                "signal_id": request.signal_id,
                "contributor_id": contributor_id,
                "features": feature_set["features"],
                "feature_category": feature_set["category"],
                "feature_keywords": feature_set["keywords"],
                "content_summary": feature_set["summary"],
                "original_content": content[:500],
                "value_score": feature_set.get("value_score", 0.5),
                "novelty_score": feature_set.get("novelty_score", 0.5),
                # 5:3:2 가치 분해
                "value_breakdown_532": value_breakdown,
                "status": "indexed",
                "module_ids": [],  # 이 자산이 속한 모듈들
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.indexed_assets.insert_one(asset_doc)
            extracted_assets.append({
                "asset_id": asset_id,
                "feature_category": feature_set["category"],
                "keywords": feature_set["keywords"],
                "summary": feature_set["summary"],
                "value_breakdown_532": value_breakdown
            })
            
            logger.info(f"Asset extracted: {asset_id} from signal {request.signal_id} with 5:3:2 value breakdown")
    else:
        # 단일 자산으로 추출
        asset_id = f"AST_{uuid.uuid4().hex[:12]}"
        
        # 기본 가치
        base_value = 50  # 기본 점수
        
        # 5:3:2 결이론 기반 가치 분해
        value_breakdown = {
            "total_value": base_value,
            "public_value": base_value * PUBLIC_SHARE,
            "operation_value": base_value * OPERATION_SHARE,
            "management_value": base_value * MANAGEMENT_SHARE
        }
        
        asset_doc = {
            "asset_id": asset_id,
            "signal_id": request.signal_id,
            "contributor_id": contributor_id,
            "features": [{"feature_id": "general", "feature_name": "일반", "feature_category": "general", "keywords": [], "weight": 1.0}],
            "feature_category": "general",
            "feature_keywords": [],
            "content_summary": content[:200],
            "original_content": content[:500],
            "value_score": 0.5,
            "novelty_score": 0.5,
            # 5:3:2 가치 분해
            "value_breakdown_532": value_breakdown,
            "status": "indexed",
            "module_ids": [],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.indexed_assets.insert_one(asset_doc)
        extracted_assets.append({
            "asset_id": asset_id,
            "feature_category": "general",
            "keywords": [],
            "summary": content[:200],
            "value_breakdown_532": value_breakdown
        })
    
    # 시그널에 추출된 자산 ID 기록
    await db.pipeline_signals.update_one(
        {"signal_id": request.signal_id},
        {"$set": {"extracted_asset_ids": [a["asset_id"] for a in extracted_assets]}}
    )
    
    return {
        "success": True,
        "signal_id": request.signal_id,
        "contributor_id": contributor_id,
        "assets_extracted": len(extracted_assets),
        "assets": extracted_assets,
        "message": f"시그널에서 {len(extracted_assets)}개 자산이 추출되었습니다"
    }

def extract_features_from_content(content: str, ai_analysis: dict) -> List[dict]:
    """
    콘텐츠에서 특성 추출 (시뮬레이션)
    실제 환경에서는 LLM을 사용하여 특성 분류
    """
    features = []
    content_lower = content.lower()
    
    # 기술 특성 감지
    tech_keywords = ["ai", "인공지능", "머신러닝", "딥러닝", "알고리즘", "데이터", "분석"]
    if any(kw in content_lower for kw in tech_keywords):
        features.append({
            "category": "technology",
            "keywords": [kw for kw in tech_keywords if kw in content_lower],
            "summary": f"기술 관련: {content[:100]}",
            "value_score": 0.7,
            "novelty_score": 0.6,
            "features": [{"feature_id": "tech_1", "feature_name": "기술", "feature_category": "technology", "keywords": tech_keywords, "weight": 1.0}]
        })
    
    # 비즈니스 특성 감지
    biz_keywords = ["비즈니스", "수익", "시장", "고객", "판매", "마케팅", "전략"]
    if any(kw in content_lower for kw in biz_keywords):
        features.append({
            "category": "business",
            "keywords": [kw for kw in biz_keywords if kw in content_lower],
            "summary": f"비즈니스 관련: {content[:100]}",
            "value_score": 0.6,
            "novelty_score": 0.5,
            "features": [{"feature_id": "biz_1", "feature_name": "비즈니스", "feature_category": "business", "keywords": biz_keywords, "weight": 1.0}]
        })
    
    # 특허/아이디어 특성 감지
    patent_keywords = ["특허", "아이디어", "혁신", "발명", "창작", "독창"]
    if any(kw in content_lower for kw in patent_keywords):
        features.append({
            "category": "patent_idea",
            "keywords": [kw for kw in patent_keywords if kw in content_lower],
            "summary": f"특허/아이디어 관련: {content[:100]}",
            "value_score": 0.8,
            "novelty_score": 0.7,
            "features": [{"feature_id": "patent_1", "feature_name": "특허/아이디어", "feature_category": "patent_idea", "keywords": patent_keywords, "weight": 1.0}]
        })
    
    # 프로세스/자동화 특성 감지
    process_keywords = ["자동화", "프로세스", "워크플로우", "효율", "최적화", "시스템"]
    if any(kw in content_lower for kw in process_keywords):
        features.append({
            "category": "process",
            "keywords": [kw for kw in process_keywords if kw in content_lower],
            "summary": f"프로세스 관련: {content[:100]}",
            "value_score": 0.6,
            "novelty_score": 0.5,
            "features": [{"feature_id": "proc_1", "feature_name": "프로세스", "feature_category": "process", "keywords": process_keywords, "weight": 1.0}]
        })
    
    # 특성이 없으면 일반으로 분류
    if not features:
        features.append({
            "category": "general",
            "keywords": [],
            "summary": content[:150],
            "value_score": 0.5,
            "novelty_score": 0.5,
            "features": [{"feature_id": "gen_1", "feature_name": "일반", "feature_category": "general", "keywords": [], "weight": 1.0}]
        })
    
    return features

# ==================== 모듈 생성 및 관리 ====================

@router.post("/create")
async def create_module(
    request: CreateModuleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    동일 특성의 자산들을 묶어 모듈 생성
    """
    from server import db
    
    if not request.asset_ids:
        raise HTTPException(status_code=400, detail="최소 1개 이상의 자산이 필요합니다")
    
    # 자산들 조회
    assets = await db.indexed_assets.find(
        {"asset_id": {"$in": request.asset_ids}},
        {"_id": 0}
    ).to_list(len(request.asset_ids))
    
    if not assets:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다")
    
    # 기여자 목록 추출 (중복 제거)
    contributors = list(set(a.get("contributor_id") for a in assets if a.get("contributor_id")))
    
    # 총 가치 점수 계산
    total_value = sum(a.get("value_score", 0.5) for a in assets)
    avg_value = total_value / len(assets)
    
    module_id = f"MOD_{uuid.uuid4().hex[:12]}"
    
    module_doc = {
        "module_id": module_id,
        "module_name": request.module_name,
        "description": request.description,
        "feature_category": request.feature_category,
        "feature_keywords": request.feature_keywords,
        "assets": request.asset_ids,
        "asset_count": len(request.asset_ids),
        "contributors": contributors,
        "contributor_count": len(contributors),
        "total_value_score": total_value,
        "avg_value_score": avg_value,
        "price": request.price if request.price > 0 else calculate_module_price(avg_value, len(assets)),
        "status": "available",
        "created_by": current_user.get("user_id"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "sale_count": 0,
        "total_revenue": 0
    }
    
    await db.asset_modules.insert_one(module_doc)
    
    # 자산들에 모듈 ID 추가
    await db.indexed_assets.update_many(
        {"asset_id": {"$in": request.asset_ids}},
        {"$push": {"module_ids": module_id}}
    )
    
    logger.info(f"Module created: {module_id} with {len(request.asset_ids)} assets")
    
    return {
        "success": True,
        "module_id": module_id,
        "module_name": request.module_name,
        "asset_count": len(request.asset_ids),
        "contributor_count": len(contributors),
        "price": module_doc["price"],
        "message": f"모듈 '{request.module_name}'이 생성되었습니다"
    }

def calculate_module_price(avg_value_score: float, asset_count: int) -> float:
    """모듈 가격 자동 계산"""
    base_price = 1000  # 기본 ₩1,000
    value_multiplier = avg_value_score * 2  # 가치 점수 반영
    count_multiplier = 1 + (asset_count * 0.1)  # 자산 수 반영
    
    return base_price * value_multiplier * count_multiplier

@router.get("/list")
async def list_modules(
    category: str = None,
    status: str = "available",
    limit: int = 50
):
    """모듈 목록 조회"""
    from server import db
    
    query = {}
    if category:
        query["feature_category"] = category
    if status:
        query["status"] = status
    
    modules = await db.asset_modules.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "modules": modules,
        "total": len(modules)
    }

@router.get("/{module_id}")
async def get_module_detail(module_id: str):
    """모듈 상세 조회"""
    from server import db
    
    module = await db.asset_modules.find_one(
        {"module_id": module_id},
        {"_id": 0}
    )
    
    if not module:
        raise HTTPException(status_code=404, detail="모듈을 찾을 수 없습니다")
    
    # 포함된 자산 정보 조회
    assets = await db.indexed_assets.find(
        {"asset_id": {"$in": module.get("assets", [])}},
        {"_id": 0, "asset_id": 1, "contributor_id": 1, "feature_category": 1, "content_summary": 1, "value_score": 1}
    ).to_list(100)
    
    return {
        **module,
        "asset_details": assets
    }

# ==================== 모듈 구매 및 보상 분배 ====================

@router.post("/purchase")
async def purchase_module(
    request: PurchaseModuleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    모듈 구매 및 5:3:2 결이론 기반 가치 분배
    
    5:3:2 분배 로직:
    - 5 (50%): 공공 환원 → 기여자들에게 분배 (자산 수 n으로 나눔)
    - 3 (30%): 운영 → 플랫폼 시스템 적립
    - 2 (20%): 기획/관리 → GVIC 운영자 보상
    """
    from server import db
    
    buyer_id = current_user.get("user_id")
    
    # 모듈 조회
    module = await db.asset_modules.find_one(
        {"module_id": request.module_id},
        {"_id": 0}
    )
    
    if not module:
        raise HTTPException(status_code=404, detail="모듈을 찾을 수 없습니다")
    
    # 모듈 내 자산들 조회
    assets = await db.indexed_assets.find(
        {"asset_id": {"$in": module.get("assets", [])}},
        {"_id": 0}
    ).to_list(100)
    
    if not assets:
        raise HTTPException(status_code=400, detail="모듈에 자산이 없습니다")
    
    # ==================== 5:3:2 결이론 적용 ====================
    purchase_price = request.purchase_price
    
    # 5 (50%): 공공 환원 - 기여자들에게 분배
    public_share_total = purchase_price * PUBLIC_SHARE
    asset_count = len(assets)
    reward_per_asset = public_share_total / asset_count
    reward_points_per_asset = reward_per_asset * CASH_TO_POINT_RATIO
    
    # 3 (30%): 운영 - 플랫폼 적립
    operation_share_total = purchase_price * OPERATION_SHARE
    
    # 2 (20%): 기획/관리 - GVIC 운영자 보상
    management_share_total = purchase_price * MANAGEMENT_SHARE
    
    # 기여자별 보상 분배
    contributor_rewards = {}  # contributor_id -> {cash, points, assets}
    reward_distribution = []
    
    for asset in assets:
        contributor_id = asset.get("contributor_id")
        asset_id = asset.get("asset_id")
        
        if contributor_id:
            if contributor_id not in contributor_rewards:
                contributor_rewards[contributor_id] = {
                    "cash": 0,
                    "points": 0,
                    "assets": [],
                    "asset_count": 0
                }
            
            contributor_rewards[contributor_id]["cash"] += reward_per_asset
            contributor_rewards[contributor_id]["points"] += reward_points_per_asset
            contributor_rewards[contributor_id]["assets"].append(asset_id)
            contributor_rewards[contributor_id]["asset_count"] += 1
    
    # 각 기여자에게 포인트 적립
    for contributor_id, reward_info in contributor_rewards.items():
        transaction = {
            "type": "earn",
            "amount": reward_info["points"],
            "description": f"모듈 구매 보상 ({reward_info['asset_count']}개 자산)",
            "reference_id": request.module_id,
            "module_name": module.get("module_name"),
            "purchase_price": request.purchase_price,
            "asset_count": reward_info["asset_count"],
            "total_assets_in_module": asset_count,
            "cash_value": reward_info["cash"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await db.user_points.update_one(
            {"user_id": contributor_id},
            {
                "$inc": {
                    "total_points": reward_info["points"],
                    "available_points": reward_info["points"],
                    "total_earned": reward_info["points"]
                },
                "$push": {"transactions": transaction},
                "$set": {"last_updated": datetime.now(timezone.utc).isoformat()}
            },
            upsert=True
        )
        
        reward_distribution.append({
            "contributor_id": contributor_id,
            "asset_count": reward_info["asset_count"],
            "share_ratio": reward_info["asset_count"] / asset_count,
            "reward_cash": reward_info["cash"],
            "reward_points": reward_info["points"]
        })
        
        logger.info(f"Module purchase reward: {contributor_id} +{reward_info['points']}P for {reward_info['asset_count']} assets")
    
    # 구매 기록 저장 (5:3:2 분배 내역 포함)
    purchase_record = {
        "purchase_id": f"MPUR_{uuid.uuid4().hex[:12]}",
        "module_id": request.module_id,
        "module_name": module.get("module_name"),
        "buyer_id": buyer_id,
        "purchase_price": request.purchase_price,
        # 5:3:2 결이론 분배 내역
        "value_distribution": {
            "public": {
                "ratio": PUBLIC_SHARE,
                "amount": public_share_total,
                "description": "공공 환원 (기여자 분배)"
            },
            "operation": {
                "ratio": OPERATION_SHARE,
                "amount": operation_share_total,
                "description": "운영 (플랫폼 시스템)"
            },
            "management": {
                "ratio": MANAGEMENT_SHARE,
                "amount": management_share_total,
                "description": "기획/관리 (GVIC 운영자)"
            }
        },
        "asset_count": asset_count,
        "reward_per_asset": reward_per_asset,
        "reward_distribution": reward_distribution,
        "unique_contributors": len(contributor_rewards),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.module_purchases.insert_one(purchase_record)
    
    # 플랫폼 운영 적립금 기록 (3: 운영)
    await db.platform_funds.update_one(
        {"fund_type": "operation"},
        {
            "$inc": {"total_amount": operation_share_total},
            "$push": {
                "transactions": {
                    "amount": operation_share_total,
                    "source": "module_purchase",
                    "module_id": request.module_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        },
        upsert=True
    )
    
    # GVIC 운영자 보상 기록 (2: 기획/관리)
    await db.platform_funds.update_one(
        {"fund_type": "management"},
        {
            "$inc": {"total_amount": management_share_total},
            "$push": {
                "transactions": {
                    "amount": management_share_total,
                    "source": "module_purchase",
                    "module_id": request.module_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            }
        },
        upsert=True
    )
    
    # 모듈 판매 통계 업데이트
    await db.asset_modules.update_one(
        {"module_id": request.module_id},
        {
            "$inc": {"sale_count": 1, "total_revenue": request.purchase_price},
            "$set": {"last_sold_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {
        "success": True,
        "purchase_id": purchase_record["purchase_id"],
        "module_id": request.module_id,
        "module_name": module.get("module_name"),
        "purchase_price": request.purchase_price,
        # 5:3:2 분배 결과
        "value_distribution_532": {
            "public_5": {
                "amount": public_share_total,
                "recipients": len(contributor_rewards),
                "per_asset": reward_per_asset
            },
            "operation_3": {
                "amount": operation_share_total,
                "destination": "플랫폼 운영"
            },
            "management_2": {
                "amount": management_share_total,
                "destination": "GVIC 운영자"
            }
        },
        "asset_count": asset_count,
        "unique_contributors": len(contributor_rewards),
        "reward_distribution": reward_distribution,
        "message": f"₩{request.purchase_price:,.0f} 구매 완료. 5:3:2 결이론 적용 - 공공 ₩{public_share_total:,.0f} ({len(contributor_rewards)}명), 운영 ₩{operation_share_total:,.0f}, 기획 ₩{management_share_total:,.0f}"
    }

# ==================== 인덱스 조회 ====================

@router.get("/index/by-feature")
async def get_assets_by_feature(
    category: str = None,
    keywords: str = None,
    limit: int = 50
):
    """특성 기반 자산 인덱스 조회"""
    from server import db
    
    query = {}
    if category:
        query["feature_category"] = category
    if keywords:
        keyword_list = [k.strip() for k in keywords.split(",")]
        query["feature_keywords"] = {"$in": keyword_list}
    
    assets = await db.indexed_assets.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # 카테고리별 집계
    category_stats = {}
    for asset in assets:
        cat = asset.get("feature_category", "unknown")
        if cat not in category_stats:
            category_stats[cat] = 0
        category_stats[cat] += 1
    
    return {
        "assets": assets,
        "total": len(assets),
        "category_stats": category_stats
    }

@router.get("/index/by-contributor/{contributor_id}")
async def get_assets_by_contributor(
    contributor_id: str,
    limit: int = 50
):
    """질문자(기여자) 기반 자산 인덱스 조회"""
    from server import db
    
    assets = await db.indexed_assets.find(
        {"contributor_id": contributor_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # 이 기여자가 포함된 모듈 조회
    modules = await db.asset_modules.find(
        {"contributors": contributor_id},
        {"_id": 0, "module_id": 1, "module_name": 1, "asset_count": 1, "price": 1}
    ).to_list(50)
    
    return {
        "contributor_id": contributor_id,
        "assets": assets,
        "asset_count": len(assets),
        "modules_included": modules,
        "module_count": len(modules)
    }

@router.get("/index/contributor-ranking")
async def get_contributor_ranking(limit: int = 20):
    """기여자 랭킹 조회"""
    from server import db
    
    # 자산 수 기준 랭킹
    pipeline = [
        {"$group": {
            "_id": "$contributor_id",
            "asset_count": {"$sum": 1},
            "total_value": {"$sum": "$value_score"},
            "categories": {"$addToSet": "$feature_category"}
        }},
        {"$sort": {"asset_count": -1}},
        {"$limit": limit}
    ]
    
    ranking = await db.indexed_assets.aggregate(pipeline).to_list(limit)
    
    return {
        "ranking": [
            {
                "rank": idx + 1,
                "contributor_id": r["_id"],
                "asset_count": r["asset_count"],
                "total_value": r["total_value"],
                "avg_value": r["total_value"] / r["asset_count"] if r["asset_count"] > 0 else 0,
                "categories": r["categories"]
            }
            for idx, r in enumerate(ranking) if r["_id"]
        ]
    }

# ==================== 통계 ====================

@router.get("/stats/overview")
async def get_module_stats():
    """모듈 및 자산 통계"""
    from server import db
    
    total_modules = await db.asset_modules.count_documents({})
    available_modules = await db.asset_modules.count_documents({"status": "available"})
    total_assets = await db.indexed_assets.count_documents({})
    
    # 카테고리별 통계
    category_pipeline = [
        {"$group": {"_id": "$feature_category", "count": {"$sum": 1}}}
    ]
    categories = await db.indexed_assets.aggregate(category_pipeline).to_list(20)
    
    # 총 구매 금액
    revenue_pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$purchase_price"}}}
    ]
    revenue = await db.module_purchases.aggregate(revenue_pipeline).to_list(1)
    total_revenue = revenue[0]["total"] if revenue else 0
    
    return {
        "modules": {
            "total": total_modules,
            "available": available_modules
        },
        "assets": {
            "total": total_assets,
            "by_category": {c["_id"]: c["count"] for c in categories if c["_id"]}
        },
        "revenue": {
            "total": total_revenue,
            "contributor_share": total_revenue * PURCHASE_CONTRIBUTOR_SHARE
        }
    }
