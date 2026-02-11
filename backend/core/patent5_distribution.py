"""
특허 5: 가중 분배 모듈
자산을 공공/생산/개인 영역으로 분배
"""
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

class DistributionTarget(Enum):
    PUBLIC = "public"          # 공공
    PRODUCTIVE = "productive"  # 생산
    INDIVIDUAL = "individual"  # 개인

@dataclass
class DistributionAllocation:
    """분배 할당"""
    target: DistributionTarget
    amount: float
    ratio: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "target": self.target.value,
            "amount": self.amount,
            "ratio": self.ratio,
            "timestamp": self.timestamp
        }

class WeightedDistributor:
    """가중 분배기"""
    
    def __init__(self, base_ratio: List[float] = [0.5, 0.3, 0.2]):
        self.base_ratio = np.array(base_ratio)
        self.current_ratio = self.base_ratio.copy()
        self.distribution_history: List[Dict] = []
        self.total_distributed = 0.0
    
    def distribute(self, 
                   total_amount: float, 
                   custom_ratio: List[float] = None) -> Dict[str, DistributionAllocation]:
        """분배 실행"""
        ratio = np.array(custom_ratio) if custom_ratio else self.current_ratio
        
        # 비율 정규화
        if np.sum(ratio) > 0:
            ratio = ratio / np.sum(ratio)
        else:
            ratio = self.base_ratio
        
        amounts = ratio * total_amount
        
        allocations = {
            "public": DistributionAllocation(
                target=DistributionTarget.PUBLIC,
                amount=float(amounts[0]),
                ratio=float(ratio[0])
            ),
            "productive": DistributionAllocation(
                target=DistributionTarget.PRODUCTIVE,
                amount=float(amounts[1]),
                ratio=float(ratio[1])
            ),
            "individual": DistributionAllocation(
                target=DistributionTarget.INDIVIDUAL,
                amount=float(amounts[2]),
                ratio=float(ratio[2])
            )
        }
        
        self.total_distributed += total_amount
        self.distribution_history.append({
            "total": total_amount,
            "allocations": {k: v.to_dict() for k, v in allocations.items()},
            "timestamp": datetime.now().isoformat()
        })
        
        return allocations
    
    def adjust_ratio(self, target: DistributionTarget, delta: float):
        """비율 조정"""
        idx = {DistributionTarget.PUBLIC: 0, 
               DistributionTarget.PRODUCTIVE: 1, 
               DistributionTarget.INDIVIDUAL: 2}[target]
        
        self.current_ratio[idx] += delta
        self.current_ratio = np.maximum(self.current_ratio, 0)  # 음수 방지
        
        # 재정규화
        if np.sum(self.current_ratio) > 0:
            self.current_ratio = self.current_ratio / np.sum(self.current_ratio)
    
    def reset_ratio(self):
        """비율 초기화"""
        self.current_ratio = self.base_ratio.copy()
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        if not self.distribution_history:
            return {
                "total_distributed": 0,
                "distribution_count": 0,
                "current_ratio": self.current_ratio.tolist()
            }
        
        return {
            "total_distributed": self.total_distributed,
            "distribution_count": len(self.distribution_history),
            "current_ratio": self.current_ratio.tolist(),
            "base_ratio": self.base_ratio.tolist(),
            "avg_per_distribution": self.total_distributed / len(self.distribution_history)
        }
