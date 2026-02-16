"""
SaaS Module API Tests - Seller Intelligence Hub
Tests for:
- Review Analyzer (POST /api/saas/reviews/analyze, analyze-single, dashboard/summary)
- QA Manager (POST /api/saas/qa/items, GET items, stats, generate-faq)
- Dashboard Service (GET overview, insights-532, action-items, full)
- Crawl Integration (POST crawl-and-analyze, analyze-existing)
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


class TestReviewAnalyzer(TestAuthSetup):
    """Review Analyzer API Tests - /api/saas/reviews/*"""
    
    def test_analyze_batch_reviews(self, auth_headers):
        """POST /api/saas/reviews/analyze - 리뷰 배치 분석"""
        payload = {
            "reviews": [
                {
                    "content": "정말 좋은 제품이에요! 배송도 빠르고 품질도 최고입니다. 다음에도 재구매할 예정이에요.",
                    "rating": 5,
                    "platform": "naver",
                    "product_name": "테스트 상품",
                    "author": "테스트유저1"
                },
                {
                    "content": "가격 대비 괜찮은 품질입니다. 다만 포장이 조금 아쉬웠어요.",
                    "rating": 4,
                    "platform": "naver",
                    "product_name": "테스트 상품",
                    "author": "테스트유저2"
                },
                {
                    "content": "배송이 너무 늦었어요. 품질도 기대 이하입니다. 실망했습니다.",
                    "rating": 2,
                    "platform": "coupang",
                    "product_name": "테스트 상품",
                    "author": "테스트유저3"
                },
                {
                    "content": "가성비 최고! 이 가격에 이 품질은 정말 대박이에요. 강추합니다!",
                    "rating": 5,
                    "platform": "naver",
                    "product_name": "테스트 상품",
                    "author": "테스트유저4"
                },
                {
                    "content": "사이즈가 생각보다 작아요. 교환 요청했습니다.",
                    "rating": 3,
                    "platform": "11st",
                    "product_name": "테스트 상품",
                    "author": "테스트유저5"
                }
            ],
            "product_id": f"TEST_PROD_{uuid.uuid4().hex[:8]}",
            "analysis_depth": "standard"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/saas/reviews/analyze",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Batch analyze failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "analysis_id" in data, "Missing analysis_id"
        assert "total_reviews" in data, "Missing total_reviews"
        assert data["total_reviews"] == 5, f"Expected 5 reviews, got {data['total_reviews']}"
        
        # Validate sentiment analysis
        assert "sentiment" in data, "Missing sentiment"
        sentiment = data["sentiment"]
        assert "positive_ratio" in sentiment, "Missing positive_ratio"
        assert "negative_ratio" in sentiment, "Missing negative_ratio"
        assert "label" in sentiment, "Missing sentiment label"
        
        # Validate keywords
        assert "keywords" in data, "Missing keywords"
        assert isinstance(data["keywords"], list), "Keywords should be a list"
        
        # Validate 5:3:2 insights
        assert "insights_532" in data, "Missing insights_532"
        insights = data["insights_532"]
        assert "customer_insights" in insights, "Missing customer_insights"
        assert "operation_insights" in insights, "Missing operation_insights"
        assert "strategy_insights" in insights, "Missing strategy_insights"
        
        # Validate issues and strengths
        assert "issues" in data, "Missing issues"
        assert "strengths" in data, "Missing strengths"
        
        # Validate summary and recommendations
        assert "summary" in data, "Missing summary"
        assert "recommendations" in data, "Missing recommendations"
        
        print(f"✓ Batch analysis completed: {data['analysis_id']}")
        print(f"  - Sentiment: {sentiment['label']} (score: {sentiment.get('average_score', 'N/A')})")
        print(f"  - Keywords: {len(data['keywords'])} extracted")
        print(f"  - Issues: {len(data['issues'])} identified")
        print(f"  - Strengths: {len(data['strengths'])} identified")
        
        return data["analysis_id"]
    
    def test_analyze_single_review(self, auth_headers):
        """POST /api/saas/reviews/analyze-single - 단일 리뷰 분석"""
        payload = {
            "content": "품질이 정말 좋아요! 배송도 빠르고 포장도 꼼꼼했습니다. 가성비 최고!",
            "rating": 5,
            "platform": "naver",
            "product_name": "테스트 상품"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/saas/reviews/analyze-single",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Single analyze failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "sentiment" in data, "Missing sentiment"
        assert "keywords" in data, "Missing keywords"
        assert "features" in data, "Missing features"
        assert "issues" in data, "Missing issues"
        assert "strengths" in data, "Missing strengths"
        
        # Validate sentiment
        sentiment = data["sentiment"]
        assert sentiment["label"] == "positive", f"Expected positive sentiment, got {sentiment['label']}"
        
        print(f"✓ Single review analysis completed")
        print(f"  - Sentiment: {sentiment['label']} (score: {sentiment['score']})")
        print(f"  - Keywords: {len(data['keywords'])} extracted")
        print(f"  - Features: {len(data['features'])} identified")
    
    def test_review_dashboard_summary(self, auth_headers):
        """GET /api/saas/reviews/dashboard/summary - 리뷰 대시보드 요약"""
        response = requests.get(
            f"{BASE_URL}/api/saas/reviews/dashboard/summary",
            params={"days": 30},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Dashboard summary failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "total_analyses" in data, "Missing total_analyses"
        assert "total_reviews" in data, "Missing total_reviews"
        assert "avg_sentiment_score" in data, "Missing avg_sentiment_score"
        assert "top_issues" in data, "Missing top_issues"
        assert "top_strengths" in data, "Missing top_strengths"
        assert "trend" in data, "Missing trend"
        
        print(f"✓ Dashboard summary retrieved")
        print(f"  - Total analyses: {data['total_analyses']}")
        print(f"  - Total reviews: {data['total_reviews']}")
        print(f"  - Avg sentiment: {data['avg_sentiment_score']}")
        print(f"  - Trend: {data['trend']}")


class TestQAManager(TestAuthSetup):
    """QA Manager API Tests - /api/saas/qa/*"""
    
    def test_create_qa_items_batch(self, auth_headers):
        """POST /api/saas/qa/items - Q&A 배치 등록 (자동 카테고리 분류)"""
        payload = {
            "items": [
                {
                    "question": "배송은 언제 되나요?",
                    "answer": None,
                    "category": "general",
                    "platform": "naver"
                },
                {
                    "question": "교환/반품은 어떻게 하나요?",
                    "answer": "수령 후 7일 이내 신청 가능합니다.",
                    "category": "general",
                    "platform": "coupang"
                },
                {
                    "question": "사이즈 추천 부탁드려요. 키 170, 몸무게 65입니다.",
                    "answer": None,
                    "category": "general",
                    "platform": "naver"
                },
                {
                    "question": "재입고 언제 되나요?",
                    "answer": None,
                    "category": "general",
                    "platform": "11st"
                },
                {
                    "question": "쿠폰 적용이 안되는데 어떻게 해야 하나요?",
                    "answer": None,
                    "category": "general",
                    "platform": "coupang"
                }
            ],
            "product_id": f"TEST_PROD_{uuid.uuid4().hex[:8]}"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/saas/qa/items",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create QA items failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data["success"] == True, "Expected success=True"
        assert data["created_count"] == 5, f"Expected 5 items, got {data['created_count']}"
        assert "items" in data, "Missing items"
        
        # Check auto-categorization
        items = data["items"]
        categories = [item["category"] for item in items]
        
        # Verify categories were auto-assigned
        assert "delivery" in categories, "Expected 'delivery' category for shipping question"
        assert "exchange" in categories, "Expected 'exchange' category for return question"
        assert "size" in categories, "Expected 'size' category for size question"
        
        print(f"✓ QA items created: {data['created_count']}")
        print(f"  - Categories assigned: {set(categories)}")
        
        # Check suggested answers
        suggested_count = sum(1 for item in items if item.get("has_suggested_answer"))
        print(f"  - Items with suggested answers: {suggested_count}")
    
    def test_get_qa_items(self, auth_headers):
        """GET /api/saas/qa/items - Q&A 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/saas/qa/items",
            params={"limit": 50},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get QA items failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "items" in data, "Missing items"
        assert "total" in data, "Missing total"
        assert isinstance(data["items"], list), "Items should be a list"
        
        print(f"✓ QA items retrieved: {data['total']} items")
        
        if data["items"]:
            # Check item structure
            item = data["items"][0]
            assert "qa_id" in item, "Missing qa_id"
            assert "question" in item, "Missing question"
            assert "category" in item, "Missing category"
    
    def test_get_qa_items_filtered(self, auth_headers):
        """GET /api/saas/qa/items - Q&A 목록 필터 조회"""
        # Filter by status
        response = requests.get(
            f"{BASE_URL}/api/saas/qa/items",
            params={"status": "pending", "limit": 20},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get filtered QA items failed: {response.text}"
        data = response.json()
        
        # All items should have pending status
        for item in data["items"]:
            assert item.get("status") == "pending", f"Expected pending status, got {item.get('status')}"
        
        print(f"✓ Filtered QA items (pending): {data['total']} items")
    
    def test_get_qa_stats(self, auth_headers):
        """GET /api/saas/qa/stats - Q&A 통계"""
        response = requests.get(
            f"{BASE_URL}/api/saas/qa/stats",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get QA stats failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "total" in data, "Missing total"
        assert "pending" in data, "Missing pending"
        assert "answered" in data, "Missing answered"
        assert "answer_rate" in data, "Missing answer_rate"
        assert "by_category" in data, "Missing by_category"
        
        print(f"✓ QA stats retrieved")
        print(f"  - Total: {data['total']}")
        print(f"  - Pending: {data['pending']}")
        print(f"  - Answered: {data['answered']}")
        print(f"  - Answer rate: {data['answer_rate']}%")
        print(f"  - Categories: {list(data['by_category'].keys())}")
    
    def test_generate_faq(self, auth_headers):
        """POST /api/saas/qa/generate-faq - FAQ 자동 생성"""
        response = requests.post(
            f"{BASE_URL}/api/saas/qa/generate-faq",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Generate FAQ failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "success" in data, "Missing success"
        assert "total_questions" in data, "Missing total_questions"
        assert "faqs_generated" in data, "Missing faqs_generated"
        assert "faqs" in data, "Missing faqs"
        
        print(f"✓ FAQ generation completed")
        print(f"  - Total questions analyzed: {data['total_questions']}")
        print(f"  - FAQs generated: {data['faqs_generated']}")
        
        if data["faqs"]:
            for faq in data["faqs"][:3]:
                print(f"  - FAQ: {faq.get('question', 'N/A')[:50]}...")


class TestDashboardService(TestAuthSetup):
    """Dashboard Service API Tests - /api/saas/dashboard/*"""
    
    def test_dashboard_overview(self, auth_headers):
        """GET /api/saas/dashboard/overview - 대시보드 개요"""
        response = requests.get(
            f"{BASE_URL}/api/saas/dashboard/overview",
            params={"days": 30},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Dashboard overview failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "review_stats" in data, "Missing review_stats"
        assert "qa_stats" in data, "Missing qa_stats"
        assert "crawl_stats" in data, "Missing crawl_stats"
        assert "period_days" in data, "Missing period_days"
        
        print(f"✓ Dashboard overview retrieved")
        print(f"  - Review stats: {data['review_stats']}")
        print(f"  - QA stats: {data['qa_stats']}")
        print(f"  - Crawl stats: {data['crawl_stats']}")
    
    def test_insights_532(self, auth_headers):
        """GET /api/saas/dashboard/insights-532 - 5:3:2 인사이트"""
        response = requests.get(
            f"{BASE_URL}/api/saas/dashboard/insights-532",
            params={"days": 30},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Insights 532 failed: {response.text}"
        data = response.json()
        
        # Validate 5:3:2 structure
        assert "customer_insights" in data, "Missing customer_insights (50%)"
        assert "operation_insights" in data, "Missing operation_insights (30%)"
        assert "strategy_insights" in data, "Missing strategy_insights (20%)"
        
        # Validate ratios
        assert data["customer_insights"]["ratio"] == "50%", "Customer insights should be 50%"
        assert data["operation_insights"]["ratio"] == "30%", "Operation insights should be 30%"
        assert data["strategy_insights"]["ratio"] == "20%", "Strategy insights should be 20%"
        
        print(f"✓ 5:3:2 Insights retrieved")
        print(f"  - Customer insights (50%): {data['customer_insights']['count']} items")
        print(f"  - Operation insights (30%): {data['operation_insights']['count']} items")
        print(f"  - Strategy insights (20%): {data['strategy_insights']['count']} items")
    
    def test_action_items(self, auth_headers):
        """GET /api/saas/dashboard/action-items - 액션 아이템"""
        response = requests.get(
            f"{BASE_URL}/api/saas/dashboard/action-items",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Action items failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "action_items" in data, "Missing action_items"
        assert "total" in data, "Missing total"
        assert "high_priority" in data, "Missing high_priority"
        
        print(f"✓ Action items retrieved")
        print(f"  - Total: {data['total']}")
        print(f"  - High priority: {data['high_priority']}")
        
        if data["action_items"]:
            for item in data["action_items"][:3]:
                print(f"  - [{item.get('priority', 'N/A')}] {item.get('title', 'N/A')}")
    
    def test_full_dashboard(self, auth_headers):
        """GET /api/saas/dashboard/full - 전체 대시보드"""
        response = requests.get(
            f"{BASE_URL}/api/saas/dashboard/full",
            params={"days": 30},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Full dashboard failed: {response.text}"
        data = response.json()
        
        # Validate all sections present
        assert "overview" in data, "Missing overview"
        assert "insights_532" in data, "Missing insights_532"
        assert "action_items" in data, "Missing action_items"
        assert "trends" in data, "Missing trends"
        assert "generated_at" in data, "Missing generated_at"
        
        print(f"✓ Full dashboard retrieved")
        print(f"  - Generated at: {data['generated_at']}")
        print(f"  - Overview: {list(data['overview'].keys())}")
        print(f"  - Insights 532: {list(data['insights_532'].keys())}")
        print(f"  - Action items: {data['action_items']['total']} items")
        print(f"  - Trends: {data['trends'].get('trend_direction', 'N/A')}")


class TestCrawlIntegration(TestAuthSetup):
    """Crawl Integration API Tests - /api/crawl/*"""
    
    def test_crawl_and_analyze(self, auth_headers):
        """POST /api/crawl/crawl-and-analyze - 크롤링 + 분석 통합"""
        # Note: This test uses a sample URL that may not return real data
        # In production, use actual e-commerce URLs
        payload = {
            "url": "https://smartstore.naver.com/example/products/12345",
            "crawl_type": "reviews",
            "max_reviews": 10,
            "convert_to_signals": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/crawl/crawl-and-analyze",
            params={"analysis_depth": "standard"},
            json=payload,
            headers=auth_headers
        )
        
        # May return 400 if no reviews found (expected for fake URL)
        if response.status_code == 400:
            data = response.json()
            assert "리뷰를 찾을 수 없습니다" in data.get("detail", ""), "Unexpected error message"
            print(f"✓ Crawl-and-analyze handled empty result correctly")
            return None
        
        assert response.status_code == 200, f"Crawl-and-analyze failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "success" in data, "Missing success"
        assert "crawl_id" in data, "Missing crawl_id"
        assert "analysis_id" in data, "Missing analysis_id"
        assert "platform" in data, "Missing platform"
        assert "analysis" in data, "Missing analysis"
        
        print(f"✓ Crawl-and-analyze completed")
        print(f"  - Crawl ID: {data['crawl_id']}")
        print(f"  - Analysis ID: {data['analysis_id']}")
        print(f"  - Platform: {data['platform']}")
        print(f"  - Reviews crawled: {data.get('reviews_crawled', 0)}")
        
        return data.get("crawl_id")
    
    def test_create_sample_crawl_data(self, auth_headers):
        """POST /api/crawl/test/sample - 테스트용 샘플 데이터 생성"""
        response = requests.post(
            f"{BASE_URL}/api/crawl/test/sample",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Create sample data failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data["success"] == True, "Expected success=True"
        assert "crawl_id" in data, "Missing crawl_id"
        assert "reviews_count" in data, "Missing reviews_count"
        
        print(f"✓ Sample crawl data created")
        print(f"  - Crawl ID: {data['crawl_id']}")
        print(f"  - Product: {data.get('product', 'N/A')}")
        print(f"  - Reviews: {data['reviews_count']}")
        print(f"  - Signals created: {data.get('signals_created', 0)}")
        
        return data["crawl_id"]
    
    def test_analyze_existing_crawl(self, auth_headers):
        """POST /api/crawl/analyze-existing/{crawl_id} - 기존 크롤링 결과 재분석"""
        # First create sample data
        sample_response = requests.post(
            f"{BASE_URL}/api/crawl/test/sample",
            headers=auth_headers
        )
        
        assert sample_response.status_code == 200, f"Create sample failed: {sample_response.text}"
        crawl_id = sample_response.json()["crawl_id"]
        
        # Now analyze existing crawl
        response = requests.post(
            f"{BASE_URL}/api/crawl/analyze-existing/{crawl_id}",
            params={"analysis_depth": "standard"},
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Analyze existing failed: {response.text}"
        data = response.json()
        
        # Validate response
        assert data["success"] == True, "Expected success=True"
        assert data["crawl_id"] == crawl_id, "Crawl ID mismatch"
        assert "analysis_id" in data, "Missing analysis_id"
        assert "analysis" in data, "Missing analysis"
        
        # Validate analysis content
        analysis = data["analysis"]
        assert "sentiment" in analysis, "Missing sentiment in analysis"
        assert "keywords" in analysis, "Missing keywords in analysis"
        assert "insights_532" in analysis, "Missing insights_532 in analysis"
        
        print(f"✓ Existing crawl re-analyzed")
        print(f"  - Crawl ID: {data['crawl_id']}")
        print(f"  - Analysis ID: {data['analysis_id']}")
        print(f"  - Reviews analyzed: {data['reviews_analyzed']}")
        print(f"  - Sentiment: {analysis['sentiment'].get('label', 'N/A')}")
    
    def test_analyze_nonexistent_crawl(self, auth_headers):
        """POST /api/crawl/analyze-existing/{crawl_id} - 존재하지 않는 크롤링 404"""
        fake_crawl_id = f"CRL_nonexistent_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/crawl/analyze-existing/{fake_crawl_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Non-existent crawl returns 404 correctly")


class TestAuthRequired(TestAuthSetup):
    """Test that all endpoints require authentication"""
    
    def test_review_analyze_requires_auth(self):
        """POST /api/saas/reviews/analyze - requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/saas/reviews/analyze",
            json={"reviews": []}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Review analyze requires auth")
    
    def test_qa_items_requires_auth(self):
        """GET /api/saas/qa/items - requires auth"""
        response = requests.get(f"{BASE_URL}/api/saas/qa/items")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ QA items requires auth")
    
    def test_dashboard_requires_auth(self):
        """GET /api/saas/dashboard/overview - requires auth"""
        response = requests.get(f"{BASE_URL}/api/saas/dashboard/overview")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Dashboard requires auth")
    
    def test_crawl_requires_auth(self):
        """POST /api/crawl/crawl-and-analyze - requires auth"""
        response = requests.post(
            f"{BASE_URL}/api/crawl/crawl-and-analyze",
            json={"url": "https://example.com"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Crawl requires auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
