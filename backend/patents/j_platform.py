"""
J: PLATFORM - 입력 특허 모듈
시그널 유입 채널 관리 (텍스트, 파일, URL, API)
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging

router = APIRouter(prefix="/api/patent/j", tags=["J:PLATFORM"])
logger = logging.getLogger(__name__)

class InputChannel(BaseModel):
    """입력 채널 정의"""
    channel_id: str
    channel_type: str  # text, file, url, api
    name: str
    status: str  # active, inactive, pending
    config: Dict[str, Any] = {}

class SignalInput(BaseModel):
    """시그널 입력"""
    content: str
    channel: str = "text"
    metadata: Dict[str, Any] = {}

# ==================== 입력 채널 관리 ====================

@router.get("/channels")
async def get_input_channels():
    """활성화된 입력 채널 목록 조회"""
    channels = [
        {"channel_id": "text", "channel_type": "text", "name": "텍스트 입력", "status": "active", "description": "직접 텍스트 입력"},
        {"channel_id": "file", "channel_type": "file", "name": "파일 업로드", "status": "active", "description": "Excel, CSV, PDF, 이미지 등"},
        {"channel_id": "url", "channel_type": "url", "name": "URL 크롤링", "status": "active", "description": "웹페이지 텍스트 추출"},
        {"channel_id": "api", "channel_type": "api", "name": "API 연동", "status": "active", "description": "외부 시스템 웹훅"},
        {"channel_id": "ocr", "channel_type": "ocr", "name": "이미지 OCR", "status": "active", "description": "이미지에서 텍스트 추출"}
    ]
    return {"success": True, "channels": channels}

@router.get("/stats")
async def get_input_stats():
    """입력 채널별 통계"""
    from server import db
    
    # 채널별 시그널 수 집계
    pipeline = [
        {"$group": {
            "_id": "$metadata.input_method",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.pipeline_signals.aggregate(pipeline).to_list(100)
    
    stats = {r["_id"]: r["count"] for r in results if r["_id"]}
    
    return {
        "success": True,
        "stats": stats,
        "total": sum(stats.values())
    }

@router.post("/validate")
async def validate_input(request: SignalInput):
    """입력 데이터 유효성 검증"""
    errors = []
    warnings = []
    
    # 내용 검증
    if not request.content.strip():
        errors.append("내용이 비어있습니다")
    elif len(request.content) < 10:
        warnings.append("내용이 너무 짧습니다 (10자 미만)")
    elif len(request.content) > 100000:
        errors.append("내용이 너무 깁니다 (100,000자 초과)")
    
    # 채널 검증
    valid_channels = ["text", "file", "url", "api", "ocr"]
    if request.channel not in valid_channels:
        errors.append(f"유효하지 않은 채널: {request.channel}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "content_length": len(request.content),
        "channel": request.channel
    }
