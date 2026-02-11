"""
시각화 모듈
차트 및 그래프 데이터 생성
"""
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field

@dataclass
class ChartData:
    """차트 데이터"""
    chart_type: str
    labels: List[str]
    datasets: List[Dict]
    options: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "type": self.chart_type,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options
        }

class GVICVisualizer:
    """GVIC 시각화기"""
    
    def __init__(self):
        self.color_palette = {
            "public": "#3B82F6",      # 파랑
            "productive": "#10B981",  # 초록
            "individual": "#F59E0B",  # 주황
            "primary": "#6366F1",     # 인디고
            "secondary": "#8B5CF6",   # 보라
            "danger": "#EF4444",      # 빨강
            "warning": "#F59E0B",     # 주황
            "success": "#10B981"      # 초록
        }
    
    def create_distribution_pie(self, distribution: Dict) -> ChartData:
        """분배 파이 차트"""
        labels = ["공공 (Public)", "생산 (Productive)", "개인 (Individual)"]
        values = [
            distribution.get("public", 0.5),
            distribution.get("productive", 0.3),
            distribution.get("individual", 0.2)
        ]
        
        return ChartData(
            chart_type="pie",
            labels=labels,
            datasets=[{
                "data": values,
                "backgroundColor": [
                    self.color_palette["public"],
                    self.color_palette["productive"],
                    self.color_palette["individual"]
                ]
            }],
            options={"responsive": True}
        )
    
    def create_convergence_line(self, history: List[Dict], limit: int = 20) -> ChartData:
        """수렴 히스토리 라인 차트"""
        history = history[-limit:]
        
        labels = [f"T-{len(history)-i}" for i in range(len(history))]
        
        public_data = [h.get("output", [0.5, 0.3, 0.2])[0] for h in history]
        productive_data = [h.get("output", [0.5, 0.3, 0.2])[1] for h in history]
        individual_data = [h.get("output", [0.5, 0.3, 0.2])[2] for h in history]
        
        return ChartData(
            chart_type="line",
            labels=labels,
            datasets=[
                {"label": "공공", "data": public_data, 
                 "borderColor": self.color_palette["public"], "fill": False},
                {"label": "생산", "data": productive_data,
                 "borderColor": self.color_palette["productive"], "fill": False},
                {"label": "개인", "data": individual_data,
                 "borderColor": self.color_palette["individual"], "fill": False}
            ],
            options={"responsive": True, "maintainAspectRatio": False}
        )
    
    def create_balance_gauge(self, balance_score: float) -> Dict:
        """균형 지수 게이지"""
        return {
            "type": "gauge",
            "value": balance_score,
            "min": 0,
            "max": 1,
            "thresholds": [
                {"value": 0.3, "color": self.color_palette["danger"]},
                {"value": 0.7, "color": self.color_palette["warning"]},
                {"value": 1.0, "color": self.color_palette["success"]}
            ]
        }
    
    def create_metrics_bar(self, metrics: Dict) -> ChartData:
        """메트릭 바 차트"""
        labels = list(metrics.keys())
        values = [metrics[k].get("latest", 0) if isinstance(metrics[k], dict) else metrics[k] 
                  for k in labels]
        
        return ChartData(
            chart_type="bar",
            labels=labels,
            datasets=[{
                "label": "메트릭",
                "data": values,
                "backgroundColor": self.color_palette["primary"]
            }],
            options={"responsive": True}
        )
    
    def create_alert_summary(self, alerts_stats: Dict) -> Dict:
        """알림 요약 데이터"""
        by_level = alerts_stats.get("by_level", {})
        return {
            "type": "summary",
            "total": alerts_stats.get("total", 0),
            "active": alerts_stats.get("active", 0),
            "by_level": {
                "critical": {"count": by_level.get("critical", 0), "color": self.color_palette["danger"]},
                "error": {"count": by_level.get("error", 0), "color": self.color_palette["danger"]},
                "warning": {"count": by_level.get("warning", 0), "color": self.color_palette["warning"]},
                "info": {"count": by_level.get("info", 0), "color": self.color_palette["primary"]}
            }
        }
    
    def create_dashboard_data(self, engine_status: Dict, control_data: Dict) -> Dict:
        """대시보드 전체 데이터"""
        return {
            "distribution_chart": self.create_distribution_pie(
                engine_status.get("modules", {}).get("distributor", {})
            ).to_dict(),
            "balance_gauge": self.create_balance_gauge(
                engine_status.get("balance_score", 0.8)
            ),
            "alerts_summary": self.create_alert_summary(
                control_data.get("alerts", {}).get("statistics", {})
            ),
            "system_health": control_data.get("health", {}),
            "metrics": control_data.get("metrics", {})
        }
