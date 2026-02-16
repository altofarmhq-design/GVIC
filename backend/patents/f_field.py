"""
F: FIELD - 물리 계층 자원 집행 시스템
(Physical Layer Resource Execution System Based on Entropy Control)

특허 핵심 구성요소:
- 1110: 자원 사영 엔진 (Resource Projection Engine)
- 1120: 팩토리 평형 컨트롤러 (Factory Equilibrium Controller)
- 1130: 엔트로피 역전 유닛 (Entropy Reversal Unit)
- 열역학적 킬스위치 (Thermodynamic Kill-switch)
- 하드웨어 상태 보정기 (Hardware State Corrector)
- 위상 정합 엔진 (Phase Alignment Engine)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import logging
import math
import hashlib

router = APIRouter(prefix="/api/patent/f", tags=["F:FIELD"])
logger = logging.getLogger(__name__)

# ==================== 물리 계층 상수 ====================

# 5:3:2 결이론 비율 (H:CORE에서 정의)
PUBLIC_RATIO = 0.5
OPERATION_RATIO = 0.3
MANAGEMENT_RATIO = 0.2

# 물리적 임계치 기본값
DEFAULT_THRESHOLDS = {
    "temperature_max": 85.0,      # 최대 온도 (°C)
    "cpu_utilization_max": 90.0,  # 최대 CPU 사용률 (%)
    "memory_utilization_max": 85.0,  # 최대 메모리 사용률 (%)
    "entropy_rate_max": 0.15,     # 최대 엔트로피 상승률
    "signal_decay_max": 0.20,     # 최대 신호 감쇄율
    "hardware_wear_max": 0.80     # 최대 하드웨어 마모율
}

# 평형 상수 (영역별)
EQUILIBRIUM_CONSTANTS = {
    "public": 1.0,      # 공공 영역
    "operation": 0.8,   # 운영 영역
    "management": 0.6   # 관리 영역
}

# ==================== Models ====================

class AllocationVector(BaseModel):
    """배분 벡터 (C:EXEC에서 전달)"""
    execution_id: str
    total_value: float
    public_allocation: float = Field(description="공공 배분 (5)")
    operation_allocation: float = Field(description="운영 배분 (3)")
    management_allocation: float = Field(description="관리 배분 (2)")
    source_signal_id: Optional[str] = None

class NodeState(BaseModel):
    """노드 상태 벡터 F_state"""
    node_id: str
    node_type: str  # compute, storage, network
    temperature: float = 45.0
    cpu_utilization: float = 30.0
    memory_utilization: float = 40.0
    energy_consumption: float = 100.0  # Watts
    operational_capacity: float = 1.0  # 0-1
    hardware_wear_rate: float = 0.0    # 마모율 0-1
    signal_latency: float = 0.0        # ms
    is_active: bool = True

class ProjectionResult(BaseModel):
    """자원 사영 결과"""
    node_id: str
    allocated_physical_resources: Dict[str, float]
    entropy_cost: float
    projection_accuracy: float

class EntropyState(BaseModel):
    """엔트로피 상태"""
    system_entropy: float
    entropy_rate: float  # dS/dt
    heat_generation: float
    energy_efficiency: float

class ExecutionProof(BaseModel):
    """집행 증명 (D:LEDGER로 전송)"""
    execution_id: str
    physical_results: Dict[str, Any]
    entropy_delta: float
    proof_hash: str
    timestamp: str

# ==================== 1110: 자원 사영 엔진 ====================

@router.post("/project-resources")
async def project_resources(allocation: AllocationVector):
    """
    배분 벡터를 물리적 자원량으로 사영 (Projection)
    
    수리 모델:
    E_i(t) = ∫(R_alloc · F_i - κ · dS_i/dt) dt
    """
    from server import db
    
    # 활성 노드 조회
    nodes = await db.physical_nodes.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    if not nodes:
        # 기본 시뮬레이션 노드 생성
        nodes = [
            {"node_id": "NODE_PUBLIC_01", "node_type": "compute", "region": "public", "capacity": 1.0, "temperature": 45.0, "cpu_utilization": 30.0},
            {"node_id": "NODE_OPERATION_01", "node_type": "compute", "region": "operation", "capacity": 0.8, "temperature": 50.0, "cpu_utilization": 40.0},
            {"node_id": "NODE_MANAGEMENT_01", "node_type": "compute", "region": "management", "capacity": 0.6, "temperature": 42.0, "cpu_utilization": 25.0}
        ]
    
    projection_results = []
    total_entropy_cost = 0
    
    # 영역별 노드에 자원 사영
    region_allocations = {
        "public": allocation.public_allocation,
        "operation": allocation.operation_allocation,
        "management": allocation.management_allocation
    }
    
    for node in nodes:
        region = node.get("region", "public")
        region_value = region_allocations.get(region, 0)
        
        # 노드 상태 벡터
        F_i = node.get("capacity", 1.0)
        T_i = node.get("temperature", 45.0)
        cpu = node.get("cpu_utilization", 30.0)
        
        # 열역학적 구속 조건 검사
        if T_i >= DEFAULT_THRESHOLDS["temperature_max"]:
            continue  # 임계치 초과 노드 제외
        
        # 엔트로피 변화율 계산
        kappa = 0.01  # 열역학적 손실 계수
        dS_dt = kappa * (cpu / 100) * (T_i / 100)
        
        # 물리량 사영: E_i = R_alloc · F_i - κ · dS/dt
        equilibrium_k = EQUILIBRIUM_CONSTANTS.get(region, 1.0)
        physical_value = (region_value * F_i * equilibrium_k) - (kappa * dS_dt * 1000)
        physical_value = max(0, physical_value)
        
        # 사영 정확도 계산 (라그랑주 승수법 근사)
        projection_accuracy = 1.0 - (dS_dt * 10)  # 엔트로피에 따른 정확도 감소
        projection_accuracy = max(0.5, min(1.0, projection_accuracy))
        
        result = {
            "node_id": node["node_id"],
            "region": region,
            "input_value": region_value,
            "projected_physical_value": round(physical_value, 4),
            "entropy_cost": round(dS_dt * 100, 4),
            "projection_accuracy": round(projection_accuracy, 4),
            "node_state": {
                "temperature": T_i,
                "cpu_utilization": cpu,
                "capacity": F_i
            }
        }
        
        projection_results.append(result)
        total_entropy_cost += dS_dt
    
    # 집행 기록 저장
    execution_record = {
        "execution_id": allocation.execution_id,
        "allocation_vector": allocation.dict(),
        "projection_results": projection_results,
        "total_entropy_cost": round(total_entropy_cost * 100, 4),
        "projected_at": datetime.now(timezone.utc).isoformat(),
        "status": "projected"
    }
    
    await db.field_executions.insert_one(execution_record)
    
    return {
        "success": True,
        "execution_id": allocation.execution_id,
        "projection_results": projection_results,
        "total_entropy_cost": round(total_entropy_cost * 100, 4),
        "theoretical_vs_actual": {
            "theoretical_total": allocation.total_value,
            "actual_projected": sum(r["projected_physical_value"] for r in projection_results),
            "accuracy": round(sum(r["projection_accuracy"] for r in projection_results) / len(projection_results) * 100, 2) if projection_results else 0
        }
    }

@router.get("/projection/{execution_id}")
async def get_projection_result(execution_id: str):
    """사영 결과 조회"""
    from server import db
    
    result = await db.field_executions.find_one(
        {"execution_id": execution_id},
        {"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="사영 결과를 찾을 수 없습니다")
    
    return {"success": True, "projection": result}

# ==================== 1120: 팩토리 평형 컨트롤러 ====================

@router.get("/factory-balance")
async def get_factory_balance():
    """
    분산 노드 간 부하 균형 상태 조회
    영역별 평형 상수(Equilibrium Constants) 기반
    """
    from server import db
    
    nodes = await db.physical_nodes.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    if not nodes:
        # 시뮬레이션 데이터
        nodes = [
            {"node_id": "NODE_PUBLIC_01", "region": "public", "load": 0.45, "capacity": 1.0},
            {"node_id": "NODE_PUBLIC_02", "region": "public", "load": 0.52, "capacity": 1.0},
            {"node_id": "NODE_OPERATION_01", "region": "operation", "load": 0.38, "capacity": 0.8},
            {"node_id": "NODE_MANAGEMENT_01", "region": "management", "load": 0.25, "capacity": 0.6}
        ]
    
    # 영역별 부하 집계
    region_loads = {"public": [], "operation": [], "management": []}
    
    for node in nodes:
        region = node.get("region", "public")
        load = node.get("load", node.get("cpu_utilization", 30) / 100)
        if region in region_loads:
            region_loads[region].append({
                "node_id": node["node_id"],
                "load": load,
                "capacity": node.get("capacity", 1.0)
            })
    
    # 평형 상태 계산
    balance_status = {}
    total_deviation = 0
    
    for region, nodes_in_region in region_loads.items():
        if not nodes_in_region:
            continue
            
        loads = [n["load"] for n in nodes_in_region]
        avg_load = sum(loads) / len(loads)
        variance = sum((l - avg_load) ** 2 for l in loads) / len(loads)
        std_dev = math.sqrt(variance)
        
        # 평형 상수와 비교
        equilibrium_k = EQUILIBRIUM_CONSTANTS[region]
        target_load = equilibrium_k * 0.5  # 목표 부하 = 평형상수 * 50%
        deviation = abs(avg_load - target_load)
        total_deviation += deviation
        
        balance_status[region] = {
            "node_count": len(nodes_in_region),
            "nodes": nodes_in_region,
            "average_load": round(avg_load, 4),
            "std_deviation": round(std_dev, 4),
            "equilibrium_constant": equilibrium_k,
            "target_load": target_load,
            "deviation_from_target": round(deviation, 4),
            "is_balanced": std_dev < 0.1 and deviation < 0.15
        }
    
    # 전체 시스템 평형 상태
    all_balanced = all(s.get("is_balanced", False) for s in balance_status.values())
    
    return {
        "success": True,
        "factory_balance": {
            "regions": balance_status,
            "total_deviation": round(total_deviation, 4),
            "system_balanced": all_balanced,
            "equilibrium_constants": EQUILIBRIUM_CONSTANTS,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    }

@router.post("/rebalance")
async def rebalance_factory(target_region: Optional[str] = None):
    """
    팩토리 노드 간 부하 재균형
    미분 방정식 기반 유량 편차 소거
    """
    from server import db
    
    # 현재 균형 상태 조회
    balance = await get_factory_balance()
    regions = balance["factory_balance"]["regions"]
    
    rebalance_actions = []
    
    for region, status in regions.items():
        if target_region and region != target_region:
            continue
            
        if status["is_balanced"]:
            continue
        
        nodes = status["nodes"]
        target_load = status["target_load"]
        
        # 부하 재분배 계산 (위치 에너지 평형화)
        for node in nodes:
            current_load = node["load"]
            adjustment = (target_load - current_load) * 0.5  # PID 제어 근사
            new_load = current_load + adjustment
            new_load = max(0.1, min(0.9, new_load))  # 범위 제한
            
            action = {
                "node_id": node["node_id"],
                "region": region,
                "current_load": round(current_load, 4),
                "target_load": round(target_load, 4),
                "adjustment": round(adjustment, 4),
                "new_load": round(new_load, 4)
            }
            rebalance_actions.append(action)
            
            # DB 업데이트 (시뮬레이션)
            await db.physical_nodes.update_one(
                {"node_id": node["node_id"]},
                {"$set": {"load": new_load, "rebalanced_at": datetime.now(timezone.utc).isoformat()}},
                upsert=True
            )
    
    # 재균형 이력 기록
    rebalance_record = {
        "rebalance_id": f"REB_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "target_region": target_region,
        "actions": rebalance_actions,
        "executed_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.rebalance_history.insert_one(rebalance_record)
    
    return {
        "success": True,
        "rebalance_id": rebalance_record["rebalance_id"],
        "actions_count": len(rebalance_actions),
        "actions": rebalance_actions
    }

# ==================== 1130: 엔트로피 역전 유닛 ====================

@router.get("/entropy-status")
async def get_entropy_status():
    """
    시스템 엔트로피 상태 조회
    dS/dt (엔트로피 상승률) 모니터링
    """
    from server import db
    
    # 최근 집행 기록에서 엔트로피 데이터 수집
    recent_executions = await db.field_executions.find(
        {},
        {"_id": 0, "total_entropy_cost": 1, "projected_at": 1}
    ).sort("projected_at", -1).limit(100).to_list(100)
    
    if not recent_executions:
        # 시뮬레이션 데이터
        entropy_values = [0.05, 0.06, 0.04, 0.07, 0.05]
    else:
        entropy_values = [e.get("total_entropy_cost", 0.05) for e in recent_executions]
    
    # 엔트로피 통계 계산
    current_entropy = entropy_values[0] if entropy_values else 0
    avg_entropy = sum(entropy_values) / len(entropy_values) if entropy_values else 0
    
    # 엔트로피 변화율 (dS/dt) 추정
    if len(entropy_values) >= 2:
        entropy_rate = (entropy_values[0] - entropy_values[-1]) / len(entropy_values)
    else:
        entropy_rate = 0
    
    # 열 발생량 추정 (Q = T * dS)
    avg_temp = 50  # 평균 온도 추정
    heat_generation = avg_temp * abs(entropy_rate) * 100
    
    # 에너지 효율 계산
    if current_entropy > 0:
        energy_efficiency = max(0, 1 - (current_entropy / DEFAULT_THRESHOLDS["entropy_rate_max"]))
    else:
        energy_efficiency = 1.0
    
    entropy_status = {
        "current_entropy": round(current_entropy, 6),
        "average_entropy": round(avg_entropy, 6),
        "entropy_rate_dS_dt": round(entropy_rate, 6),
        "heat_generation_estimate": round(heat_generation, 4),
        "energy_efficiency": round(energy_efficiency, 4),
        "threshold": DEFAULT_THRESHOLDS["entropy_rate_max"],
        "status": "normal" if current_entropy < DEFAULT_THRESHOLDS["entropy_rate_max"] else "warning",
        "samples_analyzed": len(entropy_values),
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }
    
    return {"success": True, "entropy_status": entropy_status}

@router.post("/entropy-feedback")
async def entropy_feedback_to_refine():
    """
    엔트로피 손실량을 G:정제(REFINE) 노드로 피드백
    에너지 보존 및 시스템 최적화
    """
    from server import db
    
    # 현재 엔트로피 상태 조회
    entropy_status = await get_entropy_status()
    entropy_data = entropy_status["entropy_status"]
    
    # 피드백 계수 계산
    feedback_coefficient = 1.0 - entropy_data["energy_efficiency"]
    
    # 정제 노드에 보정 요청 생성
    feedback_record = {
        "feedback_id": f"FB_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "source": "F:FIELD (엔트로피 역전 유닛)",
        "destination": "G:REFINE (정제 노드)",
        "entropy_data": entropy_data,
        "feedback_coefficient": round(feedback_coefficient, 6),
        "recommended_actions": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 권장 조치 결정
    if entropy_data["current_entropy"] > DEFAULT_THRESHOLDS["entropy_rate_max"] * 0.8:
        feedback_record["recommended_actions"].append({
            "action": "reduce_processing_load",
            "priority": "high",
            "reason": "엔트로피가 임계치의 80% 초과"
        })
    
    if entropy_data["energy_efficiency"] < 0.7:
        feedback_record["recommended_actions"].append({
            "action": "optimize_resource_allocation",
            "priority": "medium",
            "reason": "에너지 효율이 70% 미만"
        })
    
    if entropy_data["entropy_rate_dS_dt"] > 0:
        feedback_record["recommended_actions"].append({
            "action": "initiate_cooling_cycle",
            "priority": "low",
            "reason": "엔트로피 상승 추세 감지"
        })
    
    await db.entropy_feedback.insert_one(feedback_record)
    
    return {
        "success": True,
        "feedback_id": feedback_record["feedback_id"],
        "feedback_coefficient": feedback_record["feedback_coefficient"],
        "recommended_actions": feedback_record["recommended_actions"],
        "entropy_reversed": feedback_coefficient > 0
    }

# ==================== 열역학적 킬스위치 ====================

@router.get("/thresholds")
async def get_thresholds():
    """물리적 임계치 설정 조회"""
    return {
        "success": True,
        "thresholds": DEFAULT_THRESHOLDS,
        "description": {
            "temperature_max": "최대 허용 온도 (°C)",
            "cpu_utilization_max": "최대 CPU 사용률 (%)",
            "memory_utilization_max": "최대 메모리 사용률 (%)",
            "entropy_rate_max": "최대 엔트로피 상승률",
            "signal_decay_max": "최대 신호 감쇄율",
            "hardware_wear_max": "최대 하드웨어 마모율"
        }
    }

@router.post("/kill-switch")
async def activate_kill_switch(node_id: str, reason: str = "manual"):
    """
    열역학적 킬스위치 활성화
    임계치 초과 시 노드 유량 차단
    """
    from server import db
    
    # 노드 상태 조회
    node = await db.physical_nodes.find_one({"node_id": node_id}, {"_id": 0})
    
    if not node:
        # 시뮬레이션용 노드 생성
        node = {"node_id": node_id, "is_active": True, "temperature": 45.0}
    
    # 킬스위치 발동
    kill_record = {
        "kill_id": f"KILL_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "node_id": node_id,
        "reason": reason,
        "node_state_before": node,
        "activated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 노드 비활성화
    await db.physical_nodes.update_one(
        {"node_id": node_id},
        {"$set": {
            "is_active": False,
            "kill_switch_activated": True,
            "kill_reason": reason,
            "deactivated_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    await db.kill_switch_logs.insert_one(kill_record)
    
    return {
        "success": True,
        "kill_id": kill_record["kill_id"],
        "node_id": node_id,
        "status": "deactivated",
        "reason": reason,
        "message": f"노드 {node_id}의 유량이 차단되었습니다"
    }

@router.post("/kill-switch/auto-check")
async def auto_check_kill_switch():
    """
    자동 킬스위치 검사
    모든 노드의 임계치 초과 여부 확인
    """
    from server import db
    
    nodes = await db.physical_nodes.find(
        {"is_active": True},
        {"_id": 0}
    ).to_list(100)
    
    if not nodes:
        return {"success": True, "checked": 0, "triggered": 0, "nodes_checked": []}
    
    triggered_nodes = []
    
    for node in nodes:
        violations = []
        
        # 온도 체크
        if node.get("temperature", 0) >= DEFAULT_THRESHOLDS["temperature_max"]:
            violations.append(f"온도 초과: {node.get('temperature')}°C")
        
        # CPU 체크
        if node.get("cpu_utilization", 0) >= DEFAULT_THRESHOLDS["cpu_utilization_max"]:
            violations.append(f"CPU 초과: {node.get('cpu_utilization')}%")
        
        # 메모리 체크
        if node.get("memory_utilization", 0) >= DEFAULT_THRESHOLDS["memory_utilization_max"]:
            violations.append(f"메모리 초과: {node.get('memory_utilization')}%")
        
        # 하드웨어 마모율 체크
        if node.get("hardware_wear_rate", 0) >= DEFAULT_THRESHOLDS["hardware_wear_max"]:
            violations.append(f"마모율 초과: {node.get('hardware_wear_rate')}")
        
        if violations:
            # 킬스위치 발동
            await activate_kill_switch(node["node_id"], reason="; ".join(violations))
            triggered_nodes.append({
                "node_id": node["node_id"],
                "violations": violations
            })
    
    return {
        "success": True,
        "checked": len(nodes),
        "triggered": len(triggered_nodes),
        "triggered_nodes": triggered_nodes
    }

@router.post("/kill-switch/restore/{node_id}")
async def restore_node(node_id: str):
    """킬스위치 해제 및 노드 복원"""
    from server import db
    
    result = await db.physical_nodes.update_one(
        {"node_id": node_id},
        {"$set": {
            "is_active": True,
            "kill_switch_activated": False,
            "restored_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "node_id": node_id,
        "status": "restored",
        "message": f"노드 {node_id}가 복원되었습니다"
    }

# ==================== 하드웨어 상태 보정기 ====================

@router.post("/hardware-correction")
async def hardware_state_correction(node_id: str):
    """
    하드웨어 마모율 기반 집행 가중치 실시간 재계산
    """
    from server import db
    
    node = await db.physical_nodes.find_one({"node_id": node_id}, {"_id": 0})
    
    if not node:
        # 시뮬레이션 데이터
        node = {
            "node_id": node_id,
            "hardware_wear_rate": 0.15,
            "operational_hours": 8760,  # 1년
            "execution_weight": 1.0
        }
    
    # 마모율 기반 가중치 감쇄
    wear_rate = node.get("hardware_wear_rate", 0)
    operational_hours = node.get("operational_hours", 0)
    
    # 수명 주기 확률 모델 (와이블 분포 근사)
    expected_lifetime = 87600  # 10년 예상 수명
    lifetime_ratio = operational_hours / expected_lifetime
    
    # 새로운 가중치 계산
    # 마모율과 수명 비율에 따라 점진적 감쇄
    correction_factor = (1 - wear_rate) * (1 - lifetime_ratio * 0.5)
    correction_factor = max(0.1, min(1.0, correction_factor))
    
    new_weight = node.get("execution_weight", 1.0) * correction_factor
    
    # 업데이트
    await db.physical_nodes.update_one(
        {"node_id": node_id},
        {"$set": {
            "execution_weight": round(new_weight, 4),
            "correction_factor": round(correction_factor, 4),
            "corrected_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {
        "success": True,
        "node_id": node_id,
        "hardware_state": {
            "wear_rate": wear_rate,
            "operational_hours": operational_hours,
            "lifetime_ratio": round(lifetime_ratio, 4)
        },
        "correction": {
            "original_weight": node.get("execution_weight", 1.0),
            "correction_factor": round(correction_factor, 4),
            "new_weight": round(new_weight, 4)
        }
    }

# ==================== 위상 정합 엔진 ====================

@router.post("/phase-alignment")
async def phase_alignment(execution_ids: List[str]):
    """
    집행 신호의 전송 지연을 수리적 위상차로 계산하여 동기화
    """
    from server import db
    
    # 신호 전파 속도 상수 (시뮬레이션)
    SIGNAL_PROPAGATION_SPEED = 299792458  # m/s (광속)
    NETWORK_LATENCY_BASE = 10  # ms 기본 지연
    
    executions = await db.field_executions.find(
        {"execution_id": {"$in": execution_ids}},
        {"_id": 0}
    ).to_list(100)
    
    if not executions:
        return {"success": False, "error": "집행 기록을 찾을 수 없습니다"}
    
    alignment_results = []
    reference_time = None
    
    for exec in executions:
        exec_time = exec.get("projected_at", datetime.now(timezone.utc).isoformat())
        if isinstance(exec_time, str):
            exec_time = datetime.fromisoformat(exec_time.replace('Z', '+00:00'))
        
        if reference_time is None:
            reference_time = exec_time
        
        # 위상차 계산 (시간 차이를 위상으로 변환)
        time_delta = (exec_time - reference_time).total_seconds() * 1000  # ms
        phase_difference = (time_delta / NETWORK_LATENCY_BASE) * 2 * math.pi  # 라디안
        
        # 동기화 보정값
        sync_correction = -time_delta  # 역방향 보정
        
        alignment_results.append({
            "execution_id": exec["execution_id"],
            "original_time": exec_time.isoformat(),
            "time_delta_ms": round(time_delta, 4),
            "phase_difference_rad": round(phase_difference, 6),
            "sync_correction_ms": round(sync_correction, 4),
            "aligned": abs(time_delta) < NETWORK_LATENCY_BASE
        })
    
    return {
        "success": True,
        "reference_time": reference_time.isoformat() if reference_time else None,
        "signal_propagation_speed": SIGNAL_PROPAGATION_SPEED,
        "alignment_results": alignment_results,
        "all_aligned": all(r["aligned"] for r in alignment_results)
    }

# ==================== D:LEDGER 데이터 동기화 인터페이스 ====================

@router.post("/sync-to-ledger")
async def sync_to_ledger(execution_id: str):
    """
    집행 완료된 물리적 결과값을 비가역적 증명 데이터로 변환하여
    기록 노드(D:LEDGER)로 전송
    """
    from server import db
    
    # 집행 결과 조회
    execution = await db.field_executions.find_one(
        {"execution_id": execution_id},
        {"_id": 0}
    )
    
    if not execution:
        raise HTTPException(status_code=404, detail="집행 기록을 찾을 수 없습니다")
    
    # 비가역적 증명 해시 생성
    proof_data = {
        "execution_id": execution_id,
        "projection_results": execution.get("projection_results", []),
        "total_entropy_cost": execution.get("total_entropy_cost", 0),
        "timestamp": execution.get("projected_at", datetime.now(timezone.utc).isoformat())
    }
    
    proof_string = str(proof_data)
    proof_hash = hashlib.sha256(proof_string.encode()).hexdigest()
    
    # D:LEDGER에 기록 (ledger 컬렉션 사용)
    ledger_record = {
        "record_type": "physical_execution_proof",
        "execution_id": execution_id,
        "proof_hash": proof_hash,
        "proof_data": proof_data,
        "source": "F:FIELD",
        "destination": "D:LEDGER",
        "is_irreversible": True,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }
    
    # D:LEDGER의 record API 호출 (내부)
    from patents.d_ledger import record_transaction, Transaction
    
    tx = Transaction(
        transaction_type="physical_execution",
        from_account="F:FIELD",
        to_account="D:LEDGER",
        amount=execution.get("total_entropy_cost", 0),
        asset_id=execution_id,
        metadata={"proof_hash": proof_hash}
    )
    
    ledger_result = await record_transaction(tx)
    
    # 증명 기록 저장
    await db.execution_proofs.insert_one(ledger_record)
    
    # 집행 상태 업데이트
    await db.field_executions.update_one(
        {"execution_id": execution_id},
        {"$set": {
            "status": "synced_to_ledger",
            "proof_hash": proof_hash,
            "ledger_transaction_id": ledger_result.get("transaction_id"),
            "synced_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "execution_id": execution_id,
        "proof_hash": proof_hash,
        "ledger_transaction_id": ledger_result.get("transaction_id"),
        "is_irreversible": True,
        "synced_to": "D:LEDGER"
    }

# ==================== I:INTEGRITY 무결성 검증 연동 ====================

@router.post("/verify-with-integrity/{execution_id}")
async def verify_with_integrity(execution_id: str):
    """
    물리적 집행 내역을 증명 노드(I:INTEGRITY)의 유효성 검증 알고리즘과 1:1 대응
    """
    from server import db
    
    # 집행 기록 조회
    execution = await db.field_executions.find_one(
        {"execution_id": execution_id},
        {"_id": 0}
    )
    
    if not execution:
        raise HTTPException(status_code=404, detail="집행 기록을 찾을 수 없습니다")
    
    # 증명 기록 조회
    proof = await db.execution_proofs.find_one(
        {"execution_id": execution_id},
        {"_id": 0}
    )
    
    # I:INTEGRITY 검증 호출
    from patents.i_integrity import create_audit_log, AuditLog
    
    # 감사 로그 생성
    audit = AuditLog(
        action="physical_execution_verification",
        entity_type="field_execution",
        entity_id=execution_id,
        user_id="F:FIELD_SYSTEM",
        details={
            "proof_hash": proof.get("proof_hash") if proof else None,
            "total_entropy_cost": execution.get("total_entropy_cost"),
            "projection_results_count": len(execution.get("projection_results", []))
        }
    )
    
    audit_result = await create_audit_log(audit)
    
    # 해시 검증
    if proof:
        proof_data = proof.get("proof_data", {})
        proof_string = str(proof_data)
        recalculated_hash = hashlib.sha256(proof_string.encode()).hexdigest()
        hash_valid = recalculated_hash == proof.get("proof_hash")
    else:
        hash_valid = False
        recalculated_hash = None
    
    verification_result = {
        "execution_id": execution_id,
        "verification_status": "valid" if hash_valid else "invalid",
        "hash_verification": {
            "original_hash": proof.get("proof_hash") if proof else None,
            "recalculated_hash": recalculated_hash,
            "match": hash_valid
        },
        "audit_id": audit_result.get("audit_id"),
        "integrity_node": "I:INTEGRITY",
        "verified_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 검증 결과 저장
    await db.integrity_verifications.insert_one({
        **verification_result,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"success": True, "verification": verification_result}

# ==================== 마켓플레이스 (기존 기능 유지) ====================

class SaleRegistration(BaseModel):
    """판매 등록 요청"""
    module_id: str
    price: float
    title: str
    description: str = ""
    tags: List[str] = []

@router.post("/register")
async def register_for_sale(request: SaleRegistration):
    """모듈 판매 등록"""
    from server import db
    
    module = await db.asset_modules.find_one({"module_id": request.module_id}, {"_id": 0})
    
    if not module:
        raise HTTPException(status_code=404, detail="모듈을 찾을 수 없습니다")
    
    sale_listing = {
        "listing_id": f"LIST_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "module_id": request.module_id,
        "title": request.title,
        "description": request.description,
        "price": request.price,
        "tags": request.tags,
        "status": "active",
        "views": 0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.marketplace_listings.insert_one(sale_listing)
    
    await db.asset_modules.update_one(
        {"module_id": request.module_id},
        {"$set": {"status": "on_sale", "listing_id": sale_listing["listing_id"]}}
    )
    
    return {
        "success": True,
        "listing_id": sale_listing["listing_id"],
        "message": "판매 등록 완료"
    }

@router.get("/marketplace")
async def browse_marketplace(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: str = "created_at",
    order: str = "desc",
    limit: int = 20,
    offset: int = 0
):
    """마켓플레이스 브라우징"""
    from server import db
    
    query = {"status": "active"}
    
    if category:
        query["category"] = category
    if min_price is not None:
        query["price"] = {"$gte": min_price}
    if max_price is not None:
        query.setdefault("price", {})["$lte"] = max_price
    
    sort_order = -1 if order == "desc" else 1
    
    listings = await db.marketplace_listings.find(
        query,
        {"_id": 0}
    ).sort(sort_by, sort_order).skip(offset).limit(limit).to_list(limit)
    
    total = await db.marketplace_listings.count_documents(query)
    
    return {
        "success": True,
        "listings": listings,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/stats")
async def get_field_stats():
    """F:FIELD 통합 통계"""
    from server import db
    
    # 마켓플레이스 통계
    total_listings = await db.marketplace_listings.count_documents({"status": "active"})
    total_sales = await db.module_sales.count_documents({})
    
    # 물리 계층 통계
    total_nodes = await db.physical_nodes.count_documents({})
    active_nodes = await db.physical_nodes.count_documents({"is_active": True})
    total_executions = await db.field_executions.count_documents({})
    
    # 엔트로피 상태
    entropy_status = await get_entropy_status()
    
    return {
        "success": True,
        "stats": {
            "marketplace": {
                "total_listings": total_listings,
                "total_sales": total_sales
            },
            "physical_layer": {
                "total_nodes": total_nodes,
                "active_nodes": active_nodes,
                "total_executions": total_executions,
                "current_entropy": entropy_status["entropy_status"]["current_entropy"]
            },
            "system_health": "normal" if entropy_status["entropy_status"]["status"] == "normal" else "warning"
        }
    }
