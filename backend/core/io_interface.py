"""
IO 인터페이스 모듈
입출력 처리 통합
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field

@dataclass
class ProcessedInput:
    """처리된 입력"""
    data: Any
    format: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict = field(default_factory=dict)

class InputProcessor:
    """입력 프로세서"""
    
    def __init__(self):
        self.supported_formats = ["json", "text", "csv", "numeric"]
        self.history: List[ProcessedInput] = []
    
    def process(self, data: Any, format: str = "auto") -> ProcessedInput:
        """입력 처리"""
        if format == "auto":
            format = self._detect_format(data)
        
        if format == "json":
            if isinstance(data, str):
                processed = json.loads(data)
            else:
                processed = data
        elif format == "numeric":
            processed = float(data)
        else:
            processed = str(data)
        
        result = ProcessedInput(data=processed, format=format)
        self.history.append(result)
        return result
    
    def _detect_format(self, data: Any) -> str:
        if isinstance(data, dict):
            return "json"
        if isinstance(data, (int, float)):
            return "numeric"
        if isinstance(data, str):
            try:
                json.loads(data)
                return "json"
            except:
                pass
        return "text"

class OutputFormatter:
    """출력 포매터"""
    
    def __init__(self):
        self.default_format = "json"
    
    def format(self, data: Any, format: str = None) -> str:
        """출력 포맷팅"""
        format = format or self.default_format
        
        if format == "json":
            return json.dumps(data, ensure_ascii=False, default=str)
        elif format == "text":
            return str(data)
        elif format == "pretty":
            return json.dumps(data, ensure_ascii=False, indent=2, default=str)
        else:
            return str(data)

class IOInterface:
    """통합 IO 인터페이스"""
    
    def __init__(self):
        self.input_processor = InputProcessor()
        self.output_formatter = OutputFormatter()
    
    def process_input(self, data: Any, format: str = "auto") -> ProcessedInput:
        """입력 처리"""
        return self.input_processor.process(data, format)
    
    def format_output(self, data: Any, format: str = "json") -> str:
        """출력 포맷팅"""
        return self.output_formatter.format(data, format)
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        return {
            "inputs_processed": len(self.input_processor.history),
            "supported_formats": self.input_processor.supported_formats
        }
