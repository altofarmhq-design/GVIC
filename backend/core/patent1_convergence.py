"""
특허 1: 수렴 제어 모듈
비율 조정 및 수렴 제어
"""
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OmegaConstraints:
    """Ω 제약조건"""
    lower_bounds: np.ndarray  # 하한
    upper_bounds: np.ndarray  # 상한
    sum_constraint: float = 1.0  # 합계 제약
    
    def is_valid(self, V: np.ndarray) -> bool:
        """제약조건 검증"""
        if len(V) != len(self.lower_bounds):
            return False
        if not np.allclose(np.sum(V), self.sum_constraint, atol=0.01):
            return False
        if np.any(V < self.lower_bounds - 0.001):
            return False
        if np.any(V > self.upper_bounds + 0.001):
            return False
        return True

class ConvergenceController:
    """수렴 제어기"""
    
    def __init__(self, 
                 default_ratio: List[float] = [0.5, 0.3, 0.2],
                 omega: Dict = None):
        self.R = np.array(default_ratio)  # 기본 비율 Σ
        
        omega = omega or {}
        self.omega = OmegaConstraints(
            lower_bounds=np.array([omega.get('V_pub_min', 0.2), 0.0, 0.0]),
            upper_bounds=np.array([omega.get('V_pub_max', 0.8), 1.0, omega.get('V_ind_max', 0.5)]),
            sum_constraint=omega.get('sum_constraint', 1.0)
        )
        
        self.convergence_history: List[Dict] = []
        self.violation_count = 0
    
    def converge(self, V_in: np.ndarray, max_iterations: int = 100) -> Tuple[np.ndarray, Dict]:
        """수렴 실행"""
        V = V_in.copy()
        transformed = False
        iterations = 0
        
        # 정규화
        if np.sum(V) > 0:
            V = V / np.sum(V) * self.omega.sum_constraint
        else:
            V = self.R.copy()
        
        # 제약조건 적용
        for i in range(max_iterations):
            iterations = i + 1
            
            # 하한 적용
            V = np.maximum(V, self.omega.lower_bounds)
            # 상한 적용  
            V = np.minimum(V, self.omega.upper_bounds)
            
            # 재정규화
            if np.sum(V) > 0:
                V = V / np.sum(V) * self.omega.sum_constraint
            
            if self.omega.is_valid(V):
                break
            transformed = True
        
        is_valid = self.omega.is_valid(V)
        if not is_valid:
            self.violation_count += 1
            V = self.R.copy()  # 기본값으로 폴백
        
        metadata = {
            "status": "valid" if is_valid else "fallback",
            "iterations": iterations,
            "transformed": transformed,
            "violation_count": self.violation_count
        }
        
        self.convergence_history.append({
            "input": V_in.tolist(),
            "output": V.tolist(),
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        })
        
        return V, metadata
    
    def calculate_balance_index(self, V: np.ndarray) -> float:
        """균형 지수 계산"""
        if len(V) != len(self.R):
            return 0.0
        deviation = np.sum(np.abs(V - self.R))
        return max(0, 1 - deviation)
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        if not self.convergence_history:
            return {"total": 0, "valid": 0, "violations": 0}
        
        valid = sum(1 for h in self.convergence_history if h["metadata"]["status"] == "valid")
        return {
            "total": len(self.convergence_history),
            "valid": valid,
            "violations": self.violation_count,
            "valid_rate": valid / len(self.convergence_history)
        }
