"""
GVIC External Integration Connector
- Zapier, n8n, Make 등 외부 자동화 도구 연동을 위한 내부 커넥터
- 실제 연결 없이 테스트 및 시뮬레이션 가능
"""
from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import asyncio
import logging

router = APIRouter(prefix="/api/connector", tags=["connector"])
logger = logging.getLogger(__name__)

# ==================== 연동 설정 저장소 ====================

integration_configs = {
    "zapier": {
        "id": "zapier",
        "name": "Zapier",
        "description": "5,000+ 앱과 자동화 연동",
        "icon": "⚡",
        "status": "ready",  # ready, connected, error
        "webhook_url": None,
        "triggers": [
            {"id": "new_signal", "name": "새 시그널 수신", "description": "외부에서 새 시그널이 들어올 때"},
            {"id": "signal_analyzed", "name": "시그널 분석 완료", "description": "AI 분석이 완료되었을 때"},
            {"id": "asset_created", "name": "자산 생성됨", "description": "새 자산이 자산화되었을 때"}
        ],
        "actions": [
            {"id": "send_signal", "name": "시그널 전송", "description": "GVIC로 시그널 전송"},
            {"id": "get_analysis", "name": "분석 결과 조회", "description": "시그널 분석 결과 가져오기"},
            {"id": "search_assets", "name": "자산 검색", "description": "자산화된 시그널 검색"}
        ],
        "setup_guide": """
## Zapier 연동 설정

1. Zapier에서 새 Zap 생성
2. Trigger로 "Webhooks by Zapier" 선택
3. GVIC API 키를 X-API-Key 헤더에 추가
4. Webhook URL: {base_url}/api/webhook/signal
5. Method: POST
6. Data: {"type": "text", "content": "{{data}}"}
        """
    },
    "n8n": {
        "id": "n8n",
        "name": "n8n",
        "description": "오픈소스 워크플로우 자동화",
        "icon": "🔄",
        "status": "ready",
        "webhook_url": None,
        "triggers": [
            {"id": "webhook_receive", "name": "웹훅 수신", "description": "GVIC에서 이벤트 수신"},
            {"id": "schedule", "name": "스케줄", "description": "정해진 시간에 실행"}
        ],
        "actions": [
            {"id": "http_request", "name": "HTTP 요청", "description": "GVIC API 호출"},
            {"id": "batch_process", "name": "배치 처리", "description": "여러 시그널 한번에 처리"}
        ],
        "setup_guide": """
## n8n 연동 설정

1. n8n 워크플로우에서 "HTTP Request" 노드 추가
2. Method: POST
3. URL: {base_url}/api/webhook/signal
4. Headers: X-API-Key: {your_api_key}
5. Body: JSON 형식으로 시그널 데이터 전송
        """
    },
    "make": {
        "id": "make",
        "name": "Make (Integromat)",
        "description": "시각적 자동화 플랫폼",
        "icon": "🎨",
        "status": "ready",
        "webhook_url": None,
        "triggers": [
            {"id": "watch_webhook", "name": "웹훅 감시", "description": "웹훅 이벤트 감시"}
        ],
        "actions": [
            {"id": "make_request", "name": "API 요청", "description": "GVIC API 호출"}
        ],
        "setup_guide": """
## Make 연동 설정

1. Make 시나리오에서 "HTTP" 모듈 추가
2. "Make a request" 선택
3. URL: {base_url}/api/webhook/signal
4. Method: POST
5. Headers에 X-API-Key 추가
        """
    },
    "custom": {
        "id": "custom",
        "name": "커스텀 연동",
        "description": "직접 구현한 시스템과 연동",
        "icon": "🔧",
        "status": "ready",
        "webhook_url": None,
        "triggers": [],
        "actions": [],
        "setup_guide": """
## 커스텀 시스템 연동

### API 엔드포인트
- 단일 시그널: POST /api/webhook/signal
- 배치 시그널: POST /api/webhook/signal/batch
- 이벤트: POST /api/webhook/event

### 인증
X-API-Key: {your_api_key}

### 샘플 코드 (Python)
```python
import requests

API_URL = "{base_url}/api/webhook/signal"
API_KEY = "your_api_key"

response = requests.post(
    API_URL,
    headers={"X-API-Key": API_KEY},
    json={
        "type": "text",
        "content": "분석할 내용",
        "analysis_type": "general"
    }
)
print(response.json())
```
        """
    }
}

