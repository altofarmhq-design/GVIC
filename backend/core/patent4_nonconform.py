"""
특허 4: 비적합 데이터 처리 모듈
범위를 벗어난 데이터 정규화
"""
import numpy as np
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class NonconformType(Enum):
    OVERFLOW = "overflow"      # 상한 초과
    UNDERFLOW = "underflow"    # 하한 미달
    INVALID = "invalid"        # 유효하지 않음
    NORMAL = "normal"          # 정상

@dataclass
class NonconformResult:
    """비적합 처리 결과"""
    original: Any
    processed: Any
    nonconform_type: NonconformType
    adjustment: float
    timestamp: str
    
    def to_dict(self) -> Dict:
        return {
            "original": self.original,
            "processed": self.processed,
            "type": self.nonconform_type.value,
            "adjustment": self.adjustment,
            "timestamp": self.timestamp
        }

class NonconformHandler:
    """비적합 데이터 핸들러"""
    
    def __init__(self, 
                 lower_bound: float = 0.0, 
                 upper_bound: float = 1.0,
                 clamp: bool = True):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.clamp = clamp
        self.processing_history: list = []
        self.overflow_count = 0
        self.underflow_count = 0
        self.invalid_count = 0
    
    def detect_nonconform(self, value: Any) -> Tuple[NonconformType, float]:
        """비적합 감지"""
        if not isinstance(value, (int, float)):
            return NonconformType.INVALID, 0.0
        
        if np.isnan(value) or np.isinf(value):
            return NonconformType.INVALID, 0.0
        
        if value > self.upper_bound:
            return NonconformType.OVERFLOW, value - self.upper_bound
        
        if value < self.lower_bound:
            return NonconformType.UNDERFLOW, self.lower_bound - value
        
        return NonconformType.NORMAL, 0.0
    
    def process(self, value: Any) -> Dict:
        """비적합 처리"""
        nc_type, adjustment = self.detect_nonconform(value)
        
        if nc_type == NonconformType.NORMAL:
            processed = value
        elif nc_type == NonconformType.OVERFLOW:
            self.overflow_count += 1
            processed = self.upper_bound if self.clamp else value
        elif nc_type == NonconformType.UNDERFLOW:
            self.underflow_count += 1
            processed = self.lower_bound if self.clamp else value
        else:  # INVALID
            self.invalid_count += 1
            processed = (self.lower_bound + self.upper_bound) / 2  # 중간값
        
        result = NonconformResult(
            original=value,
            processed=processed,
            nonconform_type=nc_type,
            adjustment=adjustment,
            timestamp=datetime.now().isoformat()
        )
        
        self.processing_history.append(result.to_dict())
        
        return {
            "status": nc_type.value,
            "original": value,
            "processed": processed,
            "adjustment": adjustment
        }
    
    def process_array(self, values: np.ndarray) -> np.ndarray:
        """배열 처리"""
        result = np.zeros_like(values, dtype=float)
        for i, v in enumerate(values):
            proc_result = self.process(v)
            result[i] = proc_result["processed"]
        return result
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        total = len(self.processing_history)
        return {
            "total_processed": total,
            "overflow_count": self.overflow_count,
            "underflow_count": self.underflow_count,
            "invalid_count": self.invalid_count,
            "normal_count": total - self.overflow_count - self.underflow_count - self.invalid_count,
            "bounds": {
                "lower": self.lower_bound,
                "upper": self.upper_bound
            }
        }
