"""
C: EXEC - 집행 특허 모듈
실행 결정 및 워크플로우 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/c", tags=["C:EXEC"])
logger = logging.getLogger(__name__)

class ExecutionRequest(BaseModel):
    """실행 요청"""
    signal_id: str
    action: str
    parameters: Dict[str, Any] = {}

class WorkflowStep(BaseModel):
    """워크플로우 단계"""
    step_id: str
    name: str
    action: str
    status: str = "pending"

# ==================== 실행 관리 ====================

@router.post("/execute")
async def execute_action(request: ExecutionRequest):
    """액션 실행"""
    from server import db
    
    valid_actions = ["analyze", "assetize", "modularize", "archive", "delete"]
    
    if request.action not in valid_actions:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 액션: {request.action}")
    
    # 실행 로그 생성
    execution_log = {
        "execution_id": f"EXEC_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "signal_id": request.signal_id,
        "action": request.action,
        "parameters": request.parameters,
        "status": "started",
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 액션별 처리
    result = {}
    
    if request.action == "analyze":
        from core.ai_analyzer import analyze_signal
        signal = await db.pipeline_signals.find_one({"signal_id": request.signal_id}, {"_id": 0})
        if signal:
            result = await analyze_signal(signal.get("content", ""), "", "", "general")
            execution_log["status"] = "completed"
        else:
            execution_log["status"] = "failed"
            execution_log["error"] = "시그널을 찾을 수 없음"
    
    elif request.action == "assetize":
        from module_system import extract_assets
        execution_log["status"] = "completed"
        result = {"message": "자산화 요청됨"}
    
    elif request.action == "archive":
        await db.pipeline_signals.update_one(
            {"signal_id": request.signal_id},
            {"$set": {"status": "archived", "archived_at": datetime.now(timezone.utc).isoformat()}}
        )
        execution_log["status"] = "completed"
        result = {"message": "아카이브됨"}
    
    execution_log["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution_log["result"] = result
    
    await db.execution_logs.insert_one(execution_log)
    
    return {
        "success": execution_log["status"] == "completed",
        "execution_id": execution_log["execution_id"],
        "action": request.action,
        "status": execution_log["status"],
        "result": result
    }

@router.get("/actions")
async def get_available_actions():
    """사용 가능한 액션 목록"""
    actions = [
        {"action": "analyze", "name": "분석", "description": "AI 분석 수행"},
        {"action": "assetize", "name": "자산화", "description": "자산으로 변환"},
        {"action": "modularize", "name": "모듈화", "description": "모듈에 추가"},
        {"action": "archive", "name": "아카이브", "description": "보관 처리"},
        {"action": "delete", "name": "삭제", "description": "영구 삭제"}
    ]
    return {"success": True, "actions": actions}

@router.get("/queue")
async def get_execution_queue():
    """실행 대기열 조회"""
    from server import db
    
    queue = await db.execution_logs.find(
        {"status": {"$in": ["pending", "started"]}},
        {"_id": 0}
    ).sort("started_at", -1).limit(50).to_list(50)
    
    return {"success": True, "queue": queue, "count": len(queue)}

@router.get("/history")
async def get_execution_history(limit: int = 50):
    """실행 이력 조회"""
    from server import db
    
    history = await db.execution_logs.find(
        {},
        {"_id": 0}
    ).sort("started_at", -1).limit(limit).to_list(limit)
    
    return {"success": True, "history": history, "count": len(history)}

@router.post("/batch-execute")
async def batch_execute(signal_ids: List[str], action: str):
    """배치 실행"""
    results = []
    
    for signal_id in signal_ids:
        try:
            result = await execute_action(ExecutionRequest(
                signal_id=signal_id,
                action=action
            ))
            results.append({"signal_id": signal_id, "success": True, "result": result})
        except Exception as e:
            results.append({"signal_id": signal_id, "success": False, "error": str(e)})
    
    success_count = sum(1 for r in results if r["success"])
    
    return {
        "success": True,
        "total": len(signal_ids),
        "succeeded": success_count,
        "failed": len(signal_ids) - success_count,
        "results": results
    }
