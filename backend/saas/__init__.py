"""
GVIC SaaS Module - Seller Intelligence Hub
이커머스 셀러를 위한 AI 인사이트 플랫폼

핵심 모듈:
- review_analyzer: 리뷰 분석 및 인사이트 도출
- qa_manager: Q&A/CS 통합 관리
- dashboard_service: 셀러 대시보드 데이터
- shop_manager: 쇼핑몰/제품 관리, API 키 발급
- product_insights: 4대 인사이트 분석 (강점/건의/불만/신제품욕구)
"""

from .review_analyzer import ReviewAnalyzer, router as review_router
from .qa_manager import QAManager, router as qa_router
from .dashboard_service import DashboardService, router as dashboard_router
from .shop_manager import router as shop_router
from .product_insights import ProductInsightAnalyzer, router as insights_router

__all__ = [
    'ReviewAnalyzer',
    'QAManager', 
    'DashboardService',
    'ProductInsightAnalyzer',
    'review_router',
    'qa_router',
    'dashboard_router',
    'shop_router',
    'insights_router'
]
