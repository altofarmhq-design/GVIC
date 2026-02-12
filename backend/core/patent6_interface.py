"""특허 6: 도메인 인터페이스
외부 시스템과의 인터페이스
"""
from typing import Dict, List, Any
from datetime import datetime
import json

class DomainInterface:
    """도메인 인터페이스 클래스"""
    
    def __init__(self):
        self.connections: Dict[str, Dict] = {}
        self.history: List[Dict] = []
        self.error_count = 0
    
    def process(self, data: Any, source_type: str = "auto") -> Dict:
        """입력 데이터 처리"""
        processed = self._normalize_input(data)
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'source_type': source_type,
            'input_type': type(data).__name__,
            'success': processed is not None,
            'output': processed
        }
        
        self.history.append(record)
        
        return processed if processed else {'error': 'Processing failed'}
    
    def _normalize_input(self, data: Any) -> Dict:
        """입력 정규화"""
        try:
            if isinstance(data, dict):
                return data
            elif isinstance(data, str):
                try:
                    return json.loads(data)
                except:
                    return {'value': data, 'type': 'string'}
            elif isinstance(data, (int, float)):
                return {'value': float(data), 'type': 'numeric'}
            elif isinstance(data, list):
                return {'values': data, 'type': 'array'}
            else:
                return {'value': str(data), 'type': 'unknown'}
        except Exception as e:
            self.error_count += 1
            return None
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.history)
        success = sum(1 for h in self.history if h['success'])
        
        return {
            'total_processed': total,
            'success_count': success,
            'error_count': self.error_count,
            'success_rate': success / total if total > 0 else 0
        }
