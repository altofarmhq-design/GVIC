"""
GVIC Product Insight Analyzer - 4대 인사이트 분석 엔진
- 강점 분석 (유지/보강)
- 건의사항 분석 (서비스 개선)
- 불만 분석 (개선/드롭 결정)
- 신제품 욕구 분석 (신규 개발 기회)
"""
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging
import re

router = APIRouter(prefix="/api/insights", tags=["product-insights"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== Models ====================

class ReviewForAnalysis(BaseModel):
    """분석용 리뷰"""
    content: str
    rating: Optional[float] = None
    date: Optional[str] = None
    author: Optional[str] = None

class ProductAnalysisRequest(BaseModel):
    """제품 분석 요청"""
    product_id: str
    reviews: List[ReviewForAnalysis]
    analysis_depth: str = Field("standard", description="분석 깊이: quick, standard, deep")

class InsightItem(BaseModel):
    """인사이트 항목"""
    type: str
    content: str
    count: int = 1
    examples: List[str] = []
    severity: Optional[str] = None
    action: Optional[str] = None

class StrengthInsight(BaseModel):
    """강점 인사이트"""
    items: List[InsightItem]
    total_count: int
    top_strengths: List[str]
    recommendation: str
    action: str = "유지/보강"

class SuggestionInsight(BaseModel):
    """건의사항 인사이트"""
    items: List[InsightItem]
    total_count: int
    top_suggestions: List[str]
    recommendation: str
    action: str = "서비스 개선"

class ComplaintInsight(BaseModel):
    """불만 인사이트"""
    items: List[InsightItem]
    total_count: int
    severity_distribution: Dict[str, int]
    top_complaints: List[str]
    recommendation: str
    action: str = "개선 또는 드롭 검토"
    drop_recommendation: bool = False

class NewProductNeedInsight(BaseModel):
    """신제품 욕구 인사이트"""
    items: List[InsightItem]
    total_count: int
    detected_needs: List[str]
    recommendation: str
    action: str = "신제품 개발 기회"
    development_priority: str = "low"

class FourInsightResult(BaseModel):
    """4대 인사이트 결과"""
    analysis_id: str
    product_id: str
    total_reviews: int
    analysis_period: str
    strengths: StrengthInsight
    suggestions: SuggestionInsight
    complaints: ComplaintInsight
    new_product_needs: NewProductNeedInsight
    overall_score: float
    overall_trend: str
    summary: str
    analyzed_at: str

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

# ==================== 4대 인사이트 분석 엔진 ====================

class ProductInsightAnalyzer:
    """4대 인사이트 분석 엔진"""
    
    # 강점 키워드
    STRENGTH_KEYWORDS = {
        "품질": ["품질좋", "퀄리티", "고급", "튼튼", "내구성", "견고", "잘만들"],
        "가격": ["가성비", "저렴", "싸다", "합리적", "가격대비"],
        "배송": ["빠른배송", "배송빠름", "빨리도착", "다음날", "당일"],
        "디자인": ["예쁘", "이쁘", "디자인", "세련", "고급스러"],
        "기능": ["기능좋", "성능좋", "잘작동", "편리", "실용적"],
        "서비스": ["친절", "응대좋", "서비스좋", "빠른답변"],
        "재구매": ["재구매", "또살", "다시사", "추천"]
    }
    
    # 건의사항 키워드
    SUGGESTION_KEYWORDS = {
        "색상": ["색상추가", "다른색", "색깔다양", "컬러추가"],
        "사이즈": ["사이즈추가", "큰사이즈", "작은사이즈", "다양한사이즈"],
        "기능": ["기능추가", "있었으면", "됐으면", "추가해주"],
        "포장": ["포장개선", "포장보완", "상자", "완충재"],
        "가격": ["할인", "세일", "쿠폰", "가격인하"],
        "배송": ["배송옵션", "새벽배송", "빠른배송옵션"],
        "설명서": ["설명서", "매뉴얼", "사용법", "가이드"]
    }
    
    # 불만 키워드
    COMPLAINT_KEYWORDS = {
        "품질불량": ["불량", "하자", "고장", "망가", "파손", "찢어", "깨진"],
        "배송지연": ["늦은", "지연", "안와", "안옴", "느린배송"],
        "오배송": ["오배송", "잘못온", "다른제품"],
        "색상차이": ["색다름", "색상다름", "사진과다름"],
        "사이즈오류": ["사이즈다름", "크기다름", "안맞"],
        "CS불만": ["불친절", "연락안", "답변없"],
        "환불문제": ["환불안됨", "환불거부", "교환거부"]
    }
    
    # 신제품 욕구 키워드
    NEW_PRODUCT_KEYWORDS = {
        "신기능": ["있었으면", "나왔으면", "만들어", "출시해"],
        "변형제품": ["버전", "시리즈", "라인", "종류"],
        "업그레이드": ["업그레이드", "개선판", "신형", "2세대"],
        "조합제품": ["세트", "묶음", "패키지", "함께"],
        "특수용도": ["방수", "방진", "무소음", "무선", "휴대용"]
    }
    
    def __init__(self, db=None):
        self.db = db
    
    def analyze_strengths(self, reviews: List[ReviewForAnalysis]) -> StrengthInsight:
        """강점 분석"""
        strength_counts = {k: {"count": 0, "examples": []} for k in self.STRENGTH_KEYWORDS}
        
        for review in reviews:
            content = review.content.lower().replace(" ", "")
            for category, keywords in self.STRENGTH_KEYWORDS.items():
                for kw in keywords:
                    if kw in content:
                        strength_counts[category]["count"] += 1
                        if len(strength_counts[category]["examples"]) < 3:
                            strength_counts[category]["examples"].append(review.content[:100])
                        break
        
        # 결과 정리
        items = []
        for category, data in strength_counts.items():
            if data["count"] > 0:
                items.append(InsightItem(
                    type=category,
                    content=f"{category} 관련 긍정 리뷰",
                    count=data["count"],
                    examples=data["examples"],
                    action="마케팅 강조 포인트"
                ))
        
        items.sort(key=lambda x: x.count, reverse=True)
        total_count = sum(item.count for item in items)
        top_strengths = [item.type for item in items[:3]]
        
        if items:
            recommendation = f"'{top_strengths[0]}' 강점을 마케팅에 적극 활용하세요. "
            if len(top_strengths) > 1:
                recommendation += f"'{top_strengths[1]}' 역시 고객에게 어필하는 포인트입니다."
        else:
            recommendation = "뚜렷한 강점이 감지되지 않았습니다. 리뷰를 더 수집해주세요."
        
        return StrengthInsight(
            items=items,
            total_count=total_count,
            top_strengths=top_strengths,
            recommendation=recommendation,
            action="유지/보강"
        )
    
    def analyze_suggestions(self, reviews: List[ReviewForAnalysis]) -> SuggestionInsight:
        """건의사항 분석"""
        suggestion_counts = {k: {"count": 0, "examples": []} for k in self.SUGGESTION_KEYWORDS}
        
        for review in reviews:
            content = review.content.lower().replace(" ", "")
            for category, keywords in self.SUGGESTION_KEYWORDS.items():
                for kw in keywords:
                    if kw in content:
                        suggestion_counts[category]["count"] += 1
                        if len(suggestion_counts[category]["examples"]) < 3:
                            suggestion_counts[category]["examples"].append(review.content[:100])
                        break
        
        items = []
        for category, data in suggestion_counts.items():
            if data["count"] > 0:
                items.append(InsightItem(
                    type=category,
                    content=f"{category} 관련 건의",
                    count=data["count"],
                    examples=data["examples"],
                    action="서비스/제품 개선 검토"
                ))
        
        items.sort(key=lambda x: x.count, reverse=True)
        total_count = sum(item.count for item in items)
        top_suggestions = [item.type for item in items[:3]]
        
        if items:
            recommendation = f"'{top_suggestions[0]}' 관련 건의가 가장 많습니다. 개선을 검토하세요."
        else:
            recommendation = "특별한 건의사항이 감지되지 않았습니다."
        
        return SuggestionInsight(
            items=items,
            total_count=total_count,
            top_suggestions=top_suggestions,
            recommendation=recommendation,
            action="서비스 개선"
        )
    
    def analyze_complaints(self, reviews: List[ReviewForAnalysis]) -> ComplaintInsight:
        """불만 분석"""
        complaint_counts = {k: {"count": 0, "examples": [], "severity": "medium"} for k in self.COMPLAINT_KEYWORDS}
        
        # 심각도 설정
        high_severity = ["품질불량", "오배송", "환불문제"]
        
        for review in reviews:
            content = review.content.lower().replace(" ", "")
            rating = review.rating or 3
            
            for category, keywords in self.COMPLAINT_KEYWORDS.items():
                for kw in keywords:
                    if kw in content:
                        complaint_counts[category]["count"] += 1
                        if len(complaint_counts[category]["examples"]) < 3:
                            complaint_counts[category]["examples"].append(review.content[:100])
                        
                        # 심각도 판단
                        if category in high_severity or rating <= 2:
                            complaint_counts[category]["severity"] = "high"
                        break
        
        items = []
        severity_dist = {"high": 0, "medium": 0, "low": 0}
        
        for category, data in complaint_counts.items():
            if data["count"] > 0:
                items.append(InsightItem(
                    type=category,
                    content=f"{category} 관련 불만",
                    count=data["count"],
                    examples=data["examples"],
                    severity=data["severity"],
                    action="개선 필요" if data["severity"] == "high" else "모니터링"
                ))
                severity_dist[data["severity"]] += data["count"]
        
        items.sort(key=lambda x: (x.severity == "high", x.count), reverse=True)
        total_count = sum(item.count for item in items)
        top_complaints = [item.type for item in items[:3]]
        
        # 드롭 권장 여부
        drop_recommendation = False
        if severity_dist["high"] >= 5 and total_count >= 10:
            drop_recommendation = True
            recommendation = f"⚠️ 심각한 불만이 다수 감지되었습니다. '{top_complaints[0]}' 문제 해결이 시급합니다. 해결 불가 시 제품 드롭을 검토하세요."
        elif items:
            recommendation = f"'{top_complaints[0]}' 관련 불만이 가장 많습니다. 개선 방안을 마련하세요."
        else:
            recommendation = "심각한 불만이 감지되지 않았습니다."
        
        return ComplaintInsight(
            items=items,
            total_count=total_count,
            severity_distribution=severity_dist,
            top_complaints=top_complaints,
            recommendation=recommendation,
            action="개선 또는 드롭 검토",
            drop_recommendation=drop_recommendation
        )
    
    def analyze_new_product_needs(self, reviews: List[ReviewForAnalysis]) -> NewProductNeedInsight:
        """신제품 욕구 분석"""
        need_counts = {k: {"count": 0, "examples": []} for k in self.NEW_PRODUCT_KEYWORDS}
        
        # 추가 패턴 탐지
        wish_patterns = [
            r'있었으면\s*좋겠',
            r'나왔으면\s*좋겠',
            r'있으면\s*좋을',
            r'출시해\s*주',
            r'만들어\s*주',
            r'버전.*있',
            r'시리즈.*나'
        ]
        
        detected_wishes = []
        
        for review in reviews:
            content = review.content.lower().replace(" ", "")
            original_content = review.content
            
            # 키워드 기반 탐지
            for category, keywords in self.NEW_PRODUCT_KEYWORDS.items():
                for kw in keywords:
                    if kw in content:
                        need_counts[category]["count"] += 1
                        if len(need_counts[category]["examples"]) < 3:
                            need_counts[category]["examples"].append(original_content[:100])
                        break
            
            # 패턴 기반 탐지
            for pattern in wish_patterns:
                if re.search(pattern, original_content):
                    detected_wishes.append(original_content[:100])
                    break
        
        items = []
        for category, data in need_counts.items():
            if data["count"] > 0:
                items.append(InsightItem(
                    type=category,
                    content=f"{category} 관련 욕구",
                    count=data["count"],
                    examples=data["examples"],
                    action="신제품 개발 검토"
                ))
        
        items.sort(key=lambda x: x.count, reverse=True)
        total_count = sum(item.count for item in items) + len(detected_wishes)
        detected_needs = [item.type for item in items[:3]]
        
        # 개발 우선순위
        if total_count >= 10:
            development_priority = "high"
        elif total_count >= 5:
            development_priority = "medium"
        else:
            development_priority = "low"
        
        if items:
            recommendation = f"'{detected_needs[0]}' 관련 신제품 욕구가 감지되었습니다. 개발 타당성을 검토하세요."
        else:
            recommendation = "뚜렷한 신제품 욕구가 감지되지 않았습니다."
        
        return NewProductNeedInsight(
            items=items,
            total_count=total_count,
            detected_needs=detected_needs,
            recommendation=recommendation,
            action="신제품 개발 기회",
            development_priority=development_priority
        )
    
    def calculate_overall_score(
        self,
        reviews: List[ReviewForAnalysis],
        strengths: StrengthInsight,
        complaints: ComplaintInsight
    ) -> float:
        """종합 점수 계산"""
        # 평점 기반 점수 (있는 경우)
        ratings = [r.rating for r in reviews if r.rating is not None]
        if ratings:
            rating_score = (sum(ratings) / len(ratings)) * 20  # 0-100 스케일
        else:
            rating_score = 50
        
        # 강점 점수
        strength_score = min(strengths.total_count * 2, 30)
        
        # 불만 감점
        complaint_penalty = min(complaints.total_count * 3, 40)
        if complaints.drop_recommendation:
            complaint_penalty += 20
        
        overall = rating_score + strength_score - complaint_penalty
        return max(0, min(100, overall))
    
    def determine_trend(self, reviews: List[ReviewForAnalysis]) -> str:
        """트렌드 판단"""
        if len(reviews) < 5:
            return "insufficient_data"
        
        # 날짜가 있는 리뷰 정렬
        dated_reviews = [r for r in reviews if r.date]
        if len(dated_reviews) < 5:
            return "unknown"
        
        # 최근 절반 vs 이전 절반 비교
        mid = len(dated_reviews) // 2
        recent = dated_reviews[:mid]
        older = dated_reviews[mid:]
        
        recent_ratings = [r.rating for r in recent if r.rating]
        older_ratings = [r.rating for r in older if r.rating]
        
        if not recent_ratings or not older_ratings:
            return "unknown"
        
        recent_avg = sum(recent_ratings) / len(recent_ratings)
        older_avg = sum(older_ratings) / len(older_ratings)
        
        if recent_avg > older_avg + 0.3:
            return "improving"
        elif recent_avg < older_avg - 0.3:
            return "declining"
        else:
            return "stable"
    
    async def analyze(
        self,
        product_id: str,
        reviews: List[ReviewForAnalysis],
        analysis_depth: str = "standard"
    ) -> FourInsightResult:
        """4대 인사이트 통합 분석"""
        analysis_id = f"INS_{uuid.uuid4().hex[:12]}"
        
        # 4대 인사이트 분석
        strengths = self.analyze_strengths(reviews)
        suggestions = self.analyze_suggestions(reviews)
        complaints = self.analyze_complaints(reviews)
        new_product_needs = self.analyze_new_product_needs(reviews)
        
        # 종합 점수 및 트렌드
        overall_score = self.calculate_overall_score(reviews, strengths, complaints)
        overall_trend = self.determine_trend(reviews)
        
        # 요약 생성
        summary_parts = [f"총 {len(reviews)}개 리뷰 분석 완료."]
        
        if strengths.top_strengths:
            summary_parts.append(f"💪 강점: {', '.join(strengths.top_strengths[:2])}")
        
        if complaints.drop_recommendation:
            summary_parts.append(f"⚠️ 심각: 제품 드롭 검토 필요")
        elif complaints.top_complaints:
            summary_parts.append(f"⚠️ 주의: {complaints.top_complaints[0]} 개선 필요")
        
        if new_product_needs.development_priority in ["high", "medium"]:
            summary_parts.append(f"🚀 기회: 신제품 욕구 감지")
        
        summary = " ".join(summary_parts)
        
        # 분석 기간 (리뷰 날짜 기반)
        dates = [r.date for r in reviews if r.date]
        if dates:
            analysis_period = f"{min(dates)} ~ {max(dates)}"
        else:
            analysis_period = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        return FourInsightResult(
            analysis_id=analysis_id,
            product_id=product_id,
            total_reviews=len(reviews),
            analysis_period=analysis_period,
            strengths=strengths,
            suggestions=suggestions,
            complaints=complaints,
            new_product_needs=new_product_needs,
            overall_score=round(overall_score, 1),
            overall_trend=overall_trend,
            summary=summary,
            analyzed_at=datetime.now(timezone.utc).isoformat()
        )


# ==================== API Endpoints ====================

@router.post("/analyze", response_model=FourInsightResult)
async def analyze_product_insights(
    request: ProductAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    제품 4대 인사이트 분석
    
    - 강점: 유지/보강할 포인트
    - 건의사항: 서비스 개선 포인트
    - 불만: 개선 또는 드롭 결정
    - 신제품 욕구: 신규 개발 기회
    """
    from server import db
    
    user_id = current_user.get("user_id")
    
    analyzer = ProductInsightAnalyzer(db)
    result = await analyzer.analyze(
        product_id=request.product_id,
        reviews=request.reviews,
        analysis_depth=request.analysis_depth
    )
    
    # DB에 저장
    await db.product_analyses.insert_one({
        "analysis_id": result.analysis_id,
        "product_id": result.product_id,
        "user_id": user_id,
        "total_reviews": result.total_reviews,
        "analysis_period": result.analysis_period,
        "strengths": result.strengths.dict(),
        "suggestions": result.suggestions.dict(),
        "complaints": result.complaints.dict(),
        "new_product_needs": result.new_product_needs.dict(),
        "overall_score": result.overall_score,
        "overall_trend": result.overall_trend,
        "summary": result.summary,
        "analyzed_at": result.analyzed_at
    })
    
    # 제품 정보 업데이트
    await db.shop_products.update_one(
        {"product_id": request.product_id},
        {"$set": {
            "last_analysis": result.analyzed_at,
            "latest_insights": {
                "analysis_id": result.analysis_id,
                "overall_score": result.overall_score,
                "summary": result.summary
            },
            "total_reviews_analyzed": result.total_reviews
        }}
    )
    
    return result


@router.get("/product/{product_id}")
async def get_product_insights(
    product_id: str,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """제품 분석 이력 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    analyses = await db.product_analyses.find(
        {"product_id": product_id, "user_id": user_id},
        {"_id": 0}
    ).sort("analyzed_at", -1).limit(limit).to_list(limit)
    
    return {
        "product_id": product_id,
        "analyses": analyses,
        "total": len(analyses)
    }


@router.get("/analysis/{analysis_id}")
async def get_analysis_detail(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """분석 결과 상세 조회"""
    from server import db
    
    analysis = await db.product_analyses.find_one(
        {"analysis_id": analysis_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
    
    return analysis


@router.post("/product/{product_id}/analyze-now")
async def analyze_product_now(
    product_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    제품 즉시 분석 (크롤링 + 분석)
    """
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 제품 조회
    product = await db.shop_products.find_one(
        {"product_id": product_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")
    
    product_url = product.get("product_url")
    if not product_url:
        raise HTTPException(status_code=400, detail="제품 URL이 없습니다")
    
    # 크롤링 및 분석 (동기 실행)
    from review_crawler import detect_platform, crawl_naver_reviews, crawl_coupang_reviews, crawl_generic_reviews
    
    platform = detect_platform(product_url)
    
    try:
        if platform == "naver":
            _, reviews = await crawl_naver_reviews(product_url, 100)
        elif platform == "coupang":
            _, reviews = await crawl_coupang_reviews(product_url, 100)
        else:
            _, reviews = await crawl_generic_reviews(product_url, 100)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"크롤링 실패: {str(e)}")
    
    if not reviews:
        raise HTTPException(status_code=400, detail="리뷰를 찾을 수 없습니다")
    
    # 분석 실행
    review_inputs = [
        ReviewForAnalysis(
            content=r.content,
            rating=r.rating,
            date=r.date,
            author=r.author
        )
        for r in reviews
    ]
    
    analyzer = ProductInsightAnalyzer(db)
    result = await analyzer.analyze(
        product_id=product_id,
        reviews=review_inputs,
        analysis_depth="standard"
    )
    
    # DB 저장
    await db.product_analyses.insert_one({
        "analysis_id": result.analysis_id,
        "product_id": product_id,
        "user_id": user_id,
        "total_reviews": result.total_reviews,
        "analysis_period": result.analysis_period,
        "strengths": result.strengths.dict(),
        "suggestions": result.suggestions.dict(),
        "complaints": result.complaints.dict(),
        "new_product_needs": result.new_product_needs.dict(),
        "overall_score": result.overall_score,
        "overall_trend": result.overall_trend,
        "summary": result.summary,
        "analyzed_at": result.analyzed_at
    })
    
    # 제품 정보 업데이트
    await db.shop_products.update_one(
        {"product_id": product_id},
        {"$set": {
            "last_analysis": result.analyzed_at,
            "latest_insights": {
                "analysis_id": result.analysis_id,
                "overall_score": result.overall_score,
                "summary": result.summary
            },
            "total_reviews_analyzed": result.total_reviews
        }}
    )
    
    return {
        "success": True,
        "analysis_id": result.analysis_id,
        "reviews_analyzed": result.total_reviews,
        "overall_score": result.overall_score,
        "summary": result.summary,
        "insights": {
            "strengths": len(result.strengths.items),
            "suggestions": len(result.suggestions.items),
            "complaints": len(result.complaints.items),
            "new_product_needs": len(result.new_product_needs.items)
        }
    }