# 이벤트 로그 저장소 (시뮬레이션용)
event_log = []

# 스케줄된 작업 저장소
scheduled_jobs = []

# ==================== Models ====================

class IntegrationSetup(BaseModel):
    integration_id: str
    webhook_url: Optional[str] = None
    api_key_id: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

class SimulateSignalRequest(BaseModel):
    source: str = Field("manual", description="시뮬레이션 소스")
    signal_type: str = Field("text", description="시그널 유형")
    content: str = Field(..., description="시그널 내용")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScheduledJobCreate(BaseModel):
    name: str
    integration_id: str
    action: str
    schedule: str  # cron 형식 또는 interval (예: "every_5min", "every_hour", "daily_9am")
    payload: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

class OutboundWebhookConfig(BaseModel):
    url: str
    events: List[str]  # ["signal_created", "signal_analyzed", "asset_created"]
    headers: Dict[str, str] = Field(default_factory=dict)
    enabled: bool = True

# 아웃바운드 웹훅 설정 저장소
outbound_webhooks = []

# ==================== Integration Configs ====================

@router.get("/integrations")
async def list_integrations():
    """사용 가능한 연동 목록"""
    return {
        "integrations": [
            {
                "id": cfg["id"],
                "name": cfg["name"],
                "description": cfg["description"],
                "icon": cfg["icon"],
                "status": cfg["status"],
                "triggers_count": len(cfg.get("triggers", [])),
                "actions_count": len(cfg.get("actions", []))
            }
            for cfg in integration_configs.values()
        ]
    }

@router.get("/integrations/{integration_id}")
async def get_integration_detail(integration_id: str):
    """연동 상세 정보"""
    if integration_id not in integration_configs:
        raise HTTPException(status_code=404, detail="연동을 찾을 수 없습니다")
    
    config = integration_configs[integration_id]
    
    # base_url 치환
    from server import app
    base_url = "https://your-domain.com"  # 실제 배포 시 변경
    
    setup_guide = config.get("setup_guide", "").replace("{base_url}", base_url)
    
    return {
        **config,
        "setup_guide": setup_guide
    }

@router.post("/integrations/{integration_id}/setup")
async def setup_integration(integration_id: str, setup: IntegrationSetup):
    """연동 설정 저장"""
    if integration_id not in integration_configs:
        raise HTTPException(status_code=404, detail="연동을 찾을 수 없습니다")
    
    config = integration_configs[integration_id]
    
    if setup.webhook_url:
        config["webhook_url"] = setup.webhook_url
    
    config["status"] = "connected"
    config["api_key_id"] = setup.api_key_id
    config["custom_config"] = setup.config
    config["connected_at"] = datetime.now(timezone.utc).isoformat()
    
    logger.info(f"Integration setup: {integration_id}")
    
    return {
        "success": True,
        "integration_id": integration_id,
        "status": "connected"
    }

@router.post("/integrations/{integration_id}/disconnect")
async def disconnect_integration(integration_id: str):
    """연동 해제"""
    if integration_id not in integration_configs:
        raise HTTPException(status_code=404, detail="연동을 찾을 수 없습니다")
    
    config = integration_configs[integration_id]
    config["status"] = "ready"
    config["webhook_url"] = None
    config["api_key_id"] = None
    
    return {"success": True, "status": "disconnected"}

# ==================== 시뮬레이션 ====================

