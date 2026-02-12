"""특허 3: 신호 자산화 통합 플랫폼
Signal Assetization Integrated Platform

시스템 구성:
- 1100: 신호 수집 계층 (이종 신호 통합 수집)
- 1200: 신호 정규화 엔진 (Signal Object 변환)
- 1300: 가치 산출 엔진 (Asset Object 생성)
- 1400: 출력 어댑터 계층 (다양한 형태 변환)
- 1500: 무결성 관리부 (처리 이력 및 검증)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """신호 원천 유형"""
    TEXT = "text"
    SENSOR = "sensor"
    BEHAVIOR = "behavior"
    EVENT = "event"


class OutputFormat(Enum):
    """출력 형식"""
    JSON = "json"
    CSV = "csv"
    BINARY = "binary"
    STREAM = "stream"


@dataclass
class SignalObject:
    """신호 객체 (Signal Object)"""
    signal_id: str
    source_type: SourceType
    timestamp: str
    payload: List[float]  # 정규화된 벡터
    metadata: Dict = field(default_factory=dict)
    context: Dict = field(default_factory=dict)
    
    @classmethod
    def create(cls, source_type: SourceType, payload: List[float], 
               domain: str = "", tags: List[str] = None) -> 'SignalObject':
        return cls(
            signal_id=str(uuid.uuid4()),
            source_type=source_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            payload=payload,
            metadata={
                'original_format': 'vector',
                'preprocessing_applied': [],
                'quality_score': 0.0
            },
            context={
                'domain': domain,
                'relevance_tags': tags or []
            }
        )


@dataclass  
class AssetObject:
    """자산 객체 (Asset Object)"""
    asset_id: str
    source_signals: List[str]
    value_vector: List[float]  # [V₁, V₂, V₃]
    total_value: float
    confidence: float
    creation_timestamp: str
    validity_period: str  # ISO 8601 duration
    domain_values: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def create(cls, signals: List[SignalObject], value_vector: List[float],
               total_value: float, confidence: float, 
               validity_hours: int = 24) -> 'AssetObject':
        return cls(
            asset_id=str(uuid.uuid4()),
            source_signals=[s.signal_id for s in signals],
            value_vector=value_vector,
            total_value=total_value,
            confidence=confidence,
            creation_timestamp=datetime.now(timezone.utc).isoformat(),
            validity_period=f"PT{validity_hours}H"
        )


class SignalCollector:
    """1100: 신호 수집 계층
    이종 신호 통합 수집
    """
    
    def __init__(self):
        self.collected_signals: List[SignalObject] = []
        self.collection_stats: Dict[str, int] = {t.value: 0 for t in SourceType}
    
    def collect(self, raw_data: Any, source_type: SourceType = None,
                domain: str = "", tags: List[str] = None) -> SignalObject:
        """신호 수집 및 기본 변환"""
        if source_type is None:
            source_type = self._detect_source_type(raw_data)
        
        # 페이로드 추출
        payload = self._extract_payload(raw_data, source_type)
        
        signal = SignalObject.create(source_type, payload, domain, tags)
        self.collected_signals.append(signal)
        self.collection_stats[source_type.value] += 1
        
        return signal
    
    def _detect_source_type(self, data: Any) -> SourceType:
        """원천 유형 자동 감지"""
        if isinstance(data, str):
            return SourceType.TEXT
        elif isinstance(data, dict):
            if 'sensor' in str(data).lower() or 'temperature' in data:
                return SourceType.SENSOR
            elif 'user' in str(data).lower() or 'action' in data:
                return SourceType.BEHAVIOR
            else:
                return SourceType.EVENT
        else:
            return SourceType.SENSOR
    
    def _extract_payload(self, data: Any, source_type: SourceType) -> List[float]:
        """데이터에서 페이로드 추출"""
        if isinstance(data, (list, np.ndarray)):
            return [float(x) for x in data]
        elif isinstance(data, dict):
            values = [v for v in data.values() if isinstance(v, (int, float))]
            return values if values else [0.0]
        elif isinstance(data, (int, float)):
            return [float(data)]
        elif isinstance(data, str):
            # 텍스트는 해시 기반 벡터로 변환
            hash_bytes = hashlib.sha256(data.encode()).digest()
            return [b / 255.0 for b in hash_bytes[:16]]
        else:
            return [0.0]


class SignalNormalizer:
    """1200: 신호 정규화 엔진
    Signal Object로 표준화 변환
    """
    
    def __init__(self, completeness_weight: float = 0.3,
                 accuracy_weight: float = 0.4,
                 freshness_weight: float = 0.3,
                 decay_lambda: float = 0.1):
        self.w_c = completeness_weight
        self.w_a = accuracy_weight
        self.w_f = freshness_weight
        self.lambda_decay = decay_lambda
    
    def normalize(self, signal: SignalObject) -> SignalObject:
        """신호 정규화 및 품질 점수 계산"""
        # 페이로드 정규화
        payload = np.array(signal.payload)
        if payload.size > 0 and np.max(np.abs(payload)) > 0:
            normalized_payload = payload / np.max(np.abs(payload))
        else:
            normalized_payload = payload
        
        signal.payload = normalized_payload.tolist()
        
        # [수학식 1] 품질 점수 계산
        quality = self.calculate_quality_score(signal)
        signal.metadata['quality_score'] = quality
        signal.metadata['preprocessing_applied'].append('normalization')
        
        return signal
    
    def calculate_quality_score(self, signal: SignalObject) -> float:
        """[수학식 1] 신호 품질 점수 Q(s)
        
        Q(s) = w_c × C(s) + w_a × A(s) + w_f × F(s)
        
        - C(s): 완전성 = 채워진 필수 필드 / 전체 필수 필드
        - A(s): 정확성 = 유효 범위 내 값 / 전체 값
        - F(s): 신선도 = exp(-λ × Δt)
        """
        # C(s): 완전성
        required_fields = ['signal_id', 'source_type', 'timestamp', 'payload']
        filled = sum(1 for f in required_fields if getattr(signal, f, None) is not None)
        C = filled / len(required_fields)
        
        # A(s): 정확성 (페이로드 값의 유효성)
        payload = np.array(signal.payload)
        if payload.size > 0:
            valid_values = np.sum((payload >= -1) & (payload <= 1))
            A = valid_values / payload.size
        else:
            A = 0.0
        
        # F(s): 신선도
        try:
            created = datetime.fromisoformat(signal.timestamp.replace('Z', '+00:00'))
            delta_t = (datetime.now(timezone.utc) - created).total_seconds() / 3600  # 시간 단위
            F = np.exp(-self.lambda_decay * delta_t)
        except (ValueError, TypeError):
            F = 1.0
        
        return self.w_c * C + self.w_a * A + self.w_f * F


class ValueCalculator:
    """1300: 가치 산출 엔진
    가치 정량화 → Asset Object 생성
    """
    
    def __init__(self, quality_weight: float = 0.25,
                 relevance_weight: float = 0.30,
                 scarcity_weight: float = 0.20,
                 timeliness_weight: float = 0.25,
                 gamma: float = 1.0):
        self.weights = [quality_weight, relevance_weight, scarcity_weight, timeliness_weight]
        self.gamma = gamma  # 비선형 조정 계수
        self.signal_pool: List[SignalObject] = []
        self.domain_vectors: Dict[str, np.ndarray] = {}
    
    def set_domain_vector(self, domain: str, vector: np.ndarray):
        """도메인 특징 벡터 설정"""
        self.domain_vectors[domain] = vector / np.linalg.norm(vector) if np.linalg.norm(vector) > 0 else vector
    
    def add_to_pool(self, signal: SignalObject):
        """신호 풀에 추가"""
        self.signal_pool.append(signal)
    
    def calculate_relevance(self, signal: SignalObject, domain: str = None) -> float:
        """[수학식 2] 관련성 점수 R(s, d)
        
        R(s, d) = cos(V_s, V_d) = (V_s · V_d) / (||V_s|| × ||V_d||)
        """
        if domain is None:
            domain = signal.context.get('domain', '')
        
        if domain not in self.domain_vectors:
            return 0.5  # 기본값
        
        V_s = np.array(signal.payload)
        V_d = self.domain_vectors[domain]
        
        # 차원 맞추기
        min_len = min(len(V_s), len(V_d))
        V_s, V_d = V_s[:min_len], V_d[:min_len]
        
        norm_s, norm_d = np.linalg.norm(V_s), np.linalg.norm(V_d)
        if norm_s == 0 or norm_d == 0:
            return 0.0
        
        cos_sim = np.dot(V_s, V_d) / (norm_s * norm_d)
        return (cos_sim + 1) / 2  # 0~1 범위로 정규화
    
    def calculate_scarcity(self, signal: SignalObject, similarity_threshold: float = 0.8) -> float:
        """[수학식 3] 희소성 점수 Sc(s)
        
        Sc(s) = 1 - (n_similar / N_total)
        """
        if not self.signal_pool:
            return 1.0
        
        V_s = np.array(signal.payload)
        n_similar = 0
        
        for other in self.signal_pool:
            if other.signal_id == signal.signal_id:
                continue
            V_other = np.array(other.payload)
            
            min_len = min(len(V_s), len(V_other))
            if min_len == 0:
                continue
                
            cos_sim = np.dot(V_s[:min_len], V_other[:min_len])
            norm_product = np.linalg.norm(V_s[:min_len]) * np.linalg.norm(V_other[:min_len])
            
            if norm_product > 0:
                similarity = cos_sim / norm_product
                if similarity >= similarity_threshold:
                    n_similar += 1
        
        return 1 - (n_similar / len(self.signal_pool))
    
    def calculate_timeliness(self, signal: SignalObject, 
                            event_time: datetime = None,
                            peak_window: float = 1.0,
                            alpha: float = 0.1) -> float:
        """[수학식 4] 시의성 점수 T(s)
        
        T(s) = σ(α × (t_peak - |t_s - t_event|))
        σ(x) = 1 / (1 + exp(-x))
        """
        if event_time is None:
            return 0.5  # 기본값
        
        try:
            t_s = datetime.fromisoformat(signal.timestamp.replace('Z', '+00:00'))
            delta = abs((t_s - event_time).total_seconds() / 3600)  # 시간 단위
            x = alpha * (peak_window - delta)
            return 1 / (1 + np.exp(-x))
        except (ValueError, TypeError):
            return 0.5
    
    def calculate_total_value(self, signal: SignalObject, domain: str = None) -> Tuple[float, List[float]]:
        """[수학식 5] 종합 가치 산출
        
        V_total(s) = Σᵢ (wᵢ × Fᵢ(s))^γ
        """
        Q = signal.metadata.get('quality_score', 0.5)
        R = self.calculate_relevance(signal, domain)
        Sc = self.calculate_scarcity(signal)
        T = self.calculate_timeliness(signal)
        
        factors = [Q, R, Sc, T]
        
        # 가중 합산 (γ 적용)
        V_total = sum(
            (w * f) ** self.gamma 
            for w, f in zip(self.weights, factors)
        )
        
        return V_total, factors
    
    def calculate_confidence(self, signal: SignalObject, factors: List[float]) -> float:
        """[수학식 7] 가치 산출 신뢰도
        
        Conf(s) = min(Q(s), σ_data, σ_model)
        """
        Q = signal.metadata.get('quality_score', 0.5)
        
        # σ_data: 데이터 안정성 (표준편차 기반)
        payload = np.array(signal.payload)
        if len(payload) > 1:
            max_std = 0.5  # 예상 최대 표준편차
            sigma_data = 1 - min(np.std(payload) / max_std, 1.0)
        else:
            sigma_data = 0.5
        
        # σ_model: 모델 일치도 (여기서는 단순화)
        sigma_model = np.mean(factors) if factors else 0.5
        
        return min(Q, sigma_data, sigma_model)
    
    def calculate_validity_period(self, signal: SignalObject, 
                                  base_hours: int = 24,
                                  scarcity_weight: float = 0.5) -> int:
        """[수학식 8] 자산 유효 기간
        
        T_valid(s) = T_base × (1 + β × Sc(s)) × F(s)
        """
        Sc = self.calculate_scarcity(signal)
        F = signal.metadata.get('quality_score', 0.5)  # 신선도 근사
        
        T_valid = base_hours * (1 + scarcity_weight * Sc) * F
        return max(1, int(T_valid))
    
    def create_asset(self, signals: List[SignalObject], domain: str = None) -> AssetObject:
        """자산 객체 생성"""
        if not signals:
            raise ValueError("At least one signal required")
        
        # 단일 신호 처리
        if len(signals) == 1:
            signal = signals[0]
            total_value, factors = self.calculate_total_value(signal, domain)
            confidence = self.calculate_confidence(signal, factors)
            validity = self.calculate_validity_period(signal)
            
            return AssetObject.create(
                signals=signals,
                value_vector=factors,
                total_value=total_value,
                confidence=confidence,
                validity_hours=validity
            )
        
        # 복수 신호: 시너지 가치 계산 [수학식 9]
        individual_values = []
        all_factors = []
        
        for signal in signals:
            value, factors = self.calculate_total_value(signal, domain)
            individual_values.append(value)
            all_factors.append(factors)
        
        # 기본 집계
        V_agg = np.mean(individual_values)
        
        # 시너지 계산: V_synergy = α × Σᵢⱼ (1 - sim(sᵢ, sⱼ)) × min(V(sᵢ), V(sⱼ))
        synergy_alpha = 0.2
        V_synergy = 0.0
        
        for i in range(len(signals)):
            for j in range(i + 1, len(signals)):
                V_i = np.array(signals[i].payload)
                V_j = np.array(signals[j].payload)
                min_len = min(len(V_i), len(V_j))
                
                if min_len > 0:
                    norm_i, norm_j = np.linalg.norm(V_i[:min_len]), np.linalg.norm(V_j[:min_len])
                    if norm_i > 0 and norm_j > 0:
                        sim = np.dot(V_i[:min_len], V_j[:min_len]) / (norm_i * norm_j)
                        V_synergy += (1 - sim) * min(individual_values[i], individual_values[j])
        
        V_synergy *= synergy_alpha
        total_value = V_agg + V_synergy
        
        # 평균 팩터 및 신뢰도
        avg_factors = np.mean(all_factors, axis=0).tolist()
        avg_confidence = np.mean([
            self.calculate_confidence(s, f) 
            for s, f in zip(signals, all_factors)
        ])
        
        return AssetObject.create(
            signals=signals,
            value_vector=avg_factors,
            total_value=total_value,
            confidence=avg_confidence,
            validity_hours=24
        )


class OutputAdapter:
    """1400: 출력 어댑터 계층
    다양한 형태로 변환 출력
    """
    
    def adapt(self, asset: AssetObject, format: OutputFormat = OutputFormat.JSON) -> Any:
        """자산을 지정된 형식으로 변환"""
        if format == OutputFormat.JSON:
            return self._to_json(asset)
        elif format == OutputFormat.CSV:
            return self._to_csv(asset)
        elif format == OutputFormat.BINARY:
            return self._to_binary(asset)
        else:
            return self._to_json(asset)
    
    def _to_json(self, asset: AssetObject) -> Dict:
        """JSON 형식 변환"""
        return {
            'asset_id': asset.asset_id,
            'source_signals': asset.source_signals,
            'value_vector': asset.value_vector,
            'total_value': asset.total_value,
            'confidence': asset.confidence,
            'creation_timestamp': asset.creation_timestamp,
            'validity_period': asset.validity_period,
            'domain_values': asset.domain_values
        }
    
    def _to_csv(self, asset: AssetObject) -> str:
        """CSV 형식 변환"""
        headers = ['asset_id', 'total_value', 'confidence', 'validity_period']
        values = [asset.asset_id, asset.total_value, asset.confidence, asset.validity_period]
        return ','.join(headers) + '\n' + ','.join(str(v) for v in values)
    
    def _to_binary(self, asset: AssetObject) -> bytes:
        """바이너리 형식 변환"""
        import json
        return json.dumps(self._to_json(asset)).encode('utf-8')


class IntegrityManager:
    """1500: 무결성 관리부
    처리 이력 및 무결성 검증
    """
    
    def __init__(self):
        self.processing_log: List[Dict] = []
        self.asset_registry: Dict[str, AssetObject] = {}
    
    def log_processing(self, signal: SignalObject, asset: AssetObject, 
                      operation: str = "create"):
        """처리 이력 기록"""
        self.processing_log.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'operation': operation,
            'signal_id': signal.signal_id,
            'asset_id': asset.asset_id,
            'checksum': self._calculate_checksum(asset)
        })
        
        if operation == "create":
            self.asset_registry[asset.asset_id] = asset
    
    def _calculate_checksum(self, asset: AssetObject) -> str:
        """체크섬 계산"""
        data = f"{asset.asset_id}{asset.total_value}{asset.confidence}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def verify_integrity(self, asset_id: str) -> bool:
        """무결성 검증"""
        if asset_id not in self.asset_registry:
            return False
        
        asset = self.asset_registry[asset_id]
        current_checksum = self._calculate_checksum(asset)
        
        # 로그에서 원본 체크섬 찾기
        for log in reversed(self.processing_log):
            if log['asset_id'] == asset_id:
                return log['checksum'] == current_checksum
        
        return False
    
    def reevaluate_asset(self, asset: AssetObject, 
                        decay_lambda: float = 0.01) -> float:
        """[알고리즘 3] 가치 재평가 (시간 경과)
        
        V_updated = V × exp(-λ × Δt)
        """
        try:
            created = datetime.fromisoformat(asset.creation_timestamp.replace('Z', '+00:00'))
            delta_t = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            decay_factor = np.exp(-decay_lambda * delta_t)
            return asset.total_value * decay_factor
        except (ValueError, TypeError):
            return asset.total_value


class SignalAssetizationPlatform:
    """신호 자산화 통합 플랫폼 (통합)"""
    
    def __init__(self, sigma: List[float] = None):
        self.sigma = sigma or [0.33, 0.34, 0.33]
        
        self.collector = SignalCollector()
        self.normalizer = SignalNormalizer()
        self.calculator = ValueCalculator()
        self.adapter = OutputAdapter()
        self.integrity = IntegrityManager()
        
        self.total_value = 0.0
        self.assets: List[AssetObject] = []
    
    def process_signal(self, signal_value: Any, domain: str = "") -> Dict:
        """신호를 자산 가치로 변환 (하위 호환성)"""
        # 1. 수집
        signal = self.collector.collect(signal_value, domain=domain)
        
        # 2. 정규화
        signal = self.normalizer.normalize(signal)
        
        # 3. 풀에 추가
        self.calculator.add_to_pool(signal)
        
        # 4. 가치 산출
        asset = self.calculator.create_asset([signal], domain)
        
        # 5. 무결성 로깅
        self.integrity.log_processing(signal, asset)
        
        # 6. 기록
        self.assets.append(asset)
        self.total_value += asset.total_value
        
        # 7. 출력 형식 변환
        output = self.adapter.adapt(asset)
        
        # 하위 호환성을 위한 반환 형식
        return {
            'id': len(self.assets),
            'timestamp': asset.creation_timestamp,
            'signal': signal_value if isinstance(signal_value, (int, float)) else 0,
            'value': asset.total_value,
            'multiplier': 1.0 + (asset.total_value * 0.1),
            'quality_score': signal.metadata.get('quality_score', 0),
            'asset': output
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        if not self.assets:
            return {'count': 0, 'total_value': 0, 'average': 0}
        
        values = [a.total_value for a in self.assets]
        return {
            'count': len(self.assets),
            'total_value': self.total_value,
            'average': float(np.mean(values)),
            'max': float(max(values)),
            'min': float(min(values)),
            'collection_stats': self.collector.collection_stats
        }


# 하위 호환성을 위한 별칭
SignalAssetizer = SignalAssetizationPlatform
