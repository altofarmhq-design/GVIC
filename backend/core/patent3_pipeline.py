"""
특허 3: 파이프라인 처리 모듈
데이터 흐름 및 파이프라인 관리
"""
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

class PipelineStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class PipelineStage:
    """파이프라인 단계"""
    name: str
    processor: Callable
    order: int
    config: Dict = field(default_factory=dict)

@dataclass
class PipelineResult:
    """파이프라인 실행 결과"""
    pipeline_id: str
    status: PipelineStatus
    stages_completed: int
    total_stages: int
    output: Any = None
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "stages_completed": self.stages_completed,
            "total_stages": self.total_stages,
            "output": self.output,
            "errors": self.errors,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp
        }

class PipelineProcessor:
    """파이프라인 프로세서"""
    
    def __init__(self):
        self.stages: List[PipelineStage] = []
        self.execution_history: List[PipelineResult] = []
        self._setup_default_stages()
    
    def _setup_default_stages(self):
        """기본 단계 설정"""
        self.add_stage("validate", self._validate_stage, 1)
        self.add_stage("transform", self._transform_stage, 2)
        self.add_stage("process", self._process_stage, 3)
        self.add_stage("output", self._output_stage, 4)
    
    def _validate_stage(self, data: Any, config: Dict) -> Any:
        """검증 단계"""
        if data is None:
            raise ValueError("입력 데이터가 없습니다")
        return data
    
    def _transform_stage(self, data: Any, config: Dict) -> Any:
        """변환 단계"""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data
    
    def _process_stage(self, data: Any, config: Dict) -> Any:
        """처리 단계"""
        return {"processed": True, "data": data}
    
    def _output_stage(self, data: Any, config: Dict) -> Any:
        """출력 단계"""
        return data
    
    def add_stage(self, name: str, processor: Callable, order: int, config: Dict = None):
        """단계 추가"""
        stage = PipelineStage(
            name=name,
            processor=processor,
            order=order,
            config=config or {}
        )
        self.stages.append(stage)
        self.stages.sort(key=lambda s: s.order)
    
    def execute(self, input_data: Any) -> PipelineResult:
        """파이프라인 실행"""
        pipeline_id = f"PIP-{uuid.uuid4().hex[:8].upper()}"
        start_time = datetime.now()
        
        current_data = input_data
        stages_completed = 0
        errors = []
        
        try:
            for stage in self.stages:
                current_data = stage.processor(current_data, stage.config)
                stages_completed += 1
            
            status = PipelineStatus.COMPLETED
            output = current_data
            
        except Exception as e:
            status = PipelineStatus.FAILED
            output = None
            errors.append(f"{self.stages[stages_completed].name}: {str(e)}")
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        
        result = PipelineResult(
            pipeline_id=pipeline_id,
            status=status,
            stages_completed=stages_completed,
            total_stages=len(self.stages),
            output=output,
            errors=errors,
            duration_ms=duration
        )
        
        self.execution_history.append(result)
        return result
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        if not self.execution_history:
            return {"total": 0, "completed": 0, "failed": 0}
        
        completed = sum(1 for r in self.execution_history if r.status == PipelineStatus.COMPLETED)
        failed = sum(1 for r in self.execution_history if r.status == PipelineStatus.FAILED)
        durations = [r.duration_ms for r in self.execution_history]
        
        return {
            "total": len(self.execution_history),
            "completed": completed,
            "failed": failed,
            "success_rate": completed / len(self.execution_history),
            "avg_duration_ms": sum(durations) / len(durations)
        }
