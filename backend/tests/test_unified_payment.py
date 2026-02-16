"""
Unified Payment System API Tests - GVIC 통합 결제 시스템
Tests for:
- GET /api/payments/methods - 결제 수단 목록 조회 (6개 결제 수단)
- POST /api/payments/unified/checkout - 통합 결제 세션 생성 (Stripe + 한국 결제 수단)
- POST /api/payments/unified/verify - 결제 승인/검증
- GET /api/payments/unified/status/{order_id} - 결제 상태 조회
- GET /api/payments/config/required-keys - 결제 수단별 필요 API 키 조회

지원 결제 수단:
- Stripe (해외 카드) - 실제 연동
- 카카오페이 (KakaoPay) - 시뮬레이션 모드
- 네이버페이 (NaverPay) - 시뮬레이션 모드
- 토스페이먼츠 (TossPayments) - 시뮬레이션 모드
- 삼성페이 (SamsungPay) - 시뮬레이션 모드
- Payco - 시뮬레이션 모드
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

# Payment methods to test
PAYMENT_METHODS = ["stripe", "kakaopay", "naverpay", "tosspayments", "samsungpay", "payco"]
KOREAN_PAYMENT_METHODS = ["kakaopay", "naverpay", "tosspayments", "samsungpay", "payco"]


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


# ==================== 결제 수단 목록 조회 테스트 ====================

class TestPaymentMethods(TestAuthSetup):
    """Payment Methods API Tests - /api/payments/methods"""
    
    def test_get_payment_methods(self):
        """GET /api/payments/methods - 결제 수단 목록 조회 (인증 불필요)"""
        response = requests.get(f"{BASE_URL}/api/payments/methods")
        
        assert response.status_code == 200, f"Get payment methods failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "methods" in data, "Missing methods"
        assert "total" in data, "Missing total"
        
        methods = data["methods"]
        assert data["total"] == 6, f"Expected 6 payment methods, got {data['total']}"
        assert len(methods) == 6, f"Expected 6 methods in list, got {len(methods)}"
        
        # Validate all expected payment methods are present
        method_ids = [m["method_id"] for m in methods]
        for expected_method in PAYMENT_METHODS:
            assert expected_method in method_ids, f"Missing payment method: {expected_method}"
        
        # Validate method structure
        for method in methods:
            assert "method_id" in method, "Missing method_id"
            assert "name" in method, "Missing name"
            assert "name_ko" in method, "Missing name_ko"
            assert "icon" in method, "Missing icon"
            assert "enabled" in method, "Missing enabled"
            assert "description" in method, "Missing description"
            assert method["enabled"] == True, f"Method {method['method_id']} should be enabled"
        
        print(f"✓ All 6 payment methods retrieved:")
        for method in methods:
            print(f"  - {method['method_id']}: {method['name_ko']} ({method['icon']})")
    
    def test_payment_methods_korean_names(self):
        """GET /api/payments/methods - 한국어 이름 확인"""
        response = requests.get(f"{BASE_URL}/api/payments/methods")
        
        assert response.status_code == 200
        data = response.json()
        
        expected_names = {
            "stripe": "해외카드 (Stripe)",
            "kakaopay": "카카오페이",
            "naverpay": "네이버페이",
            "tosspayments": "토스페이먼츠",
            "samsungpay": "삼성페이",
            "payco": "페이코"
        }
        
        for method in data["methods"]:
            method_id = method["method_id"]
            assert method["name_ko"] == expected_names[method_id], \
                f"Wrong name_ko for {method_id}: expected {expected_names[method_id]}, got {method['name_ko']}"
        
        print(f"✓ All Korean names verified correctly")


# ==================== 결제 수단별 필요 API 키 조회 테스트 ====================

class TestRequiredKeys(TestAuthSetup):
    """Required API Keys API Tests - /api/payments/config/required-keys"""
    
    def test_get_required_keys(self):
        """GET /api/payments/config/required-keys - 결제 수단별 필요 API 키 조회"""
        response = requests.get(f"{BASE_URL}/api/payments/config/required-keys")
        
        assert response.status_code == 200, f"Get required keys failed: {response.text}"
        data = response.json()
        
        # Validate all payment methods have key info
        for method in PAYMENT_METHODS:
            assert method in data, f"Missing key info for {method}"
            assert "keys" in data[method], f"Missing keys for {method}"
            assert "description" in data[method], f"Missing description for {method}"
            assert "docs_url" in data[method], f"Missing docs_url for {method}"
        
        # Validate specific keys
        assert "STRIPE_API_KEY" in data["stripe"]["keys"]
        assert "KAKAOPAY_ADMIN_KEY" in data["kakaopay"]["keys"]
        assert "NAVERPAY_CLIENT_ID" in data["naverpay"]["keys"]
        assert "TOSS_CLIENT_KEY" in data["tosspayments"]["keys"]
        assert "SAMSUNGPAY_SERVICE_ID" in data["samsungpay"]["keys"]
        assert "PAYCO_SELLER_KEY" in data["payco"]["keys"]
        
        print(f"✓ Required API keys info retrieved for all 6 payment methods")
        for method in PAYMENT_METHODS:
            print(f"  - {method}: {data[method]['keys']}")


# ==================== Stripe 결제 세션 생성 테스트 ====================

class TestStripeCheckout(TestAuthSetup):
    """Stripe Checkout API Tests - /api/payments/unified/checkout with stripe"""
    
    def test_create_stripe_checkout_starter(self, auth_headers):
        """POST /api/payments/unified/checkout - Stripe 스타터 플랜 결제 세션"""
        payload = {
            "plan_id": "starter",
            "payment_method": "stripe",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create Stripe checkout failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "order_id" in data, "Missing order_id"
        assert "transaction_id" in data, "Missing transaction_id"
        assert "payment_method" in data, "Missing payment_method"
        assert "payment_method_name" in data, "Missing payment_method_name"
        assert "checkout_url" in data, "Missing checkout_url"
        assert "session_id" in data, "Missing session_id"
        assert "provider" in data, "Missing provider"
        
        # Validate values
        assert data["payment_method"] == "stripe"
        assert data["payment_method_name"] == "해외카드 (Stripe)"
        assert data["provider"] == "stripe"
        assert data["order_id"].startswith("ORD_")
        assert data["transaction_id"].startswith("TXN_")
        
        # Stripe should return real checkout URL
        assert "checkout.stripe.com" in data["checkout_url"], "Expected Stripe checkout URL"
        assert data["session_id"].startswith("cs_"), "Expected Stripe session ID format"
        
        # Should NOT be simulated
        assert data.get("simulated") != True, "Stripe should not be simulated"
        
        print(f"✓ Stripe checkout session created")
        print(f"  - Order ID: {data['order_id']}")
        print(f"  - Session ID: {data['session_id'][:30]}...")
        print(f"  - Checkout URL: {data['checkout_url'][:50]}...")
        
        return data["order_id"]
    
    def test_create_stripe_checkout_growth_yearly(self, auth_headers):
        """POST /api/payments/unified/checkout - Stripe 그로스 플랜 연간 결제"""
        payload = {
            "plan_id": "growth",
            "payment_method": "stripe",
            "billing_cycle": "yearly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create Stripe checkout failed: {response.text}"
        data = response.json()
        
        assert data["payment_method"] == "stripe"
        assert "checkout.stripe.com" in data["checkout_url"]
        
        print(f"✓ Stripe growth yearly checkout created")


# ==================== 한국 결제 수단 시뮬레이션 테스트 ====================

class TestKoreanPaymentMethods(TestAuthSetup):
    """Korean Payment Methods Tests - Simulation Mode"""
    
    def test_create_kakaopay_checkout(self, auth_headers):
        """POST /api/payments/unified/checkout - 카카오페이 결제 세션 (시뮬레이션)"""
        payload = {
            "plan_id": "starter",
            "payment_method": "kakaopay",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create KakaoPay checkout failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data["payment_method"] == "kakaopay"
        assert data["payment_method_name"] == "카카오페이"
        assert data["provider"] == "kakaopay"
        assert data["simulated"] == True, "KakaoPay should be in simulation mode"
        assert "시뮬레이션" in data.get("message", ""), "Should have simulation message"
        assert data["session_id"].startswith("kakao_sim_")
        
        print(f"✓ KakaoPay checkout (simulated): {data['order_id']}")
        
        return data["order_id"]
    
    def test_create_naverpay_checkout(self, auth_headers):
        """POST /api/payments/unified/checkout - 네이버페이 결제 세션 (시뮬레이션)"""
        payload = {
            "plan_id": "growth",
            "payment_method": "naverpay",
            "billing_cycle": "yearly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create NaverPay checkout failed: {response.text}"
        data = response.json()
        
        assert data["payment_method"] == "naverpay"
        assert data["payment_method_name"] == "네이버페이"
        assert data["provider"] == "naverpay"
        assert data["simulated"] == True
        assert data["session_id"].startswith("naver_sim_")
        
        print(f"✓ NaverPay checkout (simulated): {data['order_id']}")
        
        return data["order_id"]
    
    def test_create_tosspayments_checkout(self, auth_headers):
        """POST /api/payments/unified/checkout - 토스페이먼츠 결제 세션 (시뮬레이션)"""
        payload = {
            "plan_id": "pro",
            "payment_method": "tosspayments",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create TossPayments checkout failed: {response.text}"
        data = response.json()
        
        assert data["payment_method"] == "tosspayments"
        assert data["payment_method_name"] == "토스페이먼츠"
        assert data["provider"] == "tosspayments"
        assert data["simulated"] == True
        assert data["session_id"].startswith("toss_sim_")
        
        print(f"✓ TossPayments checkout (simulated): {data['order_id']}")
        
        return data["order_id"]
    
    def test_create_samsungpay_checkout(self, auth_headers):
        """POST /api/payments/unified/checkout - 삼성페이 결제 세션 (시뮬레이션)"""
        payload = {
            "plan_id": "starter",
            "payment_method": "samsungpay",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create SamsungPay checkout failed: {response.text}"
        data = response.json()
        
        assert data["payment_method"] == "samsungpay"
        assert data["payment_method_name"] == "삼성페이"
        assert data["provider"] == "samsungpay"
        assert data["simulated"] == True
        assert data["session_id"].startswith("samsung_sim_")
        
        print(f"✓ SamsungPay checkout (simulated): {data['order_id']}")
        
        return data["order_id"]
    
    def test_create_payco_checkout(self, auth_headers):
        """POST /api/payments/unified/checkout - Payco 결제 세션 (시뮬레이션)"""
        payload = {
            "plan_id": "growth",
            "payment_method": "payco",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create Payco checkout failed: {response.text}"
        data = response.json()
        
        assert data["payment_method"] == "payco"
        assert data["payment_method_name"] == "페이코"
        assert data["provider"] == "payco"
        assert data["simulated"] == True
        assert data["session_id"].startswith("payco_sim_")
        
        print(f"✓ Payco checkout (simulated): {data['order_id']}")
        
        return data["order_id"]


# ==================== 결제 상태 조회 테스트 ====================

class TestPaymentStatus(TestAuthSetup):
    """Payment Status API Tests - /api/payments/unified/status/{order_id}"""
    
    @pytest.fixture(scope="class")
    def created_order(self, auth_headers):
        """Create a test order for status tests"""
        payload = {
            "plan_id": "starter",
            "payment_method": "kakaopay",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def test_get_payment_status(self, auth_headers, created_order):
        """GET /api/payments/unified/status/{order_id} - 결제 상태 조회"""
        if not created_order:
            pytest.skip("No order created for status test")
        
        order_id = created_order["order_id"]
        
        response = requests.get(
            f"{BASE_URL}/api/payments/unified/status/{order_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get payment status failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "order_id" in data, "Missing order_id"
        assert "status" in data, "Missing status"
        assert "payment_status" in data, "Missing payment_status"
        assert "payment_method" in data, "Missing payment_method"
        assert "amount" in data, "Missing amount"
        assert "plan_id" in data, "Missing plan_id"
        assert "simulated" in data, "Missing simulated"
        assert "created_at" in data, "Missing created_at"
        
        # Validate values
        assert data["order_id"] == order_id
        assert data["status"] == "pending"
        assert data["payment_status"] == "initiated"
        assert data["payment_method"] == "kakaopay"
        assert data["plan_id"] == "starter"
        assert data["amount"] == 29000  # Starter monthly price
        assert data["simulated"] == True
        
        print(f"✓ Payment status retrieved for {order_id}")
        print(f"  - Status: {data['status']}")
        print(f"  - Payment Status: {data['payment_status']}")
        print(f"  - Amount: ₩{data['amount']:,}")
    
    def test_get_payment_status_nonexistent(self, auth_headers):
        """GET /api/payments/unified/status/{order_id} - 존재하지 않는 주문 404"""
        response = requests.get(
            f"{BASE_URL}/api/payments/unified/status/ORD_nonexistent_12345",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent order returns 404 correctly")
    
    def test_get_payment_status_requires_auth(self):
        """GET /api/payments/unified/status/{order_id} - 인증 필수 401"""
        response = requests.get(f"{BASE_URL}/api/payments/unified/status/ORD_test")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Payment status requires authentication")


# ==================== 결제 승인/검증 테스트 ====================

class TestPaymentVerify(TestAuthSetup):
    """Payment Verify API Tests - /api/payments/unified/verify"""
    
    @pytest.fixture(scope="class")
    def created_order(self, auth_headers):
        """Create a test order for verify tests"""
        payload = {
            "plan_id": "starter",
            "payment_method": "payco",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def test_verify_payment_simulated(self, auth_headers, created_order):
        """POST /api/payments/unified/verify - 시뮬레이션 결제 승인"""
        if not created_order:
            pytest.skip("No order created for verify test")
        
        order_id = created_order["order_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/verify",
            params={"order_id": order_id, "payment_key": "test_payment_key"},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Verify payment failed: {response.text}"
        data = response.json()
        
        # Simulated payments should return verified=True
        assert "verified" in data, "Missing verified"
        assert "status" in data, "Missing status"
        assert "provider" in data, "Missing provider"
        
        assert data["verified"] == True, "Simulated payment should be verified"
        assert data["status"] == "simulated"
        assert data["provider"] == "payco"
        
        print(f"✓ Payment verified (simulated): {order_id}")
        print(f"  - Verified: {data['verified']}")
        print(f"  - Status: {data['status']}")
    
    def test_verify_payment_nonexistent(self, auth_headers):
        """POST /api/payments/unified/verify - 존재하지 않는 주문 404"""
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/verify",
            params={"order_id": "ORD_nonexistent_12345", "payment_key": "test"},
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent order verify returns 404 correctly")
    
    def test_verify_payment_requires_auth(self):
        """POST /api/payments/unified/verify - 인증 필수 401"""
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/verify",
            params={"order_id": "ORD_test", "payment_key": "test"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Payment verify requires authentication")


# ==================== 에러 케이스 테스트 ====================

class TestCheckoutErrors(TestAuthSetup):
    """Checkout Error Cases Tests"""
    
    def test_checkout_free_plan_error(self, auth_headers):
        """POST /api/payments/unified/checkout - 무료 플랜 결제 시도 400"""
        payload = {
            "plan_id": "free",
            "payment_method": "stripe",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "무료 플랜" in data.get("detail", ""), "Expected free plan error message"
        
        print(f"✓ Free plan checkout correctly rejected with 400")
    
    def test_checkout_enterprise_plan_error(self, auth_headers):
        """POST /api/payments/unified/checkout - 엔터프라이즈 플랜 결제 시도 400"""
        payload = {
            "plan_id": "enterprise",
            "payment_method": "stripe",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "엔터프라이즈" in data.get("detail", "") or "별도 문의" in data.get("detail", ""), \
            "Expected enterprise error message"
        
        print(f"✓ Enterprise plan checkout correctly rejected with 400")
    
    def test_checkout_invalid_plan_error(self, auth_headers):
        """POST /api/payments/unified/checkout - 유효하지 않은 플랜 400"""
        payload = {
            "plan_id": "invalid_plan",
            "payment_method": "stripe",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print(f"✓ Invalid plan checkout correctly rejected with 400")
    
    def test_checkout_invalid_payment_method_error(self, auth_headers):
        """POST /api/payments/unified/checkout - 지원하지 않는 결제 수단 400"""
        payload = {
            "plan_id": "starter",
            "payment_method": "invalid_method",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "지원하지 않는 결제 수단" in data.get("detail", ""), \
            "Expected invalid payment method error message"
        
        print(f"✓ Invalid payment method correctly rejected with 400")


# ==================== 인증 필수 테스트 ====================

class TestAuthRequired:
    """Test that all protected endpoints require authentication"""
    
    def test_unified_checkout_requires_auth(self):
        """POST /api/payments/unified/checkout - 인증 필수 401"""
        payload = {
            "plan_id": "starter",
            "payment_method": "stripe",
            "billing_cycle": "monthly",
            "origin_url": "https://example.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Unified checkout requires authentication")
    
    def test_unified_verify_requires_auth(self):
        """POST /api/payments/unified/verify - 인증 필수 401"""
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/verify",
            params={"order_id": "ORD_test", "payment_key": "test"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Unified verify requires authentication")
    
    def test_unified_status_requires_auth(self):
        """GET /api/payments/unified/status/{order_id} - 인증 필수 401"""
        response = requests.get(f"{BASE_URL}/api/payments/unified/status/ORD_test")
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✓ Unified status requires authentication")
    
    def test_payment_methods_no_auth_required(self):
        """GET /api/payments/methods - 인증 불필요 (공개 API)"""
        response = requests.get(f"{BASE_URL}/api/payments/methods")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Payment methods is public (no auth required)")
    
    def test_required_keys_no_auth_required(self):
        """GET /api/payments/config/required-keys - 인증 불필요 (공개 API)"""
        response = requests.get(f"{BASE_URL}/api/payments/config/required-keys")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print(f"✓ Required keys is public (no auth required)")


# ==================== 데이터 지속성 테스트 ====================

class TestDataPersistence(TestAuthSetup):
    """Test that payment transactions are persisted in database"""
    
    def test_checkout_creates_transaction_record(self, auth_headers):
        """POST /api/payments/unified/checkout - 트랜잭션 DB 기록 확인"""
        # Create checkout
        payload = {
            "plan_id": "starter",
            "payment_method": "naverpay",
            "billing_cycle": "monthly",
            "origin_url": "https://ecom-analyzer-6.preview.emergentagent.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/payments/unified/checkout",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        order_id = data["order_id"]
        
        # Verify transaction was persisted by checking status
        status_response = requests.get(
            f"{BASE_URL}/api/payments/unified/status/{order_id}",
            headers=auth_headers
        )
        
        assert status_response.status_code == 200, "Transaction should be persisted"
        status_data = status_response.json()
        
        assert status_data["order_id"] == order_id
        assert status_data["payment_method"] == "naverpay"
        assert status_data["plan_id"] == "starter"
        assert status_data["amount"] == 29000
        
        print(f"✓ Transaction persisted in database: {order_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
