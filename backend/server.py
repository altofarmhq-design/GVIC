from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request
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

# Import auth module
from auth import create_auth_router

# Create auth router and get dependencies
auth_router = create_auth_router(db)
get_current_user = auth_router.get_current_user
require_role = auth_router.require_role

# Import GVIC modules
from core import GVICEngine, InternalControlSystem, IOInterface, GVICVisualizer, WorkflowManager
from core import MultiDomainIntegrationSystem
from core.data_hub import init_data_hub, get_data_hub
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

# Initialize Data Hub (모든 탭 연동)
data_hub = init_data_hub(db)

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
    """대시보드 데이터 조회 (모든 분석 데이터 통합)"""
    status = engine.get_system_status()
    control_data = control_system.get_dashboard_data()
    
    sigma = config_mgr.get_sigma()
    balance_score = engine.convergence.calculate_balance_index()
    
    # 데이터 허브에서 통합 데이터 조회
    hub_data = await data_hub.get_dashboard_data()
    
    return {
        "metrics": {
            "total_processed": hub_data.get("total_records_processed", status.get("total_processed", 0)),
            "success_rate": status.get("success_rate", 0),
            "active_alerts": control_data["alerts"]["statistics"].get("active", 0),
            "system_status": "active" if status.get("success_rate", 0) >= 0.5 or status.get("total_processed", 0) == 0 else "degraded",
            "total_sessions": hub_data.get("total_sessions", 0),
            "avg_positive_ratio": hub_data.get("avg_positive_ratio", 0),
            "avg_fairness_index": hub_data.get("avg_fairness_index", 0)
        },
        "sigma": sigma,
        "omega": config_mgr.get_omega(),
        "balance_score": balance_score,
        "charts": {
            "distribution": visualizer.create_pie_chart_data(sigma),
            "balance": visualizer.create_gauge_chart_data(balance_score * 100)
        },
        "health": control_data["health"],
        "alerts": control_data["alerts"],
        "recent_sessions": hub_data.get("recent_sessions", []),
        "last_updated": hub_data.get("last_updated", "")
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

# ==================== Real-time Monitoring APIs ====================

import random
import time

# 모니터링 데이터 저장소 (메모리)
# ==================== 실시간 시그널 모니터링 시스템 ====================
real_signal_monitor = {
    "signal_history": [],          # 실제 시그널 처리 기록
    "analysis_history": [],        # 분석 이력
    "asset_history": [],           # 자산화 이력
    "alerts": [],                  # 알림
    "stats": {
        "total_analyzed": 0,       # 총 분석 건수
        "total_assets": 0,         # 총 자산화 건수
        "success_rate": 0,         # 성공률
        "by_signal_type": {},      # 시그널 유형별 통계
        "by_sentiment": {},        # 감성별 통계
        "last_hour_count": 0,      # 최근 1시간 처리량
        "last_update": None
    }
}

def record_signal_analysis(input_text: str, result: dict, success: bool = True):
    """실제 시그널 분석 결과 기록"""
    now = datetime.now(timezone.utc)
    
    record = {
        "timestamp": now.isoformat(),
        "time_display": now.strftime("%H:%M:%S"),
        "input_length": len(input_text),
        "success": success,
        "signal_type": result.get("signal_type", "unknown"),
        "signal_type_label": result.get("signal_type_label", "알 수 없음"),
        "signal_count": result.get("signal_count", 0),
        "overall_sentiment": result.get("overall_sentiment", "neutral"),
        "module_id": result.get("module_id", ""),
        "input_id": result.get("input_id", "")
    }
    
    # 히스토리에 추가 (최대 100개 유지)
    real_signal_monitor["signal_history"].append(record)
    if len(real_signal_monitor["signal_history"]) > 100:
        real_signal_monitor["signal_history"] = real_signal_monitor["signal_history"][-100:]
    
    # 통계 업데이트
    stats = real_signal_monitor["stats"]
    stats["total_analyzed"] += 1
    stats["last_update"] = now.isoformat()
    
    # 시그널 유형별 통계
    sig_type = result.get("signal_type_label", "unknown")
    stats["by_signal_type"][sig_type] = stats["by_signal_type"].get(sig_type, 0) + 1
    
    # 감성별 통계
    sentiment = result.get("overall_sentiment", "neutral")
    stats["by_sentiment"][sentiment] = stats["by_sentiment"].get(sentiment, 0) + 1
    
    # 성공률 계산
    success_count = sum(1 for r in real_signal_monitor["signal_history"] if r.get("success", False))
    stats["success_rate"] = success_count / len(real_signal_monitor["signal_history"]) if real_signal_monitor["signal_history"] else 0
    
    # 최근 1시간 처리량
    one_hour_ago = now - timedelta(hours=1)
    stats["last_hour_count"] = sum(
        1 for r in real_signal_monitor["signal_history"] 
        if datetime.fromisoformat(r["timestamp"].replace('Z', '+00:00')) > one_hour_ago
    )

def record_asset_creation(asset_data: dict):
    """자산화 기록"""
    now = datetime.now(timezone.utc)
    
    record = {
        "timestamp": now.isoformat(),
        "time_display": now.strftime("%H:%M:%S"),
        "asset_id": asset_data.get("asset_id", ""),
        "signal_type": asset_data.get("signal_type_label", ""),
        "classification": asset_data.get("classification", ""),
        "signal_count": asset_data.get("signal_count", 0)
    }
    
    real_signal_monitor["asset_history"].append(record)
    if len(real_signal_monitor["asset_history"]) > 50:
        real_signal_monitor["asset_history"] = real_signal_monitor["asset_history"][-50:]
    
    real_signal_monitor["stats"]["total_assets"] += 1

def get_realtime_signal_stats():
    """실시간 시그널 통계 조회"""
    stats = real_signal_monitor["stats"]
    history = real_signal_monitor["signal_history"]
    
    # 최근 20개 기록의 시그널 수 합계 (차트용)
    recent_signals = history[-20:] if history else []
    chart_data = [
        {
            "time": r["time_display"],
            "signals": r["signal_count"],
            "sentiment": 1 if r["overall_sentiment"] == "positive" else -1 if r["overall_sentiment"] == "negative" else 0
        }
        for r in recent_signals
    ]
    
    # 상태 결정
    if stats["last_hour_count"] > 50:
        status = "active"
    elif stats["last_hour_count"] > 10:
        status = "normal"
    elif stats["last_hour_count"] > 0:
        status = "low"
    else:
        status = "idle"
    
    return {
        "total_analyzed": stats["total_analyzed"],
        "total_assets": stats["total_assets"],
        "success_rate": stats["success_rate"],
        "last_hour_count": stats["last_hour_count"],
        "by_signal_type": stats["by_signal_type"],
        "by_sentiment": stats["by_sentiment"],
        "status": status,
        "chart_data": chart_data,
        "recent_signals": recent_signals[-10:],
        "recent_assets": real_signal_monitor["asset_history"][-10:],
        "last_update": stats["last_update"]
    }

# 기존 시뮬레이션 데이터 (호환성 유지)
monitoring_data = {
    "consumption": [],
    "distribution_history": [],
    "alerts": [],
    "last_update": None
}

def generate_monitoring_data():
    """실시간 모니터링 데이터 생성 - 실제 데이터 + 시뮬레이션 혼합"""
    now = datetime.now(timezone.utc)
    sigma = config_mgr.get_sigma()
    
    # 실제 시그널 데이터가 있으면 활용
    real_stats = get_realtime_signal_stats()
    
    if real_stats["total_analyzed"] > 0:
        # 실제 데이터 기반
        sentiment_data = real_stats["by_sentiment"]
        positive = sentiment_data.get("positive", 0)
        negative = sentiment_data.get("negative", 0)
        neutral = sentiment_data.get("neutral", 0) + sentiment_data.get("mixed", 0)
        total = positive + negative + neutral or 1
        
        consumption = {
            "timestamp": now.isoformat(),
            "public": neutral * 10,      # 중립 → 공공
            "productive": positive * 10,  # 긍정 → 생산
            "individual": negative * 10,  # 부정 → 소비자
            "total": total * 10
        }
    else:
        # 시뮬레이션 데이터
        base_consumption = [100, 120, 80]
        consumption = {
            "timestamp": now.isoformat(),
            "public": base_consumption[0] * (1 + random.uniform(-0.1, 0.1)),
            "productive": base_consumption[1] * (1 + random.uniform(-0.1, 0.1)),
            "individual": base_consumption[2] * (1 + random.uniform(-0.1, 0.1)),
            "total": sum(base_consumption) * (1 + random.uniform(-0.05, 0.05))
        }
    
    total = consumption["total"] or 1
    actual_ratio = [
        consumption["public"] / total,
        consumption["productive"] / total,
        consumption["individual"] / total
    ]
    
    deviation = [abs(actual_ratio[i] - sigma[i]) for i in range(3)]
    avg_deviation = sum(deviation) / 3
    
    return {
        "consumption": consumption,
        "target_ratio": sigma,
        "actual_ratio": actual_ratio,
        "deviation": deviation,
        "avg_deviation": avg_deviation,
        "efficiency": 1 - avg_deviation,
        "status": "optimal" if avg_deviation < 0.05 else "adjusting" if avg_deviation < 0.1 else "alert",
        "real_signal_stats": real_stats  # 실제 시그널 통계 포함
    }

@api_router.get("/monitor/realtime")
async def get_realtime_monitoring():
    """실시간 모니터링 데이터 조회"""
    # 새 데이터 생성
    data = generate_monitoring_data()
    
    # 히스토리에 추가 (최대 60개 유지 - 1분 데이터)
    monitoring_data["consumption"].append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "public": data["consumption"]["public"],
        "productive": data["consumption"]["productive"],
        "individual": data["consumption"]["individual"]
    })
    if len(monitoring_data["consumption"]) > 60:
        monitoring_data["consumption"] = monitoring_data["consumption"][-60:]
    
    monitoring_data["last_update"] = datetime.now(timezone.utc).isoformat()
    
    return {
        "current": data,
        "history": monitoring_data["consumption"][-20:],  # 최근 20개
        "last_update": monitoring_data["last_update"]
    }

@api_router.get("/monitor/signals")
async def get_signal_monitoring():
    """실시간 시그널 모니터링 - 실제 데이터"""
    return get_realtime_signal_stats()

