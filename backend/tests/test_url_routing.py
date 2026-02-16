"""
GVIC URL Routing Tests
- 쇼핑몰 URL 감지 및 크롤러 라우팅 테스트
- 일반 URL 텍스트 추출 테스트
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "admin@gvic.com"
TEST_PASSWORD = "gvicgvic!"


class TestURLRouting:
    """URL 라우팅 테스트 - 쇼핑몰 URL vs 일반 URL"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_naver_smartstore_url_routing(self):
        """네이버 스마트스토어 URL → platform='naver', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://smartstore.naver.com/test-product/123", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        # Verify shopping URL routing
        assert data.get("input_type") == "shopping_url", f"Expected shopping_url, got {data.get('input_type')}"
        assert data.get("platform") == "naver", f"Expected naver, got {data.get('platform')}"
        assert data.get("success") == True
        assert "crawl_id" in data
        print(f"✅ Naver SmartStore URL correctly routed: platform={data.get('platform')}, input_type={data.get('input_type')}")
    
    def test_naver_brand_url_routing(self):
        """네이버 브랜드스토어 URL → platform='naver', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://brand.naver.com/test-brand/products/123", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "naver"
        print(f"✅ Naver Brand URL correctly routed: platform={data.get('platform')}")
    
    def test_naver_shopping_url_routing(self):
        """네이버 쇼핑 URL → platform='naver', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://shopping.naver.com/product/123", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "naver"
        print(f"✅ Naver Shopping URL correctly routed: platform={data.get('platform')}")
    
    def test_coupang_url_routing(self):
        """쿠팡 URL → platform='coupang', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.coupang.com/vp/products/12345", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "shopping_url", f"Expected shopping_url, got {data.get('input_type')}"
        assert data.get("platform") == "coupang", f"Expected coupang, got {data.get('platform')}"
        assert data.get("success") == True
        print(f"✅ Coupang URL correctly routed: platform={data.get('platform')}, input_type={data.get('input_type')}")
    
    def test_11st_url_routing(self):
        """11번가 URL → platform='11st', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.11st.co.kr/products/12345", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "11st"
        print(f"✅ 11st URL correctly routed: platform={data.get('platform')}")
    
    def test_gmarket_url_routing(self):
        """G마켓 URL → platform='gmarket', input_type='shopping_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.gmarket.co.kr/item/12345", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "gmarket"
        print(f"✅ Gmarket URL correctly routed: platform={data.get('platform')}")
    
    def test_generic_url_text_extraction(self):
        """일반 URL (example.com) → input_type='generic_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://example.com", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "generic_url", f"Expected generic_url, got {data.get('input_type')}"
        assert data.get("success") == True
        assert "signal_id" in data
        assert "extracted_text" in data
        assert len(data.get("extracted_text", "")) > 0
        print(f"✅ Generic URL correctly processed: input_type={data.get('input_type')}, signal_id={data.get('signal_id')}")
    
    def test_generic_url_with_path(self):
        """일반 URL with path → input_type='generic_url'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://httpbin.org/html", "purpose": "테스트"}
        )
        
        assert response.status_code == 200, f"Request failed: {response.text}"
        data = response.json()
        
        assert data.get("input_type") == "generic_url"
        assert data.get("success") == True
        print(f"✅ Generic URL with path correctly processed: input_type={data.get('input_type')}")
    
    def test_empty_url_error(self):
        """빈 URL → 400 에러"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "", "purpose": "테스트"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Empty URL correctly returns 400 error")
    
    def test_invalid_url_format_error(self):
        """잘못된 URL 형식 → 400 에러"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "not-a-valid-url", "purpose": "테스트"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✅ Invalid URL format correctly returns 400 error")
    
    def test_unauthorized_access(self):
        """인증 없이 접근 → 401 에러"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers={"Content-Type": "application/json"},
            json={"url": "https://example.com", "purpose": "테스트"}
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✅ Unauthorized access correctly returns 401 error")


class TestDetectShoppingPlatform:
    """detect_shopping_platform 함수 테스트 (간접 테스트)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_amazon_url_detection(self):
        """Amazon URL → platform='amazon'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.amazon.com/dp/B08N5WRWNW", "purpose": "테스트"}
        )
        
        assert response.status_code == 200
        data = response.json()
        # Amazon should be detected as shopping_url
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "amazon"
        print(f"✅ Amazon URL detected: platform={data.get('platform')}")
    
    def test_aliexpress_url_detection(self):
        """AliExpress URL → platform='aliexpress'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.aliexpress.com/item/12345.html", "purpose": "테스트"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "aliexpress"
        print(f"✅ AliExpress URL detected: platform={data.get('platform')}")
    
    def test_auction_url_detection(self):
        """옥션 URL → platform='auction'"""
        response = requests.post(
            f"{BASE_URL}/api/signal/ingest/url",
            headers=self.headers,
            json={"url": "https://www.auction.co.kr/item/12345", "purpose": "테스트"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("input_type") == "shopping_url"
        assert data.get("platform") == "auction"
        print(f"✅ Auction URL detected: platform={data.get('platform')}")


class TestCrawlEndpoints:
    """크롤링 관련 엔드포인트 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
        )
        assert response.status_code == 200
        self.token = response.json().get("token")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_supported_platforms(self):
        """지원 플랫폼 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/crawl/platforms",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "platforms" in data
        
        platforms = [p["id"] for p in data["platforms"]]
        assert "naver" in platforms
        assert "coupang" in platforms
        print(f"✅ Supported platforms: {platforms}")
    
    def test_create_sample_crawl_data(self):
        """테스트용 샘플 크롤링 데이터 생성"""
        response = requests.post(
            f"{BASE_URL}/api/crawl/test/sample",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "crawl_id" in data
        assert data.get("reviews_count") > 0
        print(f"✅ Sample crawl data created: crawl_id={data.get('crawl_id')}, reviews={data.get('reviews_count')}")
    
    def test_get_crawl_history(self):
        """크롤링 이력 조회"""
        response = requests.get(
            f"{BASE_URL}/api/crawl/history",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "total" in data
        print(f"✅ Crawl history retrieved: total={data.get('total')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
