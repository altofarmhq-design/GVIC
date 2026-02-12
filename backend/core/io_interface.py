"""입출력 인터페이스 모듈"""
from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime
import json

@dataclass
class ProcessedInput:
    """처리된 입력 데이터 클래스"""
    data: Any
    format: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

class InputProcessor:
    """입력 처리기"""
    
    def __init__(self):
        self.supported_formats = ['json', 'text', 'csv', 'numeric', 'key_value']
        self.history: List[ProcessedInput] = []
    
    def process(self, data: Any, format: str = 'auto') -> ProcessedInput:
        """입력 데이터 처리"""
        if format == 'auto':
            format = self._detect_format(data)
        
        processed_data = data
        
        if format == 'json':
            if isinstance(data, str):
                try:
                    processed_data = json.loads(data)
                except (json.JSONDecodeError, ValueError):
                    processed_data = {'raw': data}
            else:
                processed_data = data
        elif format == 'numeric':
            try:
                processed_data = float(data)
            except (ValueError, TypeError):
                processed_data = 0.0
        elif format == 'key_value':
            if isinstance(data, str):
                processed_data = self._parse_key_value(data)
            else:
                processed_data = data
        elif format == 'csv':
            if isinstance(data, str):
                processed_data = self._parse_csv(data)
            else:
                processed_data = data
        else:
            processed_data = str(data)
        
        result = ProcessedInput(
            data=processed_data,
            format=format
        )
        
        self.history.append(result)
        return result
    
    def _detect_format(self, data: Any) -> str:
        """입력 형식 자동 감지"""
        if isinstance(data, dict):
            return 'json'
        elif isinstance(data, (int, float)):
            return 'numeric'
        elif isinstance(data, str):
            # JSON 시도
            try:
                json.loads(data)
                return 'json'
            except (json.JSONDecodeError, ValueError):
                pass
            
            # key=value 형식 확인
            if '=' in data and '\n' in data:
                return 'key_value'
            
            # CSV 형식 확인
            if ',' in data and '\n' in data:
                return 'csv'
        
        return 'text'
    
    def _parse_key_value(self, data: str) -> Dict:
        """key=value 형식 파싱"""
        result = {}
        for line in data.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                try:
                    result[key.strip()] = float(value.strip())
                except (ValueError, TypeError):
                    result[key.strip()] = value.strip()
        return result
    
    def _parse_csv(self, data: str) -> List[Dict]:
        """CSV 형식 파싱"""
        lines = data.strip().split('\n')
        if len(lines) < 2:
            return [{'raw': data}]
        
        headers = [h.strip() for h in lines[0].split(',')]
        result = []
        
        for line in lines[1:]:
            values = [v.strip() for v in line.split(',')]
            row = {}
            for i, header in enumerate(headers):
                if i < len(values):
                    try:
                        row[header] = float(values[i])
                    except (ValueError, TypeError):
                        row[header] = values[i]
            result.append(row)
        
        return result

class OutputFormatter:
    """출력 포맷터"""
    
    def __init__(self, default_format: str = 'json'):
        self.default_format = default_format
    
    def format(self, data: Any, format: str = None) -> str:
        """데이터 포맷팅"""
        format = format or self.default_format
        
        if format == 'json':
            return json.dumps(data, ensure_ascii=False, default=str)
        elif format == 'pretty':
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        elif format == 'text':
            return str(data)
        else:
            return str(data)

class IOInterface:
    """통합 입출력 인터페이스"""
    
    def __init__(self):
        self.input_processor = InputProcessor()
        self.output_formatter = OutputFormatter()
    
    def process_input(self, data: Any, format: str = 'auto') -> Dict:
        """입력 처리"""
        result = self.input_processor.process(data, format)
        return result.data
    
    def format_output(self, data: Any, format: str = 'json') -> str:
        """출력 포맷팅"""
        return self.output_formatter.format(data, format)
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        format_counts = {}
        for item in self.input_processor.history:
            fmt = item.format
            format_counts[fmt] = format_counts.get(fmt, 0) + 1
        
        return {
            'total_processed': len(self.input_processor.history),
            'supported_formats': self.input_processor.supported_formats,
            'format_distribution': format_counts
        }
