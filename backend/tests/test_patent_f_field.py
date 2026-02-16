"""
특허 F: FIELD - 물리 계층 자원 집행 시스템 테스트
(Physical Layer Resource Execution System Based on Entropy Control)

테스트 대상:
- 1110: 자원 사영 엔진 (Resource Projection Engine)
- 1120: 팩토리 평형 컨트롤러 (Factory Equilibrium Controller)
- 1130: 엔트로피 역전 유닛 (Entropy Reversal Unit)
- 열역학적 킬스위치 (Thermodynamic Kill-switch)
- 하드웨어 상태 보정기 (Hardware State Corrector)
- 위상 정합 엔진 (Phase Alignment Engine)
- D:LEDGER 동기화
- I:INTEGRITY 검증 연동
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestResourceProjectionEngine:
    """1110: 자원 사영 엔진 테스트"""
    
    def test_project_resources_basic(self):
        """기본 자원 사영 테스트"""
        payload = {
            "execution_id": f"EXEC_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "total_value": 10000,
            "public_allocation": 5000,      # 5:3:2 비율 - 공공 50%
            "operation_allocation": 3000,   # 운영 30%
            "management_allocation": 2000,  # 관리 20%
            "source_signal_id": "SIG_TEST_001"
        }
        
        response = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=payload)
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert data["execution_id"] == payload["execution_id"]
        assert "projection_results" in data
        assert "total_entropy_cost" in data
        assert "theoretical_vs_actual" in data
        
        # 사영 결과 검증
        if data["projection_results"]:
            result = data["projection_results"][0]
            assert "node_id" in result
            assert "region" in result
            assert "projected_physical_value" in result
            assert "entropy_cost" in result
            assert "projection_accuracy" in result
        
        print(f"✓ 자원 사영 성공: {len(data['projection_results'])}개 노드에 사영됨")
        print(f"  - 총 엔트로피 비용: {data['total_entropy_cost']}")
        print(f"  - 이론값 vs 실제값: {data['theoretical_vs_actual']}")
        
        return data["execution_id"]
    
    def test_get_projection_result(self):
        """사영 결과 조회 테스트"""
        # 먼저 사영 실행
        exec_id = f"EXEC_GET_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "execution_id": exec_id,
            "total_value": 5000,
            "public_allocation": 2500,
            "operation_allocation": 1500,
            "management_allocation": 1000
        }
        
        create_response = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=payload)
        assert create_response.status_code == 200
        
        # 결과 조회
        response = requests.get(f"{BASE_URL}/api/patent/f/projection/{exec_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "projection" in data
        assert data["projection"]["execution_id"] == exec_id
        
        print(f"✓ 사영 결과 조회 성공: {exec_id}")
    
    def test_projection_not_found(self):
        """존재하지 않는 사영 결과 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/projection/NON_EXISTENT_ID")
        
        assert response.status_code == 404
        print("✓ 존재하지 않는 사영 결과 404 반환 확인")


class TestFactoryEquilibriumController:
    """1120: 팩토리 평형 컨트롤러 테스트"""
    
    def test_get_factory_balance(self):
        """팩토리 균형 상태 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/factory-balance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "factory_balance" in data
        
        balance = data["factory_balance"]
        assert "regions" in balance
        assert "total_deviation" in balance
        assert "system_balanced" in balance
        assert "equilibrium_constants" in balance
        
        # 영역별 균형 상태 검증
        for region, status in balance["regions"].items():
            assert "node_count" in status
            assert "average_load" in status
            assert "equilibrium_constant" in status
            assert "is_balanced" in status
        
        print(f"✓ 팩토리 균형 상태 조회 성공")
        print(f"  - 시스템 균형 상태: {balance['system_balanced']}")
        print(f"  - 총 편차: {balance['total_deviation']}")
        print(f"  - 평형 상수: {balance['equilibrium_constants']}")
    
    def test_rebalance_factory(self):
        """팩토리 재균형 테스트"""
        response = requests.post(f"{BASE_URL}/api/patent/f/rebalance")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "rebalance_id" in data
        assert "actions_count" in data
        assert "actions" in data
        
        print(f"✓ 팩토리 재균형 성공: {data['rebalance_id']}")
        print(f"  - 조치 수: {data['actions_count']}")
    
    def test_rebalance_specific_region(self):
        """특정 영역 재균형 테스트"""
        response = requests.post(f"{BASE_URL}/api/patent/f/rebalance?target_region=public")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        
        # 모든 액션이 public 영역에 대한 것인지 확인
        for action in data["actions"]:
            assert action["region"] == "public"
        
        print(f"✓ 특정 영역(public) 재균형 성공")


class TestEntropyReversalUnit:
    """1130: 엔트로피 역전 유닛 테스트"""
    
    def test_get_entropy_status(self):
        """엔트로피 상태 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/entropy-status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "entropy_status" in data
        
        status = data["entropy_status"]
        assert "current_entropy" in status
        assert "average_entropy" in status
        assert "entropy_rate_dS_dt" in status
        assert "heat_generation_estimate" in status
        assert "energy_efficiency" in status
        assert "threshold" in status
        assert "status" in status
        
        print(f"✓ 엔트로피 상태 조회 성공")
        print(f"  - 현재 엔트로피: {status['current_entropy']}")
        print(f"  - 엔트로피 변화율 (dS/dt): {status['entropy_rate_dS_dt']}")
        print(f"  - 에너지 효율: {status['energy_efficiency']}")
        print(f"  - 상태: {status['status']}")
    
    def test_entropy_feedback_to_refine(self):
        """엔트로피 피드백 (G:REFINE 연동)"""
        response = requests.post(f"{BASE_URL}/api/patent/f/entropy-feedback")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "feedback_id" in data
        assert "feedback_coefficient" in data
        assert "recommended_actions" in data
        assert "entropy_reversed" in data
        
        print(f"✓ 엔트로피 피드백 성공: {data['feedback_id']}")
        print(f"  - 피드백 계수: {data['feedback_coefficient']}")
        print(f"  - 권장 조치: {len(data['recommended_actions'])}개")


