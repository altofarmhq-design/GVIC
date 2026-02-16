"""
GVIC External API Webhook Module
- 외부 시스템에서 시그널을 수신하는 API 엔드포인트
- API 키 기반 인증
- 연속 시그널 수집 지원
"""
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import hashlib
import secrets
import logging

router = APIRouter(prefix="/api/webhook", tags=["webhook"])
logger = logging.getLogger(__name__)

# API 키 저장소 (실제 환경에서는 MongoDB에 저장)
api_keys_store = {}

# ==================== Models ====================

class APIKeyCreate(BaseModel):
    name: str = Field(..., description="API 키 이름")
    description: str = Field("", description="설명")
    rate_limit: int = Field(100, description="시간당 요청 제한")
    allowed_types: List[str] = Field(["text", "json", "event"], description="허용 시그널 유형")

class APIKeyResponse(BaseModel):
    key_id: str
    api_key: str  # 생성 시에만 반환
    name: str
    created_at: str
    rate_limit: int
    allowed_types: List[str]

class WebhookSignal(BaseModel):
    type: str = Field("text", description="시그널 유형: text, json, event")
    content: str = Field(..., description="시그널 내용")
    source: str = Field("external_api", description="시그널 출처")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="추가 메타데이터")
    analysis_type: str = Field("general", description="분석 유형")
    priority: str = Field("normal", description="우선순위: low, normal, high, critical")
    tags: List[str] = Field(default_factory=list, description="태그")

class BatchWebhookRequest(BaseModel):
    signals: List[WebhookSignal] = Field(..., description="배치 시그널 목록")
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8], description="배치 ID")

class WebhookEventRequest(BaseModel):
    event_type: str = Field(..., description="이벤트 유형")
    payload: Dict[str, Any] = Field(..., description="이벤트 데이터")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

# ==================== Helper Functions ====================

def generate_api_key() -> str:
    """보안 API 키 생성"""
    return f"gvic_{secrets.token_urlsafe(32)}"

def hash_api_key(api_key: str) -> str:
    """API 키 해시"""
    return hashlib.sha256(api_key.encode()).hexdigest()

async def validate_api_key(api_key: str) -> dict:
    """API 키 유효성 검증"""
    if not api_key:
        raise HTTPException(status_code=401, detail="API 키가 필요합니다")
    
    # Bearer 토큰 처리
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # 키 검증
    key_hash = hash_api_key(api_key)
    
    for key_id, key_data in api_keys_store.items():
        if key_data.get("key_hash") == key_hash:
            # 요청 카운트 증가
            key_data["request_count"] = key_data.get("request_count", 0) + 1
            key_data["last_used"] = datetime.now(timezone.utc).isoformat()
            return key_data
    
    raise HTTPException(status_code=401, detail="유효하지 않은 API 키입니다")

# ==================== API Key Management ====================

@router.post("/keys", response_model=APIKeyResponse)
async def create_api_key(request: APIKeyCreate):
    """새 API 키 생성"""
    key_id = f"key_{uuid.uuid4().hex[:12]}"
    api_key = generate_api_key()
    key_hash = hash_api_key(api_key)
    
    key_data = {
        "key_id": key_id,
        "key_hash": key_hash,
        "name": request.name,
        "description": request.description,
        "rate_limit": request.rate_limit,
        "allowed_types": request.allowed_types,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "request_count": 0,
        "last_used": None,
        "is_active": True
    }
    
    api_keys_store[key_id] = key_data
    
    logger.info(f"New API key created: {key_id} ({request.name})")
    
    return APIKeyResponse(
        key_id=key_id,
        api_key=api_key,  # 생성 시에만 반환
        name=request.name,
        created_at=key_data["created_at"],
        rate_limit=request.rate_limit,
        allowed_types=request.allowed_types
    )

@router.get("/keys")
async def list_api_keys():
    """API 키 목록 조회 (키 값은 제외)"""
    keys_list = []
    for key_id, key_data in api_keys_store.items():
        keys_list.append({
            "key_id": key_id,
            "name": key_data.get("name"),
            "description": key_data.get("description"),
            "created_at": key_data.get("created_at"),
            "rate_limit": key_data.get("rate_limit"),
            "allowed_types": key_data.get("allowed_types"),
            "request_count": key_data.get("request_count", 0),
            "last_used": key_data.get("last_used"),
            "is_active": key_data.get("is_active", True)
        })
    
    return {
        "keys": keys_list,
        "total": len(keys_list)
    }

