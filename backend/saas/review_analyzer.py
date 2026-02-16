"""
SaaS Review Analyzer - 이커머스 리뷰 분석 엔진
- 리뷰 감성 분석
- 핵심 키워드 추출
- 상품 특성 파악
- 문제점/개선점 도출
- 5:3:2 인사이트 분류 (고객/운영/전략)
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging
import re

router = APIRouter(prefix="/api/saas/reviews", tags=["saas-reviews"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== Models ====================

class ReviewInput(BaseModel):
    """리뷰 입력"""
    content: str = Field(..., description="리뷰 내용")
    rating: Optional[float] = Field(None, description="평점 (1-5)")
    platform: str = Field("unknown", description="플랫폼 (naver, coupang, etc)")
    product_name: Optional[str] = Field(None, description="상품명")
    author: Optional[str] = Field(None, description="작성자")
    date: Optional[str] = Field(None, description="작성일")

class BatchReviewRequest(BaseModel):
    """배치 리뷰 분석 요청"""
    reviews: List[ReviewInput]
    product_id: Optional[str] = None
    analysis_depth: str = Field("standard", description="분석 깊이: quick, standard, deep")

class InsightCategory(BaseModel):
    """5:3:2 인사이트 카테고리"""
    customer_insights: List[Dict[str, Any]] = Field(default_factory=list, description="고객 인사이트 (50%)")
    operation_insights: List[Dict[str, Any]] = Field(default_factory=list, description="운영 인사이트 (30%)")
    strategy_insights: List[Dict[str, Any]] = Field(default_factory=list, description="전략 인사이트 (20%)")

class ReviewAnalysisResult(BaseModel):
    """리뷰 분석 결과"""
    analysis_id: str
    total_reviews: int
    sentiment: Dict[str, Any]
    keywords: List[Dict[str, Any]]
    product_features: List[Dict[str, Any]]
    issues: List[Dict[str, Any]]
    strengths: List[Dict[str, Any]]
    insights_532: InsightCategory
    summary: str
    recommendations: List[str]
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

# ==================== Review Analyzer Class ====================

class ReviewAnalyzer:
    """이커머스 리뷰 분석기"""
    
    # 감성 키워드
    POSITIVE_KEYWORDS = [
        "좋아요", "좋습니다", "만족", "최고", "추천", "빠른", "깔끔", "예쁘", "튼튼",
        "가성비", "친절", "편리", "훌륭", "대박", "재구매", "강추", "품질", "만점",
        "퀄리티", "고급", "세련", "완벽", "훌륭", "감사", "사랑"
    ]
    
    NEGATIVE_KEYWORDS = [
        "별로", "실망", "불만", "느린", "비싸", "불량", "하자", "교환", "환불",
        "안좋", "최악", "짜증", "후회", "구림", "쓰레기", "망", "낭비", "불친절",
        "답답", "늦은", "파손", "찢어", "고장"
    ]
    
    # 상품 특성 키워드
    FEATURE_CATEGORIES = {
        "품질": ["품질", "퀄리티", "재질", "소재", "내구성", "튼튼", "견고"],
        "배송": ["배송", "도착", "택배", "빠른", "느린", "포장"],
        "가격": ["가격", "가성비", "비싸", "저렴", "할인", "이벤트"],
        "디자인": ["디자인", "색상", "색깔", "예쁘", "스타일", "모양"],
        "사이즈": ["사이즈", "크기", "작은", "큰", "딱맞", "넉넉"],
        "서비스": ["친절", "응대", "CS", "문의", "답변", "서비스"]
    }
    
    def __init__(self, db=None):
        self.db = db
    
    def analyze_sentiment(self, content: str) -> Dict[str, Any]:
        """감성 분석"""
        content_lower = content.lower()
        
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in content_lower)
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in content_lower)
        
        total = positive_count + negative_count
        if total == 0:
            sentiment_score = 0.5
            sentiment_label = "neutral"
        else:
            sentiment_score = positive_count / total
            if sentiment_score >= 0.7:
                sentiment_label = "positive"
            elif sentiment_score <= 0.3:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
        
        return {
            "score": round(sentiment_score, 2),
            "label": sentiment_label,
            "positive_count": positive_count,
            "negative_count": negative_count
        }
    
    def extract_keywords(self, content: str, top_n: int = 10) -> List[Dict[str, Any]]:
        """핵심 키워드 추출"""
        # 간단한 키워드 빈도 분석
        # 실제로는 형태소 분석기 사용 권장
        words = re.findall(r'[가-힣]+', content)
        
        # 불용어 제거
        stopwords = ["이", "그", "저", "것", "수", "등", "들", "및", "를", "에", "의", "가", "은", "는", "도", "로", "와", "과"]
        words = [w for w in words if len(w) >= 2 and w not in stopwords]
        
        # 빈도 계산
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 정렬 및 상위 N개 선택
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return [
            {"keyword": word, "count": count, "importance": round(count / len(words) * 100, 1) if words else 0}
            for word, count in sorted_words
        ]
    
    def extract_features(self, content: str) -> List[Dict[str, Any]]:
        """상품 특성 추출"""
        features = []
        content_lower = content.lower()
        
        for category, keywords in self.FEATURE_CATEGORIES.items():
            mentions = sum(1 for kw in keywords if kw in content_lower)
            if mentions > 0:
                # 해당 카테고리의 감성 파악
                sentiment = self.analyze_sentiment(content)
                features.append({
                    "category": category,
                    "mentions": mentions,
                    "sentiment": sentiment["label"],
                    "keywords_found": [kw for kw in keywords if kw in content_lower]
                })
        
        return sorted(features, key=lambda x: x["mentions"], reverse=True)
    
    def identify_issues(self, content: str) -> List[Dict[str, Any]]:
        """문제점 식별"""
        issues = []
        content_lower = content.lower()
        
        issue_patterns = {
            "배송 지연": ["늦은", "지연", "안와", "안옴", "느린배송"],
            "품질 불량": ["불량", "하자", "고장", "망가", "찢어", "파손"],
            "사이즈 불일치": ["작아", "커요", "안맞", "사이즈다름"],
            "색상 차이": ["색상다름", "색깔차이", "다른색"],
            "포장 문제": ["포장", "박스", "찌그러", "훼손"],
            "CS 불만": ["불친절", "답변없", "연락안"],
            "가격 불만": ["비싸", "가격", "바가지"]
        }
        
        for issue_type, patterns in issue_patterns.items():
            matches = [p for p in patterns if p in content_lower]
            if matches:
                issues.append({
                    "type": issue_type,
                    "severity": "high" if len(matches) >= 2 else "medium",
                    "patterns_found": matches,
                    "action_needed": True
                })
        
        return issues
    
    def identify_strengths(self, content: str) -> List[Dict[str, Any]]:
        """강점 식별"""
        strengths = []
        content_lower = content.lower()
        
        strength_patterns = {
            "빠른 배송": ["빠른배송", "빨리", "바로도착", "다음날"],
            "우수한 품질": ["품질좋", "퀄리티", "고급", "튼튼"],
            "합리적 가격": ["가성비", "저렴", "싸게", "할인"],
            "예쁜 디자인": ["예쁘", "이쁘", "디자인", "세련"],
            "친절한 서비스": ["친절", "응대", "감사"],
            "재구매 의향": ["재구매", "또살", "다시"]
        }
        
        for strength_type, patterns in strength_patterns.items():
            matches = [p for p in patterns if p in content_lower]
            if matches:
                strengths.append({
                    "type": strength_type,
                    "confidence": "high" if len(matches) >= 2 else "medium",
                    "patterns_found": matches
                })
        
        return strengths
    
    def classify_insights_532(self, reviews: List[ReviewInput], analysis_results: Dict) -> InsightCategory:
        """5:3:2 인사이트 분류
        - 고객 인사이트 (50%): 고객 만족/불만, 니즈, 선호도
        - 운영 인사이트 (30%): 배송, CS, 재고, 포장
        - 전략 인사이트 (20%): 가격, 경쟁사, 시장 트렌드
        """
        customer_insights = []
        operation_insights = []
        strategy_insights = []
        
        # 감성 분석 기반 고객 인사이트
        sentiment = analysis_results.get("sentiment", {})
        if sentiment.get("label") == "positive":
            customer_insights.append({
                "type": "satisfaction",
                "title": "높은 고객 만족도",
                "detail": f"긍정 비율 {sentiment.get('score', 0)*100:.0f}%로 고객 만족도가 높습니다.",
                "priority": "info"
            })
        elif sentiment.get("label") == "negative":
            customer_insights.append({
                "type": "dissatisfaction",
                "title": "고객 불만 주의",
                "detail": f"부정 비율이 높습니다. 원인 파악이 필요합니다.",
                "priority": "high"
            })
        
        # 이슈 기반 운영 인사이트
        issues = analysis_results.get("issues", [])
        for issue in issues:
            if issue["type"] in ["배송 지연", "포장 문제", "CS 불만"]:
                operation_insights.append({
                    "type": "operation_issue",
                    "title": f"{issue['type']} 개선 필요",
                    "detail": f"고객 리뷰에서 {issue['type']} 관련 불만이 감지되었습니다.",
                    "priority": issue.get("severity", "medium"),
                    "action": "운영 프로세스 점검 필요"
                })
        
        # 강점 기반 전략 인사이트
        strengths = analysis_results.get("strengths", [])
        for strength in strengths:
            if strength["type"] in ["합리적 가격", "예쁜 디자인"]:
                strategy_insights.append({
                    "type": "competitive_advantage",
                    "title": f"{strength['type']} - 경쟁 우위",
                    "detail": f"'{strength['type']}'이 핵심 강점입니다. 마케팅에 활용하세요.",
                    "priority": "info",
                    "action": "마케팅 포인트로 강조"
                })
        
        # 가격 관련 전략 인사이트
        for issue in issues:
            if issue["type"] == "가격 불만":
                strategy_insights.append({
                    "type": "pricing",
                    "title": "가격 정책 검토",
                    "detail": "가격에 대한 불만이 있습니다. 가격 정책 또는 가치 전달 개선이 필요합니다.",
                    "priority": "medium",
                    "action": "경쟁사 가격 분석 및 가치 제안 강화"
                })
        
        return InsightCategory(
            customer_insights=customer_insights,
            operation_insights=operation_insights,
            strategy_insights=strategy_insights
        )
    
    async def analyze_reviews(
        self, 
        reviews: List[ReviewInput], 
        analysis_depth: str = "standard"
    ) -> ReviewAnalysisResult:
        """리뷰 배치 분석"""
        analysis_id = f"RA_{uuid.uuid4().hex[:12]}"
        
        # 전체 콘텐츠 합치기
        all_content = " ".join([r.content for r in reviews])
        
        # 개별 리뷰 감성 분석
        individual_sentiments = [self.analyze_sentiment(r.content) for r in reviews]
        
        # 전체 감성 집계
        positive_count = sum(1 for s in individual_sentiments if s["label"] == "positive")
        negative_count = sum(1 for s in individual_sentiments if s["label"] == "negative")
        neutral_count = sum(1 for s in individual_sentiments if s["label"] == "neutral")
        
        overall_sentiment = {
            "positive_ratio": round(positive_count / len(reviews), 2) if reviews else 0,
            "negative_ratio": round(negative_count / len(reviews), 2) if reviews else 0,
            "neutral_ratio": round(neutral_count / len(reviews), 2) if reviews else 0,
            "average_score": round(sum(s["score"] for s in individual_sentiments) / len(individual_sentiments), 2) if individual_sentiments else 0,
            "label": "positive" if positive_count > negative_count else ("negative" if negative_count > positive_count else "neutral"),
            "distribution": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": neutral_count
            }
        }
        
        # 평점 통계 (있는 경우)
        ratings = [r.rating for r in reviews if r.rating is not None]
        if ratings:
            overall_sentiment["rating_average"] = round(sum(ratings) / len(ratings), 1)
            overall_sentiment["rating_count"] = len(ratings)
        
        # 키워드 추출
        keywords = self.extract_keywords(all_content, top_n=15)
        
        # 상품 특성 분석
        features = self.extract_features(all_content)
        
        # 문제점 식별
        all_issues = []
        for review in reviews:
            issues = self.identify_issues(review.content)
            all_issues.extend(issues)
        
        # 이슈 집계
        issue_counts = {}
        for issue in all_issues:
            key = issue["type"]
            if key not in issue_counts:
                issue_counts[key] = {"type": key, "count": 0, "severity": issue["severity"]}
            issue_counts[key]["count"] += 1
        
        aggregated_issues = sorted(issue_counts.values(), key=lambda x: x["count"], reverse=True)
        
        # 강점 식별
        all_strengths = []
        for review in reviews:
            strengths = self.identify_strengths(review.content)
            all_strengths.extend(strengths)
        
        # 강점 집계
        strength_counts = {}
        for strength in all_strengths:
            key = strength["type"]
            if key not in strength_counts:
                strength_counts[key] = {"type": key, "count": 0}
            strength_counts[key]["count"] += 1
        
        aggregated_strengths = sorted(strength_counts.values(), key=lambda x: x["count"], reverse=True)
        
        # 분석 결과 딕셔너리
        analysis_results = {
            "sentiment": overall_sentiment,
            "issues": aggregated_issues,
            "strengths": aggregated_strengths
        }
        
        # 5:3:2 인사이트 분류
        insights_532 = self.classify_insights_532(reviews, analysis_results)
        
        # AI 심층 분석 (deep 모드)
        ai_summary = ""
        ai_recommendations = []
        
        if analysis_depth == "deep":
            ai_result = await self._ai_deep_analysis(reviews, analysis_results)
            ai_summary = ai_result.get("summary", "")
            ai_recommendations = ai_result.get("recommendations", [])
        else:
            # 기본 요약 생성
            ai_summary = self._generate_basic_summary(overall_sentiment, aggregated_issues, aggregated_strengths, len(reviews))
            ai_recommendations = self._generate_basic_recommendations(aggregated_issues, aggregated_strengths)
        
        return ReviewAnalysisResult(
            analysis_id=analysis_id,
            total_reviews=len(reviews),
            sentiment=overall_sentiment,
            keywords=keywords,
            product_features=features,
            issues=aggregated_issues,
            strengths=aggregated_strengths,
            insights_532=insights_532,
            summary=ai_summary,
            recommendations=ai_recommendations,
            analyzed_at=datetime.now(timezone.utc).isoformat()
        )
    
    def _generate_basic_summary(
        self, 
        sentiment: Dict, 
        issues: List, 
        strengths: List, 
        total: int
    ) -> str:
        """기본 요약 생성"""
        sentiment_text = {
            "positive": "긍정적",
            "negative": "부정적",
            "neutral": "중립적"
        }.get(sentiment.get("label", "neutral"), "중립적")
        
        summary_parts = [
            f"총 {total}개 리뷰 분석 결과, 전반적인 고객 반응은 {sentiment_text}입니다.",
            f"긍정 {sentiment.get('distribution', {}).get('positive', 0)}건, 부정 {sentiment.get('distribution', {}).get('negative', 0)}건."
        ]
        
        if issues:
            top_issue = issues[0]["type"]
            summary_parts.append(f"주요 이슈: {top_issue}")
        
        if strengths:
            top_strength = strengths[0]["type"]
            summary_parts.append(f"핵심 강점: {top_strength}")
        
        return " ".join(summary_parts)
    
    def _generate_basic_recommendations(
        self, 
        issues: List, 
        strengths: List
    ) -> List[str]:
        """기본 추천 생성"""
        recommendations = []
        
        # 이슈 기반 추천
        issue_recommendations = {
            "배송 지연": "배송 프로세스 점검 및 물류 파트너 협의",
            "품질 불량": "품질 검수 강화 및 QC 프로세스 개선",
            "사이즈 불일치": "사이즈 가이드 상세화 및 실측 정보 추가",
            "색상 차이": "실제 색상에 가까운 상품 이미지 촬영",
            "포장 문제": "포장재 품질 개선 및 완충재 보강",
            "CS 불만": "CS 응대 매뉴얼 정비 및 응답 시간 단축",
            "가격 불만": "가격 경쟁력 분석 또는 가치 차별화 강조"
        }
        
        for issue in issues[:3]:  # 상위 3개 이슈
            rec = issue_recommendations.get(issue["type"])
            if rec:
                recommendations.append(f"[개선] {rec}")
        
        # 강점 기반 추천
        strength_recommendations = {
            "빠른 배송": "빠른 배송을 상품 상세페이지에 강조",
            "우수한 품질": "품질 관련 키워드를 마케팅에 활용",
            "합리적 가격": "가성비 강조 프로모션 진행",
            "예쁜 디자인": "디자인 특화 마케팅 캠페인 기획",
            "친절한 서비스": "서비스 만족 후기를 상품 페이지에 노출",
            "재구매 의향": "재구매 고객 대상 로열티 프로그램 운영"
        }
        
        for strength in strengths[:2]:  # 상위 2개 강점
            rec = strength_recommendations.get(strength["type"])
            if rec:
                recommendations.append(f"[강화] {rec}")
        
        return recommendations
    
    async def _ai_deep_analysis(
        self, 
        reviews: List[ReviewInput], 
        analysis_results: Dict
    ) -> Dict[str, Any]:
        """AI 심층 분석 (LLM 사용)"""
        try:
            from local_llm import LlmChat, UserMessage
            
            EMERGENT_LLM_KEY = os.environ.get("OPENAI_API_KEY", "")
            if not EMERGENT_LLM_KEY:
                return {"summary": "", "recommendations": []}
            
            # 리뷰 샘플 (최대 20개)
            sample_reviews = reviews[:20]
            reviews_text = "\n".join([f"- [{r.rating or '?'}점] {r.content[:200]}" for r in sample_reviews])
            
            prompt = f"""
