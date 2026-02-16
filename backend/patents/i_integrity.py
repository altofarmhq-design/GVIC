"""
I: INTEGRITY - 무결성 특허 모듈
시스템 무결성 및 감사 관리
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import hashlib
import logging

router = APIRouter(prefix="/api/patent/i", tags=["I:INTEGRITY"])
logger = logging.getLogger(__name__)

class AuditLog(BaseModel):
    """감사 로그"""
    action: str
    entity_type: str
    entity_id: str
    user_id: str
    details: Dict[str, Any] = {}

class IntegrityCheck(BaseModel):
    """무결성 검사 요청"""
    entity_type: str  # asset, signal, module, transaction
    entity_id: str

# ==================== 감사 로그 ====================

@router.post("/audit-log")
async def create_audit_log(log: AuditLog):
    """감사 로그 기록"""
    from server import db
    
    audit_record = {
        "audit_id": f"AUD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
        "action": log.action,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "user_id": log.user_id,
        "details": log.details,
        "ip_address": log.details.get("ip_address", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    await db.audit_logs.insert_one(audit_record)
    
    return {"success": True, "audit_id": audit_record["audit_id"]}

@router.get("/audit-logs")
async def get_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """감사 로그 조회"""
    from server import db
    
    query = {}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if user_id:
        query["user_id"] = user_id
    if action:
        query["action"] = action
    
    logs = await db.audit_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
    
    total = await db.audit_logs.count_documents(query)
    
    return {
        "success": True,
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }

# ==================== 무결성 검사 ====================

@router.post("/verify")
async def verify_integrity(request: IntegrityCheck):
    """엔티티 무결성 검증"""
    from server import db
    
    collection_map = {
        "asset": "indexed_assets",
        "signal": "pipeline_signals",
        "module": "asset_modules",
        "transaction": "ledger"
    }
    
    if request.entity_type not in collection_map:
        raise HTTPException(status_code=400, detail=f"유효하지 않은 엔티티 유형: {request.entity_type}")
    
    collection = db[collection_map[request.entity_type]]
    id_field = f"{request.entity_type}_id"
    
    entity = await collection.find_one({id_field: request.entity_id}, {"_id": 0})
    
    if not entity:
        return {
            "success": True,
            "valid": False,
            "entity_type": request.entity_type,
            "entity_id": request.entity_id,
            "error": "엔티티를 찾을 수 없습니다"
        }
    
    # 무결성 검사
    issues = []
    
    # 필수 필드 검사
    required_fields = {
        "asset": ["asset_id", "content", "created_at"],
        "signal": ["signal_id", "content", "created_at"],
        "module": ["module_id", "name", "created_at"],
        "transaction": ["transaction_id", "amount", "timestamp"]
    }
    
    for field in required_fields.get(request.entity_type, []):
        if field not in entity or entity[field] is None:
            issues.append({"type": "missing_field", "field": field})
    
    # 해시 무결성 검사 (저장된 해시가 있는 경우)
    if "content_hash" in entity and "content" in entity:
        current_hash = hashlib.sha256(str(entity["content"]).encode()).hexdigest()
        if current_hash != entity["content_hash"]:
            issues.append({"type": "hash_mismatch", "expected": entity["content_hash"], "actual": current_hash})
    
    return {
        "success": True,
        "valid": len(issues) == 0,
        "entity_type": request.entity_type,
        "entity_id": request.entity_id,
        "issues": issues,
        "verified_at": datetime.now(timezone.utc).isoformat()
    }

@router.post("/system-check")
async def run_system_integrity_check():
    """시스템 전체 무결성 검사"""
    from server import db
    
    results = {
        "database_connection": True,
        "collections": {},
        "data_integrity": {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    # 컬렉션별 검사
    collections_to_check = [
        ("pipeline_signals", "signal_id"),
        ("indexed_assets", "asset_id"),
        ("asset_modules", "module_id"),
        ("ledger", "transaction_id"),
        ("users", "email")
    ]
    
    for collection_name, id_field in collections_to_check:
        try:
            collection = db[collection_name]
            count = await collection.count_documents({})
            
            # 중복 ID 검사
            dup_pipeline = [
                {"$group": {"_id": f"${id_field}", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gt": 1}}}
            ]
            duplicates = await collection.aggregate(dup_pipeline).to_list(100)
            
            results["collections"][collection_name] = {
                "count": count,
                "duplicates": len(duplicates),
                "status": "healthy" if len(duplicates) == 0 else "warning"
            }
        except Exception as e:
            results["collections"][collection_name] = {
                "status": "error",
                "error": str(e)
            }
    
    # 블록체인 무결성 검사
    try:
        from patents.d_ledger import verify_blockchain
        blockchain_result = await verify_blockchain()
        results["data_integrity"]["blockchain"] = {
            "valid": blockchain_result.get("valid", False),
            "total_blocks": blockchain_result.get("total_blocks", 0)
        }
    except:
        results["data_integrity"]["blockchain"] = {"status": "check_failed"}
    
    # 전체 상태 결정
    all_healthy = all(
        c.get("status") == "healthy" 
        for c in results["collections"].values()
    )
    results["overall_status"] = "healthy" if all_healthy else "needs_attention"
    
    return {"success": True, "results": results}

# ==================== 데이터 복구 ====================

@router.post("/repair/{entity_type}/{entity_id}")
async def repair_entity(entity_type: str, entity_id: str, repair_action: str = "recalculate_hash"):
    """엔티티 복구 시도"""
    from server import db
    
    collection_map = {
        "asset": "indexed_assets",
        "signal": "pipeline_signals",
        "module": "asset_modules"
    }
    
    if entity_type not in collection_map:
        raise HTTPException(status_code=400, detail="유효하지 않은 엔티티 유형")
    
    collection = db[collection_map[entity_type]]
    id_field = f"{entity_type}_id"
    
    entity = await collection.find_one({id_field: entity_id}, {"_id": 0})
    
    if not entity:
        raise HTTPException(status_code=404, detail="엔티티를 찾을 수 없습니다")
    
    repairs = []
    
    if repair_action == "recalculate_hash" and "content" in entity:
        new_hash = hashlib.sha256(str(entity["content"]).encode()).hexdigest()
        await collection.update_one(
            {id_field: entity_id},
            {"$set": {"content_hash": new_hash, "hash_updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        repairs.append({"action": "hash_recalculated", "new_hash": new_hash})
    
    # 감사 로그
    await create_audit_log(AuditLog(
        action="repair",
        entity_type=entity_type,
        entity_id=entity_id,
        user_id="system",
        details={"repair_action": repair_action, "repairs": repairs}
    ))
    
    return {
        "success": True,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "repairs": repairs
    }

# ==================== 통계 및 보고 ====================

@router.get("/stats")
async def get_integrity_stats():
    """무결성 통계"""
    from server import db
    
    # 감사 로그 통계
    total_audits = await db.audit_logs.count_documents({})
    
    # 액션별 통계
    action_pipeline = [
        {"$group": {"_id": "$action", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    action_stats = await db.audit_logs.aggregate(action_pipeline).to_list(20)
    
    # 최근 24시간 활동
    from datetime import timedelta
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    recent_audits = await db.audit_logs.count_documents({"timestamp": {"$gte": yesterday}})
    
    return {
        "success": True,
        "stats": {
            "total_audit_logs": total_audits,
            "recent_24h": recent_audits,
            "by_action": {a["_id"]: a["count"] for a in action_stats}
        }
    }

@router.get("/health")
async def get_system_health():
    """시스템 헬스 체크"""
    from server import db
    
    try:
        # DB 연결 테스트
        await db.command("ping")
        db_status = "connected"
    except:
        db_status = "disconnected"
    
    return {
        "success": True,
        "health": {
            "database": db_status,
            "integrity_module": "active",
            "audit_logging": "active",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
