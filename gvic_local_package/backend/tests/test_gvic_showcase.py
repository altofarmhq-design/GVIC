"""
GVIC Showcase Tab - AI 기반 시그널 분석 시스템 테스트
테스트 대상:
- POST /api/signal-tracer/ai-analyze: AI 분석 API
- POST /api/gvic-assets: 자산 저장 API
- GET /api/gvic-assets: 자산 목록 조회 API
- GET /api/gvic-assets/{asset_id}: 자산 상세 조회 API
- DELETE /api/gvic-assets/{asset_id}: 자산 삭제 API
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test session token (created via mongosh)
TEST_SESSION_TOKEN = "test_session_1771073519173"


class TestGVICShowcaseAIAnalyze:
    """AI 기반 시그널 분석 API 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def test_ai_analyze_product_review(self):
        """상품 후기 분석 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers=self.headers,
            json={"content": "효과가 정말 좋아요! 포장도 꼼꼼하고 배송도 빨랐어요."},
            timeout=60
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # 필수 필드 확인
        assert data.get("success") == True
        assert "input_id" in data
        assert "module_id" in data
        assert "requester_id" in data
        
        # ID 체계 확인 (INP_, MOD_, SIG_ 접두사)
        assert data["input_id"].startswith("INP_"), f"input_id should start with INP_: {data['input_id']}"
        assert data["module_id"].startswith("MOD_"), f"module_id should start with MOD_: {data['module_id']}"
        
        # 시그널 유형 감지 확인
        assert "signal_type" in data
        assert "signal_type_label" in data
        assert "signal_type_confidence" in data
        assert data["signal_type_confidence"] >= 0 and data["signal_type_confidence"] <= 1
        
        # 발견된 시그널 확인
        assert "discovered_signals" in data
        assert "signal_count" in data
        assert data["signal_count"] > 0
        
        # 각 시그널에 signal_id 확인
        for sig in data["discovered_signals"]:
            assert "signal_id" in sig
            assert sig["signal_id"].startswith("SIG_"), f"signal_id should start with SIG_: {sig['signal_id']}"
            assert "sentiment" in sig
            assert "type" in sig
            assert "intensity" in sig
        
        # 분석 결과 확인
        assert "overall_sentiment" in data
        assert "key_themes" in data
        assert "summary" in data
        
        # 3관점 분석 확인
        assert "applicable_perspectives" in data
        perspectives = data["applicable_perspectives"]
        assert "society" in perspectives
        assert "production" in perspectives
        assert "consumer" in perspectives
        
        print(f"✅ AI 분석 성공: {data['signal_type_label']} (신뢰도: {data['signal_type_confidence']*100:.0f}%)")
        print(f"   발견된 시그널: {data['signal_count']}개")
    
    def test_ai_analyze_requirement(self):
        """요구사항 분석 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers=self.headers,
            json={"content": "실제 시그널이 어떻게 gvic에서 가공되고 결과를 얻게 되는 구나를 알 수 있어야 겠지."},
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "discovered_signals" in data
        
        print(f"✅ 요구사항 분석 성공: {data['signal_type_label']}")
    
    def test_ai_analyze_mixed_sentiment(self):
        """체념적 만족 (복합 감성) 분석 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers=self.headers,
            json={"content": "두 번째 구매할 때 2kg를 주문했는데 키로 수도 맛도 믿음이 안 갔는데. 사장님께서 직접 전화 주시고 친절하게 대응하시기에 미안함도 있고. 맛은 맛있어요. 그냥 그것에 만족할게요."},
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        
        # 숨겨진 의미 추출 확인
        has_hidden_meaning = False
        for sig in data.get("discovered_signals", []):
            if sig.get("hidden_meaning"):
                has_hidden_meaning = True
                break
        
        print(f"✅ 복합 감성 분석 성공: {data['overall_sentiment']}")
        print(f"   숨겨진 의미 추출: {'있음' if has_hidden_meaning else '없음'}")
    
    def test_ai_analyze_empty_content(self):
        """빈 내용 분석 시 에러 처리 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers=self.headers,
            json={"content": ""},
            timeout=30
        )
        
        # 빈 내용은 에러 상태 코드 예상 (400, 422, 500, 520 등)
        assert response.status_code >= 400, f"Expected error status, got {response.status_code}"
        print(f"✅ 빈 내용 에러 처리 확인: {response.status_code}")
    
    def test_ai_analyze_unauthorized(self):
        """인증 없이 분석 시 에러 처리 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers={"Content-Type": "application/json"},
            json={"content": "테스트"},
            timeout=30
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print(f"✅ 인증 없이 접근 시 401 반환 확인")


class TestGVICAssets:
    """GVIC 자산 API 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        self.created_asset_ids = []
    
    def teardown_method(self, method):
        """테스트 후 생성된 자산 정리"""
        for asset_id in self.created_asset_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/gvic-assets/{asset_id}",
                    headers=self.headers,
                    timeout=10
                )
            except:
                pass
    
    def test_get_assets_list(self):
        """자산 목록 조회 테스트"""
        response = requests.get(
            f"{BASE_URL}/api/gvic-assets",
            headers=self.headers,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "assets" in data
        assert "stats" in data
        
        stats = data["stats"]
        assert "total" in stats
        assert "positive" in stats
        assert "neutral" in stats
        assert "negative" in stats
        
        print(f"✅ 자산 목록 조회 성공: 총 {stats['total']}개")
        print(f"   긍정: {stats['positive']}, 중립: {stats['neutral']}, 부정: {stats['negative']}")
    
    def test_create_asset(self):
        """자산 생성 테스트"""
        response = requests.post(
            f"{BASE_URL}/api/gvic-assets",
            headers=self.headers,
            json={
                "content": "TEST_테스트 자산 내용입니다.",
                "rating": 4,
                "analysis_result": {
                    "signal_type": "product_review",
                    "overall_sentiment": "positive",
                    "steps": {
                        "step5_output": {
                            "final_score": {"value": 75, "classification": "긍정"}
                        },
                        "step4_convergence": {
                            "distribution": {
                                "after_adjustment": {"V_pub": 30, "V_pro": 35, "V_ind": 35}
                            }
                        }
                    }
                }
            },
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data.get("success") == True
        assert "asset_id" in data
        assert data["asset_id"].startswith("AST_")
        
        self.created_asset_ids.append(data["asset_id"])
        
        print(f"✅ 자산 생성 성공: {data['asset_id']}")
        
        # 생성된 자산 조회 확인
        get_response = requests.get(
            f"{BASE_URL}/api/gvic-assets/{data['asset_id']}",
            headers=self.headers,
            timeout=30
        )
        
        assert get_response.status_code == 200
        asset = get_response.json()
        assert asset["content"] == "TEST_테스트 자산 내용입니다."
        
        print(f"✅ 생성된 자산 조회 확인 완료")
    
    def test_get_asset_not_found(self):
        """존재하지 않는 자산 조회 테스트"""
        response = requests.get(
            f"{BASE_URL}/api/gvic-assets/AST_NOTEXIST",
            headers=self.headers,
            timeout=30
        )
        
        assert response.status_code == 404
        print(f"✅ 존재하지 않는 자산 조회 시 404 반환 확인")
    
    def test_delete_asset(self):
        """자산 삭제 테스트"""
        # 먼저 자산 생성
        create_response = requests.post(
            f"{BASE_URL}/api/gvic-assets",
            headers=self.headers,
            json={
                "content": "TEST_삭제 테스트용 자산",
                "rating": 3,
                "analysis_result": {}
            },
            timeout=30
        )
        
        assert create_response.status_code == 200
        asset_id = create_response.json()["asset_id"]
        
        # 삭제
        delete_response = requests.delete(
            f"{BASE_URL}/api/gvic-assets/{asset_id}",
            headers=self.headers,
            timeout=30
        )
        
        assert delete_response.status_code == 200
        
        # 삭제 확인
        get_response = requests.get(
            f"{BASE_URL}/api/gvic-assets/{asset_id}",
            headers=self.headers,
            timeout=30
        )
        
        assert get_response.status_code == 404
        print(f"✅ 자산 삭제 및 확인 완료")


class TestGVICShowcaseIntegration:
    """GVIC Showcase 통합 테스트 - 분석 후 자산 저장 플로우"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """테스트 설정"""
        self.headers = {
            "Authorization": f"Bearer {TEST_SESSION_TOKEN}",
            "Content-Type": "application/json"
        }
        self.created_asset_ids = []
    
    def teardown_method(self, method):
        """테스트 후 생성된 자산 정리"""
        for asset_id in self.created_asset_ids:
            try:
                requests.delete(
                    f"{BASE_URL}/api/gvic-assets/{asset_id}",
                    headers=self.headers,
                    timeout=10
                )
            except:
                pass
    
    def test_full_flow_analyze_and_save(self):
        """전체 플로우 테스트: AI 분석 → 자산 저장 → 조회"""
        # 1. AI 분석
        analyze_response = requests.post(
            f"{BASE_URL}/api/signal-tracer/ai-analyze",
            headers=self.headers,
            json={"content": "TEST_통합 테스트용 텍스트입니다. 품질이 좋고 배송도 빨랐어요."},
            timeout=60
        )
        
        assert analyze_response.status_code == 200
        analysis_result = analyze_response.json()
        assert analysis_result.get("success") == True
        
        print(f"✅ 1단계: AI 분석 완료")
        print(f"   시그널 유형: {analysis_result['signal_type_label']}")
        print(f"   발견된 시그널: {analysis_result['signal_count']}개")
        
        # 2. 자산 저장
        save_response = requests.post(
            f"{BASE_URL}/api/gvic-assets",
            headers=self.headers,
            json={
                "content": "TEST_통합 테스트용 텍스트입니다. 품질이 좋고 배송도 빨랐어요.",
                "rating": 5,
                "analysis_result": analysis_result
            },
            timeout=30
        )
        
        assert save_response.status_code == 200
        save_data = save_response.json()
        assert save_data.get("success") == True
        
        asset_id = save_data["asset_id"]
        self.created_asset_ids.append(asset_id)
        
        print(f"✅ 2단계: 자산 저장 완료 ({asset_id})")
        
        # 3. 자산 목록에서 확인
        list_response = requests.get(
            f"{BASE_URL}/api/gvic-assets",
            headers=self.headers,
            timeout=30
        )
        
        assert list_response.status_code == 200
        assets = list_response.json()["assets"]
        
        found = False
        for asset in assets:
            if asset["asset_id"] == asset_id:
                found = True
                assert "TEST_통합 테스트용" in asset["content"]
                break
        
        assert found, f"저장된 자산 {asset_id}를 목록에서 찾을 수 없음"
        
        print(f"✅ 3단계: 자산 목록에서 확인 완료")
        print(f"✅ 전체 플로우 테스트 성공!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
