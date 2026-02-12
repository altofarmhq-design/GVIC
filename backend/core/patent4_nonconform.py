"""특허 5: 비적합 데이터 자산화 시스템 (시스템 3000)
Non-Conforming Data Assetization System

시스템 구성:
- 3100: 비적합 감지부 (Non-Conformance Detector)
- 3150: 격리 저장소 (Quarantine Storage)
- 3200: 비적합 분류부 (Non-Conformance Classifier)
- 3300: 가치 평가부 (Value Assessor)
- 3400: 자산 변환부 (Asset Converter)
- 3500: 규칙 개선 제안부 (Rule Improvement Suggester)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


class NonConformanceType(Enum):
    """비적합 유형"""
    STRUCTURAL = "structural"    # 구조적 비적합: 스키마 불일치, 필수 필드 누락
    VALUE = "value"             # 값 비적합: 범위 위반, 형식 오류, 타입 불일치
    LOGICAL = "logical"         # 논리적 비적합: 비즈니스 규칙 위반, 모순 관계
    TEMPORAL = "temporal"       # 시간적 비적합: 순서 위반, 타임스탬프 이상


class ValueLevel(Enum):
    """가치 수준"""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


@dataclass
class NonConformingData:
    """비적합 데이터"""
    nc_id: str
    original_data: Any
    nc_type: NonConformanceType
    nc_reason: str
    detection_time: str
    source_info: Dict = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)


@dataclass
class SecondaryAsset:
    """2차 자산 객체"""
    asset_id: str
    original_nc_id: str
    original_data: Any
    classification: NonConformanceType
    value_score: float
    value_factors: Dict[str, float]
    suggested_utilization: List[str]
    creation_time: str
    expiry_time: Optional[str] = None


@dataclass
class RuleImprovement:
    """규칙 개선 제안"""
    suggestion_id: str
    nc_type: NonConformanceType
    pattern_description: str
    frequency: int
    suggested_rule_change: str
    priority: int  # 1=highest
    creation_time: str


class NonConformanceDetector:
    """3100: 비적합 감지부
    데이터 처리 파이프라인에서 비적합 데이터 실시간 감지
    """
    
    def __init__(self):
        self.detection_rules: List[Dict] = []
        self.detection_history: List[Dict] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """기본 감지 규칙 초기화"""
        self.detection_rules = [
            {
                'id': 'schema_check',
                'type': NonConformanceType.STRUCTURAL,
                'check': lambda d, ctx: self._check_schema(d, ctx.get('required_fields', []))
            },
            {
                'id': 'value_range_check',
                'type': NonConformanceType.VALUE,
                'check': lambda d, ctx: self._check_value_range(d, ctx.get('bounds', (0, 1)))
            },
            {
                'id': 'type_check',
                'type': NonConformanceType.VALUE,
                'check': lambda d, ctx: self._check_type(d, ctx.get('expected_type'))
            },
            {
                'id': 'timestamp_check',
                'type': NonConformanceType.TEMPORAL,
                'check': lambda d, ctx: self._check_timestamp(d)
            }
        ]
    
    def _check_schema(self, data: Any, required_fields: List[str]) -> Tuple[bool, str]:
        """스키마 검증"""
        if not isinstance(data, dict):
            return True, ""  # 딕셔너리 아니면 패스
        
        missing = [f for f in required_fields if f not in data]
        if missing:
            return False, f"Missing required fields: {missing}"
        return True, ""
    
    def _check_value_range(self, data: Any, bounds: Tuple[float, float]) -> Tuple[bool, str]:
        """값 범위 검증"""
        lower, upper = bounds
        
        if isinstance(data, (int, float)):
            if data < lower or data > upper:
                return False, f"Value {data} out of range [{lower}, {upper}]"
        elif isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    if value < lower or value > upper:
                        return False, f"Field '{key}' value {value} out of range [{lower}, {upper}]"
        
        return True, ""
    
    def _check_type(self, data: Any, expected_type: type) -> Tuple[bool, str]:
        """타입 검증"""
        if expected_type is None:
            return True, ""
        
        if not isinstance(data, expected_type):
            return False, f"Expected {expected_type.__name__}, got {type(data).__name__}"
        return True, ""
    
    def _check_timestamp(self, data: Any) -> Tuple[bool, str]:
        """타임스탬프 검증"""
        if isinstance(data, dict) and 'timestamp' in data:
            try:
                ts = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                
                # 미래 시간 체크
                if ts > now:
                    return False, f"Future timestamp detected: {data['timestamp']}"
                
                # 너무 오래된 데이터 체크 (1년 이상)
                days_old = (now - ts).days
                if days_old > 365:
                    return False, f"Data too old: {days_old} days"
                    
            except ValueError as e:
                return False, f"Invalid timestamp format: {str(e)}"
        
        return True, ""
    
    def detect(self, data: Any, context: Dict = None) -> List[NonConformingData]:
        """비적합 데이터 감지"""
        context = context or {}
        detected = []
        
        for rule in self.detection_rules:
            is_valid, reason = rule['check'](data, context)
            
            if not is_valid:
                nc = NonConformingData(
                    nc_id=str(uuid.uuid4()),
                    original_data=data,
                    nc_type=rule['type'],
                    nc_reason=reason,
                    detection_time=datetime.now(timezone.utc).isoformat(),
                    source_info=context.get('source_info', {}),
                    metadata={'rule_id': rule['id']}
                )
                detected.append(nc)
                
                self.detection_history.append({
                    'timestamp': nc.detection_time,
                    'nc_id': nc.nc_id,
                    'type': nc.nc_type.value,
                    'reason': nc.nc_reason
                })
        
        return detected


class QuarantineStorage:
    """3150: 격리 저장소
    비적합 데이터 별도 저장
    """
    
    def __init__(self, retention_days: int = 30):
        self.storage: Dict[str, NonConformingData] = {}
        self.retention_days = retention_days
    
    def store(self, nc_data: NonConformingData):
        """비적합 데이터 저장"""
        self.storage[nc_data.nc_id] = nc_data
        logger.debug(f"Stored non-conforming data: {nc_data.nc_id}")
    
    def retrieve(self, nc_id: str) -> Optional[NonConformingData]:
        """비적합 데이터 조회"""
        return self.storage.get(nc_id)
    
    def retrieve_by_type(self, nc_type: NonConformanceType) -> List[NonConformingData]:
        """유형별 조회"""
        return [nc for nc in self.storage.values() if nc.nc_type == nc_type]
    
    def cleanup_expired(self):
        """만료된 데이터 정리"""
        now = datetime.now(timezone.utc)
        expired_ids = []
        
        for nc_id, nc_data in self.storage.items():
            detection_time = datetime.fromisoformat(nc_data.detection_time.replace('Z', '+00:00'))
            age_days = (now - detection_time).days
            
            if age_days > self.retention_days:
                expired_ids.append(nc_id)
        
        for nc_id in expired_ids:
            del self.storage[nc_id]
        
        return len(expired_ids)
    
    def get_statistics(self) -> Dict:
        """통계 정보"""
        type_counts = {}
        for nc in self.storage.values():
            type_key = nc.nc_type.value
            type_counts[type_key] = type_counts.get(type_key, 0) + 1
        
        return {
            'total_count': len(self.storage),
            'by_type': type_counts
        }


class NonConformanceClassifier:
    """3200: 비적합 분류부
    격리된 비적합 데이터를 유형별로 분류
    """
    
    def __init__(self):
        self.classification_history: List[Dict] = []
    
    def classify(self, nc_data: NonConformingData) -> NonConformanceType:
        """비적합 유형 분류 (세부 분류)"""
        # 이미 감지 단계에서 기본 분류됨
        # 여기서는 세부 분류 수행
        
        reason = nc_data.nc_reason.lower()
        
        # 세부 분류 로직
        if 'missing' in reason or 'required' in reason or 'schema' in reason:
            detailed_type = NonConformanceType.STRUCTURAL
        elif 'range' in reason or 'format' in reason or 'type' in reason:
            detailed_type = NonConformanceType.VALUE
        elif 'rule' in reason or 'contradiction' in reason or 'logic' in reason:
            detailed_type = NonConformanceType.LOGICAL
        elif 'timestamp' in reason or 'sequence' in reason or 'order' in reason:
            detailed_type = NonConformanceType.TEMPORAL
        else:
            detailed_type = nc_data.nc_type
        
        self.classification_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'nc_id': nc_data.nc_id,
            'original_type': nc_data.nc_type.value,
            'classified_type': detailed_type.value
        })
        
        return detailed_type


class ValueAssessor:
    """3300: 가치 평가부
    분류된 비적합 데이터에 대한 가치 평가 알고리즘
    """
    
    def __init__(self, value_threshold: float = 0.5):
        self.value_threshold = value_threshold
        self.assessment_history: List[Dict] = []
        self.pattern_frequency: Dict[str, int] = {}
    
    def assess(self, nc_data: NonConformingData, 
               business_relevance: float = 0.5) -> Tuple[float, Dict[str, float]]:
        """가치 평가
        
        ValueScore = f(Frequency, Recency, PatternNovelty, BusinessRelevance, RecoveryCost)
        """
        # 1. 발생 빈도 (Frequency)
        pattern_key = f"{nc_data.nc_type.value}:{nc_data.nc_reason[:50]}"
        self.pattern_frequency[pattern_key] = self.pattern_frequency.get(pattern_key, 0) + 1
        frequency = min(self.pattern_frequency[pattern_key] / 100, 1.0)
        
        # 2. 최근성 (Recency)
        try:
            detection_time = datetime.fromisoformat(nc_data.detection_time.replace('Z', '+00:00'))
            hours_ago = (datetime.now(timezone.utc) - detection_time).total_seconds() / 3600
            recency = np.exp(-0.1 * hours_ago)  # 최근일수록 높음
        except (ValueError, TypeError):
            recency = 0.5
        
        # 3. 패턴 신규성 (PatternNovelty)
        # 빈도가 낮을수록 신규성 높음
        novelty = 1.0 - frequency
        
        # 4. 비즈니스 관련성 (BusinessRelevance)
        # 외부 입력 사용
        
        # 5. 복구 비용 (RecoveryCost) - 낮을수록 좋음
        # 간단한 휴리스틱: 구조적 > 논리적 > 시간적 > 값
        recovery_cost_map = {
            NonConformanceType.STRUCTURAL: 0.8,
            NonConformanceType.LOGICAL: 0.6,
            NonConformanceType.TEMPORAL: 0.4,
            NonConformanceType.VALUE: 0.2
        }
        recovery_cost = recovery_cost_map.get(nc_data.nc_type, 0.5)
        inverse_recovery_cost = 1.0 - recovery_cost
        
        # 가중 합산
        factors = {
            'frequency': frequency,
            'recency': recency,
            'novelty': novelty,
            'business_relevance': business_relevance,
            'inverse_recovery_cost': inverse_recovery_cost
        }
        
        weights = {
            'frequency': 0.20,
            'recency': 0.20,
            'novelty': 0.25,
            'business_relevance': 0.25,
            'inverse_recovery_cost': 0.10
        }
        
        value_score = sum(factors[k] * weights[k] for k in factors)
        
        self.assessment_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'nc_id': nc_data.nc_id,
            'value_score': value_score,
            'factors': factors
        })
        
        return value_score, factors
    
    def get_value_level(self, score: float) -> ValueLevel:
        """가치 수준 판정"""
        if score >= 0.8:
            return ValueLevel.VERY_HIGH
        elif score >= 0.6:
            return ValueLevel.HIGH
        elif score >= 0.4:
            return ValueLevel.MEDIUM
        elif score >= 0.2:
            return ValueLevel.LOW
        else:
            return ValueLevel.NEGLIGIBLE


class AssetConverter:
    """3400: 자산 변환부
    가치 임계치 이상의 비적합 데이터를 2차 자산 객체로 변환
    """
    
    def __init__(self, value_threshold: float = 0.5):
        self.value_threshold = value_threshold
        self.converted_assets: Dict[str, SecondaryAsset] = {}
        self.conversion_history: List[Dict] = []
    
    def convert(self, nc_data: NonConformingData, value_score: float,
                value_factors: Dict[str, float]) -> Optional[SecondaryAsset]:
        """2차 자산으로 변환"""
        if value_score < self.value_threshold:
            return None
        
        # 활용 방안 제안 생성
        utilizations = self._generate_utilization_suggestions(nc_data, value_factors)
        
        asset = SecondaryAsset(
            asset_id=str(uuid.uuid4()),
            original_nc_id=nc_data.nc_id,
            original_data=nc_data.original_data,
            classification=nc_data.nc_type,
            value_score=value_score,
            value_factors=value_factors,
            suggested_utilization=utilizations,
            creation_time=datetime.now(timezone.utc).isoformat()
        )
        
        self.converted_assets[asset.asset_id] = asset
        
        self.conversion_history.append({
            'timestamp': asset.creation_time,
            'nc_id': nc_data.nc_id,
            'asset_id': asset.asset_id,
            'value_score': value_score
        })
        
        return asset
    
    def _generate_utilization_suggestions(self, nc_data: NonConformingData,
                                         factors: Dict[str, float]) -> List[str]:
        """활용 방안 제안 생성"""
        suggestions = []
        
        if nc_data.nc_type == NonConformanceType.STRUCTURAL:
            suggestions.extend([
                "Schema validation rule improvement",
                "Data entry form enhancement",
                "API input validation update"
            ])
        elif nc_data.nc_type == NonConformanceType.VALUE:
            suggestions.extend([
                "Value range rule adjustment",
                "Data transformation pipeline enhancement",
                "Anomaly detection training data"
            ])
        elif nc_data.nc_type == NonConformanceType.LOGICAL:
            suggestions.extend([
                "Business rule clarification",
                "Exception handling improvement",
                "Workflow optimization candidate"
            ])
        elif nc_data.nc_type == NonConformanceType.TEMPORAL:
            suggestions.extend([
                "Timestamp synchronization check",
                "Sequence validation enhancement",
                "Time-series analysis input"
            ])
        
        # 높은 신규성 → ML 훈련 데이터로 활용
        if factors.get('novelty', 0) > 0.7:
            suggestions.append("Machine learning training data candidate")
        
        # 높은 빈도 → 규칙 개선 우선 대상
        if factors.get('frequency', 0) > 0.5:
            suggestions.append("High-priority rule improvement candidate")
        
        return suggestions


class RuleImprovementSuggester:
    """3500: 규칙 개선 제안부
    비적합 데이터 발생 패턴 분석 → 규칙 개선점 도출
    """
    
    def __init__(self, min_frequency_for_suggestion: int = 5):
        self.min_frequency = min_frequency_for_suggestion
        self.pattern_tracker: Dict[str, List[NonConformingData]] = {}
        self.suggestions: List[RuleImprovement] = []
    
    def track_pattern(self, nc_data: NonConformingData):
        """패턴 추적"""
        pattern_key = f"{nc_data.nc_type.value}:{nc_data.nc_reason[:50]}"
        
        if pattern_key not in self.pattern_tracker:
            self.pattern_tracker[pattern_key] = []
        
        self.pattern_tracker[pattern_key].append(nc_data)
    
    def analyze_and_suggest(self) -> List[RuleImprovement]:
        """패턴 분석 및 규칙 개선 제안"""
        new_suggestions = []
        
        for pattern_key, nc_list in self.pattern_tracker.items():
            if len(nc_list) < self.min_frequency:
                continue
            
            # 이미 제안된 패턴인지 확인
            existing = [s for s in self.suggestions 
                       if s.pattern_description == pattern_key]
            if existing:
                # 빈도 업데이트
                existing[0].frequency = len(nc_list)
                continue
            
            nc_type = nc_list[0].nc_type
            
            # 개선 제안 생성
            suggestion = RuleImprovement(
                suggestion_id=str(uuid.uuid4()),
                nc_type=nc_type,
                pattern_description=pattern_key,
                frequency=len(nc_list),
                suggested_rule_change=self._generate_rule_change(nc_type, nc_list),
                priority=self._calculate_priority(len(nc_list)),
                creation_time=datetime.now(timezone.utc).isoformat()
            )
            
            self.suggestions.append(suggestion)
            new_suggestions.append(suggestion)
        
        return new_suggestions
    
    def _generate_rule_change(self, nc_type: NonConformanceType,
                             nc_list: List[NonConformingData]) -> str:
        """규칙 변경 제안 생성"""
        if nc_type == NonConformanceType.VALUE:
            # 값 범위 분석하여 새 범위 제안
            return "Consider expanding value range or adding validation exceptions"
        elif nc_type == NonConformanceType.STRUCTURAL:
            return "Consider making fields optional or adding auto-completion logic"
        elif nc_type == NonConformanceType.LOGICAL:
            return "Review business rules for edge cases and add exception handling"
        elif nc_type == NonConformanceType.TEMPORAL:
            return "Adjust timestamp tolerance or add time synchronization handling"
        return "Review and update processing rules"
    
    def _calculate_priority(self, frequency: int) -> int:
        """우선순위 계산 (1=highest)"""
        if frequency >= 100:
            return 1
        elif frequency >= 50:
            return 2
        elif frequency >= 20:
            return 3
        elif frequency >= 10:
            return 4
        else:
            return 5
    
    def get_top_suggestions(self, n: int = 5) -> List[RuleImprovement]:
        """상위 제안 조회"""
        sorted_suggestions = sorted(self.suggestions, key=lambda s: s.priority)
        return sorted_suggestions[:n]


class NonConformingDataAssetizationSystem:
    """비적합 데이터 자산화 시스템 (통합 - 시스템 3000)"""
    
    def __init__(self, value_threshold: float = 0.5, retention_days: int = 30):
        # 서브시스템 초기화
        self.detector = NonConformanceDetector()           # 3100
        self.quarantine = QuarantineStorage(retention_days) # 3150
        self.classifier = NonConformanceClassifier()       # 3200
        self.assessor = ValueAssessor(value_threshold)     # 3300
        self.converter = AssetConverter(value_threshold)   # 3400
        self.suggester = RuleImprovementSuggester()        # 3500
        
        self.processing_history: List[Dict] = []
    
    def process(self, data: Any, context: Dict = None) -> Dict:
        """메인 처리 함수"""
        context = context or {}
        result = {
            'original_data': data,
            'is_conforming': True,
            'non_conformances': [],
            'assets_created': [],
            'processed': data
        }
        
        # 1. 비적합 감지 (3100)
        nc_list = self.detector.detect(data, context)
        
        if not nc_list:
            # 정합 데이터
            return result
        
        result['is_conforming'] = False
        
        for nc_data in nc_list:
            # 2. 격리 저장 (3150)
            self.quarantine.store(nc_data)
            
            # 3. 상세 분류 (3200)
            detailed_type = self.classifier.classify(nc_data)
            nc_data.nc_type = detailed_type
            
            # 4. 가치 평가 (3300)
            value_score, factors = self.assessor.assess(
                nc_data, 
                business_relevance=context.get('business_relevance', 0.5)
            )
            
            nc_info = {
                'nc_id': nc_data.nc_id,
                'type': nc_data.nc_type.value,
                'reason': nc_data.nc_reason,
                'value_score': value_score,
                'value_level': self.assessor.get_value_level(value_score).value
            }
            result['non_conformances'].append(nc_info)
            
            # 5. 자산 변환 (3400) - 임계치 이상인 경우
            asset = self.converter.convert(nc_data, value_score, factors)
            if asset:
                result['assets_created'].append({
                    'asset_id': asset.asset_id,
                    'value_score': asset.value_score,
                    'utilizations': asset.suggested_utilization
                })
            
            # 6. 패턴 추적 (3500)
            self.suggester.track_pattern(nc_data)
        
        # 처리된 데이터 (비적합 부분 제거 또는 보정)
        result['processed'] = self._sanitize_data(data, nc_list)
        
        self.processing_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'nc_count': len(nc_list),
            'assets_created': len(result['assets_created'])
        })
        
        return result
    
    def _sanitize_data(self, data: Any, nc_list: List[NonConformingData]) -> Any:
        """데이터 정제 (비적합 부분 처리)"""
        if isinstance(data, (int, float)):
            # 범위 내로 클램핑
            return max(0, min(data, 1))
        elif isinstance(data, dict):
            # 문제 필드 기본값으로 대체
            sanitized = data.copy()
            for nc in nc_list:
                if nc.nc_type == NonConformanceType.VALUE:
                    for key, value in sanitized.items():
                        if isinstance(value, (int, float)):
                            sanitized[key] = max(0, min(value, 1))
            return sanitized
        return data
    
    def get_rule_improvements(self) -> List[Dict]:
        """규칙 개선 제안 조회"""
        self.suggester.analyze_and_suggest()
        top_suggestions = self.suggester.get_top_suggestions(10)
        
        return [
            {
                'suggestion_id': s.suggestion_id,
                'type': s.nc_type.value,
                'pattern': s.pattern_description,
                'frequency': s.frequency,
                'suggested_change': s.suggested_rule_change,
                'priority': s.priority
            }
            for s in top_suggestions
        ]
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        quarantine_stats = self.quarantine.get_statistics()
        
        return {
            'total_processed': len(self.processing_history),
            'quarantine': quarantine_stats,
            'assets_created': len(self.converter.converted_assets),
            'rule_suggestions': len(self.suggester.suggestions),
            'pattern_types_tracked': len(self.suggester.pattern_tracker)
        }


# 하위 호환성을 위한 별칭
class NonconformHandler(NonConformingDataAssetizationSystem):
    """하위 호환성 래퍼"""
    
    def __init__(self, threshold: float = 0.1):
        super().__init__(value_threshold=0.5)
        self.threshold = threshold
        self.history: List[Dict] = []
        self.nonconform_count = 0
    
    def process(self, value: float, bounds: Tuple[float, float] = (0, 1)) -> Dict:
        """하위 호환성 처리 함수"""
        lower, upper = bounds
        original = value
        is_nonconform = False
        adjustment = 0.0
        
        if value < lower:
            is_nonconform = True
            adjustment = lower - value
            value = lower
        elif value > upper:
            is_nonconform = True
            adjustment = value - upper
            value = upper
        
        if is_nonconform:
            self.nonconform_count += 1
            
            # 상위 클래스 기능 호출
            super().process(
                {'value': original},
                context={'bounds': bounds}
            )
        
        result = {
            'original': original,
            'processed': value,
            'is_nonconform': is_nonconform,
            'adjustment': adjustment,
            'bounds': bounds,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        self.history.append(result)
        return result
    
    def batch_process(self, values: List[float], 
                     bounds: Tuple[float, float] = (0, 1)) -> List[Dict]:
        """배치 처리"""
        return [self.process(v, bounds) for v in values]
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환 (하위 호환성)"""
        total = len(self.history)
        
        adjustments = [h['adjustment'] for h in self.history if h['is_nonconform']]
        
        return {
            'total_processed': total,
            'nonconform_count': self.nonconform_count,
            'nonconform_rate': self.nonconform_count / total if total > 0 else 0,
            'average_adjustment': float(np.mean(adjustments)) if adjustments else 0,
            'max_adjustment': max(adjustments) if adjustments else 0,
            **super().get_statistics()
        }