@api_router.get("/dashboard/realstats")
async def get_real_dashboard_stats():
    """대시보드 실제 통계"""
    # 실제 시그널 통계
    signal_stats = get_realtime_signal_stats()
    
    # MongoDB에서 실제 자산 통계
    try:
        total_assets = await db.gvic_assets.count_documents({})
        positive_assets = await db.gvic_assets.count_documents({"classification": "긍정"})
        negative_assets = await db.gvic_assets.count_documents({"classification": "부정"})
        mixed_assets = await db.gvic_assets.count_documents({"classification": "혼합"})
        neutral_assets = await db.gvic_assets.count_documents({"classification": "중립"})
        
        # 시그널 유형별 통계
        signal_type_pipeline = [
            {"$group": {"_id": "$signal_type_label", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        signal_types = {}
        async for doc in db.gvic_assets.aggregate(signal_type_pipeline):
            if doc["_id"]:
                signal_types[doc["_id"]] = doc["count"]
        
        # 최근 처리 이력
        recent_cursor = db.gvic_assets.find({}, {"_id": 0, "asset_id": 1, "signal_type_label": 1, "classification": 1, "created_at": 1}).sort("created_at", -1).limit(10)
        recent_assets = await recent_cursor.to_list(length=10)
        
    except Exception as e:
        total_assets = 0
        positive_assets = 0
        negative_assets = 0
        mixed_assets = 0
        neutral_assets = 0
        signal_types = {}
        recent_assets = []
    
    return {
        # 실시간 분석 현황
        "realtime": {
            "total_analyzed": signal_stats["total_analyzed"],
            "last_hour_count": signal_stats["last_hour_count"],
            "success_rate": signal_stats["success_rate"],
            "status": signal_stats["status"]
        },
        # 자산 현황
        "assets": {
            "total": total_assets,
            "positive": positive_assets,
            "negative": negative_assets,
            "mixed": mixed_assets,
            "neutral": neutral_assets
        },
        # 시그널 유형별
        "by_signal_type": signal_types,
        # 감성별
        "by_sentiment": signal_stats["by_sentiment"],
        # 최근 처리
        "recent_assets": recent_assets,
        # 차트 데이터
        "chart_data": signal_stats["chart_data"],
        # 최근 시그널
        "recent_signals": signal_stats["recent_signals"],
        # 업데이트 시간
        "last_update": signal_stats["last_update"] or datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/monitor/distribution")
async def get_distribution_monitor():
    """분배 상태 모니터링"""
    sigma = config_mgr.get_sigma()
    omega = config_mgr.get_omega()
    
    # 실제 분배 상태 시뮬레이션
    actual = [
        sigma[0] + random.uniform(-0.02, 0.02),
        sigma[1] + random.uniform(-0.02, 0.02),
        sigma[2] + random.uniform(-0.02, 0.02)
    ]
    # 정규화
    total = sum(actual)
    actual = [a/total for a in actual]
    
    # 경계 조건 검증
    violations = []
    if actual[0] < omega.get("V_pub_min", 0.2):
        violations.append({"type": "V_pub_min", "current": actual[0], "limit": omega["V_pub_min"]})
    if actual[0] > omega.get("V_pub_max", 0.5):
        violations.append({"type": "V_pub_max", "current": actual[0], "limit": omega["V_pub_max"]})
    if actual[1] < omega.get("V_pro_min", 0.2):
        violations.append({"type": "V_pro_min", "current": actual[1], "limit": omega["V_pro_min"]})
    if actual[1] > omega.get("V_pro_max", 0.5):
        violations.append({"type": "V_pro_max", "current": actual[1], "limit": omega["V_pro_max"]})
    if actual[2] < omega.get("V_ind_min", 0.1):
        violations.append({"type": "V_ind_min", "current": actual[2], "limit": omega["V_ind_min"]})
    if actual[2] > omega.get("V_ind_max", 0.5):
        violations.append({"type": "V_ind_max", "current": actual[2], "limit": omega["V_ind_max"]})
    
    return {
        "target": sigma,
        "actual": actual,
        "omega": omega,
        "violations": violations,
        "is_valid": len(violations) == 0,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

# ==================== Dynamic Adjustment APIs (특허6: DynamicAdjuster) ====================

# 자동 조정 설정 저장소
auto_adjustment_config = {
    "enabled": False,
    "threshold": 0.05,  # 5% 편차 임계값
    "adjustment_rate": 0.01,  # 1% 조정률
    "max_adjustments": 10,  # 최대 조정 횟수
    "interval_seconds": 60,  # 조정 간격 (초)
    "last_adjustment": None,
    "adjustment_history": []
}

class AutoAdjustmentConfig(BaseModel):
    enabled: bool = False
    threshold: float = 0.05
    adjustment_rate: float = 0.01
    max_adjustments: int = 10
    interval_seconds: int = 60

@api_router.get("/adjustment/config")
async def get_adjustment_config():
    """자동 조정 설정 조회"""
    return auto_adjustment_config

@api_router.put("/adjustment/config")
async def update_adjustment_config(config: AutoAdjustmentConfig):
    """자동 조정 설정 업데이트"""
    auto_adjustment_config["enabled"] = config.enabled
    auto_adjustment_config["threshold"] = config.threshold
    auto_adjustment_config["adjustment_rate"] = config.adjustment_rate
    auto_adjustment_config["max_adjustments"] = config.max_adjustments
    auto_adjustment_config["interval_seconds"] = config.interval_seconds
    
    tracker.log("자동조정", "설정 변경", {
        "enabled": config.enabled,
        "threshold": config.threshold
    })
    
    return {"success": True, "config": auto_adjustment_config}

@api_router.post("/adjustment/execute")
async def execute_adjustment():
    """수동 조정 실행 (특허6: DynamicAdjuster 로직)"""
    sigma = config_mgr.get_sigma()
    omega = config_mgr.get_omega()
    
    # 현재 분배 상태 시뮬레이션
    actual = [
        sigma[0] + random.uniform(-0.05, 0.05),
        sigma[1] + random.uniform(-0.05, 0.05),
        sigma[2] + random.uniform(-0.05, 0.05)
    ]
    total = sum(actual)
    actual = [a/total for a in actual]
    
    # 편차 계산
    deviations = [abs(actual[i] - sigma[i]) for i in range(3)]
    max_deviation = max(deviations)
    
    adjustments = []
    new_sigma = list(sigma)
    
    # 임계값 초과 시 조정
    threshold = auto_adjustment_config["threshold"]
    rate = auto_adjustment_config["adjustment_rate"]
    
    for i in range(3):
        if deviations[i] > threshold:
            # 목표 방향으로 조정
            direction = 1 if actual[i] < sigma[i] else -1
            adjustment = direction * rate
            
            # 경계 조건 확인
            new_value = new_sigma[i] + adjustment
            category = ["V_pub", "V_pro", "V_ind"][i]
            min_key = f"{category}_min"
            max_key = f"{category}_max"
            
            # 경계 내로 제한
            new_value = max(omega.get(min_key, 0.1), min(omega.get(max_key, 0.5), new_value))
            
            adjustments.append({
                "category": ["public", "productive", "individual"][i],
                "from": sigma[i],
                "to": new_value,
                "deviation": deviations[i],
                "direction": "increase" if direction > 0 else "decrease"
            })
            new_sigma[i] = new_value
    
    # 정규화 (합이 1이 되도록)
    total_new = sum(new_sigma)
    new_sigma = [s/total_new for s in new_sigma]
    
    # 시그마 업데이트 (조정이 있을 경우만)
    if adjustments:
        config_mgr.update_sigma(new_sigma)
        
        # 이력 저장
        adjustment_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "old_sigma": sigma,
            "new_sigma": new_sigma,
            "adjustments": adjustments,
            "max_deviation": max_deviation
        }
        auto_adjustment_config["adjustment_history"].append(adjustment_record)
        if len(auto_adjustment_config["adjustment_history"]) > 100:
            auto_adjustment_config["adjustment_history"] = auto_adjustment_config["adjustment_history"][-100:]
        
        auto_adjustment_config["last_adjustment"] = datetime.now(timezone.utc).isoformat()
        
        tracker.log("자동조정", "조정 실행", {
            "adjustments_count": len(adjustments),
            "max_deviation": max_deviation
        })
    
    return {
        "success": True,
        "adjusted": len(adjustments) > 0,
        "old_sigma": sigma,
        "new_sigma": new_sigma,
        "adjustments": adjustments,
        "max_deviation": max_deviation,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/adjustment/history")
async def get_adjustment_history(limit: int = 20):
    """조정 이력 조회"""
    history = auto_adjustment_config["adjustment_history"][-limit:]
    return {
        "history": history,
        "total": len(auto_adjustment_config["adjustment_history"]),
        "last_adjustment": auto_adjustment_config["last_adjustment"]
    }

# ==================== Multi-Model Management APIs (특허6: 4100 모델 저장부) ====================

# 사전 정의된 분배 모델들
distribution_models = {
    "default": {
        "id": "default",
        "name": "기본 균형 모델",
        "description": "공공/생산/개인 균형 분배 (33/34/33)",
        "sigma": [0.33, 0.34, 0.33],
        "omega": {
            "V_pub_min": 0.2, "V_pub_max": 0.5,
            "V_pro_min": 0.2, "V_pro_max": 0.5,
            "V_ind_min": 0.1, "V_ind_max": 0.5
        },
        "type": "balanced",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "public_priority": {
        "id": "public_priority",
        "name": "공공 우선 모델",
        "description": "공공 영역 우선 분배 (45/30/25)",
        "sigma": [0.45, 0.30, 0.25],
        "omega": {
            "V_pub_min": 0.35, "V_pub_max": 0.55,
            "V_pro_min": 0.2, "V_pro_max": 0.4,
            "V_ind_min": 0.15, "V_ind_max": 0.35
        },
        "type": "public_priority",
        "is_active": False,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "productive_priority": {
        "id": "productive_priority",
        "name": "생산 우선 모델",
        "description": "생산 영역 우선 분배 (25/50/25)",
        "sigma": [0.25, 0.50, 0.25],
        "omega": {
            "V_pub_min": 0.15, "V_pub_max": 0.35,
            "V_pro_min": 0.4, "V_pro_max": 0.6,
            "V_ind_min": 0.15, "V_ind_max": 0.35
        },
        "type": "productive_priority",
        "is_active": False,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "individual_priority": {
        "id": "individual_priority",
        "name": "개인 우선 모델",
        "description": "개인 영역 우선 분배 (25/30/45)",
        "sigma": [0.25, 0.30, 0.45],
        "omega": {
            "V_pub_min": 0.15, "V_pub_max": 0.35,
            "V_pro_min": 0.2, "V_pro_max": 0.4,
            "V_ind_min": 0.35, "V_ind_max": 0.55
        },
        "type": "individual_priority",
        "is_active": False,
        "created_at": "2026-01-01T00:00:00Z"
    },
    "growth": {
        "id": "growth",
        "name": "성장 집중 모델",
        "description": "생산과 개인 집중 분배 (20/40/40)",
        "sigma": [0.20, 0.40, 0.40],
        "omega": {
            "V_pub_min": 0.1, "V_pub_max": 0.3,
            "V_pro_min": 0.3, "V_pro_max": 0.5,
            "V_ind_min": 0.3, "V_ind_max": 0.5
        },
        "type": "growth",
        "is_active": False,
        "created_at": "2026-01-01T00:00:00Z"
    }
}

current_model_id = "default"

class ModelCreateRequest(BaseModel):
    name: str
    description: str = ""
    sigma: List[float]
    omega: Dict[str, float]
    type: str = "custom"

@api_router.get("/models")
async def get_all_models():
    """모든 분배 모델 조회"""
    models_list = list(distribution_models.values())
    return {
        "models": models_list,
        "current_model_id": current_model_id,
        "total": len(models_list)
    }

@api_router.get("/models/{model_id}")
async def get_model(model_id: str):
    """특정 모델 조회"""
    if model_id not in distribution_models:
        raise HTTPException(status_code=404, detail="Model not found")
    return distribution_models[model_id]

@api_router.post("/models")
async def create_model(request: ModelCreateRequest):
    """새 분배 모델 생성"""
    # 시그마 합계 검증
    if abs(sum(request.sigma) - 1.0) > 0.01:
        raise HTTPException(status_code=400, detail="Sigma must sum to 1.0")
    
    model_id = f"custom_{uuid.uuid4().hex[:8]}"
    new_model = {
        "id": model_id,
        "name": request.name,
        "description": request.description,
        "sigma": request.sigma,
        "omega": request.omega,
        "type": request.type,
        "is_active": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    distribution_models[model_id] = new_model
    
    tracker.log("모델", "새 모델 생성", {"model_id": model_id, "name": request.name})
    
    return {"success": True, "model": new_model}

@api_router.post("/models/{model_id}/activate")
async def activate_model(model_id: str):
    """모델 활성화 (전환)"""
    global current_model_id
    
    if model_id not in distribution_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # 기존 활성 모델 비활성화
    for mid in distribution_models:
        distribution_models[mid]["is_active"] = False
    
    # 선택된 모델 활성화
    model = distribution_models[model_id]
    model["is_active"] = True
    current_model_id = model_id
    
    # 시그마와 오메가 업데이트
    config_mgr.update_sigma(model["sigma"])
    config_mgr.update_omega(model["omega"])
    
    tracker.log("모델", "모델 전환", {"model_id": model_id, "name": model["name"]})
    
    return {
        "success": True,
        "activated_model": model,
        "sigma": model["sigma"],
        "omega": model["omega"]
    }

@api_router.delete("/models/{model_id}")
async def delete_model(model_id: str):
    """커스텀 모델 삭제"""
    if model_id not in distribution_models:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model = distribution_models[model_id]
    
    # 기본 모델은 삭제 불가
    if not model_id.startswith("custom_"):
        raise HTTPException(status_code=400, detail="Cannot delete built-in models")
    
    # 활성 모델은 삭제 불가
    if model["is_active"]:
        raise HTTPException(status_code=400, detail="Cannot delete active model")
    
    del distribution_models[model_id]
    
    tracker.log("모델", "모델 삭제", {"model_id": model_id})
    
    return {"success": True, "deleted_model_id": model_id}

# ==================== Time Series Prediction APIs (시계열 예측 기반 사전 조정) ====================

import numpy as np
from collections import deque

# 예측 데이터 저장소
prediction_data = {
    "history": deque(maxlen=100),  # 최근 100개 데이터 포인트
    "predictions": [],
    "last_prediction": None
}

class PredictionConfig(BaseModel):
    window_size: int = 10  # 예측에 사용할 데이터 윈도우 크기
    forecast_steps: int = 5  # 예측할 미래 스텝 수
    confidence_threshold: float = 0.7  # 자동 조정 신뢰도 임계값
    auto_adjust: bool = False  # 예측 기반 자동 조정 활성화

prediction_config = {
    "window_size": 10,
    "forecast_steps": 5,
    "confidence_threshold": 0.7,
    "auto_adjust": False
}

def simple_moving_average_forecast(data: List[float], window: int, steps: int) -> List[float]:
    """단순 이동 평균 기반 예측"""
    if len(data) < window:
        return [data[-1] if data else 0.0] * steps
    
    forecasts = []
    recent = list(data[-window:])
    
    for _ in range(steps):
        pred = sum(recent) / len(recent)
        forecasts.append(pred)
        recent.pop(0)
        recent.append(pred)
    
    return forecasts

def exponential_smoothing_forecast(data: List[float], alpha: float, steps: int) -> List[float]:
    """지수 평활법 기반 예측"""
    if not data:
        return [0.0] * steps
    
    # 초기값
    smoothed = data[0]
    
    # 지수 평활
    for val in data[1:]:
        smoothed = alpha * val + (1 - alpha) * smoothed
    
    # 예측 (지수 평활법의 예측은 마지막 평활값)
    return [smoothed] * steps

def calculate_confidence(actual: List[float], predicted: List[float]) -> float:
    """예측 신뢰도 계산 (MAPE 기반)"""
    if not actual or not predicted:
        return 0.0
    
    n = min(len(actual), len(predicted))
    errors = []
    for i in range(n):
        if actual[i] != 0:
            error = abs(actual[i] - predicted[i]) / abs(actual[i])
            errors.append(error)
    
    if not errors:
        return 1.0
    
    mape = sum(errors) / len(errors)
    confidence = max(0, 1 - mape)
    return confidence

@api_router.get("/prediction/config")
async def get_prediction_config():
    """예측 설정 조회"""
    return prediction_config

@api_router.put("/prediction/config")
async def update_prediction_config(config: PredictionConfig):
    """예측 설정 업데이트"""
    prediction_config["window_size"] = config.window_size
    prediction_config["forecast_steps"] = config.forecast_steps
    prediction_config["confidence_threshold"] = config.confidence_threshold
    prediction_config["auto_adjust"] = config.auto_adjust
    
    tracker.log("예측", "설정 변경", {"auto_adjust": config.auto_adjust})
    return {"success": True, "config": prediction_config}

@api_router.post("/prediction/analyze")
async def analyze_and_predict():
    """시계열 분석 및 예측 수행"""
    # MongoDB에서 최근 처리 이력 조회
    history = await db.processing_history.find(
        {"success": True}, {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    if len(history) < 3:
        return {
            "success": False,
            "message": "예측을 위한 충분한 데이터가 없습니다 (최소 3건 필요)",
            "data_count": len(history)
        }
    
    # 데이터 추출 (역순으로 정렬 - 오래된 것부터)
    history = list(reversed(history))
    
    # 분배 비율 데이터 추출
    public_ratios = []
    productive_ratios = []
    individual_ratios = []
    balance_scores = []
    
    for h in history:
        dist = h.get("data", {}).get("distribution", {})
        if dist:
            total = dist.get("public", 0) + dist.get("productive", 0) + dist.get("individual", 0)
            if total > 0:
                public_ratios.append(dist.get("public", 0) / total)
                productive_ratios.append(dist.get("productive", 0) / total)
                individual_ratios.append(dist.get("individual", 0) / total)
        balance = h.get("data", {}).get("balance_score", 0)
        if balance:
            balance_scores.append(balance)
    
    window = prediction_config["window_size"]
    steps = prediction_config["forecast_steps"]
    
    # 예측 수행 (이동 평균 + 지수 평활 앙상블)
    predictions = {
        "public": {
            "sma": simple_moving_average_forecast(public_ratios, window, steps),
            "exp": exponential_smoothing_forecast(public_ratios, 0.3, steps)
        },
        "productive": {
            "sma": simple_moving_average_forecast(productive_ratios, window, steps),
            "exp": exponential_smoothing_forecast(productive_ratios, 0.3, steps)
        },
        "individual": {
            "sma": simple_moving_average_forecast(individual_ratios, window, steps),
            "exp": exponential_smoothing_forecast(individual_ratios, 0.3, steps)
        },
        "balance": {
            "sma": simple_moving_average_forecast(balance_scores, window, steps),
            "exp": exponential_smoothing_forecast(balance_scores, 0.3, steps)
        }
    }
    
    # 앙상블 예측 (평균)
    ensemble = {
        "public": [(predictions["public"]["sma"][i] + predictions["public"]["exp"][i]) / 2 for i in range(steps)],
        "productive": [(predictions["productive"]["sma"][i] + predictions["productive"]["exp"][i]) / 2 for i in range(steps)],
        "individual": [(predictions["individual"]["sma"][i] + predictions["individual"]["exp"][i]) / 2 for i in range(steps)],
        "balance": [(predictions["balance"]["sma"][i] + predictions["balance"]["exp"][i]) / 2 for i in range(steps)]
    }
    
    # 신뢰도 계산
    confidence = calculate_confidence(
        public_ratios[-min(5, len(public_ratios)):] if public_ratios else [],
        ensemble["public"][:min(5, steps)]
    )
    
    # 현재 시그마와 비교하여 조정 필요 여부 판단
    current_sigma = config_mgr.get_sigma()
    predicted_sigma = [
        ensemble["public"][0],
        ensemble["productive"][0],
        ensemble["individual"][0]
    ]
    
    # 정규화
    total = sum(predicted_sigma)
    if total > 0:
        predicted_sigma = [s/total for s in predicted_sigma]
    
    # 편차 계산
    deviations = [abs(current_sigma[i] - predicted_sigma[i]) for i in range(3)]
    max_deviation = max(deviations)
    
    # 조정 제안
    adjustment_needed = max_deviation > prediction_config["confidence_threshold"] * 0.1
    suggested_sigma = predicted_sigma if adjustment_needed else current_sigma
    
    result = {
        "success": True,
        "data_points": len(history),
        "current_sigma": current_sigma,
        "predicted_sigma": predicted_sigma,
        "ensemble_predictions": ensemble,
        "confidence": confidence,
        "max_deviation": max_deviation,
        "adjustment_needed": adjustment_needed,
        "suggested_sigma": suggested_sigma,
        "forecast_steps": steps,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    prediction_data["predictions"].append(result)
    if len(prediction_data["predictions"]) > 50:
        prediction_data["predictions"] = prediction_data["predictions"][-50:]
    prediction_data["last_prediction"] = result
    
    tracker.log("예측", "분석 완료", {
        "confidence": confidence,
        "adjustment_needed": adjustment_needed
    })
    
    return result

@api_router.post("/prediction/apply")
async def apply_prediction():
    """예측 결과 적용 (시그마 조정)"""
    if not prediction_data["last_prediction"]:
        raise HTTPException(status_code=400, detail="No prediction available")
    
    pred = prediction_data["last_prediction"]
    suggested = pred.get("suggested_sigma")
    
    if not suggested:
        raise HTTPException(status_code=400, detail="No suggested sigma in prediction")
    
    # 시그마 업데이트
    old_sigma = config_mgr.get_sigma()
    config_mgr.update_sigma(suggested)
    
    tracker.log("예측", "예측 적용", {
        "old_sigma": old_sigma,
        "new_sigma": suggested
    })
    
    return {
        "success": True,
        "old_sigma": old_sigma,
        "new_sigma": suggested,
        "confidence": pred.get("confidence", 0)
    }

@api_router.get("/prediction/history")
async def get_prediction_history(limit: int = 10):
    """예측 이력 조회"""
    history = prediction_data["predictions"][-limit:]
    return {
        "history": history,
        "total": len(prediction_data["predictions"]),
        "last_prediction": prediction_data["last_prediction"]
    }

# ==================== Pareto Optimization APIs (파레토 최적화 배분) ====================

class ParetoObjective(BaseModel):
    name: str
    weight: float = 1.0
    target: str  # "maximize" or "minimize"

class ParetoConfig(BaseModel):
    objectives: List[Dict] = []
    population_size: int = 50
    generations: int = 100

pareto_config = {
    "objectives": [
        {"name": "balance", "weight": 1.0, "target": "maximize", "description": "균형 점수 최대화"},
        {"name": "public_value", "weight": 0.8, "target": "maximize", "description": "공공 가치 최대화"},
        {"name": "efficiency", "weight": 0.9, "target": "maximize", "description": "분배 효율성 최대화"},
        {"name": "risk", "weight": 0.7, "target": "minimize", "description": "분배 리스크 최소화"}
    ],
    "population_size": 50,
    "generations": 100
}

def evaluate_solution(sigma: List[float], omega: Dict) -> Dict[str, float]:
    """솔루션 평가 함수 (목적 함수 값 계산)"""
    # 균형 점수
    target_sigma = [0.33, 0.34, 0.33]
    balance = 1 - sum(abs(sigma[i] - target_sigma[i]) for i in range(3)) / 2
    
    # 공공 가치 (공공 비율이 높을수록 좋음)
    public_value = sigma[0]
    
    # 효율성 (경계 조건 내에 있을수록 좋음)
    efficiency = 1.0
    if sigma[0] < omega.get("V_pub_min", 0.2) or sigma[0] > omega.get("V_pub_max", 0.5):
        efficiency -= 0.2
    if sigma[1] < omega.get("V_pro_min", 0.2) or sigma[1] > omega.get("V_pro_max", 0.5):
        efficiency -= 0.2
    if sigma[2] < omega.get("V_ind_min", 0.1) or sigma[2] > omega.get("V_ind_max", 0.5):
        efficiency -= 0.2
    
    # 리스크 (편차가 클수록 리스크 증가)
    risk = sum((sigma[i] - target_sigma[i])**2 for i in range(3))
    
    return {
        "balance": max(0, min(1, balance)),
        "public_value": public_value,
        "efficiency": max(0, efficiency),
        "risk": risk
    }

def dominates(sol1: Dict[str, float], sol2: Dict[str, float], objectives: List[Dict]) -> bool:
    """sol1이 sol2를 지배하는지 확인"""
    dominated = False
    at_least_one_better = False
    
    for obj in objectives:
        name = obj["name"]
        target = obj["target"]
        
        if target == "maximize":
            if sol1.get(name, 0) < sol2.get(name, 0):
                return False
            if sol1.get(name, 0) > sol2.get(name, 0):
                at_least_one_better = True
        else:  # minimize
            if sol1.get(name, 0) > sol2.get(name, 0):
                return False
            if sol1.get(name, 0) < sol2.get(name, 0):
                at_least_one_better = True
    
    return at_least_one_better

def find_pareto_front(solutions: List[Dict]) -> List[Dict]:
    """파레토 프론트 찾기"""
    objectives = pareto_config["objectives"]
    pareto_front = []
    
    for i, sol1 in enumerate(solutions):
        is_dominated = False
        for j, sol2 in enumerate(solutions):
            if i != j:
                if dominates(sol2["scores"], sol1["scores"], objectives):
                    is_dominated = True
                    break
        if not is_dominated:
            pareto_front.append(sol1)
    
    return pareto_front

@api_router.get("/pareto/config")
async def get_pareto_config():
    """파레토 최적화 설정 조회"""
    return pareto_config

@api_router.put("/pareto/config")
async def update_pareto_config(config: ParetoConfig):
    """파레토 최적화 설정 업데이트"""
    pareto_config["population_size"] = config.population_size
    pareto_config["generations"] = config.generations
    if config.objectives:
        pareto_config["objectives"] = config.objectives
    
    return {"success": True, "config": pareto_config}

@api_router.post("/pareto/optimize")
async def run_pareto_optimization():
    """파레토 최적화 실행"""
    omega = config_mgr.get_omega()
    current_sigma = config_mgr.get_sigma()
    
    # 솔루션 생성
    solutions = []
    
    # 현재 솔루션 추가
    current_scores = evaluate_solution(current_sigma, omega)
    solutions.append({
        "sigma": current_sigma,
        "scores": current_scores,
        "label": "현재"
    })
    
    # 랜덤 솔루션 생성
    for i in range(pareto_config["population_size"]):
        # 경계 조건 내에서 랜덤 생성
        pub = random.uniform(omega.get("V_pub_min", 0.2), omega.get("V_pub_max", 0.5))
        pro = random.uniform(omega.get("V_pro_min", 0.2), omega.get("V_pro_max", 0.5))
        ind = random.uniform(omega.get("V_ind_min", 0.1), omega.get("V_ind_max", 0.5))
        
        # 정규화
        total = pub + pro + ind
        sigma = [pub/total, pro/total, ind/total]
        
        scores = evaluate_solution(sigma, omega)
        solutions.append({
            "sigma": sigma,
            "scores": scores,
            "label": f"후보 {i+1}"
        })
    
    # 사전 정의된 전략 추가
    strategies = [
        {"sigma": [0.33, 0.34, 0.33], "label": "균형"},
        {"sigma": [0.45, 0.30, 0.25], "label": "공공 우선"},
        {"sigma": [0.25, 0.50, 0.25], "label": "생산 우선"},
        {"sigma": [0.25, 0.30, 0.45], "label": "개인 우선"},
        {"sigma": [0.20, 0.40, 0.40], "label": "성장"}
    ]
    
    for strat in strategies:
        scores = evaluate_solution(strat["sigma"], omega)
        solutions.append({
            "sigma": strat["sigma"],
            "scores": scores,
            "label": strat["label"]
        })
    
    # 파레토 프론트 계산
    pareto_front = find_pareto_front(solutions)
    
    # 가중 점수 계산 및 정렬
    for sol in pareto_front:
        weighted_score = 0
        for obj in pareto_config["objectives"]:
            name = obj["name"]
            weight = obj["weight"]
            target = obj["target"]
            score = sol["scores"].get(name, 0)
            
            if target == "minimize":
                score = 1 - score  # 최소화 목표는 반전
            
            weighted_score += score * weight
        
        sol["weighted_score"] = weighted_score / sum(obj["weight"] for obj in pareto_config["objectives"])
    
    # 가중 점수로 정렬
    pareto_front.sort(key=lambda x: x["weighted_score"], reverse=True)
    
    # 최적 솔루션
    best_solution = pareto_front[0] if pareto_front else None
    
    tracker.log("파레토", "최적화 실행", {
        "solutions_count": len(solutions),
        "pareto_front_size": len(pareto_front),
        "best_weighted_score": best_solution["weighted_score"] if best_solution else 0
    })
    
    return {
        "success": True,
        "current_sigma": current_sigma,
        "current_scores": current_scores,
        "pareto_front": pareto_front[:10],  # 상위 10개만
        "best_solution": best_solution,
        "total_solutions": len(solutions),
        "objectives": pareto_config["objectives"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.post("/pareto/apply/{index}")
async def apply_pareto_solution(index: int = 0):
    """파레토 최적 솔루션 적용"""
    # 최근 최적화 결과에서 적용
    # 간단히 구현: 인덱스 기반 적용
    
    omega = config_mgr.get_omega()
    current_sigma = config_mgr.get_sigma()
    
    # 재계산
    solutions = []
    for i in range(pareto_config["population_size"]):
        pub = random.uniform(omega.get("V_pub_min", 0.2), omega.get("V_pub_max", 0.5))
        pro = random.uniform(omega.get("V_pro_min", 0.2), omega.get("V_pro_max", 0.5))
        ind = random.uniform(omega.get("V_ind_min", 0.1), omega.get("V_ind_max", 0.5))
        total = pub + pro + ind
        sigma = [pub/total, pro/total, ind/total]
        scores = evaluate_solution(sigma, omega)
        solutions.append({"sigma": sigma, "scores": scores})
    
    pareto_front = find_pareto_front(solutions)
    
    for sol in pareto_front:
        weighted_score = 0
        for obj in pareto_config["objectives"]:
            name = obj["name"]
            weight = obj["weight"]
            target = obj["target"]
            score = sol["scores"].get(name, 0)
            if target == "minimize":
                score = 1 - score
            weighted_score += score * weight
        sol["weighted_score"] = weighted_score / sum(obj["weight"] for obj in pareto_config["objectives"])
    
    pareto_front.sort(key=lambda x: x["weighted_score"], reverse=True)
    
    if index >= len(pareto_front):
        raise HTTPException(status_code=400, detail="Invalid solution index")
    
    new_sigma = pareto_front[index]["sigma"]
    config_mgr.update_sigma(new_sigma)
    
    tracker.log("파레토", "솔루션 적용", {
        "old_sigma": current_sigma,
        "new_sigma": new_sigma
    })
    
    return {
        "success": True,
        "old_sigma": current_sigma,
        "new_sigma": new_sigma,
        "applied_solution": pareto_front[index]
    }

# ==================== Comparison Analysis APIs (처리 결과 비교 분석) ====================

class ComparisonRequest(BaseModel):
    record_ids: List[str] = []
    limit: int = 10

@api_router.post("/comparison/analyze")
async def analyze_comparison(request: ComparisonRequest):
    """처리 결과 비교 분석"""
    # 레코드 조회
    if request.record_ids:
        records = []
        for rid in request.record_ids:
            record = await db.processing_history.find_one({"id": rid}, {"_id": 0})
            if record:
                records.append(record)
    else:
        # 최근 N개 레코드 조회
        records = await db.processing_history.find(
            {"success": True}, {"_id": 0}
        ).sort("timestamp", -1).limit(request.limit).to_list(request.limit)
    
    if len(records) < 2:
        return {
            "success": False,
            "message": "비교를 위해 최소 2개의 레코드가 필요합니다",
            "records_count": len(records)
        }
    
    # 통계 계산
    asset_values = []
    balance_scores = []
    distributions = {"public": [], "productive": [], "individual": []}
    
    for record in records:
        data = record.get("data", {})
        asset = data.get("asset", {})
        dist = data.get("distribution", {})
        
        if asset.get("value"):
            asset_values.append(asset["value"])
        if data.get("balance_score"):
            balance_scores.append(data["balance_score"])
        if dist:
            total = dist.get("public", 0) + dist.get("productive", 0) + dist.get("individual", 0)
            if total > 0:
                distributions["public"].append(dist.get("public", 0) / total)
                distributions["productive"].append(dist.get("productive", 0) / total)
                distributions["individual"].append(dist.get("individual", 0) / total)
    
    # 통계 계산
    def calc_stats(values):
        if not values:
            return {"min": 0, "max": 0, "avg": 0, "std": 0}
        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "std": (sum((v - sum(values)/len(values))**2 for v in values) / len(values)) ** 0.5
        }
    
    stats = {
        "asset_value": calc_stats(asset_values),
        "balance_score": calc_stats(balance_scores),
        "distribution": {
            "public": calc_stats(distributions["public"]),
            "productive": calc_stats(distributions["productive"]),
            "individual": calc_stats(distributions["individual"])
        }
    }
    
    # 트렌드 분석
    trend = {
        "asset_value": "stable",
        "balance_score": "stable"
    }
    
    if len(asset_values) >= 3:
        recent = asset_values[:3]
        older = asset_values[-3:]
        if sum(recent)/3 > sum(older)/3 * 1.05:
            trend["asset_value"] = "increasing"
        elif sum(recent)/3 < sum(older)/3 * 0.95:
            trend["asset_value"] = "decreasing"
    
    if len(balance_scores) >= 3:
        recent = balance_scores[:3]
        older = balance_scores[-3:]
        if sum(recent)/3 > sum(older)/3 * 1.02:
            trend["balance_score"] = "increasing"
        elif sum(recent)/3 < sum(older)/3 * 0.98:
            trend["balance_score"] = "decreasing"
    
    # 이상치 탐지
    outliers = []
    if asset_values:
        avg = stats["asset_value"]["avg"]
        std = stats["asset_value"]["std"]
        for i, v in enumerate(asset_values):
            if std > 0 and abs(v - avg) > 2 * std:
                outliers.append({
                    "index": i,
                    "value": v,
                    "type": "asset_value",
                    "deviation": (v - avg) / std
                })
    
    # 레코드별 상세 데이터
    comparison_data = []
    for i, record in enumerate(records):
        data = record.get("data", {})
        comparison_data.append({
            "index": i,
            "id": record.get("id"),
            "timestamp": record.get("timestamp"),
            "input_value": record.get("input_value"),
            "asset_value": data.get("asset", {}).get("value", 0),
            "balance_score": data.get("balance_score", 0),
            "quality_score": data.get("asset", {}).get("quality_score", 0),
            "distribution": data.get("distribution", {})
        })
    
    tracker.log("비교", "분석 완료", {"records_count": len(records)})
    
    return {
        "success": True,
        "records_count": len(records),
        "statistics": stats,
        "trend": trend,
        "outliers": outliers,
        "comparison_data": comparison_data,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@api_router.get("/comparison/records")
async def get_comparison_records(limit: int = 20):
    """비교 가능한 레코드 목록 조회"""
    records = await db.processing_history.find(
        {"success": True}, {"_id": 0, "id": 1, "timestamp": 1, "input_value": 1, "data.asset.value": 1, "data.balance_score": 1}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "records": records,
        "total": await db.processing_history.count_documents({"success": True})
    }

# ==================== External Data Source APIs (외부 데이터 소스 연동) ====================

import aiohttp
import asyncio
from typing import Literal

# 데이터 소스 저장소
data_sources = {}

# 수집된 데이터 저장소
collected_data = {
    "history": [],
    "last_collection": None
}

# 백그라운드 태스크 관리
background_tasks = {}

class DataSourceConfig(BaseModel):
    name: str
    source_type: Literal["api", "webhook", "manual"] = "api"
    url: Optional[str] = None
    method: Literal["GET", "POST"] = "GET"
    headers: Optional[Dict[str, str]] = None
    body: Optional[Dict[str, Any]] = None
    auth_type: Optional[Literal["none", "api_key", "bearer", "basic"]] = "none"
    auth_value: Optional[str] = None
    polling_interval: int = 60  # 초 단위
    data_mapping: Optional[Dict[str, str]] = None  # 응답 데이터 매핑
    enabled: bool = True

@api_router.get("/datasources")
async def get_data_sources():
    """등록된 데이터 소스 목록 조회"""
    sources_list = []
    for source_id, source in data_sources.items():
        sources_list.append({
            "id": source_id,
            **source,
            "is_running": source_id in background_tasks
        })
    return {
        "sources": sources_list,
        "total": len(sources_list)
    }

@api_router.post("/datasources")
async def create_data_source(config: DataSourceConfig):
    """새 데이터 소스 등록"""
    source_id = f"ds_{uuid.uuid4().hex[:8]}"
    
    source_data = {
        "name": config.name,
        "source_type": config.source_type,
        "url": config.url,
        "method": config.method,
        "headers": config.headers or {},
        "body": config.body,
        "auth_type": config.auth_type,
        "auth_value": config.auth_value,
        "polling_interval": config.polling_interval,
        "data_mapping": config.data_mapping or {"value": "value"},
        "enabled": config.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_fetch": None,
        "last_status": None,
        "fetch_count": 0,
        "error_count": 0
    }
    
    data_sources[source_id] = source_data
    
    # MongoDB에 저장
    await db.data_sources.update_one(
        {"id": source_id},
        {"$set": {**source_data, "id": source_id}},
        upsert=True
    )
    
    tracker.log("데이터소스", "소스 등록", {"source_id": source_id, "name": config.name})
    
    return {"success": True, "source_id": source_id, "source": source_data}

@api_router.get("/datasources/collected")
async def get_collected_data(source_id_filter: Optional[str] = None, limit: int = 50):
    """수집된 데이터 조회"""
    query = {}
    if source_id_filter:
        query["source_id"] = source_id_filter
    
    records = await db.collected_data.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).limit(limit).to_list(limit)
    
    return {
        "data": records,
        "total": len(records),
        "last_collection": collected_data.get("last_collection")
    }

@api_router.get("/datasources/{source_id}")
async def get_data_source(source_id: str):
    """특정 데이터 소스 조회"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    return {"source": data_sources[source_id], "id": source_id}

@api_router.put("/datasources/{source_id}")
async def update_data_source(source_id: str, config: DataSourceConfig):
    """데이터 소스 수정"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    source = data_sources[source_id]
    source.update({
        "name": config.name,
        "source_type": config.source_type,
        "url": config.url,
        "method": config.method,
        "headers": config.headers or {},
        "body": config.body,
        "auth_type": config.auth_type,
        "auth_value": config.auth_value,
        "polling_interval": config.polling_interval,
        "data_mapping": config.data_mapping or {"value": "value"},
        "enabled": config.enabled
    })
    
    # MongoDB 업데이트
    await db.data_sources.update_one(
        {"id": source_id},
        {"$set": source}
    )
    
    return {"success": True, "source": source}

@api_router.delete("/datasources/{source_id}")
async def delete_data_source(source_id: str):
    """데이터 소스 삭제"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # 실행 중이면 중지
    if source_id in background_tasks:
        background_tasks[source_id].cancel()
        del background_tasks[source_id]
    
    del data_sources[source_id]
    
    # MongoDB에서 삭제
    await db.data_sources.delete_one({"id": source_id})
    
    tracker.log("데이터소스", "소스 삭제", {"source_id": source_id})
    
    return {"success": True, "deleted_source_id": source_id}

async def fetch_data_from_source(source_id: str, source: Dict) -> Dict:
    """외부 소스에서 데이터 가져오기"""
    if source["source_type"] != "api" or not source["url"]:
        return {"success": False, "error": "Invalid source configuration"}
    
    headers = dict(source.get("headers", {}))
    
    # 인증 헤더 추가
    if source["auth_type"] == "api_key" and source["auth_value"]:
        headers["X-API-Key"] = source["auth_value"]
    elif source["auth_type"] == "bearer" and source["auth_value"]:
        headers["Authorization"] = f"Bearer {source['auth_value']}"
    elif source["auth_type"] == "basic" and source["auth_value"]:
        headers["Authorization"] = f"Basic {source['auth_value']}"
    
    try:
        async with aiohttp.ClientSession() as session:
            if source["method"] == "GET":
                async with session.get(source["url"], headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status_code": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status_code": response.status}
            else:  # POST
                async with session.post(source["url"], headers=headers, json=source.get("body"), timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {"success": True, "data": data, "status_code": response.status}
                    else:
                        return {"success": False, "error": f"HTTP {response.status}", "status_code": response.status}
    except asyncio.TimeoutError:
        return {"success": False, "error": "Request timeout"}
    except aiohttp.ClientError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def extract_value_from_data(data: Any, mapping: Dict[str, str]) -> Optional[float]:
    """응답 데이터에서 값 추출"""
    try:
        # 기본 매핑: value 필드 찾기
        value_path = mapping.get("value", "value")
        
        # 점 표기법 지원 (예: "data.result.value")
        keys = value_path.split(".")
        result = data
        for key in keys:
            if isinstance(result, dict):
                result = result.get(key)
            elif isinstance(result, list) and key.isdigit():
                result = result[int(key)]
            else:
                return None
        
        if result is not None:
            return float(result)
        return None
    except (ValueError, TypeError, KeyError, IndexError):
        return None

@api_router.post("/datasources/{source_id}/fetch")
async def fetch_data_source(source_id: str):
    """데이터 소스에서 수동으로 데이터 가져오기"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    source = data_sources[source_id]
    result = await fetch_data_from_source(source_id, source)
    
    # 상태 업데이트
    source["last_fetch"] = datetime.now(timezone.utc).isoformat()
    source["last_status"] = "success" if result["success"] else "error"
    source["fetch_count"] += 1
    if not result["success"]:
        source["error_count"] += 1
    
    # 성공 시 값 추출 및 처리
    processed_value = None
    if result["success"] and result.get("data"):
        value = extract_value_from_data(result["data"], source.get("data_mapping", {}))
        if value is not None:
            processed_value = value
            
            # 수집 데이터 저장
            collection_record = {
                "source_id": source_id,
                "source_name": source["name"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "raw_data": result["data"],
                "extracted_value": value
            }
            collected_data["history"].append(collection_record)
            if len(collected_data["history"]) > 1000:
                collected_data["history"] = collected_data["history"][-1000:]
            collected_data["last_collection"] = collection_record
            
            # MongoDB에 저장
            await db.collected_data.insert_one({
                **collection_record,
                "id": f"cd_{uuid.uuid4().hex[:8]}"
            })
    
    tracker.log("데이터소스", "데이터 수집", {
        "source_id": source_id,
        "success": result["success"],
        "value": processed_value
    })
    
    return {
        "success": result["success"],
        "source_id": source_id,
        "raw_data": result.get("data") if result["success"] else None,
        "extracted_value": processed_value,
        "error": result.get("error"),
        "timestamp": source["last_fetch"]
    }

@api_router.post("/datasources/{source_id}/process")
async def process_collected_data(source_id: str):
    """수집된 데이터를 GVIC 파이프라인으로 처리"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    source = data_sources[source_id]
    
    # 먼저 데이터 가져오기
    result = await fetch_data_from_source(source_id, source)
    
    if not result["success"]:
        return {"success": False, "error": result.get("error")}
    
    # 값 추출
    value = extract_value_from_data(result["data"], source.get("data_mapping", {}))
    
    if value is None:
        return {"success": False, "error": "Could not extract value from data"}
    
    # GVIC 엔진으로 처리
    try:
        process_result = engine.process(value)
        
        # 처리 이력 저장
        history_record = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_value": value,
            "source": "external",
            "source_id": source_id,
            "source_name": source["name"],
            "success": True,
            "data": process_result
        }
        await db.processing_history.insert_one(history_record)
        
        tracker.log("데이터소스", "파이프라인 처리", {
            "source_id": source_id,
            "input_value": value,
            "success": True
        })
        
        return {
            "success": True,
            "source_id": source_id,
            "input_value": value,
            "result": process_result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@api_router.post("/datasources/{source_id}/start")
async def start_polling(source_id: str):
    """폴링 시작"""
    if source_id not in data_sources:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    if source_id in background_tasks:
        return {"success": False, "message": "Polling already running"}
    
    source = data_sources[source_id]
    
    async def polling_task():
        while True:
            try:
                await fetch_data_source(source_id)
                await asyncio.sleep(source["polling_interval"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.error(f"Polling error for {source_id}: {e}")
                await asyncio.sleep(source["polling_interval"])
    
    task = asyncio.create_task(polling_task())
    background_tasks[source_id] = task
    
    tracker.log("데이터소스", "폴링 시작", {"source_id": source_id})
    
    return {"success": True, "message": f"Polling started for {source_id}"}

@api_router.post("/datasources/{source_id}/stop")
async def stop_polling(source_id: str):
    """폴링 중지"""
    if source_id not in background_tasks:
        return {"success": False, "message": "Polling not running"}
    
    background_tasks[source_id].cancel()
    del background_tasks[source_id]
    
    tracker.log("데이터소스", "폴링 중지", {"source_id": source_id})
    
    return {"success": True, "message": f"Polling stopped for {source_id}"}



# ==================== Review Analysis APIs (실시간 GVIC 분석) ====================

import pandas as pd
import numpy as np
from core.patent1_convergence import ConvergenceController
from core.patent2_signal import SignalPreprocessor, SignalType
from core.patent4_nonconform import NonConformingDataAssetizationSystem
from core.patent5_distribution import WeightedDistributionSystem

# 분석 진행 상태 저장
analysis_sessions = {}

class ReviewAnalysisRequest(BaseModel):
    file_path: Optional[str] = None
    use_sample: bool = True
    sample_size: int = 100

class AnalysisStepRequest(BaseModel):
    session_id: str
    step: str  # 'sentiment', 'convergence', 'signal', 'nonconform', 'distribution', 'pipeline'

@api_router.get("/analysis/files")
async def get_available_files():
    """분석 가능한 데이터 파일 목록"""
    data_dir = "/app/backend/data"
    files = []
    if os.path.exists(data_dir):
        for f in os.listdir(data_dir):
            if f.endswith('.xlsx') and 'oliveyoung' in f:
                file_path = os.path.join(data_dir, f)
                files.append({
                    "name": f,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
    return {"files": files}

@api_router.post("/analysis/start")
async def start_analysis(request: ReviewAnalysisRequest):
    """분석 세션 시작"""
    session_id = str(uuid.uuid4())[:8]
    
    # 데이터 로드
    data_dir = "/app/backend/data"
    if request.file_path and os.path.exists(request.file_path):
        file_path = request.file_path
    else:
        # 가장 최신 파일 사용
        files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx') and 'oliveyoung' in f]
        if not files:
            raise HTTPException(status_code=404, detail="No data files found")
        file_path = os.path.join(data_dir, sorted(files)[-1])
    
    df = pd.read_excel(file_path)
    
    # 샘플 추출
    if request.sample_size < len(df):
        df = df.sample(n=request.sample_size, random_state=42)
    
    analysis_sessions[session_id] = {
        "id": session_id,
        "file_path": file_path,
        "data": df.to_dict('records'),
        "total_records": len(df),
        "status": "initialized",
        "results": {},
        "current_step": 0,
        "steps": ["sentiment", "convergence", "signal", "nonconform", "distribution", "pipeline"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    tracker.log("분석", "세션 시작", {"session_id": session_id, "records": len(df)})
    
    return {
        "session_id": session_id,
        "total_records": len(df),
        "file_name": os.path.basename(file_path),
        "steps": analysis_sessions[session_id]["steps"]
    }

@api_router.get("/analysis/{session_id}/status")
async def get_analysis_status(session_id: str):
    """분석 세션 상태 조회"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "current_step": session["current_step"],
        "total_steps": len(session["steps"]),
        "completed_steps": list(session["results"].keys()),
        "total_records": session["total_records"]
    }

@api_router.post("/analysis/{session_id}/step/{step_name}")
async def run_analysis_step(session_id: str, step_name: str):
    """특정 분석 단계 실행"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    df = pd.DataFrame(session["data"])
    
    result = {}
    
    if step_name == "sentiment":
        # 감성 분석
        df['sentiment'] = df['rating'].apply(lambda x: 'positive' if x >= 4 else ('neutral' if x == 3 else 'negative'))
        sentiment_counts = df['sentiment'].value_counts()
        total = len(df)
        
        result = {
            "step": "sentiment",
            "title": "감성 분포 분석",
            "description": "리뷰 평점을 기반으로 긍정/중립/부정 분류",
            "data": {
                "positive": {"count": int(sentiment_counts.get('positive', 0)), "ratio": sentiment_counts.get('positive', 0) / total},
                "neutral": {"count": int(sentiment_counts.get('neutral', 0)), "ratio": sentiment_counts.get('neutral', 0) / total},
                "negative": {"count": int(sentiment_counts.get('negative', 0)), "ratio": sentiment_counts.get('negative', 0) / total},
            },
            "summary": {
                "total_reviews": total,
                "avg_rating": float(df['rating'].mean()),
                "rating_distribution": df['rating'].value_counts().to_dict()
            },
            "status": "completed"
        }
        
    elif step_name == "convergence":
        # 수렴 제어 (특허 1)
        sentiment = session["results"].get("sentiment", {}).get("data", {})
        if not sentiment:
            raise HTTPException(status_code=400, detail="Run sentiment step first")
        
        V_input = np.array([
            sentiment.get("positive", {}).get("ratio", 0.33),
            sentiment.get("neutral", {}).get("ratio", 0.34),
            sentiment.get("negative", {}).get("ratio", 0.33)
        ])
        
        controller = ConvergenceController(
            default_ratio=[0.33, 0.34, 0.33],
            omega={
                'lower_bounds': [0.1, 0.05, 0.01],
                'upper_bounds': [0.95, 0.5, 0.5],
                'sum_constraint': 1.0
            }
        )
        
        V_output, metadata = controller.converge(V_input)
        is_valid = controller.omega.is_valid(V_output)
        
        result = {
            "step": "convergence",
            "title": "전역 수렴 제어 (특허 1)",
            "description": "OBC 경계 조건을 기반으로 입력 데이터를 수렴 변환",
            "data": {
                "input_vector": V_input.tolist(),
                "output_vector": V_output.tolist(),
                "transformation": {
                    "applied": metadata.get("transformed", False),
                    "status": metadata.get("status", "unknown"),
                    "balance_index": metadata.get("balance_index", 0)
                },
                "boundary_check": {
                    "is_valid": bool(is_valid),
                    "lower_bounds": [0.1, 0.05, 0.01],
                    "upper_bounds": [0.95, 0.5, 0.5]
                }
            },
            "status": "completed"
        }
        
    elif step_name == "signal":
        # 신호 전처리 (특허 2)
        preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
        sample_size = min(100, len(df))
        
        modules_result = {
            "total_processed": 0,
            "conforming": 0,
            "non_conforming": 0,
            "unclassified": 0,
            "processed_samples": []
        }
        
        for idx, row in df.head(sample_size).iterrows():
            signal_data = {
                'rating': row['rating'],
                'review_length': row['review_length'],
                'helpful_count': row['helpful_count'],
                'is_repurchase': 1 if row.get('is_repurchase', False) else 0,
                'mentions_effect': 1 if row.get('mentions_effect', False) else 0
            }
            
            modules = preprocessor.process(signal_data, SignalType.BEHAVIOR)
            modules_result["total_processed"] += 1
            
            for module in modules:
                status = module.conformance_status.value
                if status == 'conforming':
                    modules_result["conforming"] += 1
                elif status == 'non_conforming':
                    modules_result["non_conforming"] += 1
                else:
                    modules_result["unclassified"] += 1
            
            if len(modules_result["processed_samples"]) < 10:
                modules_result["processed_samples"].append({
                    "index": int(idx),
                    "rating": int(row['rating']),
                    "status": modules[0].conformance_status.value if modules else "unknown"
                })
        
        total_modules = modules_result["conforming"] + modules_result["non_conforming"] + modules_result["unclassified"]
        
        result = {
            "step": "signal",
            "title": "다단계 신호 전처리 (특허 2)",
            "description": "리뷰 데이터를 신호로 변환하고 정합성 판별",
            "data": {
                "total_processed": modules_result["total_processed"],
                "modules_generated": total_modules,
                "conforming": modules_result["conforming"],
                "non_conforming": modules_result["non_conforming"],
                "unclassified": modules_result["unclassified"],
                "conformance_rate": modules_result["conforming"] / total_modules if total_modules > 0 else 0,
                "samples": modules_result["processed_samples"]
            },
            "status": "completed"
        }
        
    elif step_name == "nonconform":
        # 비적합 데이터 자산화 (특허 5)
        nc_system = NonConformingDataAssetizationSystem(value_threshold=0.5, retention_days=30)
        sample_size = min(100, len(df))
        
        nc_result = {
            "total_processed": 0,
            "conforming": 0,
            "nonconforming": 0,
            "assets_created": 0,
            "nc_types": {},
            "asset_samples": []
        }
        
        for idx, row in df.head(sample_size).iterrows():
            context = {
                'required_fields': ['rating', 'content'],
                'bounds': (1, 5),
                'business_relevance': 0.7
            }
            
            review_data = {
                'rating': row['rating'],
                'content': row.get('content', ''),
                'review_length': row.get('review_length', 0),
                'helpful_count': row.get('helpful_count', 0)
            }
            
            proc_result = nc_system.process(review_data, context)
            nc_result["total_processed"] += 1
            
            if proc_result['is_conforming']:
                nc_result["conforming"] += 1
            else:
                nc_result["nonconforming"] += 1
                for nc in proc_result.get('non_conformances', []):
                    nc_type = nc.get('type', 'unknown')
                    nc_result["nc_types"][nc_type] = nc_result["nc_types"].get(nc_type, 0) + 1
                
                nc_result["assets_created"] += len(proc_result.get('assets_created', []))
                
                if len(nc_result["asset_samples"]) < 5:
                    nc_result["asset_samples"].append({
                        "index": int(idx),
                        "type": proc_result.get('non_conformances', [{}])[0].get('type', 'unknown'),
                        "value": proc_result.get('assets_created', [{}])[0].get('value', 0) if proc_result.get('assets_created') else 0
                    })
        
        result = {
            "step": "nonconform",
            "title": "비적합 데이터 자산화 (특허 5)",
            "description": "비적합 데이터를 감지하고 2차 자산으로 변환",
            "data": {
                "total_processed": nc_result["total_processed"],
                "conforming": nc_result["conforming"],
                "nonconforming": nc_result["nonconforming"],
                "assets_created": nc_result["assets_created"],
                "nc_types": nc_result["nc_types"],
                "asset_samples": nc_result["asset_samples"],
                "assetization_rate": nc_result["assets_created"] / nc_result["nonconforming"] if nc_result["nonconforming"] > 0 else 0
            },
            "status": "completed"
        }
        
    elif step_name == "distribution":
        # 가중 분배 (특허 6)
        sentiment = session["results"].get("sentiment", {}).get("data", {})
        if not sentiment:
            raise HTTPException(status_code=400, detail="Run sentiment step first")
        
        base_ratio = [
            sentiment.get("positive", {}).get("ratio", 0.33),
            sentiment.get("neutral", {}).get("ratio", 0.34) + 0.1,
            sentiment.get("negative", {}).get("ratio", 0.33) + 0.1
        ]
        total = sum(base_ratio)
        base_ratio = [r / total for r in base_ratio]
        
        distributor = WeightedDistributionSystem(base_ratio=base_ratio)
        total_value = 1000000
        
        distribution = distributor.distribute(total_value)
        analytics = distributor.get_analytics()
        
        # 소비 시뮬레이션
        consumptions = {
            'public': distribution.get('public', 0) * 0.85,
            'productive': distribution.get('productive', 0) * 1.1,
            'individual': distribution.get('individual', 0) * 0.9
        }
        adjustment = distributor.update_with_consumption(consumptions)
        
        result = {
            "step": "distribution",
            "title": "가중 분배 모델 (특허 6)",
            "description": "감성 비율을 기반으로 자원을 영역별 분배",
            "data": {
                "total_value": total_value,
                "base_ratio": base_ratio,
                "distribution": {
                    "public": distribution.get("public", 0),
                    "productive": distribution.get("productive", 0),
                    "individual": distribution.get("individual", 0)
                },
                "analytics": {
                    "fairness_index": analytics.get("fairness_index", 0),
                    "weighted_fairness": analytics.get("weighted_fairness", 0),
                    "efficiency": analytics.get("efficiency", 0),
                    "utilization": analytics.get("utilization", 0)
                },
                "adjustment": {
                    "applied": adjustment.get("adjusted", False),
                    "consumptions": consumptions
                }
            },
            "status": "completed"
        }
        
    elif step_name == "pipeline":
        # 전체 파이프라인 (GVIC 엔진)
        sample_size = min(50, len(df))
        
        pipeline_result = {
            "total_processed": 0,
            "success": 0,
            "failure": 0,
            "balance_scores": [],
            "distribution_totals": {"public": 0, "productive": 0, "individual": 0},
            "processed_samples": []
        }
        
        for idx, row in df.head(sample_size).iterrows():
            input_data = {
                'value': row['rating'] * 20,
                'amount': row.get('helpful_count', 0),
                'quality': row.get('review_length', 0) / 100,
                'metadata': {
                    'is_repurchase': row.get('is_repurchase', False),
                    'mentions_effect': row.get('mentions_effect', False)
                }
            }
            
            proc_result = engine.process(input_data, source_type="review")
            pipeline_result["total_processed"] += 1
            
            if proc_result.success:
                pipeline_result["success"] += 1
                balance_score = proc_result.data.get('balance_score', 0)
                pipeline_result["balance_scores"].append(balance_score)
                
                dist = proc_result.data.get('distribution', {})
                for key in ['public', 'productive', 'individual']:
                    pipeline_result["distribution_totals"][key] += dist.get(key, 0)
                
                if len(pipeline_result["processed_samples"]) < 10:
                    pipeline_result["processed_samples"].append({
                        "index": int(idx),
                        "input_value": input_data["value"],
                        "balance_score": balance_score,
                        "success": True
                    })
            else:
                pipeline_result["failure"] += 1
        
        avg_balance = np.mean(pipeline_result["balance_scores"]) if pipeline_result["balance_scores"] else 0
        
        result = {
            "step": "pipeline",
            "title": "전체 GVIC 파이프라인",
            "description": "모든 특허 모듈을 통합한 전체 처리 흐름",
            "data": {
                "total_processed": pipeline_result["total_processed"],
                "success": pipeline_result["success"],
                "failure": pipeline_result["failure"],
                "success_rate": pipeline_result["success"] / pipeline_result["total_processed"] if pipeline_result["total_processed"] > 0 else 0,
                "avg_balance_score": avg_balance,
                "distribution_totals": pipeline_result["distribution_totals"],
                "samples": pipeline_result["processed_samples"]
            },
            "status": "completed"
        }
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown step: {step_name}")
    
    # 결과 저장
    session["results"][step_name] = result
    session["current_step"] = session["steps"].index(step_name) + 1 if step_name in session["steps"] else session["current_step"]
    session["status"] = "completed" if session["current_step"] >= len(session["steps"]) else "in_progress"
    
    tracker.log("분석", f"단계 완료: {step_name}", {"session_id": session_id})
    
    return result

@api_router.get("/analysis/{session_id}/results")
async def get_analysis_results(session_id: str):
    """전체 분석 결과 조회"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    return {
        "session_id": session_id,
        "status": session["status"],
        "total_records": session["total_records"],
        "results": session["results"],
        "completed_steps": list(session["results"].keys())
    }

@api_router.post("/analysis/{session_id}/run-all")
async def run_all_analysis_steps(session_id: str):
    """모든 분석 단계 순차 실행"""
    if session_id not in analysis_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = analysis_sessions[session_id]
    results = {}
    
    for step in session["steps"]:
        try:
            result = await run_analysis_step(session_id, step)
            results[step] = result
        except Exception as e:
            results[step] = {"status": "error", "error": str(e)}
            break
    
    return {
        "session_id": session_id,
        "status": session["status"],
        "results": results
    }


# ==================== Full Pipeline API (입력→GVIC→출력) ====================

from adapters.input_adapter import ProductReviewAdapter, DataDomain, InputAdapterFactory
from adapters.output_adapter import (
    PDFReportAdapter, OutputType, OutputAdapterFactory, 
    ModularAnalysisResult, FactorExtractor
)

class PipelineRequest(BaseModel):
    file_path: Optional[str] = None
    sample_size: int = 1000

@api_router.post("/pipeline/run")
async def run_full_pipeline_api(request: PipelineRequest):
    """전체 파이프라인 실행 (입력→GVIC 분석→PDF 출력)"""
    import uuid as uuid_module
    
    # 1. 데이터 파일 찾기
    data_dir = "/app/backend/data"
    if request.file_path and os.path.exists(request.file_path):
        file_path = request.file_path
    else:
        files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx') and 'oliveyoung' in f]
        if not files:
            raise HTTPException(status_code=404, detail="No data files found")
        file_path = os.path.join(data_dir, sorted(files)[-1])
    
    # 2. 입력 어댑터
    input_adapter = InputAdapterFactory.get_adapter(DataDomain.PRODUCT_REVIEW)
    input_batch = input_adapter.process(file_path)
    
    # 3. 감성 분석
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    ratings = []
    for record in input_batch.records:
        ratings.append(record.metadata.get("original_rating", 3))
        sentiment_counts[record.sentiment_hint] += 1
    
    total = len(input_batch.records)
    sentiment_distribution = {
        "positive": {"count": sentiment_counts["positive"], "ratio": sentiment_counts["positive"] / total},
        "neutral": {"count": sentiment_counts["neutral"], "ratio": sentiment_counts["neutral"] / total},
        "negative": {"count": sentiment_counts["negative"], "ratio": sentiment_counts["negative"] / total}
    }
    
    # 4. 요인 추출
    factor_extractor = FactorExtractor()
    records_for_extraction = [r.to_dict() for r in input_batch.records]
    positive_factors, negative_factors = factor_extractor.extract_factors(records_for_extraction)
    
    # 5. GVIC 분석
    gvic_results = {}
    
    # 수렴 제어
    V_input = np.array([
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"],
        sentiment_distribution["negative"]["ratio"]
    ])
    controller = ConvergenceController(
        default_ratio=[0.33, 0.34, 0.33],
        omega={'lower_bounds': [0.1, 0.05, 0.01], 'upper_bounds': [0.95, 0.5, 0.5], 'sum_constraint': 1.0}
    )
    V_output, conv_metadata = controller.converge(V_input)
    gvic_results["convergence"] = {
        "status": conv_metadata.get("status"),
        "balance_index": conv_metadata.get("balance_index", 0)
    }
    
    # 신호 처리
    preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
    conforming_count = 0
    sample_size = min(100, len(input_batch.records))
    for record in input_batch.records[:sample_size]:
        signal_data = {'rating': record.metadata.get("original_rating", 3)}
        modules = preprocessor.process(signal_data, SignalType.BEHAVIOR)
        for m in modules:
            if m.conformance_status.value == 'conforming':
                conforming_count += 1
    gvic_results["signal"] = {
        "total_processed": sample_size,
        "conformance_rate": conforming_count / sample_size if sample_size > 0 else 0
    }
    
    # 가중 분배
    base_ratio = [
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"] + 0.1,
        sentiment_distribution["negative"]["ratio"] + 0.1
    ]
    total_ratio = sum(base_ratio)
    base_ratio = [r / total_ratio for r in base_ratio]
    distributor = WeightedDistributionSystem(base_ratio=base_ratio)
    distribution = distributor.distribute(1000000)
    analytics = distributor.get_analytics()
    gvic_results["distribution"] = distribution
    gvic_results["fairness_index"] = analytics.get("fairness_index", 0)
    
    # 6. 인사이트 생성
    insights = []
    recommendations = []
    if sentiment_distribution["positive"]["ratio"] > 0.8:
        insights.append(f"전체 리뷰의 {sentiment_distribution['positive']['ratio']*100:.0f}%가 긍정적입니다.")
    if positive_factors:
        insights.append(f"가장 많이 언급된 긍정 요인: '{positive_factors[0].category}' ({positive_factors[0].count}건)")
    if negative_factors:
        insights.append(f"주요 개선 필요 요인: '{negative_factors[0].category}' ({negative_factors[0].count}건)")
        recommendations.append(f"'{negative_factors[0].category}' 관련 개선이 필요합니다.")
    
    # 7. PDF 생성
    output_dir = "/app/backend/data/reports"
    os.makedirs(output_dir, exist_ok=True)
    
    analysis_result = ModularAnalysisResult(
        result_id=str(uuid_module.uuid4())[:8],
        analysis_type="상품 후기 분석",
        created_at=datetime.now(timezone.utc).isoformat(),
        input_summary={
            "total_records": input_batch.total_count,
            "avg_rating": float(np.mean(ratings)),
            "source": os.path.basename(file_path),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        sentiment_distribution=sentiment_distribution,
        positive_factors=positive_factors,
        negative_factors=negative_factors,
        gvic_results=gvic_results,
        insights=insights,
        recommendations=recommendations
    )
    
    output_file = os.path.join(output_dir, f"GVIC_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    output_adapter = OutputAdapterFactory.get_adapter(OutputType.PDF_REPORT)
    formatted_data = output_adapter.format(analysis_result)
    pdf_path = output_adapter.export(formatted_data, output_file)
    
    # public 폴더에 복사
    public_pdf = f"/app/frontend/public/GVIC_Report_Latest.pdf"
    import shutil
    shutil.copy(pdf_path, public_pdf)
    
    tracker.log("파이프라인", "전체 분석 완료", {"records": total, "pdf": pdf_path})
    
    return {
        "success": True,
        "batch_id": input_batch.batch_id,
        "total_records": input_batch.total_count,
        "sentiment_distribution": sentiment_distribution,
        "positive_factors": [{"category": f.category, "count": f.count, "ratio": f.ratio} for f in positive_factors],
        "negative_factors": [{"category": f.category, "count": f.count, "ratio": f.ratio} for f in negative_factors],
        "gvic_results": gvic_results,
        "insights": insights,
        "recommendations": recommendations,
        "pdf_url": "/GVIC_Report_Latest.pdf"
    }

@api_router.get("/pipeline/reports")
async def list_pipeline_reports():
    """생성된 PDF 리포트 목록"""
    report_dir = "/app/backend/data/reports"
    reports = []
    if os.path.exists(report_dir):
        for f in os.listdir(report_dir):
            if f.endswith('.pdf'):
                file_path = os.path.join(report_dir, f)
                # UTC 시간으로 반환 (프론트엔드에서 현지 시각으로 변환)
                created_utc = datetime.fromtimestamp(os.path.getctime(file_path), tz=timezone.utc)
                reports.append({
                    "name": f,
                    "path": file_path,
                    "size": os.path.getsize(file_path),
                    "created": created_utc.isoformat()
                })
    return {"reports": sorted(reports, key=lambda x: x["created"], reverse=True)}

@api_router.get("/pipeline/download/{filename}")
async def direct_download_report(filename: str):
    """PDF 리포트 직접 다운로드 - fetch/blob 방식 지원"""
    file_path = f"/app/backend/data/reports/{filename}"
    
    # public 폴더에서도 확인
    if not os.path.exists(file_path):
        file_path = f"/app/frontend/public/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


@api_router.get("/pipeline/report/{filename}")
async def download_report(filename: str):
    """PDF 리포트 다운로드 - 강제 다운로드"""
    file_path = f"/app/backend/data/reports/{filename}"
    
    # public 폴더에서도 확인
    if not os.path.exists(file_path):
        file_path = f"/app/frontend/public/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    # application/octet-stream으로 강제 다운로드 (브라우저가 열지 않고 저장)
    return FileResponse(
        file_path, 
        media_type="application/octet-stream", 
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Content-Type": "application/octet-stream"
        }
    )


@api_router.get("/pipeline/report-base64/{filename}")
async def download_report_base64(filename: str):
    """PDF 리포트를 base64로 반환"""
    import base64
    
    file_path = f"/app/backend/data/reports/{filename}"
    
    if not os.path.exists(file_path):
        file_path = f"/app/frontend/public/{filename}"
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Report not found")
    
    with open(file_path, "rb") as f:
        content = f.read()
    
    return {
        "filename": filename,
        "content": base64.b64encode(content).decode("utf-8"),
        "size": len(content)
    }


# ==================== URL 기반 분석 API ====================

from crawlers.url_crawler import crawl_url, CrawlResult

class OutputOptionsModel(BaseModel):
    reportTitle: str = ""
    includeInsights: bool = True
    includeRecommendations: bool = True
    includeSentiment: bool = True
    includeFactors: bool = True
    includeGvicAnalysis: bool = True
    customNotes: str = ""

class URLAnalysisRequest(BaseModel):
    url: str
    max_reviews: int = 1000
    output_options: Optional[OutputOptionsModel] = None
    timezone_offset: int = 0  # 사용자 타임존 오프셋 (분 단위, UTC 기준)

@api_router.post("/pipeline/analyze-url")
async def analyze_url(request: URLAnalysisRequest):
    """URL에서 데이터를 수집하여 분석하고 PDF 리포트 생성 (모든 탭 연동)"""
    import uuid as uuid_module
    from datetime import timedelta
    
    url = request.url
    max_reviews = request.max_reviews  # 사용자 입력값 그대로 사용
    
    # 사용자 로컬 시간 계산 (타임존 오프셋 적용)
    user_local_time = datetime.now(timezone.utc) - timedelta(minutes=request.timezone_offset)
    
    tracker.log("URL분석", "시작", {"url": url, "max_reviews": max_reviews})
    
    # 1. URL 크롤링
    crawl_result = crawl_url(url, max_reviews)
    
    if not crawl_result.success or not crawl_result.reviews:
        raise HTTPException(status_code=400, detail=f"URL에서 데이터를 수집할 수 없습니다: {crawl_result.error}")
    
    reviews = crawl_result.reviews
    product_name = crawl_result.product_name
    
    # ===== 데이터 허브: 세션 시작 (모든 탭 연동) =====
    session = await data_hub.start_session(
        source_type='url',
        source_url=url,
        product_name=product_name
    )
    
    # 2. 입력 어댑터로 표준화
    input_adapter = InputAdapterFactory.get_adapter(DataDomain.PRODUCT_REVIEW)
    input_batch = input_adapter.transform(reviews)
    
    # ===== 데이터 허브: 입력 데이터 업데이트 =====
    await data_hub.update_input_summary(
        total_records=input_batch.total_count,
        valid_records=input_batch.valid_count
    )
    
    # 3. 감성 분석
    sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
    ratings = []
    for record in input_batch.records:
        ratings.append(record.metadata.get("original_rating", 3))
        sentiment_counts[record.sentiment_hint] += 1
    
    total = len(input_batch.records)
    sentiment_distribution = {
        "positive": {"count": sentiment_counts["positive"], "ratio": sentiment_counts["positive"] / total},
        "neutral": {"count": sentiment_counts["neutral"], "ratio": sentiment_counts["neutral"] / total},
        "negative": {"count": sentiment_counts["negative"], "ratio": sentiment_counts["negative"] / total}
    }
    
    # ===== 데이터 허브: 감성 분석 업데이트 =====
    await data_hub.update_sentiment_analysis(
        positive=sentiment_counts["positive"],
        neutral=sentiment_counts["neutral"],
        negative=sentiment_counts["negative"],
        avg_rating=float(np.mean(ratings))
    )
    
    # 4. 요인 추출
    factor_extractor = FactorExtractor()
    records_for_extraction = [r.to_dict() for r in input_batch.records]
    positive_factors, negative_factors = factor_extractor.extract_factors(records_for_extraction)
    
    # ===== 데이터 허브: 요인 분석 업데이트 =====
    await data_hub.update_factors(
        positive_factors=[{"category": f.category, "count": f.count, "ratio": f.ratio} for f in positive_factors],
        negative_factors=[{"category": f.category, "count": f.count, "ratio": f.ratio} for f in negative_factors]
    )
    
    # 5. GVIC 분석
    gvic_results = {}
    
    # 수렴 제어
    V_input = np.array([
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"],
        sentiment_distribution["negative"]["ratio"]
    ])
    controller = ConvergenceController(
        default_ratio=[0.33, 0.34, 0.33],
        omega={'lower_bounds': [0.1, 0.05, 0.01], 'upper_bounds': [0.95, 0.5, 0.5], 'sum_constraint': 1.0}
    )
    V_output, conv_metadata = controller.converge(V_input)
    gvic_results["convergence"] = {
        "status": conv_metadata.get("status"),
        "balance_index": conv_metadata.get("balance_index", 0)
    }
    
    # 신호 처리
    preprocessor = SignalPreprocessor(dimension=64, threshold=0.7)
    conforming_count = 0
    sample_size = min(100, len(input_batch.records))
    for record in input_batch.records[:sample_size]:
        signal_data = {'rating': record.metadata.get("original_rating", 3)}
        modules = preprocessor.process(signal_data, SignalType.BEHAVIOR)
        for m in modules:
            if m.conformance_status.value == 'conforming':
                conforming_count += 1
    conformance_rate = conforming_count / sample_size if sample_size > 0 else 0
    gvic_results["signal"] = {
        "total_processed": sample_size,
        "conformance_rate": conformance_rate
    }
    
    # 가중 분배
    base_ratio = [
        sentiment_distribution["positive"]["ratio"],
        sentiment_distribution["neutral"]["ratio"] + 0.1,
        sentiment_distribution["negative"]["ratio"] + 0.1
    ]
    total_ratio = sum(base_ratio)
    base_ratio = [r / total_ratio for r in base_ratio]
    distributor = WeightedDistributionSystem(base_ratio=base_ratio)
    distribution = distributor.distribute(1000000)
    analytics = distributor.get_analytics()
    gvic_results["distribution"] = distribution
    gvic_results["fairness_index"] = analytics.get("fairness_index", 0)
    
    # ===== 데이터 허브: GVIC 분석 결과 업데이트 =====
    await data_hub.update_gvic_results(
        convergence_status=conv_metadata.get("status", ""),
        balance_index=conv_metadata.get("balance_index", 0),
        conformance_rate=conformance_rate,
        distribution=distribution,
        fairness_index=analytics.get("fairness_index", 0)
    )
    
    # 6. 인사이트 생성
    insights = [f"'{product_name}' 상품에 대한 {total}건의 리뷰를 분석했습니다."]
    recommendations = []
    
    if sentiment_distribution["positive"]["ratio"] > 0.8:
        insights.append(f"전체 리뷰의 {sentiment_distribution['positive']['ratio']*100:.0f}%가 긍정적입니다.")
    elif sentiment_distribution["positive"]["ratio"] < 0.5:
        insights.append(f"긍정 리뷰 비율이 {sentiment_distribution['positive']['ratio']*100:.0f}%로 개선이 필요합니다.")
    
    if positive_factors:
        insights.append(f"가장 많이 언급된 긍정 요인: '{positive_factors[0].category}' ({positive_factors[0].count}건)")
    if negative_factors:
        insights.append(f"주요 개선 필요 요인: '{negative_factors[0].category}' ({negative_factors[0].count}건)")
        recommendations.append(f"'{negative_factors[0].category}' 관련 개선이 필요합니다.")
    
    recommendations.append("긍정 리뷰의 핵심 요인을 마케팅에 활용하세요.")
    
    # ===== 데이터 허브: 인사이트 업데이트 =====
    await data_hub.update_insights(insights, recommendations)
    
    # 7. PDF 생성
    output_dir = "/app/backend/data/reports"
    os.makedirs(output_dir, exist_ok=True)
    
    analysis_result = ModularAnalysisResult(
        result_id=session.session_id,
        analysis_type="URL 기반 상품 후기 분석",
        created_at=datetime.now(timezone.utc).isoformat(),
        input_summary={
            "total_records": total,
            "avg_rating": float(np.mean(ratings)),
            "source": url,
            "product_name": product_name,
            "site_type": crawl_result.site_type.value,
            "analysis_date": user_local_time.strftime("%Y-%m-%d %H:%M")
        },
        sentiment_distribution=sentiment_distribution,
        positive_factors=positive_factors,
        negative_factors=negative_factors,
        gvic_results=gvic_results,
        insights=insights,
        recommendations=recommendations
    )
    
    # 사용자 로컬 시간 기준 파일명 생성
    output_file = os.path.join(output_dir, f"GVIC_Report_{user_local_time.strftime('%Y%m%d_%H%M%S')}.pdf")
    output_adapter = OutputAdapterFactory.get_adapter(OutputType.PDF_REPORT)
    
    # 출력 옵션을 딕셔너리로 변환
    output_opts = request.output_options.dict() if request.output_options else {}
    formatted_data = output_adapter.format(analysis_result, output_opts)
    pdf_path = output_adapter.export(formatted_data, output_file)
    
    # public 폴더에 복사 (원본 파일명으로도 복사)
    import shutil
    public_pdf_latest = f"/app/frontend/public/GVIC_Report_Latest.pdf"
    public_pdf_named = f"/app/frontend/public/{os.path.basename(pdf_path)}"
    shutil.copy(pdf_path, public_pdf_latest)
    shutil.copy(pdf_path, public_pdf_named)
    
    # ===== 데이터 허브: 세션 완료 =====
    await data_hub.complete_session(pdf_path, "/GVIC_Report_Latest.pdf")
    
    tracker.log("URL분석", "완료", {"url": url, "records": total, "pdf": pdf_path})
    
    return {
        "success": True,
        "session_id": session.session_id,
        "url": url,
        "product_name": product_name,
        "site_type": crawl_result.site_type.value,
        "total_records": total,
        "sentiment_distribution": sentiment_distribution,
        "positive_factors": [{"category": f.category, "count": f.count, "ratio": f.ratio} for f in positive_factors],
        "negative_factors": [{"category": f.category, "count": f.count, "ratio": f.ratio} for f in negative_factors],
        "gvic_results": gvic_results,
        "insights": insights,
        "recommendations": recommendations,
        "pdf_url": "/GVIC_Report_Latest.pdf",
        "pdf_filename": os.path.basename(pdf_path)
    }


# ==================== 통합 데이터 조회 API (모든 탭 연동) ====================

@api_router.get("/hub/monitoring")
async def get_hub_monitoring():
    """모니터링 탭 데이터 - 실시간 이벤트 및 처리 이력"""
    return await data_hub.get_monitoring_data()

@api_router.get("/hub/predictions")
async def get_hub_predictions():
    """예측 탭 데이터 - GVIC 예측 결과"""
    return await data_hub.get_prediction_data()

@api_router.get("/hub/pareto")
async def get_hub_pareto():
    """파레토 탭 데이터 - 요인별 분석"""
    return await data_hub.get_pareto_data()

@api_router.get("/hub/comparison")
async def get_hub_comparison():
    """비교 탭 데이터 - 세션별 비교 분석"""
    return await data_hub.get_comparison_data()

@api_router.get("/hub/alerts")
async def get_hub_alerts(unread_only: bool = False):
    """알림 데이터"""
    alerts = await data_hub.get_alerts(unread_only)
    return {"alerts": alerts, "count": len(alerts)}

@api_router.post("/hub/alerts/{alert_id}/read")
async def mark_alert_read(alert_id: str):
    """알림 읽음 처리"""
    await db.alerts.update_one(
        {'id': alert_id},
        {'$set': {'read': True}}
    )
    return {"success": True}

@api_router.get("/hub/sessions")
async def get_analysis_sessions(limit: int = 20):
    """분석 세션 목록 조회"""
    sessions = await db.analysis_sessions.find(
        {}, {'_id': 0}
    ).sort('created_at', -1).limit(limit).to_list(limit)
    return {"sessions": sessions, "count": len(sessions)}

@api_router.get("/hub/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """분석 세션 상세 조회"""
    session = await db.analysis_sessions.find_one(
        {'session_id': session_id}, {'_id': 0}
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


# 서버 시작 시 저장된 데이터 소스 로드
@app.on_event("startup")
async def load_data_sources():
    """저장된 데이터 소스 로드"""
    try:
        sources = await db.data_sources.find({}, {"_id": 0}).to_list(100)
        for source in sources:
            source_id = source.pop("id", None)
            if source_id:
                data_sources[source_id] = source
        logging.info(f"Loaded {len(data_sources)} data sources")
    except Exception as e:
        logging.error(f"Error loading data sources: {e}")

# Include auth router in api_router
api_router.include_router(auth_router)

# Include the router in the main app

# ==================== Signal Tracer API ====================
# 시그널 추적기 - 단일 후기의 처리 과정을 단계별로 시각화

class SignalTracerInput(BaseModel):
    """시그널 추적기 입력"""
    content: str = Field(..., description="후기 내용")
    rating: int = Field(default=5, ge=1, le=5, description="평점 (1-5)")
    # 튜닝 가능한 파라미터
    sigma: Optional[List[float]] = Field(default=None, description="시그마 가중치 [V_pub, V_pro, V_ind]")
    omega_min: Optional[List[float]] = Field(default=None, description="오메가 최소값")
    omega_max: Optional[List[float]] = Field(default=None, description="오메가 최대값")
    # 키워드 가중치
    keyword_weights: Optional[Dict[str, float]] = Field(default=None, description="키워드별 가중치")

class SignalTracerResponse(BaseModel):
    """시그널 추적기 응답 - 5단계 결과"""
    success: bool
    trace_id: str
    steps: Dict[str, Any]

# 키워드 사전 (시그널 분류용)
SIGNAL_KEYWORDS = {
    "society": {  # 사회/규제 관점
        "positive": ["안전", "인증", "친환경", "무첨가", "자연", "유기농", "검증"],
        "negative": ["위험", "부작용", "알러지", "환경오염", "플라스틱", "화학"]
    },
    "production": {  # 생산/기업 관점
        "positive": ["품질", "포장", "배송", "꼼꼼", "신속", "정품", "유통기한"],
        "negative": ["불량", "파손", "지연", "오배송", "누락", "하자"]
    },
    "consumer": {  # 소비자 관점
        "positive": ["효과", "만족", "추천", "재구매", "좋아요", "최고", "가성비"],
        "negative": ["실망", "비싸", "효과없", "후회", "비추", "가격"]
    }
}

# AI 기반 시그널 감지기 초기화
from core.signal_detector import GVICSignalDetector
from core.gvic_models import Signal, SignalModule, SignalInput, GVICAsset, generate_id

signal_detector = None

def get_signal_detector():
    global signal_detector
    if signal_detector is None:
        try:
            signal_detector = GVICSignalDetector()
        except Exception as e:
            print(f"Signal detector init failed: {e}")
            return None
    return signal_detector


class AISignalAnalysisInput(BaseModel):
    """AI 기반 시그널 분석 입력"""
    content: str = Field(..., description="분석할 텍스트")
    include_perspective_mapping: bool = Field(default=True, description="3관점 매핑 포함 여부")


@api_router.post("/signal-tracer/ai-analyze")
async def ai_analyze_signal(
    request: AISignalAnalysisInput,
    current_user: dict = Depends(get_current_user)
):
    """
    AI 기반 시그널 분석 - 시그널 유형 자동 감지 및 특징 추출
    
    ID 체계:
    - input_id: 입력 고유 ID
    - module_id: 모듈 고유 ID  
    - signal_id: 개별 시그널 고유 ID
    - requester_id: 요구자 ID
    """
    # ID 생성
    requester_id = current_user.get("user_id")
    input_id = generate_id("INP")
    module_id = generate_id("MOD")
    
    detector = get_signal_detector()
    if detector is None:
        raise HTTPException(status_code=500, detail="AI 시그널 감지기 초기화 실패")
    
    try:
        result = await detector.detect_and_extract(
            text=request.content,
            session_id=f"gvic_{input_id}"
        )
        
        if not result.get("success", False):
            raise HTTPException(
                status_code=500, 
                detail=f"분석 실패: {result.get('error', 'Unknown error')}"
            )
        
        # 시그널 유형 라벨
        signal_type = result.get("signal_type", "unknown")
        signal_type_labels = {
            "product_review": "상품/서비스 후기",
            "requirement": "요구사항/기능요청",
            "complaint": "불만/클레임",
            "inquiry": "문의/질문",
            "news": "뉴스/기사",
            "feedback": "피드백/제안",
            "conversation": "일상대화",
            "data": "데이터/수치",
            "unknown": "분류불가"
        }
        
        # 개별 시그널에 ID 부여
        discovered_signals = result.get("discovered_signals", [])
        signals_with_id = []
        for sig in discovered_signals:
            signal_id = generate_id("SIG")
            sig_with_id = {
                "signal_id": signal_id,
                "module_id": module_id,
                "input_id": input_id,
                **sig
            }
            signals_with_id.append(sig_with_id)
        
        response_data = {
            "success": True,
            
            # ID 체계
            "input_id": input_id,
            "module_id": module_id,
            "requester_id": requester_id,
            
            # 입력 정보
            "raw_content": request.content,
            "content_length": len(request.content),
            
            # 모듈 정보
            "signal_type": signal_type,
            "signal_type_label": signal_type_labels.get(signal_type, "알 수 없음"),
            "signal_type_confidence": result.get("signal_type_confidence", 0),
            "signal_type_reason": result.get("signal_type_reason", ""),
            
            # 시그널들 (각각 signal_id 포함)
            "discovered_signals": signals_with_id,
            "signal_count": len(signals_with_id),
            
            # 분석 결과
            "overall_sentiment": result.get("overall_sentiment", "neutral"),
            "key_themes": result.get("key_themes", []),
            "summary": result.get("summary", ""),
            
            # 3관점 적용 여부
            "applicable_perspectives": result.get("applicable_perspectives", {
                "society": False,
                "production": False,
                "consumer": False
            }),
            "perspective_relevance": result.get("perspective_relevance", ""),
            
            # 메타데이터
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # 실시간 모니터링에 기록
        record_signal_analysis(request.content, response_data, success=True)
        
        return response_data
        
    except HTTPException:
        # 실패 기록
        record_signal_analysis(request.content, {"signal_type": "error"}, success=False)
        raise
    except Exception as e:
        record_signal_analysis(request.content, {"signal_type": "error"}, success=False)
        raise HTTPException(status_code=500, detail=f"분석 중 오류: {str(e)}")


def analyze_keywords(content: str, custom_weights: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """키워드 기반 시그널 분석"""
    results = {
        "society": {"positive": [], "negative": [], "score": 0},
        "production": {"positive": [], "negative": [], "score": 0},
        "consumer": {"positive": [], "negative": [], "score": 0}
    }
    
    content_lower = content.lower()
    
    for domain, keywords in SIGNAL_KEYWORDS.items():
        pos_count = 0
        neg_count = 0
        
        for kw in keywords["positive"]:
            if kw in content_lower:
                results[domain]["positive"].append(kw)
                weight = custom_weights.get(kw, 1.0) if custom_weights else 1.0
                pos_count += weight
                
        for kw in keywords["negative"]:
            if kw in content_lower:
                results[domain]["negative"].append(kw)
                weight = custom_weights.get(kw, 1.0) if custom_weights else 1.0
                neg_count += weight
        
        # 점수 계산 (0-100)
        total = pos_count + neg_count
        if total > 0:
            results[domain]["score"] = int((pos_count / (pos_count + neg_count + 0.5)) * 100)
        else:
            results[domain]["score"] = 50  # 중립
    
    return results

@api_router.post("/signal-tracer/analyze", response_model=SignalTracerResponse)
async def analyze_single_review(request: SignalTracerInput, current_user: dict = Depends(get_current_user)):
    """
    시그널 추적기 - 단일 후기를 5단계로 분석
    회원 전용 기능
    """
    trace_id = str(uuid.uuid4())[:8]
    
    # 기본 파라미터 설정
    sigma = request.sigma or [0.33, 0.34, 0.33]
    omega_min = request.omega_min or [0.2, 0.2, 0.1]
    omega_max = request.omega_max or [0.5, 0.5, 0.5]
    
    # ==================== STEP 1: 입력 ====================
    step1_input = {
        "step": 1,
        "name": "입력 (Input)",
        "description": "원본 후기 데이터",
        "data": {
            "content": request.content,
            "rating": request.rating,
            "char_count": len(request.content),
            "word_count": len(request.content.split())
        }
    }
    
    # ==================== STEP 2: 표준화 ====================
    # 평점을 0-100 스케일로 변환
    normalized_value = (request.rating / 5.0) * 100
    
    # 감성 힌트 결정
    if request.rating >= 4:
        sentiment_hint = "positive"
    elif request.rating == 3:
        sentiment_hint = "neutral"
    else:
        sentiment_hint = "negative"
    
    step2_standardize = {
        "step": 2,
        "name": "표준화 (Standardization)",
        "description": "GVIC 표준 입력 포맷으로 변환",
        "transformation": {
            "rating_scale": "1-5 → 0-100",
            "formula": f"({request.rating} / 5) × 100 = {normalized_value}"
        },
        "data": {
            "primary_value": normalized_value,
            "sentiment_hint": sentiment_hint,
            "source_type": "direct_input",
            "domain": "product_review"
        }
    }
    
    # ==================== STEP 3: 시그널 분석 ====================
    keyword_analysis = analyze_keywords(request.content, request.keyword_weights)
    
    # 각 영역별 원시 점수
    raw_scores = {
        "V_pub": keyword_analysis["society"]["score"],
        "V_pro": keyword_analysis["production"]["score"],
        "V_ind": keyword_analysis["consumer"]["score"]
    }
    
    # 평점 기반 보정
    rating_factor = normalized_value / 100
    for key in raw_scores:
        raw_scores[key] = int(raw_scores[key] * 0.6 + rating_factor * 100 * 0.4)
    
    step3_signal = {
        "step": 3,
        "name": "시그널 분석 (Signal Analysis)",
        "description": "3가지 관점에서 시그널 추출",
        "keyword_analysis": {
            "society": {
                "label": "🏛️ 사회·규제 관점",
                "found_positive": keyword_analysis["society"]["positive"],
                "found_negative": keyword_analysis["society"]["negative"],
                "raw_score": keyword_analysis["society"]["score"]
            },
            "production": {
                "label": "🏭 기업·생산 관점",
                "found_positive": keyword_analysis["production"]["positive"],
                "found_negative": keyword_analysis["production"]["negative"],
                "raw_score": keyword_analysis["production"]["score"]
            },
            "consumer": {
                "label": "👤 소비자·고객 관점",
                "found_positive": keyword_analysis["consumer"]["positive"],
                "found_negative": keyword_analysis["consumer"]["negative"],
                "raw_score": keyword_analysis["consumer"]["score"]
            }
        },
        "raw_scores": raw_scores,
        "rating_adjustment": f"평점({request.rating}점) 기반 40% 보정 적용"
    }
    
    # ==================== STEP 4: 수렴 연산 ====================
    import numpy as np
    
    # 시그마 가중치 적용
    sigma_arr = np.array(sigma)
    scores_arr = np.array([raw_scores["V_pub"], raw_scores["V_pro"], raw_scores["V_ind"]])
    
    # 가중 평균 계산
    weighted_scores = scores_arr * sigma_arr
    
    # 정규화 (합이 100이 되도록)
    total = np.sum(weighted_scores)
    if total > 0:
        normalized_distribution = (weighted_scores / total) * 100
    else:
        normalized_distribution = np.array([33.33, 33.34, 33.33])
    
    # 오메가 경계 조건 검증
    omega_min_arr = np.array(omega_min) * 100
    omega_max_arr = np.array(omega_max) * 100
    
    boundary_violations = []
    adjusted_distribution = normalized_distribution.copy()
    
    for i, (val, min_v, max_v, name) in enumerate(zip(
        normalized_distribution, 
        omega_min_arr, 
        omega_max_arr,
        ["V_pub", "V_pro", "V_ind"]
    )):
        if val < min_v:
            boundary_violations.append(f"{name}: {val:.1f}% < 최소 {min_v:.1f}%")
            adjusted_distribution[i] = min_v
        elif val > max_v:
            boundary_violations.append(f"{name}: {val:.1f}% > 최대 {max_v:.1f}%")
            adjusted_distribution[i] = max_v
    
    # 재정규화
    if boundary_violations:
        adjusted_distribution = (adjusted_distribution / np.sum(adjusted_distribution)) * 100
    
    step4_convergence = {
        "step": 4,
        "name": "수렴 연산 (Convergence)",
        "description": "Σ 시그마 가중치 적용 및 Ω 오메가 경계 검증",
        "sigma_applied": {
            "weights": {"V_pub": sigma[0], "V_pro": sigma[1], "V_ind": sigma[2]},
            "formula": "weighted_score = raw_score × sigma",
            "weighted_scores": {
                "V_pub": round(weighted_scores[0], 2),
                "V_pro": round(weighted_scores[1], 2),
                "V_ind": round(weighted_scores[2], 2)
            }
        },
        "omega_validation": {
            "boundaries": {
                "V_pub": f"{omega_min[0]*100:.0f}% ~ {omega_max[0]*100:.0f}%",
                "V_pro": f"{omega_min[1]*100:.0f}% ~ {omega_max[1]*100:.0f}%",
                "V_ind": f"{omega_min[2]*100:.0f}% ~ {omega_max[2]*100:.0f}%"
            },
            "violations": boundary_violations if boundary_violations else ["없음 - 경계 조건 충족"],
            "is_valid": len(boundary_violations) == 0
        },
        "distribution": {
            "before_adjustment": {
                "V_pub": round(normalized_distribution[0], 2),
                "V_pro": round(normalized_distribution[1], 2),
                "V_ind": round(normalized_distribution[2], 2)
            },
            "after_adjustment": {
                "V_pub": round(adjusted_distribution[0], 2),
                "V_pro": round(adjusted_distribution[1], 2),
                "V_ind": round(adjusted_distribution[2], 2)
            }
        }
    }
    
    # ==================== STEP 5: 최종 출력 ====================
    # 종합 점수 계산
    final_score = int(np.sum(scores_arr * sigma_arr))
    
    # 인사이트 생성
    insights = []
    
    # 긍정 키워드 기반 인사이트
    all_positive = (
        keyword_analysis["society"]["positive"] + 
        keyword_analysis["production"]["positive"] + 
        keyword_analysis["consumer"]["positive"]
    )
    all_negative = (
        keyword_analysis["society"]["negative"] + 
        keyword_analysis["production"]["negative"] + 
        keyword_analysis["consumer"]["negative"]
    )
    
    if all_positive:
        insights.append({"type": "positive", "text": f"긍정 요소: {', '.join(all_positive)}"})
    if all_negative:
        insights.append({"type": "negative", "text": f"개선 필요: {', '.join(all_negative)}"})
    
    # 영역별 인사이트
    max_domain = max(["V_pub", "V_pro", "V_ind"], key=lambda x: adjusted_distribution[["V_pub", "V_pro", "V_ind"].index(x)])
    domain_labels = {"V_pub": "사회·규제", "V_pro": "기업·생산", "V_ind": "소비자·고객"}
    insights.append({
        "type": "info", 
        "text": f"주요 관점: {domain_labels[max_domain]} ({adjusted_distribution[['V_pub', 'V_pro', 'V_ind'].index(max_domain)]:.1f}%)"
    })
    
    # 분류 결정
    if final_score >= 70:
        classification = "긍정"
        classification_color = "green"
    elif final_score >= 40:
        classification = "중립"
        classification_color = "yellow"
    else:
        classification = "부정"
        classification_color = "red"
    
    step5_output = {
        "step": 5,
        "name": "최종 출력 (Output)",
        "description": "분석 결과 및 인사이트",
        "final_score": {
            "value": final_score,
            "max": 100,
            "classification": classification,
            "color": classification_color
        },
        "distribution_chart": {
            "V_pub": {"label": "🏛️ 사회·규제", "value": round(adjusted_distribution[0], 1)},
            "V_pro": {"label": "🏭 기업·생산", "value": round(adjusted_distribution[1], 1)},
            "V_ind": {"label": "👤 소비자·고객", "value": round(adjusted_distribution[2], 1)}
        },
        "insights": insights,
        "recommendations": [
            "이 후기는 제품 품질에 대한 피드백을 포함합니다." if keyword_analysis["production"]["positive"] or keyword_analysis["production"]["negative"] else None,
            "소비자 만족도 관련 의견이 포함되어 있습니다." if keyword_analysis["consumer"]["positive"] or keyword_analysis["consumer"]["negative"] else None,
            "사회적/규제적 관점의 언급이 있습니다." if keyword_analysis["society"]["positive"] or keyword_analysis["society"]["negative"] else None
        ]
    }
    # None 제거
    step5_output["recommendations"] = [r for r in step5_output["recommendations"] if r]
    
    # 전체 응답 조립
    return SignalTracerResponse(
        success=True,
        trace_id=trace_id,
        steps={
            "step1_input": step1_input,
            "step2_standardize": step2_standardize,
            "step3_signal": step3_signal,
            "step4_convergence": step4_convergence,
            "step5_output": step5_output
        }
    )

@api_router.get("/signal-tracer/keywords")
async def get_signal_keywords(current_user: dict = Depends(get_current_user)):
    """시그널 분석에 사용되는 키워드 사전 조회"""
    return {
        "keywords": SIGNAL_KEYWORDS,
        "description": {
            "society": "사회·규제 관점 (환경, 안전, 인증 등)",
            "production": "기업·생산 관점 (품질, 포장, 배송 등)",
            "consumer": "소비자·고객 관점 (효과, 만족, 가성비 등)"
        }
    }

@api_router.put("/signal-tracer/keywords")
async def update_signal_keywords(
    keywords: Dict[str, Dict[str, List[str]]],
    current_user: dict = Depends(require_role(["admin", "super_admin"]))
):
    """시그널 키워드 사전 업데이트 (관리자 전용)"""
    global SIGNAL_KEYWORDS
    SIGNAL_KEYWORDS = keywords
    return {"success": True, "message": "키워드 사전이 업데이트되었습니다."}


# ==================== GVIC 자산 관리 API ====================
# GVIC 자산 - 분석된 데이터를 구조화된 자산으로 저장

class GVICAssetCreate(BaseModel):
    """GVIC 자산 생성 요청"""
    content: str
    rating: int
    analysis_result: Dict[str, Any]

class GVICAssetCreateV2(BaseModel):
    content: str
    rating: int = 5
    analysis_result: dict
    visibility: str = "showcase"  # "showcase" (공개) or "private" (유료요구자 전용)

@api_router.post("/gvic-assets")
async def create_gvic_asset(
    request: GVICAssetCreate,
    current_user: dict = Depends(get_current_user)
):
    """AI 분석 결과를 GVIC 자산(모듈)으로 저장"""
    try:
        result = request.analysis_result
        
        # 유료 요구자 여부 확인 (role 기반 또는 별도 필드로 관리)
        # 유료 요구자: ext_admin, ext_operator 등 외부 역할 또는 별도 표시
        user_role = current_user.get("role", "visitor")
        is_paid_requester = user_role in ["ext_admin", "ext_operator"] or current_user.get("is_paid", False)
        
        # 기본 visibility 결정: 유료 요구자는 private, 그 외는 showcase
        visibility = "private" if is_paid_requester else "showcase"
        
        # AI 분석 결과인지 기존 키워드 분석 결과인지 확인
        is_ai_result = "signal_type" in result and "discovered_signals" in result
        
        if is_ai_result:
            discovered_signals = result.get("discovered_signals", [])
            
            overall_sentiment = result.get("overall_sentiment", "neutral")
            if overall_sentiment == "positive":
                classification = "긍정"
            elif overall_sentiment == "negative":
                classification = "부정"
            elif overall_sentiment == "mixed":
                classification = "혼합"
            else:
                classification = "중립"
            
            signal_texts = [sig.get("text", "") for sig in discovered_signals]
            signal_types = list(set([sig.get("type", "") for sig in discovered_signals]))
            hidden_meanings = [sig.get("hidden_meaning", "") for sig in discovered_signals if sig.get("hidden_meaning")]
            
            asset = {
                "asset_id": f"AST_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6].upper()}",
                "raw_content": request.content,
                "content_length": len(request.content),
                "module_id": result.get("module_id"),
                "input_id": result.get("input_id"),
                "signal_type": result.get("signal_type"),
                "signal_type_label": result.get("signal_type_label"),
                "signal_count": result.get("signal_count", 0),
                "discovered_signals": discovered_signals,
                "signal_texts": signal_texts,
                "signal_types": signal_types,
                "hidden_meanings": hidden_meanings,
                "summary": result.get("summary", ""),
                "key_themes": result.get("key_themes", []),
                "overall_sentiment": overall_sentiment,
                "classification": classification,
                "applicable_perspectives": result.get("applicable_perspectives", {}),
                "perspective_relevance": result.get("perspective_relevance", ""),
                "created_by": current_user.get("user_id"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used_count": 0,
                "used_for": [],
                "full_analysis": result,
                # 접근 제어
                "visibility": visibility,
                "owner_id": current_user.get("user_id")
            }
        else:
            steps = result.get("steps", {})
            step5 = steps.get("step5_output", {})
            step4 = steps.get("step4_convergence", {})
            final_score = step5.get("final_score", {})
            distribution = step4.get("distribution", {}).get("after_adjustment", {})
            
            asset = {
                "asset_id": f"AST_{uuid.uuid4().hex[:8].upper()}",
                "raw_content": request.content,
                "content_length": len(request.content),
                "rating": request.rating,
                "score": final_score.get("value", 0),
                "classification": final_score.get("classification", "미분류"),
                "v_pub": distribution.get("V_pub", 0),
                "v_pro": distribution.get("V_pro", 0),
                "v_ind": distribution.get("V_ind", 0),
                "signal_type": "legacy_keyword",
                "signal_type_label": "키워드 분석 (레거시)",
                "summary": "",
                "key_themes": [],
                "signal_texts": [],
                "full_analysis": result,
                "created_by": current_user.get("user_id"),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "used_count": 0,
                "used_for": [],
                "visibility": visibility,
                "owner_id": current_user.get("user_id")
            }
        
        await db.gvic_assets.insert_one(asset)
        
        return {"success": True, "asset_id": asset["asset_id"], "message": "자산(모듈)이 저장되었습니다."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자산 저장 실패: {str(e)}")

@api_router.get("/gvic-assets")
async def get_gvic_assets(
    limit: int = 50,
    classification: Optional[str] = None,
    search: Optional[str] = None,
    signal_type: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """GVIC 자산(모듈) 목록 조회 - 모듈화된 데이터 검색"""
    try:
        query = {}
        if classification:
            query["classification"] = classification
        if signal_type:
            query["signal_type"] = signal_type
        
        # 모듈화된 데이터 검색 (원시 content가 아닌 모듈 데이터 검색)
        if search:
            search_lower = search.lower()
            query["$or"] = [
                # 시그널 유형 레이블
                {"signal_type_label": {"$regex": search, "$options": "i"}},
                # 시그널 텍스트들
                {"signal_texts": {"$regex": search, "$options": "i"}},
                # 요약
                {"summary": {"$regex": search, "$options": "i"}},
                # 주요 테마
                {"key_themes": {"$regex": search, "$options": "i"}},
                # 숨겨진 의미
                {"hidden_meanings": {"$regex": search, "$options": "i"}},
                # 시그널 유형들
                {"signal_types": {"$regex": search, "$options": "i"}},
                # 관점 관련성
                {"perspective_relevance": {"$regex": search, "$options": "i"}},
                # 모듈 ID로도 검색 가능
                {"module_id": {"$regex": search, "$options": "i"}},
                {"asset_id": {"$regex": search, "$options": "i"}}
            ]
        
        assets_cursor = db.gvic_assets.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        assets = await assets_cursor.to_list(length=limit)
        
        # 통계 계산
        total = await db.gvic_assets.count_documents({})
        positive = await db.gvic_assets.count_documents({"classification": "긍정"})
        neutral = await db.gvic_assets.count_documents({"classification": "중립"})
        negative = await db.gvic_assets.count_documents({"classification": "부정"})
        mixed = await db.gvic_assets.count_documents({"classification": "혼합"})
        
        # 시그널 유형별 통계
        signal_type_stats = {}
        pipeline = [
            {"$group": {"_id": "$signal_type_label", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        async for doc in db.gvic_assets.aggregate(pipeline):
            if doc["_id"]:
                signal_type_stats[doc["_id"]] = doc["count"]
        
        stats = {
            "total": total,
            "positive": positive,
            "neutral": neutral,
            "negative": negative,
            "mixed": mixed,
            "by_signal_type": signal_type_stats
        }
        
        return {"assets": assets, "stats": stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자산 조회 실패: {str(e)}")

@api_router.get("/gvic-warehouse")
async def get_gvic_warehouse(
    current_user: dict = Depends(get_current_user)
):
    """자산화창고 - 공개 쇼케이스용 탑 10 유사 모듈"""
    try:
        # 공개(showcase) 자산만 조회
        base_query = {"visibility": {"$in": ["showcase", None]}}  # None은 기존 데이터 호환
        
        # 시그널 유형별 그룹화 및 카운트 (탑 10)
        pipeline = [
            {"$match": base_query},
            {"$group": {
                "_id": "$signal_type_label",
                "count": {"$sum": 1},
                "sample_assets": {"$push": {
                    "asset_id": "$asset_id",
                    "summary": "$summary",
                    "classification": "$classification",
                    "key_themes": "$key_themes",
                    "signal_count": "$signal_count",
                    "overall_sentiment": "$overall_sentiment"
                }}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10},
            {"$project": {
                "signal_type": "$_id",
                "count": 1,
                "sample_assets": {"$slice": ["$sample_assets", 3]}  # 각 유형별 샘플 3개
            }}
        ]
        
        top_modules = []
        async for doc in db.gvic_assets.aggregate(pipeline):
            if doc.get("_id"):
                top_modules.append({
                    "signal_type": doc["signal_type"],
                    "count": doc["count"],
                    "samples": doc.get("sample_assets", [])
                })
        
        # 전체 통계 (공개 자산만)
        total_showcase = await db.gvic_assets.count_documents(base_query)
        
        # 감성별 통계
        sentiment_stats = {
            "positive": await db.gvic_assets.count_documents({**base_query, "classification": "긍정"}),
            "negative": await db.gvic_assets.count_documents({**base_query, "classification": "부정"}),
            "mixed": await db.gvic_assets.count_documents({**base_query, "classification": "혼합"}),
            "neutral": await db.gvic_assets.count_documents({**base_query, "classification": "중립"})
        }
        
        return {
            "top_modules": top_modules,
            "total_showcase": total_showcase,
            "sentiment_stats": sentiment_stats,
            "message": "궁금증을 자아내는 자산화창고입니다"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"자산화창고 조회 실패: {str(e)}")

class NLSearchRequest(BaseModel):
    query: str

@api_router.post("/gvic-warehouse/search")
async def search_warehouse_nl(
    request: NLSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """자산화창고 자연어 검색 - AI 기반"""
    try:
        from core.signal_detector import GVICSignalDetector
        detector = GVICSignalDetector()
        
        # 자연어 쿼리를 AI로 분석하여 검색 키워드 추출
        prompt = f"""사용자가 자산화창고에서 다음과 같이 검색했습니다:
"{request.query}"

이 자연어 검색 쿼리에서 핵심 검색 키워드들을 추출해주세요.
응답은 JSON 형식으로:
{{"keywords": ["키워드1", "키워드2", ...], "intent": "검색 의도 요약", "sentiment_filter": "positive/negative/mixed/neutral/all"}}
"""
        
        # AI로 검색 의도 분석
        search_analysis = await detector._call_llm(prompt)
        
        # 검색 실행 (공개 자산만)
        base_query = {"visibility": {"$in": ["showcase", None]}}
        
        # 추출된 키워드로 검색
        keywords = search_analysis.get("keywords", [request.query])
        sentiment_filter = search_analysis.get("sentiment_filter", "all")
        
        search_conditions = []
        for kw in keywords:
            search_conditions.extend([
                {"signal_type_label": {"$regex": kw, "$options": "i"}},
                {"summary": {"$regex": kw, "$options": "i"}},
                {"key_themes": {"$regex": kw, "$options": "i"}},
                {"signal_texts": {"$regex": kw, "$options": "i"}},
                {"hidden_meanings": {"$regex": kw, "$options": "i"}}
            ])
        
        if search_conditions:
            base_query["$or"] = search_conditions
        
        if sentiment_filter != "all":
            sentiment_map = {"positive": "긍정", "negative": "부정", "mixed": "혼합", "neutral": "중립"}
            if sentiment_filter in sentiment_map:
                base_query["classification"] = sentiment_map[sentiment_filter]
        
        # 검색 결과
        cursor = db.gvic_assets.find(base_query, {"_id": 0, "full_analysis": 0}).sort("created_at", -1).limit(10)
        results = await cursor.to_list(length=10)
        
        return {
            "query": request.query,
            "analysis": {
                "keywords": keywords,
                "intent": search_analysis.get("intent", ""),
                "sentiment_filter": sentiment_filter
            },
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        # AI 분석 실패 시 단순 키워드 검색으로 폴백
        base_query = {
            "visibility": {"$in": ["showcase", None]},
            "$or": [
                {"summary": {"$regex": request.query, "$options": "i"}},
                {"key_themes": {"$regex": request.query, "$options": "i"}},
                {"signal_type_label": {"$regex": request.query, "$options": "i"}}
            ]
        }
        cursor = db.gvic_assets.find(base_query, {"_id": 0, "full_analysis": 0}).sort("created_at", -1).limit(10)
        results = await cursor.to_list(length=10)
        
        return {
            "query": request.query,
            "analysis": {"keywords": [request.query], "intent": "단순 검색", "sentiment_filter": "all"},
            "results": results,
            "count": len(results)
        }

@api_router.get("/gvic-assets/my")
async def get_my_assets(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """내 자산 조회 (유료 요구자용) - 본인 자산만"""
    try:
        query = {"owner_id": current_user.get("user_id")}
        cursor = db.gvic_assets.find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
        assets = await cursor.to_list(length=limit)
        
        total = await db.gvic_assets.count_documents(query)
        
        return {"assets": assets, "total": total}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"내 자산 조회 실패: {str(e)}")

@api_router.get("/gvic-assets/{asset_id}")
async def get_gvic_asset(
    asset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """특정 GVIC 자산 상세 조회"""
    asset = await db.gvic_assets.find_one({"asset_id": asset_id}, {"_id": 0})
    if not asset:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다.")
    return asset

@api_router.delete("/gvic-assets/{asset_id}")
async def delete_gvic_asset(
    asset_id: str,
    current_user: dict = Depends(require_role(["admin", "super_admin"]))
):
    """GVIC 자산 삭제 (관리자 전용)"""
    result = await db.gvic_assets.delete_one({"asset_id": asset_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다.")
    return {"success": True, "message": "자산이 삭제되었습니다."}

@api_router.post("/gvic-assets/{asset_id}/use")
async def record_asset_usage(
    asset_id: str,
    usage_type: str,
    current_user: dict = Depends(get_current_user)
):
    """자산 사용 기록"""
    result = await db.gvic_assets.update_one(
        {"asset_id": asset_id},
        {
            "$inc": {"used_count": 1},
            "$push": {"used_for": {"type": usage_type, "at": datetime.now(timezone.utc).isoformat()}}
        }
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다.")
    return {"success": True, "message": "사용 기록이 추가되었습니다."}


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
