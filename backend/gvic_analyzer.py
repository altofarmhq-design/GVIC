"""
GVIC 고유 분석 엔진
- AI 원시 결과를 5:3:2 결이론으로 재가공
- 크로스 분석: 기존 자산과 비교/연결
- 인사이트 도출: 패턴 발견
- 가치 평가: 다차원 스코어링
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
import os

router = APIRouter(prefix="/api/gvic", tags=["gvic-analyzer"])
logger = logging.getLogger(__name__)

# ==================== 5:3:2 결이론 상수 ====================
PUBLIC_RATIO = 0.5      # 공공 환원 (5/10)
OPERATION_RATIO = 0.3   # 운영 (3/10)
MANAGEMENT_RATIO = 0.2  # 기획/관리 (2/10)

# ==================== Models ====================

class GVICAnalysisRequest(BaseModel):
    """GVIC 분석 요청"""
    signal_id: str
    content: str
    ai_analysis: Dict[str, Any]  # AI 원시 분석 결과
    purpose: str = ""
    context: str = ""

class ValueBreakdown532(BaseModel):
    """5:3:2 가치 분해"""
    public_value: float = Field(description="공공 기여 가치 (5)")
    operation_value: float = Field(description="운영 활용 가치 (3)")
    management_value: float = Field(description="기획/관리 가치 (2)")
    total_value: float = Field(description="총 가치")

class GVICInterpretation(BaseModel):
    """GVIC 결이론 해석"""
    # 공공 관점 (5)
    public_contribution: str = Field(description="공공 기여 분석")
    public_beneficiaries: List[str] = Field(description="혜택 받을 대상")
    public_score: float = Field(description="공공 기여 점수 0-100")
    
    # 운영 관점 (3)
    operation_utility: str = Field(description="운영 활용 분석")
    operation_applications: List[str] = Field(description="활용 가능 영역")
    operation_score: float = Field(description="운영 활용 점수 0-100")
    
    # 기획/관리 관점 (2)
    management_potential: str = Field(description="기획 가치 분석")
    management_opportunities: List[str] = Field(description="기획 기회")
    management_score: float = Field(description="기획 가치 점수 0-100")

class GVICAnalysisResult(BaseModel):
    """GVIC 분석 결과"""
    signal_id: str
    original_ai_summary: str
    gvic_interpretation: GVICInterpretation
    value_breakdown: ValueBreakdown532
    gvic_insight: str  # GVIC 관점 종합 인사이트
    recommended_actions: List[str]  # 추천 액션

# ==================== GVIC 분석 엔진 ====================

async def analyze_with_gvic_lens(
    content: str,
    ai_analysis: Dict[str, Any],
    purpose: str = ""
) -> Dict[str, Any]:
    """
    AI 분석 결과를 GVIC 결이론(5:3:2) 관점으로 재해석
    
    5 (공공): 이 정보가 커뮤니티/이용자들에게 어떤 가치를 줄 수 있는가?
    3 (운영): 플랫폼 운영/발전에 어떻게 활용될 수 있는가?
    2 (기획): 새로운 서비스/비즈니스 기획에 어떤 기회를 제공하는가?
    """
    
    # AI 원시 결과 추출
    ai_summary = ai_analysis.get("analysis_summary", "")
    ai_confidence = ai_analysis.get("confidence", 0.5)
    ai_keywords = ai_analysis.get("keywords", [])
    ai_category = ai_analysis.get("signal_category", "general")
    
    # LLM 클라이언트 생성
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import os
    
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
    
    if not EMERGENT_LLM_KEY:
        return generate_fallback_gvic_analysis(content, ai_analysis, ai_confidence)
    
    gvic_prompt = f"""
당신은 GVIC(결이론 기반 가치 분석) 전문가입니다.
다음 콘텐츠와 AI 분석 결과를 5:3:2 결이론 관점에서 재해석해주세요.

[원본 콘텐츠]
{content[:2000]}

[AI 분석 결과]
{ai_summary}

[분석 목적]
{purpose or "일반 분석"}

=== 5:3:2 결이론 관점 분석 ===

