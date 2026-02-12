"""설정 관리 모듈"""
import json
from pathlib import Path
from typing import Dict, List, Any

class ConfigManager:
    """설정 관리자"""
    
    def __init__(self, config_path: str = "config/settings.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """설정 파일 로드"""
        default_config = {
            'sigma': [0.33, 0.34, 0.33],
            'omega': {
                'V_pub_min': 0.2,
                'V_pub_max': 0.5,
                'V_pro_min': 0.2,
                'V_pro_max': 0.5,
                'V_ind_min': 0.1,
                'V_ind_max': 0.5,
                'sum_constraint': 1.0
            },
            'system': {
                'max_alerts': 100,
                'log_retention_days': 30
            }
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return {**default_config, **json.load(f)}
            except:
                pass
        
        return default_config
    
    def _save_config(self):
        """설정 파일 저장"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def get_sigma(self) -> List[float]:
        """sigma 조회"""
        return self.config.get('sigma', [0.33, 0.34, 0.33])
    
    def set_sigma(self, sigma: List[float]):
        """sigma 설정"""
        self.config['sigma'] = sigma
        self._save_config()
    
    def get_omega(self) -> Dict:
        """omega 조회"""
        return self.config.get('omega', {})
    
    def set_omega(self, omega: Dict):
        """omega 설정"""
        self.config['omega'] = omega
        self._save_config()
    
    def get_all(self) -> Dict:
        """모든 설정 조회"""
        return self.config
    
    def update(self, key: str, value: Any):
        """설정 업데이트"""
        self.config[key] = value
        self._save_config()
