"""특허 2: 재귀적 모듈화를 이용한 다단계 신호 전처리 시스템
Multi-stage Signal Preprocessing System Using Recursive Modularization

시스템 구성:
- 310: 벡터 변환부 (n차원 특성 벡터 변환)
- 320: 정합성 판별부 (코사인 유사도 기반)
- 330: 재모듈화 처리부 (재귀적 분해/재분류)
- 340: 정제 처리부 (PCA/ICA 핵심 성분 추출)
- 350: 모듈 생성부 (특성별 모듈화 및 태그 부여)
- 360: 적응형 분류 장치 (미분류 패턴 학습)
"""
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """신호 유형"""
    TEXT = "text"
    SENSOR = "sensor"
    BEHAVIOR = "behavior"
    EVENT = "event"
    UNKNOWN = "unknown"


class ConformanceStatus(Enum):
    """정합성 상태"""
    CONFORMING = "conforming"        # 정합
    NON_CONFORMING = "non_conforming"  # 비정합
    UNCLASSIFIED = "unclassified"    # 미분류


@dataclass
class SignalModule:
    """신호 모듈 (처리 결과 단위)"""
    module_id: str
    signal_type: SignalType
    conformance_status: ConformanceStatus
    feature_vector: List[float]
    conformance_index: float
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    sub_modules: List['SignalModule'] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class VectorTransformer:
    """310: 벡터 변환부
    신호 데이터를 n차원 특성 벡터로 변환
    """
    
    def __init__(self, dimension: int = 64):
        self.dimension = dimension
        self.transform_history: List[Dict] = []
    
    def transform(self, signal: Any, signal_type: SignalType = None) -> Tuple[np.ndarray, SignalType]:
        """신호를 특성 벡터로 변환"""
        if signal_type is None:
            signal_type = self._detect_type(signal)
        
        if signal_type == SignalType.TEXT:
            vector = self._transform_text(signal)
        elif signal_type == SignalType.SENSOR:
            vector = self._transform_sensor(signal)
        elif signal_type == SignalType.BEHAVIOR:
            vector = self._transform_behavior(signal)
        elif signal_type == SignalType.EVENT:
            vector = self._transform_event(signal)
        else:
            vector = self._transform_generic(signal)
        
        # 차원 조정
        if len(vector) < self.dimension:
            vector = np.pad(vector, (0, self.dimension - len(vector)))
        elif len(vector) > self.dimension:
            vector = vector[:self.dimension]
        
        # 정규화
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        self.transform_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'signal_type': signal_type.value,
            'vector_norm': float(np.linalg.norm(vector))
        })
        
        return vector, signal_type
    
    def _detect_type(self, signal: Any) -> SignalType:
        """신호 유형 자동 감지"""
        if isinstance(signal, str):
            return SignalType.TEXT
        elif isinstance(signal, dict):
            if 'sensor_id' in signal or 'temperature' in signal or 'pressure' in signal:
                return SignalType.SENSOR
            elif 'user_id' in signal or 'action' in signal:
                return SignalType.BEHAVIOR
            elif 'event_type' in signal or 'event_id' in signal:
                return SignalType.EVENT
        elif isinstance(signal, (list, np.ndarray)):
            return SignalType.SENSOR
        return SignalType.UNKNOWN
    
    def _transform_text(self, text: str) -> np.ndarray:
        """텍스트 → 벡터 (간단한 해시 기반 임베딩)"""
        # 실제로는 NLP 임베딩 사용 (여기서는 해시 기반 시뮬레이션)
        hash_bytes = hashlib.sha256(text.encode()).digest()
        vector = np.array([b / 255.0 for b in hash_bytes[:self.dimension]])
        return vector
    
    def _transform_sensor(self, data: Any) -> np.ndarray:
        """센서 데이터 → 벡터 (FFT 시뮬레이션)"""
        if isinstance(data, dict):
            values = [v for v in data.values() if isinstance(v, (int, float))]
        elif isinstance(data, (list, np.ndarray)):
            values = list(data)
        else:
            values = [float(data)]
        
        vector = np.array(values, dtype=float)
        # 패딩
        if len(vector) < self.dimension:
            vector = np.pad(vector, (0, self.dimension - len(vector)))
        return vector[:self.dimension]
    
    def _transform_behavior(self, data: Dict) -> np.ndarray:
        """행동 데이터 → 벡터"""
        vector = np.zeros(self.dimension)
        idx = 0
        for key, value in data.items():
            if isinstance(value, (int, float)) and idx < self.dimension:
                vector[idx] = float(value)
                idx += 1
        return vector
    
    def _transform_event(self, data: Dict) -> np.ndarray:
        """이벤트 데이터 → 벡터"""
        return self._transform_behavior(data)
    
    def _transform_generic(self, data: Any) -> np.ndarray:
        """범용 변환"""
        if isinstance(data, (int, float)):
            vector = np.full(self.dimension, float(data) / self.dimension)
        else:
            vector = np.random.rand(self.dimension)
        return vector


