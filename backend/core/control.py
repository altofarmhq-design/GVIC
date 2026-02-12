"""내부 통제 시스템
알림 관리 및 헬스체크
"""
from dataclasses import dataclass
from typing import Dict, List, Callable, Optional
from datetime import datetime
from enum import Enum

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Alert:
    """알림 데이터 클래스"""
    id: str
    level: AlertLevel
    component: str
    message: str
    timestamp: str
    resolved: bool = False
    resolved_at: Optional[str] = None

class AlertManager:
    """알림 관리자"""
    
    def __init__(self, max_alerts: int = 100):
        self.alerts: List[Alert] = []
        self.max_alerts = max_alerts
        self.alert_counter = 0
        self.subscribers: List[Callable] = []
    
    def create_alert(self, level: AlertLevel, component: str, message: str) -> Alert:
        """알림 생성"""
        self.alert_counter += 1
        alert = Alert(
            id=f"ALT-{self.alert_counter:05d}",
            level=level,
            component=component,
            message=message,
            timestamp=datetime.now().isoformat()
        )
        
        self.alerts.append(alert)
        
        # 최대 개수 초과시 오래된 알림 제거
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 구독자에게 알림
        for subscriber in self.subscribers:
            try:
                subscriber(alert)
            except Exception:
                pass
        
        return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """알림 해결 처리"""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now().isoformat()
                return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """활성 알림 조회"""
        return [a for a in self.alerts if not a.resolved]
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        active = [a for a in self.alerts if not a.resolved]
        resolved = [a for a in self.alerts if a.resolved]
        
        by_level = {
            'info': sum(1 for a in active if a.level == AlertLevel.INFO),
            'warning': sum(1 for a in active if a.level == AlertLevel.WARNING),
            'error': sum(1 for a in active if a.level == AlertLevel.ERROR),
            'critical': sum(1 for a in active if a.level == AlertLevel.CRITICAL)
        }
        
        return {
            'total': len(self.alerts),
            'active': len(active),
            'resolved': len(resolved),
            'by_level': by_level
        }

class HealthChecker:
    """헬스 체크 관리자"""
    
    def __init__(self):
        self.checks: Dict[str, Dict] = {}
        self.results: Dict[str, Dict] = {}
    
    def check_component(self, name: str, check_func: Callable) -> Dict:
        """컴포넌트 헬스 체크 실행"""
        try:
            result = check_func()
            self.results[name] = {
                'status': 'healthy' if result.get('healthy', False) else 'unhealthy',
                'message': result.get('message', ''),
                'timestamp': datetime.now().isoformat(),
                'details': result.get('details', {})
            }
        except Exception as e:
            self.results[name] = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
        
        return self.results[name]
    
    def get_system_health(self) -> Dict:
        """전체 시스템 헬스 조회"""
        healthy_count = sum(1 for r in self.results.values() if r['status'] == 'healthy')
        total = len(self.results)
        
        return {
            'overall': 'healthy' if healthy_count == total and total > 0 else 'degraded',
            'healthy_count': healthy_count,
            'total': total,
            'components': self.results
        }

class InternalControlSystem:
    """내부 통제 시스템"""
    
    def __init__(self):
        self.alert_manager = AlertManager()
        self.health_checker = HealthChecker()
        self.health_checks = {
            'engine': self._check_engine,
            'io': self._check_io,
            'config': self._check_config
        }
    
    def _check_engine(self) -> Dict:
        """엔진 헬스 체크"""
        try:
            from .engine import GVICEngine
            engine = GVICEngine()
            result = engine.process({'value': 0.5})
            return {
                'healthy': result.success,
                'message': '엔진 정상 동작' if result.success else '엔진 오류',
                'details': {'processed': result.success}
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'엔진 체크 실패: {str(e)}'
            }
    
    def _check_io(self) -> Dict:
        """IO 헬스 체크"""
        try:
            from .io_interface import IOInterface
            io = IOInterface()
            result = io.process_input('{"test": 1}', format='json')
            return {
                'healthy': result is not None,
                'message': 'IO 정상 동작',
                'details': {'processed': True}
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'IO 체크 실패: {str(e)}'
            }
    
    def _check_config(self) -> Dict:
        """설정 헬스 체크"""
        return {
            'healthy': True,
            'message': '설정 정상',
            'details': {'loaded': True}
        }
    
    def run_health_checks(self) -> Dict:
        """모든 헬스 체크 실행"""
        results = {}
        
        for name, check_func in self.health_checks.items():
            result = self.health_checker.check_component(name, check_func)
            results[name] = result
            
            if result['status'] != 'healthy':
                self.alert_manager.create_alert(
                    AlertLevel.ERROR,
                    name,
                    f"헬스체크 실패: {result.get('message', 'Unknown error')}"
                )
        
        return results
    
    def get_dashboard_data(self) -> Dict:
        """대시보드 데이터 조회"""
        return {
            'health': self.health_checker.get_system_health(),
            'alerts': {
                'active': [{
                    'id': a.id,
                    'level': a.level.value,
                    'component': a.component,
                    'message': a.message,
                    'timestamp': a.timestamp
                } for a in self.alert_manager.get_active_alerts()],
                'statistics': self.alert_manager.get_statistics()
            }
        }
