"""
GVIC PDF Report Generator Module
- 시그널 분석 결과 PDF 리포트 생성
- 대시보드 통계 리포트
- 자산 포트폴리오 리포트
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import tempfile
import io
import os
import logging

router = APIRouter(prefix="/api/report", tags=["report"])
logger = logging.getLogger(__name__)

# JWT Secret
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

async def get_current_user_simple(authorization: str = Header(None)):
    """간단한 인증 확인"""
    import jwt
    
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    
    try:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        if not token or token in ('null', 'undefined', ''):
            raise HTTPException(status_code=401, detail="토큰이 없습니다")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

# ==================== Models ====================

class SignalReportRequest(BaseModel):
    signal_id: str = Field(..., description="시그널 ID")
    include_ai_analysis: bool = Field(True, description="AI 분석 결과 포함")
    include_pipeline_stages: bool = Field(True, description="파이프라인 단계 포함")

class DashboardReportRequest(BaseModel):
    date_range: str = Field("7d", description="기간: 1d, 7d, 30d, all")
    include_charts: bool = Field(True, description="차트 포함")
    include_recent_signals: bool = Field(True, description="최근 시그널 포함")

class AssetReportRequest(BaseModel):
    asset_ids: List[str] = Field(default_factory=list, description="특정 자산 ID 목록")
    category: str = Field("all", description="카테고리 필터")
    limit: int = Field(50, description="최대 자산 수")

# ==================== PDF Generation Helpers ====================

def create_pdf_styles():
    """PDF 스타일 설정"""
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    styles = getSampleStyleSheet()
    
    # 커스텀 스타일 추가
    styles.add(ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#334155'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        textColor=colors.HexColor('#475569'),
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        textColor=colors.HexColor('#334155')
    ))
    
    styles.add(ParagraphStyle(
        'CustomSmall',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#64748b')
    ))
    
    return styles

def create_table_style(header_color='#3b82f6'):
    """테이블 스타일 생성"""
    from reportlab.lib import colors
    from reportlab.platypus import TableStyle
    
    return TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(header_color)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#334155')),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white])
    ])

# ==================== Report Endpoints ====================

@router.post("/signal")
async def generate_signal_report(
    request: SignalReportRequest,
    current_user: dict = Depends(get_current_user_simple)
):
    """
    시그널 분석 결과 PDF 리포트 생성
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, PageBreak
    from reportlab.lib.units import cm
    
    from server import db
    
    # 시그널 조회
    signal = await db.pipeline_signals.find_one(
        {"signal_id": request.signal_id},
        {"_id": 0}
    )
    
    if not signal:
        raise HTTPException(status_code=404, detail="시그널을 찾을 수 없습니다")
    
    # PDF 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_pdf_styles()
    elements = []
    
    # 제목
    elements.append(Paragraph("GVIC Signal Analysis Report", styles['CustomTitle']))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles['CustomSmall']
    ))
    elements.append(Spacer(1, 20))
    
    # 시그널 기본 정보
    elements.append(Paragraph("1. Signal Information", styles['CustomHeading']))
    
    info_data = [
        ["Field", "Value"],
        ["Signal ID", signal.get("signal_id", "-")],
        ["Type", signal.get("type", "-")],
        ["Category", signal.get("category", "-")],
        ["Status", signal.get("status", "-")],
        ["Created At", str(signal.get("created_at", "-"))[:19]],
        ["Source", signal.get("source", "-")[:50]]
    ]
    
    info_table = Table(info_data, colWidths=[5*cm, 11*cm])
    info_table.setStyle(create_table_style('#3b82f6'))
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    # 시그널 내용
    elements.append(Paragraph("2. Signal Content", styles['CustomHeading']))
    content = signal.get("content", "")[:2000]
    if len(signal.get("content", "")) > 2000:
        content += "... (truncated)"
    elements.append(Paragraph(content.replace('\n', '<br/>'), styles['CustomNormal']))
    elements.append(Spacer(1, 20))
    
    # AI 분석 결과
    if request.include_ai_analysis:
        ai_response = signal.get("ai_response", {})
        metadata = signal.get("metadata", {})
        ai_analysis = metadata.get("ai_analysis", {})
        
        if ai_analysis or ai_response:
            elements.append(Paragraph("3. AI Analysis Results", styles['CustomHeading']))
            
            analysis_type = ai_analysis.get("analysis_type", metadata.get("analysis_type", "general"))
            elements.append(Paragraph(f"Analysis Type: {analysis_type}", styles['CustomSubHeading']))
            
            # 분석 요약
            summary = ai_analysis.get("analysis_summary", ai_response.get("summary", ""))
            if summary:
                elements.append(Paragraph("Summary:", styles['CustomSubHeading']))
                elements.append(Paragraph(summary, styles['CustomNormal']))
                elements.append(Spacer(1, 10))
            
            # 신뢰도
            confidence = ai_analysis.get("confidence", ai_response.get("confidence", 0))
            if confidence:
                elements.append(Paragraph(f"Confidence: {float(confidence)*100:.1f}%", styles['CustomNormal']))
            
            # 핵심 포인트
            key_points = ai_analysis.get("key_points", [])
            if key_points:
                elements.append(Paragraph("Key Points:", styles['CustomSubHeading']))
                for point in key_points[:10]:
                    elements.append(Paragraph(f"• {point}", styles['CustomNormal']))
            
            elements.append(Spacer(1, 20))
    
    # 파이프라인 단계
    if request.include_pipeline_stages:
        elements.append(Paragraph("4. Pipeline Stages", styles['CustomHeading']))
        
        stages_completed = signal.get("stages_completed", [])
        status_dict = signal.get("status_dict", {})
        
        stage_data = [["Stage", "Status", "Timestamp"]]
        
        stage_names = {
            "j_input": "J:입력",
            "ll_evaluate": "LL:의도",
            "h_core": "H:코어",
            "a_asset": "A:자산화",
            "g_module": "G:모듈화"
        }
        
        for stage_key, stage_name in stage_names.items():
            if stage_key in stages_completed:
                stage_status = status_dict.get(stage_key, {})
                stage_data.append([
                    stage_name,
                    "Completed",
                    str(stage_status.get("completed_at", "-"))[:19] if isinstance(stage_status, dict) else "-"
                ])
            else:
                stage_data.append([stage_name, "Pending", "-"])
        
        stage_table = Table(stage_data, colWidths=[5*cm, 5*cm, 6*cm])
        stage_table.setStyle(create_table_style('#10b981'))
        elements.append(stage_table)
    
    # 푸터
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        "Generated by GVIC Engine v2.0.0 - AI-Powered Signal Analysis Platform",
        styles['CustomSmall']
    ))
    
    # PDF 빌드
    doc.build(elements)
    
    logger.info(f"Signal report generated: {request.signal_id}")
    
    return FileResponse(
        temp_file.name,
        media_type="application/pdf",
        filename=f"gvic_signal_report_{request.signal_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

@router.post("/dashboard")
async def generate_dashboard_report(
    request: DashboardReportRequest,
    current_user: dict = Depends(get_current_user_simple)
):
    """
    대시보드 통계 PDF 리포트 생성
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.units import cm
    
    from server import db
    
    # 날짜 범위 계산
    now = datetime.now(timezone.utc)
    if request.date_range == "1d":
        start_date = now - timedelta(days=1)
        range_label = "Last 24 Hours"
    elif request.date_range == "7d":
        start_date = now - timedelta(days=7)
        range_label = "Last 7 Days"
    elif request.date_range == "30d":
        start_date = now - timedelta(days=30)
        range_label = "Last 30 Days"
    else:
        start_date = None
        range_label = "All Time"
    
    # 통계 집계
    query = {}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    
    total_signals = await db.pipeline_signals.count_documents(query)
    completed_signals = await db.pipeline_signals.count_documents({**query, "status": "completed"})
    
    wanted_count = await db.pipeline_signals.count_documents({**query, "category": "wanted"})
    unwanted_count = await db.pipeline_signals.count_documents({**query, "category": "unwanted"})
    null_count = await db.pipeline_signals.count_documents({**query, "category": "null"})
    
    total_assets = await db.gvic_assets.count_documents({})
    
    # PDF 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_pdf_styles()
    elements = []
    
    # 제목
    elements.append(Paragraph("GVIC Dashboard Report", styles['CustomTitle']))
    elements.append(Paragraph(f"Period: {range_label}", styles['CustomSubHeading']))
    elements.append(Paragraph(
        f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles['CustomSmall']
    ))
    elements.append(Spacer(1, 30))
    
    # 전체 통계
    elements.append(Paragraph("1. Overall Statistics", styles['CustomHeading']))
    
    success_rate = (completed_signals / total_signals * 100) if total_signals > 0 else 0
    
    stats_data = [
        ["Metric", "Value"],
        ["Total Signals", str(total_signals)],
        ["Completed Signals", str(completed_signals)],
        ["Success Rate", f"{success_rate:.1f}%"],
        ["Total Assets", str(total_assets)]
    ]
    
    stats_table = Table(stats_data, colWidths=[8*cm, 8*cm])
    stats_table.setStyle(create_table_style('#3b82f6'))
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    # 카테고리별 분포
    elements.append(Paragraph("2. Signal Categories", styles['CustomHeading']))
    
    category_data = [
        ["Category", "Count", "Percentage"],
        ["Wanted (직접 분석)", str(wanted_count), f"{wanted_count/total_signals*100:.1f}%" if total_signals > 0 else "0%"],
        ["Unwanted (자산화)", str(unwanted_count), f"{unwanted_count/total_signals*100:.1f}%" if total_signals > 0 else "0%"],
        ["Null", str(null_count), f"{null_count/total_signals*100:.1f}%" if total_signals > 0 else "0%"],
        ["Total", str(total_signals), "100%"]
    ]
    
    category_table = Table(category_data, colWidths=[6*cm, 5*cm, 5*cm])
    category_table.setStyle(create_table_style('#10b981'))
    elements.append(category_table)
    elements.append(Spacer(1, 20))
    
    # 최근 시그널
    if request.include_recent_signals:
        elements.append(Paragraph("3. Recent Signals", styles['CustomHeading']))
        
        recent_signals = await db.pipeline_signals.find(
            query,
            {"_id": 0, "signal_id": 1, "type": 1, "category": 1, "status": 1, "created_at": 1}
        ).sort("created_at", -1).limit(10).to_list(10)
        
        if recent_signals:
            recent_data = [["Signal ID", "Type", "Category", "Status"]]
            for sig in recent_signals:
                recent_data.append([
                    sig.get("signal_id", "-")[:15],
                    sig.get("type", "-"),
                    sig.get("category", "-"),
                    sig.get("status", "-")
                ])
            
            recent_table = Table(recent_data, colWidths=[5*cm, 4*cm, 4*cm, 3*cm])
            recent_table.setStyle(create_table_style('#8b5cf6'))
            elements.append(recent_table)
        else:
            elements.append(Paragraph("No signals in the selected period.", styles['CustomNormal']))
    
    # 푸터
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        "Generated by GVIC Engine v2.0.0 - AI-Powered Signal Analysis Platform",
        styles['CustomSmall']
    ))
    
    # PDF 빌드
    doc.build(elements)
    
    logger.info(f"Dashboard report generated for period: {range_label}")
    
    return FileResponse(
        temp_file.name,
        media_type="application/pdf",
        filename=f"gvic_dashboard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

@router.post("/assets")
async def generate_asset_report(
    request: AssetReportRequest,
    current_user: dict = Depends(get_current_user_simple)
):
    """
    자산 포트폴리오 PDF 리포트 생성
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
    from reportlab.lib.units import cm
    
    from server import db
    
    # 자산 조회
    query = {}
    if request.asset_ids:
        query["asset_id"] = {"$in": request.asset_ids}
    if request.category != "all":
        query["classification"] = request.category
    
    assets = await db.gvic_assets.find(
        query,
        {"_id": 0}
    ).sort("creation_date", -1).limit(request.limit).to_list(request.limit)
    
    # PDF 생성
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(
        temp_file.name,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    styles = create_pdf_styles()
    elements = []
    
    # 제목
    elements.append(Paragraph("GVIC Asset Portfolio Report", styles['CustomTitle']))
    elements.append(Paragraph(
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        styles['CustomSmall']
    ))
    elements.append(Spacer(1, 30))
    
    # 포트폴리오 요약
    elements.append(Paragraph("1. Portfolio Summary", styles['CustomHeading']))
    
    total_value = sum(
        asset.get("value_analysis", {}).get("value_score", 0) * 100 
        for asset in assets
    )
    
    summary_data = [
        ["Metric", "Value"],
        ["Total Assets", str(len(assets))],
        ["Total Estimated Value", f"${total_value:,.0f}"],
        ["Average Value", f"${total_value/len(assets):,.0f}" if assets else "$0"],
        ["Category Filter", request.category]
    ]
    
    summary_table = Table(summary_data, colWidths=[8*cm, 8*cm])
    summary_table.setStyle(create_table_style('#f59e0b'))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # 자산 목록
    elements.append(Paragraph("2. Asset List", styles['CustomHeading']))
    
    if assets:
        asset_data = [["Asset ID", "Classification", "Value Score", "Novelty"]]
        for asset in assets[:20]:  # 최대 20개
            value_analysis = asset.get("value_analysis", {})
            asset_data.append([
                asset.get("asset_id", "-")[:15],
                asset.get("classification", "-"),
                f"{value_analysis.get('value_score', 0)*100:.0f}%",
                f"{value_analysis.get('novelty_score', 0)*100:.0f}%"
            ])
        
        asset_table = Table(asset_data, colWidths=[5*cm, 4*cm, 4*cm, 3*cm])
        asset_table.setStyle(create_table_style('#10b981'))
        elements.append(asset_table)
    else:
        elements.append(Paragraph("No assets found.", styles['CustomNormal']))
    
    # 푸터
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        "Generated by GVIC Engine v2.0.0 - AI-Powered Signal Analysis Platform",
        styles['CustomSmall']
    ))
    
    # PDF 빌드
    doc.build(elements)
    
    logger.info(f"Asset report generated: {len(assets)} assets")
    
    return FileResponse(
        temp_file.name,
        media_type="application/pdf",
        filename=f"gvic_asset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

# ==================== Quick Report (GET) ====================

@router.get("/quick/signal/{signal_id}")
async def quick_signal_report(
    signal_id: str,
    current_user: dict = Depends(get_current_user_simple)
):
    """간편 시그널 리포트 생성 (GET)"""
    request = SignalReportRequest(signal_id=signal_id)
    return await generate_signal_report(request, current_user)

@router.get("/quick/dashboard")
async def quick_dashboard_report(
    date_range: str = "7d",
    current_user: dict = Depends(get_current_user_simple)
):
    """간편 대시보드 리포트 생성 (GET)"""
    request = DashboardReportRequest(date_range=date_range)
    return await generate_dashboard_report(request, current_user)