class ConformanceChecker:
    """320: 정합성 판별부
    기준 벡터(Σ)와 코사인 유사도로 정합성 판별
    """
    
    def __init__(self, reference_vector: np.ndarray = None, threshold: float = 0.7):
        self.Sigma = reference_vector  # 시스템 기준 벡터
        self.tau = threshold  # 정합성 임계치
        self.check_history: List[Dict] = []
    
    def set_reference(self, reference: np.ndarray):
        """기준 벡터 설정"""
        self.Sigma = reference / np.linalg.norm(reference) if np.linalg.norm(reference) > 0 else reference
    
    def calculate_conformance_index(self, V: np.ndarray) -> float:
        """[수학식] 정합성 지수 계산
        
        S_idx = (V · Σ) / (|V| × |Σ|)
        
        코사인 유사도 (-1 ~ 1)
        """
        if self.Sigma is None:
            return 1.0  # 기준 벡터 없으면 정합으로 처리
        
        V_norm = np.linalg.norm(V)
        Sigma_norm = np.linalg.norm(self.Sigma)
        
        if V_norm == 0 or Sigma_norm == 0:
            return 0.0
        
        return float(np.dot(V, self.Sigma) / (V_norm * Sigma_norm))
    
    def check(self, V: np.ndarray) -> Tuple[ConformanceStatus, float]:
        """정합성 판별
        
        S_idx ≥ τ → 정합 신호 → 정제 처리
        S_idx < τ → 비정합 신호 → 재귀적 재분류
        """
        S_idx = self.calculate_conformance_index(V)
        
        if S_idx >= self.tau:
            status = ConformanceStatus.CONFORMING
        else:
            status = ConformanceStatus.NON_CONFORMING
        
        self.check_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'conformance_index': S_idx,
            'threshold': self.tau,
            'status': status.value
        })
        
        return status, S_idx


class RecursiveRemodulator:
    """330: 재모듈화 처리부
    비정합 신호를 재귀적으로 분해/재분류
    """
    
    def __init__(self, max_depth: int = 5, min_segment_size: int = 2):
        self.max_depth = max_depth
        self.min_segment_size = min_segment_size
        self.remodulation_history: List[Dict] = []
    
    def decompose(self, vector: np.ndarray, depth: int = 0) -> List[np.ndarray]:
        """신호를 하위 신호로 분해"""
        if depth >= self.max_depth or len(vector) < self.min_segment_size * 2:
            return [vector]
        
        # 중간 지점에서 분할
        mid = len(vector) // 2
        return [vector[:mid], vector[mid:]]
    
    def recursive_classify(self, vector: np.ndarray, checker: ConformanceChecker,
                          depth: int = 0) -> List[Tuple[np.ndarray, ConformanceStatus, float]]:
        """재귀적 재분류 알고리즘
        
        Module_k = Classify(N, k) for k = 1, 2, ..., K
        
        if ∃ n ∈ N : Unclassified(n)
            then N' = {n | Unclassified(n)}
            Recurse(N', k+1)
        """
        results = []
        
        # 현재 벡터 판별
        status, S_idx = checker.check(vector)
        
        if status == ConformanceStatus.CONFORMING:
            # 정합 → 결과 반환
            results.append((vector, status, S_idx))
        elif depth >= self.max_depth or len(vector) < self.min_segment_size * 2:
            # 종료 조건: 최대 깊이 도달 또는 더 이상 분해 불가
            results.append((vector, ConformanceStatus.UNCLASSIFIED, S_idx))
        else:
            # 비정합 → 분해 후 재귀 호출
            sub_vectors = self.decompose(vector, depth)
            for sub_v in sub_vectors:
                sub_results = self.recursive_classify(sub_v, checker, depth + 1)
                results.extend(sub_results)
        
        self.remodulation_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'depth': depth,
            'input_size': len(vector),
            'output_count': len(results),
            'status': status.value
        })
        
        return results


