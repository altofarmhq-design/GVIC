# 특허 6-J: 다중 도메인 통합 인터페이스 시스템

## 기본 정보
- **영문명**: Multiple Domain Integration Interface System
- **기술분야**: 이종 시스템 간 데이터 통합 및 교환
- **상태**: ✅ 구현 완료

## 시스템 구성요소

| 구성요소 | 설명 |
|---------|------|
| Domain Adapter Manager | 도메인별 어댑터 관리 (ERP, CRM, SCM, MES, Finance 등) |
| Data Transformation Engine | CDM(공통 데이터 모델) 변환 엔진 |
| Semantic Mapping Repository | 도메인 간 필드 의미 매핑 저장소 |
| Routing Engine | 규칙 기반 메시지 라우팅 |
| Integration Monitor | 실시간 모니터링 (처리량, 지연시간, 에러) |

## 데이터 구조

### CommonDataModel (CDM)
```python
@dataclass
class CommonDataModel:
    message_id: str          # UUID
    source_domain: str       # 소스 도메인
    target_domains: List[str] # 타겟 도메인 목록
    timestamp: str           # ISO8601
    payload: Dict            # 정규화된 데이터
    metadata: Dict           # 메타데이터
```

### DomainAdapter
```python
@dataclass
class DomainAdapter:
    domain_id: str
    domain_type: DomainType  # ERP, CRM, SCM, MES, etc.
    protocol: ProtocolType   # REST, SOAP, MQ, WebSocket, etc.
    endpoint: str
    health_score: float      # 0~1
    message_count: int
    error_count: int
```

### SemanticMapping
```python
@dataclass
class SemanticMapping:
    mapping_id: str
    source_domain: str
    source_field: str
    target_domain: str
    target_field: str
    similarity_score: float  # 0~1
```

### RoutingRule
```python
@dataclass
class RoutingRule:
    rule_id: str
    name: str
    source_domain: str
    message_type: str
    target_domains: List[str]
    priority: int
    enabled: bool
```

## 핵심 기능

### 1. Hub-and-Spoke 아키텍처
- O(n²) → O(n) 복잡도 감소
- 중앙 허브를 통한 데이터 교환

### 2. 데이터 교환 프로세스
```
1. 소스 어댑터 확인/생성
2. CDM으로 변환 (to_cdm)
3. 라우팅 규칙 적용 → 타겟 도메인 결정
4. 각 타겟으로 변환 (from_cdm)
5. 어댑터 헬스 업데이트
6. 모니터링 기록
```

### 3. 기본 어댑터 (5개)
- erp_adapter (REST)
- crm_adapter (REST)
- scm_adapter (Message Queue)
- mes_adapter (WebSocket)
- finance_adapter (REST)

### 4. 기본 매핑 (6개)
| 소스 | 필드 | 타겟 | 필드 | 유사도 |
|------|------|------|------|--------|
| erp | customer_id | crm | account_number | 95% |
| erp | product_code | scm | item_id | 90% |
| erp | order_date | finance | transaction_date | 85% |
| crm | customer_name | erp | client_name | 92% |
| mes | work_order | erp | production_order | 88% |
| scm | supplier_id | finance | vendor_code | 87% |

### 5. 기본 라우팅 규칙 (4개)
| 규칙 | 소스 | 메시지 | 타겟 | 우선순위 |
|------|------|--------|------|----------|
| order_sync | erp | order | crm, scm, finance | 10 |
| inventory_update | scm | inventory | erp, mes, wms | 9 |
| customer_sync | crm | customer | erp, finance | 8 |
| production_report | mes | production | erp, scm | 7 |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | /api/integration/status | 통합 시스템 상태 |
| POST | /api/integration/exchange | 데이터 교환 실행 |
| GET | /api/integration/adapters | 어댑터 목록 |
| POST | /api/integration/adapters | 어댑터 추가 |
| GET | /api/integration/mappings | 매핑 목록 |
| POST | /api/integration/mappings | 매핑 추가 |
| GET | /api/integration/routing | 라우팅 규칙 목록 |
| POST | /api/integration/routing | 라우팅 규칙 추가 |

## 구현 파일
- `/app/backend/core/multi_domain_integration.py`
