"""시각화 모듈"""
from typing import Dict, List

class GVICVisualizer:
    """GVIC 시각화 클래스"""
    
    def __init__(self):
        self.chart_configs = {}
    
    def create_pie_chart_data(self, sigma: List[float], labels: List[str] = None) -> Dict:
        """파이 차트 데이터 생성"""
        labels = labels or ['공공', '생산', '개인']
        colors = ['#3b82f6', '#10b981', '#f59e0b']
        
        return {
            'type': 'pie',
            'data': [
                {'name': label, 'value': value * 100, 'color': color}
                for label, value, color in zip(labels, sigma, colors)
            ]
        }
    
    def create_gauge_chart_data(self, value: float, min_val: float = 0, max_val: float = 100) -> Dict:
        """게이지 차트 데이터 생성"""
        return {
            'type': 'gauge',
            'value': value,
            'min': min_val,
            'max': max_val,
            'zones': [
                {'min': 0, 'max': 30, 'color': 'rgba(239, 68, 68, 0.3)'},
                {'min': 30, 'max': 70, 'color': 'rgba(245, 158, 11, 0.3)'},
                {'min': 70, 'max': 100, 'color': 'rgba(16, 185, 129, 0.3)'}
            ]
        }
    
    def create_bar_chart_data(self, distribution: Dict) -> Dict:
        """바 차트 데이터 생성"""
        return {
            'type': 'bar',
            'data': [
                {'name': '공공', 'value': distribution.get('public', 0), 'color': '#3b82f6'},
                {'name': '생산', 'value': distribution.get('productive', 0), 'color': '#10b981'},
                {'name': '개인', 'value': distribution.get('individual', 0), 'color': '#f59e0b'}
            ]
        }
    
    def create_line_chart_data(self, history: List[Dict]) -> Dict:
        """라인 차트 데이터 생성"""
        return {
            'type': 'line',
            'data': [
                {
                    'timestamp': h.get('timestamp', ''),
                    'value': h.get('value', 0)
                }
                for h in history[-50:]  # 최근 50개
            ]
        }
