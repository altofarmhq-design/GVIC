"""GVIC Engine Core Modules
특허 기반 핵심 모듈 구성

- 특허 1: 전역 수렴 제어 시스템 (patent1_convergence)
- 특허 2: 다단계 신호 전처리 시스템 (patent2_signal)
- 특허 3: 신호 자산화 통합 플랫폼 (patent3_signal_asset)
- 특허 4: 재귀적 모듈화 파이프라인 (patent3_pipeline)
- 특허 5: 비적합 데이터 자산화 시스템 (patent4_nonconform) - 시스템 3000
- 특허 6: 가중 분배 모델 시스템 (patent5_distribution) - 시스템 4000
- 특허 6-J: 다중 도메인 통합 인터페이스 (multi_domain_integration)
"""

# 특허 1: 전역 수렴 제어 시스템
from .patent1_convergence import (
    ConvergenceController,
    OmegaConstraints,
    RecoveryStage,
    AnomalyLevel,
    ParameterCollector,
    BoundaryValidator,
    ConvergenceCalculator,
    RecoveryController
)

# 특허 2: 다단계 신호 전처리 시스템
from .patent2_signal import (
    SignalPreprocessor,
    SignalAssetizer,  # 하위 호환성 별칭
    SignalType,
    ConformanceStatus,
    SignalModule,
    VectorTransformer,
    ConformanceChecker,
    RecursiveRemodulator,
    SignalRefiner,
    ModuleGenerator,
    AdaptiveClassifier
)

# 특허 3: 신호 자산화 통합 플랫폼
from .patent3_signal_asset import (
    SignalAssetizationPlatform,
    SignalObject,
    AssetObject,
    SourceType,
    OutputFormat,
    SignalCollector,
    SignalNormalizer,
    ValueCalculator,
    OutputAdapter,
    IntegrityManager
)

# 특허 4: 재귀적 모듈화 파이프라인
from .patent3_pipeline import (
    RecursiveModularPipeline,
    PipelineProcessor,  # 하위 호환성 별칭
    ProcessingModule,
    ModuleType,
    CompositeType,
    Schema,
    ModuleRegistry,
    PipelineBuilder,
    ExecutionEngine,
    StateManager
)

# 특허 5: 비적합 데이터 자산화 시스템 (시스템 3000)
from .patent4_nonconform import (
    NonConformingDataAssetizationSystem,
    NonconformHandler,  # 하위 호환성 별칭
    NonConformanceType,
    ValueLevel,
    NonConformingData,
    SecondaryAsset,
    RuleImprovement,
    NonConformanceDetector,
    QuarantineStorage,
    NonConformanceClassifier,
    ValueAssessor,
    AssetConverter,
    RuleImprovementSuggester
)

# 특허 6: 가중 분배 모델 시스템 (시스템 4000)
from .patent5_distribution import (
    WeightedDistributionSystem,
    WeightedDistributor,  # 하위 호환성 별칭
    WeightedDistributionModel,
    DomainDefinition,
    AllocationResult,
    ModelRepository,
    AllocationCalculator,
    ConsumptionMonitor,
    DynamicAdjuster,
    AnalyticsUnit
)

# 특허 6-J: 다중 도메인 통합 인터페이스
from .multi_domain_integration import (
    MultiDomainIntegrationSystem,
    DomainType,
    ProtocolType,
    CommonDataModel,
    DomainAdapter,
    SemanticMapping,
    RoutingRule
)

# 통합 엔진
from .engine import GVICEngine, ProcessingResult

# 내부 통제 시스템
from .control import InternalControlSystem, AlertManager, HealthChecker

# IO 인터페이스
from .io_interface import IOInterface

# 시각화
from .visualization import GVICVisualizer

# 워크플로우
from .workflow import WorkflowManager

__all__ = [
    # 엔진
    'GVICEngine',
    'ProcessingResult',
    
    # 특허 1
    'ConvergenceController',
    'OmegaConstraints',
    
    # 특허 2
    'SignalPreprocessor',
    'SignalAssetizer',
    
    # 특허 3
    'SignalAssetizationPlatform',
    'SignalObject',
    'AssetObject',
    
    # 특허 4
    'RecursiveModularPipeline',
    'PipelineProcessor',
    
    # 특허 5 (시스템 3000)
    'NonConformingDataAssetizationSystem',
    'NonconformHandler',
    
    # 특허 6 (시스템 4000)
    'WeightedDistributionSystem',
    'WeightedDistributor',
    
    # 특허 6-J
    'MultiDomainIntegrationSystem',
    'DomainType',
    'ProtocolType',
    
    # 기타
    'InternalControlSystem',
    'IOInterface',
    'GVICVisualizer',
    'WorkflowManager',
]
