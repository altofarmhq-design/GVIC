"""특허 3: 파이프라인 프로세서
데이터 파이프라인 처리
"""
from typing import Dict, List, Any, Callable
from datetime import datetime

class PipelineProcessor:
    """데이터 파이프라인 처리 클래스"""
    
    def __init__(self):
        self.stages: List[Dict] = []
        self.history: List[Dict] = []
    
    def add_stage(self, name: str, processor: Callable, config: Dict = None):
        """파이프라인 스테이지 추가"""
        self.stages.append({
            'name': name,
            'processor': processor,
            'config': config or {},
            'enabled': True
        })
    
    def process(self, data: Any) -> Dict:
        """파이프라인 실행"""
        result = data
        stage_results = []
        
        for stage in self.stages:
            if not stage['enabled']:
                continue
            
            try:
                result = stage['processor'](result, stage['config'])
                stage_results.append({
                    'stage': stage['name'],
                    'success': True,
                    'output_type': type(result).__name__
                })
            except Exception as e:
                stage_results.append({
                    'stage': stage['name'],
                    'success': False,
                    'error': str(e)
                })
                break
        
        record = {
            'timestamp': datetime.now().isoformat(),
            'stages_executed': len(stage_results),
            'success': all(s['success'] for s in stage_results),
            'details': stage_results
        }
        
        self.history.append(record)
        
        return {
            'result': result,
            'metadata': record
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.history)
        success = sum(1 for h in self.history if h['success'])
        
        return {
            'total_executions': total,
            'success_count': success,
            'success_rate': success / total if total > 0 else 0,
            'stages_count': len(self.stages)
        }
