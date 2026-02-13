"""
GVIC 통합 데이터 연동 시스템
============================
분석 결과를 모든 탭과 연동하기 위한 중앙 데이터 관리 모듈

모든 시그널(URL 분석, 파일 분석 등)이 처리되면:
1. 처리 이력에 기록
2. 대시보드 통계 업데이트
3. 모니터링 데이터 업데이트
4. 알림 생성
5. 모델/예측 데이터 연동
6. 파레토/비교 분석 데이터 업데이트
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import uuid
import logging
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class AnalysisSession:
    """분석 세션 데이터"""
    session_id: str
    source_type: str  # 'url', 'file', 'api'
    source_url: str
    product_name: str
    created_at: str
    completed_at: Optional[str] = None
    status: str = 'running'  # 'running', 'completed', 'failed'
    
    # 입력 데이터 요약
    total_records: int = 0
    valid_records: int = 0
    
    # 감성 분석 결과
    sentiment_positive: int = 0
    sentiment_neutral: int = 0
    sentiment_negative: int = 0
    sentiment_positive_ratio: float = 0.0
    sentiment_neutral_ratio: float = 0.0
    sentiment_negative_ratio: float = 0.0
    avg_rating: float = 0.0
    
    # 요인 분석 결과
    positive_factors: List[Dict] = field(default_factory=list)
    negative_factors: List[Dict] = field(default_factory=list)
    
    # GVIC 엔진 결과
    convergence_status: str = ''
    convergence_balance_index: float = 0.0
    signal_conformance_rate: float = 0.0
    distribution_public: float = 0.0
    distribution_productive: float = 0.0
    distribution_individual: float = 0.0
    fairness_index: float = 0.0
    
    # 인사이트 및 권장사항
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # 출력 파일
    pdf_path: str = ''
    pdf_url: str = ''
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class GVICDataHub:
    """GVIC 통합 데이터 허브 - 모든 탭 연동"""
    
    def __init__(self, db):
        self.db = db
        self.current_session: Optional[AnalysisSession] = None
        self._listeners = []
    
    async def start_session(
        self, 
        source_type: str, 
        source_url: str, 
        product_name: str = ""
    ) -> AnalysisSession:
        """새 분석 세션 시작"""
        session = AnalysisSession(
            session_id=str(uuid.uuid4())[:8],
            source_type=source_type,
            source_url=source_url,
            product_name=product_name,
            created_at=datetime.now(timezone.utc).isoformat(),
            status='running'
        )
        self.current_session = session
        
        # DB에 세션 기록
        await self.db.analysis_sessions.insert_one({
            **session.to_dict(),
            '_id': session.session_id
        })
        
        # 모니터링: 분석 시작 이벤트
        await self._emit_event('analysis_started', {
            'session_id': session.session_id,
            'source_type': source_type,
            'source_url': source_url
        })
        
        return session
    
    async def update_input_summary(
        self, 
        total_records: int, 
        valid_records: int
    ):
        """입력 데이터 요약 업데이트"""
        if not self.current_session:
            return
        
        self.current_session.total_records = total_records
        self.current_session.valid_records = valid_records
        
        # 처리 이력에 기록
        await self.db.processing_history.insert_one({
            'id': str(uuid.uuid4()),
            'session_id': self.current_session.session_id,
            'type': 'input_loaded',
            'input_value': total_records,
            'success': True,
            'data': {
                'total_records': total_records,
                'valid_records': valid_records,
                'source_url': self.current_session.source_url
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    async def update_sentiment_analysis(
        self, 
        positive: int, 
        neutral: int, 
        negative: int,
        avg_rating: float
    ):
        """감성 분석 결과 업데이트"""
        if not self.current_session:
            return
        
        total = positive + neutral + negative
        if total == 0:
            total = 1
        
        self.current_session.sentiment_positive = positive
        self.current_session.sentiment_neutral = neutral
        self.current_session.sentiment_negative = negative
        self.current_session.sentiment_positive_ratio = positive / total
        self.current_session.sentiment_neutral_ratio = neutral / total
        self.current_session.sentiment_negative_ratio = negative / total
        self.current_session.avg_rating = avg_rating
        
        # 처리 이력에 기록
        await self.db.processing_history.insert_one({
            'id': str(uuid.uuid4()),
            'session_id': self.current_session.session_id,
            'type': 'sentiment_analysis',
            'input_value': total,
            'success': True,
            'data': {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'avg_rating': avg_rating
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # 알림: 부정 비율이 높으면 경고
        if self.current_session.sentiment_negative_ratio > 0.2:
            await self._create_alert(
                'warning',
                f"부정 리뷰 비율이 {self.current_session.sentiment_negative_ratio*100:.1f}%로 높습니다",
                {'session_id': self.current_session.session_id}
            )
    
    async def update_factors(
        self, 
        positive_factors: List[Dict], 
        negative_factors: List[Dict]
    ):
        """요인 분석 결과 업데이트"""
        if not self.current_session:
            return
        
        self.current_session.positive_factors = positive_factors
        self.current_session.negative_factors = negative_factors
        
        # 파레토 분석 데이터로 저장
        await self.db.pareto_analysis.insert_one({
            'session_id': self.current_session.session_id,
            'type': 'factor_analysis',
            'positive_factors': positive_factors,
            'negative_factors': negative_factors,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    async def update_gvic_results(
        self,
        convergence_status: str,
        balance_index: float,
        conformance_rate: float,
        distribution: Dict[str, float],
        fairness_index: float
    ):
        """GVIC 엔진 분석 결과 업데이트"""
        if not self.current_session:
            return
        
        self.current_session.convergence_status = convergence_status
        self.current_session.convergence_balance_index = balance_index
        self.current_session.signal_conformance_rate = conformance_rate
        self.current_session.distribution_public = distribution.get('public', 0)
        self.current_session.distribution_productive = distribution.get('productive', 0)
        self.current_session.distribution_individual = distribution.get('individual', 0)
        self.current_session.fairness_index = fairness_index
        
        # 처리 이력에 기록
        await self.db.processing_history.insert_one({
            'id': str(uuid.uuid4()),
            'session_id': self.current_session.session_id,
            'type': 'gvic_analysis',
            'input_value': self.current_session.total_records,
            'success': True,
            'data': {
                'convergence_status': convergence_status,
                'balance_index': balance_index,
                'conformance_rate': conformance_rate,
                'distribution': distribution,
                'fairness_index': fairness_index
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # 모델/예측 데이터 업데이트
        await self.db.predictions.insert_one({
            'id': str(uuid.uuid4()),
            'session_id': self.current_session.session_id,
            'model_type': 'gvic_engine',
            'input': {
                'total_records': self.current_session.total_records,
                'sentiment_ratio': {
                    'positive': self.current_session.sentiment_positive_ratio,
                    'neutral': self.current_session.sentiment_neutral_ratio,
                    'negative': self.current_session.sentiment_negative_ratio
                }
            },
            'output': {
                'balance_index': balance_index,
                'fairness_index': fairness_index,
                'distribution': distribution
            },
            'confidence': conformance_rate,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
        # 비교 분석 데이터 저장
        await self.db.comparison_data.insert_one({
            'session_id': self.current_session.session_id,
            'source_url': self.current_session.source_url,
            'product_name': self.current_session.product_name,
            'metrics': {
                'total_records': self.current_session.total_records,
                'avg_rating': self.current_session.avg_rating,
                'positive_ratio': self.current_session.sentiment_positive_ratio,
                'balance_index': balance_index,
                'fairness_index': fairness_index
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    async def update_insights(
        self, 
        insights: List[str], 
        recommendations: List[str]
    ):
        """인사이트 업데이트"""
        if not self.current_session:
            return
        
        self.current_session.insights = insights
        self.current_session.recommendations = recommendations
    
    async def complete_session(
        self, 
        pdf_path: str, 
        pdf_url: str
    ) -> AnalysisSession:
        """분석 세션 완료"""
        if not self.current_session:
            return None
        
        self.current_session.status = 'completed'
        self.current_session.completed_at = datetime.now(timezone.utc).isoformat()
        self.current_session.pdf_path = pdf_path
        self.current_session.pdf_url = pdf_url
        
        # DB 업데이트
        await self.db.analysis_sessions.update_one(
            {'_id': self.current_session.session_id},
            {'$set': self.current_session.to_dict()}
        )
        
        # 통계 업데이트
        await self._update_statistics()
        
        # 알림: 분석 완료
        await self._create_alert(
            'info',
            f"'{self.current_session.product_name}' 분석이 완료되었습니다 ({self.current_session.total_records}건)",
            {'session_id': self.current_session.session_id, 'pdf_url': pdf_url}
        )
        
        # 이벤트 발생
        await self._emit_event('analysis_completed', {
            'session_id': self.current_session.session_id,
            'total_records': self.current_session.total_records,
            'pdf_url': pdf_url
        })
        
        completed_session = self.current_session
        self.current_session = None
        
        return completed_session
    
    async def _update_statistics(self):
        """전체 통계 업데이트 (대시보드용)"""
        if not self.current_session:
            return
        
        # 기존 통계 가져오기
        stats = await self.db.system_statistics.find_one({'_id': 'global'})
        
        if not stats:
            stats = {
                '_id': 'global',
                'total_sessions': 0,
                'total_records_processed': 0,
                'avg_positive_ratio': 0,
                'avg_fairness_index': 0,
                'sessions_history': []
            }
        
        # 업데이트
        stats['total_sessions'] += 1
        stats['total_records_processed'] += self.current_session.total_records
        
        # 이동 평균 계산
        n = stats['total_sessions']
        stats['avg_positive_ratio'] = (
            (stats['avg_positive_ratio'] * (n-1) + self.current_session.sentiment_positive_ratio) / n
        )
        stats['avg_fairness_index'] = (
            (stats['avg_fairness_index'] * (n-1) + self.current_session.fairness_index) / n
        )
        
        # 최근 세션 이력 (최대 100개)
        stats['sessions_history'].append({
            'session_id': self.current_session.session_id,
            'product_name': self.current_session.product_name,
            'total_records': self.current_session.total_records,
            'positive_ratio': self.current_session.sentiment_positive_ratio,
            'fairness_index': self.current_session.fairness_index,
            'timestamp': self.current_session.completed_at
        })
        if len(stats['sessions_history']) > 100:
            stats['sessions_history'] = stats['sessions_history'][-100:]
        
        stats['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # 저장
        await self.db.system_statistics.update_one(
            {'_id': 'global'},
            {'$set': stats},
            upsert=True
        )
    
    async def _create_alert(
        self, 
        level: str, 
        message: str, 
        data: Dict = None
    ):
        """알림 생성"""
        alert = {
            'id': str(uuid.uuid4()),
            'level': level,  # 'info', 'warning', 'error'
            'message': message,
            'data': data or {},
            'read': False,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await self.db.alerts.insert_one(alert)
    
    async def _emit_event(self, event_type: str, data: Dict):
        """이벤트 발생 (모니터링용)"""
        event = {
            'id': str(uuid.uuid4()),
            'type': event_type,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        await self.db.events.insert_one(event)
    
    # ==================== 탭별 데이터 조회 API ====================
    
    async def get_dashboard_data(self) -> Dict[str, Any]:
        """대시보드 데이터 조회"""
        stats = await self.db.system_statistics.find_one({'_id': 'global'}) or {}
        
        # 최근 세션들
        recent_sessions = await self.db.analysis_sessions.find(
            {'status': 'completed'}, {'_id': 0}
        ).sort('completed_at', -1).limit(10).to_list(10)
        
        # 처리 이력 건수
        history_count = await self.db.processing_history.count_documents({})
        
        return {
            'total_sessions': stats.get('total_sessions', 0),
            'total_records_processed': stats.get('total_records_processed', 0),
            'avg_positive_ratio': stats.get('avg_positive_ratio', 0),
            'avg_fairness_index': stats.get('avg_fairness_index', 0),
            'recent_sessions': recent_sessions,
            'processing_history_count': history_count,
            'last_updated': stats.get('last_updated', '')
        }
    
    async def get_monitoring_data(self) -> Dict[str, Any]:
        """모니터링 데이터 조회"""
        # 최근 이벤트
        events = await self.db.events.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(50).to_list(50)
        
        # 최근 처리 이력
        history = await self.db.processing_history.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(20).to_list(20)
        
        return {
            'events': events,
            'processing_history': history
        }
    
    async def get_prediction_data(self) -> Dict[str, Any]:
        """예측 데이터 조회"""
        predictions = await self.db.predictions.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(20).to_list(20)
        
        return {'predictions': predictions}
    
    async def get_pareto_data(self) -> Dict[str, Any]:
        """파레토 분석 데이터 조회"""
        pareto = await self.db.pareto_analysis.find(
            {}, {'_id': 0}
        ).sort('timestamp', -1).limit(10).to_list(10)
        
        # 요인별 집계
        all_positive_factors = {}
        all_negative_factors = {}
        
        for p in pareto:
            for f in p.get('positive_factors', []):
                cat = f.get('category', 'unknown')
                all_positive_factors[cat] = all_positive_factors.get(cat, 0) + f.get('count', 0)
            for f in p.get('negative_factors', []):
                cat = f.get('category', 'unknown')
                all_negative_factors[cat] = all_negative_factors.get(cat, 0) + f.get('count', 0)
        
        return {
            'sessions': pareto,
            'aggregated_positive': sorted(
                [{'category': k, 'count': v} for k, v in all_positive_factors.items()],
                key=lambda x: x['count'], reverse=True
            ),
            'aggregated_negative': sorted(
                [{'category': k, 'count': v} for k, v in all_negative_factors.items()],
                key=lambda x: x['count'], reverse=True
            )
        }
    
    async def get_comparison_data(self) -> Dict[str, Any]:
        """비교 분석 데이터 조회 - analysis_sessions 기반"""
        # analysis_sessions에서 최근 세션들 가져오기
        sessions = await self.db.analysis_sessions.find(
            {}, {'_id': 0}
        ).sort('created_at', -1).limit(20).to_list(20)
        
        # 비교 데이터 형식으로 변환
        comparisons = []
        total_positive = 0
        total_fairness = 0
        total_balance = 0
        
        for session in sessions:
            result = session.get('result', {})
            sentiment_dist = result.get('sentiment_distribution', {})
            gvic_result = result.get('gvic_result', {})
            
            total_records = sentiment_dist.get('total', 0) or session.get('total_records', 0)
            positive = sentiment_dist.get('positive', 0)
            
            positive_ratio = positive / total_records if total_records > 0 else 0
            fairness_index = gvic_result.get('fairness_index', 0.5)
            balance_index = gvic_result.get('balance_index', 0.5)
            
            comparisons.append({
                'session_id': session.get('session_id'),
                'product_name': session.get('product_name', '분석 세션'),
                'source_url': session.get('source_url'),
                'analyzed_at': session.get('created_at'),
                'metrics': {
                    'total_records': total_records,
                    'positive_ratio': positive_ratio,
                    'fairness_index': fairness_index,
                    'balance_index': balance_index
                }
            })
            
            total_positive += positive_ratio
            total_fairness += fairness_index
            total_balance += balance_index
        
        count = len(comparisons)
        average_metrics = {
            'positive_ratio': total_positive / count if count > 0 else 0,
            'fairness_index': total_fairness / count if count > 0 else 0,
            'balance_index': total_balance / count if count > 0 else 0
        }
        
        return {
            'comparisons': comparisons,
            'total_sessions': count,
            'average_metrics': average_metrics
        }
    
    async def get_alerts(self, unread_only: bool = False) -> List[Dict]:
        """알림 조회"""
        query = {'read': False} if unread_only else {}
        alerts = await self.db.alerts.find(
            query, {'_id': 0}
        ).sort('timestamp', -1).limit(50).to_list(50)
        
        return alerts


# 싱글톤 인스턴스 (server.py에서 초기화)
data_hub: Optional[GVICDataHub] = None


def init_data_hub(db) -> GVICDataHub:
    """데이터 허브 초기화"""
    global data_hub
    data_hub = GVICDataHub(db)
    return data_hub


def get_data_hub() -> GVICDataHub:
    """데이터 허브 인스턴스 반환"""
    return data_hub
