from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import FileResponse
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
from io import BytesIO
import tempfile

# Load environment
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Import GVIC modules
from core import GVICEngine, InternalControlSystem, IOInterface, GVICVisualizer, WorkflowManager
from core import MultiDomainIntegrationSystem
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
            {"name": "시각화", "status": "active", "description": "차트 데이터 생성"},
            {"name": "다중도메인통합", "status": "active", "description": "도메인 통합 인터페이스"}
        ]
    }

# ==================== Multi-Domain Integration APIs ====================

class ExchangeRequest(BaseModel):
    data: Dict[str, Any]
    source_domain: str
    message_type: str = "default"

class AdapterCreate(BaseModel):
    domain_id: str
    domain_type: str = "custom"
    protocol: str = "rest"
    endpoint: str = ""

class MappingCreate(BaseModel):
    source_domain: str
    source_field: str
    target_domain: str
    target_field: str
    similarity_score: float = 1.0

class RoutingRuleCreate(BaseModel):
    name: str
    source_domain: str
    message_type: str
    target_domains: List[str]
    priority: int = 0

@api_router.get("/integration/status")
async def get_integration_status():
    """통합 시스템 상태 조회"""
    return integration_system.get_system_status()

@api_router.post("/integration/exchange")
async def execute_exchange(request: ExchangeRequest):
    """데이터 교환 실행"""
    result = integration_system.exchange(
        request.data, 
        request.source_domain, 
        request.message_type
    )
    
    tracker.log("통합", "데이터 교환", {
        "source": request.source_domain,
        "success": result['success']
    })
    
    return result

@api_router.get("/integration/adapters")
async def get_adapters():
    """어댑터 목록 조회"""
    return {"adapters": integration_system.get_adapters()}

@api_router.post("/integration/adapters")
async def create_adapter(request: AdapterCreate):
    """어댑터 추가"""
    adapter = integration_system.add_adapter(
        request.domain_id,
        request.domain_type,
        request.protocol,
        request.endpoint
    )
    tracker.log("통합", "어댑터 추가", {"domain_id": request.domain_id})
    return {"success": True, "adapter": adapter}

@api_router.get("/integration/mappings")
async def get_mappings():
    """의미 매핑 목록 조회"""
    return {"mappings": integration_system.get_mappings()}

@api_router.post("/integration/mappings")
async def create_mapping(request: MappingCreate):
    """의미 매핑 추가"""
    mapping = integration_system.add_mapping(
        request.source_domain,
        request.source_field,
        request.target_domain,
        request.target_field,
        request.similarity_score
    )
    tracker.log("통합", "매핑 추가", {
        "source": f"{request.source_domain}.{request.source_field}",
        "target": f"{request.target_domain}.{request.target_field}"
    })
    return {"success": True, "mapping": mapping}

@api_router.get("/integration/routing")
async def get_routing_rules():
    """라우팅 규칙 목록 조회"""
    return {"rules": integration_system.get_routing_rules()}

@api_router.post("/integration/routing")
async def create_routing_rule(request: RoutingRuleCreate):
    """라우팅 규칙 추가"""
    rule = integration_system.add_routing_rule(
        request.name,
        request.source_domain,
        request.message_type,
        request.target_domains,
        request.priority
    )
    tracker.log("통합", "라우팅 규칙 추가", {"name": request.name})
    return {"success": True, "rule": rule}

# ==================== Report Generation APIs ====================

class ReportRequest(BaseModel):
    record_id: Optional[str] = None
    include_history: bool = True
    limit: int = 10

