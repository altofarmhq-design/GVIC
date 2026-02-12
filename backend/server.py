from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Import GVIC modules
from core import GVICEngine, InternalControlSystem, IOInterface, GVICVisualizer, WorkflowManager
from core import MultiDomainIntegrationSystem, DomainType, ProtocolType
from utils import ConfigManager, ProgressTracker

# Initialize components
config_mgr = ConfigManager(str(ROOT_DIR / "config/settings.json"))
tracker = ProgressTracker(str(ROOT_DIR / "data/progress_log.json"))
engine = GVICEngine(sigma=config_mgr.get_sigma(), omega=config_mgr.get_omega())
control_system = InternalControlSystem()
io_interface = IOInterface()
visualizer = GVICVisualizer()
workflow_mgr = WorkflowManager()
integration_system = MultiDomainIntegrationSystem()

# Create the main app
app = FastAPI(title="GVIC Engine API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Models ====================

class ProcessRequest(BaseModel):
    value: float = Field(..., ge=0, le=10)

class ProcessResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = []
    timestamp: str

class SigmaUpdate(BaseModel):
    sigma: List[float] = Field(..., min_length=3, max_length=3)

class OmegaUpdate(BaseModel):
    V_pub_min: float = 0.2
    V_pub_max: float = 0.5
    V_pro_min: float = 0.2
    V_pro_max: float = 0.5
    V_ind_min: float = 0.1
    V_ind_max: float = 0.5
    sum_constraint: float = 1.0

class IORequest(BaseModel):
    data: str
    format: str = "auto"

class LogEntry(BaseModel):
    phase: str
    action: str
    data: Optional[Dict[str, Any]] = None

class AlertResolve(BaseModel):
    alert_id: str

# ==================== Dashboard APIs ====================

@api_router.get("/")
async def root():
    return {"message": "GVIC Engine API v1.0.0"}

@api_router.get("/dashboard")
async def get_dashboard():
    """대시보드 데이터 조회"""
    status = engine.get_system_status()
    control_data = control_system.get_dashboard_data()
    
    sigma = config_mgr.get_sigma()
    balance_score = engine.convergence.calculate_balance_index()
    
    return {
        "metrics": {
            "total_processed": status.get("total_processed", 0),
            "success_rate": status.get("success_rate", 0),
            "active_alerts": control_data["alerts"]["statistics"].get("active", 0),
            "system_status": "active" if status.get("success_rate", 0) >= 0.5 or status.get("total_processed", 0) == 0 else "degraded"
        },
        "sigma": sigma,
        "omega": config_mgr.get_omega(),
        "balance_score": balance_score,
        "charts": {
            "distribution": visualizer.create_pie_chart_data(sigma),
            "balance": visualizer.create_gauge_chart_data(balance_score * 100)
        },
        "health": control_data["health"],
        "alerts": control_data["alerts"]
    }

@api_router.get("/status")
async def get_system_status():
    """시스템 상태 조회"""
    return engine.get_system_status()

# ==================== Processing APIs ====================

@api_router.post("/process", response_model=ProcessResponse)
async def process_value(request: ProcessRequest):
    """값 처리 실행"""
    result = engine.process({"value": request.value})
    
    # 로그 기록
    tracker.log("처리", "엔진 실행", {"value": request.value, "success": result.success})
    
    # MongoDB에 저장
    await db.processing_history.insert_one({
        "id": str(uuid.uuid4()),
        "input_value": request.value,
        "success": result.success,
        "data": result.data if result.success else None,
        "errors": result.errors,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return ProcessResponse(
        success=result.success,
        data=result.data,
        errors=result.errors,
        timestamp=result.timestamp
    )

@api_router.get("/process/history")
async def get_processing_history(limit: int = 20):
    """처리 이력 조회"""
    history = await db.processing_history.find(
        {}, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {"history": history, "count": len(history)}

# ==================== Configuration APIs ====================

@api_router.get("/config/sigma")
async def get_sigma():
    """시그마 조회"""
    return {"sigma": config_mgr.get_sigma()}

@api_router.put("/config/sigma")
async def update_sigma(request: SigmaUpdate):
    """시그마 업데이트"""
    sigma = request.sigma
    total = sum(sigma)
    
    if abs(total - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"시그마 합계가 1이 아닙니다: {total}")
    
    config_mgr.set_sigma(sigma)
    engine.update_sigma(sigma)
    
    tracker.log("설정", "Σ 업데이트", {"sigma": sigma})
    
    return {"success": True, "sigma": sigma}

@api_router.get("/config/omega")
async def get_omega():
    """오메가 조회"""
    return {"omega": config_mgr.get_omega()}

@api_router.put("/config/omega")
async def update_omega(request: OmegaUpdate):
    """오메가 업데이트"""
    omega = request.model_dump()
    
    config_mgr.set_omega(omega)
    engine.update_omega(omega)
    
    tracker.log("설정", "Ω 업데이트", omega)
    
    return {"success": True, "omega": omega}

@api_router.get("/config")
async def get_all_config():
    """모든 설정 조회"""
    return config_mgr.get_all()

# ==================== IO APIs ====================

@api_router.post("/io/process")
async def process_io(request: IORequest):
    """입출력 처리"""
    result = io_interface.process_input(request.data, format=request.format)
    
    tracker.log("데이터", "IO 처리", {"format": request.format})
    
    return {"success": True, "data": result, "format": request.format}

@api_router.get("/io/statistics")
async def get_io_statistics():
    """IO 통계 조회"""
    return io_interface.get_statistics()

# ==================== Alert APIs ====================

@api_router.get("/alerts")
async def get_alerts():
    """알림 조회"""
    active = control_system.alert_manager.get_active_alerts()
    stats = control_system.alert_manager.get_statistics()
    
    return {
        "active_alerts": [
            {
                "id": a.id,
                "level": a.level.value,
                "component": a.component,
                "message": a.message,
                "timestamp": a.timestamp
            }
            for a in active
        ],
        "statistics": stats
    }

@api_router.post("/alerts/resolve")
async def resolve_alert(request: AlertResolve):
    """알림 해결"""
    success = control_system.alert_manager.resolve_alert(request.alert_id)
    
    if success:
        tracker.log("알림", "알림 해결", {"alert_id": request.alert_id})
    
    return {"success": success}

@api_router.post("/health-check")
async def run_health_check():
    """헬스체크 실행"""
    results = control_system.run_health_checks()
    
    tracker.log("알림", "헬스체크 실행", {})
    
    return {"results": results, "summary": control_system.health_checker.get_system_health()}

# ==================== Log APIs ====================

@api_router.get("/logs")
async def get_logs(count: int = 10):
    """로그 조회"""
    logs = tracker.get_recent_logs(count)
    return {"logs": logs, "count": len(logs)}

@api_router.post("/logs")
async def create_log(entry: LogEntry):
    """로그 생성"""
    tracker.log(entry.phase, entry.action, entry.data)
    return {"success": True}

@api_router.delete("/logs")
async def clear_logs():
    """로그 초기화"""
    tracker.clear_logs()
    return {"success": True}

@api_router.get("/logs/statistics")
async def get_log_statistics():
    """로그 통계 조회"""
    return tracker.get_statistics()

# ==================== Module Status APIs ====================

@api_router.get("/modules")
async def get_module_status():
    """모듈 상태 조회"""
    return {
        "modules": [
            {"name": "엔진", "status": "active", "description": "GVIC 통합 엔진"},
            {"name": "입출력", "status": "active", "description": "IO 인터페이스"},
            {"name": "내부통제", "status": "active", "description": "알림 및 헬스체크"},
            {"name": "워크플로우", "status": "active", "description": "워크플로우 관리"},
            {"name": "시각화", "status": "active", "description": "차트 데이터 생성"}
        ]
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
