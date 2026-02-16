"""
GVIC Shop Manager - 쇼핑몰 운영자 관리 시스템
- 쇼핑몰 등록/관리
- 제품 등록/관리
- API 키 발급
- 분석 주기 설정
- 웹훅 설정
"""
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import secrets
import hashlib
import os
import jwt
import logging

router = APIRouter(prefix="/api/shop", tags=["shop-manager"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== Models ====================

class ShopCreate(BaseModel):
    """쇼핑몰 등록"""
    name: str = Field(..., description="쇼핑몰 이름")
    platform: str = Field(..., description="플랫폼: naver, coupang, 11st, gmarket, self")
    url: str = Field(..., description="쇼핑몰 URL")
    description: Optional[str] = Field(None, description="설명")

class ShopUpdate(BaseModel):
    """쇼핑몰 수정"""
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class ProductCreate(BaseModel):
    """제품 등록"""
    name: str = Field(..., description="제품명")
    product_url: str = Field(..., description="제품 URL")
    product_id_external: Optional[str] = Field(None, description="외부 상품 ID")
    category: Optional[str] = Field(None, description="카테고리")
    price: Optional[str] = Field(None, description="가격")

class ProductUpdate(BaseModel):
    """제품 수정"""
    name: Optional[str] = None
    product_url: Optional[str] = None
    category: Optional[str] = None
    price: Optional[str] = None
    is_active: Optional[bool] = None

class AnalysisSchedule(BaseModel):
    """분석 주기 설정"""
    frequency: str = Field(..., description="분석 주기: daily, weekly, monthly")
    day_of_week: Optional[int] = Field(None, description="주간 분석 시 요일 (0=월, 6=일)")
    day_of_month: Optional[int] = Field(None, description="월간 분석 시 일자 (1-28)")
    hour: int = Field(9, description="분석 시간 (0-23)")
    timezone: str = Field("Asia/Seoul", description="타임존")

class WebhookConfig(BaseModel):
    """웹훅 설정"""
    url: str = Field(..., description="웹훅 URL")
    events: List[str] = Field(["analysis_complete"], description="구독 이벤트")
    secret: Optional[str] = Field(None, description="웹훅 시크릿 (서명 검증용)")
    is_active: bool = Field(True, description="활성화 여부")

class APIKeyCreate(BaseModel):
    """API 키 생성"""
    name: str = Field(..., description="API 키 이름")
    permissions: List[str] = Field(["read", "analyze"], description="권한")
    rate_limit: int = Field(1000, description="일일 요청 제한")

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

def generate_api_key() -> str:
    """보안 API 키 생성"""
    return f"gvic_sk_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """API 키 해시"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generate_webhook_secret() -> str:
    """웹훅 시크릿 생성"""
    return f"whsec_{secrets.token_urlsafe(24)}"

# ==================== 쇼핑몰 관리 API ====================

@router.post("/shops")
async def create_shop(
    shop: ShopCreate,
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 등록"""
    from server import db
    
    user_id = current_user.get("user_id")
    shop_id = f"shop_{uuid.uuid4().hex[:12]}"
    
    # 중복 체크
    existing = await db.shops.find_one({
        "user_id": user_id,
        "url": shop.url
    })
    if existing:
        raise HTTPException(status_code=400, detail="이미 등록된 쇼핑몰입니다")
    
    shop_record = {
        "shop_id": shop_id,
        "user_id": user_id,
        "name": shop.name,
        "platform": shop.platform,
        "url": shop.url,
        "description": shop.description,
        "is_active": True,
        "products_count": 0,
        "analysis_schedule": None,
        "webhook_config": None,
        "last_analysis": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shops.insert_one(shop_record)
    
    return {
        "success": True,
        "shop_id": shop_id,
        "message": "쇼핑몰이 등록되었습니다"
    }

@router.get("/shops")
async def get_shops(
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 목록 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    shops = await db.shops.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {
        "shops": shops,
        "total": len(shops)
    }

@router.get("/shops/{shop_id}")
async def get_shop(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 상세 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    shop = await db.shops.find_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not shop:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    # 제품 목록도 함께 조회
    products = await db.shop_products.find(
        {"shop_id": shop_id},
        {"_id": 0}
    ).to_list(100)
    
    shop["products"] = products
    
    return shop

@router.put("/shops/{shop_id}")
async def update_shop(
    shop_id: str,
    update: ShopUpdate,
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 수정"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.shops.update_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    return {"success": True, "message": "쇼핑몰이 수정되었습니다"}

@router.delete("/shops/{shop_id}")
async def delete_shop(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 삭제"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 쇼핑몰 삭제
    result = await db.shops.delete_one(
        {"shop_id": shop_id, "user_id": user_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    # 관련 제품도 삭제
    await db.shop_products.delete_many({"shop_id": shop_id})
    
    return {"success": True, "message": "쇼핑몰이 삭제되었습니다"}

# ==================== 제품 관리 API ====================

@router.post("/shops/{shop_id}/products")
async def create_product(
    shop_id: str,
    product: ProductCreate,
    current_user: dict = Depends(get_current_user)
):
    """제품 등록"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 쇼핑몰 확인
    shop = await db.shops.find_one(
        {"shop_id": shop_id, "user_id": user_id}
    )
    if not shop:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    product_id = f"prod_{uuid.uuid4().hex[:12]}"
    
    product_record = {
        "product_id": product_id,
        "shop_id": shop_id,
        "user_id": user_id,
        "name": product.name,
        "product_url": product.product_url,
        "product_id_external": product.product_id_external,
        "category": product.category,
        "price": product.price,
        "is_active": True,
        "total_reviews_analyzed": 0,
        "last_analysis": None,
        "latest_insights": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.shop_products.insert_one(product_record)
    
    # 쇼핑몰 제품 수 업데이트
    await db.shops.update_one(
        {"shop_id": shop_id},
        {"$inc": {"products_count": 1}}
    )
    
    return {
        "success": True,
        "product_id": product_id,
        "message": "제품이 등록되었습니다"
    }

@router.get("/shops/{shop_id}/products")
async def get_products(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """제품 목록 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 쇼핑몰 확인
    shop = await db.shops.find_one(
        {"shop_id": shop_id, "user_id": user_id}
    )
    if not shop:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    products = await db.shop_products.find(
        {"shop_id": shop_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    return {
        "shop_id": shop_id,
        "products": products,
        "total": len(products)
    }

@router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """제품 상세 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    product = await db.shop_products.find_one(
        {"product_id": product_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")
    
    # 최근 분석 결과 조회
    recent_analyses = await db.product_analyses.find(
        {"product_id": product_id},
        {"_id": 0}
    ).sort("analyzed_at", -1).limit(5).to_list(5)
    
    product["recent_analyses"] = recent_analyses
    
    return product

@router.put("/products/{product_id}")
async def update_product(
    product_id: str,
    update: ProductUpdate,
    current_user: dict = Depends(get_current_user)
):
    """제품 수정"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.shop_products.update_one(
        {"product_id": product_id, "user_id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")
    
    return {"success": True, "message": "제품이 수정되었습니다"}

@router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    current_user: dict = Depends(get_current_user)
):
    """제품 삭제"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    product = await db.shop_products.find_one(
        {"product_id": product_id, "user_id": user_id}
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")
    
    shop_id = product.get("shop_id")
    
    # 제품 삭제
    await db.shop_products.delete_one({"product_id": product_id})
    
    # 쇼핑몰 제품 수 업데이트
    await db.shops.update_one(
        {"shop_id": shop_id},
        {"$inc": {"products_count": -1}}
    )
    
    return {"success": True, "message": "제품이 삭제되었습니다"}

# ==================== 분석 주기 설정 API ====================

@router.put("/shops/{shop_id}/schedule")
async def set_analysis_schedule(
    shop_id: str,
    schedule: AnalysisSchedule,
    current_user: dict = Depends(get_current_user)
):
    """분석 주기 설정"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 유효성 검사
    if schedule.frequency == "weekly" and schedule.day_of_week is None:
        raise HTTPException(status_code=400, detail="주간 분석 시 요일을 지정해주세요")
    if schedule.frequency == "monthly" and schedule.day_of_month is None:
        raise HTTPException(status_code=400, detail="월간 분석 시 일자를 지정해주세요")
    
    schedule_data = {
        "frequency": schedule.frequency,
        "day_of_week": schedule.day_of_week,
        "day_of_month": schedule.day_of_month,
        "hour": schedule.hour,
        "timezone": schedule.timezone,
        "is_active": True,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 다음 분석 일정 계산
    next_analysis = calculate_next_analysis(schedule)
    schedule_data["next_analysis"] = next_analysis
    
    result = await db.shops.update_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"$set": {"analysis_schedule": schedule_data}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    return {
        "success": True,
        "schedule": schedule_data,
        "next_analysis": next_analysis,
        "message": "분석 주기가 설정되었습니다"
    }

def calculate_next_analysis(schedule: AnalysisSchedule) -> str:
    """다음 분석 일정 계산"""
    now = datetime.now(timezone.utc)
    
    if schedule.frequency == "daily":
        # 오늘 해당 시간이 지났으면 내일
        next_time = now.replace(hour=schedule.hour, minute=0, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=1)
    
    elif schedule.frequency == "weekly":
        # 이번 주 해당 요일, 지났으면 다음 주
        days_ahead = schedule.day_of_week - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_time = now + timedelta(days=days_ahead)
        next_time = next_time.replace(hour=schedule.hour, minute=0, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=7)
    
    elif schedule.frequency == "monthly":
        # 이번 달 해당 일자, 지났으면 다음 달
        try:
            next_time = now.replace(day=schedule.day_of_month, hour=schedule.hour, minute=0, second=0, microsecond=0)
            if next_time <= now:
                # 다음 달로
                if now.month == 12:
                    next_time = next_time.replace(year=now.year + 1, month=1)
                else:
                    next_time = next_time.replace(month=now.month + 1)
        except ValueError:
            # 해당 달에 그 날짜가 없으면 (예: 31일)
            next_time = now.replace(day=28, hour=schedule.hour, minute=0, second=0, microsecond=0)
            if next_time <= now:
                if now.month == 12:
                    next_time = next_time.replace(year=now.year + 1, month=1)
                else:
                    next_time = next_time.replace(month=now.month + 1)
    else:
        next_time = now + timedelta(days=1)
    
    return next_time.isoformat()

@router.delete("/shops/{shop_id}/schedule")
async def delete_analysis_schedule(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """분석 주기 삭제"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    result = await db.shops.update_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"$set": {"analysis_schedule": None}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    return {"success": True, "message": "분석 주기가 삭제되었습니다"}

# ==================== 웹훅 설정 API ====================

@router.put("/shops/{shop_id}/webhook")
async def set_webhook(
    shop_id: str,
    webhook: WebhookConfig,
    current_user: dict = Depends(get_current_user)
):
    """웹훅 설정"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    webhook_data = {
        "url": webhook.url,
        "events": webhook.events,
        "secret": webhook.secret or generate_webhook_secret(),
        "is_active": webhook.is_active,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.shops.update_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"$set": {"webhook_config": webhook_data}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    return {
        "success": True,
        "webhook": webhook_data,
        "message": "웹훅이 설정되었습니다"
    }

@router.delete("/shops/{shop_id}/webhook")
async def delete_webhook(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """웹훅 삭제"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    result = await db.shops.update_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"$set": {"webhook_config": None}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    return {"success": True, "message": "웹훅이 삭제되었습니다"}

@router.post("/shops/{shop_id}/webhook/test")
async def test_webhook(
    shop_id: str,
    current_user: dict = Depends(get_current_user)
):
    """웹훅 테스트"""
    from server import db
    import aiohttp
    
    user_id = current_user.get("user_id")
    
    shop = await db.shops.find_one(
        {"shop_id": shop_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not shop:
        raise HTTPException(status_code=404, detail="쇼핑몰을 찾을 수 없습니다")
    
    webhook_config = shop.get("webhook_config")
    if not webhook_config:
        raise HTTPException(status_code=400, detail="웹훅이 설정되지 않았습니다")
    
    # 테스트 페이로드 전송
    test_payload = {
        "event": "webhook.test",
        "shop_id": shop_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "message": "GVIC 웹훅 테스트입니다"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_config["url"],
                json=test_payload,
                headers={"X-GVIC-Signature": webhook_config.get("secret", "")},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                success = response.status < 400
                return {
                    "success": success,
                    "status_code": response.status,
                    "message": "웹훅 테스트 성공" if success else "웹훅 테스트 실패"
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "웹훅 연결 실패"
        }

# ==================== API 키 관리 ====================

@router.post("/api-keys")
async def create_api_key(
    key_config: APIKeyCreate,
    current_user: dict = Depends(get_current_user)
):
    """API 키 생성"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # API 키 생성
    api_key = generate_api_key()
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    
    key_record = {
        "key_id": key_id,
        "user_id": user_id,
        "name": key_config.name,
        "key_hash": hash_api_key(api_key),
        "key_prefix": api_key[:12] + "...",  # 표시용 접두사
        "permissions": key_config.permissions,
        "rate_limit": key_config.rate_limit,
        "usage_count": 0,
        "last_used": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.api_keys.insert_one(key_record)
    
    return {
        "success": True,
        "key_id": key_id,
        "api_key": api_key,  # 최초 1회만 표시
        "name": key_config.name,
        "message": "API 키가 생성되었습니다. 이 키는 다시 표시되지 않으니 안전하게 보관하세요."
    }

@router.get("/api-keys")
async def get_api_keys(
    current_user: dict = Depends(get_current_user)
):
    """API 키 목록 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    keys = await db.api_keys.find(
        {"user_id": user_id},
        {"_id": 0, "key_hash": 0}  # 해시 제외
    ).sort("created_at", -1).to_list(50)
    
    return {
        "api_keys": keys,
        "total": len(keys)
    }

@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """API 키 삭제"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    result = await db.api_keys.delete_one(
        {"key_id": key_id, "user_id": user_id}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    return {"success": True, "message": "API 키가 삭제되었습니다"}

@router.put("/api-keys/{key_id}/deactivate")
async def deactivate_api_key(
    key_id: str,
    current_user: dict = Depends(get_current_user)
):
    """API 키 비활성화"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    result = await db.api_keys.update_one(
        {"key_id": key_id, "user_id": user_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    return {"success": True, "message": "API 키가 비활성화되었습니다"}

# ==================== 온보딩 상태 API ====================

@router.get("/onboarding/status")
async def get_onboarding_status(
    current_user: dict = Depends(get_current_user)
):
    """온보딩 진행 상태 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 쇼핑몰 등록 여부
    shops = await db.shops.find(
        {"user_id": user_id},
        {"_id": 0, "shop_id": 1}
    ).to_list(10)
    has_shop = len(shops) > 0
    
    # 제품 등록 여부
    products = await db.shop_products.find(
        {"user_id": user_id},
        {"_id": 0, "product_id": 1}
    ).to_list(10)
    has_product = len(products) > 0
    
    # 분석 주기 설정 여부
    shops_with_schedule = await db.shops.find(
        {"user_id": user_id, "analysis_schedule": {"$ne": None}},
        {"_id": 0, "shop_id": 1}
    ).to_list(10)
    has_schedule = len(shops_with_schedule) > 0
    
    # API 키 발급 여부
    api_keys = await db.api_keys.find(
        {"user_id": user_id},
        {"_id": 0, "key_id": 1}
    ).to_list(10)
    has_api_key = len(api_keys) > 0
    
    # 분석 실행 여부
    analyses = await db.product_analyses.find(
        {"user_id": user_id},
        {"_id": 0, "analysis_id": 1}
    ).to_list(1)
    has_analysis = len(analyses) > 0
    
    steps = [
        {"step": 1, "name": "쇼핑몰 등록", "completed": has_shop},
        {"step": 2, "name": "제품 등록", "completed": has_product},
        {"step": 3, "name": "분석 주기 설정", "completed": has_schedule},
        {"step": 4, "name": "API 키 발급", "completed": has_api_key},
        {"step": 5, "name": "첫 분석 실행", "completed": has_analysis}
    ]
    
    completed_steps = sum(1 for s in steps if s["completed"])
    
    return {
        "steps": steps,
        "completed_steps": completed_steps,
        "total_steps": len(steps),
        "progress_percent": round(completed_steps / len(steps) * 100),
        "is_complete": completed_steps == len(steps),
        "next_step": next((s for s in steps if not s["completed"]), None)
    }

# ==================== 통계 API ====================

@router.get("/stats/overview")
async def get_shop_stats(
    current_user: dict = Depends(get_current_user)
):
    """쇼핑몰 통계 개요"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 쇼핑몰 수
    shops_count = await db.shops.count_documents({"user_id": user_id})
    
    # 제품 수
    products_count = await db.shop_products.count_documents({"user_id": user_id})
    
    # 총 분석 수
    analyses_count = await db.product_analyses.count_documents({"user_id": user_id})
    
    # API 호출 수 (이번 달)
    start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    api_calls = await db.api_usage_logs.count_documents({
        "user_id": user_id,
        "timestamp": {"$gte": start_of_month.isoformat()}
    })
    
    return {
        "shops_count": shops_count,
        "products_count": products_count,
        "analyses_count": analyses_count,
        "api_calls_this_month": api_calls
    }
