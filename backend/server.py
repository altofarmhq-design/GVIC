from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone

# Core imports
from core import GVICEngine, InternalControlSystem, GVICVisualizer, Database
from core.control import AlertLevel

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize GVIC components
gvic_engine = GVICEngine()
control_system = InternalControlSystem()
visualizer = GVICVisualizer()
gvic_database = Database()

# Create the main app
app = FastAPI(title="GVIC Dashboard API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ===== Pydantic Models =====
class ProcessRequest(BaseModel):
    value: float = Field(..., ge=0, le=100)
    source_type: str = "auto"

class SigmaUpdate(BaseModel):
    sigma: List[float] = Field(..., min_length=3, max_length=3)

class OmegaUpdate(BaseModel):
    V_pub_min: float = 0.2
    V_pub_max: float = 0.8
    V_ind_max: float = 0.5
    sum_constraint: float = 1.0

class BatchProcessRequest(BaseModel):
    items: List[Dict[str, Any]]

class SaveDataRequest(BaseModel):
    collection: str
    data: Dict[str, Any]

class QueryDataRequest(BaseModel):
    collection: str
    query: Dict[str, Any] = {}
    limit: int = 100

# ===== API Routes =====

@api_router.get("/")
async def root():
    return {"message": "GVIC Dashboard API", "version": "1.0.0"}

# ----- Engine Routes -----
@api_router.post("/engine/process")
async def process_value(request: ProcessRequest):
    """단일 값 처리"""
    result = gvic_engine.process({"value": request.value}, request.source_type)
    
    # Save to database
    try:
        await gvic_database.save_processing_result({
            "input": request.value,
            "result": result.data,
            "success": result.success,
            "errors": result.errors
        })
    except Exception as e:
        logging.warning(f"Failed to save result: {e}")
    
    return {
        "success": result.success,
        "data": result.data,
        "metadata": result.metadata,
        "errors": result.errors,
        "timestamp": result.timestamp
    }

@api_router.post("/engine/batch")
async def process_batch(request: BatchProcessRequest):
    """배치 처리"""
    results = gvic_engine.process_batch(request.items)
    return {
        "total": len(results),
        "success_count": sum(1 for r in results if r.success),
        "results": [{"success": r.success, "data": r.data, "errors": r.errors} for r in results]
    }

@api_router.get("/engine/status")
async def get_engine_status():
    """엔진 상태 조회"""
    return gvic_engine.get_system_status()

@api_router.post("/engine/reset")
async def reset_engine():
    """엔진 초기화"""
    gvic_engine.reset()
    return {"status": "reset", "message": "엔진이 초기화되었습니다"}

# ----- Config Routes -----
@api_router.get("/config/sigma")
async def get_sigma():
    """Σ 조회"""
    return {"sigma": gvic_engine.sigma}

@api_router.put("/config/sigma")
async def update_sigma(request: SigmaUpdate):
    """Σ 업데이트"""
    if abs(sum(request.sigma) - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail="Σ 합계는 1.0이어야 합니다")
    gvic_engine.update_sigma(request.sigma)
    
    # Save config
    await gvic_database.save_config("sigma", {"sigma": request.sigma})
    
    return {"status": "updated", "sigma": gvic_engine.sigma}

@api_router.get("/config/omega")
async def get_omega():
    """Ω 조회"""
    return {"omega": gvic_engine.omega}

@api_router.put("/config/omega")
async def update_omega(request: OmegaUpdate):
    """Ω 업데이트"""
    omega = request.model_dump()
    gvic_engine.update_omega(omega)
    
    # Save config
    await gvic_database.save_config("omega", omega)
    
    return {"status": "updated", "omega": gvic_engine.omega}

# ----- Control Routes -----
@api_router.get("/control/health")
async def get_health():
    """헬스 체크"""
    return control_system.run_health_checks()

@api_router.get("/control/alerts")
async def get_alerts():
    """알림 조회"""
    return {
        "active": [a.to_dict() for a in control_system.alert_manager.get_active_alerts()],
        "statistics": control_system.alert_manager.get_statistics()
    }

@api_router.post("/control/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """알림 해결"""
    success = control_system.alert_manager.resolve_alert(alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="알림을 찾을 수 없습니다")
    return {"status": "resolved", "alert_id": alert_id}

@api_router.get("/control/thresholds")
async def get_thresholds():
    """임계값 조회"""
    return control_system.threshold_manager.get_all()

# ----- Dashboard Routes -----
@api_router.get("/dashboard")
async def get_dashboard_data():
    """대시보드 전체 데이터"""
    engine_status = gvic_engine.get_system_status()
    control_data = control_system.get_dashboard_data()
    
    # Get convergence history for chart
    convergence_history = gvic_engine.convergence.convergence_history[-20:]
    
    return {
        "engine": engine_status,
        "control": control_data,
        "charts": {
            "distribution": visualizer.create_distribution_pie(
                engine_status.get("modules", {}).get("distributor", {})
            ).to_dict(),
            "convergence": visualizer.create_convergence_line(convergence_history).to_dict(),
            "balance": visualizer.create_balance_gauge(
                engine_status.get("balance_score", 0.8) if "balance_score" in engine_status else 0.8
            )
        },
        "summary": control_system.get_status_summary()
    }

@api_router.get("/dashboard/charts/distribution")
async def get_distribution_chart():
    """분배 차트 데이터"""
    stats = gvic_engine.distributor.get_statistics()
    distribution = {
        "public": stats.get("current_ratio", [0.5, 0.3, 0.2])[0] if isinstance(stats.get("current_ratio"), list) else 0.5,
        "productive": stats.get("current_ratio", [0.5, 0.3, 0.2])[1] if isinstance(stats.get("current_ratio"), list) else 0.3,
        "individual": stats.get("current_ratio", [0.5, 0.3, 0.2])[2] if isinstance(stats.get("current_ratio"), list) else 0.2,
    }
    return visualizer.create_distribution_pie(distribution).to_dict()

@api_router.get("/dashboard/charts/convergence")
async def get_convergence_chart():
    """수렴 차트 데이터"""
    history = gvic_engine.convergence.convergence_history[-20:]
    return visualizer.create_convergence_line(history).to_dict()

# ----- Data Tab Routes (💾 데이터) -----
@api_router.get("/data/stats")
async def get_data_stats():
    """데이터베이스 통계"""
    try:
        stats = await gvic_database.get_statistics()
        return {
            "status": "connected",
            "collections": stats
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

@api_router.get("/data/processing-results")
async def get_processing_results(limit: int = 50):
    """처리 결과 조회"""
    try:
        results = await gvic_database.get_processing_results(limit)
        return {"count": len(results), "results": results}
    except Exception as e:
        return {"count": 0, "results": [], "error": str(e)}

@api_router.get("/data/configs")
async def get_all_configs():
    """모든 설정 조회"""
    try:
        await gvic_database.connect()
        cursor = gvic_database.db.configs.find({}, {"_id": 0})
        configs = await cursor.to_list(length=100)
        return {"configs": configs}
    except Exception as e:
        return {"configs": [], "error": str(e)}

@api_router.get("/data/alerts")
async def get_all_alerts(active_only: bool = False, limit: int = 50):
    """알림 히스토리"""
    try:
        alerts = await gvic_database.get_alerts(active_only=active_only, limit=limit)
        return {"count": len(alerts), "alerts": alerts}
    except Exception as e:
        return {"count": 0, "alerts": [], "error": str(e)}

@api_router.get("/data/metrics")
async def get_all_metrics(name: Optional[str] = None, limit: int = 100):
    """메트릭 조회"""
    try:
        metrics = await gvic_database.get_metrics(name=name, limit=limit)
        return {"count": len(metrics), "metrics": metrics}
    except Exception as e:
        return {"count": 0, "metrics": [], "error": str(e)}

@api_router.post("/data/export")
async def export_data(collection: str):
    """데이터 내보내기"""
    try:
        await gvic_database.connect()
        if collection == "processing_results":
            data = await gvic_database.get_processing_results(limit=1000)
        elif collection == "alerts":
            data = await gvic_database.get_alerts(limit=1000)
        elif collection == "metrics":
            data = await gvic_database.get_metrics(limit=1000)
        elif collection == "configs":
            cursor = gvic_database.db.configs.find({}, {"_id": 0})
            data = await cursor.to_list(length=100)
        else:
            raise HTTPException(status_code=400, detail="Invalid collection")
        
        return {
            "collection": collection,
            "count": len(data),
            "data": data,
            "exported_at": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/data/clear/{collection}")
async def clear_collection(collection: str):
    """컬렉션 초기화"""
    valid_collections = ["processing_results", "alerts", "metrics"]
    if collection not in valid_collections:
        raise HTTPException(status_code=400, detail=f"Invalid collection. Valid: {valid_collections}")
    
    try:
        await gvic_database.connect()
        result = await gvic_database.db[collection].delete_many({})
        return {
            "status": "cleared",
            "collection": collection,
            "deleted_count": result.deleted_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ----- Legacy Routes -----
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    return status_checks

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """시작 시 데이터베이스 연결"""
    try:
        await gvic_database.connect()
        logger.info("GVIC Database connected")
    except Exception as e:
        logger.error(f"Database connection error: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
    await gvic_database.disconnect()