당신은 이커머스 리뷰 분석 전문가입니다.
다음 고객 리뷰들을 분석하고 셀러에게 도움이 되는 인사이트를 제공해주세요.

[리뷰 데이터]
{reviews_text}

[기초 분석 결과]
- 감성: {analysis_results.get('sentiment', {}).get('label', 'unknown')}
- 주요 이슈: {[i['type'] for i in analysis_results.get('issues', [])[:3]]}
- 핵심 강점: {[s['type'] for s in analysis_results.get('strengths', [])[:3]]}

다음 JSON 형식으로 응답해주세요:
{{
    "summary": "3-4문장의 종합 분석 요약",
    "recommendations": ["구체적 개선 권장사항 5개"]
}}
"""
            
            llm = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"review-{uuid.uuid4().hex[:8]}",
                system_message="You are an e-commerce review analyst."
            ).with_model("gemini", "gemini-2.0-flash")
            
            response = await llm.send_message(UserMessage(text=prompt))
            
            # JSON 파싱
            import json
            response_text = response.strip()
            
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_json = False
                for line in lines:
                    if line.startswith("```") and not in_json:
                        in_json = True
                        continue
                    elif line.startswith("```") and in_json:
                        break
                    elif in_json:
                        json_lines.append(line)
                response_text = "\n".join(json_lines)
            
            import re
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group())
            
            return {"summary": response_text[:500], "recommendations": []}
            
        except Exception as e:
            logger.error(f"AI deep analysis error: {e}")
            return {"summary": "", "recommendations": []}


# ==================== API Endpoints ====================

@router.post("/analyze", response_model=ReviewAnalysisResult)
async def analyze_reviews(
    request: BatchReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    리뷰 배치 분석
    
    - 감성 분석 (긍정/부정/중립)
    - 핵심 키워드 추출
    - 상품 특성 파악
    - 문제점/강점 식별
    - 5:3:2 인사이트 분류
    """
    from server import db
    
    analyzer = ReviewAnalyzer(db)
    result = await analyzer.analyze_reviews(
        reviews=request.reviews,
        analysis_depth=request.analysis_depth
    )
    
    # DB에 분석 결과 저장
    user_id = current_user.get("user_id")
    
    await db.review_analyses.insert_one({
        "analysis_id": result.analysis_id,
        "user_id": user_id,
        "product_id": request.product_id,
        "total_reviews": result.total_reviews,
        "sentiment": result.sentiment,
        "keywords": result.keywords,
        "issues": result.issues,
        "strengths": result.strengths,
        "insights_532": result.insights_532.dict(),
        "summary": result.summary,
        "recommendations": result.recommendations,
        "analyzed_at": result.analyzed_at
    })
    
    return result