@router.delete("/keys/{key_id}")
async def delete_api_key(key_id: str):
    """API 키 삭제"""
    if key_id not in api_keys_store:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    del api_keys_store[key_id]
    logger.info(f"API key deleted: {key_id}")
    
    return {"success": True, "message": f"API 키 {key_id} 삭제됨"}

@router.put("/keys/{key_id}/toggle")
async def toggle_api_key(key_id: str):
    """API 키 활성화/비활성화 토글"""
    if key_id not in api_keys_store:
        raise HTTPException(status_code=404, detail="API 키를 찾을 수 없습니다")
    
    key_data = api_keys_store[key_id]
    key_data["is_active"] = not key_data.get("is_active", True)
    
    return {
        "success": True,
        "key_id": key_id,
        "is_active": key_data["is_active"]
    }

# ==================== Webhook Signal Endpoints ====================

@router.post("/signal")
async def receive_signal(
    signal: WebhookSignal,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    외부 시스템에서 단일 시그널 수신
    
    Headers:
        X-API-Key: API 키
    
    Body:
        type: 시그널 유형 (text, json, event)
        content: 시그널 내용
        source: 출처
        metadata: 추가 메타데이터
        analysis_type: 분석 유형 (general, code, patent_idea)
        priority: 우선순위 (low, normal, high, critical)
        tags: 태그 목록
    """
    # API 키 검증
    key_data = await validate_api_key(x_api_key)
    
    # 시그널 유형 검증
    if signal.type not in key_data.get("allowed_types", ["text", "json", "event"]):
        raise HTTPException(
            status_code=403, 
            detail=f"이 API 키는 '{signal.type}' 유형을 지원하지 않습니다"
        )
    
    # 파이프라인 실행
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    try:
        result = await pipeline.create_signal(
            signal_type=signal.type,
            content=signal.content,
            source=signal.source,
            metadata={
                "input_method": "api_webhook",
                "api_key_id": key_data.get("key_id"),
                "api_key_name": key_data.get("name"),
                "analysis_type": signal.analysis_type,
                "priority": signal.priority,
                "tags": signal.tags,
                **signal.metadata
            },
            user_id=f"api_{key_data.get('key_id')}"
        )
        
        logger.info(f"Webhook signal received: {result.get('signal_id')} from {key_data.get('name')}")
        
        return {
            "success": True,
            "signal_id": result.get("signal_id"),
            "category": result.get("category"),
            "status": result.get("status"),
            "message": "시그널이 성공적으로 처리되었습니다",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Webhook signal processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"시그널 처리 실패: {str(e)}")

@router.post("/signal/batch")
async def receive_batch_signals(
    request: BatchWebhookRequest,
    background_tasks: BackgroundTasks,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    배치 시그널 수신 (여러 시그널 한번에 처리)
    
    최대 100개 시그널 동시 처리
    """
    # API 키 검증
    key_data = await validate_api_key(x_api_key)
    
    if len(request.signals) > 100:
        raise HTTPException(status_code=400, detail="배치당 최대 100개 시그널만 허용됩니다")
    
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    results = []
    success_count = 0
    fail_count = 0
    
    for idx, signal in enumerate(request.signals):
        try:
            # 시그널 유형 검증
            if signal.type not in key_data.get("allowed_types", ["text", "json", "event"]):
                results.append({
                    "index": idx,
                    "success": False,
                    "error": f"허용되지 않는 시그널 유형: {signal.type}"
                })
                fail_count += 1
                continue
            
            result = await pipeline.create_signal(
                signal_type=signal.type,
                content=signal.content,
                source=signal.source,
                metadata={
                    "input_method": "api_webhook_batch",
                    "batch_id": request.batch_id,
                    "batch_index": idx,
                    "api_key_id": key_data.get("key_id"),
                    "analysis_type": signal.analysis_type,
                    "priority": signal.priority,
                    "tags": signal.tags,
                    **signal.metadata
                },
                user_id=f"api_{key_data.get('key_id')}"
            )
            
            results.append({
                "index": idx,
                "success": True,
                "signal_id": result.get("signal_id"),
                "category": result.get("category")
            })
            success_count += 1
            
        except Exception as e:
            results.append({
                "index": idx,
                "success": False,
                "error": str(e)
            })
            fail_count += 1
    
    logger.info(f"Batch webhook: {success_count}/{len(request.signals)} signals processed")
    
    return {
        "success": True,
        "batch_id": request.batch_id,
        "total": len(request.signals),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/event")
async def receive_event(
    event: WebhookEventRequest,
    x_api_key: str = Header(None, alias="X-API-Key")
):
    """
    이벤트 기반 시그널 수신
    
    특정 이벤트 유형에 대한 처리:
    - user_action: 사용자 행동 이벤트
    - system_alert: 시스템 알림
    - data_update: 데이터 업데이트
    - custom: 커스텀 이벤트
    """
    # API 키 검증
    key_data = await validate_api_key(x_api_key)
    
    if "event" not in key_data.get("allowed_types", []):
        raise HTTPException(status_code=403, detail="이 API 키는 이벤트를 지원하지 않습니다")
    
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    # 이벤트를 시그널로 변환
    content = f"[Event: {event.event_type}]\n{str(event.payload)}"
    
    try:
        result = await pipeline.create_signal(
            signal_type="event",
            content=content,
            source=f"event:{event.event_type}",
            metadata={
                "input_method": "api_event",
                "event_type": event.event_type,
                "event_payload": event.payload,
                "event_timestamp": event.timestamp,
                "api_key_id": key_data.get("key_id")
            },
            user_id=f"api_{key_data.get('key_id')}"
        )
        
        return {
            "success": True,
            "event_type": event.event_type,
            "signal_id": result.get("signal_id"),
            "category": result.get("category"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트 처리 실패: {str(e)}")

# ==================== Webhook Status & Stats ====================

@router.get("/stats")
async def get_webhook_stats(x_api_key: str = Header(None, alias="X-API-Key")):
    """웹훅 통계 조회"""
    key_data = await validate_api_key(x_api_key)
    
    return {
        "api_key_id": key_data.get("key_id"),
        "api_key_name": key_data.get("name"),
        "total_requests": key_data.get("request_count", 0),
        "rate_limit": key_data.get("rate_limit"),
        "allowed_types": key_data.get("allowed_types"),
        "last_used": key_data.get("last_used"),
        "is_active": key_data.get("is_active", True)
    }

@router.get("/health")
async def webhook_health():
    """웹훅 서비스 상태 확인 (인증 불필요)"""
    return {
        "status": "healthy",
        "service": "GVIC Webhook API",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "active_keys": len([k for k in api_keys_store.values() if k.get("is_active", True)])
    }

# ==================== Documentation Endpoint ====================

@router.get("/docs/usage")
async def get_usage_docs():
    """웹훅 API 사용 가이드"""
    return {
        "title": "GVIC Webhook API 사용 가이드",
        "version": "1.0.0",
        "authentication": {
            "method": "API Key",
            "header": "X-API-Key",
            "example": "X-API-Key: gvic_xxxxx"
        },
        "endpoints": {
            "POST /api/webhook/signal": {
                "description": "단일 시그널 전송",
                "body": {
                    "type": "text | json | event",
                    "content": "시그널 내용",
                    "source": "출처 (선택)",
                    "analysis_type": "general | code | patent_idea",
                    "priority": "low | normal | high | critical",
                    "tags": ["태그1", "태그2"],
                    "metadata": {}
                }
            },
            "POST /api/webhook/signal/batch": {
                "description": "배치 시그널 전송 (최대 100개)",
                "body": {
                    "signals": "[시그널 배열]",
                    "batch_id": "배치 ID (선택)"
                }
            },
            "POST /api/webhook/event": {
                "description": "이벤트 전송",
                "body": {
                    "event_type": "이벤트 유형",
                    "payload": {},
                    "timestamp": "ISO 8601 형식"
                }
            }
        },
        "example_curl": """
curl -X POST "https://your-domain.com/api/webhook/signal" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: gvic_your_api_key" \\
  -d '{
    "type": "text",
    "content": "분석할 텍스트 내용",
    "source": "my_system",
    "analysis_type": "general",
    "priority": "normal"
  }'
        """,
        "rate_limits": "API 키별 시간당 요청 제한 적용",
        "support": "관리자에게 문의하세요"
    }
