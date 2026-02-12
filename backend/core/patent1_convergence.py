"""특허 1: 수렴 제어 모듈
비율 조정 및 수렴 제어
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any
from datetime import datetime

@dataclass
class OmegaConstraints:
    """오메가 경계 조건 정의"""
    lower_bounds: np.ndarray = field(default_factory=lambda: np.array([0.2, 0.2, 0.1]))
    upper_bounds: np.ndarray = field(default_factory=lambda: np.array([0.5, 0.5, 0.5]))
    sum_constraint: float = 1.0
    
    def is_valid(self, V: np.ndarray) -> bool:
        """V가 경계 조건을 만족하는지 확인"""
        if not np.allclose(V.sum(), self.sum_constraint, atol=0.01):
            return False
        if np.any(V < self.lower_bounds - 0.001):
            return False
        if np.any(V > self.upper_bounds + 0.001):
            return False
        return True

class ConvergenceController:
    """수렴 제어 컨트롤러"""
    
    def __init__(self, default_ratio: List[float] = None, omega: Dict = None):
        self.R = np.array(default_ratio or [0.33, 0.34, 0.33])
        
        omega = omega or {}
        self.omega = OmegaConstraints(
            lower_bounds=np.array(omega.get('lower_bounds', [0.2, 0.2, 0.1])),
            upper_bounds=np.array(omega.get('upper_bounds', [0.5, 0.5, 0.5])),
            sum_constraint=omega.get('sum_constraint', 1.0)
        )
        
        self.convergence_history: List[Dict] = []
        self.violation_count = 0
    
    def converge(self, V_in: np.ndarray, max_iterations: int = 100) -> Tuple[np.ndarray, Dict]:
        """V_in을 omega 조건에 맞게 수렴"""
        V = V_in.copy() if V_in.sum() > 0 else self.R.copy()
        
        # 초기 정규화
        if V.sum() > 0:
            V = V / V.sum() * self.omega.sum_constraint
        
        transformed = False
        iterations = 0
        
        for i in range(max_iterations):
            iterations = i + 1
            old_V = V.copy()
            
            # 하한 적용
            V = np.maximum(V, self.omega.lower_bounds)
            
            # 상한 적용
            V = np.minimum(V, self.omega.upper_bounds)
            
            # 재정규화
            if V.sum() > 0:
                V = V / V.sum() * self.omega.sum_constraint
            
            if not np.allclose(old_V, V):
                transformed = True
            
            if self.omega.is_valid(V):
                break
        
        # 수렴 실패시 기본값 사용
        if not self.omega.is_valid(V):
            self.violation_count += 1
            V = self.R.copy()
        
        metadata = {
            'status': 'converged' if self.omega.is_valid(V) else 'fallback',
            'iterations': iterations,
            'transformed': transformed,
            'violation_count': self.violation_count
        }
        
        self.convergence_history.append({
            'timestamp': datetime.now().isoformat(),
            'input': V_in.tolist(),
            'output': V.tolist(),
            'metadata': metadata
        })
        
        return V, metadata
    
    def calculate_balance_index(self, V: np.ndarray = None) -> float:
        """균형 지수 계산 (0~1)"""
        if V is None:
            V = self.R
        
        if len(V) != len(self.R):
            return 0.0
        
        deviation = np.abs(V - self.R).sum()
        balance = max(0, 1 - deviation)
        return float(balance)
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.convergence_history)
        valid = sum(1 for h in self.convergence_history if h['metadata']['status'] == 'converged')
        
        return {
            'total_operations': total,
            'valid_count': valid,
            'valid_rate': valid / total if total > 0 else 0,
            'violation_count': self.violation_count
        }
