"""워크플로우 관리 모듈"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

class WorkflowStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowManager:
    """워크플로우 관리자"""
    
    def __init__(self):
        self.workflows: Dict[str, Dict] = {}
        self.workflow_counter = 0
        self.execution_history: List[Dict] = []
    
    def create_workflow(self, name: str, steps: List[Dict]) -> str:
        """워크플로우 생성"""
        self.workflow_counter += 1
        workflow_id = f"WF-{self.workflow_counter:05d}"
        
        self.workflows[workflow_id] = {
            'id': workflow_id,
            'name': name,
            'steps': steps,
            'status': WorkflowStatus.PENDING,
            'created_at': datetime.now().isoformat(),
            'current_step': 0,
            'results': []
        }
        
        return workflow_id
    
    def execute_workflow(self, workflow_id: str, context: Dict = None) -> Dict:
        """워크플로우 실행"""
        if workflow_id not in self.workflows:
            return {'success': False, 'error': 'Workflow not found'}
        
        workflow = self.workflows[workflow_id]
        workflow['status'] = WorkflowStatus.RUNNING
        context = context or {}
        
        results = []
        
        for i, step in enumerate(workflow['steps']):
            workflow['current_step'] = i
            
            try:
                # 스텝 실행 (여기서는 시뮬레이션)
                step_result = {
                    'step': step.get('name', f'Step {i+1}'),
                    'success': True,
                    'output': step.get('config', {})
                }
                results.append(step_result)
                
            except Exception as e:
                step_result = {
                    'step': step.get('name', f'Step {i+1}'),
                    'success': False,
                    'error': str(e)
                }
                results.append(step_result)
                workflow['status'] = WorkflowStatus.FAILED
                break
        
        if workflow['status'] != WorkflowStatus.FAILED:
            workflow['status'] = WorkflowStatus.COMPLETED
        
        workflow['results'] = results
        workflow['completed_at'] = datetime.now().isoformat()
        
        self.execution_history.append({
            'workflow_id': workflow_id,
            'timestamp': datetime.now().isoformat(),
            'status': workflow['status'].value,
            'steps_completed': len([r for r in results if r['success']])
        })
        
        return {
            'success': workflow['status'] == WorkflowStatus.COMPLETED,
            'workflow_id': workflow_id,
            'results': results
        }
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """워크플로우 상태 조회"""
        if workflow_id not in self.workflows:
            return None
        
        wf = self.workflows[workflow_id]
        return {
            'id': wf['id'],
            'name': wf['name'],
            'status': wf['status'].value,
            'current_step': wf['current_step'],
            'total_steps': len(wf['steps']),
            'created_at': wf['created_at']
        }
    
    def get_statistics(self) -> Dict:
        """통계 정보 반환"""
        total = len(self.workflows)
        completed = sum(1 for w in self.workflows.values() if w['status'] == WorkflowStatus.COMPLETED)
        failed = sum(1 for w in self.workflows.values() if w['status'] == WorkflowStatus.FAILED)
        
        return {
            'total_workflows': total,
            'completed': completed,
            'failed': failed,
            'pending': total - completed - failed,
            'success_rate': completed / total if total > 0 else 0
        }
