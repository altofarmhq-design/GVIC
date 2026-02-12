"""특허 4: 재귀적 모듈화 기반의 데이터 처리 시스템
Recursive Modularization-Based Data Processing System

시스템 구성:
- 2100: 모듈 레지스트리 (표준화된 처리 모듈 저장/관리)
- 2200: 파이프라인 구성기 (재귀적 조합으로 파이프라인 생성)
- 2300: 실행 엔진 (모듈 간 데이터 흐름 제어/실행)
- 2400: 상태 관리자 (실행 결과/이력 기록, 장애 복구)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """모듈 유형"""
    TRANSFORM = "transform"     # 변환
    FILTER = "filter"          # 필터링
    AGGREGATE = "aggregate"    # 집계
    ROUTE = "route"           # 라우팅
    MERGE = "merge"           # 병합


class CompositeType(Enum):
    """복합 구조 유형"""
    SEQUENCE = "sequence"      # Seq(P₁, P₂, ...)
    PARALLEL = "parallel"      # Par(P₁, P₂, ...)
    CONDITIONAL = "conditional" # Cond(c, P₁, P₂)
    LOOP = "loop"             # Loop(c, P)


class CompatibilityLevel(Enum):
    """스키마 호환성 수준"""
    FULL = "full"         # 완전 호환
    PARTIAL = "partial"   # 부분 호환
    NONE = "none"         # 호환 불가


@dataclass
class Schema:
    """데이터 스키마"""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, str] = field(default_factory=dict)
    
    @property
    def all_fields(self) -> set:
        return set(self.required_fields) | set(self.optional_fields)


@dataclass
class ProcessingModule:
    """처리 모듈 표준 인터페이스"""
    module_id: str
    module_type: ModuleType
    name: str
    input_schema: Schema
    output_schema: Schema
    parameters: Dict = field(default_factory=dict)
    processor: Optional[Callable] = None
    enabled: bool = True
    
    def process(self, input_data: Any) -> Any:
        """데이터 처리"""
        if self.processor is None:
            return input_data
        return self.processor(input_data, self.parameters)
    
    def validate(self, input_data: Any) -> bool:
        """입력 검증"""
        if isinstance(input_data, dict):
            required = set(self.input_schema.required_fields)
            provided = set(input_data.keys())
            return required.issubset(provided)
        return True


class PipelineNode(ABC):
    """파이프라인 노드 추상 클래스"""
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        pass
    
    @abstractmethod
    def get_complexity(self) -> int:
        pass


class ModuleNode(PipelineNode):
    """단일 모듈 노드"""
    
    def __init__(self, module: ProcessingModule):
        self.module = module
    
    def execute(self, input_data: Any) -> Any:
        if not self.module.enabled:
            return input_data
        return self.module.process(input_data)
    
    def get_complexity(self) -> int:
        """[수학식 3] C(Module) = 1"""
        return 1


class SequenceNode(PipelineNode):
    """순차 실행 노드: Seq(P₁, P₂, ..., Pₙ)"""
    
    def __init__(self, children: List[PipelineNode]):
        self.children = children
    
    def execute(self, input_data: Any) -> Any:
        result = input_data
        for child in self.children:
            result = child.execute(result)
        return result
    
    def get_complexity(self) -> int:
        """[수학식 3] C(Seq(P₁, ..., Pₙ)) = Σᵢ C(Pᵢ)"""
        return sum(child.get_complexity() for child in self.children)


class ParallelNode(PipelineNode):
    """병렬 실행 노드: Par(P₁, P₂, ..., Pₙ)"""
    
    def __init__(self, children: List[PipelineNode], merge_func: Callable = None):
        self.children = children
        self.merge_func = merge_func or (lambda results: results)
    
    def execute(self, input_data: Any) -> Any:
        results = [child.execute(input_data) for child in self.children]
        return self.merge_func(results)
    
    def get_complexity(self) -> int:
        """[수학식 3] C(Par(P₁, ..., Pₙ)) = max(C(Pᵢ))"""
        if not self.children:
            return 0
        return max(child.get_complexity() for child in self.children)


class ConditionalNode(PipelineNode):
    """조건부 실행 노드: Cond(c, P₁, P₂)"""
    
    def __init__(self, condition: Callable, true_branch: PipelineNode, 
                 false_branch: PipelineNode):
        self.condition = condition
        self.true_branch = true_branch
        self.false_branch = false_branch
    
    def execute(self, input_data: Any) -> Any:
        if self.condition(input_data):
            return self.true_branch.execute(input_data)
        else:
            return self.false_branch.execute(input_data)
    
    def get_complexity(self) -> int:
        """[수학식 3] C(Cond(c, P₁, P₂)) = C(c) + max(C(P₁), C(P₂))"""
        return 1 + max(self.true_branch.get_complexity(), 
                      self.false_branch.get_complexity())


class LoopNode(PipelineNode):
    """반복 실행 노드: Loop(c, P)"""
    
    def __init__(self, condition: Callable, body: PipelineNode, 
                 max_iterations: int = 100):
        self.condition = condition
        self.body = body
        self.max_iterations = max_iterations
        self.estimated_iterations = 5  # 평균 반복 횟수 추정
    
    def execute(self, input_data: Any) -> Any:
        result = input_data
        iterations = 0
        while self.condition(result) and iterations < self.max_iterations:
            result = self.body.execute(result)
            iterations += 1
        return result
    
    def get_complexity(self) -> int:
        """[수학식 3] C(Loop(c, P)) = C(c) + k × C(P)"""
        return 1 + self.estimated_iterations * self.body.get_complexity()


class ModuleRegistry:
    """2100: 모듈 레지스트리
    표준화된 처리 모듈 저장/관리
    """
    
    def __init__(self):
        self.modules: Dict[str, ProcessingModule] = {}
        self._register_builtin_modules()
    
    def _register_builtin_modules(self):
        """내장 모듈 등록"""
        # 변환 모듈
        self.register(ProcessingModule(
            module_id="transform_normalize",
            module_type=ModuleType.TRANSFORM,
            name="Normalize",
            input_schema=Schema(required_fields=['value']),
            output_schema=Schema(required_fields=['value']),
            processor=lambda data, params: {
                **data, 
                'value': data.get('value', 0) / params.get('max', 1)
            }
        ))
        
        # 필터 모듈
        self.register(ProcessingModule(
            module_id="filter_threshold",
            module_type=ModuleType.FILTER,
            name="ThresholdFilter",
            input_schema=Schema(required_fields=['value']),
            output_schema=Schema(required_fields=['value', 'passed']),
            processor=lambda data, params: {
                **data, 
                'passed': data.get('value', 0) >= params.get('threshold', 0.5)
            }
        ))
        
        # 집계 모듈
        self.register(ProcessingModule(
            module_id="aggregate_sum",
            module_type=ModuleType.AGGREGATE,
            name="Sum",
            input_schema=Schema(required_fields=['values']),
            output_schema=Schema(required_fields=['sum']),
            processor=lambda data, params: {
                'sum': sum(data.get('values', []))
            }
        ))
    
    def register(self, module: ProcessingModule):
        """모듈 등록"""
        self.modules[module.module_id] = module
        logger.debug(f"Module registered: {module.module_id}")
    
    def get(self, module_id: str) -> Optional[ProcessingModule]:
        """모듈 조회"""
        return self.modules.get(module_id)
    
    def list_modules(self, module_type: ModuleType = None) -> List[ProcessingModule]:
        """모듈 목록 조회"""
        if module_type is None:
            return list(self.modules.values())
        return [m for m in self.modules.values() if m.module_type == module_type]


class SchemaValidator:
    """스키마 호환성 검증기"""
    
    @staticmethod
    def check_compatibility(S_out: Schema, S_in: Schema) -> Tuple[CompatibilityLevel, float]:
        """[수학식 2] 스키마 호환성 검증
        
        Compatible(S_out, S_in) = 
            TRUE     if S₁ ⊇ S₂ (완전 호환)
            PARTIAL  if S₁ ∩ S₂ ≠ ∅ (부분 호환)
            FALSE    if S₁ ∩ S₂ = ∅ (호환 불가)
        
        coverage = |required_fields ∩ provided_fields| / |required_fields|
        """
        provided = S_out.all_fields
        required = set(S_in.required_fields)
        
        if not required:
            return CompatibilityLevel.FULL, 1.0
        
        intersection = required & provided
        coverage = len(intersection) / len(required)
        
        if coverage == 1.0:
            return CompatibilityLevel.FULL, coverage
        elif coverage > 0:
            return CompatibilityLevel.PARTIAL, coverage
        else:
            return CompatibilityLevel.NONE, 0.0


class PipelineBuilder:
    """2200: 파이프라인 구성기
    재귀적 조합으로 파이프라인 생성
    """
    
    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
    
    def build_sequence(self, module_ids: List[str]) -> SequenceNode:
        """순차 파이프라인 생성"""
        nodes = []
        for mid in module_ids:
            module = self.registry.get(mid)
            if module:
                nodes.append(ModuleNode(module))
        return SequenceNode(nodes)
    
    def build_parallel(self, module_ids: List[str], 
                      merge_func: Callable = None) -> ParallelNode:
        """병렬 파이프라인 생성"""
        nodes = []
        for mid in module_ids:
            module = self.registry.get(mid)
            if module:
                nodes.append(ModuleNode(module))
        return ParallelNode(nodes, merge_func)
    
    def build_conditional(self, condition: Callable,
                         true_modules: List[str],
                         false_modules: List[str]) -> ConditionalNode:
        """조건부 파이프라인 생성"""
        true_branch = self.build_sequence(true_modules)
        false_branch = self.build_sequence(false_modules)
        return ConditionalNode(condition, true_branch, false_branch)
    
    def build_from_definition(self, definition: Dict) -> PipelineNode:
        """정의 기반 파이프라인 생성"""
        node_type = definition.get('type', 'module')
        
        if node_type == 'module':
            module = self.registry.get(definition['module_id'])
            return ModuleNode(module) if module else None
        
        elif node_type == 'sequence':
            children = [self.build_from_definition(c) for c in definition['children']]
            return SequenceNode([c for c in children if c])
        
        elif node_type == 'parallel':
            children = [self.build_from_definition(c) for c in definition['children']]
            return ParallelNode([c for c in children if c])
        
        elif node_type == 'conditional':
            condition = definition.get('condition', lambda x: True)
            true_branch = self.build_from_definition(definition['true_branch'])
            false_branch = self.build_from_definition(definition['false_branch'])
            return ConditionalNode(condition, true_branch, false_branch)
        
        return None


@dataclass
class ExecutionCheckpoint:
    """실행 체크포인트"""
    checkpoint_id: str
    pipeline_id: str
    stage_index: int
    intermediate_data: Any
    timestamp: str
    pending_modules: List[str] = field(default_factory=list)


class ExecutionEngine:
    """2300: 실행 엔진
    모듈 간 데이터 흐름 제어/실행
    """
    
    def __init__(self):
        self.execution_log: List[Dict] = []
    
    def execute(self, pipeline: PipelineNode, input_data: Any) -> Tuple[Any, Dict]:
        """파이프라인 실행"""
        start_time = datetime.now(timezone.utc)
        
        try:
            result = pipeline.execute(input_data)
            success = True
            error = None
        except Exception as e:
            result = None
            success = False
            error = str(e)
        
        end_time = datetime.now(timezone.utc)
        
        metadata = {
            'success': success,
            'error': error,
            'complexity': pipeline.get_complexity(),
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_ms': (end_time - start_time).total_seconds() * 1000
        }
        
        self.execution_log.append({
            'timestamp': end_time.isoformat(),
            **metadata
        })
        
        return result, metadata


class StateManager:
    """2400: 상태 관리자
    실행 결과/이력 기록, 장애 복구
    """
    
    def __init__(self):
        self.checkpoints: Dict[str, ExecutionCheckpoint] = {}
        self.execution_history: List[Dict] = []
    
    def create_checkpoint(self, pipeline_id: str, stage_index: int,
                         intermediate_data: Any, 
                         pending_modules: List[str] = None) -> ExecutionCheckpoint:
        """체크포인트 생성"""
        checkpoint = ExecutionCheckpoint(
            checkpoint_id=str(uuid.uuid4()),
            pipeline_id=pipeline_id,
            stage_index=stage_index,
            intermediate_data=intermediate_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
            pending_modules=pending_modules or []
        )
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        return checkpoint
    
    def find_latest_checkpoint(self, pipeline_id: str, 
                              before_stage: int = None) -> Optional[ExecutionCheckpoint]:
        """[알고리즘 5] 최신 유효 체크포인트 찾기"""
        valid_checkpoints = [
            cp for cp in self.checkpoints.values()
            if cp.pipeline_id == pipeline_id
        ]
        
        if before_stage is not None:
            valid_checkpoints = [
                cp for cp in valid_checkpoints 
                if cp.stage_index < before_stage
            ]
        
        if not valid_checkpoints:
            return None
        
        return max(valid_checkpoints, key=lambda cp: cp.timestamp)
    
    def recover_from_failure(self, pipeline_id: str, 
                            failure_stage: int) -> Tuple[Any, List[str]]:
        """[알고리즘 5] 체크포인트 기반 장애 복구"""
        checkpoint = self.find_latest_checkpoint(pipeline_id, failure_stage)
        
        if checkpoint is None:
            return None, []
        
        return checkpoint.intermediate_data, checkpoint.pending_modules
    
    def log_execution(self, pipeline_id: str, result: Dict):
        """실행 결과 기록"""
        self.execution_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'pipeline_id': pipeline_id,
            **result
        })


class PipelineOptimizer:
    """파이프라인 최적화기"""
    
    @staticmethod
    def optimize(pipeline: PipelineNode) -> PipelineNode:
        """[수학식 5] 최적화 변환 규칙 적용"""
        # 실제 구현에서는 AST 변환 수행
        # 여기서는 간단히 원본 반환
        return pipeline
    
    @staticmethod
    def estimate_cost(pipeline: PipelineNode) -> Dict:
        """비용 추정"""
        complexity = pipeline.get_complexity()
        return {
            'complexity': complexity,
            'estimated_time_ms': complexity * 10,  # 단순 추정
            'parallelizable': isinstance(pipeline, ParallelNode)
        }


class RecursiveModularPipeline:
    """재귀적 모듈화 파이프라인 시스템 (통합)"""
    
    def __init__(self):
        self.registry = ModuleRegistry()
        self.builder = PipelineBuilder(self.registry)
        self.engine = ExecutionEngine()
        self.state_manager = StateManager()
        self.optimizer = PipelineOptimizer()
        
        self.pipelines: Dict[str, PipelineNode] = {}
        self.history: List[Dict] = []
    
    def register_module(self, module: ProcessingModule):
        """모듈 등록"""
        self.registry.register(module)
    
    def create_pipeline(self, name: str, definition: Dict) -> str:
        """파이프라인 생성"""
        pipeline_id = str(uuid.uuid4())
        pipeline = self.builder.build_from_definition(definition)
        
        if pipeline:
            # 최적화 적용
            optimized = self.optimizer.optimize(pipeline)
            self.pipelines[pipeline_id] = optimized
            
            logger.info(f"Pipeline created: {name} ({pipeline_id})")
        
        return pipeline_id
    
    def execute_pipeline(self, pipeline_id: str, input_data: Any) -> Dict:
        """파이프라인 실행"""
        if pipeline_id not in self.pipelines:
            return {'error': 'Pipeline not found', 'success': False}
        
        pipeline = self.pipelines[pipeline_id]
        result, metadata = self.engine.execute(pipeline, input_data)
        
        # 상태 기록
        self.state_manager.log_execution(pipeline_id, {
            'result': result,
            'metadata': metadata
        })
        
        self.history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'pipeline_id': pipeline_id,
            'success': metadata['success']
        })
        
        return {
            'result': result,
            'metadata': metadata
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.history)
        success = sum(1 for h in self.history if h['success'])
        
        return {
            'total_executions': total,
            'success_count': success,
            'success_rate': success / total if total > 0 else 0,
            'registered_modules': len(self.registry.modules),
            'pipelines_count': len(self.pipelines)
        }


# 하위 호환성을 위한 별칭
class PipelineProcessor(RecursiveModularPipeline):
    """하위 호환성 래퍼"""
    
    def __init__(self):
        super().__init__()
        self.stages: List[Dict] = []
    
    def add_stage(self, name: str, processor: Callable, config: Dict = None):
        """스테이지 추가 (하위 호환성)"""
        module = ProcessingModule(
            module_id=f"custom_{len(self.stages)}",
            module_type=ModuleType.TRANSFORM,
            name=name,
            input_schema=Schema(),
            output_schema=Schema(),
            parameters=config or {},
            processor=processor
        )
        self.register_module(module)
        self.stages.append({
            'name': name,
            'module_id': module.module_id,
            'enabled': True
        })
    
    def process(self, data: Any) -> Dict:
        """처리 실행 (하위 호환성)"""
        result = data
        stage_results = []
        
        for stage in self.stages:
            if not stage['enabled']:
                continue
            
            module = self.registry.get(stage['module_id'])
            if module:
                try:
                    result = module.process(result)
                    stage_results.append({
                        'stage': stage['name'],
                        'success': True
                    })
                except Exception as e:
                    stage_results.append({
                        'stage': stage['name'],
                        'success': False,
                        'error': str(e)
                    })
                    break
        
        return {
            'result': result,
            'metadata': {
                'stages_executed': len(stage_results),
                'success': all(s['success'] for s in stage_results),
                'details': stage_results
            }
        }