@router.post("/analyze-single")
async def analyze_single_review(
    review: ReviewInput,
    current_user: dict = Depends(get_current_user)
):
    """단일 리뷰 분석"""
    analyzer = ReviewAnalyzer()
    
    sentiment = analyzer.analyze_sentiment(review.content)
    keywords = analyzer.extract_keywords(review.content, top_n=5)
    features = analyzer.extract_features(review.content)
    issues = analyzer.identify_issues(review.content)
    strengths = analyzer.identify_strengths(review.content)
    
    return {
        "sentiment": sentiment,
        "keywords": keywords,
        "features": features,
        "issues": issues,
        "strengths": strengths,
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """분석 이력 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    analyses = await db.review_analyses.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("analyzed_at", -1).limit(limit).to_list(limit)
    
    return {
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
    
    analysis = await db.review_analyses.find_one(
        {"analysis_id": analysis_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
    
    return analysis


@router.get("/dashboard/summary")
async def get_review_dashboard(
    days: int = 30,
    current_user: dict = Depends(get_current_user)
):
    """리뷰 대시보드 요약"""
    from server import db
    from datetime import timedelta
    
    user_id = current_user.get("user_id")
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    
    # 최근 분석 통계
    recent_analyses = await db.review_analyses.find(
        {"user_id": user_id, "analyzed_at": {"$gte": cutoff_date}},
        {"_id": 0}
    ).to_list(100)
    
    if not recent_analyses:
        return {
            "total_analyses": 0,
            "total_reviews": 0,
            "avg_sentiment_score": 0,
            "top_issues": [],
            "top_strengths": [],
            "trend": "insufficient_data"
        }
    
    total_reviews = sum(a.get("total_reviews", 0) for a in recent_analyses)
    
    # 감성 점수 평균
    sentiment_scores = [
        a.get("sentiment", {}).get("average_score", 0.5) 
        for a in recent_analyses
    ]
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
    
    # 이슈 집계
    all_issues = {}
    for a in recent_analyses:
        for issue in a.get("issues", []):
            key = issue.get("type", "unknown")
            all_issues[key] = all_issues.get(key, 0) + issue.get("count", 1)
    
    top_issues = sorted(all_issues.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 강점 집계
    all_strengths = {}
    for a in recent_analyses:
        for strength in a.get("strengths", []):
            key = strength.get("type", "unknown")
            all_strengths[key] = all_strengths.get(key, 0) + strength.get("count", 1)
    
    top_strengths = sorted(all_strengths.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # 트렌드 판단
    if len(sentiment_scores) >= 2:
        recent_half = sentiment_scores[:len(sentiment_scores)//2]
        older_half = sentiment_scores[len(sentiment_scores)//2:]
        
        recent_avg = sum(recent_half) / len(recent_half) if recent_half else 0
        older_avg = sum(older_half) / len(older_half) if older_half else 0
        
        if recent_avg > older_avg + 0.05:
            trend = "improving"
        elif recent_avg < older_avg - 0.05:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        "total_analyses": len(recent_analyses),
        "total_reviews": total_reviews,
        "avg_sentiment_score": round(avg_sentiment, 2),
        "top_issues": [{"type": t, "count": c} for t, c in top_issues],
        "top_strengths": [{"type": t, "count": c} for t, c in top_strengths],
        "trend": trend,
        "period_days": days
    }
