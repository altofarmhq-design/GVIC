"""진행 추적 모듈"""
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

class ProgressTracker:
    """진행 추적기"""
    
    def __init__(self, log_path: str = "data/progress_log.json"):
        self.log_path = Path(log_path)
        self.logs: List[Dict] = self._load_logs()
    
    def _load_logs(self) -> List[Dict]:
        """로그 파일 로드"""
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_logs(self):
        """로그 파일 저장"""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(self.logs[-1000:], f, ensure_ascii=False, indent=2)  # 최대 1000개 유지
    
    def log(self, phase: str, action: str, data: Dict = None):
        """로그 기록"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'phase': phase,
            'action': action,
            'data': data or {}
        }
        self.logs.append(entry)
        self._save_logs()
    
    def get_recent_logs(self, count: int = 10) -> List[Dict]:
        """최근 로그 조회"""
        return self.logs[-count:][::-1]
    
    def get_logs_by_phase(self, phase: str) -> List[Dict]:
        """페이즈별 로그 조회"""
        return [log for log in self.logs if log['phase'] == phase]
    
    def clear_logs(self):
        """로그 초기화"""
        self.logs = []
        self._save_logs()
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        phase_counts = {}
        for log in self.logs:
            phase = log['phase']
            phase_counts[phase] = phase_counts.get(phase, 0) + 1
        
        return {
            'total_logs': len(self.logs),
            'by_phase': phase_counts
        }
