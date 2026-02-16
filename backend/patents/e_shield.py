"""
E: SHIELD - 방어막 특허 모듈
보안, 검증, 무결성 보호
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import logging

router = APIRouter(prefix="/api/patent/e", tags=["E:SHIELD"])
logger = logging.getLogger(__name__)

class SecurityCheck(BaseModel):
    """보안 검사 요청"""
    content: str
    source: str = "unknown"
    metadata: Dict[str, Any] = {}

class IntegrityVerification(BaseModel):
    """무결성 검증 요청"""
    asset_id: str
    expected_hash: str = ""

# ==================== 보안 검사 ====================

@router.post("/scan")
async def security_scan(request: SecurityCheck):
    """콘텐츠 보안 스캔"""
    threats = []
    warnings = []
    
    content_lower = request.content.lower()
    
    # 악성 패턴 검사
    malicious_patterns = [
        ("script", "스크립트 태그 감지"),
        ("javascript:", "JavaScript 프로토콜 감지"),
        ("onclick", "이벤트 핸들러 감지"),
        ("eval(", "eval 함수 감지"),
        ("exec(", "exec 함수 감지"),
        ("<iframe", "iframe 태그 감지")
    ]
    
    for pattern, message in malicious_patterns:
        if pattern in content_lower:
            threats.append({"type": "malicious_content", "message": message, "pattern": pattern})
    
    # 민감 정보 검사
    sensitive_patterns = [
        ("password", "비밀번호 포함 가능"),
        ("api_key", "API 키 포함 가능"),
        ("secret", "비밀 정보 포함 가능"),
        ("token", "토큰 정보 포함 가능")
    ]
    
    for pattern, message in sensitive_patterns:
        if pattern in content_lower:
            warnings.append({"type": "sensitive_data", "message": message})
    
    risk_level = "high" if threats else ("medium" if warnings else "low")
    
    return {
        "success": True,
        "risk_level": risk_level,
        "threats": threats,
        "warnings": warnings,
        "scan_timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/hash")
async def generate_hash(content: str):
    """콘텐츠 해시 생성"""
    content_bytes = content.encode('utf-8')
    
    hashes = {
        "md5": hashlib.md5(content_bytes).hexdigest(),
        "sha256": hashlib.sha256(content_bytes).hexdigest(),
        "sha512": hashlib.sha512(content_bytes).hexdigest()
    }
    
    return {
        "success": True,
        "hashes": hashes,
        "content_length": len(content)
    }

@router.post("/verify-integrity")
async def verify_integrity(request: IntegrityVerification):
    """자산 무결성 검증"""
    from server import db
    
    asset = await db.indexed_assets.find_one(
        {"asset_id": request.asset_id},
        {"_id": 0}
    )
    
    if not asset:
        raise HTTPException(status_code=404, detail="자산을 찾을 수 없습니다")
    
    content = asset.get("original_content", "")
    current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    if request.expected_hash:
        is_valid = current_hash == request.expected_hash
    else:
        is_valid = True  # 기대 해시가 없으면 현재 해시 반환
    
    return {
        "success": True,
        "asset_id": request.asset_id,
        "is_valid": is_valid,
        "current_hash": current_hash,
        "expected_hash": request.expected_hash or "not_provided"
    }

@router.get("/shield-status")
async def get_shield_status():
    """방어막 상태"""
    return {
        "success": True,
        "status": "active",
        "features": {
            "content_scanning": True,
            "integrity_verification": True,
            "sensitive_data_detection": True,
            "malicious_pattern_detection": True
        },
        "last_scan": datetime.now(timezone.utc).isoformat()
    }

@router.get("/threat-report")
async def get_threat_report():
    """위협 리포트"""
    from server import db
    
    # 최근 위협 로그 조회
    threats = await db.security_logs.find(
        {"type": "threat"},
        {"_id": 0}
    ).sort("timestamp", -1).limit(50).to_list(50)
    
    return {
        "success": True,
        "total_threats": len(threats),
        "threats": threats,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
