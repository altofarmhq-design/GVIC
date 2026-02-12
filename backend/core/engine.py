"""GVIC 통합 엔진
7개 특허 모듈 통합 - 특허 사양 기반 리팩토링

특허 1: 전역 수렴 제어 시스템
특허 2: 다단계 신호 전처리 시스템
특허 3: 신호 자산화 통합 플랫폼
특허 4: 재귀적 모듈화 파이프라인
특허 5: 비적합 데이터 자산화 시스템 (시스템 3000)
특허 6: 가중 분배 모델 시스템 (시스템 4000)
특허 6-J: 다중 도메인 통합 인터페이스
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import numpy as np
import logging

from .patent1_convergence import ConvergenceController
from .patent2_signal import SignalPreprocessor, SignalType
from .patent3_signal_asset import SignalAssetizationPlatform
from .patent3_pipeline import PipelineProcessor
from .patent4_nonconform import NonconformHandler
from .patent5_distribution import WeightedDistributor
from .patent6_interface import DomainInterface

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """처리 결과 데이터 클래스"""
    success: bool
    data: Any
    metadata: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class GVICEngine:
    """GVIC 통합 엔진 - 특허 사양 기반"""
    
    def __init__(self, sigma: List[float] = None, omega: Dict = None):
        """엔진 초기화
        
        Args:
            sigma: 기본 분배 비율 [public, productive, individual]
            omega: 경계 조건 {V_pub_min, V_pub_max, V_pro_min, V_pro_max, V_ind_min, V_ind_max}
        """
        self.sigma = sigma or [0.33, 0.34, 0.33]
        self.omega = omega or {
            'V_pub_min': 0.2, 'V_pub_max': 0.5,
            'V_pro_min': 0.2, 'V_pro_max': 0.5,
            'V_ind_min': 0.1, 'V_ind_max': 0.5,
            'sum_constraint': 1.0
        }
        
        # 오메가 설정 변환
        omega_config = {
            'lower_bounds': [
                self.omega.get('V_pub_min', 0.2),
                self.omega.get('V_pro_min', 0.2),
                self.omega.get('V_ind_min', 0.1)
            ],
            'upper_bounds': [
                self.omega.get('V_pub_max', 0.5),
                self.omega.get('V_pro_max', 0.5),
                self.omega.get('V_ind_max', 0.5)
            ],
            'sum_constraint': self.omega.get('sum_constraint', 1.0)
        }
        
        # 특허 모듈 초기화
        # 특허 1: 전역 수렴 제어
        self.convergence = ConvergenceController(
            default_ratio=self.sigma, 
            omega=omega_config
        )
        
        # 특허 2: 신호 전처리
        self.preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
        
        # 특허 3: 신호 자산화
        self.assetizer = SignalAssetizationPlatform(sigma=self.sigma)
        
        # 특허 4: 파이프라인 (재귀적 모듈화)
        self.pipeline = PipelineProcessor()
        
        # 특허 5: 비적합 데이터 처리 (시스템 3000)
        self.nonconform = NonconformHandler(threshold=0.1)
        
        # 특허 6: 가중 분배 (시스템 4000)
        self.distributor = WeightedDistributor(base_ratio=self.sigma)
        
        # 특허 6-J: 도메인 인터페이스
        self.interface = DomainInterface()
        
        # 처리 이력
        self.processing_history: List[ProcessingResult] = []
        
        logger.info("GVIC Engine initialized with patent-based modules")
    
    def process(self, input_data: Any, source_type: str = "auto") -> ProcessingResult:
        """데이터 처리 메인 함수
        
        처리 흐름:
        1. 입력 인터페이스 (특허 6-J) - 데이터 수신 및 형식 변환
        2. 비적합 감지/처리 (특허 5/3000) - 비적합 데이터 분류 및 자산화
        3. 신호 전처리 (특허 2) - 벡터화, 정합성 판별, 재귀적 분류
        4. 신호 자산화 (특허 3) - 가치 산출 및 자산 객체 생성
        5. 가중 분배 (특허 6/4000) - WDM 기반 영역별 배분
        6. 수렴 제어 (특허 1) - OBC 검증 및 수렴 변환
        """
        try:
            # 1. 입력 인터페이스 (특허 6-J)
            processed_data = self.interface.process(input_data, source_type)
            
            if 'error' in processed_data:
                return ProcessingResult(
                    success=False,
                    data=None,
                    errors=[processed_data['error']]
                )
            
            # 2. 비적합 감지 및 처리 (특허 5 - 시스템 3000)
            nc_result = None
            if isinstance(processed_data, dict):
                for key, value in processed_data.items():
                    if isinstance(value, (int, float)):
                        nc_result = self.nonconform.process(value)
                        processed_data[key] = nc_result['processed']
            elif isinstance(processed_data, (int, float)):
                nc_result = self.nonconform.process(processed_data)
                processed_data = nc_result['processed']
            
            # 3. 신호 전처리 (특허 2)
            # 입력을 벡터로 변환하고 정합성 판별
            signal_modules = []
            if isinstance(processed_data, dict):
                signal_modules = self.preprocessor.process(processed_data)
            elif isinstance(processed_data, (int, float)):
                signal_modules = self.preprocessor.process({'value': processed_data})
            
            # 4. 신호 자산화 (특허 3)
            signal_value = 0.0
            if isinstance(processed_data, dict):
                signal_value = processed_data.get('value', 0)
                if signal_value == 0:
                    signal_value = processed_data.get('amount', 0)
                if signal_value == 0:
                    nums = [v for v in processed_data.values() if isinstance(v, (int, float))]
                    signal_value = sum(nums) if nums else 0
            elif isinstance(processed_data, (int, float)):
                signal_value = processed_data
            
            asset_result = self.assetizer.process_signal(signal_value)
            
            # 5. 가중 분배 (특허 6 - 시스템 4000)
            asset_value = asset_result.get('value', 0)
            distribution = self.distributor.distribute(asset_value)
            
            # 6. 수렴 제어 (특허 1)
            V_in = np.array([
                distribution.get('public', 0),
                distribution.get('productive', 0),
                distribution.get('individual', 0)
            ])
            
            # 정규화
            if V_in.sum() > 0:
                V_normalized = V_in / V_in.sum()
            else:
                V_normalized = np.array(self.sigma)
            
            # 수렴 변환 적용
            V_out, convergence_meta = self.convergence.converge(V_normalized)
            
            # 결과 조립
            result_data = {
                'input': {
                    'raw': str(input_data)[:100],
                    'processed': processed_data if not isinstance(processed_data, (dict, list)) else "complex"
                },
                'preprocessing': {
                    'modules_generated': len(signal_modules),
                    'conforming': sum(1 for m in signal_modules if m.conformance_status.value == 'conforming')
                },
                'asset': asset_result,
                'nonconformance': {
                    'detected': nc_result['is_nonconform'] if nc_result else False,
                    'adjustment': nc_result['adjustment'] if nc_result else 0
                },
                'distribution': {
                    'public': distribution['public'],
                    'productive': distribution['productive'],
                    'individual': distribution['individual']
                },
                'convergence': {
                    'input_ratio': V_normalized.tolist(),
                    'output_ratio': V_out.tolist(),
                    'is_valid': convergence_meta['status'] in ['valid', 'converged'],
                    'transformed': convergence_meta['transformed'],
                    'balance_index': convergence_meta.get('balance_index', 0)
                },
                'balance_score': self.convergence.calculate_balance_index(V_out)
            }
            
            result = ProcessingResult(
                success=True,
                data=result_data,
                metadata=convergence_meta
            )
            
        except Exception as e:
            logger.error(f"Processing error: {str(e)}", exc_info=True)
            result = ProcessingResult(
                success=False,
                data=None,
                errors=[str(e)]
            )
        
        self.processing_history.append(result)
        return result
    
    def process_batch(self, items: List[Any]) -> List[ProcessingResult]:
        """배치 처리"""
        return [self.process(item) for item in items]
    
    def update_sigma(self, new_sigma: List[float]):
        """시그마(기본 분배 비율) 업데이트"""
        if len(new_sigma) != 3:
            raise ValueError("Sigma must have 3 elements")
        
        total = sum(new_sigma)
        if not np.isclose(total, 1.0, atol=0.01):
            new_sigma = [s / total for s in new_sigma]
        
        self.sigma = new_sigma
        
        # 모듈별 업데이트
        self.convergence.R = np.array(new_sigma)
        self.assetizer.sigma = new_sigma
        self.distributor.update_ratio(new_sigma)
        
        logger.info(f"Sigma updated: {new_sigma}")
    
    def update_omega(self, new_omega: Dict):
        """오메가(경계 조건) 업데이트"""
        self.omega = new_omega
        
        # 수렴 제어기 업데이트
        self.convergence.omega.lower_bounds = np.array([
            new_omega.get('V_pub_min', 0.2),
            new_omega.get('V_pro_min', 0.2),
            new_omega.get('V_ind_min', 0.1)
        ])
        self.convergence.omega.upper_bounds = np.array([
            new_omega.get('V_pub_max', 0.5),
            new_omega.get('V_pro_max', 0.5),
            new_omega.get('V_ind_max', 0.5)
        ])
        
        logger.info("Omega updated")
    
    def get_system_status(self) -> Dict:
        """시스템 상태 조회"""
        total = len(self.processing_history)
        success = sum(1 for r in self.processing_history if r.success)
        
        return {
            'sigma': self.sigma,
            'omega': self.omega,
            'total_processed': total,
            'success_rate': success / total if total > 0 else 0,
            'modules': {
                'convergence': self.convergence.get_statistics(),
                'preprocessor': self.preprocessor.get_statistics(),
                'assetizer': self.assetizer.get_statistics(),
                'distributor': self.distributor.get_statistics(),
                'nonconform': self.nonconform.get_statistics(),
                'interface': self.interface.get_statistics()
            }
        }
    
    def get_rule_improvements(self) -> List[Dict]:
        """규칙 개선 제안 조회 (특허 5 기능)"""
        return self.nonconform.get_rule_improvements()
    
    def get_distribution_analytics(self) -> Dict:
        """분배 분석 데이터 조회 (특허 6 기능)"""
        return self.distributor.get_analytics()
    
    def reset(self):
        """엔진 리셋"""
        omega_config = {
            'lower_bounds': [
                self.omega.get('V_pub_min', 0.2),
                self.omega.get('V_pro_min', 0.2),
                self.omega.get('V_ind_min', 0.1)
            ],
            'upper_bounds': [
                self.omega.get('V_pub_max', 0.5),
                self.omega.get('V_pro_max', 0.5),
                self.omega.get('V_ind_max', 0.5)
            ],
            'sum_constraint': self.omega.get('sum_constraint', 1.0)
        }
        
        self.convergence = ConvergenceController(
            default_ratio=self.sigma, 
            omega=omega_config
        )
        self.preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
        self.assetizer = SignalAssetizationPlatform(sigma=self.sigma)
        self.distributor = WeightedDistributor(base_ratio=self.sigma)
        self.nonconform = NonconformHandler(threshold=0.1)
        self.processing_history = []
        
        logger.info("GVIC Engine reset")