다음 JSON 형식으로 응답해주세요:
{{
    "public_analysis": {{
        "contribution": "이 정보가 이용자/주주/구성원에게 줄 수 있는 구체적 가치 (2-3문장)",
        "beneficiaries": ["혜택 받을 대상 목록", "최대 5개"],
        "score": 0-100 (공공 기여 점수)
    }},
    "operation_analysis": {{
        "utility": "플랫폼 운영/발전에 활용할 수 있는 방법 (2-3문장)",
        "applications": ["활용 가능 영역 목록", "최대 5개"],
        "score": 0-100 (운영 활용 점수)
    }},
    "management_analysis": {{
        "potential": "새로운 서비스/비즈니스 기획 기회 (2-3문장)",
        "opportunities": ["기획 기회 목록", "최대 5개"],
        "score": 0-100 (기획 가치 점수)
    }},
    "gvic_insight": "5:3:2 관점을 종합한 GVIC 인사이트 (3-4문장)",
    "recommended_actions": ["GVIC 관점에서 권장하는 액션 목록", "최대 5개"]
}}
"""
    
    try:
        llm = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            model="gemini-2.0-flash"
        )
        
        response = await llm.send_message(
            UserMessage(text=gvic_prompt)
        )
        
        response_text = response.strip()
        
        # JSON 파싱
        import json
        import re
        
        # JSON 블록 추출
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
        
        json_match = re.search(r'\{[\s\S]*\}', response_text)
        if json_match:
            gvic_result = json.loads(json_match.group())
        else:
            raise ValueError("JSON not found in response")
        
        # 점수 추출
        public_score = gvic_result.get("public_analysis", {}).get("score", 50)
        operation_score = gvic_result.get("operation_analysis", {}).get("score", 50)
        management_score = gvic_result.get("management_analysis", {}).get("score", 50)
        
        # 5:3:2 가중 평균 계산
        weighted_total = (
            public_score * PUBLIC_RATIO +
            operation_score * OPERATION_RATIO +
            management_score * MANAGEMENT_RATIO
        )
        
        # 가치 분해 계산
        value_breakdown = {
            "public_value": weighted_total * PUBLIC_RATIO,
            "operation_value": weighted_total * OPERATION_RATIO,
            "management_value": weighted_total * MANAGEMENT_RATIO,
            "total_value": weighted_total
        }
        
        return {
            "success": True,
            "original_ai_summary": ai_summary,
            "gvic_interpretation": {
                "public_contribution": gvic_result.get("public_analysis", {}).get("contribution", ""),
                "public_beneficiaries": gvic_result.get("public_analysis", {}).get("beneficiaries", []),
                "public_score": public_score,
                "operation_utility": gvic_result.get("operation_analysis", {}).get("utility", ""),
                "operation_applications": gvic_result.get("operation_analysis", {}).get("applications", []),
                "operation_score": operation_score,
                "management_potential": gvic_result.get("management_analysis", {}).get("potential", ""),
                "management_opportunities": gvic_result.get("management_analysis", {}).get("opportunities", []),
                "management_score": management_score
            },
            "value_breakdown_532": value_breakdown,
            "gvic_insight": gvic_result.get("gvic_insight", ""),
            "recommended_actions": gvic_result.get("recommended_actions", [])
        }
        
    except Exception as e:
        logger.error(f"GVIC analysis error: {e}")
        # 폴백: 기본 분석
        return generate_fallback_gvic_analysis(content, ai_analysis, ai_confidence)


def generate_fallback_gvic_analysis(
    content: str,
    ai_analysis: Dict[str, Any],
    confidence: float
) -> Dict[str, Any]:
    """LLM 실패 시 규칙 기반 GVIC 분석"""
    
    content_lower = content.lower()
    ai_summary = ai_analysis.get("analysis_summary", "")
    
    # 키워드 기반 점수 계산
    public_keywords = ["공유", "커뮤니티", "도움", "정보", "리뷰", "후기", "팁", "가이드"]
    operation_keywords = ["데이터", "분석", "통계", "트렌드", "패턴", "시스템"]
    management_keywords = ["사업", "비즈니스", "기획", "전략", "수익", "시장", "기회"]
    
    public_score = 50 + sum(10 for kw in public_keywords if kw in content_lower)
    operation_score = 50 + sum(10 for kw in operation_keywords if kw in content_lower)
    management_score = 50 + sum(10 for kw in management_keywords if kw in content_lower)
    
    # 점수 정규화 (0-100)
    public_score = min(100, public_score)
    operation_score = min(100, operation_score)
    management_score = min(100, management_score)
    
    weighted_total = (
        public_score * PUBLIC_RATIO +
        operation_score * OPERATION_RATIO +
        management_score * MANAGEMENT_RATIO
    )
    
    return {
        "success": True,
        "original_ai_summary": ai_summary,
        "gvic_interpretation": {
            "public_contribution": "이 콘텐츠는 커뮤니티 구성원들에게 유용한 정보를 제공할 수 있습니다.",
            "public_beneficiaries": ["GVIC 이용자", "관련 분야 관심자"],
            "public_score": public_score,
            "operation_utility": "플랫폼 데이터 풍부화 및 분석 자료로 활용 가능합니다.",
            "operation_applications": ["데이터 축적", "분석 자료"],
            "operation_score": operation_score,
            "management_potential": "향후 서비스 기획을 위한 참고 자료로 활용할 수 있습니다.",
            "management_opportunities": ["서비스 개선", "기능 확장"],
            "management_score": management_score
        },
        "value_breakdown_532": {
            "public_value": weighted_total * PUBLIC_RATIO,
            "operation_value": weighted_total * OPERATION_RATIO,
            "management_value": weighted_total * MANAGEMENT_RATIO,
            "total_value": weighted_total
        },
        "gvic_insight": f"이 시그널은 5:3:2 결이론 관점에서 총 {weighted_total:.1f}점의 가치를 가집니다.",
        "recommended_actions": ["자산으로 등록", "관련 모듈 검토"]
    }


# ==================== 2단계: 크로스 분석 ====================

class CrossAnalysisRequest(BaseModel):
    """크로스 분석 요청"""
    signal_id: str
    content: str
    keywords: List[str] = []
    category: str = "general"
    max_related: int = 10

class AssetRelation(BaseModel):
    """자산 연결 관계"""
    source_id: str
    target_id: str
    relation_type: str  # similar, complementary, conflicting, duplicate
    similarity_score: float
    common_keywords: List[str]
    description: str

async def calculate_text_similarity(text1: str, text2: str) -> float:
    """텍스트 유사도 계산 (키워드 기반)"""
    # 간단한 Jaccard 유사도
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union) if union else 0.0

async def find_keyword_matches(keywords: List[str], asset_keywords: List[str]) -> List[str]:
    """공통 키워드 찾기"""
    set1 = set(k.lower() for k in keywords)
    set2 = set(k.lower() for k in asset_keywords)
    return list(set1 & set2)

async def cross_analyze_signal(
    signal_id: str,
    content: str,
    keywords: List[str],
    category: str,
    max_related: int = 10
) -> Dict[str, Any]:
    """
    신규 시그널과 기존 자산들을 크로스 분석
    
    분석 내용:
    1. 유사 자산 탐색 (similar)
    2. 보완 자산 탐색 (complementary)
    3. 충돌 자산 탐색 (conflicting)
    4. 중복 자산 탐색 (duplicate)
    """
    from server import db
    
    # 기존 자산들 조회
    existing_assets = await db.indexed_assets.find(
        {"status": "indexed"},
        {"_id": 0}
    ).to_list(500)
    
    # 기존 시그널들도 조회 (자산화되지 않은 것들)
    existing_signals = await db.pipeline_signals.find(
        {"signal_id": {"$ne": signal_id}},
        {"_id": 0, "signal_id": 1, "content": 1, "metadata": 1, "created_at": 1}
    ).to_list(200)
    
    related_assets = []
    similar_signals = []
    potential_duplicates = []
    complementary_assets = []
    conflicting_assets = []
    
    content_lower = content.lower()
    
    # 자산 크로스 분석
    for asset in existing_assets:
        asset_content = asset.get("original_content", "") or asset.get("content_summary", "")
        asset_keywords = asset.get("feature_keywords", [])
        
        # 텍스트 유사도 계산
        similarity = await calculate_text_similarity(content, asset_content)
        
        # 키워드 매칭
        common_kw = await find_keyword_matches(keywords, asset_keywords)
        keyword_score = len(common_kw) / max(len(keywords), 1) if keywords else 0
        
        # 카테고리 매칭
        category_match = 1.0 if asset.get("feature_category") == category else 0.3
        
        # 종합 점수
        total_score = (similarity * 0.4) + (keyword_score * 0.4) + (category_match * 0.2)
        
        if total_score > 0.1:  # 최소 임계값
            relation = {
                "asset_id": asset.get("asset_id"),
                "similarity_score": round(total_score, 3),
                "text_similarity": round(similarity, 3),
                "keyword_match": round(keyword_score, 3),
                "common_keywords": common_kw[:5],
                "category": asset.get("feature_category"),
                "summary": asset.get("content_summary", "")[:100],
                "value_score": asset.get("value_score", 0),
                "created_at": asset.get("created_at")
            }
            
            # 관계 유형 분류
            if total_score > 0.8:
                relation["relation_type"] = "duplicate"
                relation["description"] = "높은 유사도 - 중복 가능성"
                potential_duplicates.append(relation)
            elif total_score > 0.5:
                relation["relation_type"] = "similar"
                relation["description"] = "유사한 주제/내용"
                related_assets.append(relation)
            elif keyword_score > 0.3 and similarity < 0.3:
                relation["relation_type"] = "complementary"
                relation["description"] = "관련 키워드 공유 - 보완 가능"
                complementary_assets.append(relation)
    
    # 시그널 크로스 분석
    for sig in existing_signals:
        sig_content = sig.get("content", "")
        similarity = await calculate_text_similarity(content, sig_content)
        
        if similarity > 0.3:
            similar_signals.append({
                "signal_id": sig.get("signal_id"),
                "similarity_score": round(similarity, 3),
                "content_preview": sig_content[:100],
                "created_at": sig.get("created_at")
            })
    
    # 정렬
    related_assets.sort(key=lambda x: x["similarity_score"], reverse=True)
    similar_signals.sort(key=lambda x: x["similarity_score"], reverse=True)
    complementary_assets.sort(key=lambda x: x["keyword_match"], reverse=True)
    
    # 결과 구성
    cross_analysis = {
        "signal_id": signal_id,
        "analysis_type": "cross_analysis",
        "summary": {
            "total_assets_scanned": len(existing_assets),
            "total_signals_scanned": len(existing_signals),
            "related_found": len(related_assets),
            "duplicates_found": len(potential_duplicates),
            "complementary_found": len(complementary_assets),
            "similar_signals_found": len(similar_signals)
        },
        "related_assets": related_assets[:max_related],
        "potential_duplicates": potential_duplicates[:5],
        "complementary_assets": complementary_assets[:max_related],
        "similar_signals": similar_signals[:5],
        "recommendations": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # 추천 생성
    if potential_duplicates:
        cross_analysis["recommendations"].append({
            "type": "warning",
            "message": f"중복 가능성이 있는 자산이 {len(potential_duplicates)}개 발견되었습니다. 확인 후 병합을 고려하세요."
        })
    
    if related_assets:
        cross_analysis["recommendations"].append({
            "type": "info",
            "message": f"관련 자산 {len(related_assets)}개와 연결하여 모듈화할 수 있습니다."
        })
    
    if complementary_assets:
        cross_analysis["recommendations"].append({
            "type": "success",
            "message": f"보완 가능한 자산 {len(complementary_assets)}개가 있습니다. 시너지 효과를 기대할 수 있습니다."
        })
    
    if not related_assets and not complementary_assets:
        cross_analysis["recommendations"].append({
            "type": "highlight",
            "message": "기존 자산과 중복이 없는 새로운 유형입니다. 희소성이 높을 수 있습니다."
        })
    
    return cross_analysis


# ==================== 3단계: 인사이트 도출 ====================

async def extract_insights(
    signal_id: str = None,
    content: str = None,
    time_range_days: int = 30
) -> Dict[str, Any]:
    """
    축적된 데이터에서 인사이트 도출
    
    분석 내용:
    1. 반복 패턴 - 자주 등장하는 주제/키워드
    2. 트렌드 분석 - 시간별 관심사 변화
    3. 이상치 발견 - 독특한 가치를 가진 항목
    4. 클러스터 분석 - 유사 그룹 발견
    """
    from server import db
    from collections import Counter
    from datetime import timedelta
    
    # 모든 시그널 조회 (시간 필터 없이)
    all_signals = await db.pipeline_signals.find(
        {},
        {"_id": 0, "signal_id": 1, "content": 1, "metadata": 1, "created_at": 1, "category": 1}
    ).to_list(500)
    
    # 전체 자산 조회
    all_assets = await db.indexed_assets.find({}, {"_id": 0}).to_list(500)
    
    # GVIC 분석 결과 조회
    gvic_analyses = await db.gvic_analyses.find({}, {"_id": 0}).to_list(200)
    
    insights = {
        "analysis_type": "insight_extraction",
        "time_range_days": time_range_days,
        "data_summary": {
            "total_signals": len(all_signals),
            "total_assets": len(all_assets),
            "total_gvic_analyses": len(gvic_analyses)
        },
        "patterns": {},
        "trends": {},
        "anomalies": [],
        "clusters": [],
        "key_insights": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # ===== 1. 반복 패턴 분석 =====
    all_keywords = []
    all_categories = []
    all_words = []
    
    for signal in all_signals:
        metadata = signal.get("metadata", {})
        ai_analysis = metadata.get("ai_analysis", {})
        
        # 키워드 수집
        keywords = ai_analysis.get("keywords", [])
        all_keywords.extend(keywords)
        
        # 카테고리 수집
        category = ai_analysis.get("signal_category", signal.get("category", "general"))
        all_categories.append(category)
        
        # 단어 빈도 (간단한 토큰화)
        content = signal.get("content", "")
        words = [w for w in content.lower().split() if len(w) > 2]
        all_words.extend(words)
    
    # 키워드 빈도
    keyword_freq = Counter(all_keywords).most_common(20)
    category_freq = Counter(all_categories).most_common(10)
    word_freq = Counter(all_words).most_common(30)
    
    insights["patterns"] = {
        "top_keywords": [{"keyword": k, "count": c} for k, c in keyword_freq],
        "category_distribution": [{"category": k, "count": c} for k, c in category_freq],
        "frequent_words": [{"word": w, "count": c} for w, c in word_freq[:15]],
        "total_unique_keywords": len(set(all_keywords)),
        "dominant_topic": keyword_freq[0][0] if keyword_freq else None
    }
    
    # ===== 2. 트렌드 분석 =====
    # 일별 시그널 수
    daily_counts = Counter()
    daily_categories = {}
    
    for signal in all_signals:
        created_raw = signal.get("created_at", "")
        # datetime 객체인 경우 문자열로 변환
        if hasattr(created_raw, 'isoformat'):
            created = created_raw.isoformat()[:10]
        else:
            created = str(created_raw)[:10]  # YYYY-MM-DD
        daily_counts[created] += 1
        
        category = signal.get("metadata", {}).get("ai_analysis", {}).get("signal_category", "general")
        if created not in daily_categories:
            daily_categories[created] = Counter()
        daily_categories[created][category] += 1
    
    # 최근 7일 vs 이전 7일 비교
    sorted_dates = sorted(daily_counts.keys(), reverse=True)
    recent_7 = sum(daily_counts[d] for d in sorted_dates[:7]) if len(sorted_dates) >= 7 else sum(daily_counts.values())
    prev_7 = sum(daily_counts[d] for d in sorted_dates[7:14]) if len(sorted_dates) >= 14 else 0
    
    trend_direction = "상승" if recent_7 > prev_7 else ("하락" if recent_7 < prev_7 else "유지")
    trend_change = ((recent_7 - prev_7) / prev_7 * 100) if prev_7 > 0 else 0
    
    insights["trends"] = {
        "daily_activity": [{"date": d, "count": c} for d, c in sorted(daily_counts.items())[-14:]],
        "recent_7_days": recent_7,
        "previous_7_days": prev_7,
        "trend_direction": trend_direction,
        "trend_change_percent": round(trend_change, 1),
        "peak_day": max(daily_counts.items(), key=lambda x: x[1])[0] if daily_counts else None,
        "avg_daily": round(sum(daily_counts.values()) / len(daily_counts), 1) if daily_counts else 0
    }
    
    # ===== 3. 이상치 발견 =====
    # 가치 점수 기준 이상치
    if all_assets:
        value_scores = [a.get("value_score", 0.5) for a in all_assets]
        avg_value = sum(value_scores) / len(value_scores)
        std_value = (sum((v - avg_value) ** 2 for v in value_scores) / len(value_scores)) ** 0.5
        
        for asset in all_assets:
            score = asset.get("value_score", 0.5)
            z_score = (score - avg_value) / std_value if std_value > 0 else 0
            
            if abs(z_score) > 1.5:  # 1.5 표준편차 이상
                insights["anomalies"].append({
                    "asset_id": asset.get("asset_id"),
                    "type": "high_value" if z_score > 0 else "low_value",
                    "value_score": round(score, 3),
                    "z_score": round(z_score, 2),
                    "summary": asset.get("content_summary", "")[:100],
                    "reason": "평균보다 매우 높은 가치" if z_score > 0 else "평균보다 매우 낮은 가치"
                })
        
        insights["anomalies"] = sorted(insights["anomalies"], key=lambda x: abs(x["z_score"]), reverse=True)[:10]
    
    # ===== 4. 클러스터 분석 (카테고리 기반) =====
    category_assets = {}
    for asset in all_assets:
        cat = asset.get("feature_category", "general")
        if cat not in category_assets:
            category_assets[cat] = []
        category_assets[cat].append(asset)
    
    for cat, assets in category_assets.items():
        if len(assets) >= 2:
            avg_value = sum(a.get("value_score", 0.5) for a in assets) / len(assets)
            insights["clusters"].append({
                "category": cat,
                "count": len(assets),
                "avg_value_score": round(avg_value, 3),
                "sample_assets": [a.get("asset_id") for a in assets[:3]]
            })
    
    insights["clusters"] = sorted(insights["clusters"], key=lambda x: x["count"], reverse=True)
    
    # ===== 5. 핵심 인사이트 생성 =====
    if insights["patterns"]["dominant_topic"]:
        insights["key_insights"].append({
            "type": "pattern",
            "title": "주요 관심사",
            "description": f"'{insights['patterns']['dominant_topic']}'가 가장 빈번하게 등장하는 키워드입니다.",
            "importance": "high"
        })
    
    if trend_direction == "상승" and trend_change > 20:
        insights["key_insights"].append({
            "type": "trend",
            "title": "활동 급증",
            "description": f"최근 7일간 활동이 {trend_change:.0f}% 증가했습니다. 관심도가 높아지고 있습니다.",
            "importance": "high"
        })
    elif trend_direction == "하락" and trend_change < -20:
        insights["key_insights"].append({
            "type": "trend",
            "title": "활동 감소",
            "description": f"최근 7일간 활동이 {abs(trend_change):.0f}% 감소했습니다.",
            "importance": "medium"
        })
    
    high_value_anomalies = [a for a in insights["anomalies"] if a["type"] == "high_value"]
    if high_value_anomalies:
        insights["key_insights"].append({
            "type": "anomaly",
            "title": "고가치 자산 발견",
            "description": f"평균보다 높은 가치를 가진 자산 {len(high_value_anomalies)}개가 발견되었습니다.",
            "importance": "high"
        })
    
    if insights["clusters"]:
        top_cluster = insights["clusters"][0]
        insights["key_insights"].append({
            "type": "cluster",
            "title": "주요 자산 그룹",
            "description": f"'{top_cluster['category']}' 카테고리에 {top_cluster['count']}개의 자산이 집중되어 있습니다.",
            "importance": "medium"
        })
    
    return insights


# ==================== API Endpoints ====================

@router.get("/insights")
async def get_platform_insights(time_range_days: int = 30):
    """
    플랫폼 전체 인사이트 조회
    
    - 반복 패턴 (키워드, 카테고리 빈도)
    - 트렌드 (일별 활동량, 증감)
    - 이상치 (고가치/저가치 자산)
    - 클러스터 (카테고리별 그룹)
    """
    insights = await extract_insights(time_range_days=time_range_days)
    
    # DB에 저장
    from server import db
    await db.platform_insights.insert_one({
        **insights,
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return insights


@router.post("/cross-analyze")
async def cross_analyze_endpoint(request: CrossAnalysisRequest):
    """
    신규 시그널과 기존 자산/시그널 크로스 분석
    
    분석 결과:
    - 유사 자산 목록
    - 중복 가능성 자산
    - 보완 가능 자산
    - 유사 시그널 목록
    - 추천 액션
    """
    result = await cross_analyze_signal(
        signal_id=request.signal_id,
        content=request.content,
        keywords=request.keywords,
        category=request.category,
        max_related=request.max_related
    )
    
    # DB에 크로스 분석 결과 저장
    from server import db
    
    await db.cross_analyses.update_one(
        {"signal_id": request.signal_id},
        {"$set": result},
        upsert=True
    )
    
    return result


@router.get("/cross-analysis/{signal_id}")
async def get_cross_analysis(signal_id: str):
    """저장된 크로스 분석 결과 조회"""
    from server import db
    
    analysis = await db.cross_analyses.find_one(
        {"signal_id": signal_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="크로스 분석 결과가 없습니다")
    
    return analysis


@router.post("/analyze")
async def gvic_analyze_signal(request: GVICAnalysisRequest):
    """
    시그널을 GVIC 결이론(5:3:2)으로 분석
    
    AI 분석 결과를 받아서:
    1. 공공 기여 관점 (5) 분석
    2. 운영 활용 관점 (3) 분석  
    3. 기획/관리 관점 (2) 분석
    4. 종합 인사이트 도출
    """
    result = await analyze_with_gvic_lens(
        content=request.content,
        ai_analysis=request.ai_analysis,
        purpose=request.purpose
    )
    
    result["signal_id"] = request.signal_id
    
    # DB에 GVIC 분석 결과 저장
    from server import db
    
    gvic_record = {
        "signal_id": request.signal_id,
        "analysis_type": "gvic_532",
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.gvic_analyses.update_one(
        {"signal_id": request.signal_id},
        {"$set": gvic_record},
        upsert=True
    )
    
    return result


@router.get("/analysis/{signal_id}")
async def get_gvic_analysis(signal_id: str):
    """저장된 GVIC 분석 결과 조회"""
    from server import db
    
    analysis = await db.gvic_analyses.find_one(
        {"signal_id": signal_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="GVIC 분석 결과가 없습니다")
    
    return analysis


@router.post("/reanalyze/{signal_id}")
async def reanalyze_with_gvic(signal_id: str):
    """기존 시그널을 GVIC 관점으로 재분석"""
    from server import db
    
    # 시그널 조회
    signal = await db.pipeline_signals.find_one(
        {"signal_id": signal_id},
        {"_id": 0}
    )
    
    if not signal:
        raise HTTPException(status_code=404, detail="시그널을 찾을 수 없습니다")
    
    content = signal.get("content", "")
    ai_analysis = signal.get("metadata", {}).get("ai_analysis", {})
    purpose = signal.get("metadata", {}).get("purpose", "")
    
    # GVIC 분석 수행
    result = await analyze_with_gvic_lens(
        content=content,
        ai_analysis=ai_analysis,
        purpose=purpose
    )
    
    result["signal_id"] = signal_id
    
    # 결과 저장
    gvic_record = {
        "signal_id": signal_id,
        "analysis_type": "gvic_532",
        "result": result,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.gvic_analyses.update_one(
        {"signal_id": signal_id},
        {"$set": gvic_record},
        upsert=True
    )
    
    # 시그널에 GVIC 분석 결과 연결
    await db.pipeline_signals.update_one(
        {"signal_id": signal_id},
        {"$set": {"gvic_analysis": result}}
    )
    
    return result
