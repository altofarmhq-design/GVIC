"""
SaaS Dashboard Service - 셀러 대시보드 통합 서비스
- 리뷰/Q&A 통합 요약
- 인사이트 트렌드
- 알림 및 액션 아이템
- 성과 지표
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import os
import jwt
import logging

router = APIRouter(prefix="/api/saas/dashboard", tags=["saas-dashboard"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== Models ====================

class DashboardSummary(BaseModel):
    """대시보드 요약"""
    total_reviews: int = 0
    total_qa: int = 0
    pending_qa: int = 0
    avg_sentiment: float = 0.5
    sentiment_trend: str = "stable"
    top_issues: List[Dict[str, Any]] = []
    top_strengths: List[Dict[str, Any]] = []
    action_items: List[Dict[str, Any]] = []

class ActionItem(BaseModel):
    """액션 아이템"""
    type: str
    priority: str
    title: str
    description: str
    related_data: Optional[Dict[str, Any]] = None

# ==================== Helper Functions ====================

async def get_current_user(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="인증이 필요합니다")
    try:
        token = authorization[7:] if authorization.startswith("Bearer ") else authorization
        if not token or token in ('null', 'undefined', ''):
            raise HTTPException(status_code=401, detail="토큰이 없습니다")
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

# ==================== Dashboard Service Class ====================

class DashboardService:
    """셀러 대시보드 서비스"""
    
    def __init__(self, db):
        self.db = db
    
    async def get_overview(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """대시보드 개요"""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # 리뷰 분석 통계
        review_analyses = await self.db.review_analyses.find(
            {"user_id": user_id, "analyzed_at": {"$gte": cutoff_date}},
            {"_id": 0}
        ).to_list(100)
        
        total_reviews = sum(a.get("total_reviews", 0) for a in review_analyses)
        
        # 감성 평균
        if review_analyses:
            sentiment_scores = [a.get("sentiment", {}).get("average_score", 0.5) for a in review_analyses]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        else:
            avg_sentiment = 0.5
        
        # Q&A 통계
        total_qa = await self.db.qa_items.count_documents({"user_id": user_id})
        pending_qa = await self.db.qa_items.count_documents({"user_id": user_id, "status": "pending"})
        
        # 크롤링 통계
        crawl_count = await self.db.crawl_results.count_documents({"user_id": user_id})
        
        return {
            "review_stats": {
                "total_analyses": len(review_analyses),
                "total_reviews": total_reviews,
                "avg_sentiment": round(avg_sentiment, 2),
                "sentiment_label": "positive" if avg_sentiment >= 0.6 else ("negative" if avg_sentiment <= 0.4 else "neutral")
            },
            "qa_stats": {
                "total": total_qa,
                "pending": pending_qa,
                "answered": total_qa - pending_qa,
                "answer_rate": round((total_qa - pending_qa) / total_qa * 100, 1) if total_qa > 0 else 0
            },
            "crawl_stats": {
                "total_crawls": crawl_count
            },
            "period_days": days
        }
    
    async def get_insights_532(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """5:3:2 인사이트 집계"""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        review_analyses = await self.db.review_analyses.find(
            {"user_id": user_id, "analyzed_at": {"$gte": cutoff_date}},
            {"_id": 0, "insights_532": 1}
        ).to_list(100)
        
        customer_insights = []
        operation_insights = []
        strategy_insights = []
        
        for a in review_analyses:
            insights = a.get("insights_532", {})
            customer_insights.extend(insights.get("customer_insights", []))
            operation_insights.extend(insights.get("operation_insights", []))
            strategy_insights.extend(insights.get("strategy_insights", []))
        
        return {
            "customer_insights": {
                "count": len(customer_insights),
                "ratio": "50%",
                "items": customer_insights[:10]  # 상위 10개
            },
            "operation_insights": {
                "count": len(operation_insights),
                "ratio": "30%",
                "items": operation_insights[:10]
            },
            "strategy_insights": {
                "count": len(strategy_insights),
                "ratio": "20%",
                "items": strategy_insights[:10]
            }
        }
    
    async def get_action_items(self, user_id: str) -> List[Dict[str, Any]]:
        """액션 아이템 생성"""
        action_items = []
        
        # 미답변 Q&A 확인
        pending_qa = await self.db.qa_items.count_documents(
            {"user_id": user_id, "status": "pending"}
        )
        
        if pending_qa > 0:
            action_items.append({
                "type": "qa",
                "priority": "high" if pending_qa >= 10 else "medium",
                "title": f"미답변 Q&A {pending_qa}건",
                "description": "고객 문의에 빠른 답변이 필요합니다.",
                "action": "/qa-center",
                "count": pending_qa
            })
        
        # 최근 부정 리뷰 확인
        recent_analyses = await self.db.review_analyses.find(
            {"user_id": user_id},
            {"_id": 0, "sentiment": 1, "issues": 1, "analyzed_at": 1}
        ).sort("analyzed_at", -1).limit(5).to_list(5)
        
        for analysis in recent_analyses:
            sentiment = analysis.get("sentiment", {})
            if sentiment.get("label") == "negative":
                issues = analysis.get("issues", [])
                action_items.append({
                    "type": "review",
                    "priority": "high",
                    "title": "부정 리뷰 발생",
                    "description": f"주요 이슈: {', '.join([i['type'] for i in issues[:3]])}",
                    "action": "/review-dashboard",
                    "issues": issues[:3]
                })
                break
        
        # 반복 이슈 확인
        issue_counts = {}
        for analysis in recent_analyses:
            for issue in analysis.get("issues", []):
                issue_type = issue.get("type", "unknown")
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + issue.get("count", 1)
        
        for issue_type, count in issue_counts.items():
            if count >= 5:  # 5회 이상 반복된 이슈
                action_items.append({
                    "type": "recurring_issue",
                    "priority": "high",
                    "title": f"반복 이슈: {issue_type}",
                    "description": f"최근 {count}회 발생. 근본 원인 해결이 필요합니다.",
                    "action": "/review-dashboard",
                    "issue_type": issue_type,
                    "occurrence_count": count
                })
        
        return sorted(action_items, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3))
    
    async def get_trend_data(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """트렌드 데이터"""
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # 리뷰 분석 이력
        analyses = await self.db.review_analyses.find(
            {"user_id": user_id, "analyzed_at": {"$gte": cutoff_date}},
            {"_id": 0, "analyzed_at": 1, "sentiment": 1, "total_reviews": 1}
        ).sort("analyzed_at", 1).to_list(100)
        
        # 일별 데이터 집계
        daily_data = {}
        for a in analyses:
            date = a.get("analyzed_at", "")[:10]  # YYYY-MM-DD
            if date not in daily_data:
                daily_data[date] = {
                    "reviews": 0,
                    "sentiment_sum": 0,
                    "count": 0
                }
            daily_data[date]["reviews"] += a.get("total_reviews", 0)
            daily_data[date]["sentiment_sum"] += a.get("sentiment", {}).get("average_score", 0.5)
            daily_data[date]["count"] += 1
        
        # 트렌드 계산
        trend_data = []
        for date, data in sorted(daily_data.items()):
            avg_sentiment = data["sentiment_sum"] / data["count"] if data["count"] > 0 else 0.5
            trend_data.append({
                "date": date,
                "reviews": data["reviews"],
                "sentiment": round(avg_sentiment, 2)
            })
        
        # 트렌드 방향 판단
        if len(trend_data) >= 2:
            recent = trend_data[-min(5, len(trend_data)):]
            older = trend_data[:-min(5, len(trend_data))] if len(trend_data) > 5 else []
            
            recent_avg = sum(d["sentiment"] for d in recent) / len(recent)
            older_avg = sum(d["sentiment"] for d in older) / len(older) if older else recent_avg
            
            if recent_avg > older_avg + 0.05:
                trend_direction = "improving"
            elif recent_avg < older_avg - 0.05:
                trend_direction = "declining"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "daily_data": trend_data,
            "trend_direction": trend_direction,
            "period_days": days
        }


# ==================== API Endpoints ====================

@router.get("/overview")
async def get_dashboard_overview(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """대시보드 개요"""
    from server import db
    
    user_id = current_user.get("user_id")
    service = DashboardService(db)
    
    return await service.get_overview(user_id, days)


@router.get("/insights-532")
async def get_insights_532(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """5:3:2 인사이트"""
    from server import db
    
    user_id = current_user.get("user_id")
    service = DashboardService(db)
    
    return await service.get_insights_532(user_id, days)


@router.get("/action-items")
async def get_action_items(
    current_user: dict = Depends(get_current_user)
):
    """액션 아이템"""
    from server import db
    
    user_id = current_user.get("user_id")
    service = DashboardService(db)
    
    items = await service.get_action_items(user_id)
    
    return {
        "action_items": items,
        "total": len(items),
        "high_priority": len([i for i in items if i["priority"] == "high"])
    }


@router.get("/trends")
async def get_trends(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """트렌드 데이터"""
    from server import db
    
    user_id = current_user.get("user_id")
    service = DashboardService(db)
    
    return await service.get_trend_data(user_id, days)


@router.get("/full")
async def get_full_dashboard(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """전체 대시보드 데이터"""
    from server import db
    
    user_id = current_user.get("user_id")
    service = DashboardService(db)
    
    # 모든 데이터 통합
    overview = await service.get_overview(user_id, days)
    insights = await service.get_insights_532(user_id, days)
    action_items = await service.get_action_items(user_id)
    trends = await service.get_trend_data(user_id, days)
    
    return {
        "overview": overview,
        "insights_532": insights,
        "action_items": {
            "items": action_items,
            "total": len(action_items),
            "high_priority": len([i for i in action_items if i["priority"] == "high"])
        },
        "trends": trends,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