class TestThermodynamicKillSwitch:
    """열역학적 킬스위치 테스트"""
    
    def test_get_thresholds(self):
        """물리적 임계치 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/thresholds")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "thresholds" in data
        assert "description" in data
        
        thresholds = data["thresholds"]
        assert "temperature_max" in thresholds
        assert "cpu_utilization_max" in thresholds
        assert "memory_utilization_max" in thresholds
        assert "entropy_rate_max" in thresholds
        assert "signal_decay_max" in thresholds
        assert "hardware_wear_max" in thresholds
        
        print(f"✓ 물리적 임계치 조회 성공")
        print(f"  - 최대 온도: {thresholds['temperature_max']}°C")
        print(f"  - 최대 CPU: {thresholds['cpu_utilization_max']}%")
        print(f"  - 최대 엔트로피율: {thresholds['entropy_rate_max']}")
    
    def test_activate_kill_switch(self):
        """킬스위치 활성화 테스트"""
        node_id = f"TEST_NODE_{datetime.now().strftime('%H%M%S')}"
        
        response = requests.post(
            f"{BASE_URL}/api/patent/f/kill-switch",
            params={"node_id": node_id, "reason": "테스트 킬스위치 발동"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["node_id"] == node_id
        assert data["status"] == "deactivated"
        assert "kill_id" in data
        
        print(f"✓ 킬스위치 활성화 성공: {data['kill_id']}")
        print(f"  - 노드: {node_id}")
        print(f"  - 상태: {data['status']}")
        
        return node_id
    
    def test_restore_node(self):
        """노드 복원 테스트"""
        # 먼저 킬스위치 발동
        node_id = f"RESTORE_TEST_{datetime.now().strftime('%H%M%S')}"
        kill_response = requests.post(
            f"{BASE_URL}/api/patent/f/kill-switch",
            params={"node_id": node_id, "reason": "복원 테스트용"}
        )
        assert kill_response.status_code == 200
        
        # 노드 복원
        response = requests.post(f"{BASE_URL}/api/patent/f/kill-switch/restore/{node_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["node_id"] == node_id
        assert data["status"] == "restored"
        
        print(f"✓ 노드 복원 성공: {node_id}")
    
    def test_auto_check_kill_switch(self):
        """자동 킬스위치 검사"""
        response = requests.post(f"{BASE_URL}/api/patent/f/kill-switch/auto-check")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "checked" in data
        assert "triggered" in data
        
        print(f"✓ 자동 킬스위치 검사 완료")
        print(f"  - 검사된 노드: {data['checked']}")
        print(f"  - 발동된 킬스위치: {data['triggered']}")


class TestHardwareStateCorrector:
    """하드웨어 상태 보정기 테스트"""
    
    def test_hardware_correction(self):
        """하드웨어 상태 보정 테스트"""
        node_id = f"HW_TEST_{datetime.now().strftime('%H%M%S')}"
        
        response = requests.post(
            f"{BASE_URL}/api/patent/f/hardware-correction",
            params={"node_id": node_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["node_id"] == node_id
        assert "hardware_state" in data
        assert "correction" in data
        
        hw_state = data["hardware_state"]
        assert "wear_rate" in hw_state
        assert "operational_hours" in hw_state
        assert "lifetime_ratio" in hw_state
        
        correction = data["correction"]
        assert "original_weight" in correction
        assert "correction_factor" in correction
        assert "new_weight" in correction
        
        print(f"✓ 하드웨어 상태 보정 성공: {node_id}")
        print(f"  - 마모율: {hw_state['wear_rate']}")
        print(f"  - 수명 비율: {hw_state['lifetime_ratio']}")
        print(f"  - 보정 계수: {correction['correction_factor']}")
        print(f"  - 새 가중치: {correction['new_weight']}")


class TestPhaseAlignmentEngine:
    """위상 정합 엔진 테스트"""
    
    def test_phase_alignment(self):
        """위상 정합 테스트"""
        # 먼저 여러 집행 생성
        exec_ids = []
        for i in range(3):
            payload = {
                "execution_id": f"PHASE_TEST_{i}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "total_value": 1000 * (i + 1),
                "public_allocation": 500 * (i + 1),
                "operation_allocation": 300 * (i + 1),
                "management_allocation": 200 * (i + 1)
            }
            resp = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=payload)
            if resp.status_code == 200:
                exec_ids.append(payload["execution_id"])
        
        if not exec_ids:
            pytest.skip("집행 생성 실패")
        
        # 위상 정합 실행
        response = requests.post(
            f"{BASE_URL}/api/patent/f/phase-alignment",
            json=exec_ids
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "reference_time" in data
        assert "alignment_results" in data
        assert "all_aligned" in data
        
        for result in data["alignment_results"]:
            assert "execution_id" in result
            assert "time_delta_ms" in result
            assert "phase_difference_rad" in result
            assert "sync_correction_ms" in result
            assert "aligned" in result
        
        print(f"✓ 위상 정합 성공")
        print(f"  - 정합된 집행 수: {len(data['alignment_results'])}")
        print(f"  - 전체 정합 상태: {data['all_aligned']}")
    
    def test_phase_alignment_no_executions(self):
        """존재하지 않는 집행 위상 정합"""
        response = requests.post(
            f"{BASE_URL}/api/patent/f/phase-alignment",
            json=["NON_EXISTENT_1", "NON_EXISTENT_2"]
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == False
        assert "error" in data
        
        print("✓ 존재하지 않는 집행 위상 정합 에러 처리 확인")


class TestDLedgerSync:
    """D:LEDGER 동기화 테스트"""
    
    def test_sync_to_ledger(self):
        """원장 동기화 테스트"""
        # 먼저 집행 생성
        exec_id = f"LEDGER_SYNC_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "execution_id": exec_id,
            "total_value": 10000,
            "public_allocation": 5000,
            "operation_allocation": 3000,
            "management_allocation": 2000
        }
        
        create_resp = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=payload)
        assert create_resp.status_code == 200
        
        # 원장 동기화
        response = requests.post(
            f"{BASE_URL}/api/patent/f/sync-to-ledger",
            params={"execution_id": exec_id}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert data["execution_id"] == exec_id
        assert "proof_hash" in data
        assert "ledger_transaction_id" in data
        assert data["is_irreversible"] == True
        assert data["synced_to"] == "D:LEDGER"
        
        print(f"✓ D:LEDGER 동기화 성공: {exec_id}")
        print(f"  - 증명 해시: {data['proof_hash'][:16]}...")
        print(f"  - 원장 트랜잭션 ID: {data['ledger_transaction_id']}")
        print(f"  - 비가역성: {data['is_irreversible']}")
        
        return exec_id
    
    def test_sync_to_ledger_not_found(self):
        """존재하지 않는 집행 동기화"""
        response = requests.post(
            f"{BASE_URL}/api/patent/f/sync-to-ledger",
            params={"execution_id": "NON_EXISTENT_EXEC"}
        )
        
        assert response.status_code == 404
        print("✓ 존재하지 않는 집행 동기화 404 반환 확인")


class TestIntegrityVerification:
    """I:INTEGRITY 검증 연동 테스트"""
    
    def test_verify_with_integrity(self):
        """무결성 검증 테스트"""
        # 먼저 집행 생성 및 원장 동기화
        exec_id = f"INTEGRITY_TEST_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        payload = {
            "execution_id": exec_id,
            "total_value": 5000,
            "public_allocation": 2500,
            "operation_allocation": 1500,
            "management_allocation": 1000
        }
        
        # 집행 생성
        create_resp = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=payload)
        assert create_resp.status_code == 200
        
        # 원장 동기화
        sync_resp = requests.post(
            f"{BASE_URL}/api/patent/f/sync-to-ledger",
            params={"execution_id": exec_id}
        )
        assert sync_resp.status_code == 200
        
        # 무결성 검증
        response = requests.post(f"{BASE_URL}/api/patent/f/verify-with-integrity/{exec_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "verification" in data
        
        verification = data["verification"]
        assert verification["execution_id"] == exec_id
        assert "verification_status" in verification
        assert "hash_verification" in verification
        assert "audit_id" in verification
        assert verification["integrity_node"] == "I:INTEGRITY"
        
        hash_check = verification["hash_verification"]
        assert "original_hash" in hash_check
        assert "recalculated_hash" in hash_check
        assert "match" in hash_check
        
        print(f"✓ I:INTEGRITY 검증 성공: {exec_id}")
        print(f"  - 검증 상태: {verification['verification_status']}")
        print(f"  - 해시 일치: {hash_check['match']}")
        print(f"  - 감사 ID: {verification['audit_id']}")
    
    def test_verify_not_found(self):
        """존재하지 않는 집행 검증"""
        response = requests.post(f"{BASE_URL}/api/patent/f/verify-with-integrity/NON_EXISTENT")
        
        assert response.status_code == 404
        print("✓ 존재하지 않는 집행 검증 404 반환 확인")


class TestFieldStats:
    """F:FIELD 통합 통계 테스트"""
    
    def test_get_field_stats(self):
        """통합 통계 조회"""
        response = requests.get(f"{BASE_URL}/api/patent/f/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "stats" in data
        
        stats = data["stats"]
        assert "marketplace" in stats
        assert "physical_layer" in stats
        assert "system_health" in stats
        
        physical = stats["physical_layer"]
        assert "total_nodes" in physical
        assert "active_nodes" in physical
        assert "total_executions" in physical
        assert "current_entropy" in physical
        
        print(f"✓ F:FIELD 통합 통계 조회 성공")
        print(f"  - 총 노드: {physical['total_nodes']}")
        print(f"  - 활성 노드: {physical['active_nodes']}")
        print(f"  - 총 집행: {physical['total_executions']}")
        print(f"  - 시스템 상태: {stats['system_health']}")


class TestEndToEndFlow:
    """E2E 흐름 테스트: 5:3:2 결이론 → 물리적 자원 사영 → 원장 기록 → 무결성 검증"""
    
    def test_complete_flow(self):
        """전체 흐름 테스트"""
        exec_id = f"E2E_FLOW_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Step 1: 5:3:2 결이론 기반 가치 분배 (자원 사영)
        print("\n=== Step 1: 자원 사영 (5:3:2 결이론 기반) ===")
        projection_payload = {
            "execution_id": exec_id,
            "total_value": 10000,
            "public_allocation": 5000,      # 50%
            "operation_allocation": 3000,   # 30%
            "management_allocation": 2000,  # 20%
            "source_signal_id": "E2E_TEST_SIGNAL"
        }
        
        proj_resp = requests.post(f"{BASE_URL}/api/patent/f/project-resources", json=projection_payload)
        assert proj_resp.status_code == 200
        proj_data = proj_resp.json()
        assert proj_data["success"] == True
        print(f"  ✓ 자원 사영 완료: {len(proj_data['projection_results'])}개 노드")
        print(f"    - 엔트로피 비용: {proj_data['total_entropy_cost']}")
        
        # Step 2: 원장 기록 (D:LEDGER 동기화)
        print("\n=== Step 2: D:LEDGER 동기화 ===")
        sync_resp = requests.post(
            f"{BASE_URL}/api/patent/f/sync-to-ledger",
            params={"execution_id": exec_id}
        )
        assert sync_resp.status_code == 200
        sync_data = sync_resp.json()
        assert sync_data["success"] == True
        print(f"  ✓ 원장 동기화 완료")
        print(f"    - 증명 해시: {sync_data['proof_hash'][:32]}...")
        print(f"    - 트랜잭션 ID: {sync_data['ledger_transaction_id']}")
        
        # Step 3: 무결성 검증 (I:INTEGRITY 연동)
        print("\n=== Step 3: I:INTEGRITY 무결성 검증 ===")
        verify_resp = requests.post(f"{BASE_URL}/api/patent/f/verify-with-integrity/{exec_id}")
        assert verify_resp.status_code == 200
        verify_data = verify_resp.json()
        assert verify_data["success"] == True
        
        verification = verify_data["verification"]
        print(f"  ✓ 무결성 검증 완료")
        print(f"    - 검증 상태: {verification['verification_status']}")
        print(f"    - 해시 일치: {verification['hash_verification']['match']}")
        
        # Step 4: 최종 상태 확인
        print("\n=== Step 4: 최종 상태 확인 ===")
        stats_resp = requests.get(f"{BASE_URL}/api/patent/f/stats")
        assert stats_resp.status_code == 200
        stats_data = stats_resp.json()
        print(f"  ✓ 시스템 상태: {stats_data['stats']['system_health']}")
        
        print(f"\n✓✓✓ E2E 흐름 테스트 완료: {exec_id} ✓✓✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
