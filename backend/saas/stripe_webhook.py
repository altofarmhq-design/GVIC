"""
GVIC Stripe Webhook Handler
- Stripe 결제 이벤트 수신
- 결제 상태 업데이트
"""
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime, timezone, timedelta
import os
import logging

router = APIRouter(tags=["stripe-webhook"])
logger = logging.getLogger(__name__)

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

# 구독 플랜 정보 (payment_service와 동기화)
SUBSCRIPTION_PLANS = {
    "free": {"analysis_limit": 10, "products_limit": 3, "shops_limit": 1},
    "starter": {"analysis_limit": 50, "products_limit": 5, "shops_limit": 1},
    "growth": {"analysis_limit": 200, "products_limit": 20, "shops_limit": 3},
    "pro": {"analysis_limit": 1000, "products_limit": 50, "shops_limit": 10},
    "enterprise": {"analysis_limit": -1, "products_limit": -1, "shops_limit": -1}
}

@router.post("/api/webhook/stripe")
async def handle_stripe_webhook(request: Request):
    """Stripe 웹훅 처리"""
    from server import db
    from local_stripe import StripeCheckout
    
    try:
        # 요청 본문 읽기
        body = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        # 웹훅 처리
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY)
        webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        event = stripe_checkout.verify_webhook(body, signature, webhook_secret)
        
        if not event:
            raise HTTPException(status_code=400, detail="Invalid webhook")
        
        event_type = event.get("type", "")
        session_data = event.get("data", {}).get("object", {})
        session_id = session_data.get("id", "")
        payment_status = session_data.get("payment_status", "")
        metadata = session_data.get("metadata", {})
        
        logger.info(f"Webhook received: {event_type}, session: {session_id}, status: {payment_status}")
        
        # 결제 완료 이벤트 처리
        if event_type == "checkout.session.completed" and payment_status == "paid":
            # 트랜잭션 조회
            transaction = await db.payment_transactions.find_one(
                {"session_id": session_id}
            )
            
            if not transaction:
                logger.warning(f"Transaction not found for session: {session_id}")
                return {"status": "ok", "message": "Transaction not found"}
            
            # 이미 처리된 결제인지 확인
            if transaction.get("payment_status") == "paid":
                logger.info(f"Transaction already processed: {session_id}")
                return {"status": "ok", "message": "Already processed"}
            
            user_id = transaction.get("user_id")
            plan_id = transaction.get("plan_id")
            billing_cycle = transaction.get("billing_cycle", "monthly")
            
            # 트랜잭션 업데이트
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "complete",
                    "payment_status": "paid",
                    "paid_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # 구독 기간 계산
            now = datetime.now(timezone.utc)
            if billing_cycle == "yearly":
                period_end = now + timedelta(days=365)
            else:
                period_end = now + timedelta(days=30)
            
            # 구독 활성화
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
            
            logger.info(f"Subscription activated via webhook: {plan_id} for user {user_id}")
        
        # 결제 만료 이벤트
        elif event_type == "checkout.session.expired":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {"$set": {
                    "status": "expired",
                    "payment_status": "expired",
                    "expired_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            logger.info(f"Checkout session expired: {session_id}")
        
        return {"status": "ok", "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        # Stripe는 200 응답을 기대하므로 에러여도 200 반환
        return {"status": "error", "message": str(e)}
