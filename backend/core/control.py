import numpy as np
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComponentStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@dataclass
class Alert:
    id: str
    level: AlertLevel
    component: str
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: str = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "level": self.level.value, "component": self.component,
            "message": self.message, "timestamp": self.timestamp,
            "resolved": self.resolved, "resolved_at": self.resolved_at
        }

@dataclass
class HealthCheckResult:
    component: str
    status: ComponentStatus
    message: str
    response_time_ms: float
    timestamp: str
    details: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            "component": self.component, "status": self.status.value,
            "message": self.message, "response_time_ms": self.response_time_ms,
            "timestamp": self.timestamp, "details": self.details or {}
        }

class ThresholdManager:
    def __init__(self, config_path: str = "config/thresholds.json"):
        self.config_path = Path(config_path)
        self.thresholds = self._load_thresholds()
    
    def _load_thresholds(self) -> Dict:
        default = {
            "convergence": {"violation_warning": 0.1, "violation_critical": 0.3, "balance_score_min": 0.7},
            "distribution": {"public_min": 0.2, "public_max": 0.8, "individual_max": 0.5},
            "performance": {"response_time_warning_ms": 500, "response_time_critical_ms": 2000},
            "system": {"queue_size_warning": 100, "queue_size_critical": 500}
        }
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    for key in default:
                        if key in loaded:
                            default[key].update(loaded[key])
            except:
                pass
        return default
    
    def save_thresholds(self):
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.thresholds, f, ensure_ascii=False, indent=2)
    
    def get(self, category: str, key: str) -> Any:
        return self.thresholds.get(category, {}).get(key)
    
    def set(self, category: str, key: str, value: Any):
        if category not in self.thresholds:
            self.thresholds[category] = {}
        self.thresholds[category][key] = value
        self.save_thresholds()
    
    def check_threshold(self, category: str, key: str, value: float) -> Optional[AlertLevel]:
        warning = self.get(category, f"{key}_warning")
        critical = self.get(category, f"{key}_critical")
        if critical and value >= critical:
            return AlertLevel.CRITICAL
        elif warning and value >= warning:
            return AlertLevel.WARNING
        return None
    
    def get_all(self) -> Dict:
        return self.thresholds

class AlertManager:
    def __init__(self, max_alerts: int = 100):
        self.alerts: List[Alert] = []
        self.max_alerts = max_alerts
        self.alert_counter = 0
        self.subscribers: List[Callable] = []
    
    def create_alert(self, level: AlertLevel, component: str, message: str) -> Alert:
        self.alert_counter += 1
        alert = Alert(
            id=f"ALT-{self.alert_counter:05d}", level=level, component=component,
            message=message, timestamp=datetime.now().isoformat()
        )
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        for sub in self.subscribers:
            try: sub(alert)
            except: pass
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now().isoformat()
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        return [a for a in self.alerts if not a.resolved]
    
    def get_statistics(self) -> Dict:
        active = self.get_active_alerts()
        by_level = {lv.value: len([a for a in active if a.level == lv]) for lv in AlertLevel}
        return {"total": len(self.alerts), "active": len(active), 
                "resolved": len(self.alerts) - len(active), "by_level": by_level}

class HealthChecker:
    def __init__(self):
        self.check_results: Dict[str, HealthCheckResult] = {}
        self.check_history: List[Dict] = []
        self.max_history = 100
    
    def check_component(self, component: str, check_func: Callable) -> HealthCheckResult:
        start = datetime.now()
        try:
            result = check_func()
            resp_time = (datetime.now() - start).total_seconds() * 1000
            status = ComponentStatus.HEALTHY if result.get("healthy") else ComponentStatus.UNHEALTHY
            message = result.get("message", "")
            details = result.get("details", {})
        except Exception as e:
            resp_time = (datetime.now() - start).total_seconds() * 1000
            status, message, details = ComponentStatus.UNHEALTHY, str(e), {"error": str(e)}
        
        check_result = HealthCheckResult(
            component=component, status=status, message=message,
            response_time_ms=resp_time, timestamp=datetime.now().isoformat(), details=details
        )
        self.check_results[component] = check_result
        self.check_history.append(check_result.to_dict())
        if len(self.check_history) > self.max_history:
            self.check_history = self.check_history[-self.max_history:]
        return check_result
    
    def get_system_health(self) -> Dict:
        if not self.check_results:
            return {"status": "unknown", "message": "헬스체크 없음", "components": {}}
        
        statuses = [r.status for r in self.check_results.values()]
        if all(s == ComponentStatus.HEALTHY for s in statuses):
            overall, msg = ComponentStatus.HEALTHY, "모든 컴포넌트 정상"
        elif any(s == ComponentStatus.UNHEALTHY for s in statuses):
            unhealthy = [c for c, r in self.check_results.items() if r.status == ComponentStatus.UNHEALTHY]
            overall, msg = ComponentStatus.UNHEALTHY, f"비정상: {', '.join(unhealthy)}"
        else:
            overall, msg = ComponentStatus.DEGRADED, "일부 성능 저하"
        
        return {"status": overall.value, "message": msg,
                "components": {c: r.to_dict() for c, r in self.check_results.items()}}

