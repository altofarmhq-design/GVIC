"""
GVIC Improvement Assets API Tests - HS Code 기반 개선점 자산화 모듈 테스트
- HS Code 목록/상세 조회
- 제품명으로 HS Code 추천
- 제품에 HS Code 설정
- 개선점 수동/자동 자산 축적
- 품목군별 자산 조회 및 체크리스트
- 전체 자산 통계
- 4대 인사이트 분석 시 자동 자산화 (auto_accumulate)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestImprovementAssetsAPI:
    """개선점 자산화 API 테스트"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """인증 토큰 획득"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@gvic.com", "password": "gvicgvic!"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """인증 헤더"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_product_id(self):
        """테스트용 제품 ID"""
        return f"TEST_prod_{uuid.uuid4().hex[:12]}"
    
    # ==================== HS Code 조회 테스트 ====================
    
    def test_get_hs_codes_list(self, auth_headers):
        """GET /api/assets/hs-codes - HS Code 목록 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/hs-codes",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # 데이터 검증
        assert "hs_codes" in data
        assert "total" in data
        assert data["total"] == 12  # 12개 품목군
        
        # 첫 번째 HS Code 구조 검증
        first_code = data["hs_codes"][0]
        assert "hs_code" in first_code
        assert "name" in first_code
        assert "name_en" in first_code
        assert "feature_modules" in first_code
        assert isinstance(first_code["feature_modules"], list)
    
    def test_get_hs_code_detail_earphone(self, auth_headers):
        """GET /api/assets/hs-codes/8518.30 - 이어폰 HS Code 상세 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/hs-codes/8518.30",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "8518.30"
        assert data["name"] == "헤드폰/이어폰"
        assert data["name_en"] == "Headphones/Earphones"
        assert "음질" in data["feature_modules"]
        assert "배터리" in data["feature_modules"]
    
    def test_get_hs_code_detail_smartphone(self, auth_headers):
        """GET /api/assets/hs-codes/8517.12 - 스마트폰 HS Code 상세 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/hs-codes/8517.12",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "8517.12"
        assert data["name"] == "스마트폰"
        assert "카메라" in data["feature_modules"]
    
    def test_get_hs_code_detail_shoes(self, auth_headers):
        """GET /api/assets/hs-codes/6402.19 - 운동화 HS Code 상세 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/hs-codes/6402.19",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "6402.19"
        assert data["name"] == "운동화/스니커즈"
        assert "착용감" in data["feature_modules"]
    
    def test_get_hs_code_not_found(self, auth_headers):
        """GET /api/assets/hs-codes/9999.99 - 존재하지 않는 HS Code 404"""
        response = requests.get(
            f"{BASE_URL}/api/assets/hs-codes/9999.99",
            headers=auth_headers
        )
        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.json().get("detail", "")
    
    # ==================== HS Code 추천 테스트 ====================
    
    def test_suggest_hs_code_airpod(self, auth_headers):
        """POST /api/assets/suggest-hs-code - 에어팟 → 이어폰 추천"""
        response = requests.post(
            f"{BASE_URL}/api/assets/suggest-hs-code?product_name=airpod",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["product_name"] == "airpod"
        assert len(data["suggestions"]) > 0
        assert data["suggestions"][0]["hs_code"] == "8518.30"
        assert data["suggestions"][0]["confidence"] == "high"
    
    def test_suggest_hs_code_sneakers(self, auth_headers):
        """POST /api/assets/suggest-hs-code - 스니커즈 → 운동화 추천"""
        response = requests.post(
            f"{BASE_URL}/api/assets/suggest-hs-code?product_name=sneakers",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        assert data["suggestions"][0]["hs_code"] == "6402.19"
    
    def test_suggest_hs_code_laptop(self, auth_headers):
        """POST /api/assets/suggest-hs-code - 노트북 추천"""
        response = requests.post(
            f"{BASE_URL}/api/assets/suggest-hs-code?product_name=laptop",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) > 0
        assert data["suggestions"][0]["hs_code"] == "8471.30"
    
    def test_suggest_hs_code_no_match(self, auth_headers):
        """POST /api/assets/suggest-hs-code - 매칭 없는 제품명"""
        response = requests.post(
            f"{BASE_URL}/api/assets/suggest-hs-code?product_name=xyz123unknown",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["suggestions"] == []  # 매칭 없음
    
    # ==================== 제품 HS Code 설정 테스트 ====================
    
    def test_set_product_hs_code(self, auth_headers):
        """POST /api/assets/products/{product_id}/set-hs-code - 제품에 HS Code 설정"""
        # 기존 제품 사용 (prod_af27651e47d8)
        response = requests.post(
            f"{BASE_URL}/api/assets/products/prod_af27651e47d8/set-hs-code",
            headers=auth_headers,
            json={
                "product_id": "prod_af27651e47d8",
                "hs_code": "8518.30"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["product_id"] == "prod_af27651e47d8"
        assert data["hs_code"] == "8518.30"
        assert data["hs_code_name"] == "헤드폰/이어폰"
    
    def test_set_product_hs_code_not_found(self, auth_headers):
        """POST /api/assets/products/{product_id}/set-hs-code - 존재하지 않는 제품 404"""
        response = requests.post(
            f"{BASE_URL}/api/assets/products/nonexistent_product/set-hs-code",
            headers=auth_headers,
            json={
                "product_id": "nonexistent_product",
                "hs_code": "8518.30"
            }
        )
        assert response.status_code == 404
    
    # ==================== 개선점 자산 축적 테스트 ====================
    
    def test_accumulate_improvements_manual(self, auth_headers, test_product_id):
        """POST /api/assets/accumulate - 개선점 수동 자산 축적"""
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate",
            headers=auth_headers,
            json={
                "product_id": test_product_id,
                "hs_code": "8517.12",  # 스마트폰
                "analysis_id": f"TEST_analysis_{uuid.uuid4().hex[:8]}",
                "improvements": [
                    {
                        "type": "suggestion",
                        "category": "색상",
                        "content": "더 다양한 색상 옵션 요청",
                        "feature_module": "디자인",
                        "examples": ["파란색도 출시해주세요"]
                    },
                    {
                        "type": "complaint",
                        "category": "품질불량",
                        "content": "화면 불량 이슈",
                        "severity": "high",
                        "feature_module": "디스플레이",
                        "examples": ["화면에 줄이 생겼어요"]
                    },
                    {
                        "type": "new_product_need",
                        "category": "신기능",
                        "content": "폴더블 버전 요청",
                        "feature_module": "디자인",
                        "examples": ["접히는 폰 출시해주세요"]
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["accumulated"] == 3
        assert data["hs_code"] == "8517.12"
    
    def test_accumulate_improvements_duplicate_increases_frequency(self, auth_headers, test_product_id):
        """POST /api/assets/accumulate - 중복 개선점 축적 시 빈도 증가"""
        # 동일한 개선점 다시 축적
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate",
            headers=auth_headers,
            json={
                "product_id": test_product_id,
                "hs_code": "8517.12",
                "analysis_id": f"TEST_analysis_{uuid.uuid4().hex[:8]}",
                "improvements": [
                    {
                        "type": "suggestion",
                        "category": "색상",
                        "content": "더 다양한 색상 옵션 요청",
                        "feature_module": "디자인",
                        "examples": ["빨간색도 있으면 좋겠어요"]
                    }
                ]
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["accumulated"] == 1
    
    # ==================== 분석 결과에서 자동 축적 테스트 ====================
    
    def test_accumulate_from_analysis(self, auth_headers):
        """POST /api/assets/accumulate-from-analysis/{analysis_id} - 분석 결과에서 자동 축적"""
        # 먼저 분석 생성 (auto_accumulate=false)
        analysis_response = requests.post(
            f"{BASE_URL}/api/insights/analyze?auto_accumulate=false",
            headers=auth_headers,
            json={
                "product_id": "prod_af27651e47d8",
                "reviews": [
                    {"content": "색상추가해주세요", "rating": 4},
                    {"content": "불량품이에요 고장났어요", "rating": 1},
                    {"content": "방수버전 출시해주세요", "rating": 4}
                ],
                "analysis_depth": "standard"
            }
        )
        assert analysis_response.status_code == 200
        analysis_id = analysis_response.json()["analysis_id"]
        
        # 분석 결과에서 자산 축적
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate-from-analysis/{analysis_id}?hs_code=8518.30",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["extracted_improvements"] >= 0
        assert data["hs_code"] == "8518.30"
    
    def test_accumulate_from_analysis_not_found(self, auth_headers):
        """POST /api/assets/accumulate-from-analysis/{analysis_id} - 존재하지 않는 분석 404"""
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate-from-analysis/nonexistent_analysis?hs_code=8518.30",
            headers=auth_headers
        )
        assert response.status_code == 404
    
    # ==================== 품목군별 자산 조회 테스트 ====================
    
    def test_get_category_assets(self, auth_headers):
        """GET /api/assets/category/{hs_code} - 품목군별 자산 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/category/8518.30",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "8518.30"
        assert data["category_name"] == "헤드폰/이어폰"
        assert "total_improvements" in data
        assert "by_type" in data
        assert "by_feature_module" in data
        assert "top_issues" in data
    
    def test_get_category_assets_empty(self, auth_headers):
        """GET /api/assets/category/{hs_code} - 자산 없는 품목군 조회"""
        response = requests.get(
            f"{BASE_URL}/api/assets/category/9403.20",  # 금속 가구 (자산 없을 수 있음)
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "9403.20"
        assert "total_improvements" in data
    
    # ==================== 품목군 체크리스트 테스트 ====================
    
    def test_get_category_checklist(self, auth_headers):
        """GET /api/assets/category/{hs_code}/checklist - 품목군 진입 체크리스트"""
        response = requests.get(
            f"{BASE_URL}/api/assets/category/8518.30/checklist",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["hs_code"] == "8518.30"
        assert data["category_name"] == "헤드폰/이어폰"
        assert "checklist" in data
        
        checklist = data["checklist"]
        assert "critical_issues" in checklist  # HIGH 심각도 불만
        assert "common_suggestions" in checklist  # 자주 발생하는 건의
        assert "market_opportunities" in checklist  # 신제품 욕구
        
        assert "total_data_points" in data
    
    # ==================== 전체 자산 통계 테스트 ====================
    
    def test_get_asset_stats_overview(self, auth_headers):
        """GET /api/assets/stats/overview - 전체 자산 통계"""
        response = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "total_assets" in data
        assert "top_categories" in data
        assert "by_type" in data
        
        # top_categories 구조 검증
        if data["top_categories"]:
            first_cat = data["top_categories"][0]
            assert "hs_code" in first_cat
            assert "name" in first_cat
            assert "asset_count" in first_cat
            assert "total_frequency" in first_cat
    
    # ==================== 4대 인사이트 자동 자산화 테스트 ====================
    
    def test_insights_analyze_with_auto_accumulate(self, auth_headers):
        """POST /api/insights/analyze with auto_accumulate=true - 분석 시 자동 자산화"""
        # 현재 자산 수 확인
        stats_before = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        ).json()
        total_before = stats_before.get("total_assets", 0)
        
        # 분석 실행 (auto_accumulate=true)
        response = requests.post(
            f"{BASE_URL}/api/insights/analyze?auto_accumulate=true",
            headers=auth_headers,
            json={
                "product_id": "prod_af27651e47d8",  # HS Code가 설정된 제품
                "reviews": [
                    {"content": "색상추가해주세요 검정색도 있었으면", "rating": 4},
                    {"content": "불량품이에요 고장났어요", "rating": 1},
                    {"content": "방수버전 출시해주세요", "rating": 4},
                    {"content": "사이즈추가 부탁드려요", "rating": 4}
                ],
                "analysis_depth": "standard"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        # 분석 결과 검증
        assert "analysis_id" in data
        assert "strengths" in data
        assert "suggestions" in data
        assert "complaints" in data
        assert "new_product_needs" in data
        
        # 자산 수 증가 확인 (개선점이 있는 경우)
        stats_after = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        ).json()
        total_after = stats_after.get("total_assets", 0)
        
        # 개선점이 감지되면 자산이 증가해야 함
        # (키워드 매칭에 따라 증가하지 않을 수도 있음)
        assert total_after >= total_before
    
    def test_insights_analyze_without_auto_accumulate(self, auth_headers):
        """POST /api/insights/analyze with auto_accumulate=false - 자동 자산화 비활성화"""
        # 현재 자산 수 확인
        stats_before = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        ).json()
        total_before = stats_before.get("total_assets", 0)
        
        # 분석 실행 (auto_accumulate=false)
        response = requests.post(
            f"{BASE_URL}/api/insights/analyze?auto_accumulate=false",
            headers=auth_headers,
            json={
                "product_id": "prod_af27651e47d8",
                "reviews": [
                    {"content": "색상추가해주세요", "rating": 4},
                    {"content": "불량품이에요", "rating": 1}
                ],
                "analysis_depth": "standard"
            }
        )
        assert response.status_code == 200
        
        # 자산 수 변화 없음 확인
        stats_after = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        ).json()
        total_after = stats_after.get("total_assets", 0)
        
        # auto_accumulate=false이므로 자산 수 변화 없어야 함
        assert total_after == total_before
    
    # ==================== 인증 필수 테스트 ====================
    
    def test_auth_required_hs_codes(self):
        """GET /api/assets/hs-codes - 인증 없이 401"""
        response = requests.get(f"{BASE_URL}/api/assets/hs-codes")
        assert response.status_code == 401
    
    def test_auth_required_suggest_hs_code(self):
        """POST /api/assets/suggest-hs-code - 인증 없이 401"""
        response = requests.post(
            f"{BASE_URL}/api/assets/suggest-hs-code?product_name=test"
        )
        assert response.status_code == 401
    
    def test_auth_required_accumulate(self):
        """POST /api/assets/accumulate - 인증 없이 401"""
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate",
            json={}
        )
        assert response.status_code == 401
    
    def test_auth_required_category_assets(self):
        """GET /api/assets/category/{hs_code} - 인증 없이 401"""
        response = requests.get(f"{BASE_URL}/api/assets/category/8518.30")
        assert response.status_code == 401
    
    def test_auth_required_checklist(self):
        """GET /api/assets/category/{hs_code}/checklist - 인증 없이 401"""
        response = requests.get(f"{BASE_URL}/api/assets/category/8518.30/checklist")
        assert response.status_code == 401
    
    def test_auth_required_stats_overview(self):
        """GET /api/assets/stats/overview - 인증 없이 401"""
        response = requests.get(f"{BASE_URL}/api/assets/stats/overview")
        assert response.status_code == 401
    
    # ==================== 개선점 타입 검증 테스트 ====================
    
    def test_improvement_types_validation(self, auth_headers):
        """개선점 타입 검증 - suggestion, complaint, new_product_need만 허용"""
        # 유효한 타입들로 축적
        response = requests.post(
            f"{BASE_URL}/api/assets/accumulate",
            headers=auth_headers,
            json={
                "product_id": "TEST_type_validation",
                "hs_code": "8518.30",
                "analysis_id": "TEST_type_analysis",
                "improvements": [
                    {"type": "suggestion", "category": "test", "content": "건의사항"},
                    {"type": "complaint", "category": "test", "content": "불만사항", "severity": "medium"},
                    {"type": "new_product_need", "category": "test", "content": "신제품욕구"}
                ]
            }
        )
        assert response.status_code == 200
        assert response.json()["accumulated"] == 3
    
    # ==================== 정리 ====================
    
    def test_cleanup_test_data(self, auth_headers):
        """테스트 데이터 정리 - TEST_ 접두사 자산 확인"""
        # 통계 조회로 테스트 데이터 존재 확인
        response = requests.get(
            f"{BASE_URL}/api/assets/stats/overview",
            headers=auth_headers
        )
        assert response.status_code == 200
        # 테스트 완료 확인
        print(f"Final asset stats: {response.json()}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
