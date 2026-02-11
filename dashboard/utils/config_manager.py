import json
from pathlib import Path
from datetime import datetime
import shutil

class ConfigManager:
    def __init__(self, config_path="config/settings.json"):
        self.config_path = Path(config_path)
        self.history_dir = Path("data/history")
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.load()
    
    def load(self):
        """설정 파일 로드"""
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def save(self, config=None):
        """설정 파일 저장 (이력 백업 포함)"""
        if config:
            self.config = config
        
        # 이력 백업
        self._backup_history()
        
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def _backup_history(self):
        """변경 이력 백업"""
        if self.config_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.history_dir / f"settings_{timestamp}.json"
            shutil.copy(self.config_path, backup_path)
            
            # 최근 20개만 유지
            history_files = sorted(self.history_dir.glob("settings_*.json"))
            if len(history_files) > 20:
                for old_file in history_files[:-20]:
                    old_file.unlink()
    
    def get_history(self):
        """변경 이력 목록"""
        history_files = sorted(self.history_dir.glob("settings_*.json"), reverse=True)
        return [f.name for f in history_files]
    
    def load_history(self, filename):
        """특정 이력 로드"""
        history_path = self.history_dir / filename
        if history_path.exists():
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def get_sigma(self):
        """시그마 값 반환"""
        return self.config.get('sigma', {}).get('values', [0.5, 0.3, 0.2])
    
    def set_sigma(self, values):
        """시그마 값 설정"""
        self.config['sigma']['values'] = values
        self.save()
    
    def get_omega(self):
        """오메가 제약조건 반환"""
        return self.config.get('omega', {})
    
    def set_omega(self, omega):
        """오메가 제약조건 설정"""
        self.config['omega'] = omega
        self.save()
    
    def get_patents(self):
        """특허 목록 반환"""
        return self.config.get('patents', {})
    
    def update_patent_status(self, patent_id, status):
        """특허 상태 업데이트"""
        if patent_id in self.config.get('patents', {}):
            self.config['patents'][patent_id]['status'] = status
            self.save()
    
    def get_phases(self):
        """단계별 진행 상태"""
        return self.config.get('phases', {})
    
    def update_phase(self, phase_id, status=None, progress=None):
        """단계 상태/진행률 업데이트"""
        if phase_id in self.config.get('phases', {}):
            if status:
                self.config['phases'][phase_id]['status'] = status
            if progress is not None:
                self.config['phases'][phase_id]['progress'] = progress
            self.save()
