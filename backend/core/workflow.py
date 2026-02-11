"""
워크플로우 관리 모듈
작업 흐름 및 스케줄링
"""
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import threading
import time

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

@dataclass
class WorkflowStep:
    """워크플로우 단계"""
    id: str
    name: str
    handler: Callable
    config: Dict = field(default_factory=dict)
    status: WorkflowStatus = WorkflowStatus.PENDING
    result: Any = None
    error: str = None

@dataclass
class Workflow:
    """워크플로우"""
    id: str
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: str = None
    completed_at: str = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status.value,
            "steps": len(self.steps),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }

class WorkflowEngine:
    """워크플로우 엔진"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
    
    def create_workflow(self, name: str) -> Workflow:
        """워크플로우 생성"""
        workflow = Workflow(
            id=f"WF-{uuid.uuid4().hex[:8].upper()}",
            name=name
        )
        self.workflows[workflow.id] = workflow
        return workflow
    
    def add_step(self, workflow_id: str, name: str, handler: Callable, config: Dict = None) -> WorkflowStep:
        """단계 추가"""
        if workflow_id not in self.workflows:
            raise ValueError(f"워크플로우 없음: {workflow_id}")
        
        step = WorkflowStep(
            id=f"STEP-{uuid.uuid4().hex[:6].upper()}",
            name=name,
            handler=handler,
            config=config or {}
        )
        self.workflows[workflow_id].steps.append(step)
        return step
    
    def execute(self, workflow_id: str, input_data: Any = None) -> Dict:
        """워크플로우 실행"""
        if workflow_id not in self.workflows:
            return {"error": "워크플로우 없음"}
        
        workflow = self.workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        
        current_data = input_data
        
        try:
            for step in workflow.steps:
                step.status = WorkflowStatus.RUNNING
                try:
                    current_data = step.handler(current_data, step.config)
                    step.result = current_data
                    step.status = WorkflowStatus.COMPLETED
                except Exception as e:
                    step.status = WorkflowStatus.FAILED
                    step.error = str(e)
                    raise
            
            workflow.status = WorkflowStatus.COMPLETED
            
        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
        
        workflow.completed_at = datetime.now().isoformat()
        
        return {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "result": current_data
        }

@dataclass
class ScheduledTask:
    """스케줄된 작업"""
    id: str
    name: str
    handler: Callable
    interval_seconds: int
    next_run: datetime
    enabled: bool = True
    last_run: datetime = None
    run_count: int = 0

class Scheduler:
    """스케줄러"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: threading.Thread = None
    
    def add_task(self, name: str, handler: Callable, interval_seconds: int) -> ScheduledTask:
        """작업 추가"""
        task = ScheduledTask(
            id=f"TASK-{uuid.uuid4().hex[:6].upper()}",
            name=name,
            handler=handler,
            interval_seconds=interval_seconds,
            next_run=datetime.now() + timedelta(seconds=interval_seconds)
        )
        self.tasks[task.id] = task
        return task
    
    def remove_task(self, task_id: str):
        """작업 제거"""
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def start(self):
        """스케줄러 시작"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """스케줄러 중지"""
        self._running = False
    
    def _run_loop(self):
        """실행 루프"""
        while self._running:
            now = datetime.now()
            for task in self.tasks.values():
                if task.enabled and now >= task.next_run:
                    try:
                        task.handler()
                        task.last_run = now
                        task.run_count += 1
                    except:
                        pass
                    task.next_run = now + timedelta(seconds=task.interval_seconds)
            time.sleep(1)
    
    def get_status(self) -> Dict:
        """상태 조회"""
        return {
            "running": self._running,
            "tasks": {t.id: {"name": t.name, "enabled": t.enabled, "run_count": t.run_count} 
                     for t in self.tasks.values()}
        }

class WorkflowManager:
    """워크플로우 관리자"""
    
    def __init__(self):
        self.engine = WorkflowEngine()
        self.scheduler = Scheduler()
    
    def create_and_execute(self, name: str, steps: List[Dict], input_data: Any = None) -> Dict:
        """워크플로우 생성 및 실행"""
        workflow = self.engine.create_workflow(name)
        
        for step_def in steps:
            self.engine.add_step(
                workflow.id,
                step_def["name"],
                step_def["handler"],
                step_def.get("config", {})
            )
        
        return self.engine.execute(workflow.id, input_data)
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        workflows = list(self.engine.workflows.values())
        return {
            "total_workflows": len(workflows),
            "completed": sum(1 for w in workflows if w.status == WorkflowStatus.COMPLETED),
            "failed": sum(1 for w in workflows if w.status == WorkflowStatus.FAILED),
            "scheduler": self.scheduler.get_status()
        }
