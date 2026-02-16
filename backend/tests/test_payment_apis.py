"""
Payment System API Tests - GVIC SaaS Phase 3
Tests for:
- GET /api/payments/plans - 구독 플랜 목록 조회
- GET /api/payments/plans/{plan_id} - 플랜 상세 조회
- POST /api/payments/checkout/session - 결제 세션 생성 (Stripe)
- GET /api/payments/checkout/status/{session_id} - 결제 상태 조회
- GET /api/payments/subscription/status - 현재 구독 상태 조회
- POST /api/payments/subscription/cancel - 구독 취소
- GET /api/payments/transactions - 결제 내역 조회
- POST /api/payments/usage/record - 사용량 기록
- GET /api/payments/usage/check - 사용량 한도 확인
- POST /api/webhook/stripe - Stripe 웹훅 처리
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

# Get BASE_URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
if not BASE_URL:
    raise ValueError("REACT_APP_BACKEND_URL environment variable is required")

# Test credentials
TEST_EMAIL = "admin@gvic.com"
TEST_PASSWORD = "gvicgvic!"


class TestAuthSetup:
    """Authentication setup for all tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get JWT token via login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "No token in login response"
        return data["token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


# ==================== 구독 플랜 조회 테스트 ====================

class TestSubscriptionPlans(TestAuthSetup):
    """Subscription Plans API Tests - /api/payments/plans/*"""
    
    def test_get_all_plans(self):
        """GET /api/payments/plans - 구독 플랜 목록 조회 (인증 불필요)"""
        response = requests.get(f"{BASE_URL}/api/payments/plans")
        
        assert response.status_code == 200, f"Get plans failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "plans" in data, "Missing plans"
        assert "currency" in data, "Missing currency"
        assert data["currency"] == "KRW", f"Expected KRW currency, got {data['currency']}"
        
        plans = data["plans"]
        assert len(plans) == 5, f"Expected 5 plans, got {len(plans)}"
        
        # Validate plan IDs
        plan_ids = [p["plan_id"] for p in plans]
        expected_ids = ["free", "starter", "growth", "pro", "enterprise"]
        for expected_id in expected_ids:
            assert expected_id in plan_ids, f"Missing plan: {expected_id}"
        
        print(f"✓ All plans retrieved: {len(plans)} plans")
        for plan in plans:
            print(f"  - {plan['plan_id']}: {plan['name_ko']} (₩{plan['price_monthly']:,.0f}/월)")
    
    def test_get_free_plan_detail(self):
        """GET /api/payments/plans/free - 무료 플랜 상세 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/free")
        
        assert response.status_code == 200, f"Get free plan failed: {response.text}"
        data = response.json()
        
        # Validate plan structure
        assert data["plan_id"] == "free", "Wrong plan_id"
        assert data["name"] == "Free", "Wrong name"
        assert data["name_ko"] == "무료", "Wrong name_ko"
        assert data["price_monthly"] == 0.0, "Free plan should have 0 price"
        assert data["price_yearly"] == 0.0, "Free plan should have 0 yearly price"
        assert data["analysis_limit"] == 10, f"Expected 10 analysis limit, got {data['analysis_limit']}"
        assert data["products_limit"] == 3, f"Expected 3 products limit, got {data['products_limit']}"
        assert data["shops_limit"] == 1, f"Expected 1 shop limit, got {data['shops_limit']}"
        
        print(f"✓ Free plan details verified")
        print(f"  - Analysis limit: {data['analysis_limit']}")
        print(f"  - Products limit: {data['products_limit']}")
        print(f"  - Features: {data['features']}")
    
    def test_get_starter_plan_detail(self):
        """GET /api/payments/plans/starter - 스타터 플랜 상세 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/starter")
        
        assert response.status_code == 200, f"Get starter plan failed: {response.text}"
        data = response.json()
        
        assert data["plan_id"] == "starter", "Wrong plan_id"
        assert data["price_monthly"] == 29000.0, f"Expected ₩29,000, got {data['price_monthly']}"
        assert data["price_yearly"] == 290000.0, f"Expected ₩290,000, got {data['price_yearly']}"
        assert data["analysis_limit"] == 50, f"Expected 50 analysis limit, got {data['analysis_limit']}"
        
        print(f"✓ Starter plan: ₩{data['price_monthly']:,.0f}/월, {data['analysis_limit']} 분석")
    
    def test_get_growth_plan_detail(self):
        """GET /api/payments/plans/growth - 그로스 플랜 상세 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/growth")
        
        assert response.status_code == 200, f"Get growth plan failed: {response.text}"
        data = response.json()
        
        assert data["plan_id"] == "growth", "Wrong plan_id"
        assert data["price_monthly"] == 99000.0, f"Expected ₩99,000, got {data['price_monthly']}"
        assert data["analysis_limit"] == 200, f"Expected 200 analysis limit, got {data['analysis_limit']}"
        assert data["shops_limit"] == 3, f"Expected 3 shops limit, got {data['shops_limit']}"
        
        print(f"✓ Growth plan: ₩{data['price_monthly']:,.0f}/월, {data['analysis_limit']} 분석, {data['shops_limit']} 샵")
    
    def test_get_pro_plan_detail(self):
        """GET /api/payments/plans/pro - 프로 플랜 상세 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/pro")
        
        assert response.status_code == 200, f"Get pro plan failed: {response.text}"
        data = response.json()
        
        assert data["plan_id"] == "pro", "Wrong plan_id"
        assert data["price_monthly"] == 249000.0, f"Expected ₩249,000, got {data['price_monthly']}"
        assert data["analysis_limit"] == 1000, f"Expected 1000 analysis limit, got {data['analysis_limit']}"
        assert data["shops_limit"] == 10, f"Expected 10 shops limit, got {data['shops_limit']}"
        
        print(f"✓ Pro plan: ₩{data['price_monthly']:,.0f}/월, {data['analysis_limit']} 분석, {data['shops_limit']} 샵")
    
    def test_get_enterprise_plan_detail(self):
        """GET /api/payments/plans/enterprise - 엔터프라이즈 플랜 상세 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/enterprise")
        
        assert response.status_code == 200, f"Get enterprise plan failed: {response.text}"
        data = response.json()
        
        assert data["plan_id"] == "enterprise", "Wrong plan_id"
        assert data["price_monthly"] == 0.0, "Enterprise should have 0 price (협의)"
        assert data["analysis_limit"] == -1, "Enterprise should have unlimited (-1) analysis"
        assert data["products_limit"] == -1, "Enterprise should have unlimited products"
        assert data["shops_limit"] == -1, "Enterprise should have unlimited shops"
        
        print(f"✓ Enterprise plan: 협의, 무제한 분석/제품/샵")
    
    def test_get_nonexistent_plan(self):
        """GET /api/payments/plans/invalid - 존재하지 않는 플랜 404"""
        response = requests.get(f"{BASE_URL}/api/payments/plans/invalid_plan")
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent plan returns 404 correctly")


# ==================== 결제 세션 생성 테스트 ====================

class TestCheckoutSession(TestAuthSetup):
    """Checkout Session API Tests - /api/payments/checkout/*"""
    
    def test_create_checkout_session_starter(self, auth_headers):
        """POST /api/payments/checkout/session - 스타터 플랜 결제 세션 생성"""
        payload = {
            "plan_id": "starter",
            "billing_cycle": "monthly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create checkout session failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "url" in data, "Missing checkout URL"
        assert "session_id" in data, "Missing session_id"
        assert "transaction_id" in data, "Missing transaction_id"
        
        # Validate URL is Stripe checkout
        assert "checkout.stripe.com" in data["url"], f"Expected Stripe URL, got {data['url']}"
        
        # Validate session_id format
        assert data["session_id"].startswith("cs_"), f"Invalid session_id format: {data['session_id']}"
        
        # Validate transaction_id format
        assert data["transaction_id"].startswith("TXN_"), f"Invalid transaction_id format: {data['transaction_id']}"
        
        print(f"✓ Checkout session created for starter plan")
        print(f"  - Session ID: {data['session_id'][:30]}...")
        print(f"  - Transaction ID: {data['transaction_id']}")
        print(f"  - Checkout URL: {data['url'][:50]}...")
        
        return data["session_id"]
    
    def test_create_checkout_session_growth_yearly(self, auth_headers):
        """POST /api/payments/checkout/session - 그로스 플랜 연간 결제 세션"""
        payload = {
            "plan_id": "growth",
            "billing_cycle": "yearly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create checkout session failed: {response.text}"
        data = response.json()
        
        assert "url" in data, "Missing checkout URL"
        assert "session_id" in data, "Missing session_id"
        
        print(f"✓ Checkout session created for growth yearly plan")
        print(f"  - Session ID: {data['session_id'][:30]}...")
    
    def test_create_checkout_session_pro(self, auth_headers):
        """POST /api/payments/checkout/session - 프로 플랜 결제 세션"""
        payload = {
            "plan_id": "pro",
            "billing_cycle": "monthly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create checkout session failed: {response.text}"
        data = response.json()
        
        assert "url" in data, "Missing checkout URL"
        print(f"✓ Checkout session created for pro plan")
    
    def test_create_checkout_session_free_plan_error(self, auth_headers):
        """POST /api/payments/checkout/session - 무료 플랜 결제 시도 400"""
        payload = {
            "plan_id": "free",
            "billing_cycle": "monthly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "무료 플랜" in data.get("detail", ""), f"Expected free plan error message"
        
        print(f"✓ Free plan checkout correctly rejected with 400")
    
    def test_create_checkout_session_enterprise_error(self, auth_headers):
        """POST /api/payments/checkout/session - 엔터프라이즈 플랜 결제 시도 400"""
        payload = {
            "plan_id": "enterprise",
            "billing_cycle": "monthly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "엔터프라이즈" in data.get("detail", "") or "별도 문의" in data.get("detail", ""), \
            f"Expected enterprise error message"
        
        print(f"✓ Enterprise plan checkout correctly rejected with 400")
    
    def test_create_checkout_session_invalid_plan(self, auth_headers):
        """POST /api/payments/checkout/session - 유효하지 않은 플랜 400"""
        payload = {
            "plan_id": "invalid_plan",
            "billing_cycle": "monthly",
            "origin_url": "https://reviewhub-46.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invalid plan checkout correctly rejected with 400")
    
    def test_create_checkout_session_requires_auth(self):
        """POST /api/payments/checkout/session - 인증 필수 401"""
        payload = {
            "plan_id": "starter",
            "billing_cycle": "monthly",
            "origin_url": "https://example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json=payload
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Checkout session requires authentication")


# ==================== 결제 상태 조회 테스트 ====================

class TestCheckoutStatus(TestAuthSetup):
    """Checkout Status API Tests - /api/payments/checkout/status/*"""
    
    def test_get_checkout_status_nonexistent(self, auth_headers):
        """GET /api/payments/checkout/status/{session_id} - 존재하지 않는 세션 404"""
        fake_session_id = "cs_test_nonexistent_session_12345"
        
        response = requests.get(
            f"{BASE_URL}/api/payments/checkout/status/{fake_session_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent session returns 404 correctly")
    
    def test_get_checkout_status_requires_auth(self):
        """GET /api/payments/checkout/status/{session_id} - 인증 필수 401"""
        response = requests.get(
            f"{BASE_URL}/api/payments/checkout/status/cs_test_session"
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Checkout status requires authentication")


# ==================== 구독 상태 조회 테스트 ====================

class TestSubscriptionStatus(TestAuthSetup):
    """Subscription Status API Tests - /api/payments/subscription/*"""
    
    def test_get_subscription_status(self, auth_headers):
        """GET /api/payments/subscription/status - 현재 구독 상태 조회"""
        response = requests.get(
            f"{BASE_URL}/api/payments/subscription/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get subscription status failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "plan_id" in data, "Missing plan_id"
        assert "plan_name" in data, "Missing plan_name"
        assert "status" in data, "Missing status"
        assert "analysis_used" in data, "Missing analysis_used"
        assert "analysis_limit" in data, "Missing analysis_limit"
        assert "products_limit" in data, "Missing products_limit"
        assert "shops_limit" in data, "Missing shops_limit"
        
        # Validate data types
        assert isinstance(data["analysis_used"], int), "analysis_used should be int"
        assert isinstance(data["analysis_limit"], int), "analysis_limit should be int"
        
        print(f"✓ Subscription status retrieved")
        print(f"  - Plan: {data['plan_id']} ({data['plan_name']})")
        print(f"  - Status: {data['status']}")
        print(f"  - Analysis: {data['analysis_used']}/{data['analysis_limit']}")
        print(f"  - Products limit: {data['products_limit']}")
        print(f"  - Shops limit: {data['shops_limit']}")
    
    def test_get_subscription_status_requires_auth(self):
        """GET /api/payments/subscription/status - 인증 필수 401"""
        response = requests.get(f"{BASE_URL}/api/payments/subscription/status")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Subscription status requires authentication")


# ==================== 구독 취소 테스트 ====================

class TestSubscriptionCancel(TestAuthSetup):
    """Subscription Cancel API Tests - /api/payments/subscription/cancel"""
    
    def test_cancel_subscription_free_plan_error(self, auth_headers):
        """POST /api/payments/subscription/cancel - 무료 플랜 취소 시도 400"""
        # First check current subscription
        status_response = requests.get(
            f"{BASE_URL}/api/payments/subscription/status",
            headers=auth_headers
        )
        
        if status_response.status_code == 200:
            current_plan = status_response.json().get("plan_id", "free")
            
            if current_plan == "free":
                # Try to cancel free plan - should fail
                response = requests.post(
                    f"{BASE_URL}/api/payments/subscription/cancel",
                    headers=auth_headers
                )
                
                assert response.status_code == 400, f"Expected 400, got {response.status_code}"
                data = response.json()
                assert "무료 플랜" in data.get("detail", "") or "활성 구독" in data.get("detail", ""), \
                    f"Expected free plan cancel error"
                
                print(f"✓ Free plan cancel correctly rejected with 400")
            else:
                print(f"⚠ User has {current_plan} plan, skipping free plan cancel test")
    
    def test_cancel_subscription_requires_auth(self):
        """POST /api/payments/subscription/cancel - 인증 필수 401"""
        response = requests.post(f"{BASE_URL}/api/payments/subscription/cancel")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Subscription cancel requires authentication")


# ==================== 결제 내역 조회 테스트 ====================

class TestPaymentTransactions(TestAuthSetup):
    """Payment Transactions API Tests - /api/payments/transactions"""
    
    def test_get_transactions(self, auth_headers):
        """GET /api/payments/transactions - 결제 내역 조회"""
        response = requests.get(
            f"{BASE_URL}/api/payments/transactions",
            params={"limit": 20},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get transactions failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "transactions" in data, "Missing transactions"
        assert "total" in data, "Missing total"
        assert isinstance(data["transactions"], list), "transactions should be a list"
        
        print(f"✓ Transactions retrieved: {data['total']} records")
        
        if data["transactions"]:
            for txn in data["transactions"][:3]:
                print(f"  - {txn.get('transaction_id', 'N/A')}: {txn.get('plan_id', 'N/A')} - {txn.get('status', 'N/A')}")
    
    def test_get_transactions_requires_auth(self):
        """GET /api/payments/transactions - 인증 필수 401"""
        response = requests.get(f"{BASE_URL}/api/payments/transactions")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Transactions requires authentication")


# ==================== 사용량 추적 테스트 ====================

class TestUsageTracking(TestAuthSetup):
    """Usage Tracking API Tests - /api/payments/usage/*"""
    
    def test_check_usage_limit(self, auth_headers):
        """GET /api/payments/usage/check - 사용량 한도 확인"""
        response = requests.get(
            f"{BASE_URL}/api/payments/usage/check",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Check usage failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "can_analyze" in data, "Missing can_analyze"
        assert "usage" in data, "Missing usage"
        assert "limit" in data, "Missing limit"
        assert "remaining" in data, "Missing remaining"
        assert "plan_id" in data, "Missing plan_id"
        
        # Validate data types
        assert isinstance(data["can_analyze"], bool), "can_analyze should be bool"
        assert isinstance(data["usage"], int), "usage should be int"
        
        print(f"✓ Usage check completed")
        print(f"  - Plan: {data['plan_id']}")
        print(f"  - Can analyze: {data['can_analyze']}")
        print(f"  - Usage: {data['usage']}/{data['limit']}")
        print(f"  - Remaining: {data['remaining']}")
    
    def test_record_usage(self, auth_headers):
        """POST /api/payments/usage/record - 사용량 기록"""
        # First check current usage
        check_response = requests.get(
            f"{BASE_URL}/api/payments/usage/check",
            headers=auth_headers
        )
        
        if check_response.status_code == 200:
            current_data = check_response.json()
            current_usage = current_data.get("usage", 0)
            can_analyze = current_data.get("can_analyze", False)
            
            if can_analyze:
                # Record usage
                response = requests.post(
                    f"{BASE_URL}/api/payments/usage/record",
                    headers=auth_headers
                )
                
                assert response.status_code == 200, f"Record usage failed: {response.text}"
                data = response.json()
                
                # Validate response
                assert data["success"] == True, "Expected success=True"
                assert "usage" in data, "Missing usage"
                assert "limit" in data, "Missing limit"
                assert "remaining" in data, "Missing remaining"
                
                # Verify usage increased
                assert data["usage"] == current_usage + 1, \
                    f"Expected usage {current_usage + 1}, got {data['usage']}"
                
                print(f"✓ Usage recorded successfully")
                print(f"  - New usage: {data['usage']}/{data['limit']}")
                print(f"  - Remaining: {data['remaining']}")
            else:
                print(f"⚠ Cannot record usage - limit reached ({current_usage}/{current_data.get('limit', 0)})")
    
    def test_usage_check_requires_auth(self):
        """GET /api/payments/usage/check - 인증 필수 401"""
        response = requests.get(f"{BASE_URL}/api/payments/usage/check")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Usage check requires authentication")
    
    def test_usage_record_requires_auth(self):
        """POST /api/payments/usage/record - 인증 필수 401"""
        response = requests.post(f"{BASE_URL}/api/payments/usage/record")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Usage record requires authentication")


# ==================== Stripe 웹훅 테스트 ====================

class TestStripeWebhook(TestAuthSetup):
    """Stripe Webhook API Tests - /api/webhook/stripe"""
    
    def test_webhook_endpoint_exists(self):
        """POST /api/webhook/stripe - 웹훅 엔드포인트 존재 확인"""
        # Send empty body - should not crash, may return error but endpoint exists
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            headers={"Content-Type": "application/json"},
            data="{}"
        )
        
        # Webhook should return 200 even on error (Stripe expects 200)
        # Or it may return 422 for validation error
        assert response.status_code in [200, 422, 400], \
            f"Unexpected status code: {response.status_code}"
        
        print(f"✓ Stripe webhook endpoint exists (status: {response.status_code})")
    
    def test_webhook_handles_invalid_signature(self):
        """POST /api/webhook/stripe - 잘못된 서명 처리"""
        # Send with fake signature
        response = requests.post(
            f"{BASE_URL}/api/webhook/stripe",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": "t=1234567890,v1=fake_signature"
            },
            json={
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "id": "cs_test_fake",
                        "payment_status": "paid"
                    }
                }
            }
        )
        
        # Should return 200 (Stripe expects 200 even on error)
        # The webhook handler catches exceptions and returns 200
        assert response.status_code in [200, 400, 422], \
            f"Unexpected status code: {response.status_code}"
        
        print(f"✓ Webhook handles invalid signature (status: {response.status_code})")


# ==================== 인증 필수 테스트 ====================

class TestAuthRequired:
    """Test that all protected endpoints require authentication"""
    
    def test_checkout_session_requires_auth(self):
        """POST /api/payments/checkout/session - 인증 필수"""
        response = requests.post(
            f"{BASE_URL}/api/payments/checkout/session",
            json={"plan_id": "starter", "billing_cycle": "monthly", "origin_url": "https://example.com"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Checkout session requires auth")
    
    def test_checkout_status_requires_auth(self):
        """GET /api/payments/checkout/status/{session_id} - 인증 필수"""
        response = requests.get(f"{BASE_URL}/api/payments/checkout/status/cs_test")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Checkout status requires auth")
    
    def test_subscription_status_requires_auth(self):
        """GET /api/payments/subscription/status - 인증 필수"""
        response = requests.get(f"{BASE_URL}/api/payments/subscription/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Subscription status requires auth")
    
    def test_subscription_cancel_requires_auth(self):
        """POST /api/payments/subscription/cancel - 인증 필수"""
        response = requests.post(f"{BASE_URL}/api/payments/subscription/cancel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Subscription cancel requires auth")
    
    def test_transactions_requires_auth(self):
        """GET /api/payments/transactions - 인증 필수"""
        response = requests.get(f"{BASE_URL}/api/payments/transactions")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Transactions requires auth")
    
    def test_usage_check_requires_auth(self):
        """GET /api/payments/usage/check - 인증 필수"""
        response = requests.get(f"{BASE_URL}/api/payments/usage/check")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Usage check requires auth")
    
    def test_usage_record_requires_auth(self):
        """POST /api/payments/usage/record - 인증 필수"""
        response = requests.post(f"{BASE_URL}/api/payments/usage/record")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Usage record requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
