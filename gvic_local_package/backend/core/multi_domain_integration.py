"""
특허 6-J: 다중 도메인 통합 인터페이스 시스템
Multiple Domain Integration Interface System
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
import uuid
import numpy as np

class DomainType(str, Enum):
    """도메인 유형"""
    ERP = "erp"
    CRM = "crm"
    SCM = "scm"
    MES = "mes"
    WMS = "wms"
    FINANCE = "finance"
    HR = "hr"
    ECOMMERCE = "ecommerce"
    HEALTHCARE = "healthcare"
    CUSTOM = "custom"

class ProtocolType(str, Enum):
    """프로토콜 유형"""
    REST = "rest"
    SOAP = "soap"
    MESSAGE_QUEUE = "mq"
    FILE_TRANSFER = "file"
    EDI = "edi"
    WEBSOCKET = "websocket"

@dataclass
class CommonDataModel:
    """공통 데이터 모델 (CDM)"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_domain: str = ""
    target_domains: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'message_id': self.message_id,
            'source_domain': self.source_domain,
            'target_domains': self.target_domains,
            'timestamp': self.timestamp,
            'payload': self.payload,
            'metadata': self.metadata
        }

@dataclass
class DomainAdapter:
    """도메인 어댑터"""
    domain_id: str
    domain_type: DomainType
    protocol: ProtocolType
    endpoint: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    health_score: float = 1.0
    message_count: int = 0
    error_count: int = 0
    last_active: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'domain_id': self.domain_id,
            'domain_type': self.domain_type.value,
            'protocol': self.protocol.value,
            'endpoint': self.endpoint,
            'enabled': self.enabled,
            'health_score': self.health_score,
            'message_count': self.message_count,
            'error_count': self.error_count,
            'last_active': self.last_active
        }

@dataclass
class SemanticMapping:
    """의미 매핑"""
    mapping_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_domain: str = ""
    source_field: str = ""
    target_domain: str = ""
    target_field: str = ""
    similarity_score: float = 1.0
    transformation_rule: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'mapping_id': self.mapping_id,
            'source_domain': self.source_domain,
            'source_field': self.source_field,
            'target_domain': self.target_domain,
            'target_field': self.target_field,
            'similarity_score': self.similarity_score,
            'transformation_rule': self.transformation_rule
        }

