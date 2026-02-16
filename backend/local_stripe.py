"""
Local Stripe Module - emergentintegrations 대체
로컬 환경에서 Stripe API를 직접 사용
"""
import os
import stripe
from typing import Optional, Dict, Any

class StripeCheckout:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("STRIPE_API_KEY", "")
        stripe.api_key = self.api_key
    
    def create_checkout_session(
        self,
        price_id: str = None,
        amount: int = None,
        currency: str = "krw",
        success_url: str = None,
        cancel_url: str = None,
        customer_email: str = None,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """체크아웃 세션 생성"""
        
        # API 키가 없으면 Mock
        if not self.api_key or "test" not in self.api_key:
            return self._mock_checkout_session(amount, currency)
        
        try:
            line_items = []
            if price_id:
                line_items.append({"price": price_id, "quantity": 1})
            elif amount:
                line_items.append({
                    "price_data": {
                        "currency": currency,
                        "unit_amount": amount,
                        "product_data": {"name": "GVIC Subscription"}
                    },
                    "quantity": 1
                })
            
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=line_items,
                mode="subscription" if price_id else "payment",
                success_url=success_url or "http://localhost:3000/success",
                cancel_url=cancel_url or "http://localhost:3000/cancel",
                customer_email=customer_email,
                metadata=metadata or {}
            )
            
            return {
                "session_id": session.id,
                "checkout_url": session.url,
                "status": "created"
            }
        except Exception as e:
            print(f"Stripe Error: {e}")
            return self._mock_checkout_session(amount, currency)
    
    def _mock_checkout_session(self, amount: int, currency: str) -> Dict[str, Any]:
        """Mock 체크아웃 세션"""
        import uuid
        return {
            "session_id": f"mock_session_{uuid.uuid4().hex[:8]}",
            "checkout_url": "http://localhost:3000/mock-checkout",
            "status": "mock",
            "message": "Stripe API 키를 설정하면 실제 결제가 가능합니다."
        }
    
    def verify_webhook(self, payload: bytes, signature: str, webhook_secret: str) -> Dict:
        """웹훅 검증"""
        try:
            event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
            return event
        except Exception as e:
            print(f"Webhook Error: {e}")
            return None


def create_checkout_session(*args, **kwargs):
    """편의 함수"""
    checkout = StripeCheckout()
    return checkout.create_checkout_session(*args, **kwargs)
