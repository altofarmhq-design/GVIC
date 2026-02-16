"""
Patent Module API Tests - 11개 특허 모듈 API 테스트
J:Platform, LL:Intelligence, H:Core, A:Gate, E:Shield, G:Refine, B:Calc, C:Exec, F:Field, D:Ledger, I:Integrity
"""
import pytest
import requests
import os
import json
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAuth:
    """Authentication for patent module tests"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@gvic.com", "password": "gvicgvic!"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        return data.get("token")
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }


class TestJPlatform(TestAuth):
    """J:PLATFORM - 입력 채널 관리 테스트"""
    
    def test_get_input_channels(self, auth_headers):
        """입력 채널 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/j/channels", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "channels" in data
        assert len(data["channels"]) > 0
        # 채널 유형 확인
        channel_types = [c["channel_type"] for c in data["channels"]]
        assert "text" in channel_types
        assert "file" in channel_types
        print(f"✓ J:Platform - 입력 채널 {len(data['channels'])}개 조회 성공")
    
    def test_get_input_stats(self, auth_headers):
        """입력 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/j/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ J:Platform - 입력 통계 조회 성공")
    
    def test_validate_input(self, auth_headers):
        """입력 데이터 유효성 검증"""
        response = requests.post(
            f"{BASE_URL}/api/patent/j/validate",
            headers=auth_headers,
            json={"content": "테스트 시그널 입력 데이터입니다.", "channel": "text"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == True
        assert "content_length" in data
        print(f"✓ J:Platform - 입력 유효성 검증 성공")
    
    def test_validate_input_empty(self, auth_headers):
        """빈 입력 데이터 검증"""
        response = requests.post(
            f"{BASE_URL}/api/patent/j/validate",
            headers=auth_headers,
            json={"content": "", "channel": "text"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("valid") == False
        assert len(data.get("errors", [])) > 0
        print(f"✓ J:Platform - 빈 입력 검증 실패 처리 성공")


class TestLLIntelligence(TestAuth):
    """LL:INTELLIGENCE - 의도 분석 테스트"""
    
    def test_get_intent_types(self, auth_headers):
        """의도 유형 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/ll/intent-types", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "types" in data
        assert len(data["types"]) > 0
        # 기본 의도 유형 확인
        type_names = [t["type"] for t in data["types"]]
        assert "wanted" in type_names
        assert "unwanted" in type_names
        print(f"✓ LL:Intelligence - 의도 유형 {len(data['types'])}개 조회 성공")
    
    def test_get_intelligence_stats(self, auth_headers):
        """의도 분석 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/ll/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "category_distribution" in data
        print(f"✓ LL:Intelligence - 의도 분석 통계 조회 성공")
    
    def test_analyze_intent(self, auth_headers):
        """의도 분석 수행"""
        response = requests.post(
            f"{BASE_URL}/api/patent/ll/analyze",
            headers=auth_headers,
            json={"content": "이 제품의 가격이 너무 비싸서 구매하기 어렵습니다.", "context": "고객 피드백"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "intent" in data
        print(f"✓ LL:Intelligence - 의도 분석 수행 성공")
    
    def test_classify_signal(self, auth_headers):
        """시그널 분류"""
        response = requests.post(
            f"{BASE_URL}/api/patent/ll/classify",
            headers=auth_headers,
            json={"content": "새로운 기능 추가 요청입니다.", "context": "기능 요청"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "classification" in data
        print(f"✓ LL:Intelligence - 시그널 분류 성공: {data.get('classification')}")


class TestHCore(TestAuth):
    """H:CORE - 5:3:2 결이론 및 시그마 설정 테스트"""
    
    def test_get_532_theory(self, auth_headers):
        """5:3:2 결이론 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/h/532-theory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "theory" in data
        theory = data["theory"]
        assert theory["name"] == "5:3:2 결이론"
        assert len(theory["components"]) == 3
        # 비율 합계 확인
        total_ratio = sum(c["ratio"] for c in theory["components"])
        assert abs(total_ratio - 1.0) < 0.01
        print(f"✓ H:Core - 5:3:2 결이론 조회 성공")
    
    def test_calculate_532_distribution(self, auth_headers):
        """5:3:2 가치 분배 계산"""
        response = requests.post(
            f"{BASE_URL}/api/patent/h/calculate-532?total_value=10000",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "distribution" in data
        dist = data["distribution"]
        assert dist["public"]["amount"] == 5000  # 50%
        assert dist["operation"]["amount"] == 3000  # 30%
        assert dist["management"]["amount"] == 2000  # 20%
        print(f"✓ H:Core - 5:3:2 분배 계산 성공: 공공={dist['public']['amount']}, 운영={dist['operation']['amount']}, 관리={dist['management']['amount']}")
    
    def test_get_sigma_config(self, auth_headers):
        """시그마 설정 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/h/sigma", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "sigma" in data
        print(f"✓ H:Core - 시그마 설정 조회 성공")
    
    def test_get_omega_config(self, auth_headers):
        """오메가 경계 조건 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/h/omega", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "omega" in data
        print(f"✓ H:Core - 오메가 경계 조건 조회 성공")
    
    def test_get_core_stats(self, auth_headers):
        """코어 시스템 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/h/core-stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ H:Core - 코어 통계 조회 성공")


class TestAGate(TestAuth):
    """A:GATE - 시그널 평가 및 필터링 테스트"""
    
    def test_get_gate_rules(self, auth_headers):
        """게이트 규칙 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/a/rules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "rules" in data
        assert len(data["rules"]) > 0
        print(f"✓ A:Gate - 게이트 규칙 {len(data['rules'])}개 조회 성공")
    
    def test_get_gate_stats(self, auth_headers):
        """게이트 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/a/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ A:Gate - 게이트 통계 조회 성공")
    
    def test_evaluate_signal(self, auth_headers):
        """시그널 게이트 평가"""
        response = requests.post(
            f"{BASE_URL}/api/patent/a/evaluate",
            headers=auth_headers,
            json={
                "signal_id": f"TEST_SIG_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "content": "이것은 테스트 시그널 콘텐츠입니다. 충분한 길이의 텍스트를 포함합니다.",
                "metadata": {}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "passed" in data
        assert "evaluations" in data
        print(f"✓ A:Gate - 시그널 평가 성공: passed={data.get('passed')}")


class TestEShield(TestAuth):
    """E:SHIELD - 보안 검사 테스트"""
    
    def test_security_scan(self, auth_headers):
        """콘텐츠 보안 스캔"""
        response = requests.post(
            f"{BASE_URL}/api/patent/e/scan",
            headers=auth_headers,
            json={"content": "안전한 텍스트 콘텐츠입니다.", "source": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "risk_level" in data
        assert data["risk_level"] == "low"
        print(f"✓ E:Shield - 보안 스캔 성공: risk_level={data.get('risk_level')}")
    
    def test_security_scan_threat(self, auth_headers):
        """위협 콘텐츠 보안 스캔"""
        response = requests.post(
            f"{BASE_URL}/api/patent/e/scan",
            headers=auth_headers,
            json={"content": "<script>alert('xss')</script>", "source": "test"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data["risk_level"] == "high"
        assert len(data.get("threats", [])) > 0
        print(f"✓ E:Shield - 위협 감지 성공: threats={len(data.get('threats', []))}개")
    
    def test_generate_hash(self, auth_headers):
        """콘텐츠 해시 생성"""
        response = requests.post(
            f"{BASE_URL}/api/patent/e/hash?content=테스트 콘텐츠",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "hashes" in data
        assert "sha256" in data["hashes"]
        print(f"✓ E:Shield - 해시 생성 성공")
    
    def test_get_shield_status(self, auth_headers):
        """방어막 상태 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/e/shield-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert data.get("status") == "active"
        print(f"✓ E:Shield - 방어막 상태 조회 성공")
    
    def test_get_threat_report(self, auth_headers):
        """위협 리포트 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/e/threat-report", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "threats" in data
        print(f"✓ E:Shield - 위협 리포트 조회 성공")


class TestGRefine(TestAuth):
    """G:REFINE - 데이터 정제 테스트"""
    
    def test_clean_content(self, auth_headers):
        """콘텐츠 정제"""
        response = requests.post(
            f"{BASE_URL}/api/patent/g/clean",
            headers=auth_headers,
            json={
                "content": "  테스트   콘텐츠   입니다.  <b>HTML</b> 태그 포함.  ",
                "options": {"normalize_whitespace": True, "remove_html": True}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "cleaned_content" in data
        assert "<b>" not in data["cleaned_content"]
        print(f"✓ G:Refine - 콘텐츠 정제 성공")
    
    def test_normalize_content(self, auth_headers):
        """콘텐츠 정규화"""
        response = requests.post(
            f"{BASE_URL}/api/patent/g/normalize?content=테스트\r\n콘텐츠\r\n입니다",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "normalized_content" in data
        print(f"✓ G:Refine - 콘텐츠 정규화 성공")
    
    def test_extract_keywords(self, auth_headers):
        """키워드 추출"""
        response = requests.post(
            f"{BASE_URL}/api/patent/g/extract-keywords?content=인공지능 기술이 발전하면서 머신러닝과 딥러닝이 주목받고 있습니다. 인공지능은 다양한 분야에서 활용됩니다.&max_keywords=5",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "keywords" in data
        print(f"✓ G:Refine - 키워드 추출 성공: {len(data.get('keywords', []))}개")
    
    def test_summarize_content(self, auth_headers):
        """콘텐츠 요약"""
        response = requests.post(
            f"{BASE_URL}/api/patent/g/summarize?content=인공지능 기술이 발전하면서 다양한 산업에서 혁신이 일어나고 있습니다. 특히 의료, 금융, 제조업 분야에서 AI 활용이 증가하고 있습니다. 이러한 변화는 앞으로도 계속될 것으로 예상됩니다.&max_length=100",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "summary" in data
        print(f"✓ G:Refine - 콘텐츠 요약 성공")
    
    def test_get_refine_options(self, auth_headers):
        """정제 옵션 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/g/refine-options", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "options" in data
        print(f"✓ G:Refine - 정제 옵션 {len(data.get('options', []))}개 조회 성공")


class TestBCalc(TestAuth):
    """B:CALC - 가치 계산 테스트"""
    
    def test_calculate_asset_value(self, auth_headers):
        """자산 가치 계산"""
        response = requests.post(
            f"{BASE_URL}/api/patent/b/calculate-value?content=고품질 데이터 분석 결과입니다. 시장 트렌드와 소비자 행동 패턴을 분석했습니다.&category=analysis",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_score" in data or "value" in data or "success" in data
        print(f"✓ B:Calc - 자산 가치 계산 성공")
    
    def test_calculate_reward_distribution(self, auth_headers):
        """보상 분배 계산 (5:3:2 결이론)"""
        response = requests.post(
            f"{BASE_URL}/api/patent/b/calculate-reward?total_amount=10000",
            headers=auth_headers,
            json=["user1", "user2", "user3"]
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "distribution_532" in data
        dist = data["distribution_532"]
        assert dist["public"]["amount"] == 5000  # 50%
        assert dist["operation"]["amount"] == 3000  # 30%
        assert dist["management"]["amount"] == 2000  # 20%
        print(f"✓ B:Calc - 보상 분배 계산 성공")
    
    def test_get_pricing_strategies(self, auth_headers):
        """가격 책정 전략 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/b/pricing-strategies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "strategies" in data
        print(f"✓ B:Calc - 가격 전략 {len(data.get('strategies', []))}개 조회 성공")
    
    def test_get_calc_stats(self, auth_headers):
        """계산 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/b/calc-stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ B:Calc - 계산 통계 조회 성공")


class TestCExec(TestAuth):
    """C:EXEC - 실행 관리 테스트"""
    
    def test_get_available_actions(self, auth_headers):
        """사용 가능한 액션 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/c/actions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "actions" in data
        action_names = [a["action"] for a in data["actions"]]
        assert "analyze" in action_names
        assert "assetize" in action_names
        print(f"✓ C:Exec - 액션 {len(data.get('actions', []))}개 조회 성공")
    
    def test_get_execution_queue(self, auth_headers):
        """실행 대기열 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/c/queue", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "queue" in data
        print(f"✓ C:Exec - 실행 대기열 조회 성공")
    
    def test_get_execution_history(self, auth_headers):
        """실행 이력 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/c/history?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "history" in data
        print(f"✓ C:Exec - 실행 이력 조회 성공")


class TestFField(TestAuth):
    """F:FIELD - 마켓플레이스 테스트"""
    
    def test_browse_marketplace(self, auth_headers):
        """마켓플레이스 브라우징"""
        response = requests.get(f"{BASE_URL}/api/patent/f/marketplace?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "listings" in data
        assert "total" in data
        print(f"✓ F:Field - 마켓플레이스 조회 성공: {data.get('total')}개 등록")
    
    def test_get_marketplace_stats(self, auth_headers):
        """마켓플레이스 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ F:Field - 마켓플레이스 통계 조회 성공")


class TestDLedger(TestAuth):
    """D:LEDGER - 분산원장 테스트"""
    
    def test_record_transaction(self, auth_headers):
        """거래 기록"""
        response = requests.post(
            f"{BASE_URL}/api/patent/d/record",
            headers=auth_headers,
            json={
                "transaction_type": "transfer",
                "from_account": "TEST_USER_A",
                "to_account": "TEST_USER_B",
                "amount": 100.0,
                "metadata": {"test": True}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "transaction_id" in data
        print(f"✓ D:Ledger - 거래 기록 성공: tx_id={data.get('transaction_id')}")
    
    def test_query_ledger(self, auth_headers):
        """원장 조회 (POST /query)"""
        response = requests.post(
            f"{BASE_URL}/api/patent/d/query?limit=10",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "transactions" in data
        print(f"✓ D:Ledger - 원장 조회 성공: {len(data.get('transactions', []))}건")
    
    def test_verify_chain(self, auth_headers):
        """체인 무결성 검증"""
        response = requests.get(f"{BASE_URL}/api/patent/d/verify-chain", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "valid" in data
        print(f"✓ D:Ledger - 체인 검증 성공: valid={data.get('valid')}")
    
    def test_get_account_balance(self, auth_headers):
        """계정 잔액 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/d/balance/TEST_USER_B", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "balance" in data
        print(f"✓ D:Ledger - 계정 잔액 조회 성공: balance={data.get('balance')}")
    
    def test_get_latest_blocks(self, auth_headers):
        """최근 블록 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/d/latest-blocks?limit=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "blocks" in data
        print(f"✓ D:Ledger - 최근 블록 조회 성공: {len(data.get('blocks', []))}개")


class TestIIntegrity(TestAuth):
    """I:INTEGRITY - 무결성 검사 테스트"""
    
    def test_get_system_health(self, auth_headers):
        """시스템 헬스 체크"""
        response = requests.get(f"{BASE_URL}/api/patent/i/health", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "health" in data
        print(f"✓ I:Integrity - 시스템 헬스 체크 성공")
    
    def test_get_integrity_stats(self, auth_headers):
        """무결성 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/i/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "stats" in data
        print(f"✓ I:Integrity - 무결성 통계 조회 성공")
    
    def test_run_system_integrity_check(self, auth_headers):
        """시스템 전체 무결성 검사"""
        response = requests.post(f"{BASE_URL}/api/patent/i/system-check", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "results" in data
        print(f"✓ I:Integrity - 시스템 무결성 검사 성공")
    
    def test_get_audit_logs(self, auth_headers):
        """감사 로그 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/i/audit-logs?limit=10", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "logs" in data
        print(f"✓ I:Integrity - 감사 로그 조회 성공: {len(data.get('logs', []))}건")
    
    def test_create_audit_log(self, auth_headers):
        """감사 로그 기록"""
        response = requests.post(
            f"{BASE_URL}/api/patent/i/audit-log",
            headers=auth_headers,
            json={
                "action": "test_action",
                "entity_type": "test",
                "entity_id": "TEST_ENTITY_001",
                "user_id": "test_user",
                "details": {"test": True}
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") == True
        assert "audit_id" in data
        print(f"✓ I:Integrity - 감사 로그 기록 성공: audit_id={data.get('audit_id')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