class SignalRefiner:
    """340: 정제 처리부
    정합 신호에서 핵심 성분 추출 (PCA/ICA)
    """
    
    def __init__(self, n_components: int = 8):
        self.n_components = n_components
        self.refinement_history: List[Dict] = []
    
    def refine(self, vector: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """핵심 성분 추출 (간단한 PCA 시뮬레이션)"""
        # 실제로는 sklearn PCA 사용
        # 여기서는 상위 n개 성분 추출로 시뮬레이션
        
        # 절대값 기준 상위 성분 인덱스
        abs_values = np.abs(vector)
        top_indices = np.argsort(abs_values)[-self.n_components:]
        
        refined = np.zeros_like(vector)
        refined[top_indices] = vector[top_indices]
        
        # 노이즈 제거율 계산
        original_energy = np.sum(vector ** 2)
        refined_energy = np.sum(refined ** 2)
        retention_rate = refined_energy / original_energy if original_energy > 0 else 1.0
        
        metadata = {
            'original_dim': len(vector),
            'components_retained': self.n_components,
            'energy_retention': float(retention_rate),
            'top_indices': top_indices.tolist()
        }
        
        self.refinement_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            **metadata
        })
        
        return refined, metadata


class ModuleGenerator:
    """350: 모듈 생성부
    특성별 모듈로 구조화 및 태그 부여
    """
    
    def __init__(self):
        self.module_counter = 0
        self.modules: Dict[str, SignalModule] = {}
    
    def generate(self, vector: np.ndarray, signal_type: SignalType,
                 status: ConformanceStatus, S_idx: float,
                 tags: List[str] = None) -> SignalModule:
        """모듈 생성"""
        self.module_counter += 1
        module_id = f"MOD-{self.module_counter:06d}"
        
        module = SignalModule(
            module_id=module_id,
            signal_type=signal_type,
            conformance_status=status,
            feature_vector=vector.tolist(),
            conformance_index=S_idx,
            tags=tags or self._auto_tag(vector, signal_type),
            metadata={
                'vector_norm': float(np.linalg.norm(vector)),
                'vector_mean': float(np.mean(vector)),
                'vector_std': float(np.std(vector))
            }
        )
        
        self.modules[module_id] = module
        return module
    
    def _auto_tag(self, vector: np.ndarray, signal_type: SignalType) -> List[str]:
        """자동 태그 생성"""
        tags = [signal_type.value]
        
        # 벡터 특성 기반 태그
        mean_val = np.mean(vector)
        if mean_val > 0.5:
            tags.append("high_intensity")
        elif mean_val < 0.2:
            tags.append("low_intensity")
        
        std_val = np.std(vector)
        if std_val > 0.3:
            tags.append("high_variance")
        elif std_val < 0.1:
            tags.append("stable")
        
        return tags


