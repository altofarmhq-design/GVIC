"""
Shop Manager & Product Insights API Tests - GVIC SaaS Phase 1 & 2
Tests for:
- Shop Manager (쇼핑몰/제품 관리, API 키, 온보딩)
  - POST /api/shop/shops - 쇼핑몰 등록
  - GET /api/shop/shops - 쇼핑몰 목록 조회
  - GET /api/shop/shops/{shop_id} - 쇼핑몰 상세 조회
  - PUT /api/shop/shops/{shop_id} - 쇼핑몰 수정
  - DELETE /api/shop/shops/{shop_id} - 쇼핑몰 삭제
  - POST /api/shop/shops/{shop_id}/products - 제품 등록
  - GET /api/shop/shops/{shop_id}/products - 제품 목록 조회
  - GET /api/shop/products/{product_id} - 제품 상세 조회
  - PUT /api/shop/products/{product_id} - 제품 수정
  - DELETE /api/shop/products/{product_id} - 제품 삭제
  - PUT /api/shop/shops/{shop_id}/schedule - 분석 주기 설정
  - PUT /api/shop/shops/{shop_id}/webhook - 웹훅 설정
  - POST /api/shop/api-keys - API 키 발급
  - GET /api/shop/api-keys - API 키 목록
  - DELETE /api/shop/api-keys/{key_id} - API 키 삭제
  - GET /api/shop/onboarding/status - 온보딩 상태 조회
  - GET /api/shop/stats/overview - 쇼핑몰 통계

- Product Insights (4대 인사이트 분석 엔진)
  - POST /api/insights/analyze - 4대 인사이트 분석 (강점/건의/불만/신제품욕구)
  - GET /api/insights/product/{product_id} - 제품 분석 이력
  - GET /api/insights/analysis/{analysis_id} - 분석 상세 조회
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


# ==================== Shop Manager Tests ====================

class TestShopCRUD(TestAuthSetup):
    """Shop CRUD API Tests - /api/shop/shops/*"""
    
    @pytest.fixture(scope="class")
    def created_shop_id(self, auth_headers):
        """Create a test shop and return its ID"""
        payload = {
            "name": f"TEST_테스트쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "naver",
            "url": f"https://smartstore.naver.com/test_{uuid.uuid4().hex[:8]}",
            "description": "테스트용 쇼핑몰입니다"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create shop failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "shop_id" in data
        
        return data["shop_id"]
    
    def test_create_shop(self, auth_headers):
        """POST /api/shop/shops - 쇼핑몰 등록"""
        payload = {
            "name": f"TEST_신규쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "coupang",
            "url": f"https://www.coupang.com/vp/products/test_{uuid.uuid4().hex[:8]}",
            "description": "쿠팡 테스트 쇼핑몰"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create shop failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["success"] == True, "Expected success=True"
        assert "shop_id" in data, "Missing shop_id"
        assert data["shop_id"].startswith("shop_"), "shop_id should start with 'shop_'"
        assert "message" in data, "Missing message"
        
        print(f"✓ Shop created: {data['shop_id']}")
        print(f"  - Message: {data['message']}")
        
        return data["shop_id"]
    
    def test_create_shop_duplicate_url(self, auth_headers, created_shop_id):
        """POST /api/shop/shops - 중복 URL 등록 시 400 에러"""
        # First get the existing shop to get its URL
        response = requests.get(
            f"{BASE_URL}/api/shop/shops/{created_shop_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        existing_url = response.json()["url"]
        
        # Try to create with same URL
        payload = {
            "name": "중복 테스트",
            "platform": "naver",
            "url": existing_url,
            "description": "중복 URL 테스트"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400 for duplicate URL, got {response.status_code}"
        data = response.json()
        assert "이미 등록된" in data.get("detail", ""), "Expected duplicate error message"
        
        print(f"✓ Duplicate URL correctly rejected with 400")
    
    def test_get_shops_list(self, auth_headers, created_shop_id):
        """GET /api/shop/shops - 쇼핑몰 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/shops",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get shops failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "shops" in data, "Missing shops"
        assert "total" in data, "Missing total"
        assert isinstance(data["shops"], list), "shops should be a list"
        assert data["total"] >= 1, "Should have at least 1 shop"
        
        # Check shop structure
        if data["shops"]:
            shop = data["shops"][0]
            assert "shop_id" in shop, "Missing shop_id"
            assert "name" in shop, "Missing name"
            assert "platform" in shop, "Missing platform"
            assert "url" in shop, "Missing url"
            assert "is_active" in shop, "Missing is_active"
            assert "created_at" in shop, "Missing created_at"
        
        print(f"✓ Shops list retrieved: {data['total']} shops")
    
    def test_get_shop_detail(self, auth_headers, created_shop_id):
        """GET /api/shop/shops/{shop_id} - 쇼핑몰 상세 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/shops/{created_shop_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get shop detail failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["shop_id"] == created_shop_id, "shop_id mismatch"
        assert "name" in data, "Missing name"
        assert "platform" in data, "Missing platform"
        assert "url" in data, "Missing url"
        assert "is_active" in data, "Missing is_active"
        assert "products_count" in data, "Missing products_count"
        assert "products" in data, "Missing products list"
        
        print(f"✓ Shop detail retrieved: {data['name']}")
        print(f"  - Platform: {data['platform']}")
        print(f"  - Products count: {data['products_count']}")
    
    def test_get_shop_not_found(self, auth_headers):
        """GET /api/shop/shops/{shop_id} - 존재하지 않는 쇼핑몰 404"""
        fake_shop_id = f"shop_nonexistent_{uuid.uuid4().hex[:8]}"
        
        response = requests.get(
            f"{BASE_URL}/api/shop/shops/{fake_shop_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent shop returns 404 correctly")
    
    def test_update_shop(self, auth_headers, created_shop_id):
        """PUT /api/shop/shops/{shop_id} - 쇼핑몰 수정"""
        payload = {
            "name": f"TEST_수정된쇼핑몰_{uuid.uuid4().hex[:8]}",
            "description": "수정된 설명입니다"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{created_shop_id}",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update shop failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        assert "message" in data, "Missing message"
        
        # Verify update by getting shop detail
        verify_response = requests.get(
            f"{BASE_URL}/api/shop/shops/{created_shop_id}",
            headers=auth_headers
        )
        verify_data = verify_response.json()
        assert verify_data["description"] == "수정된 설명입니다", "Description not updated"
        
        print(f"✓ Shop updated successfully")
        print(f"  - New description: {verify_data['description']}")


class TestProductCRUD(TestAuthSetup):
    """Product CRUD API Tests - /api/shop/products/*"""
    
    @pytest.fixture(scope="class")
    def test_shop_id(self, auth_headers):
        """Create a test shop for product tests"""
        payload = {
            "name": f"TEST_제품테스트쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "naver",
            "url": f"https://smartstore.naver.com/product_test_{uuid.uuid4().hex[:8]}",
            "description": "제품 테스트용 쇼핑몰"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        return response.json()["shop_id"]
    
    @pytest.fixture(scope="class")
    def created_product_id(self, auth_headers, test_shop_id):
        """Create a test product and return its ID"""
        payload = {
            "name": f"TEST_테스트제품_{uuid.uuid4().hex[:8]}",
            "product_url": f"https://smartstore.naver.com/test/products/{uuid.uuid4().hex[:8]}",
            "product_id_external": f"EXT_{uuid.uuid4().hex[:8]}",
            "category": "의류",
            "price": "29,900원"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/products",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "product_id" in data
        
        return data["product_id"]
    
    def test_create_product(self, auth_headers, test_shop_id):
        """POST /api/shop/shops/{shop_id}/products - 제품 등록"""
        payload = {
            "name": f"TEST_신규제품_{uuid.uuid4().hex[:8]}",
            "product_url": f"https://smartstore.naver.com/test/products/{uuid.uuid4().hex[:8]}",
            "product_id_external": f"EXT_{uuid.uuid4().hex[:8]}",
            "category": "전자제품",
            "price": "99,000원"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/products",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create product failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["success"] == True, "Expected success=True"
        assert "product_id" in data, "Missing product_id"
        assert data["product_id"].startswith("prod_"), "product_id should start with 'prod_'"
        assert "message" in data, "Missing message"
        
        print(f"✓ Product created: {data['product_id']}")
        print(f"  - Message: {data['message']}")
        
        return data["product_id"]
    
    def test_create_product_invalid_shop(self, auth_headers):
        """POST /api/shop/shops/{shop_id}/products - 존재하지 않는 쇼핑몰에 제품 등록 시 404"""
        fake_shop_id = f"shop_nonexistent_{uuid.uuid4().hex[:8]}"
        
        payload = {
            "name": "테스트 제품",
            "product_url": "https://example.com/product/123"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops/{fake_shop_id}/products",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Product creation for non-existent shop returns 404")
    
    def test_get_products_list(self, auth_headers, test_shop_id, created_product_id):
        """GET /api/shop/shops/{shop_id}/products - 제품 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/products",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get products failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "shop_id" in data, "Missing shop_id"
        assert data["shop_id"] == test_shop_id, "shop_id mismatch"
        assert "products" in data, "Missing products"
        assert "total" in data, "Missing total"
        assert isinstance(data["products"], list), "products should be a list"
        assert data["total"] >= 1, "Should have at least 1 product"
        
        # Check product structure
        if data["products"]:
            product = data["products"][0]
            assert "product_id" in product, "Missing product_id"
            assert "name" in product, "Missing name"
            assert "product_url" in product, "Missing product_url"
            assert "is_active" in product, "Missing is_active"
        
        print(f"✓ Products list retrieved: {data['total']} products")
    
    def test_get_product_detail(self, auth_headers, created_product_id):
        """GET /api/shop/products/{product_id} - 제품 상세 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/products/{created_product_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get product detail failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["product_id"] == created_product_id, "product_id mismatch"
        assert "name" in data, "Missing name"
        assert "product_url" in data, "Missing product_url"
        assert "shop_id" in data, "Missing shop_id"
        assert "is_active" in data, "Missing is_active"
        assert "recent_analyses" in data, "Missing recent_analyses"
        
        print(f"✓ Product detail retrieved: {data['name']}")
        print(f"  - Category: {data.get('category', 'N/A')}")
        print(f"  - Price: {data.get('price', 'N/A')}")
    
    def test_update_product(self, auth_headers, created_product_id):
        """PUT /api/shop/products/{product_id} - 제품 수정"""
        payload = {
            "name": f"TEST_수정된제품_{uuid.uuid4().hex[:8]}",
            "price": "39,900원"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/products/{created_product_id}",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Update product failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        
        # Verify update
        verify_response = requests.get(
            f"{BASE_URL}/api/shop/products/{created_product_id}",
            headers=auth_headers
        )
        verify_data = verify_response.json()
        assert verify_data["price"] == "39,900원", "Price not updated"
        
        print(f"✓ Product updated successfully")
        print(f"  - New price: {verify_data['price']}")


class TestAnalysisSchedule(TestAuthSetup):
    """Analysis Schedule API Tests - /api/shop/shops/{shop_id}/schedule"""
    
    @pytest.fixture(scope="class")
    def test_shop_id(self, auth_headers):
        """Create a test shop for schedule tests"""
        payload = {
            "name": f"TEST_스케줄테스트쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "naver",
            "url": f"https://smartstore.naver.com/schedule_test_{uuid.uuid4().hex[:8]}",
            "description": "스케줄 테스트용 쇼핑몰"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        return response.json()["shop_id"]
    
    def test_set_daily_schedule(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/schedule - 일간 분석 주기 설정"""
        payload = {
            "frequency": "daily",
            "hour": 9,
            "timezone": "Asia/Seoul"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/schedule",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Set daily schedule failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        assert "schedule" in data, "Missing schedule"
        assert "next_analysis" in data, "Missing next_analysis"
        assert data["schedule"]["frequency"] == "daily", "Frequency mismatch"
        
        print(f"✓ Daily schedule set successfully")
        print(f"  - Next analysis: {data['next_analysis']}")
    
    def test_set_weekly_schedule(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/schedule - 주간 분석 주기 설정"""
        payload = {
            "frequency": "weekly",
            "day_of_week": 1,  # 화요일
            "hour": 10,
            "timezone": "Asia/Seoul"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/schedule",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Set weekly schedule failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        assert data["schedule"]["frequency"] == "weekly", "Frequency mismatch"
        assert data["schedule"]["day_of_week"] == 1, "day_of_week mismatch"
        
        print(f"✓ Weekly schedule set successfully")
        print(f"  - Day of week: {data['schedule']['day_of_week']} (화요일)")
    
    def test_set_weekly_schedule_missing_day(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/schedule - 주간 분석 시 요일 누락 400 에러"""
        payload = {
            "frequency": "weekly",
            "hour": 10,
            "timezone": "Asia/Seoul"
            # day_of_week 누락
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/schedule",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "요일" in data.get("detail", ""), "Expected day_of_week error message"
        
        print(f"✓ Weekly schedule without day_of_week correctly rejected")
    
    def test_set_monthly_schedule(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/schedule - 월간 분석 주기 설정"""
        payload = {
            "frequency": "monthly",
            "day_of_month": 15,
            "hour": 9,
            "timezone": "Asia/Seoul"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/schedule",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Set monthly schedule failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        assert data["schedule"]["frequency"] == "monthly", "Frequency mismatch"
        assert data["schedule"]["day_of_month"] == 15, "day_of_month mismatch"
        
        print(f"✓ Monthly schedule set successfully")
        print(f"  - Day of month: {data['schedule']['day_of_month']}")
    
    def test_set_monthly_schedule_missing_day(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/schedule - 월간 분석 시 일자 누락 400 에러"""
        payload = {
            "frequency": "monthly",
            "hour": 10,
            "timezone": "Asia/Seoul"
            # day_of_month 누락
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/schedule",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        data = response.json()
        assert "일자" in data.get("detail", ""), "Expected day_of_month error message"
        
        print(f"✓ Monthly schedule without day_of_month correctly rejected")


class TestWebhook(TestAuthSetup):
    """Webhook API Tests - /api/shop/shops/{shop_id}/webhook"""
    
    @pytest.fixture(scope="class")
    def test_shop_id(self, auth_headers):
        """Create a test shop for webhook tests"""
        payload = {
            "name": f"TEST_웹훅테스트쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "naver",
            "url": f"https://smartstore.naver.com/webhook_test_{uuid.uuid4().hex[:8]}",
            "description": "웹훅 테스트용 쇼핑몰"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        return response.json()["shop_id"]
    
    def test_set_webhook(self, auth_headers, test_shop_id):
        """PUT /api/shop/shops/{shop_id}/webhook - 웹훅 설정"""
        payload = {
            "url": "https://webhook.example.com/gvic",
            "events": ["analysis_complete", "alert"],
            "is_active": True
        }
        
        response = requests.put(
            f"{BASE_URL}/api/shop/shops/{test_shop_id}/webhook",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Set webhook failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        assert "webhook" in data, "Missing webhook"
        assert data["webhook"]["url"] == payload["url"], "URL mismatch"
        assert "secret" in data["webhook"], "Missing webhook secret"
        assert data["webhook"]["secret"].startswith("whsec_"), "Secret should start with 'whsec_'"
        
        print(f"✓ Webhook set successfully")
        print(f"  - URL: {data['webhook']['url']}")
        print(f"  - Events: {data['webhook']['events']}")
        print(f"  - Secret: {data['webhook']['secret'][:20]}...")


class TestAPIKeys(TestAuthSetup):
    """API Key Management Tests - /api/shop/api-keys/*"""
    
    @pytest.fixture(scope="class")
    def created_key_id(self, auth_headers):
        """Create a test API key and return its ID"""
        payload = {
            "name": f"TEST_API키_{uuid.uuid4().hex[:8]}",
            "permissions": ["read", "analyze"],
            "rate_limit": 1000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/api-keys",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create API key failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "key_id" in data
        
        return data["key_id"]
    
    def test_create_api_key(self, auth_headers):
        """POST /api/shop/api-keys - API 키 발급"""
        payload = {
            "name": f"TEST_신규API키_{uuid.uuid4().hex[:8]}",
            "permissions": ["read", "analyze", "write"],
            "rate_limit": 5000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/shop/api-keys",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create API key failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["success"] == True, "Expected success=True"
        assert "key_id" in data, "Missing key_id"
        assert data["key_id"].startswith("key_"), "key_id should start with 'key_'"
        assert "api_key" in data, "Missing api_key (shown only once)"
        assert data["api_key"].startswith("gvic_sk_"), "api_key should start with 'gvic_sk_'"
        assert "message" in data, "Missing message"
        
        print(f"✓ API key created: {data['key_id']}")
        print(f"  - API Key: {data['api_key'][:20]}... (shown only once)")
        print(f"  - Name: {data['name']}")
        
        return data["key_id"]
    
    def test_get_api_keys_list(self, auth_headers, created_key_id):
        """GET /api/shop/api-keys - API 키 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/api-keys",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get API keys failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "api_keys" in data, "Missing api_keys"
        assert "total" in data, "Missing total"
        assert isinstance(data["api_keys"], list), "api_keys should be a list"
        assert data["total"] >= 1, "Should have at least 1 API key"
        
        # Check key structure (should NOT include key_hash)
        if data["api_keys"]:
            key = data["api_keys"][0]
            assert "key_id" in key, "Missing key_id"
            assert "name" in key, "Missing name"
            assert "key_prefix" in key, "Missing key_prefix"
            assert "permissions" in key, "Missing permissions"
            assert "key_hash" not in key, "key_hash should not be exposed"
        
        print(f"✓ API keys list retrieved: {data['total']} keys")
    
    def test_delete_api_key(self, auth_headers):
        """DELETE /api/shop/api-keys/{key_id} - API 키 삭제"""
        # First create a key to delete
        create_payload = {
            "name": f"TEST_삭제용API키_{uuid.uuid4().hex[:8]}",
            "permissions": ["read"],
            "rate_limit": 100
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/shop/api-keys",
            json=create_payload,
            headers=auth_headers
        )
        
        assert create_response.status_code == 200
        key_id = create_response.json()["key_id"]
        
        # Now delete it
        response = requests.delete(
            f"{BASE_URL}/api/shop/api-keys/{key_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Delete API key failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True, "Expected success=True"
        
        print(f"✓ API key deleted: {key_id}")


class TestOnboarding(TestAuthSetup):
    """Onboarding Status API Tests - /api/shop/onboarding/*"""
    
    def test_get_onboarding_status(self, auth_headers):
        """GET /api/shop/onboarding/status - 온보딩 상태 조회"""
        response = requests.get(
            f"{BASE_URL}/api/shop/onboarding/status",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get onboarding status failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "steps" in data, "Missing steps"
        assert "completed_steps" in data, "Missing completed_steps"
        assert "total_steps" in data, "Missing total_steps"
        assert "progress_percent" in data, "Missing progress_percent"
        assert "is_complete" in data, "Missing is_complete"
        
        # Validate steps structure
        assert len(data["steps"]) == 5, "Should have 5 onboarding steps"
        for step in data["steps"]:
            assert "step" in step, "Missing step number"
            assert "name" in step, "Missing step name"
            assert "completed" in step, "Missing completed status"
        
        print(f"✓ Onboarding status retrieved")
        print(f"  - Progress: {data['progress_percent']}%")
        print(f"  - Completed: {data['completed_steps']}/{data['total_steps']}")
        print(f"  - Is complete: {data['is_complete']}")
        
        if data.get("next_step"):
            print(f"  - Next step: {data['next_step']['name']}")


class TestShopStats(TestAuthSetup):
    """Shop Statistics API Tests - /api/shop/stats/*"""
    
    def test_get_stats_overview(self, auth_headers):
        """GET /api/shop/stats/overview - 쇼핑몰 통계 개요"""
        response = requests.get(
            f"{BASE_URL}/api/shop/stats/overview",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get stats overview failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "shops_count" in data, "Missing shops_count"
        assert "products_count" in data, "Missing products_count"
        assert "analyses_count" in data, "Missing analyses_count"
        assert "api_calls_this_month" in data, "Missing api_calls_this_month"
        
        print(f"✓ Stats overview retrieved")
        print(f"  - Shops: {data['shops_count']}")
        print(f"  - Products: {data['products_count']}")
        print(f"  - Analyses: {data['analyses_count']}")
        print(f"  - API calls this month: {data['api_calls_this_month']}")


# ==================== Product Insights Tests ====================

class TestProductInsights(TestAuthSetup):
    """Product Insights API Tests - /api/insights/*"""
    
    @pytest.fixture(scope="class")
    def test_product_id(self, auth_headers):
        """Create a test shop and product for insights tests"""
        # Create shop
        shop_payload = {
            "name": f"TEST_인사이트테스트쇼핑몰_{uuid.uuid4().hex[:8]}",
            "platform": "naver",
            "url": f"https://smartstore.naver.com/insights_test_{uuid.uuid4().hex[:8]}",
            "description": "인사이트 테스트용 쇼핑몰"
        }
        
        shop_response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json=shop_payload,
            headers=auth_headers
        )
        
        assert shop_response.status_code == 200
        shop_id = shop_response.json()["shop_id"]
        
        # Create product
        product_payload = {
            "name": f"TEST_인사이트테스트제품_{uuid.uuid4().hex[:8]}",
            "product_url": f"https://smartstore.naver.com/test/products/{uuid.uuid4().hex[:8]}",
            "category": "의류",
            "price": "49,900원"
        }
        
        product_response = requests.post(
            f"{BASE_URL}/api/shop/shops/{shop_id}/products",
            json=product_payload,
            headers=auth_headers
        )
        
        assert product_response.status_code == 200
        return product_response.json()["product_id"]
    
    def test_analyze_four_insights(self, auth_headers, test_product_id):
        """POST /api/insights/analyze - 4대 인사이트 분석 (강점/건의/불만/신제품욕구)"""
        payload = {
            "product_id": test_product_id,
            "reviews": [
                # 강점 리뷰 (품질, 가성비, 배송)
                {"content": "품질이 정말 좋아요! 가성비 최고입니다. 배송도 빠르고 만족합니다.", "rating": 5, "date": "2025-01-15"},
                {"content": "퀄리티가 기대 이상이에요. 튼튼하고 고급스러워요. 재구매 의사 있습니다.", "rating": 5, "date": "2025-01-14"},
                {"content": "가격 대비 품질이 훌륭합니다. 디자인도 예쁘고 실용적이에요.", "rating": 5, "date": "2025-01-13"},
                
                # 건의사항 리뷰 (색상, 사이즈)
                {"content": "좋은 제품인데 색상이 더 다양했으면 좋겠어요. 다른 색깔도 추가해주세요.", "rating": 4, "date": "2025-01-12"},
                {"content": "큰 사이즈가 없어서 아쉬워요. 사이즈 추가 부탁드립니다.", "rating": 4, "date": "2025-01-11"},
                
                # 불만 리뷰 (품질불량, 배송지연)
                {"content": "배송이 너무 늦었어요. 일주일이나 걸렸습니다. 불량품이 왔어요.", "rating": 1, "date": "2025-01-10"},
                {"content": "제품에 하자가 있었어요. 교환 요청했는데 연락이 안 와요.", "rating": 1, "date": "2025-01-09"},
                {"content": "사진과 색상이 다르고 사이즈도 안 맞아요. 실망입니다.", "rating": 2, "date": "2025-01-08"},
                
                # 신제품 욕구 리뷰
                {"content": "방수 버전이 있었으면 좋겠어요. 무선 버전도 출시해주세요.", "rating": 4, "date": "2025-01-07"},
                {"content": "세트 상품이 있으면 좋겠어요. 패키지로 묶어서 팔아주세요.", "rating": 4, "date": "2025-01-06"}
            ],
            "analysis_depth": "standard"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/insights/analyze",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Analyze insights failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "analysis_id" in data, "Missing analysis_id"
        assert data["analysis_id"].startswith("INS_"), "analysis_id should start with 'INS_'"
        assert "product_id" in data, "Missing product_id"
        assert data["product_id"] == test_product_id, "product_id mismatch"
        assert "total_reviews" in data, "Missing total_reviews"
        assert data["total_reviews"] == 10, f"Expected 10 reviews, got {data['total_reviews']}"
        
        # Validate 4대 인사이트 구조
        assert "strengths" in data, "Missing strengths (강점)"
        assert "suggestions" in data, "Missing suggestions (건의사항)"
        assert "complaints" in data, "Missing complaints (불만)"
        assert "new_product_needs" in data, "Missing new_product_needs (신제품욕구)"
        
        # Validate 강점 인사이트
        strengths = data["strengths"]
        assert "items" in strengths, "Missing strengths.items"
        assert "total_count" in strengths, "Missing strengths.total_count"
        assert "top_strengths" in strengths, "Missing strengths.top_strengths"
        assert "recommendation" in strengths, "Missing strengths.recommendation"
        assert strengths["action"] == "유지/보강", "Strengths action should be '유지/보강'"
        
        # Validate 건의사항 인사이트
        suggestions = data["suggestions"]
        assert "items" in suggestions, "Missing suggestions.items"
        assert "total_count" in suggestions, "Missing suggestions.total_count"
        assert suggestions["action"] == "서비스 개선", "Suggestions action should be '서비스 개선'"
        
        # Validate 불만 인사이트
        complaints = data["complaints"]
        assert "items" in complaints, "Missing complaints.items"
        assert "total_count" in complaints, "Missing complaints.total_count"
        assert "severity_distribution" in complaints, "Missing complaints.severity_distribution"
        assert "drop_recommendation" in complaints, "Missing complaints.drop_recommendation"
        
        # Validate 신제품 욕구 인사이트
        new_product_needs = data["new_product_needs"]
        assert "items" in new_product_needs, "Missing new_product_needs.items"
        assert "total_count" in new_product_needs, "Missing new_product_needs.total_count"
        assert "development_priority" in new_product_needs, "Missing new_product_needs.development_priority"
        
        # Validate overall metrics
        assert "overall_score" in data, "Missing overall_score"
        assert "overall_trend" in data, "Missing overall_trend"
        assert "summary" in data, "Missing summary"
        assert "analyzed_at" in data, "Missing analyzed_at"
        
        print(f"✓ 4대 인사이트 분석 완료: {data['analysis_id']}")
        print(f"  - 총 리뷰: {data['total_reviews']}개")
        print(f"  - 종합 점수: {data['overall_score']}")
        print(f"  - 트렌드: {data['overall_trend']}")
        print(f"  - 강점: {strengths['total_count']}건 - {strengths['top_strengths']}")
        print(f"  - 건의사항: {suggestions['total_count']}건")
        print(f"  - 불만: {complaints['total_count']}건 (드롭 권장: {complaints['drop_recommendation']})")
        print(f"  - 신제품 욕구: {new_product_needs['total_count']}건 (우선순위: {new_product_needs['development_priority']})")
        print(f"  - 요약: {data['summary']}")
        
        return data["analysis_id"]
    
    def test_get_product_insights_history(self, auth_headers, test_product_id):
        """GET /api/insights/product/{product_id} - 제품 분석 이력 조회"""
        # First run an analysis to ensure there's history
        analyze_payload = {
            "product_id": test_product_id,
            "reviews": [
                {"content": "좋은 제품입니다. 품질이 훌륭해요.", "rating": 5},
                {"content": "가성비 최고! 재구매 의사 있습니다.", "rating": 5}
            ],
            "analysis_depth": "quick"
        }
        
        requests.post(
            f"{BASE_URL}/api/insights/analyze",
            json=analyze_payload,
            headers=auth_headers
        )
        
        # Now get history
        response = requests.get(
            f"{BASE_URL}/api/insights/product/{test_product_id}",
            params={"limit": 10},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get product insights failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "product_id" in data, "Missing product_id"
        assert data["product_id"] == test_product_id, "product_id mismatch"
        assert "analyses" in data, "Missing analyses"
        assert "total" in data, "Missing total"
        assert isinstance(data["analyses"], list), "analyses should be a list"
        assert data["total"] >= 1, "Should have at least 1 analysis"
        
        # Check analysis structure
        if data["analyses"]:
            analysis = data["analyses"][0]
            assert "analysis_id" in analysis, "Missing analysis_id"
            assert "overall_score" in analysis, "Missing overall_score"
            assert "analyzed_at" in analysis, "Missing analyzed_at"
        
        print(f"✓ Product insights history retrieved: {data['total']} analyses")
    
    def test_get_analysis_detail(self, auth_headers, test_product_id):
        """GET /api/insights/analysis/{analysis_id} - 분석 상세 조회"""
        # First run an analysis
        analyze_payload = {
            "product_id": test_product_id,
            "reviews": [
                {"content": "품질 좋고 배송 빠릅니다. 추천해요!", "rating": 5},
                {"content": "가격 대비 괜찮아요.", "rating": 4}
            ],
            "analysis_depth": "quick"
        }
        
        analyze_response = requests.post(
            f"{BASE_URL}/api/insights/analyze",
            json=analyze_payload,
            headers=auth_headers
        )
        
        assert analyze_response.status_code == 200
        analysis_id = analyze_response.json()["analysis_id"]
        
        # Now get detail
        response = requests.get(
            f"{BASE_URL}/api/insights/analysis/{analysis_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get analysis detail failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert data["analysis_id"] == analysis_id, "analysis_id mismatch"
        assert "product_id" in data, "Missing product_id"
        assert "strengths" in data, "Missing strengths"
        assert "suggestions" in data, "Missing suggestions"
        assert "complaints" in data, "Missing complaints"
        assert "new_product_needs" in data, "Missing new_product_needs"
        assert "overall_score" in data, "Missing overall_score"
        assert "summary" in data, "Missing summary"
        
        print(f"✓ Analysis detail retrieved: {analysis_id}")
        print(f"  - Overall score: {data['overall_score']}")
        print(f"  - Summary: {data['summary']}")
    
    def test_get_analysis_not_found(self, auth_headers):
        """GET /api/insights/analysis/{analysis_id} - 존재하지 않는 분석 404"""
        fake_analysis_id = f"INS_nonexistent_{uuid.uuid4().hex[:8]}"
        
        response = requests.get(
            f"{BASE_URL}/api/insights/analysis/{fake_analysis_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent analysis returns 404 correctly")


# ==================== Auth Required Tests ====================

class TestAuthRequired:
    """Test that all endpoints require authentication"""
    
    def test_shop_create_requires_auth(self):
        """POST /api/shop/shops - requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/shop/shops",
            json={"name": "test", "platform": "naver", "url": "https://test.com"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Shop create requires auth")
    
    def test_shop_list_requires_auth(self):
        """GET /api/shop/shops - requires auth"""
        response = requests.get(f"{BASE_URL}/api/shop/shops")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Shop list requires auth")
    
    def test_api_keys_requires_auth(self):
        """GET /api/shop/api-keys - requires auth"""
        response = requests.get(f"{BASE_URL}/api/shop/api-keys")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ API keys requires auth")
    
    def test_onboarding_requires_auth(self):
        """GET /api/shop/onboarding/status - requires auth"""
        response = requests.get(f"{BASE_URL}/api/shop/onboarding/status")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Onboarding status requires auth")
    
    def test_insights_analyze_requires_auth(self):
        """POST /api/insights/analyze - requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/insights/analyze",
            json={"product_id": "test", "reviews": []}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Insights analyze requires auth")
    
    def test_stats_requires_auth(self):
        """GET /api/shop/stats/overview - requires auth"""
        response = requests.get(f"{BASE_URL}/api/shop/stats/overview")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Stats overview requires auth")


# ==================== Cleanup Tests ====================

class TestCleanup(TestAuthSetup):
    """Cleanup test data after all tests"""
    
    def test_cleanup_test_shops(self, auth_headers):
        """Delete all TEST_ prefixed shops"""
        # Get all shops
        response = requests.get(
            f"{BASE_URL}/api/shop/shops",
            headers=auth_headers
        )
        
        if response.status_code == 200:
            shops = response.json().get("shops", [])
            deleted_count = 0
            
            for shop in shops:
                if shop.get("name", "").startswith("TEST_"):
                    delete_response = requests.delete(
                        f"{BASE_URL}/api/shop/shops/{shop['shop_id']}",
                        headers=auth_headers
                    )
                    if delete_response.status_code == 200:
                        deleted_count += 1
            
            print(f"✓ Cleanup: Deleted {deleted_count} test shops")
        else:
            print(f"✓ Cleanup: Could not retrieve shops for cleanup")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
