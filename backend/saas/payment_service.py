"""
GVIC Payment System - Stripe 결제 연동
- 구독 플랜 관리 (Starter/Growth/Pro/Enterprise)
- 정기 결제 (월간)
- 사용량 기반 과금 (분석 횟수)
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import uuid
import os
import jwt
import logging
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/payments", tags=["payments"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

# ==================== 구독 플랜 정의 ====================

SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free",
        "name_ko": "무료",
        "price_monthly": 0.0,
        "price_yearly": 0.0,
        "currency": "krw",
        "analysis_limit": 10,
        "products_limit": 3,
        "shops_limit": 1,
        "features": ["기본 리뷰 분석", "4대 인사이트"],
        "description": "무료 체험"
    },
    "starter": {
        "name": "Starter",
        "name_ko": "스타터",
        "price_monthly": 29000.0,
        "price_yearly": 290000.0,
        "currency": "krw",
        "analysis_limit": 50,
        "products_limit": 5,
        "shops_limit": 1,
        "features": ["기본 리뷰 분석", "4대 인사이트", "Q&A 관리", "월간 리포트"],
        "description": "소규모 셀러를 위한 시작 플랜"
    },
    "growth": {
        "name": "Growth",
        "name_ko": "그로스",
        "price_monthly": 99000.0,
        "price_yearly": 990000.0,
        "currency": "krw",
        "analysis_limit": 200,
        "products_limit": 20,
        "shops_limit": 3,
        "features": ["기본 리뷰 분석", "4대 인사이트", "Q&A 관리", "주간 리포트", "품목군 자산 접근", "API 키 발급"],
        "description": "성장하는 셀러를 위한 플랜"
    },
    "pro": {
        "name": "Pro",
        "name_ko": "프로",
        "price_monthly": 249000.0,
        "price_yearly": 2490000.0,
        "currency": "krw",
        "analysis_limit": 1000,
        "products_limit": 50,
        "shops_limit": 10,
        "features": ["기본 리뷰 분석", "4대 인사이트", "Q&A 관리", "일간 리포트", "품목군 자산 접근", "API 키 발급", "웹훅", "우선 지원"],
        "description": "전문 셀러를 위한 프로 플랜"
    },
    "enterprise": {
        "name": "Enterprise",
        "name_ko": "엔터프라이즈",
        "price_monthly": 0.0,  # 협의
        "price_yearly": 0.0,
        "currency": "krw",
        "analysis_limit": -1,  # 무제한
        "products_limit": -1,
        "shops_limit": -1,
        "features": ["모든 기능", "무제한 분석", "전담 매니저", "커스텀 연동", "SLA 보장"],
        "description": "대규모 기업을 위한 맞춤 플랜 (협의)"
    }
}

# ==================== Models ====================

class SubscriptionPlan(BaseModel):
    """구독 플랜"""
    plan_id: str
    name: str
    name_ko: str
    price_monthly: float
    price_yearly: float
    currency: str
    analysis_limit: int
    products_limit: int
    shops_limit: int
    features: List[str]
    description: str

class CreateCheckoutRequest(BaseModel):
    """결제 세션 생성 요청"""
    plan_id: str = Field(..., description="플랜 ID: starter, growth, pro")
    billing_cycle: str = Field("monthly", description="결제 주기: monthly, yearly")
    origin_url: str = Field(..., description="프론트엔드 origin URL")

class CheckoutStatusRequest(BaseModel):
    """결제 상태 조회 요청"""
    session_id: str

class SubscriptionStatus(BaseModel):
    """구독 상태"""
    plan_id: str
    plan_name: str
    status: str
    current_period_start: Optional[str]
    current_period_end: Optional[str]
    analysis_used: int
    analysis_limit: int
    next_billing_date: Optional[str]

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

# ==================== API Endpoints ====================

@router.get("/plans")
async def get_subscription_plans():
    """구독 플랜 목록 조회"""
    plans = [
        {
            "plan_id": plan_id,
            **plan_data
        }
        for plan_id, plan_data in SUBSCRIPTION_PLANS.items()
    ]
    return {
        "plans": plans,
        "currency": "KRW"
    }

@router.get("/plans/{plan_id}")
async def get_plan_detail(plan_id: str):
    """플랜 상세 조회"""
    plan = SUBSCRIPTION_PLANS.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="플랜을 찾을 수 없습니다")
    
    return {
        "plan_id": plan_id,
        **plan
    }

@router.post("/checkout/session")
async def create_checkout_session(
    request: CreateCheckoutRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """결제 세션 생성"""
    from server import db
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse
    )
    
    user_id = current_user.get("user_id")
    email = current_user.get("email", "")
    
    # 플랜 확인
    plan = SUBSCRIPTION_PLANS.get(request.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="유효하지 않은 플랜입니다")
    
    if request.plan_id == "free":
        raise HTTPException(status_code=400, detail="무료 플랜은 결제가 필요하지 않습니다")
    
    if request.plan_id == "enterprise":
        raise HTTPException(status_code=400, detail="엔터프라이즈 플랜은 별도 문의가 필요합니다")
    
    # 금액 결정 (서버에서만 결정)
    if request.billing_cycle == "yearly":
        amount = plan["price_yearly"]
    else:
        amount = plan["price_monthly"]
    
    # URL 생성
    origin = request.origin_url.rstrip('/')
    success_url = f"{origin}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/payment/cancel"
    
    # Stripe 초기화
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(
        api_key=STRIPE_API_KEY,
        webhook_url=webhook_url
    )
    
    # 메타데이터
    metadata = {
        "user_id": user_id,
        "email": email,
        "plan_id": request.plan_id,
        "billing_cycle": request.billing_cycle,
        "source": "gvic_subscription"
    }
    
    # 결제 세션 생성
    try:
        checkout_request = CheckoutSessionRequest(
            amount=float(amount),
            currency="krw",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # 트랜잭션 기록 생성 (PENDING)
        transaction_id = f"TXN_{uuid.uuid4().hex[:12]}"
        await db.payment_transactions.insert_one({
            "transaction_id": transaction_id,
            "session_id": session.session_id,
            "user_id": user_id,
            "email": email,
            "plan_id": request.plan_id,
            "billing_cycle": request.billing_cycle,
            "amount": amount,
            "currency": "krw",
            "status": "pending",
            "payment_status": "initiated",
            "metadata": metadata,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Checkout session created: {session.session_id} for user {user_id}")
        
        return {
            "url": session.url,
            "session_id": session.session_id,
            "transaction_id": transaction_id
        }
        
    except Exception as e:
        logger.error(f"Checkout session creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"결제 세션 생성 실패: {str(e)}")

@router.get("/checkout/status/{session_id}")
async def get_checkout_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """결제 상태 조회"""
    from server import db
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    user_id = current_user.get("user_id")
    
    # 트랜잭션 조회
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="트랜잭션을 찾을 수 없습니다")
    
    # 이미 처리된 결제인지 확인
    if transaction.get("payment_status") == "paid":
        return {
            "status": "complete",
            "payment_status": "paid",
            "message": "이미 처리된 결제입니다",
            "plan_id": transaction.get("plan_id")
        }
    
    # Stripe에서 상태 조회
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url="")
    
    try:
        status_response = await stripe_checkout.get_checkout_status(session_id)
        
        # 결제 성공 시 처리
        if status_response.payment_status == "paid":
            # 중복 처리 방지
            existing = await db.payment_transactions.find_one(
                {"session_id": session_id, "payment_status": "paid"}
            )
            
            if not existing:
                # 트랜잭션 업데이트
                await db.payment_transactions.update_one(
                    {"session_id": session_id},
                    {"$set": {
                        "status": "complete",
                        "payment_status": "paid",
                        "paid_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # 구독 활성화
                plan_id = transaction.get("plan_id")
                billing_cycle = transaction.get("billing_cycle", "monthly")
                
                # 구독 기간 계산
                now = datetime.now(timezone.utc)
                if billing_cycle == "yearly":
                    period_end = now + timedelta(days=365)
                else:
                    period_end = now + timedelta(days=30)
                
                # 사용자 구독 정보 업데이트
                await db.user_subscriptions.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "user_id": user_id,
                        "plan_id": plan_id,
                        "status": "active",
                        "billing_cycle": billing_cycle,
                        "current_period_start": now.isoformat(),
                        "current_period_end": period_end.isoformat(),
                        "analysis_used": 0,
                        "last_payment_id": transaction.get("transaction_id"),
                        "updated_at": now.isoformat()
                    }},
                    upsert=True
                )
                
                logger.info(f"Subscription activated: {plan_id} for user {user_id}")
        
        return {
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount_total": status_response.amount_total,
            "currency": status_response.currency,
            "plan_id": transaction.get("plan_id")
        }
        
    except Exception as e:
        logger.error(f"Checkout status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"상태 조회 실패: {str(e)}")

@router.get("/subscription/status")
async def get_subscription_status(
    current_user: dict = Depends(get_current_user)
):
    """현재 구독 상태 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    subscription = await db.user_subscriptions.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    if not subscription:
        # 무료 플랜 기본값
        return {
            "plan_id": "free",
            "plan_name": "Free",
            "status": "active",
            "current_period_start": None,
            "current_period_end": None,
            "analysis_used": 0,
            "analysis_limit": SUBSCRIPTION_PLANS["free"]["analysis_limit"],
            "products_limit": SUBSCRIPTION_PLANS["free"]["products_limit"],
            "shops_limit": SUBSCRIPTION_PLANS["free"]["shops_limit"],
            "next_billing_date": None
        }
    
    plan_id = subscription.get("plan_id", "free")
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    return {
        "plan_id": plan_id,
        "plan_name": plan["name"],
        "status": subscription.get("status", "active"),
        "billing_cycle": subscription.get("billing_cycle"),
        "current_period_start": subscription.get("current_period_start"),
        "current_period_end": subscription.get("current_period_end"),
        "analysis_used": subscription.get("analysis_used", 0),
        "analysis_limit": plan["analysis_limit"],
        "products_limit": plan["products_limit"],
        "shops_limit": plan["shops_limit"],
        "next_billing_date": subscription.get("current_period_end")
    }

