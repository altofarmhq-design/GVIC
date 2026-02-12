"""특허 4: 비적합 처리 모듈
비적합 데이터 감지 및 처리
"""
from typing import Dict, List, Any, Tuple
from datetime import datetime
import numpy as np

class NonconformHandler:
    """비적합 데이터 처리 클래스"""
    
    def __init__(self, threshold: float = 0.1):
        self.threshold = threshold
        self.history: List[Dict] = []
        self.nonconform_count = 0
    
    def process(self, value: float, bounds: Tuple[float, float] = (0, 1)) -> Dict:
        """비적합 데이터 처리"""
        lower, upper = bounds
        original = value
        is_nonconform = False
        adjustment = 0.0
        
        if value < lower:
            is_nonconform = True
            adjustment = lower - value
            value = lower
        elif value > upper:
            is_nonconform = True
            adjustment = value - upper
            value = upper
        
        if is_nonconform:
            self.nonconform_count += 1
        
        result = {
            'original': original,
            'processed': value,
            'is_nonconform': is_nonconform,
            'adjustment': adjustment,
            'bounds': bounds,
            'timestamp': datetime.now().isoformat()
        }
        
        self.history.append(result)
        return result
    
    def batch_process(self, values: List[float], bounds: Tuple[float, float] = (0, 1)) -> List[Dict]:
        """배치 처리"""
        return [self.process(v, bounds) for v in values]
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.history)
        nonconform = self.nonconform_count
        
        adjustments = [h['adjustment'] for h in self.history if h['is_nonconform']]
        
        return {
            'total_processed': total,
            'nonconform_count': nonconform,
            'nonconform_rate': nonconform / total if total > 0 else 0,
            'average_adjustment': np.mean(adjustments) if adjustments else 0,
            'max_adjustment': max(adjustments) if adjustments else 0
        }