class AdaptiveClassifier:
    """360: 적응형 분류 장치
    미분류 패턴 학습 및 규칙 업데이트
    """
    
    def __init__(self, learning_rate: float = 0.1):
        self.learning_rate = learning_rate
        self.learned_patterns: List[np.ndarray] = []
        self.pattern_labels: List[str] = []
        self.adaptation_history: List[Dict] = []
    
    def learn(self, vector: np.ndarray, label: str = None):
        """새로운 패턴 학습"""
        self.learned_patterns.append(vector.copy())
        self.pattern_labels.append(label or f"pattern_{len(self.learned_patterns)}")
        
        self.adaptation_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'action': 'learn',
            'pattern_count': len(self.learned_patterns),
            'label': self.pattern_labels[-1]
        })
    
    def classify(self, vector: np.ndarray) -> Tuple[Optional[str], float]:
        """학습된 패턴으로 분류"""
        if not self.learned_patterns:
            return None, 0.0
        
        best_match = None
        best_similarity = -1.0
        
        for pattern, label in zip(self.learned_patterns, self.pattern_labels):
            similarity = self._cosine_similarity(vector, pattern)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = label
        
        return best_match, float(best_similarity)
    
    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """코사인 유사도"""
        norm1, norm2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))


class SignalPreprocessor:
    """신호 전처리 시스템 (통합)"""
    
    def __init__(self, dimension: int = 64, threshold: float = 0.7):
        self.transformer = VectorTransformer(dimension)
        self.checker = ConformanceChecker(threshold=threshold)
        self.remodulator = RecursiveRemodulator()
        self.refiner = SignalRefiner()
        self.generator = ModuleGenerator()
        self.classifier = AdaptiveClassifier()
        
        self.processing_history: List[Dict] = []
    
    def set_reference_vector(self, reference: np.ndarray):
        """기준 벡터 설정"""
        self.checker.set_reference(reference)
    
    def process(self, signal: Any, signal_type: SignalType = None) -> List[SignalModule]:
        """신호 전처리 메인 함수"""
        # 1. 벡터 변환 (310)
        vector, detected_type = self.transformer.transform(signal, signal_type)
        
        # 2. 정합성 판별 (320)
        status, S_idx = self.checker.check(vector)
        
        modules = []
        
        if status == ConformanceStatus.CONFORMING:
            # 정합 → 정제 처리 (340) → 모듈 생성 (350)
            refined, _ = self.refiner.refine(vector)
            module = self.generator.generate(refined, detected_type, status, S_idx)
            modules.append(module)
        else:
            # 비정합 → 재귀적 재분류 (330)
            sub_results = self.remodulator.recursive_classify(vector, self.checker)
            
            for sub_vector, sub_status, sub_idx in sub_results:
                if sub_status == ConformanceStatus.CONFORMING:
                    refined, _ = self.refiner.refine(sub_vector)
                    module = self.generator.generate(refined, detected_type, sub_status, sub_idx)
                else:
                    # 미분류 → 적응형 분류 시도 (360)
                    label, similarity = self.classifier.classify(sub_vector)
                    if label and similarity > 0.8:
                        module = self.generator.generate(
                            sub_vector, detected_type, ConformanceStatus.CONFORMING, 
                            similarity, tags=[label]
                        )
                    else:
                        # 최종 미분류
                        module = self.generator.generate(
                            sub_vector, detected_type, sub_status, sub_idx,
                            tags=["unclassified"]
                        )
                        # 새 패턴 학습
                        self.classifier.learn(sub_vector)
                
                modules.append(module)
        
        self.processing_history.append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'input_type': detected_type.value,
            'conformance_index': S_idx,
            'modules_generated': len(modules)
        })
        
        return modules
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.processing_history)
        conforming = sum(1 for m in self.generator.modules.values() 
                        if m.conformance_status == ConformanceStatus.CONFORMING)
        
        return {
            'total_processed': total,
            'modules_generated': len(self.generator.modules),
            'conforming_count': conforming,
            'conforming_rate': conforming / len(self.generator.modules) if self.generator.modules else 0,
            'learned_patterns': len(self.classifier.learned_patterns)
        }


# 하위 호환성을 위한 별칭
SignalAssetizer = SignalPreprocessor
