"""
특허 6: 도메인 인터페이스 모듈
다양한 입력 소스 처리
"""
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

class SourceType(Enum):
    JSON = "json"
    TEXT = "text"
    NUMERIC = "numeric"
    BINARY = "binary"
    UNKNOWN = "unknown"

@dataclass
class InterfaceResult:
    """인터페이스 처리 결과"""
    source_type: SourceType
    data: Any
    metadata: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "source_type": self.source_type.value,
            "data": self.data,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }

class DomainInterface:
    """도메인 인터페이스"""
    
    def __init__(self):
        self.processing_history: List[InterfaceResult] = []
        self.source_counts: Dict[str, int] = {}
    
    def detect_source_type(self, data: Any) -> SourceType:
        """소스 유형 감지"""
        if isinstance(data, (int, float)):
            return SourceType.NUMERIC
        
        if isinstance(data, bytes):
            return SourceType.BINARY
        
        if isinstance(data, dict):
            return SourceType.JSON
        
        if isinstance(data, str):
            # JSON 문자열 확인
            try:
                json.loads(data)
                return SourceType.JSON
            except:
                pass
            
            # 숫자 문자열 확인
            if re.match(r'^-?\d+\.?\d*$', data.strip()):
                return SourceType.NUMERIC
            
            return SourceType.TEXT
        
        return SourceType.UNKNOWN
    
    def process(self, data: Any, source_type: SourceType = None) -> Dict:
        """입력 처리"""
        if source_type is None:
            source_type = self.detect_source_type(data)
        
        try:
            if source_type == SourceType.JSON:
                if isinstance(data, str):
                    processed = json.loads(data)
                else:
                    processed = data
            
            elif source_type == SourceType.NUMERIC:
                if isinstance(data, str):
                    processed = float(data)
                else:
                    processed = data
            
            elif source_type == SourceType.TEXT:
                processed = {"text": str(data), "length": len(str(data))}
            
            elif source_type == SourceType.BINARY:
                processed = {"size": len(data), "type": "binary"}
            
            else:
                processed = data
            
            result = InterfaceResult(
                source_type=source_type,
                data=processed,
                metadata={"original_type": type(data).__name__}
            )
            
            self.processing_history.append(result)
            self.source_counts[source_type.value] = self.source_counts.get(source_type.value, 0) + 1
            
            return {"status": "success", "data": processed, "source_type": source_type.value}
            
        except Exception as e:
            return {"status": "error", "error": str(e), "source_type": source_type.value}
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        return {
            "total_processed": len(self.processing_history),
            "by_source_type": self.source_counts
        }
