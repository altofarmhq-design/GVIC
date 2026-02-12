"""특허 1: 운영 경계 조건 기반의 전역 수렴 제어 시스템
Global Convergence Control System Based on Operational Boundary Constraints

시스템 구성:
- 110: 파라미터 수집부 (벡터 변환)
- 120: 경계 검증부 (OBC 만족 여부)
- 130: 수렴 연산부 (위반 시 정규화)
- 140: 동기화 버스 (하위 노드 전파)
- 150: 복구 제어부 (3단계 점진적 복구)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, timezone
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RecoveryStage(Enum):
    """복구 단계"""
    NORMAL = "normal"
    SOFT_RECOVERY = "soft_recovery"      # 1단계
    FORCE_SYNC = "force_sync"            # 2단계
    FULL_RESET = "full_reset"            # 3단계


class AnomalyLevel(Enum):
    """이상 수준"""
    NORMAL = "normal"
    WARNING = "warning"      # θ_warning = 0.1
    CRITICAL = "critical"    # θ_critical = 0.2


@dataclass
class OmegaConstraints:
    """운영 경계 조건 (Ω) - [수학식 1]
    
    Ω = {
        L₁ ≤ P₁ ≤ U₁  (제1영역)
        L₂ ≤ P₂ ≤ U₂  (제2영역)  
        L₃ ≤ P₃ ≤ U₃  (제3영역)
        ΣPᵢ = 1.0     (정규화 조건)
    }
    """
    lower_bounds: np.ndarray = field(default_factory=lambda: np.array([0.2, 0.2, 0.1]))
    upper_bounds: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5, 0.5]))
    sum_constraint: float = 1.0
    
    def violation_score(self, P: np.ndarray) -> float:
        """[수학식 2] 경계 위반 판정 함수
        
        V(P) = Σᵢ max(0, Lᵢ - Pᵢ) + Σᵢ max(0, Pᵢ - Uᵢ) + |ΣPᵢ - 1.0|
        
        V(P) > 0: 경계 위반
        V(P) = 0: 경계 만족
        """
        lower_violation = np.sum(np.maximum(0, self.lower_bounds - P))
        upper_violation = np.sum(np.maximum(0, P - self.upper_bounds))
        sum_violation = abs(np.sum(P) - self.sum_constraint)
        
        return lower_violation + upper_violation + sum_violation
    
    def is_valid(self, P: np.ndarray) -> bool:
        """경계 조건 만족 여부"""
        return self.violation_score(P) < 0.001


@dataclass
class NodeState:
    """노드 상태"""
    node_id: str
    parameters: np.ndarray
    last_sync: str
    recovery_stage: RecoveryStage = RecoveryStage.NORMAL
    anomaly_level: AnomalyLevel = AnomalyLevel.NORMAL


class ParameterCollector:
    """110: 파라미터 수집부
    외부 입력을 벡터로 변환
    """
    
    def __init__(self, dimension: int = 3):
        self.dimension = dimension
        self.collection_history: List[Dict] = []
    
    def collect(self, input_data: Any) -> np.ndarray:
        """입력 데이터를 파라미터 벡터로 변환"""
        if isinstance(input_data, np.ndarray):
            vector = input_data
        elif isinstance(input_data, (list, tuple)):
            vector = np.array(input_data, dtype=float)
        elif isinstance(input_data, dict):
            # 딕셔너리에서 값 추출
            values = list(input_data.values())[:self.dimension]
            vector = np.array(values, dtype=float)
        elif isinstance(input_data, (int, float)):
            # 스칼라를 균등 분배
            vector = np.full(self.dimension, input_data / self.dimension)
        else:
            raise ValueError(f"Unsupported input type: {type(input_data)}")
        
        # 차원 맞추기
        if len(vector) < self.dimension:
            vector = np.pad(vector, (0, self.dimension - len(vector)))
        elif len(vector) > self.dimension:
            vector = vector[:self.dimension]
        
        # 정규화 (합 = 1.0)
        if vector.sum() > 0:
            vector = vector / vector.sum()
        else:
            vector = np.ones(self.dimension) / self.dimension
        
        self.collection_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input_type': type(input_data).__name__,
            'output_vector': vector.tolist()
        })
        
        return vector


class BoundaryValidator:
    """120: 경계 검증부
    OBC(운영 경계 조건) 만족 여부 검증
    """
    
    def __init__(self, omega: OmegaConstraints):
        self.omega = omega
        self.validation_history: List[Dict] = []
    
    def validate(self, P: np.ndarray) -> Tuple[bool, float, Dict]:
        """경계 조건 검증
        
        Returns:
            (is_valid, violation_score, details)
        """
        violation = self.omega.violation_score(P)
        is_valid = violation < 0.001
        
        details = {
            'lower_violations': np.maximum(0, self.omega.lower_bounds - P).tolist(),
            'upper_violations': np.maximum(0, P - self.omega.upper_bounds).tolist(),
            'sum_violation': abs(np.sum(P) - self.omega.sum_constraint),
            'total_violation': violation
        }
        
        self.validation_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input': P.tolist(),
            'is_valid': is_valid,
            'violation_score': violation,
            'details': details
        })
        
        return is_valid, violation, details


class ConvergenceCalculator:
    """130: 수렴 연산부
    위반 시 수렴 비율로 정규화
    """
    
    def __init__(self, default_ratio: np.ndarray, omega: OmegaConstraints, 
                 sensitivity: float = 2.0):
        self.R = default_ratio  # 기본 수렴 비율 벡터
        self.omega = omega
        self.beta = sensitivity  # 민감도 파라미터
        self.convergence_history: List[Dict] = []
    
    def calculate_alpha(self, violation: float) -> float:
        """[수학식 4] 수렴 강도 계수 산출
        
        α = max(0, 1 - β · V(P))
        """
        return max(0, 1 - self.beta * violation)
    
    def converge(self, V_in: np.ndarray, violation: float) -> Tuple[np.ndarray, Dict]:
        """[수학식 3] 수렴 변환 함수
        
        V_conv = F(V_in, α) = α · V_in + (1 - α) · R
        """
        alpha = self.calculate_alpha(violation)
        
        # 수렴 변환
        V_conv = alpha * V_in + (1 - alpha) * self.R
        
        # [수학식 5] 경계 조건 내 클램핑
        V_clamped = np.clip(V_conv, self.omega.lower_bounds, self.omega.upper_bounds)
        
        # 정규화
        if V_clamped.sum() > 0:
            V_final = V_clamped / V_clamped.sum() * self.omega.sum_constraint
        else:
            V_final = self.R.copy()
        
        metadata = {
            'alpha': alpha,
            'violation': violation,
            'transformed': not np.allclose(V_in, V_final),
            'clamped': not np.allclose(V_conv, V_clamped)
        }
        
        self.convergence_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input': V_in.tolist(),
            'output': V_final.tolist(),
            'metadata': metadata
        })
        
        return V_final, metadata
    
    def calculate_entropy_balance(self, P: np.ndarray) -> float:
        """[수학식 6] 엔트로피 기반 균형 지표
        
        H(P) = -Σᵢ Pᵢ · log(Pᵢ)
        H_max = log(n)
        균형 지수 B = H(P) / H_max
        """
        # 0 방지
        P_safe = np.clip(P, 1e-10, 1.0)
        P_normalized = P_safe / P_safe.sum()
        
        H = -np.sum(P_normalized * np.log(P_normalized))
        H_max = np.log(len(P))
        
        return float(H / H_max) if H_max > 0 else 0.0


class RecoveryController:
    """150: 복구 제어부
    이상 감지 시 3단계 점진적 복구
    """
    
    # 임계치 상수
    THETA_WARNING = 0.1
    THETA_CRITICAL = 0.2
    CASCADE_THRESHOLD_LOW = 0.3
    CASCADE_THRESHOLD_HIGH = 0.5
    
    def __init__(self, default_ratio: np.ndarray):
        self.R = default_ratio
        self.P_sync = default_ratio.copy()  # 동기화 기준 파라미터
        self.nodes: Dict[str, NodeState] = {}
        self.recovery_history: List[Dict] = []
    
    def register_node(self, node_id: str, initial_params: np.ndarray):
        """노드 등록"""
        self.nodes[node_id] = NodeState(
            node_id=node_id,
            parameters=initial_params.copy(),
            last_sync=datetime.now(timezone.utc).isoformat()
        )
    
    def calculate_deviation(self, node_params: np.ndarray) -> float:
        """편차 계산: D = ||P_sync - P_node||₂"""
        return float(np.linalg.norm(self.P_sync - node_params))
    
    def detect_anomaly(self, deviation: float) -> AnomalyLevel:
        """이상 감지"""
        if deviation >= self.THETA_CRITICAL:
            return AnomalyLevel.CRITICAL
        elif deviation >= self.THETA_WARNING:
            return AnomalyLevel.WARNING
        else:
            return AnomalyLevel.NORMAL
    
    def recover(self, node_id: str) -> Tuple[np.ndarray, RecoveryStage]:
        """3단계 점진적 복구 프로세스"""
        if node_id not in self.nodes:
            return self.R.copy(), RecoveryStage.FULL_RESET
        
        node = self.nodes[node_id]
        deviation = self.calculate_deviation(node.parameters)
        anomaly = self.detect_anomaly(deviation)
        
        if anomaly == AnomalyLevel.NORMAL:
            return node.parameters, RecoveryStage.NORMAL
        
        # 단계별 복구
        if node.recovery_stage == RecoveryStage.NORMAL:
            # 1단계: 소프트 복구
            P_new = 0.7 * node.parameters + 0.3 * self.P_sync
            new_stage = RecoveryStage.SOFT_RECOVERY
            
        elif node.recovery_stage == RecoveryStage.SOFT_RECOVERY:
            # 2단계: 강제 동기화
            P_new = self.P_sync.copy()
            new_stage = RecoveryStage.FORCE_SYNC
            
        else:
            # 3단계: 완전 초기화
            P_new = self.R.copy()
            new_stage = RecoveryStage.FULL_RESET
        
        # 상태 업데이트
        node.parameters = P_new
        node.recovery_stage = new_stage
        node.anomaly_level = anomaly
        node.last_sync = datetime.now(timezone.utc).isoformat()
        
        self.recovery_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'node_id': node_id,
            'deviation': deviation,
            'anomaly_level': anomaly.value,
            'recovery_stage': new_stage.value,
            'new_parameters': P_new.tolist()
        })
        
        return P_new, new_stage
    
    def check_cascade_anomaly(self) -> Tuple[str, Optional[str]]:
        """연쇄 이상 방지 체크
        
        Returns:
            (action, message)
        """
        if not self.nodes:
            return "normal", None
        
        anomaly_count = sum(
            1 for node in self.nodes.values() 
            if node.anomaly_level != AnomalyLevel.NORMAL
        )
        anomaly_rate = anomaly_count / len(self.nodes)
        
        if anomaly_rate > self.CASCADE_THRESHOLD_HIGH:
            # > 50%: 전역 비상 복구 모드
            return "global_reset", f"Critical: {anomaly_rate:.1%} nodes anomalous"
        elif anomaly_rate > self.CASCADE_THRESHOLD_LOW:
            # 30%~50%: 예방적 강화
            return "preventive", f"Warning: {anomaly_rate:.1%} nodes anomalous"
        else:
            # < 30%: 개별 복구
            return "individual", None


class ConvergenceController:
    """전역 수렴 제어 시스템 (통합)"""
    
    def __init__(self, default_ratio: List[float] = None, omega: Dict = None):
        # 기본 수렴 비율 (R)
        self.R = np.array(default_ratio or [0.33, 0.34, 0.33])
        
        # 운영 경계 조건 (Ω)
        omega = omega or {}
        self.omega = OmegaConstraints(
            lower_bounds=np.array(omega.get('lower_bounds', [0.2, 0.2, 0.1])),
            upper_bounds=np.array(omega.get('upper_bounds', [0.5, 0.5, 0.5])),
            sum_constraint=omega.get('sum_constraint', 1.0)
        )
        
        # 서브시스템 초기화
        self.collector = ParameterCollector(dimension=len(self.R))
        self.validator = BoundaryValidator(self.omega)
        self.calculator = ConvergenceCalculator(self.R, self.omega)
        self.recovery = RecoveryController(self.R)
        
        # 메인 노드 등록
        self.recovery.register_node("main", self.R)
        
        self.convergence_history: List[Dict] = []
        self.violation_count = 0
    
    def converge(self, V_in: np.ndarray, max_iterations: int = 100) -> Tuple[np.ndarray, Dict]:
        """메인 수렴 처리 함수"""
        # 입력 정규화
        V = V_in.copy() if V_in.sum() > 0 else self.R.copy()
        if V.sum() > 0:
            V = V / V.sum() * self.omega.sum_constraint
        
        # 경계 검증
        is_valid, violation, details = self.validator.validate(V)
        
        if is_valid:
            # 경계 만족 시 그대로 반환
            metadata = {
                'status': 'valid',
                'iterations': 0,
                'transformed': False,
                'violation_count': self.violation_count,
                'balance_index': self.calculator.calculate_entropy_balance(V)
            }
        else:
            # 수렴 변환 적용
            self.violation_count += 1
            V, conv_meta = self.calculator.converge(V, violation)
            
            # 반복 수렴 (필요시)
            iterations = 1
            while not self.omega.is_valid(V) and iterations < max_iterations:
                _, new_violation, _ = self.validator.validate(V)
                V, _ = self.calculator.converge(V, new_violation)
                iterations += 1
            
            # 수렴 실패시 기본값 사용
            if not self.omega.is_valid(V):
                V = self.R.copy()
            
            metadata = {
                'status': 'converged' if self.omega.is_valid(V) else 'fallback',
                'iterations': iterations,
                'transformed': conv_meta['transformed'],
                'violation_count': self.violation_count,
                'balance_index': self.calculator.calculate_entropy_balance(V)
            }
        
        self.convergence_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input': V_in.tolist(),
            'output': V.tolist(),
            'metadata': metadata
        })
        
        return V, metadata
    
    def calculate_balance_index(self, V: np.ndarray = None) -> float:
        """균형 지수 계산"""
        if V is None:
            V = self.R
        return self.calculator.calculate_entropy_balance(V)
    
    def update_sync_parameters(self, new_params: np.ndarray):
        """동기화 기준 파라미터 업데이트"""
        self.recovery.P_sync = new_params.copy()
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.convergence_history)
        valid = sum(
            1 for h in self.convergence_history 
            if h['metadata']['status'] in ['valid', 'converged']
        )
        
        return {
            'total_operations': total,
            'valid_count': valid,
            'valid_rate': valid / total if total > 0 else 1.0,
            'violation_count': self.violation_count,
            'recovery_stats': {
                'nodes': len(self.recovery.nodes),
                'recovery_events': len(self.recovery.recovery_history)
            }
        }
