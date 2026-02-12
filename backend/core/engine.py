"""GVIC 통합 엔진
6개 특허 모듈 통합
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

from .patent1_convergence import ConvergenceController
from .patent2_signal import SignalAssetizer
from .patent3_pipeline import PipelineProcessor
from .patent4_nonconform import NonconformHandler
from .patent5_distribution import WeightedDistributor
from .patent6_interface import DomainInterface

@dataclass
class ProcessingResult:
    """처리 결과 데이터 클래스"""
    success: bool
    data: Any
    metadata: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class GVICEngine:
    """GVIC 통합 엔진"""
    
    def __init__(self, sigma: List[float] = None, omega: Dict = None):
        self.sigma = sigma or [0.33, 0.34, 0.33]
        self.omega = omega or {
            'V_pub_min': 0.2, 'V_pub_max': 0.5,
            'V_pro_min': 0.2, 'V_pro_max': 0.5,
            'V_ind_min': 0.1, 'V_ind_max': 0.5,
            'sum_constraint': 1.0
        }
        
        # 모듈 초기화
        omega_config = {
            'lower_bounds': [self.omega.get('V_pub_min', 0.2), 
                           self.omega.get('V_pro_min', 0.2), 
                           self.omega.get('V_ind_min', 0.1)],
            'upper_bounds': [self.omega.get('V_pub_max', 0.5),
                           self.omega.get('V_pro_max', 0.5),
                           self.omega.get('V_ind_max', 0.5)],
            'sum_constraint': self.omega.get('sum_constraint', 1.0)
        }
        
        self.convergence = ConvergenceController(default_ratio=self.sigma, omega=omega_config)
        self.assetizer = SignalAssetizer(sigma=self.sigma)
        self.pipeline = PipelineProcessor()
        self.nonconform = NonconformHandler()
        self.distributor = WeightedDistributor(base_ratio=self.sigma)
        self.interface = DomainInterface()
        
        self.processing_history: List[ProcessingResult] = []
    
    def process(self, input_data: Any, source_type: str = "auto") -> ProcessingResult:
        """데이터 처리 메인 함수"""
        try:
            # 1. 입력 인터페이스 (특허 6)
            processed_data = self.interface.process(input_data, source_type)
            
            if 'error' in processed_data:
                return ProcessingResult(
                    success=False,
                    data=None,
                    errors=[processed_data['error']]
                )
            
            # 2. 비적합 처리 (특허 4)
            if isinstance(processed_data, dict):
                for key, value in processed_data.items():
                    if isinstance(value, (int, float)):
                        nonconform_result = self.nonconform.process(value)
                        processed_data[key] = nonconform_result['processed']
            elif isinstance(processed_data, (int, float)):
                nonconform_result = self.nonconform.process(processed_data)
                processed_data = nonconform_result['processed']
            
            # 3. 신호 자산화 (특허 2)
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
            
            # 4. 가중 분배 (특허 5)
            asset_value = asset_result.get('value', 0)
            distribution = self.distributor.distribute(asset_value)
            
            # 5. 수렴 제어 (특허 1)
            V_in = np.array([
                distribution.get('public', 0),
                distribution.get('productive', 0),
                distribution.get('individual', 0)
            ])
            
            if V_in.sum() > 0:
                V_normalized = V_in / V_in.sum()
            else:
                V_normalized = np.array(self.sigma)
            
            V_out, convergence_meta = self.convergence.converge(V_normalized)
            
            # 결과 조립
            result_data = {
                'input': {
                    'raw': str(input_data)[:100],
                    'processed': processed_data if not isinstance(processed_data, (dict, list)) else "complex"
                },
                'asset': asset_result,
                'distribution': {
                    'public': distribution['public'],
                    'productive': distribution['productive'],
                    'individual': distribution['individual']
                },
                'convergence': {
                    'input_ratio': V_normalized.tolist(),
                    'output_ratio': V_out.tolist(),
                    'is_valid': convergence_meta['status'] == 'converged',
                    'transformed': convergence_meta['transformed']
                },
                'balance_score': self.convergence.calculate_balance_index(V_out)
            }
            
            result = ProcessingResult(
                success=True,
                data=result_data,
                metadata=convergence_meta
            )
            
        except Exception as e:
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
        """시그마 업데이트"""
        self.sigma = new_sigma
        self.convergence.R = np.array(new_sigma)
        self.assetizer.sigma = new_sigma
        self.distributor.base_ratio = new_sigma
        self.distributor.current_ratio = new_sigma
    
    def update_omega(self, new_omega: Dict):
        """오메가 업데이트"""
        self.omega = new_omega
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
                'assetizer': self.assetizer.get_statistics(),
                'distributor': self.distributor.get_statistics(),
                'nonconform': self.nonconform.get_statistics(),
                'interface': self.interface.get_statistics()
            }
        }
    
    def reset(self):
        """엔진 리셋"""
        omega_config = {
            'lower_bounds': [self.omega.get('V_pub_min', 0.2),
                           self.omega.get('V_pro_min', 0.2),
                           self.omega.get('V_ind_min', 0.1)],
            'upper_bounds': [self.omega.get('V_pub_max', 0.5),
                           self.omega.get('V_pro_max', 0.5),
                           self.omega.get('V_ind_max', 0.5)],
            'sum_constraint': self.omega.get('sum_constraint', 1.0)
        }
        
        self.convergence = ConvergenceController(default_ratio=self.sigma, omega=omega_config)
        self.assetizer = SignalAssetizer(sigma=self.sigma)
        self.distributor = WeightedDistributor(base_ratio=self.sigma)
        self.nonconform = NonconformHandler()
        self.processing_history = []
