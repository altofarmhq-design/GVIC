"""
설정 관리 모듈
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """설정 로드"""
        default = {
            "sigma": [0.5, 0.3, 0.2],
            "omega": {
                "V_pub_min": 0.2,
                "V_pub_max": 0.8,
                "V_ind_max": 0.5,
                "sum_constraint": 1.0
            },
            "system": {
                "max_batch_size": 100,
                "timeout_seconds": 30
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    default.update(loaded)
            except:
                pass
        
        return default
    
    def save(self):
        """설정 저장"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """설정 조회"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """설정 변경"""
        self.config[key] = value
        self.save()
    
    def get_sigma(self) -> List[float]:
        """Σ 조회"""
        return self.config.get("sigma", [0.5, 0.3, 0.2])
    
    def get_omega(self) -> Dict:
        """Ω 조회"""
        return self.config.get("omega", {})
    
    def update_sigma(self, sigma: List[float]):
        """Σ 업데이트"""
        if len(sigma) == 3 and abs(sum(sigma) - 1.0) < 0.01:
            self.config["sigma"] = sigma
            self.save()
            return True
        return False