@api_router.post("/report/generate")
async def generate_report(request: ReportRequest):
    """PDF 분석 리포트 생성"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # 데이터 수집
    if request.record_id:
        record = await db.processing_history.find_one({"id": request.record_id}, {"_id": 0})
        if not record:
            raise HTTPException(status_code=404, detail="Record not found")
        records = [record]
    else:
        records = await db.processing_history.find(
            {}, {"_id": 0}
        ).sort("timestamp", -1).limit(request.limit).to_list(request.limit)
    
    # 시스템 상태
    status = engine.get_system_status()
    sigma = config_mgr.get_sigma()
    omega = config_mgr.get_omega()
    balance_score = engine.convergence.calculate_balance_index()
    
    # PDF 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=30, textColor=colors.HexColor('#1e293b'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=16, spaceAfter=12, textColor=colors.HexColor('#334155'))
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontSize=11, spaceAfter=8)
    
    elements = []
    
    # 제목
    elements.append(Paragraph("GVIC Engine Analysis Report", title_style))
    elements.append(Paragraph(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", normal_style))
    elements.append(Spacer(1, 20))
    
    # 시스템 개요
    elements.append(Paragraph("1. System Overview", heading_style))
    overview_data = [
        ["Metric", "Value"],
        ["Total Processed", str(status.get("total_processed", 0))],
        ["Success Rate", f"{status.get('success_rate', 0) * 100:.1f}%"],
        ["Balance Score", f"{balance_score * 100:.1f}%"],
        ["System Status", "Active" if status.get("success_rate", 0) >= 0.5 else "Degraded"]
    ]
    overview_table = Table(overview_data, colWidths=[8*cm, 8*cm])
    overview_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(overview_table)
    elements.append(Spacer(1, 20))
    
    # Sigma (분배 비율)
    elements.append(Paragraph("2. Distribution Ratio (Sigma)", heading_style))
    sigma_data = [
        ["Category", "Ratio", "Percentage"],
        ["Public (V_pub)", f"{sigma[0]:.3f}", f"{sigma[0]*100:.1f}%"],
        ["Productive (V_pro)", f"{sigma[1]:.3f}", f"{sigma[1]*100:.1f}%"],
        ["Individual (V_ind)", f"{sigma[2]:.3f}", f"{sigma[2]*100:.1f}%"],
        ["Total", f"{sum(sigma):.3f}", f"{sum(sigma)*100:.1f}%"]
    ]
    sigma_table = Table(sigma_data, colWidths=[6*cm, 5*cm, 5*cm])
    sigma_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -2), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#d1fae5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(sigma_table)
    elements.append(Spacer(1, 20))
    
    # Omega (경계 조건)
    elements.append(Paragraph("3. Boundary Conditions (Omega)", heading_style))
    omega_data = [
        ["Parameter", "Min", "Max"],
        ["V_pub", f"{omega.get('V_pub_min', 0.2):.2f}", f"{omega.get('V_pub_max', 0.5):.2f}"],
        ["V_pro", f"{omega.get('V_pro_min', 0.2):.2f}", f"{omega.get('V_pro_max', 0.5):.2f}"],
        ["V_ind", f"{omega.get('V_ind_min', 0.1):.2f}", f"{omega.get('V_ind_max', 0.5):.2f}"]
    ]
    omega_table = Table(omega_data, colWidths=[6*cm, 5*cm, 5*cm])
    omega_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
    ]))
    elements.append(omega_table)
    elements.append(Spacer(1, 20))
    
    # 처리 이력
    if records:
        elements.append(Paragraph(f"4. Processing History (Last {len(records)} records)", heading_style))
        history_data = [["Timestamp", "Input", "Asset Value", "Balance", "Status"]]
        for rec in records:
            history_data.append([
                rec.get("timestamp", "")[:19].replace("T", " "),
                str(rec.get("input_value", "-")),
                f"{rec.get('data', {}).get('asset', {}).get('value', 0):.3f}" if rec.get("success") else "-",
                f"{rec.get('data', {}).get('balance_score', 0) * 100:.1f}%" if rec.get("success") else "-",
                "Success" if rec.get("success") else "Failed"
            ])
        history_table = Table(history_data, colWidths=[4*cm, 2.5*cm, 3*cm, 3*cm, 2.5*cm])
        history_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1'))
        ]))
        elements.append(history_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Generated by GVIC Engine v2.0.0 - 7 Patent Module Integration System", 
                             ParagraphStyle('Footer', fontSize=9, textColor=colors.gray)))
    
    doc.build(elements)
    
    tracker.log("리포트", "PDF 생성", {"records": len(records)})
    
    return FileResponse(
        temp_file.name, 
        media_type="application/pdf",
        filename=f"gvic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

@api_router.get("/report/summary")
async def get_report_summary():
    """리포트 요약 데이터 조회"""
    # 최근 처리 통계
    total_count = await db.processing_history.count_documents({})
    success_count = await db.processing_history.count_documents({"success": True})
    
    # 최근 10건 평균
    recent = await db.processing_history.find(
        {"success": True}, {"_id": 0}
    ).sort("timestamp", -1).limit(10).to_list(10)
    
    avg_asset = 0
    avg_balance = 0
    if recent:
        values = [r.get("data", {}).get("asset", {}).get("value", 0) for r in recent]
        balances = [r.get("data", {}).get("balance_score", 0) for r in recent]
        avg_asset = sum(values) / len(values)
        avg_balance = sum(balances) / len(balances)
    
    return {
        "total_records": total_count,
        "success_records": success_count,
        "success_rate": success_count / total_count if total_count > 0 else 0,
        "recent_avg_asset": avg_asset,
        "recent_avg_balance": avg_balance,
        "sigma": config_mgr.get_sigma(),
        "omega": config_mgr.get_omega(),
        "balance_score": engine.convergence.calculate_balance_index()
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