@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: dict = Depends(get_current_user)
):
    """구독 취소"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    subscription = await db.user_subscriptions.find_one(
        {"user_id": user_id}
    )
    
    if not subscription:
        raise HTTPException(status_code=400, detail="활성 구독이 없습니다")
    
    if subscription.get("plan_id") == "free":
        raise HTTPException(status_code=400, detail="무료 플랜은 취소할 수 없습니다")
    
    # 구독 취소 (현재 기간 끝까지 유지)
    await db.user_subscriptions.update_one(
        {"user_id": user_id},
        {"$set": {
            "status": "cancelled",
            "cancelled_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "message": "구독이 취소되었습니다. 현재 기간이 끝나면 무료 플랜으로 전환됩니다.",
        "effective_date": subscription.get("current_period_end")
    }

@router.get("/transactions")
async def get_payment_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """결제 내역 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    transactions = await db.payment_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "transactions": transactions,
        "total": len(transactions)
    }

@router.post("/usage/record")
async def record_analysis_usage(
    current_user: dict = Depends(get_current_user)
):
    """분석 사용량 기록 (내부 호출용)"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 구독 정보 조회
    subscription = await db.user_subscriptions.find_one(
        {"user_id": user_id}
    )
    
    plan_id = subscription.get("plan_id", "free") if subscription else "free"
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    current_usage = subscription.get("analysis_used", 0) if subscription else 0
    limit = plan["analysis_limit"]
    
    # 무제한(-1)이 아니고 한도 초과 시
    if limit != -1 and current_usage >= limit:
        raise HTTPException(
            status_code=403, 
            detail=f"분석 한도 초과 ({current_usage}/{limit}). 플랜 업그레이드가 필요합니다."
        )
    
    # 사용량 증가
    await db.user_subscriptions.update_one(
        {"user_id": user_id},
        {
            "$inc": {"analysis_used": 1},
            "$set": {"last_analysis_at": datetime.now(timezone.utc).isoformat()}
        },
        upsert=True
    )
    
    return {
        "success": True,
        "usage": current_usage + 1,
        "limit": limit,
        "remaining": limit - current_usage - 1 if limit != -1 else "unlimited"
    }

@router.get("/usage/check")
async def check_usage_limit(
    current_user: dict = Depends(get_current_user)
):
    """사용량 한도 확인"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    subscription = await db.user_subscriptions.find_one(
        {"user_id": user_id},
        {"_id": 0}
    )
    
    plan_id = subscription.get("plan_id", "free") if subscription else "free"
    plan = SUBSCRIPTION_PLANS.get(plan_id, SUBSCRIPTION_PLANS["free"])
    
    current_usage = subscription.get("analysis_used", 0) if subscription else 0
    limit = plan["analysis_limit"]
    
    can_analyze = limit == -1 or current_usage < limit
    
    return {
        "can_analyze": can_analyze,
        "usage": current_usage,
        "limit": limit,
        "remaining": limit - current_usage if limit != -1 else "unlimited",
        "plan_id": plan_id
    }