@router.post("/simulate/signal")
async def simulate_signal(request: SimulateSignalRequest):
    """
    시그널 수신 시뮬레이션
    - 실제 외부 연동 없이 시그널 처리 테스트
    """
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    try:
        result = await pipeline.create_signal(
            signal_type=request.signal_type,
            content=request.content,
            source=f"simulation:{request.source}",
            metadata={
                "input_method": "simulation",
                "simulation_source": request.source,
                **request.metadata
            },
            user_id="simulation_user"
        )
        
        # 이벤트 로그 기록
        event_log.append({
            "type": "signal_simulated",
            "source": request.source,
            "signal_id": result.get("signal_id"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        return {
            "success": True,
            "simulated": True,
            "signal_id": result.get("signal_id"),
            "category": result.get("category"),
            "message": "시뮬레이션 시그널이 처리되었습니다"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시뮬레이션 실패: {str(e)}")

@router.post("/simulate/batch")
async def simulate_batch_signals(count: int = 5, source: str = "batch_test"):
    """
    배치 시그널 시뮬레이션
    - 여러 시그널 동시 처리 테스트
    """
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    sample_contents = [
        "인공지능 기반 자동화 시스템 개발 아이디어",
        "블록체인 활용 데이터 무결성 검증 방안",
        "IoT 센서 데이터 실시간 분석 파이프라인",
        "머신러닝 모델 자동 최적화 알고리즘",
        "클라우드 네이티브 마이크로서비스 아키텍처",
        "자연어 처리 기반 문서 자동 분류 시스템",
        "컴퓨터 비전 응용 품질 검사 솔루션",
        "예측 분석 기반 재고 관리 최적화",
        "실시간 이상 탐지 알고리즘 개발",
        "자동화된 코드 리뷰 시스템 구축"
    ]
    
    results = []
    
    for i in range(min(count, len(sample_contents))):
        try:
            result = await pipeline.create_signal(
                signal_type="text",
                content=sample_contents[i],
                source=f"simulation:{source}",
                metadata={
                    "input_method": "batch_simulation",
                    "batch_index": i
                },
                user_id="simulation_user"
            )
            
            results.append({
                "index": i,
                "success": True,
                "signal_id": result.get("signal_id"),
                "category": result.get("category")
            })
            
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r.get("success"))
    
    # 이벤트 로그 기록
    event_log.append({
        "type": "batch_simulated",
        "source": source,
        "count": count,
        "success": success_count,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "total": count,
        "success_count": success_count,
        "results": results
    }

@router.post("/simulate/workflow")
async def simulate_workflow(workflow_name: str = "default"):
    """
    전체 워크플로우 시뮬레이션
    - 시그널 수신 → 분석 → 자산화 → 모듈화 전 과정 테스트
    """
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    workflow_steps = []
    
    # Step 1: 시그널 수신
    step1_content = "혁신적인 AI 기반 자동화 솔루션에 대한 특허 아이디어"
    
    try:
        result = await pipeline.create_signal(
            signal_type="text",
            content=step1_content,
            source="workflow_simulation",
            metadata={
                "input_method": "workflow_simulation",
                "workflow_name": workflow_name,
                "analysis_type": "patent_idea"
            },
            user_id="simulation_user"
        )
        
        workflow_steps.append({
            "step": 1,
            "name": "시그널 수신",
            "status": "success",
            "signal_id": result.get("signal_id"),
            "category": result.get("category")
        })
        
        # Step 2: 분석 결과 확인
        workflow_steps.append({
            "step": 2,
            "name": "AI 분석",
            "status": "success",
            "analysis_type": "patent_idea",
            "ai_response": result.get("ai_analysis", {}).get("analysis_summary", "분석 완료")[:100]
        })
        
        # Step 3: 분류 결과
        workflow_steps.append({
            "step": 3,
            "name": "시그널 분류",
            "status": "success",
            "category": result.get("category"),
            "stages_completed": result.get("stages_completed", [])
        })
        
        # Step 4: 완료
        workflow_steps.append({
            "step": 4,
            "name": "파이프라인 완료",
            "status": "success",
            "final_status": result.get("status")
        })
        
    except Exception as e:
        workflow_steps.append({
            "step": len(workflow_steps) + 1,
            "name": "오류 발생",
            "status": "error",
            "error": str(e)
        })
    
    # 이벤트 로그 기록
    event_log.append({
        "type": "workflow_simulated",
        "workflow_name": workflow_name,
        "steps_count": len(workflow_steps),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": all(s.get("status") == "success" for s in workflow_steps),
        "workflow_name": workflow_name,
        "steps": workflow_steps,
        "total_steps": len(workflow_steps)
    }

# ==================== 스케줄링 ====================

@router.post("/schedule/create")
async def create_scheduled_job(job: ScheduledJobCreate):
    """스케줄 작업 생성 (시뮬레이션)"""
    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    scheduled_jobs.append({
        "job_id": job_id,
        "name": job.name,
        "integration_id": job.integration_id,
        "action": job.action,
        "schedule": job.schedule,
        "payload": job.payload,
        "enabled": job.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_run": None,
        "next_run": "준비 중 (시뮬레이션)",
        "run_count": 0
    })
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "스케줄 작업이 생성되었습니다 (시뮬레이션 모드)"
    }

@router.get("/schedule/list")
async def list_scheduled_jobs():
    """스케줄 작업 목록"""
    return {
        "jobs": scheduled_jobs,
        "total": len(scheduled_jobs)
    }

@router.delete("/schedule/{job_id}")
async def delete_scheduled_job(job_id: str):
    """스케줄 작업 삭제"""
    global scheduled_jobs
    scheduled_jobs = [j for j in scheduled_jobs if j["job_id"] != job_id]
    return {"success": True}

@router.post("/schedule/{job_id}/run")
async def run_scheduled_job_now(job_id: str):
    """스케줄 작업 즉시 실행 (시뮬레이션)"""
    job = next((j for j in scheduled_jobs if j["job_id"] == job_id), None)
    
    if not job:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다")
    
    # 시뮬레이션 실행
    job["last_run"] = datetime.now(timezone.utc).isoformat()
    job["run_count"] = job.get("run_count", 0) + 1
    
    # 이벤트 로그 기록
    event_log.append({
        "type": "scheduled_job_run",
        "job_id": job_id,
        "job_name": job["name"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "작업이 실행되었습니다 (시뮬레이션)",
        "run_count": job["run_count"]
    }

# ==================== 아웃바운드 웹훅 ====================

@router.post("/outbound/create")
async def create_outbound_webhook(config: OutboundWebhookConfig):
    """아웃바운드 웹훅 설정 (GVIC → 외부)"""
    webhook_id = f"out_{uuid.uuid4().hex[:8]}"
    
    outbound_webhooks.append({
        "webhook_id": webhook_id,
        "url": config.url,
        "events": config.events,
        "headers": config.headers,
        "enabled": config.enabled,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "delivery_count": 0,
        "last_delivery": None
    })
    
    return {
        "success": True,
        "webhook_id": webhook_id,
        "message": "아웃바운드 웹훅이 설정되었습니다"
    }

@router.get("/outbound/list")
async def list_outbound_webhooks():
    """아웃바운드 웹훅 목록"""
    return {
        "webhooks": outbound_webhooks,
        "total": len(outbound_webhooks)
    }

@router.post("/outbound/{webhook_id}/test")
async def test_outbound_webhook(webhook_id: str):
    """아웃바운드 웹훅 테스트 (시뮬레이션)"""
    webhook = next((w for w in outbound_webhooks if w["webhook_id"] == webhook_id), None)
    
    if not webhook:
        raise HTTPException(status_code=404, detail="웹훅을 찾을 수 없습니다")
    
    # 시뮬레이션: 실제로 HTTP 요청을 보내지 않음
    test_payload = {
        "event": "test",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": {"message": "테스트 이벤트입니다"}
    }
    
    webhook["last_delivery"] = datetime.now(timezone.utc).isoformat()
    webhook["delivery_count"] = webhook.get("delivery_count", 0) + 1
    
    return {
        "success": True,
        "webhook_id": webhook_id,
        "simulated": True,
        "payload_sent": test_payload,
        "message": "테스트 웹훅이 전송되었습니다 (시뮬레이션)"
    }

# ==================== 이벤트 로그 ====================

@router.get("/events/log")
async def get_event_log(limit: int = 50):
    """이벤트 로그 조회"""
    return {
        "events": event_log[-limit:],
        "total": len(event_log)
    }

@router.delete("/events/clear")
async def clear_event_log():
    """이벤트 로그 초기화"""
    global event_log
    event_log = []
    return {"success": True, "message": "이벤트 로그가 초기화되었습니다"}

# ==================== 연동 가이드 ====================

@router.get("/guide/quick-start")
async def get_quick_start_guide():
    """빠른 시작 가이드"""
    return {
        "title": "GVIC 외부 연동 빠른 시작",
        "steps": [
            {
                "step": 1,
                "title": "API 키 생성",
                "description": "API 연동 탭에서 새 API 키를 생성합니다",
                "endpoint": "/api/webhook/keys"
            },
            {
                "step": 2,
                "title": "연동 플랫폼 선택",
                "description": "Zapier, n8n, Make 또는 커스텀 중 선택합니다",
                "endpoint": "/api/connector/integrations"
            },
            {
                "step": 3,
                "title": "시뮬레이션 테스트",
                "description": "실제 연동 전 시뮬레이션으로 테스트합니다",
                "endpoint": "/api/connector/simulate/signal"
            },
            {
                "step": 4,
                "title": "실제 연동 설정",
                "description": "외부 플랫폼에서 GVIC 웹훅 URL과 API 키를 설정합니다",
                "webhook_url": "/api/webhook/signal"
            }
        ],
        "sample_payload": {
            "type": "text",
            "content": "분석할 내용",
            "analysis_type": "general",
            "priority": "normal",
            "metadata": {}
        }
    }

@router.get("/guide/use-cases")
async def get_use_cases():
    """연동 활용 사례"""
    return {
        "use_cases": [
            {
                "id": "email_to_signal",
                "title": "이메일 → 시그널 자동 변환",
                "description": "중요 이메일을 자동으로 GVIC 시그널로 변환하여 분석",
                "platforms": ["Zapier", "n8n"],
                "trigger": "새 이메일 수신",
                "action": "GVIC 시그널 생성"
            },
            {
                "id": "slack_monitoring",
                "title": "Slack 메시지 모니터링",
                "description": "특정 채널의 메시지를 자동으로 수집하여 인사이트 도출",
                "platforms": ["Zapier", "Make"],
                "trigger": "Slack 메시지",
                "action": "GVIC 분석"
            },
            {
                "id": "form_submission",
                "title": "폼 제출 자동 분석",
                "description": "Google Forms, Typeform 등의 응답을 자동 분석",
                "platforms": ["Zapier", "n8n", "Make"],
                "trigger": "폼 제출",
                "action": "GVIC 시그널 생성 + 분석"
            },
            {
                "id": "social_listening",
                "title": "소셜 미디어 리스닝",
                "description": "Twitter, RSS 등에서 특정 키워드 언급 시 자동 수집",
                "platforms": ["n8n", "Make"],
                "trigger": "키워드 언급",
                "action": "시그널 수집 + 트렌드 분석"
            },
            {
                "id": "crm_sync",
                "title": "CRM 데이터 동기화",
                "description": "고객 피드백, 문의사항을 자동으로 분석하여 인사이트 도출",
                "platforms": ["Zapier", "n8n"],
                "trigger": "새 CRM 레코드",
                "action": "고객 인사이트 분석"
            }
        ]
    }
