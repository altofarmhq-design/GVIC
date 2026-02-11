from datetime import datetime
import json
from pathlib import Path

class ProgressTracker:
    def __init__(self, log_path="data/progress_log.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs = self.load()
    
    def load(self):
        """로그 파일 로드"""
        if self.log_path.exists():
            with open(self.log_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save(self):
        """로그 파일 저장"""
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(self.logs, f, ensure_ascii=False, indent=2)
    
    def add_log(self, phase, action, details=""):
        """로그 추가"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phase": phase,
            "action": action,
            "details": details
        }
        self.logs.append(log_entry)
        self.save()
        return log_entry
    
    def get_recent_logs(self, limit=20):
        """최근 로그 반환"""
        return self.logs[-limit:][::-1]
    
    def get_logs_by_phase(self, phase):
        """특정 단계 로그 반환"""
        return [log for log in self.logs if log['phase'] == phase]
    
    def clear_logs(self):
        """로그 초기화"""
        self.logs = []
        self.save()
