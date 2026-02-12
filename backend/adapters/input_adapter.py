"""
GVIC Input Adapter - 입력부 표준화 모듈
========================================
외부 시스템에서 들어오는 다양한 형태의 시그널을 
GVIC 엔진이 처리할 수 있는 표준 포맷으로 변환

입력 유형:
- URL 크롤링 (상품 후기, 뉴스, SNS 등)
- 파일 업로드 (Excel, CSV, JSON)
- API 연동 (REST API, Webhook)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime
import pandas as pd
import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)


class InputSourceType(Enum):
    """입력 소스 유형"""
    URL_CRAWL = "url_crawl"           # URL 크롤링
    FILE_UPLOAD = "file_upload"       # 파일 업로드
    API_WEBHOOK = "api_webhook"       # API/웹훅
    STREAM = "stream"                 # 실시간 스트림


class DataDomain(Enum):
    """데이터 도메인 (분야)"""
    PRODUCT_REVIEW = "product_review"   # 상품 후기
    NEWS_ARTICLE = "news_article"       # 뉴스 기사
    SOCIAL_MEDIA = "social_media"       # 소셜 미디어
    SENSOR_DATA = "sensor_data"         # 센서 데이터
    FINANCIAL = "financial"             # 금융 데이터
    CUSTOM = "custom"                   # 사용자 정의


@dataclass
class StandardInputRecord:
    """GVIC 표준 입력 레코드"""
    record_id: str                      # 고유 ID
    source_type: InputSourceType        # 입력 유형
    domain: DataDomain                  # 데이터 도메인
    timestamp: str                      # 수집 시간
    
    # 핵심 데이터 필드 (GVIC 엔진 입력용)
    primary_value: float               # 주요 값 (예: 평점)
    content: str                       # 텍스트 내용
    
    # 분류/분석용 필드
    category: str = ""                 # 카테고리
    sentiment_hint: str = ""           # 감성 힌트 (positive/neutral/negative)
    
    # 메타데이터
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 원본 데이터 참조
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "source_type": self.source_type.value,
            "domain": self.domain.value,
            "timestamp": self.timestamp,
            "primary_value": self.primary_value,
            "content": self.content,
            "category": self.category,
            "sentiment_hint": self.sentiment_hint,
            "metadata": self.metadata,
            "raw_data": self.raw_data
        }


@dataclass
class StandardInputBatch:
    """GVIC 표준 입력 배치"""
    batch_id: str
    source_info: Dict[str, Any]         # 소스 정보
    domain: DataDomain
    records: List[StandardInputRecord]
    created_at: str
    
    # 배치 메타데이터
    total_count: int = 0
    valid_count: int = 0
    invalid_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "source_info": self.source_info,
            "domain": self.domain.value,
            "records": [r.to_dict() for r in self.records],
            "created_at": self.created_at,
            "total_count": self.total_count,
            "valid_count": self.valid_count,
            "invalid_count": self.invalid_count
        }


class InputAdapter(ABC):
    """입력 어댑터 추상 클래스"""
    
    @abstractmethod
    def load(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """원본 데이터 로드"""
        pass
    
    @abstractmethod
    def transform(self, raw_data: List[Dict[str, Any]]) -> StandardInputBatch:
        """표준 포맷으로 변환"""
        pass
    
    def process(self, source: str, **kwargs) -> StandardInputBatch:
        """전체 처리 (로드 + 변환)"""
        raw_data = self.load(source, **kwargs)
        return self.transform(raw_data)


class ProductReviewAdapter(InputAdapter):
    """
    상품 후기 입력 어댑터
    - URL 크롤링 또는 파일에서 상품 후기 데이터를 표준 포맷으로 변환
    """
    
    def __init__(self):
        self.domain = DataDomain.PRODUCT_REVIEW
        self.field_mapping = {
            # 원본 필드명 -> 표준 필드명
            "rating": "primary_value",
            "content": "content",
            "review_id": "record_id",
            "reviewer_id": "author",
            "review_date": "timestamp",
            "helpful_count": "engagement_score",
            "is_repurchase": "is_repeat",
            "mentions_effect": "mentions_effect",
            "mentions_package": "mentions_package"
        }
    
    def load(self, source: str, **kwargs) -> List[Dict[str, Any]]:
        """데이터 로드 (파일 또는 URL)"""
        if source.startswith("http://") or source.startswith("https://"):
            return self._load_from_url(source, **kwargs)
        elif source.endswith(".xlsx") or source.endswith(".xls"):
            return self._load_from_excel(source)
        elif source.endswith(".csv"):
            return self._load_from_csv(source)
        elif source.endswith(".json"):
            return self._load_from_json(source)
        else:
            raise ValueError(f"Unsupported source format: {source}")
    
    def _load_from_excel(self, filepath: str) -> List[Dict[str, Any]]:
        """엑셀 파일 로드"""
        df = pd.read_excel(filepath)
        return df.to_dict('records')
    
    def _load_from_csv(self, filepath: str) -> List[Dict[str, Any]]:
        """CSV 파일 로드"""
        df = pd.read_csv(filepath)
        return df.to_dict('records')
    
    def _load_from_json(self, filepath: str) -> List[Dict[str, Any]]:
        """JSON 파일 로드"""
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_from_url(self, url: str, **kwargs) -> List[Dict[str, Any]]:
        """URL에서 크롤링 (확장 가능)"""
        # TODO: 실제 크롤링 로직 구현
        # 현재는 샘플 데이터 반환
        logger.info(f"URL 크롤링: {url}")
        return []
    
    def transform(self, raw_data: List[Dict[str, Any]]) -> StandardInputBatch:
        """표준 포맷으로 변환"""
        batch_id = str(uuid.uuid4())[:8]
        records = []
        valid_count = 0
        invalid_count = 0
        
        for idx, raw in enumerate(raw_data):
            try:
                # 평점을 0-100 스케일로 정규화
                rating = raw.get("rating", 0)
                normalized_value = (rating / 5.0) * 100 if rating else 0
                
                # 감성 힌트 결정
                if rating >= 4:
                    sentiment_hint = "positive"
                elif rating == 3:
                    sentiment_hint = "neutral"
                else:
                    sentiment_hint = "negative"
                
                record = StandardInputRecord(
                    record_id=raw.get("review_id", f"R{batch_id}_{idx:04d}"),
                    source_type=InputSourceType.FILE_UPLOAD,
                    domain=self.domain,
                    timestamp=raw.get("review_date", datetime.now().isoformat()),
                    primary_value=normalized_value,
                    content=raw.get("content", ""),
                    category=raw.get("skin_type", ""),
                    sentiment_hint=sentiment_hint,
                    metadata={
                        "original_rating": rating,
                        "author": raw.get("reviewer_id", ""),
                        "engagement_score": raw.get("helpful_count", 0),
                        "is_repeat_purchase": raw.get("is_repurchase", False),
                        "has_photo": raw.get("has_photo", False),
                        "review_length": raw.get("review_length", 0),
                        "mentions_effect": raw.get("mentions_effect", False),
                        "mentions_package": raw.get("mentions_package", False),
                        "age_group": raw.get("age_group", ""),
                        "product_option": raw.get("purchase_option", "")
                    },
                    raw_data=raw
                )
                records.append(record)
                valid_count += 1
                
            except Exception as e:
                logger.error(f"Record transformation failed: {e}")
                invalid_count += 1
        
        # 배치 생성
        batch = StandardInputBatch(
            batch_id=batch_id,
            source_info={
                "adapter": "ProductReviewAdapter",
                "domain": self.domain.value,
                "field_mapping": self.field_mapping
            },
            domain=self.domain,
            records=records,
            created_at=datetime.now().isoformat(),
            total_count=len(raw_data),
            valid_count=valid_count,
            invalid_count=invalid_count
        )
        
        return batch


class InputAdapterFactory:
    """입력 어댑터 팩토리"""
    
    _adapters = {
        DataDomain.PRODUCT_REVIEW: ProductReviewAdapter,
        # 확장: 다른 도메인 어댑터 추가
        # DataDomain.NEWS_ARTICLE: NewsArticleAdapter,
        # DataDomain.SENSOR_DATA: SensorDataAdapter,
    }
    
    @classmethod
    def get_adapter(cls, domain: DataDomain) -> InputAdapter:
        """도메인에 맞는 어댑터 반환"""
        adapter_class = cls._adapters.get(domain)
        if not adapter_class:
            raise ValueError(f"No adapter for domain: {domain}")
        return adapter_class()
    
    @classmethod
    def register_adapter(cls, domain: DataDomain, adapter_class):
        """새 어댑터 등록"""
        cls._adapters[domain] = adapter_class


# ==================== 사용 예시 ====================
def example_usage():
    """
    사용 예시:
    
    # 1. 어댑터 생성
    adapter = InputAdapterFactory.get_adapter(DataDomain.PRODUCT_REVIEW)
    
    # 2. 데이터 로드 및 변환
    batch = adapter.process("/path/to/reviews.xlsx")
    
    # 3. GVIC 엔진에 전달
    for record in batch.records:
        engine.process(record.to_dict())
    """
    pass


if __name__ == "__main__":
    # 테스트
    adapter = ProductReviewAdapter()
    
    # 샘플 데이터
    sample_data = [
        {"review_id": "R001", "rating": 5, "content": "효과가 좋아요", "helpful_count": 10},
        {"review_id": "R002", "rating": 3, "content": "보통이에요", "helpful_count": 5},
        {"review_id": "R003", "rating": 1, "content": "효과 없어요", "helpful_count": 2}
    ]
    
    batch = adapter.transform(sample_data)
    print(f"Batch ID: {batch.batch_id}")
    print(f"Total: {batch.total_count}, Valid: {batch.valid_count}")
    for r in batch.records:
        print(f"  {r.record_id}: {r.primary_value:.0f} ({r.sentiment_hint})")
