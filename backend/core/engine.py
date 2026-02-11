"""
GVIC 통합 엔진
- 6개 특허 모듈 통합
- 전체 파이프라인 실행
"""
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from .patent1_convergence import ConvergenceController
from .patent2_signal import SignalAssetizer, SignalType
from .patent3_pipeline import PipelineProcessor
from .patent4_nonconform import NonconformHandler
from .patent5_distribution import WeightedDistributor
from .patent6_interface import DomainInterface

@dataclass
class ProcessingResult:
    """처리 결과"""
    success: bool
    data: Any
    metadata: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class GVICEngine:
    """GVIC 통합 엔진"""
    
    def __init__(self, 
                 sigma: List[float] = [0.5, 0.3, 0.2],
                 omega: Dict = None):
        self.sigma = sigma
        self.omega = omega or {
            "V_pub_min": 0.2,
            "V_pub_max": 0.8,
            "V_ind_max": 0.5,
            "sum_constraint": 1.0
        }
        
        # 6개 특허 모듈 초기화
        self.convergence = ConvergenceController(
            default_ratio=sigma,
            omega=self.omega
        )
        self.assetizer = SignalAssetizer(sigma=sigma)
        self.pipeline = PipelineProcessor()
        self.nonconform = NonconformHandler()
        self.distributor = WeightedDistributor(base_ratio=sigma)
        self.interface = DomainInterface()
        
        self.processing_history: List[ProcessingResult] = []
    
    def process(self, 
                input_data: Any, 
                source_type: str = "auto") -> ProcessingResult:
        """
        전체 처리 파이프라인 실행
        
        1. 입력 인터페이스 (특허 6)
        2. 비적합 데이터 처리 (특허 4)
        3. 신호 자산화 (특허 2)
        4. 가중 분배 (특허 5)
        5. 수렴 제어 (특허 1)
        """
        errors = []
        start_time = datetime.now()
        
        try:
            # 1. 입력 인터페이스 (특허 6)
            interface_result = self.interface.process(input_data)
            
            if interface_result.get("status") != "success":
                errors.append(f"Interface error: {interface_result.get('error')}")
                processed_data = input_data
            else:
                processed_data = interface_result.get("data", input_data)
            
            # 2. 비적합 데이터 처리 (특허 4)
            if isinstance(processed_data, dict):
                for key, value in processed_data.items():
                    if isinstance(value, (int, float)):
                        nc_result = self.nonconform.process(value)
                        if nc_result["status"] != "normal":
                            processed_data[key] = nc_result["processed"]
            elif isinstance(processed_data, (int, float)):
                nc_result = self.nonconform.process(processed_data)
                processed_data = nc_result["processed"]
            
            # 3. 신호 자산화 (특허 2)
            if isinstance(processed_data, dict):
                signal_value = processed_data.get("value", 
                              processed_data.get("amount", 
                              sum(v for v in processed_data.values() if isinstance(v, (int, float)))))
            else:
                signal_value = processed_data if isinstance(processed_data, (int, float)) else 0.5
            
            asset_result = self.assetizer.process_signal(signal_value)
            
            # 4. 가중 분배 (특허 5)
            asset_value = asset_result.get("asset", {}).get("value", 0.5)
            distribution = self.distributor.distribute(asset_value)
            
            # 5. 수렴 제어 (특허 1)
            V_in = np.array([
                distribution["public"].amount,
                distribution["productive"].amount,
                distribution["individual"].amount
            ])
            
            if np.sum(V_in) > 0:
                V_normalized = V_in / np.sum(V_in)
            else:
                V_normalized = np.array(self.sigma)
            
            V_conv, convergence_meta = self.convergence.converge(V_normalized)
            
            # 최종 결과 구성
            end_time = datetime.now()
            
            result_data = {
                "input": {
                    "raw": str(input_data)[:100],
                    "processed": processed_data if not isinstance(processed_data, (dict, list)) else "complex"
                },
                "asset": asset_result.get("asset", {}),
                "distribution": {
                    "public": distribution["public"].amount,
                    "productive": distribution["productive"].amount,
                    "individual": distribution["individual"].amount
                },
                "convergence": {
                    "input_ratio": V_normalized.tolist(),
                    "output_ratio": V_conv.tolist(),
                    "is_valid": convergence_meta.get("status") == "valid",
                    "was_transformed": convergence_meta.get("transformed", False)
                },
                "balance_score": self.convergence.calculate_balance_index(V_conv)
            }
            
            result = ProcessingResult(
                success=True,
                data=result_data,
                metadata={
                    "duration_ms": (end_time - start_time).total_seconds() * 1000,
                    "modules_used": ["interface", "nonconform", "assetizer", "distributor", "convergence"]
                },
                errors=errors
            )
            
        except Exception as e:
            result = ProcessingResult(
                success=False,
                data=None,
                metadata={"error_type": type(e).__name__},
                errors=[str(e)]
            )
        
        self.processing_history.append(result)
        return result
    
    def process_batch(self, items: List[Any]) -> List[ProcessingResult]:
        """배치 처리"""
        results = []
        for item in items:
            result = self.process(item)
            results.append(result)
        return results
    
    def update_sigma(self, new_sigma: List[float]):
        """Σ 업데이트"""
        self.sigma = new_sigma
        self.convergence.R = np.array(new_sigma)
        self.assetizer.sigma = np.array(new_sigma)
        self.distributor.base_ratio = np.array(new_sigma)
        self.distributor.current_ratio = np.array(new_sigma)
    
    def update_omega(self, new_omega: Dict):
        """Ω 업데이트"""
        self.omega = new_omega
        self.convergence.omega.lower_bounds = np.array([
            new_omega.get('V_pub_min', 0.2), 0.0, 0.0
        ])
        self.convergence.omega.upper_bounds = np.array([
            new_omega.get('V_pub_max', 0.8), 1.0, new_omega.get('V_ind_max', 0.5)
        ])
    
    def get_system_status(self) -> Dict:
        """시스템 상태 조회"""
        return {
            "sigma": self.sigma,
            "omega": self.omega,
            "total_processed": len(self.processing_history),
            "success_rate": sum(1 for r in self.processing_history if r.success) / max(1, len(self.processing_history)),
            "modules": {
                "convergence": "active",
                "assetizer": f"{len(self.assetizer.assets)} assets",
                "distributor": self.distributor.get_statistics(),
                "nonconform": self.nonconform.get_statistics(),
                "interface": self.interface.get_statistics()
            }
        }
    
    def reset(self):
        """시스템 초기화"""
        self.convergence = ConvergenceController(
            default_ratio=self.sigma,
            omega=self.omega
        )
        self.assetizer = SignalAssetizer(sigma=self.sigma)
        self.distributor = WeightedDistributor(base_ratio=self.sigma)
        self.nonconform = NonconformHandler()
        self.processing_history = []
