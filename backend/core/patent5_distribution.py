"""특허 5: 가중 분배 모듈
자산 가치의 가중 분배
"""
from typing import Dict, List
from datetime import datetime
import numpy as np

class WeightedDistributor:
    """가중 분배 클래스"""
    
    def __init__(self, base_ratio: List[float] = None):
        self.base_ratio = base_ratio or [0.33, 0.34, 0.33]
        self.current_ratio = self.base_ratio.copy()
        self.history: List[Dict] = []
        self.total_distributed = 0.0
    
    def distribute(self, total_value: float) -> Dict:
        """가치 분배"""
        distribution = {
            'public': total_value * self.current_ratio[0],
            'productive': total_value * self.current_ratio[1],
            'individual': total_value * self.current_ratio[2]
        }
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'input_value': total_value,
            'ratio_used': self.current_ratio.copy(),
            'distribution': distribution,
            'total': sum(distribution.values())
        }
        
        self.history.append(record)
        self.total_distributed += total_value
        
        return distribution
    
    def update_ratio(self, new_ratio: List[float]):
        """분배 비율 업데이트"""
        if len(new_ratio) != 3:
            raise ValueError("비율은 3개 요소가 필요합니다")
        
        total = sum(new_ratio)
        if not np.isclose(total, 1.0, atol=0.01):
            new_ratio = [r / total for r in new_ratio]
        
        self.current_ratio = new_ratio
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        if not self.history:
            return {'count': 0, 'total_distributed': 0}
        
        public_total = sum(h['distribution']['public'] for h in self.history)
        productive_total = sum(h['distribution']['productive'] for h in self.history)
        individual_total = sum(h['distribution']['individual'] for h in self.history)
        
        return {
            'count': len(self.history),
            'total_distributed': self.total_distributed,
            'public_total': public_total,
            'productive_total': productive_total,
            'individual_total': individual_total,
            'current_ratio': self.current_ratio
        }
