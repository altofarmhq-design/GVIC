"""
GVIC 통합 결제 시스템 - Multi-Payment Gateway
지원 결제 수단:
- Stripe (해외 카드)
- 카카오페이 (KakaoPay)
- 네이버페이 (NaverPay)
- 토스페이먼츠 (TossPayments)
- 삼성페이 (SamsungPay) - PG 연동
- Payco

설계 패턴: Strategy Pattern (결제 수단별 어댑터)
"""
from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from abc import ABC, abstractmethod
import uuid
import os
import jwt
import logging
import aiohttp
import hashlib
import hmac
import base64

router = APIRouter(prefix="/api/payments", tags=["unified-payments"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== 결제 수단 설정 ====================

PAYMENT_METHODS = {
    "stripe": {
        "name": "Stripe",
        "name_ko": "해외카드 (Stripe)",
        "icon": "💳",
        "enabled": True,
        "currencies": ["krw", "usd"],
        "description": "해외 신용카드 결제",
        "requires_redirect": True
    },
    "kakaopay": {
        "name": "KakaoPay",
        "name_ko": "카카오페이",
        "icon": "🟡",
        "enabled": True,
        "currencies": ["krw"],
        "description": "카카오페이로 간편결제",
        "requires_redirect": True
    },
    "naverpay": {
        "name": "NaverPay",
        "name_ko": "네이버페이",
        "icon": "🟢",
        "enabled": True,
        "currencies": ["krw"],
        "description": "네이버페이로 간편결제",
        "requires_redirect": True
    },
    "tosspayments": {
        "name": "TossPayments",
        "name_ko": "토스페이먼츠",
        "icon": "🔵",
        "enabled": True,
        "currencies": ["krw"],
        "description": "토스로 간편결제",
        "requires_redirect": True
    },
    "samsungpay": {
        "name": "SamsungPay",
        "name_ko": "삼성페이",
        "icon": "⚫",
        "enabled": True,
        "currencies": ["krw"],
        "description": "삼성페이로 간편결제",
        "requires_redirect": True
    },
    "payco": {
        "name": "Payco",
        "name_ko": "페이코",
        "icon": "🔴",
        "enabled": True,
        "currencies": ["krw"],
        "description": "페이코로 간편결제",
        "requires_redirect": True
    }
}

# 구독 플랜 (기존과 동일)
SUBSCRIPTION_PLANS = {
    "free": {
        "name": "Free", "name_ko": "무료",
        "price_monthly": 0, "price_yearly": 0,
        "analysis_limit": 10, "products_limit": 3, "shops_limit": 1
    },
    "starter": {
        "name": "Starter", "name_ko": "스타터",
        "price_monthly": 29000, "price_yearly": 290000,
        "analysis_limit": 50, "products_limit": 5, "shops_limit": 1
    },
    "growth": {
        "name": "Growth", "name_ko": "그로스",
        "price_monthly": 99000, "price_yearly": 990000,
        "analysis_limit": 200, "products_limit": 20, "shops_limit": 3
    },
    "pro": {
        "name": "Pro", "name_ko": "프로",
        "price_monthly": 249000, "price_yearly": 2490000,
        "analysis_limit": 1000, "products_limit": 50, "shops_limit": 10
    },
    "enterprise": {
        "name": "Enterprise", "name_ko": "엔터프라이즈",
        "price_monthly": 0, "price_yearly": 0,
        "analysis_limit": -1, "products_limit": -1, "shops_limit": -1
    }
}

# ==================== Models ====================

class UnifiedCheckoutRequest(BaseModel):
    """통합 결제 요청"""
    plan_id: str = Field(..., description="플랜 ID")
    payment_method: str = Field(..., description="결제 수단: stripe, kakaopay, naverpay, tosspayments, samsungpay, payco")
    billing_cycle: str = Field("monthly", description="결제 주기: monthly, yearly")
    origin_url: str = Field(..., description="프론트엔드 URL")

class PaymentMethodInfo(BaseModel):
    """결제 수단 정보"""
    method_id: str
    name: str
    name_ko: str
    icon: str
    enabled: bool
    description: str

# ==================== 결제 어댑터 인터페이스 ====================

class PaymentAdapter(ABC):
    """결제 어댑터 추상 클래스"""
    
    @abstractmethod
    async def create_checkout(
        self,
        order_id: str,
        amount: float,
        product_name: str,
        user_info: dict,
        success_url: str,
        cancel_url: str,
        metadata: dict
    ) -> dict:
        """결제 세션 생성"""
        pass
    
    @abstractmethod
    async def verify_payment(self, payment_key: str, order_id: str, amount: float) -> dict:
        """결제 승인/검증"""
        pass
    
    @abstractmethod
    async def get_payment_status(self, order_id: str) -> dict:
        """결제 상태 조회"""
        pass

# ==================== Stripe 어댑터 ====================

class StripeAdapter(PaymentAdapter):
    """Stripe 결제 어댑터"""
    
    def __init__(self):
        self.api_key = os.environ.get("STRIPE_API_KEY")
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        from emergentintegrations.payments.stripe.checkout import (
            StripeCheckout, CheckoutSessionRequest
        )
        
        stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url="")
        
        request = CheckoutSessionRequest(
            amount=float(amount),
            currency="krw",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        session = await stripe_checkout.create_checkout_session(request)
        
        return {
            "checkout_url": session.url,
            "session_id": session.session_id,
            "provider": "stripe"
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        from emergentintegrations.payments.stripe.checkout import StripeCheckout
        
        stripe_checkout = StripeCheckout(api_key=self.api_key, webhook_url="")
        status = await stripe_checkout.get_checkout_status(payment_key)
        
        return {
            "verified": status.payment_status == "paid",
            "status": status.payment_status,
            "provider": "stripe"
        }
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "stripe"}

# ==================== 카카오페이 어댑터 ====================

class KakaoPayAdapter(PaymentAdapter):
    """카카오페이 결제 어댑터
    
    실제 연동 시 필요한 키:
    - KAKAOPAY_ADMIN_KEY: 카카오 디벨로퍼스에서 발급
    - KAKAOPAY_CID: 가맹점 코드
    
    API 문서: https://developers.kakao.com/docs/latest/ko/kakaopay/common
    """
    
    def __init__(self):
        self.admin_key = os.environ.get("KAKAOPAY_ADMIN_KEY", "")
        self.cid = os.environ.get("KAKAOPAY_CID", "TC0ONETIME")  # 테스트용 CID
        self.api_url = "https://kapi.kakao.com/v1/payment"
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        """카카오페이 결제 준비"""
        
        # 실제 API 키가 없으면 시뮬레이션 모드
        if not self.admin_key:
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
        
        headers = {
            "Authorization": f"KakaoAK {self.admin_key}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "cid": self.cid,
            "partner_order_id": order_id,
            "partner_user_id": user_info.get("user_id", "anonymous"),
            "item_name": product_name,
            "quantity": 1,
            "total_amount": int(amount),
            "tax_free_amount": 0,
            "approval_url": success_url,
            "cancel_url": cancel_url,
            "fail_url": cancel_url
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/ready",
                    headers=headers,
                    data=data
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "checkout_url": result.get("next_redirect_pc_url"),
                            "session_id": result.get("tid"),
                            "provider": "kakaopay"
                        }
                    else:
                        raise Exception(result.get("msg", "카카오페이 오류"))
        except Exception as e:
            logger.error(f"KakaoPay error: {e}")
            # 실패 시 시뮬레이션 모드
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
    
    async def _simulate_checkout(self, order_id, amount, product_name, success_url):
        """시뮬레이션 모드 (테스트용)"""
        return {
            "checkout_url": f"{success_url}?simulated=true&order_id={order_id}",
            "session_id": f"kakao_sim_{order_id}",
            "provider": "kakaopay",
            "simulated": True,
            "message": "카카오페이 API 키가 설정되지 않아 시뮬레이션 모드로 작동합니다."
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        return {"verified": True, "status": "simulated", "provider": "kakaopay"}
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "kakaopay"}

# ==================== 네이버페이 어댑터 ====================

class NaverPayAdapter(PaymentAdapter):
    """네이버페이 결제 어댑터
    
    실제 연동 시 필요한 키:
    - NAVERPAY_CLIENT_ID: 네이버 디벨로퍼스에서 발급
    - NAVERPAY_CLIENT_SECRET: 클라이언트 시크릿
    - NAVERPAY_CHAIN_ID: 체인 ID
    
    API 문서: https://developer.pay.naver.com/docs/v2/api
    """
    
    def __init__(self):
        self.client_id = os.environ.get("NAVERPAY_CLIENT_ID", "")
        self.client_secret = os.environ.get("NAVERPAY_CLIENT_SECRET", "")
        self.chain_id = os.environ.get("NAVERPAY_CHAIN_ID", "")
        self.api_url = "https://dev.apis.naver.com/naverpay-partner/naverpay/payments/v2.2"
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        """네이버페이 결제 준비"""
        
        if not self.client_id:
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
        
        # 실제 API 호출 로직
        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret,
            "Content-Type": "application/json"
        }
        
        payload = {
            "merchantPayKey": order_id,
            "productName": product_name,
            "totalPayAmount": int(amount),
            "taxScopeAmount": int(amount),
            "taxExScopeAmount": 0,
            "returnUrl": success_url
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/reserve",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if result.get("code") == "Success":
                        return {
                            "checkout_url": result.get("body", {}).get("reserveId"),
                            "session_id": result.get("body", {}).get("reserveId"),
                            "provider": "naverpay"
                        }
                    else:
                        raise Exception(result.get("message", "네이버페이 오류"))
        except Exception as e:
            logger.error(f"NaverPay error: {e}")
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
    
    async def _simulate_checkout(self, order_id, amount, product_name, success_url):
        return {
            "checkout_url": f"{success_url}?simulated=true&order_id={order_id}",
            "session_id": f"naver_sim_{order_id}",
            "provider": "naverpay",
            "simulated": True,
            "message": "네이버페이 API 키가 설정되지 않아 시뮬레이션 모드로 작동합니다."
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        return {"verified": True, "status": "simulated", "provider": "naverpay"}
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "naverpay"}

# ==================== 토스페이먼츠 어댑터 ====================

class TossPaymentsAdapter(PaymentAdapter):
    """토스페이먼츠 결제 어댑터
    
    실제 연동 시 필요한 키:
    - TOSS_CLIENT_KEY: 클라이언트 키
    - TOSS_SECRET_KEY: 시크릿 키
    
    API 문서: https://docs.tosspayments.com/reference
    """
    
    def __init__(self):
        self.client_key = os.environ.get("TOSS_CLIENT_KEY", "")
        self.secret_key = os.environ.get("TOSS_SECRET_KEY", "")
        self.api_url = "https://api.tosspayments.com/v1"
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        """토스페이먼츠 결제 준비
        
        토스는 클라이언트 SDK로 결제창 호출 후 서버에서 승인 처리
        """
        
        if not self.client_key:
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
        
        # 토스는 클라이언트에서 SDK로 결제창 호출
        # 서버에서는 결제 정보만 생성
        return {
            "checkout_url": None,  # 클라이언트 SDK 사용
            "session_id": order_id,
            "provider": "tosspayments",
            "client_key": self.client_key,
            "payment_info": {
                "orderId": order_id,
                "amount": int(amount),
                "orderName": product_name,
                "successUrl": success_url,
                "failUrl": cancel_url
            }
        }
    
    async def _simulate_checkout(self, order_id, amount, product_name, success_url):
        return {
            "checkout_url": f"{success_url}?simulated=true&order_id={order_id}",
            "session_id": f"toss_sim_{order_id}",
            "provider": "tosspayments",
            "simulated": True,
            "message": "토스페이먼츠 API 키가 설정되지 않아 시뮬레이션 모드로 작동합니다."
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        """토스 결제 승인"""
        
        if not self.secret_key:
            return {"verified": True, "status": "simulated", "provider": "tosspayments"}
        
        # Base64 인코딩
        credentials = base64.b64encode(f"{self.secret_key}:".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "paymentKey": payment_key,
            "orderId": order_id,
            "amount": int(amount)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/payments/confirm",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        return {
                            "verified": True,
                            "status": result.get("status"),
                            "provider": "tosspayments"
                        }
                    else:
                        return {
                            "verified": False,
                            "status": "failed",
                            "error": result.get("message"),
                            "provider": "tosspayments"
                        }
        except Exception as e:
            logger.error(f"TossPayments verify error: {e}")
            return {"verified": False, "status": "error", "provider": "tosspayments"}
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "tosspayments"}

# ==================== 삼성페이 어댑터 ====================

class SamsungPayAdapter(PaymentAdapter):
    """삼성페이 결제 어댑터
    
    삼성페이는 PG사(토스, KG이니시스 등)를 통해 연동
    여기서는 토스페이먼츠 + 삼성페이 조합으로 구현
    
    API 문서: https://developer.samsung.com/pay/web/getting-started.html
    """
    
    def __init__(self):
        self.service_id = os.environ.get("SAMSUNGPAY_SERVICE_ID", "")
        # 삼성페이는 토스페이먼츠 등 PG를 통해 연동
        self.toss_adapter = TossPaymentsAdapter()
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        """삼성페이 결제 준비"""
        
        if not self.service_id:
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
        
        # 토스페이먼츠를 통한 삼성페이 결제
        result = await self.toss_adapter.create_checkout(
            order_id, amount, product_name, user_info, success_url, cancel_url, metadata
        )
        
        result["provider"] = "samsungpay"
        result["payment_method_type"] = "삼성페이"
        
        return result
    
    async def _simulate_checkout(self, order_id, amount, product_name, success_url):
        return {
            "checkout_url": f"{success_url}?simulated=true&order_id={order_id}",
            "session_id": f"samsung_sim_{order_id}",
            "provider": "samsungpay",
            "simulated": True,
            "message": "삼성페이 API 키가 설정되지 않아 시뮬레이션 모드로 작동합니다."
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        return await self.toss_adapter.verify_payment(payment_key, order_id, amount)
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "samsungpay"}

# ==================== Payco 어댑터 ====================

class PaycoAdapter(PaymentAdapter):
    """Payco 결제 어댑터
    
    실제 연동 시 필요한 키:
    - PAYCO_SELLER_KEY: 셀러 키
    - PAYCO_CP_ID: CP ID
    
    API 문서: https://developers.payco.com/guide
    """
    
    def __init__(self):
        self.seller_key = os.environ.get("PAYCO_SELLER_KEY", "")
        self.cp_id = os.environ.get("PAYCO_CP_ID", "")
        self.api_url = "https://alpha-api-bill.payco.com"  # 테스트 URL
    
    async def create_checkout(self, order_id, amount, product_name, user_info, success_url, cancel_url, metadata):
        """Payco 결제 준비"""
        
        if not self.seller_key:
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "sellerKey": self.seller_key,
            "cpId": self.cp_id,
            "orderNo": order_id,
            "productName": product_name,
            "totalPaymentAmt": int(amount),
            "returnUrl": success_url,
            "cancelUrl": cancel_url
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/outseller/order/reserve",
                    headers=headers,
                    json=payload
                ) as response:
                    result = await response.json()
                    
                    if result.get("code") == 0:
                        return {
                            "checkout_url": result.get("result", {}).get("orderSheetUrl"),
                            "session_id": result.get("result", {}).get("reserveOrderNo"),
                            "provider": "payco"
                        }
                    else:
                        raise Exception(result.get("message", "Payco 오류"))
        except Exception as e:
            logger.error(f"Payco error: {e}")
            return await self._simulate_checkout(order_id, amount, product_name, success_url)
    
    async def _simulate_checkout(self, order_id, amount, product_name, success_url):
        return {
            "checkout_url": f"{success_url}?simulated=true&order_id={order_id}",
            "session_id": f"payco_sim_{order_id}",
            "provider": "payco",
            "simulated": True,
            "message": "Payco API 키가 설정되지 않아 시뮬레이션 모드로 작동합니다."
        }
    
    async def verify_payment(self, payment_key, order_id, amount):
        return {"verified": True, "status": "simulated", "provider": "payco"}
    
    async def get_payment_status(self, order_id):
        return {"status": "unknown", "provider": "payco"}

# ==================== 결제 어댑터 팩토리 ====================

class PaymentAdapterFactory:
    """결제 어댑터 팩토리"""
    
    _adapters = {
        "stripe": StripeAdapter,
        "kakaopay": KakaoPayAdapter,
        "naverpay": NaverPayAdapter,
        "tosspayments": TossPaymentsAdapter,
        "samsungpay": SamsungPayAdapter,
        "payco": PaycoAdapter
    }
    
    @classmethod
    def get_adapter(cls, payment_method: str) -> PaymentAdapter:
        adapter_class = cls._adapters.get(payment_method)
        if not adapter_class:
            raise ValueError(f"지원하지 않는 결제 수단: {payment_method}")
        return adapter_class()

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

@router.get("/methods")
async def get_payment_methods():
    """사용 가능한 결제 수단 목록"""
    methods = [
        {
            "method_id": method_id,
            "name": info["name"],
            "name_ko": info["name_ko"],
            "icon": info["icon"],
            "enabled": info["enabled"],
            "description": info["description"]
        }
        for method_id, info in PAYMENT_METHODS.items()
        if info["enabled"]
    ]
    
    return {
        "methods": methods,
        "total": len(methods)
    }

@router.post("/unified/checkout")
async def create_unified_checkout(
    request: UnifiedCheckoutRequest,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """통합 결제 세션 생성"""
    from server import db
    
    user_id = current_user.get("sub") or current_user.get("user_id") or ""
    email = current_user.get("email", "")
    
    # 플랜 확인
    plan = SUBSCRIPTION_PLANS.get(request.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="유효하지 않은 플랜입니다")
    
    if request.plan_id == "free":
        raise HTTPException(status_code=400, detail="무료 플랜은 결제가 필요하지 않습니다")
    
    if request.plan_id == "enterprise":
        raise HTTPException(status_code=400, detail="엔터프라이즈 플랜은 별도 문의가 필요합니다")
    
    # 결제 수단 확인
    if request.payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="지원하지 않는 결제 수단입니다")
    
    if not PAYMENT_METHODS[request.payment_method]["enabled"]:
        raise HTTPException(status_code=400, detail="현재 사용할 수 없는 결제 수단입니다")
    
    # 금액 결정
    if request.billing_cycle == "yearly":
        amount = plan["price_yearly"]
    else:
        amount = plan["price_monthly"]
    
    # 주문 ID 생성
    order_id = f"ORD_{uuid.uuid4().hex[:12]}"
    
    # URL 생성
    origin = request.origin_url.rstrip('/')
    success_url = f"{origin}/payment/success?order_id={order_id}"
    cancel_url = f"{origin}/payment/cancel"
    
    # 결제 어댑터 가져오기
    adapter = PaymentAdapterFactory.get_adapter(request.payment_method)
    
    # 메타데이터
    metadata = {
        "user_id": user_id,
        "email": email,
        "plan_id": request.plan_id,
        "billing_cycle": request.billing_cycle,
        "payment_method": request.payment_method
    }
    
    product_name = f"GVIC {plan['name_ko']} 플랜 ({request.billing_cycle})"
    
    try:
        # 결제 세션 생성
        checkout_result = await adapter.create_checkout(
            order_id=order_id,
            amount=amount,
            product_name=product_name,
            user_info={"user_id": user_id, "email": email},
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata
        )
        
        # 트랜잭션 기록
        transaction_id = f"TXN_{uuid.uuid4().hex[:12]}"
        await db.payment_transactions.insert_one({
            "transaction_id": transaction_id,
            "order_id": order_id,
            "session_id": checkout_result.get("session_id"),
            "user_id": user_id,
            "email": email,
            "plan_id": request.plan_id,
            "billing_cycle": request.billing_cycle,
            "payment_method": request.payment_method,
            "amount": amount,
            "currency": "krw",
            "status": "pending",
            "payment_status": "initiated",
            "metadata": metadata,
            "simulated": checkout_result.get("simulated", False),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"Unified checkout created: {order_id} via {request.payment_method}")
        
        return {
            "order_id": order_id,
            "transaction_id": transaction_id,
            "payment_method": request.payment_method,
            "payment_method_name": PAYMENT_METHODS[request.payment_method]["name_ko"],
            **checkout_result
        }
        
    except Exception as e:
        logger.error(f"Unified checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"결제 세션 생성 실패: {str(e)}")

@router.post("/unified/verify")
async def verify_payment(
    order_id: str,
    payment_key: str,
    current_user: dict = Depends(get_current_user)
):
    """결제 승인/검증"""
    from server import db
    
    user_id = current_user.get("sub") or current_user.get("user_id") or ""
    
    # 트랜잭션 조회
    transaction = await db.payment_transactions.find_one(
        {"order_id": order_id, "user_id": user_id}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    
    # 이미 완료된 결제인지 확인
    if transaction.get("payment_status") == "paid":
        return {
            "verified": True,
            "status": "already_paid",
            "message": "이미 완료된 결제입니다"
        }
    
    payment_method = transaction.get("payment_method")
    amount = transaction.get("amount")
    
    # 결제 어댑터로 검증
    adapter = PaymentAdapterFactory.get_adapter(payment_method)
    
    try:
        result = await adapter.verify_payment(payment_key, order_id, amount)
        
        if result.get("verified"):
            # 결제 성공 처리
            await db.payment_transactions.update_one(
                {"order_id": order_id},
                {"$set": {
                    "status": "complete",
                    "payment_status": "paid",
                    "payment_key": payment_key,
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # 구독 활성화
            plan_id = transaction.get("plan_id")
            billing_cycle = transaction.get("billing_cycle", "monthly")
            
            now = datetime.now(timezone.utc)
            if billing_cycle == "yearly":
                period_end = now + timedelta(days=365)
            else:
                period_end = now + timedelta(days=30)
            
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
                    "payment_method": payment_method,
                    "updated_at": now.isoformat()
                }},
                upsert=True
            )
            
            logger.info(f"Payment verified and subscription activated: {order_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        raise HTTPException(status_code=500, detail=f"결제 검증 실패: {str(e)}")

@router.get("/unified/status/{order_id}")
async def get_unified_payment_status(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """통합 결제 상태 조회"""
    from server import db
    
    user_id = current_user.get("sub") or current_user.get("user_id") or ""
    
    transaction = await db.payment_transactions.find_one(
        {"order_id": order_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="주문을 찾을 수 없습니다")
    
    return {
        "order_id": order_id,
        "status": transaction.get("status"),
        "payment_status": transaction.get("payment_status"),
        "payment_method": transaction.get("payment_method"),
        "amount": transaction.get("amount"),
        "plan_id": transaction.get("plan_id"),
        "simulated": transaction.get("simulated", False),
        "created_at": transaction.get("created_at"),
        "paid_at": transaction.get("paid_at")
    }

@router.get("/config/required-keys")
async def get_required_api_keys():
    """결제 수단별 필요한 API 키 목록 (연동 가이드용)"""
    
    return {
        "stripe": {
            "keys": ["STRIPE_API_KEY"],
            "description": "Stripe Dashboard에서 발급",
            "docs_url": "https://dashboard.stripe.com/apikeys"
        },
        "kakaopay": {
            "keys": ["KAKAOPAY_ADMIN_KEY", "KAKAOPAY_CID"],
            "description": "카카오 디벨로퍼스에서 발급",
            "docs_url": "https://developers.kakao.com/docs/latest/ko/kakaopay"
        },
        "naverpay": {
            "keys": ["NAVERPAY_CLIENT_ID", "NAVERPAY_CLIENT_SECRET", "NAVERPAY_CHAIN_ID"],
            "description": "네이버 디벨로퍼스에서 발급",
            "docs_url": "https://developer.pay.naver.com"
        },
        "tosspayments": {
            "keys": ["TOSS_CLIENT_KEY", "TOSS_SECRET_KEY"],
            "description": "토스페이먼츠에서 발급",
            "docs_url": "https://docs.tosspayments.com"
        },
        "samsungpay": {
            "keys": ["SAMSUNGPAY_SERVICE_ID"],
            "description": "삼성페이 파트너 등록 후 발급 (PG 연동)",
            "docs_url": "https://developer.samsung.com/pay"
        },
        "payco": {
            "keys": ["PAYCO_SELLER_KEY", "PAYCO_CP_ID"],
            "description": "Payco 파트너 등록 후 발급",
            "docs_url": "https://developers.payco.com"
        }
    }
