"""특허 6: 가중 분배 모델 기반의 다영역 자원 배분 시스템 (시스템 4000)
Weighted Distribution Model-Based Multi-Domain Resource Allocation System

시스템 구성:
- 4100: 모델 저장부 (Model Repository)
- 4200: 배분 연산부 (Allocation Calculator)
- 4300: 소비 모니터링부 (Consumption Monitor)
- 4400: 동적 조정부 (Dynamic Adjuster)
- 4500: 분석부 (Analytics Unit)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class DomainDefinition:
    """영역 정의"""
    domain_id: str
    domain_name: str
    base_weight: float      # 기본 배분 비율 (0-1)
    min_weight: float       # 최소 배분 비율
    max_weight: float       # 최대 배분 비율
    priority: int           # 조정 우선순위 (낮을수록 높은 우선순위)
    
    def validate(self) -> bool:
        """유효성 검증"""
        return (0 <= self.min_weight <= self.base_weight <= self.max_weight <= 1.0)


@dataclass
class WeightedDistributionModel:
    """가중 분배 모델 (WDM)
    
    WDM = (D, W, B, C, A)
    - D: 영역 집합
    - W: 기본 가중치 벡터
    - B: 경계 조건 집합
    - C: 제약 조건
    - A: 조정 규칙
    """
    model_id: str
    name: str
    domains: List[DomainDefinition]
    sum_constraint: float = 1.0
    adjustment_rules: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    @property
    def weights(self) -> np.ndarray:
        return np.array([d.base_weight for d in self.domains])
    
    @property
    def lower_bounds(self) -> np.ndarray:
        return np.array([d.min_weight for d in self.domains])
    
    @property
    def upper_bounds(self) -> np.ndarray:
        return np.array([d.max_weight for d in self.domains])
    
    @property
    def priorities(self) -> np.ndarray:
        return np.array([d.priority for d in self.domains])
    
    def validate(self) -> Tuple[bool, str]:
        """모델 유효성 검증"""
        total_weight = sum(d.base_weight for d in self.domains)
        if not np.isclose(total_weight, self.sum_constraint, atol=0.01):
            return False, f"Weight sum {total_weight} != {self.sum_constraint}"
        
        for domain in self.domains:
            if not domain.validate():
                return False, f"Invalid domain: {domain.domain_id}"
        
        return True, "Valid"


@dataclass
class AllocationResult:
    """배분 결과"""
    allocation_id: str
    model_id: str
    total_resource: float
    allocations: Dict[str, float]
    timestamp: str
    metadata: Dict = field(default_factory=dict)


class ModelRepository:
    """4100: 모델 저장부
    가중 분배 모델 저장 및 관리
    """
    
    def __init__(self):
        self.models: Dict[str, WeightedDistributionModel] = {}
        self.active_model_id: Optional[str] = None
        self._create_default_model()
    
    def _create_default_model(self):
        """기본 모델 생성"""
        default_model = WeightedDistributionModel(
            model_id="default",
            name="Default Distribution Model",
            domains=[
                DomainDefinition("public", "Public", 0.33, 0.2, 0.5, 1),
                DomainDefinition("productive", "Productive", 0.34, 0.2, 0.5, 2),
                DomainDefinition("individual", "Individual", 0.33, 0.1, 0.5, 3)
            ]
        )
        self.store(default_model)
        self.active_model_id = default_model.model_id
    
    def store(self, model: WeightedDistributionModel) -> bool:
        """모델 저장"""
        is_valid, message = model.validate()
        if not is_valid:
            logger.warning(f"Invalid model: {message}")
            return False
        
        self.models[model.model_id] = model
        logger.info(f"Model stored: {model.model_id}")
        return True
    
    def get(self, model_id: str) -> Optional[WeightedDistributionModel]:
        """모델 조회"""
        return self.models.get(model_id)
    
    def get_active_model(self) -> Optional[WeightedDistributionModel]:
        """활성 모델 조회"""
        return self.models.get(self.active_model_id)
    
    def set_active_model(self, model_id: str) -> bool:
        """활성 모델 설정"""
        if model_id not in self.models:
            return False
        self.active_model_id = model_id
        return True
    
    def list_models(self) -> List[Dict]:
        """모델 목록"""
        return [
            {
                'model_id': m.model_id,
                'name': m.name,
                'domains': len(m.domains),
                'is_active': m.model_id == self.active_model_id
            }
            for m in self.models.values()
        ]


class AllocationCalculator:
    """4200: 배분 연산부
    가중 분배 모델에 따라 영역별 배분량 산출
    """
    
    def __init__(self):
        self.calculation_history: List[AllocationResult] = []
    
    def allocate(self, total_resource: float, 
                 model: WeightedDistributionModel,
                 current_weights: np.ndarray = None) -> AllocationResult:
        """[수학식 2] 경계 조건 기반 배분 연산
        
        Alloc(R, W, B) → A
        
        초기 배분: Aᵢ = R × wᵢ
        경계 검증 및 조정: clamp to [Lᵢ, Uᵢ]
        재정규화: A'ᵢ = Aᵢ × (R / Σ Aⱼ)
        """
        weights = current_weights if current_weights is not None else model.weights
        
        # 초기 배분
        allocations = total_resource * weights
        
        # 경계 조건 클램핑
        allocations, clamped = self._apply_boundary_constraints(
            allocations, total_resource, model
        )
        
        # 재정규화
        allocations = self._normalize(allocations, total_resource)
        
        # 우선순위 기반 재배분 (필요시)
        if not np.isclose(allocations.sum(), total_resource, atol=0.01):
            allocations = self._priority_redistribute(
                allocations, total_resource, model
            )
        
        # 결과 생성
        allocation_dict = {
            domain.domain_id: float(allocations[i])
            for i, domain in enumerate(model.domains)
        }
        
        result = AllocationResult(
            allocation_id=str(uuid.uuid4()),
            model_id=model.model_id,
            total_resource=total_resource,
            allocations=allocation_dict,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                'weights_used': weights.tolist(),
                'clamped_domains': clamped
            }
        )
        
        self.calculation_history.append(result)
        return result
    
    def _apply_boundary_constraints(self, allocations: np.ndarray,
                                   total: float,
                                   model: WeightedDistributionModel
                                   ) -> Tuple[np.ndarray, List[str]]:
        """경계 조건 적용"""
        clamped = []
        
        for i, domain in enumerate(model.domains):
            lower = total * domain.min_weight
            upper = total * domain.max_weight
            
            if allocations[i] < lower:
                allocations[i] = lower
                clamped.append(f"{domain.domain_id}:lower")
            elif allocations[i] > upper:
                allocations[i] = upper
                clamped.append(f"{domain.domain_id}:upper")
        
        return allocations, clamped
    
    def _normalize(self, allocations: np.ndarray, total: float) -> np.ndarray:
        """정규화"""
        current_sum = allocations.sum()
        if current_sum > 0 and not np.isclose(current_sum, total):
            allocations = allocations * (total / current_sum)
        return allocations
    
    def _priority_redistribute(self, allocations: np.ndarray,
                               total: float,
                               model: WeightedDistributionModel) -> np.ndarray:
        """[수학식 4] 우선순위 기반 재배분
        
        초과 시: 우선순위 낮은 영역부터 감축
        부족 시: 우선순위 높은 영역부터 증가
        """
        gap = total - allocations.sum()
        
        if abs(gap) < 0.001:
            return allocations
        
        priorities = model.priorities
        
        if gap < 0:  # 초과 - 낮은 우선순위부터 감축
            sorted_indices = np.argsort(-priorities)  # 우선순위 낮은 것 먼저
            excess = abs(gap)
            
            for i in sorted_indices:
                reducible = allocations[i] - total * model.domains[i].min_weight
                if reducible > 0:
                    reduction = min(reducible, excess)
                    allocations[i] -= reduction
                    excess -= reduction
                    if excess <= 0:
                        break
        
        else:  # 부족 - 높은 우선순위부터 증가
            sorted_indices = np.argsort(priorities)  # 우선순위 높은 것 먼저
            shortage = gap
            
            for i in sorted_indices:
                expandable = total * model.domains[i].max_weight - allocations[i]
                if expandable > 0:
                    expansion = min(expandable, shortage)
                    allocations[i] += expansion
                    shortage -= expansion
                    if shortage <= 0:
                        break
        
        return allocations


class ConsumptionMonitor:
    """4300: 소비 모니터링부
    각 영역의 실제 자원 소비량 실시간 모니터링
    """
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self.consumption_history: Dict[str, List[float]] = {}
        self.deviation_history: List[Dict] = []
    
    def record_consumption(self, domain_id: str, consumption: float):
        """소비량 기록"""
        if domain_id not in self.consumption_history:
            self.consumption_history[domain_id] = []
        
        self.consumption_history[domain_id].append(consumption)
        
        # 윈도우 크기 유지
        if len(self.consumption_history[domain_id]) > self.window_size:
            self.consumption_history[domain_id].pop(0)
    
    def get_average_consumption(self, domain_id: str) -> float:
        """평균 소비량 조회 (슬라이딩 윈도우)"""
        history = self.consumption_history.get(domain_id, [])
        return float(np.mean(history)) if history else 0.0
    
    def calculate_deviation(self, allocations: Dict[str, float],
                           consumptions: Dict[str, float]) -> Dict[str, Dict]:
        """[수학식 3] 편차 산출
        
        Δᵢ(t) = Consumedᵢ(t) - Allocatedᵢ(t)
        Δ_ratio(t) = Δᵢ(t) / Allocatedᵢ(t)
        """
        deviations = {}
        
        for domain_id, allocated in allocations.items():
            consumed = consumptions.get(domain_id, 0)
            
            delta = consumed - allocated
            delta_ratio = delta / allocated if allocated > 0 else 0
            
            deviations[domain_id] = {
                'allocated': allocated,
                'consumed': consumed,
                'delta': delta,
                'delta_ratio': delta_ratio
            }
            
            # 소비 기록
            self.record_consumption(domain_id, consumed)
        
        self.deviation_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'deviations': deviations
        })
        
        return deviations


class DynamicAdjuster:
    """4400: 동적 조정부
    편차 기반 배분 비율 동적 조정
    """
    
    def __init__(self, 
                 sensitivity: float = 0.1,      # α: 조정 민감도
                 trigger_threshold: float = 0.2, # θ: 트리거 임계치
                 max_adjustment: float = 0.1):   # δ_max: 최대 조정량
        self.alpha = sensitivity
        self.theta_trigger = trigger_threshold
        self.delta_max = max_adjustment
        self.adjustment_history: List[Dict] = []
    
    def should_adjust(self, deviations: Dict[str, Dict]) -> bool:
        """조정 필요 여부 판단"""
        for domain_id, dev in deviations.items():
            if abs(dev['delta_ratio']) > self.theta_trigger:
                return True
        return False
    
    def calculate_adjustments(self, current_weights: np.ndarray,
                             deviations: Dict[str, Dict],
                             model: WeightedDistributionModel) -> np.ndarray:
        """[수학식 3] 동적 조정 함수
        
        δwᵢ = α × sign(Δᵢ) × min(|Δ_ratioᵢ|, δ_max)
        """
        adjustments = np.zeros(len(current_weights))
        domain_ids = [d.domain_id for d in model.domains]
        
        for i, domain_id in enumerate(domain_ids):
            if domain_id not in deviations:
                continue
            
            delta_ratio = deviations[domain_id]['delta_ratio']
            
            if abs(delta_ratio) > self.theta_trigger:
                direction = np.sign(delta_ratio)
                magnitude = min(abs(delta_ratio) * self.alpha, self.delta_max)
                adjustments[i] = direction * magnitude
        
        # 영합 조정 (Zero-Sum Adjustment)
        adjustments = self._zero_sum_adjustment(adjustments)
        
        return adjustments
    
    def _zero_sum_adjustment(self, adjustments: np.ndarray) -> np.ndarray:
        """영합 조정: 증가분 합 = 감소분 합"""
        positive_sum = np.sum(adjustments[adjustments > 0])
        negative_sum = abs(np.sum(adjustments[adjustments < 0]))
        
        if positive_sum == 0 or negative_sum == 0:
            return adjustments
        
        if positive_sum > negative_sum:
            scale = negative_sum / positive_sum
            adjustments[adjustments > 0] *= scale
        else:
            scale = positive_sum / negative_sum
            adjustments[adjustments < 0] *= scale
        
        return adjustments
    
    def apply_adjustments(self, current_weights: np.ndarray,
                         adjustments: np.ndarray,
                         model: WeightedDistributionModel) -> np.ndarray:
        """조정 적용"""
        new_weights = current_weights + adjustments
        
        # 경계 조건 적용
        for i, domain in enumerate(model.domains):
            new_weights[i] = np.clip(new_weights[i], domain.min_weight, domain.max_weight)
        
        # 정규화
        if new_weights.sum() > 0:
            new_weights = new_weights / new_weights.sum()
        
        self.adjustment_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'before': current_weights.tolist(),
            'adjustments': adjustments.tolist(),
            'after': new_weights.tolist()
        })
        
        return new_weights


class AnalyticsUnit:
    """4500: 분석부
    배분 이력 및 효율성 지표 분석
    """
    
    def __init__(self):
        self.metrics_history: List[Dict] = []
    
    def calculate_fairness_index(self, allocations: np.ndarray) -> float:
        """[수학식 6] Jain's Fairness Index
        
        F(A) = (Σᵢ Aᵢ)² / (n × Σᵢ Aᵢ²)
        
        범위: 1/n ≤ F ≤ 1.0
        F = 1.0: 완전 균등
        """
        n = len(allocations)
        if n == 0 or np.sum(allocations ** 2) == 0:
            return 0.0
        
        return float((np.sum(allocations) ** 2) / (n * np.sum(allocations ** 2)))
    
    def calculate_weighted_fairness(self, allocations: np.ndarray,
                                   target_weights: np.ndarray) -> float:
        """가중 공정성 지표 (목표 대비)
        
        F_weighted = 1 - Σᵢ |Aᵢ/R - wᵢ| / 2
        """
        total = np.sum(allocations)
        if total == 0:
            return 0.0
        
        actual_ratios = allocations / total
        deviation = np.sum(np.abs(actual_ratios - target_weights))
        
        return float(1 - deviation / 2)
    
    def analyze_efficiency(self, allocation_history: List[AllocationResult],
                          consumption_history: List[Dict]) -> Dict:
        """효율성 분석"""
        if not allocation_history or not consumption_history:
            return {'efficiency': 0.0, 'utilization': 0.0}
        
        # 최근 배분
        recent_allocation = allocation_history[-1]
        total_allocated = sum(recent_allocation.allocations.values())
        
        # 최근 소비
        if consumption_history:
            recent_consumption = consumption_history[-1].get('deviations', {})
            total_consumed = sum(d['consumed'] for d in recent_consumption.values())
        else:
            total_consumed = 0
        
        utilization = total_consumed / total_allocated if total_allocated > 0 else 0
        
        # 편차 기반 효율성
        if recent_consumption:
            avg_abs_deviation = np.mean([
                abs(d['delta_ratio']) for d in recent_consumption.values()
            ])
            efficiency = 1 - min(avg_abs_deviation, 1.0)
        else:
            efficiency = 1.0
        
        metrics = {
            'efficiency': float(efficiency),
            'utilization': float(utilization),
            'total_allocated': total_allocated,
            'total_consumed': total_consumed
        }
        
        self.metrics_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **metrics
        })
        
        return metrics


class WeightedDistributionSystem:
    """가중 분배 모델 기반 다영역 자원 배분 시스템 (통합 - 시스템 4000)"""
    
    def __init__(self, base_ratio: List[float] = None):
        # 서브시스템 초기화
        self.repository = ModelRepository()      # 4100
        self.calculator = AllocationCalculator() # 4200
        self.monitor = ConsumptionMonitor()      # 4300
        self.adjuster = DynamicAdjuster()        # 4400
        self.analytics = AnalyticsUnit()         # 4500
        
        # 현재 가중치
        self.current_weights: Optional[np.ndarray] = None
        
        # 기본 비율 설정
        if base_ratio:
            self._update_default_model(base_ratio)
    
    def _update_default_model(self, base_ratio: List[float]):
        """기본 모델 업데이트"""
        model = self.repository.get_active_model()
        if model and len(base_ratio) == len(model.domains):
            for i, domain in enumerate(model.domains):
                domain.base_weight = base_ratio[i]
            self.current_weights = np.array(base_ratio)
    
    def distribute(self, total_value: float) -> Dict:
        """자원 배분 실행"""
        model = self.repository.get_active_model()
        if not model:
            return {'error': 'No active model'}
        
        # 현재 가중치 사용 또는 기본 가중치
        weights = self.current_weights if self.current_weights is not None else model.weights
        
        # 배분 계산
        result = self.calculator.allocate(total_value, model, weights)
        
        return result.allocations
    
    def update_with_consumption(self, consumptions: Dict[str, float]) -> Dict:
        """소비 데이터로 업데이트 및 조정"""
        model = self.repository.get_active_model()
        if not model:
            return {'adjusted': False}
        
        # 최근 배분 조회
        if not self.calculator.calculation_history:
            return {'adjusted': False}
        
        last_allocation = self.calculator.calculation_history[-1]
        
        # 편차 계산
        deviations = self.monitor.calculate_deviation(
            last_allocation.allocations, consumptions
        )
        
        # 조정 필요 여부 확인
        if not self.adjuster.should_adjust(deviations):
            return {'adjusted': False, 'deviations': deviations}
        
        # 조정량 계산
        current = self.current_weights if self.current_weights is not None else model.weights
        adjustments = self.adjuster.calculate_adjustments(current, deviations, model)
        
        # 조정 적용
        self.current_weights = self.adjuster.apply_adjustments(current, adjustments, model)
        
        return {
            'adjusted': True,
            'new_weights': self.current_weights.tolist(),
            'deviations': deviations
        }
    
    def get_analytics(self) -> Dict:
        """분석 데이터 조회"""
        model = self.repository.get_active_model()
        if not model:
            return {}
        
        weights = self.current_weights if self.current_weights is not None else model.weights
        
        # 최근 배분 기반 분석
        if self.calculator.calculation_history:
            allocations = list(self.calculator.calculation_history[-1].allocations.values())
            fairness = self.analytics.calculate_fairness_index(np.array(allocations))
            weighted_fairness = self.analytics.calculate_weighted_fairness(
                np.array(allocations), weights
            )
        else:
            fairness = 1.0
            weighted_fairness = 1.0
        
        efficiency = self.analytics.analyze_efficiency(
            self.calculator.calculation_history,
            self.monitor.deviation_history
        )
        
        return {
            'fairness_index': fairness,
            'weighted_fairness': weighted_fairness,
            'current_weights': weights.tolist(),
            **efficiency
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        return {
            'models_count': len(self.repository.models),
            'allocations_count': len(self.calculator.calculation_history),
            'adjustments_count': len(self.adjuster.adjustment_history),
            'current_weights': self.current_weights.tolist() if self.current_weights is not None else None
        }


# 하위 호환성을 위한 별칭
class WeightedDistributor(WeightedDistributionSystem):
    """하위 호환성 래퍼"""
    
    def __init__(self, base_ratio: List[float] = None):
        super().__init__(base_ratio)
        self.base_ratio = base_ratio or [0.33, 0.34, 0.33]
        self.current_ratio = self.base_ratio.copy()
        self.history: List[Dict] = []
        self.total_distributed = 0.0
    
    def distribute(self, total_value: float) -> Dict:
        """가치 분배 (하위 호환성)"""
        # 부모 클래스 호출
        result = super().distribute(total_value)
        
        # 하위 호환성 형식으로 변환
        if 'error' in result:
            # 폴백
            distribution = {
                'public': total_value * self.current_ratio[0],
                'productive': total_value * self.current_ratio[1],
                'individual': total_value * self.current_ratio[2]
            }
        else:
            distribution = {
                'public': result.get('public', total_value * self.current_ratio[0]),
                'productive': result.get('productive', total_value * self.current_ratio[1]),
                'individual': result.get('individual', total_value * self.current_ratio[2])
            }
        
        record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input_value': total_value,
            'ratio_used': self.current_ratio.copy(),
            'distribution': distribution,
            'total': sum(distribution.values())
        }
        
        self.history.append(record)
        self.total_distributed += total_value
        
        return distribution
    
    def update_ratio(self, new_ratio: List[float]):
        """분배 비율 업데이트"""
        if len(new_ratio) != 3:
            raise ValueError("비율은 3개 요소가 필요합니다")
        
        total = sum(new_ratio)
        if not np.isclose(total, 1.0, atol=0.01):
            new_ratio = [r / total for r in new_ratio]
        
        self.current_ratio = new_ratio
        self.current_weights = np.array(new_ratio)
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환 (하위 호환성)"""
        if not self.history:
            return {'count': 0, 'total_distributed': 0}
        
        public_total = sum(h['distribution']['public'] for h in self.history)
        productive_total = sum(h['distribution']['productive'] for h in self.history)
        individual_total = sum(h['distribution']['individual'] for h in self.history)
        
        return {
            'count': len(self.history),
            'total_distributed': self.total_distributed,
            'public_total': public_total,
            'productive_total': productive_total,
            'individual_total': individual_total,
            'current_ratio': self.current_ratio,
            **super().get_statistics()
        }