class MonitoringMetrics:
    def __init__(self):
        self.metrics: Dict[str, List[Dict]] = {}
        self.max_points = 100
    
    def record(self, name: str, value: float, tags: Dict = None):
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({"value": value, "timestamp": datetime.now().isoformat(), "tags": tags or {}})
        if len(self.metrics[name]) > self.max_points:
            self.metrics[name] = self.metrics[name][-self.max_points:]
    
    def get_statistics(self, name: str) -> Dict:
        points = self.metrics.get(name, [])
        if not points:
            return {"count": 0}
        values = [p["value"] for p in points]
        return {"count": len(values), "min": min(values), "max": max(values),
                "avg": sum(values)/len(values), "latest": values[-1]}
    
    def get_all_metrics(self) -> Dict:
        return {name: self.get_statistics(name) for name in self.metrics}

class InternalControlSystem:
    def __init__(self):
        self.threshold_manager = ThresholdManager()
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.metrics = MonitoringMetrics()
        self.health_checks = {"config": self._check_config, "engine": self._check_engine, "io": self._check_io}
    
    def _check_config(self) -> Dict:
        try:
            from utils.config_manager import ConfigManager
            config = ConfigManager("config/settings.json")
            sigma = config.get_sigma()
            if abs(sum(sigma) - 1.0) > 0.01:
                return {"healthy": False, "message": "Σ 합계 오류"}
            return {"healthy": True, "message": "설정 정상", "details": {"sigma": sigma}}
        except Exception as e:
            return {"healthy": False, "message": str(e)}
    
    def _check_engine(self) -> Dict:
        try:
            from core import GVICEngine
            engine = GVICEngine()
            result = engine.process({"value": 0.5})
            return {"healthy": result.success, "message": "엔진 정상" if result.success else "처리 실패"}
        except Exception as e:
            return {"healthy": False, "message": str(e)}
    
    def _check_io(self) -> Dict:
        try:
            from core.io_interface import IOInterface
            IOInterface().process_input('{"test": 1}', format="json")
            return {"healthy": True, "message": "IO 정상"}
        except Exception as e:
            return {"healthy": False, "message": str(e)}
    
    def run_health_checks(self) -> Dict:
        for name, func in self.health_checks.items():
            result = self.health_checker.check_component(name, func)
            if result.status == ComponentStatus.UNHEALTHY:
                self.alert_manager.create_alert(AlertLevel.ERROR, name, f"헬스체크 실패: {result.message}")
        return self.health_checker.get_system_health()
    
    def get_dashboard_data(self) -> Dict:
        return {
            "health": self.health_checker.get_system_health(),
            "alerts": {"active": [a.to_dict() for a in self.alert_manager.get_active_alerts()],
                      "statistics": self.alert_manager.get_statistics()},
            "metrics": self.metrics.get_all_metrics(),
            "thresholds": self.threshold_manager.get_all()
        }
    
    def get_status_summary(self) -> Dict:
        health = self.health_checker.get_system_health()
        alerts = self.alert_manager.get_statistics()
        return {"system_status": health["status"], "active_alerts": alerts["active"],
                "critical_alerts": alerts["by_level"].get("critical", 0),
                "warning_alerts": alerts["by_level"].get("warning", 0)}
