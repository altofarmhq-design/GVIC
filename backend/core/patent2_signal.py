"""특허 2: 신호 자산화 모듈
신호를 자산 가치로 변환
"""
from typing import Dict, List, Any
from datetime import datetime
import numpy as np

class SignalAssetizer:
    """신호를 자산으로 변환하는 클래스"""
    
    def __init__(self, sigma: List[float] = None):
        self.sigma = sigma or [0.33, 0.34, 0.33]
        self.assets: List[Dict] = []
        self.total_value = 0.0
    
    def process_signal(self, signal_value: float) -> Dict:
        """신호를 자산 가치로 변환"""
        # 신호 정규화 및 자산화
        normalized = min(max(signal_value, 0), 1) if signal_value <= 1 else signal_value / 10
        
        asset = {
            'id': len(self.assets) + 1,
            'timestamp': datetime.now().isoformat(),
            'signal': signal_value,
            'value': normalized,
            'multiplier': 1.0 + (normalized * 0.1),
            'quality_score': self._calculate_quality(signal_value)
        }
        
        self.assets.append(asset)
        self.total_value += normalized
        
        return asset
    
    def _calculate_quality(self, signal: float) -> float:
        """품질 점수 계산"""
        if signal <= 0:
            return 0.0
        elif signal <= 0.5:
            return signal * 1.5
        elif signal <= 1.0:
            return 0.75 + (signal - 0.5) * 0.5
        else:
            return min(1.0, 0.9 + (signal - 1) * 0.01)
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        if not self.assets:
            return {'count': 0, 'total_value': 0, 'average': 0}
        
        values = [a['value'] for a in self.assets]
        return {
            'count': len(self.assets),
            'total_value': self.total_value,
            'average': np.mean(values),
            'max': max(values),
            'min': min(values)
        }
