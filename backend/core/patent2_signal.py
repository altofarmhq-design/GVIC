"""
특허 2: 신호 자산화 모듈
입력 신호를 자산으로 변환
"""
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

class SignalType(Enum):
    MONETARY = "monetary"
    DATA = "data"
    SERVICE = "service"
    RESOURCE = "resource"
    UNKNOWN = "unknown"

@dataclass
class Asset:
    """자산 클래스"""
    id: str
    signal_type: SignalType
    value: float
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "signal_type": self.signal_type.value,
            "value": self.value,
            "metadata": self.metadata,
            "created_at": self.created_at
        }

class SignalAssetizer:
    """신호 자산화기"""
    
    def __init__(self, sigma: List[float] = [0.5, 0.3, 0.2]):
        self.sigma = np.array(sigma)
        self.assets: List[Asset] = []
        self.processing_count = 0
    
    def detect_signal_type(self, value: Any) -> SignalType:
        """신호 유형 감지"""
        if isinstance(value, (int, float)):
            if 0 <= value <= 1:
                return SignalType.DATA
            return SignalType.MONETARY
        elif isinstance(value, str):
            return SignalType.SERVICE
        elif isinstance(value, dict):
            return SignalType.RESOURCE
        return SignalType.UNKNOWN
    
    def process_signal(self, 
                       signal: Any, 
                       signal_type: SignalType = None) -> Dict:
        """신호 처리 및 자산화"""
        self.processing_count += 1
        
        if signal_type is None:
            signal_type = self.detect_signal_type(signal)
        
        # 값 정규화
        if isinstance(signal, (int, float)):
            normalized_value = float(signal)
            if normalized_value > 1:
                normalized_value = min(1.0, normalized_value / 100)  # 퍼센트로 가정
        else:
            normalized_value = 0.5  # 기본값
        
        # 자산 생성
        asset = Asset(
            id=f"AST-{uuid.uuid4().hex[:8].upper()}",
            signal_type=signal_type,
            value=normalized_value,
            metadata={
                "original_signal": str(signal)[:100],
                "sigma_applied": self.sigma.tolist()
            }
        )
        
        self.assets.append(asset)
        
        return {
            "status": "success",
            "asset": asset.to_dict(),
            "signal_type": signal_type.value
        }
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """자산 조회"""
        for asset in self.assets:
            if asset.id == asset_id:
                return asset
        return None
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        if not self.assets:
            return {"total": 0, "by_type": {}}
        
        by_type = {}
        for asset in self.assets:
            t = asset.signal_type.value
            by_type[t] = by_type.get(t, 0) + 1
        
        values = [a.value for a in self.assets]
        return {
            "total": len(self.assets),
            "by_type": by_type,
            "avg_value": sum(values) / len(values),
            "processing_count": self.processing_count
        }