@dataclass
class RoutingRule:
    """라우팅 규칙"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    source_domain: Optional[str] = None
    message_type: Optional[str] = None
    condition: Optional[str] = None
    target_domains: List[str] = field(default_factory=list)
    priority: int = 0
    enabled: bool = True
    
    def to_dict(self) -> Dict:
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'source_domain': self.source_domain,
            'message_type': self.message_type,
            'condition': self.condition,
            'target_domains': self.target_domains,
            'priority': self.priority,
            'enabled': self.enabled
        }

class DomainAdapterManager:
    """도메인 어댑터 관리자"""
    
    def __init__(self):
        self.adapters: Dict[str, DomainAdapter] = {}
        self._init_default_adapters()
    
    def _init_default_adapters(self):
        """기본 어댑터 초기화"""
        defaults = [
            ("erp_adapter", DomainType.ERP, ProtocolType.REST, "/api/erp"),
            ("crm_adapter", DomainType.CRM, ProtocolType.REST, "/api/crm"),
            ("scm_adapter", DomainType.SCM, ProtocolType.MESSAGE_QUEUE, "mq://scm"),
            ("mes_adapter", DomainType.MES, ProtocolType.WEBSOCKET, "ws://mes"),
            ("finance_adapter", DomainType.FINANCE, ProtocolType.REST, "/api/finance"),
        ]
        for domain_id, domain_type, protocol, endpoint in defaults:
            self.register_adapter(domain_id, domain_type, protocol, endpoint)
    
    def register_adapter(self, domain_id: str, domain_type: DomainType, 
                        protocol: ProtocolType, endpoint: str = "", 
                        config: Dict = None) -> DomainAdapter:
        """어댑터 등록"""
        adapter = DomainAdapter(
            domain_id=domain_id,
            domain_type=domain_type,
            protocol=protocol,
            endpoint=endpoint,
            config=config or {}
        )
        self.adapters[domain_id] = adapter
        return adapter
    
    def get_adapter(self, domain_id: str) -> Optional[DomainAdapter]:
        """어댑터 조회"""
        return self.adapters.get(domain_id)
    
    def list_adapters(self) -> List[DomainAdapter]:
        """모든 어댑터 목록"""
        return list(self.adapters.values())
    
    def update_health(self, domain_id: str, success: bool):
        """어댑터 헬스 업데이트"""
        if domain_id in self.adapters:
            adapter = self.adapters[domain_id]
            adapter.message_count += 1
            adapter.last_active = datetime.now().isoformat()
            if not success:
                adapter.error_count += 1
            # 헬스 점수 계산
            if adapter.message_count > 0:
                adapter.health_score = 1 - (adapter.error_count / adapter.message_count)

class DataTransformationEngine:
    """데이터 변환 엔진"""
    
    def __init__(self, semantic_repo: 'SemanticMappingRepository'):
        self.semantic_repo = semantic_repo
        self.transformation_history: List[Dict] = []
    
    def to_cdm(self, data: Dict, source_domain: str, target_domains: List[str] = None) -> CommonDataModel:
        """도메인 데이터를 CDM으로 변환"""
        # 엔티티 추출
        entities = []
        if isinstance(data, dict):
            for key, value in data.items():
                entities.append({
                    'name': key,
                    'value': value,
                    'type': type(value).__name__
                })
        
        cdm = CommonDataModel(
            source_domain=source_domain,
            target_domains=target_domains or [],
            payload={
                'entities': entities,
                'relationships': [],
                'original_data': data
            },
            metadata={
                'transformation_timestamp': datetime.now().isoformat(),
                'source_format': 'json'
            }
        )
        
        self.transformation_history.append({
            'timestamp': datetime.now().isoformat(),
            'direction': 'to_cdm',
            'source_domain': source_domain,
            'message_id': cdm.message_id
        })
        
        return cdm
    
    def from_cdm(self, cdm: CommonDataModel, target_domain: str) -> Dict:
        """CDM을 도메인 데이터로 변환"""
        # 의미 매핑 적용
        mappings = self.semantic_repo.get_mappings(cdm.source_domain, target_domain)
        
        result = {}
        original_data = cdm.payload.get('original_data', {})
        
        for key, value in original_data.items():
            # 매핑이 있으면 변환
            mapped_key = key
            for mapping in mappings:
                if mapping.source_field == key:
                    mapped_key = mapping.target_field
                    break
            result[mapped_key] = value
        
        self.transformation_history.append({
            'timestamp': datetime.now().isoformat(),
            'direction': 'from_cdm',
            'target_domain': target_domain,
            'message_id': cdm.message_id
        })
        
        return result
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        to_cdm_count = sum(1 for h in self.transformation_history if h['direction'] == 'to_cdm')
        from_cdm_count = sum(1 for h in self.transformation_history if h['direction'] == 'from_cdm')
        
        return {
            'total_transformations': len(self.transformation_history),
            'to_cdm_count': to_cdm_count,
            'from_cdm_count': from_cdm_count
        }

class SemanticMappingRepository:
    """의미 매핑 저장소"""
    
    def __init__(self):
        self.mappings: List[SemanticMapping] = []
        self._init_default_mappings()
    
    def _init_default_mappings(self):
        """기본 매핑 초기화"""
        defaults = [
            ("erp", "customer_id", "crm", "account_number", 0.95),
            ("erp", "product_code", "scm", "item_id", 0.90),
            ("erp", "order_date", "finance", "transaction_date", 0.85),
            ("crm", "customer_name", "erp", "client_name", 0.92),
            ("mes", "work_order", "erp", "production_order", 0.88),
            ("scm", "supplier_id", "finance", "vendor_code", 0.87),
        ]
        for src_domain, src_field, tgt_domain, tgt_field, score in defaults:
            self.add_mapping(src_domain, src_field, tgt_domain, tgt_field, score)
    
    def add_mapping(self, source_domain: str, source_field: str, 
                   target_domain: str, target_field: str,
                   similarity_score: float = 1.0,
                   transformation_rule: str = None) -> SemanticMapping:
        """매핑 추가"""
        mapping = SemanticMapping(
            source_domain=source_domain,
            source_field=source_field,
            target_domain=target_domain,
            target_field=target_field,
            similarity_score=similarity_score,
            transformation_rule=transformation_rule
        )
        self.mappings.append(mapping)
        return mapping
    
    def get_mappings(self, source_domain: str, target_domain: str) -> List[SemanticMapping]:
        """매핑 조회"""
        return [
            m for m in self.mappings 
            if m.source_domain == source_domain and m.target_domain == target_domain
        ]
    
    def calculate_similarity(self, field1: str, field2: str) -> float:
        """필드 유사도 계산"""
        # 간단한 자카드 유사도
        set1 = set(field1.lower().replace('_', ''))
        set2 = set(field2.lower().replace('_', ''))
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def list_mappings(self) -> List[SemanticMapping]:
        """모든 매핑 목록"""
        return self.mappings
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        domains = set()
        for m in self.mappings:
            domains.add(m.source_domain)
            domains.add(m.target_domain)
        
        avg_similarity = np.mean([m.similarity_score for m in self.mappings]) if self.mappings else 0
        
        return {
            'total_mappings': len(self.mappings),
            'domains_covered': len(domains),
            'average_similarity': float(avg_similarity)
        }

class RoutingEngine:
    """라우팅 엔진"""
    
    def __init__(self):
        self.rules: List[RoutingRule] = []
        self.routing_history: List[Dict] = []
        self._init_default_rules()
    
    def _init_default_rules(self):
        """기본 라우팅 규칙 초기화"""
        defaults = [
            ("order_sync", "erp", "order", ["crm", "scm", "finance"], 10),
            ("inventory_update", "scm", "inventory", ["erp", "mes", "wms"], 9),
            ("customer_sync", "crm", "customer", ["erp", "finance"], 8),
            ("production_report", "mes", "production", ["erp", "scm"], 7),
        ]
        for name, source, msg_type, targets, priority in defaults:
            self.add_rule(name, source, msg_type, targets, priority)
    
    def add_rule(self, name: str, source_domain: str = None,
                message_type: str = None, target_domains: List[str] = None,
                priority: int = 0) -> RoutingRule:
        """라우팅 규칙 추가"""
        rule = RoutingRule(
            name=name,
            source_domain=source_domain,
            message_type=message_type,
            target_domains=target_domains or [],
            priority=priority
        )
        self.rules.append(rule)
        # 우선순위순 정렬
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return rule
    
    def route(self, cdm: CommonDataModel) -> List[str]:
        """메시지 라우팅"""
        target_domains = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            # 규칙 매칭
            match = True
            if rule.source_domain and rule.source_domain != cdm.source_domain:
                match = False
            if rule.message_type and rule.message_type != cdm.payload.get('message_type'):
                match = False
            
            if match:
                target_domains.extend(rule.target_domains)
        
        # 중복 제거
        target_domains = list(set(target_domains))
        
        self.routing_history.append({
            'timestamp': datetime.now().isoformat(),
            'message_id': cdm.message_id,
            'source_domain': cdm.source_domain,
            'target_domains': target_domains,
            'rules_matched': len([r for r in self.rules if r.source_domain == cdm.source_domain])
        })
        
        return target_domains
    
    def list_rules(self) -> List[RoutingRule]:
        """모든 규칙 목록"""
        return self.rules
    
    def get_statistics(self) -> Dict:
        """통계 조회"""
        return {
            'total_rules': len(self.rules),
            'active_rules': sum(1 for r in self.rules if r.enabled),
            'total_routings': len(self.routing_history)
        }

class IntegrationMonitor:
    """통합 모니터"""
    
    def __init__(self):
        self.exchange_logs: List[Dict] = []
        self.error_logs: List[Dict] = []
        self.performance_metrics: Dict[str, List[float]] = {}
        self.start_time = datetime.now()
    
    def log_exchange(self, message_id: str, source: str, targets: List[str],
                    status: str, duration_ms: float = 0):
        """교환 로그 기록"""
        self.exchange_logs.append({
            'timestamp': datetime.now().isoformat(),
            'message_id': message_id,
            'source': source,
            'targets': targets,
            'status': status,
            'duration_ms': duration_ms
        })
        
        # 성능 메트릭 업데이트
        if source not in self.performance_metrics:
            self.performance_metrics[source] = []
        self.performance_metrics[source].append(duration_ms)
    
    def log_error(self, message_id: str, component: str, error: str):
        """에러 로그 기록"""
        self.error_logs.append({
            'timestamp': datetime.now().isoformat(),
            'message_id': message_id,
            'component': component,
            'error': error
        })
    
    def get_throughput(self) -> float:
        """처리량 계산 (메시지/초)"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if elapsed <= 0:
            return 0.0
        return len(self.exchange_logs) / elapsed
    
    def get_average_latency(self) -> float:
        """평균 지연시간"""
        if not self.exchange_logs:
            return 0.0
        return np.mean([log['duration_ms'] for log in self.exchange_logs])
    
    def get_dashboard_data(self) -> Dict:
        """대시보드 데이터"""
        return {
            'total_exchanges': len(self.exchange_logs),
            'total_errors': len(self.error_logs),
            'throughput': self.get_throughput(),
            'average_latency_ms': self.get_average_latency(),
            'recent_exchanges': self.exchange_logs[-10:][::-1],
            'recent_errors': self.error_logs[-5:][::-1],
            'uptime_seconds': (datetime.now() - self.start_time).total_seconds()
        }

class MultiDomainIntegrationSystem:
    """다중 도메인 통합 인터페이스 시스템"""
    
    def __init__(self):
        # 핵심 컴포넌트 초기화
        self.adapter_manager = DomainAdapterManager()
        self.semantic_repo = SemanticMappingRepository()
        self.transformation_engine = DataTransformationEngine(self.semantic_repo)
        self.routing_engine = RoutingEngine()
        self.monitor = IntegrationMonitor()
        
        self.exchange_history: List[Dict] = []
    
    def exchange(self, data: Dict, source_domain: str, 
                message_type: str = "default") -> Dict:
        """데이터 교환 실행"""
        import time
        start_time = time.time()
        
        results = {
            'success': False,
            'message_id': None,
            'source_domain': source_domain,
            'target_domains': [],
            'transformations': [],
            'errors': []
        }
        
        try:
            # 1. 소스 어댑터 확인
            source_adapter = self.adapter_manager.get_adapter(f"{source_domain}_adapter")
            if not source_adapter:
                # 동적 어댑터 생성
                source_adapter = self.adapter_manager.register_adapter(
                    f"{source_domain}_adapter",
                    DomainType.CUSTOM,
                    ProtocolType.REST
                )
            
            # 2. CDM으로 변환
            cdm = self.transformation_engine.to_cdm(data, source_domain)
            cdm.payload['message_type'] = message_type
            results['message_id'] = cdm.message_id
            
            # 3. 라우팅
            target_domains = self.routing_engine.route(cdm)
            if not target_domains:
                # 기본 대상
                target_domains = ['default']
            
            cdm.target_domains = target_domains
            results['target_domains'] = target_domains
            
            # 4. 각 타겟으로 변환 및 전송
            for target in target_domains:
                try:
                    transformed = self.transformation_engine.from_cdm(cdm, target)
                    results['transformations'].append({
                        'target': target,
                        'success': True,
                        'data': transformed
                    })
                except Exception as e:
                    results['transformations'].append({
                        'target': target,
                        'success': False,
                        'error': str(e)
                    })
                    results['errors'].append(f"Transform to {target} failed: {str(e)}")
            
            # 5. 어댑터 상태 업데이트
            self.adapter_manager.update_health(f"{source_domain}_adapter", True)
            
            # 6. 모니터링 기록
            duration_ms = (time.time() - start_time) * 1000
            self.monitor.log_exchange(
                cdm.message_id, source_domain, target_domains,
                'success', duration_ms
            )
            
            results['success'] = True
            results['duration_ms'] = duration_ms
            
        except Exception as e:
            results['errors'].append(str(e))
            self.monitor.log_error(results.get('message_id', 'unknown'), 'exchange', str(e))
        
        self.exchange_history.append(results)
        return results
    
    def get_system_status(self) -> Dict:
        """시스템 상태 조회"""
        return {
            'adapters': {
                'total': len(self.adapter_manager.adapters),
                'healthy': sum(1 for a in self.adapter_manager.adapters.values() if a.health_score > 0.8),
                'list': [a.to_dict() for a in self.adapter_manager.list_adapters()]
            },
            'semantic_mappings': self.semantic_repo.get_statistics(),
            'routing': self.routing_engine.get_statistics(),
            'transformations': self.transformation_engine.get_statistics(),
            'monitor': self.monitor.get_dashboard_data(),
            'total_exchanges': len(self.exchange_history),
            'success_rate': sum(1 for e in self.exchange_history if e['success']) / len(self.exchange_history) if self.exchange_history else 0
        }
    
    def get_adapters(self) -> List[Dict]:
        """어댑터 목록"""
        return [a.to_dict() for a in self.adapter_manager.list_adapters()]
    
    def get_mappings(self) -> List[Dict]:
        """매핑 목록"""
        return [m.to_dict() for m in self.semantic_repo.list_mappings()]
    
    def get_routing_rules(self) -> List[Dict]:
        """라우팅 규칙 목록"""
        return [r.to_dict() for r in self.routing_engine.list_rules()]
    
    def add_adapter(self, domain_id: str, domain_type: str, 
                   protocol: str, endpoint: str = "") -> Dict:
        """어댑터 추가"""
        adapter = self.adapter_manager.register_adapter(
            domain_id,
            DomainType(domain_type),
            ProtocolType(protocol),
            endpoint
        )
        return adapter.to_dict()
    
    def add_mapping(self, source_domain: str, source_field: str,
                   target_domain: str, target_field: str,
                   similarity_score: float = 1.0) -> Dict:
        """매핑 추가"""
        mapping = self.semantic_repo.add_mapping(
            source_domain, source_field,
            target_domain, target_field,
            similarity_score
        )
        return mapping.to_dict()
    
    def add_routing_rule(self, name: str, source_domain: str,
                        message_type: str, target_domains: List[str],
                        priority: int = 0) -> Dict:
        """라우팅 규칙 추가"""
        rule = self.routing_engine.add_rule(
            name, source_domain, message_type, target_domains, priority
        )
        return rule.to_dict()
