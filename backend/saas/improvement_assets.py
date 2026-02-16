"""
GVIC Improvement Asset Manager - 개선점 자산화 모듈
- HS Code 기반 품목군 분류
- 개선점(건의/불만/신제품욕구)만 자산화
- 강점/Null은 제외
- 품목군별 개선점 축적 및 벤치마크
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging

router = APIRouter(prefix="/api/assets", tags=["improvement-assets"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== HS Code 기본 데이터 ====================

# 주요 품목군 HS Code (6자리 기준)
HS_CODE_CATEGORIES = {
    # 전자기기
    "8518.30": {
        "name": "헤드폰/이어폰",
        "name_en": "Headphones/Earphones",
        "feature_modules": ["음질", "배터리", "착용감", "연결성", "통화품질", "노이즈캔슬링", "방수"]
    },
    "8517.12": {
        "name": "스마트폰",
        "name_en": "Smartphones",
        "feature_modules": ["디스플레이", "카메라", "배터리", "성능", "저장공간", "내구성"]
    },
    "8471.30": {
        "name": "노트북/태블릿",
        "name_en": "Laptops/Tablets",
        "feature_modules": ["디스플레이", "성능", "배터리", "키보드", "무게", "발열"]
    },
    "8516.40": {
        "name": "다리미/스티머",
        "name_en": "Irons/Steamers",
        "feature_modules": ["스팀량", "온도조절", "무게", "물탱크", "안전성"]
    },
    # 의류
    "6110.20": {
        "name": "면 스웨터/풀오버",
        "name_en": "Cotton Sweaters",
        "feature_modules": ["소재감", "사이즈", "색상", "세탁성", "보온성"]
    },
    "6203.42": {
        "name": "면 바지",
        "name_en": "Cotton Trousers",
        "feature_modules": ["핏", "소재감", "사이즈", "내구성", "색상"]
    },
    "6402.19": {
        "name": "운동화/스니커즈",
        "name_en": "Sports Shoes",
        "feature_modules": ["착용감", "쿠션", "사이즈", "내구성", "디자인", "통기성"]
    },
    # 화장품
    "3304.99": {
        "name": "기타 화장품",
        "name_en": "Other Cosmetics",
        "feature_modules": ["보습력", "발림성", "향", "지속력", "자극성", "용량"]
    },
    "3305.10": {
        "name": "샴푸",
        "name_en": "Shampoos",
        "feature_modules": ["세정력", "향", "두피자극", "거품", "헹굼", "용량"]
    },
    # 식품
    "2106.90": {
        "name": "건강기능식품",
        "name_en": "Health Supplements",
        "feature_modules": ["효능", "복용편의", "맛", "부작용", "가격", "포장"]
    },
    # 가구/생활
    "9403.20": {
        "name": "금속 가구",
        "name_en": "Metal Furniture",
        "feature_modules": ["조립", "내구성", "디자인", "크기", "마감"]
    },
    "9404.21": {
        "name": "매트리스",
        "name_en": "Mattresses",
        "feature_modules": ["경도", "소재", "사이즈", "냄새", "내구성", "배송"]
    }
}

# ==================== Models ====================

class HSCodeInfo(BaseModel):
    """HS Code 정보"""
    hs_code: str
    name: str
    name_en: str
    feature_modules: List[str]

class ImprovementItem(BaseModel):
    """개선점 항목"""
    type: str = Field(..., description="improvement_type: suggestion, complaint, new_product_need")
    category: str = Field(..., description="세부 카테고리")
    content: str = Field(..., description="개선점 내용")
    severity: Optional[str] = Field(None, description="심각도: high, medium, low")
    feature_module: Optional[str] = Field(None, description="관련 기능 모듈")
    examples: List[str] = Field(default_factory=list, description="실제 리뷰 예시")

class ProductHSMapping(BaseModel):
    """제품-HS Code 매핑"""
    product_id: str
    hs_code: str
    hs_code_10: Optional[str] = Field(None, description="10자리 세번 (역직구용)")

class AssetAccumulateRequest(BaseModel):
    """자산 축적 요청"""
    product_id: str
    hs_code: str
    analysis_id: str
    improvements: List[ImprovementItem]

class CategoryAssetSummary(BaseModel):
    """품목군별 자산 요약"""
    hs_code: str
    category_name: str
    total_improvements: int
    by_type: Dict[str, int]
    by_feature_module: Dict[str, int]
    top_issues: List[Dict[str, Any]]

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

# ==================== Improvement Asset Manager ====================

class ImprovementAssetManager:
    """개선점 자산 관리자"""
    
    def __init__(self, db=None):
        self.db = db
    
    def get_hs_code_info(self, hs_code: str) -> Optional[Dict]:
        """HS Code 정보 조회"""
        return HS_CODE_CATEGORIES.get(hs_code)
    
    def suggest_hs_code(self, product_name: str, category: str = None) -> List[Dict]:
        """제품명으로 HS Code 추천"""
        suggestions = []
        product_lower = product_name.lower()
        
        # 키워드 매칭
        keyword_mapping = {
            "8518.30": ["이어폰", "헤드폰", "에어팟", "버즈", "earphone", "headphone", "airpod"],
            "8517.12": ["스마트폰", "핸드폰", "아이폰", "갤럭시", "phone", "iphone", "galaxy"],
            "8471.30": ["노트북", "태블릿", "아이패드", "laptop", "tablet", "ipad"],
            "6110.20": ["스웨터", "니트", "풀오버", "sweater", "knit"],
            "6203.42": ["바지", "팬츠", "청바지", "pants", "jeans", "trousers"],
            "6402.19": ["운동화", "스니커즈", "신발", "shoes", "sneakers"],
            "3304.99": ["화장품", "크림", "로션", "세럼", "cosmetic", "cream", "lotion"],
            "3305.10": ["샴푸", "린스", "shampoo", "conditioner"],
            "9403.20": ["책상", "선반", "테이블", "desk", "shelf", "table"],
            "9404.21": ["매트리스", "침대", "mattress", "bed"]
        }
        
        for hs_code, keywords in keyword_mapping.items():
            for kw in keywords:
                if kw in product_lower:
                    info = HS_CODE_CATEGORIES.get(hs_code, {})
                    suggestions.append({
                        "hs_code": hs_code,
                        "name": info.get("name", ""),
                        "name_en": info.get("name_en", ""),
                        "confidence": "high" if kw in product_lower else "medium"
                    })
                    break
        
        return suggestions[:3]  # 상위 3개 추천
    
    def extract_improvements_from_analysis(self, analysis_result: Dict) -> List[ImprovementItem]:
        """분석 결과에서 개선점만 추출 (강점/Null 제외)"""
        improvements = []
        
        # 건의사항 추출
        suggestions = analysis_result.get("suggestions", {})
        for item in suggestions.get("items", []):
            improvements.append(ImprovementItem(
                type="suggestion",
                category=item.get("type", "general"),
                content=item.get("content", ""),
                feature_module=self._map_to_feature_module(item.get("type", "")),
                examples=item.get("examples", [])
            ))
        
        # 불만 추출
        complaints = analysis_result.get("complaints", {})
        for item in complaints.get("items", []):
            improvements.append(ImprovementItem(
                type="complaint",
                category=item.get("type", "general"),
                content=item.get("content", ""),
                severity=item.get("severity", "medium"),
                feature_module=self._map_to_feature_module(item.get("type", "")),
                examples=item.get("examples", [])
            ))
        
        # 신제품 욕구 추출
        new_needs = analysis_result.get("new_product_needs", {})
        for item in new_needs.get("items", []):
            improvements.append(ImprovementItem(
                type="new_product_need",
                category=item.get("type", "general"),
                content=item.get("content", ""),
                feature_module=self._map_to_feature_module(item.get("type", "")),
                examples=item.get("examples", [])
            ))
        
        return improvements
    
    def _map_to_feature_module(self, category: str) -> str:
        """카테고리를 기능 모듈로 매핑"""
        mapping = {
            # 불만 카테고리 → 기능 모듈
            "품질불량": "품질",
            "배송지연": "배송",
            "오배송": "배송",
            "색상차이": "색상",
            "사이즈오류": "사이즈",
            "CS불만": "서비스",
            "환불문제": "서비스",
            # 건의 카테고리 → 기능 모듈
            "색상": "색상",
            "사이즈": "사이즈",
            "기능": "기능",
            "포장": "포장",
            "가격": "가격",
            "배송": "배송",
            "설명서": "사용성",
            # 신제품 욕구 → 기능 모듈
            "신기능": "기능",
            "변형제품": "디자인",
            "업그레이드": "성능",
            "조합제품": "구성",
            "특수용도": "기능"
        }
        return mapping.get(category, "기타")
    
    async def accumulate_asset(
        self,
        hs_code: str,
        improvements: List[ImprovementItem],
        product_id: str,
        analysis_id: str
    ) -> Dict:
        """개선점을 품목군 자산으로 축적"""
        accumulated = 0
        
        for imp in improvements:
            asset_id = f"AST_{uuid.uuid4().hex[:12]}"
            
            # 기존 동일 개선점 확인 (중복 시 빈도 증가)
            existing = await self.db.improvement_assets.find_one({
                "hs_code": hs_code,
                "type": imp.type,
                "category": imp.category,
                "feature_module": imp.feature_module
            })
            
            if existing:
                # 빈도 증가 및 예시 추가
                new_examples = list(set(existing.get("examples", []) + imp.examples))[:10]
                await self.db.improvement_assets.update_one(
                    {"_id": existing["_id"]},
                    {
                        "$inc": {"frequency": 1},
                        "$set": {
                            "examples": new_examples,
                            "last_reported": datetime.now(timezone.utc).isoformat()
                        },
                        "$addToSet": {
                            "source_products": product_id,
                            "source_analyses": analysis_id
                        }
                    }
                )
            else:
                # 신규 자산 등록
                asset_record = {
                    "asset_id": asset_id,
                    "hs_code": hs_code,
                    "type": imp.type,
                    "category": imp.category,
                    "content": imp.content,
                    "severity": imp.severity,
                    "feature_module": imp.feature_module,
                    "examples": imp.examples[:5],
                    "frequency": 1,
                    "source_products": [product_id],
                    "source_analyses": [analysis_id],
                    "first_reported": datetime.now(timezone.utc).isoformat(),
                    "last_reported": datetime.now(timezone.utc).isoformat()
                }
                await self.db.improvement_assets.insert_one(asset_record)
            
            accumulated += 1
        
        return {
            "accumulated": accumulated,
            "hs_code": hs_code
        }
    
    async def get_category_assets(self, hs_code: str) -> CategoryAssetSummary:
        """품목군별 자산 조회"""
        assets = await self.db.improvement_assets.find(
            {"hs_code": hs_code},
            {"_id": 0}
        ).to_list(500)
        
        if not assets:
            hs_info = self.get_hs_code_info(hs_code) or {}
            return CategoryAssetSummary(
                hs_code=hs_code,
                category_name=hs_info.get("name", "Unknown"),
                total_improvements=0,
                by_type={},
                by_feature_module={},
                top_issues=[]
            )
        
        # 집계
        by_type = {}
        by_feature_module = {}
        
        for asset in assets:
            # 타입별 집계
            t = asset.get("type", "unknown")
            by_type[t] = by_type.get(t, 0) + asset.get("frequency", 1)
            
            # 기능 모듈별 집계
            fm = asset.get("feature_module", "기타")
            by_feature_module[fm] = by_feature_module.get(fm, 0) + asset.get("frequency", 1)
        
        # 상위 이슈 (빈도순)
        sorted_assets = sorted(assets, key=lambda x: x.get("frequency", 0), reverse=True)
        top_issues = [
            {
                "type": a.get("type"),
                "category": a.get("category"),
                "feature_module": a.get("feature_module"),
                "frequency": a.get("frequency"),
                "severity": a.get("severity"),
                "content": a.get("content")
            }
            for a in sorted_assets[:10]
        ]
        
        hs_info = self.get_hs_code_info(hs_code) or {}
        
        return CategoryAssetSummary(
            hs_code=hs_code,
            category_name=hs_info.get("name", "Unknown"),
            total_improvements=sum(a.get("frequency", 1) for a in assets),
            by_type=by_type,
            by_feature_module=by_feature_module,
            top_issues=top_issues
        )


# ==================== API Endpoints ====================

@router.get("/hs-codes")
async def get_hs_codes(
    current_user: dict = Depends(get_current_user)
):
    """HS Code 목록 조회"""
    codes = [
        {
            "hs_code": code,
            "name": info["name"],
            "name_en": info["name_en"],
            "feature_modules": info["feature_modules"]
        }
        for code, info in HS_CODE_CATEGORIES.items()
    ]
    return {
        "hs_codes": codes,
        "total": len(codes)
    }

@router.get("/hs-codes/{hs_code}")
async def get_hs_code_detail(
    hs_code: str,
    current_user: dict = Depends(get_current_user)
):
    """HS Code 상세 조회"""
    info = HS_CODE_CATEGORIES.get(hs_code)
    if not info:
        raise HTTPException(status_code=404, detail="HS Code를 찾을 수 없습니다")
    
    return {
        "hs_code": hs_code,
        **info
    }

@router.post("/suggest-hs-code")
async def suggest_hs_code(
    product_name: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """제품명으로 HS Code 추천"""
    manager = ImprovementAssetManager()
    suggestions = manager.suggest_hs_code(product_name, category)
    
    return {
        "product_name": product_name,
        "suggestions": suggestions
    }

@router.post("/products/{product_id}/set-hs-code")
async def set_product_hs_code(
    product_id: str,
    mapping: ProductHSMapping,
    current_user: dict = Depends(get_current_user)
):
    """제품에 HS Code 설정"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 제품 확인
    product = await db.shop_products.find_one(
        {"product_id": product_id, "user_id": user_id}
    )
    if not product:
        raise HTTPException(status_code=404, detail="제품을 찾을 수 없습니다")
    
    # HS Code 유효성 확인
    hs_info = HS_CODE_CATEGORIES.get(mapping.hs_code)
    
    # HS Code 설정
    await db.shop_products.update_one(
        {"product_id": product_id},
        {"$set": {
            "hs_code": mapping.hs_code,
            "hs_code_10": mapping.hs_code_10,
            "hs_code_name": hs_info.get("name") if hs_info else None,
            "feature_modules": hs_info.get("feature_modules") if hs_info else [],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "product_id": product_id,
        "hs_code": mapping.hs_code,
        "hs_code_name": hs_info.get("name") if hs_info else "Unknown"
    }

@router.post("/accumulate")
async def accumulate_improvements(
    request: AssetAccumulateRequest,
    current_user: dict = Depends(get_current_user)
):
    """개선점 자산 축적"""
    from server import db
    
    manager = ImprovementAssetManager(db)
    result = await manager.accumulate_asset(
        hs_code=request.hs_code,
        improvements=request.improvements,
        product_id=request.product_id,
        analysis_id=request.analysis_id
    )
    
    return {
        "success": True,
        **result
    }

@router.post("/accumulate-from-analysis/{analysis_id}")
async def accumulate_from_analysis(
    analysis_id: str,
    hs_code: str,
    current_user: dict = Depends(get_current_user)
):
    """분석 결과에서 개선점 자동 추출 및 축적"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 분석 결과 조회
    analysis = await db.product_analyses.find_one(
        {"analysis_id": analysis_id},
        {"_id": 0}
    )
    
    if not analysis:
        raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다")
    
    product_id = analysis.get("product_id")
    
    # 개선점 추출 (강점/Null 제외)
    manager = ImprovementAssetManager(db)
    improvements = manager.extract_improvements_from_analysis(analysis)
    
    if not improvements:
        return {
            "success": True,
            "message": "축적할 개선점이 없습니다 (강점만 있거나 데이터 없음)",
            "accumulated": 0
        }
    
    # 자산 축적
    result = await manager.accumulate_asset(
        hs_code=hs_code,
        improvements=improvements,
        product_id=product_id,
        analysis_id=analysis_id
    )
    
    return {
        "success": True,
        "extracted_improvements": len(improvements),
        **result
    }

@router.get("/category/{hs_code}")
async def get_category_assets(
    hs_code: str,
    current_user: dict = Depends(get_current_user)
):
    """품목군별 개선점 자산 조회"""
    from server import db
    
    manager = ImprovementAssetManager(db)
    summary = await manager.get_category_assets(hs_code)
    
    return summary.dict()

@router.get("/category/{hs_code}/checklist")
async def get_category_checklist(
    hs_code: str,
    current_user: dict = Depends(get_current_user)
):
    """품목군 진입 시 필수 체크리스트 (개선점 기반)"""
    from server import db
    
    # 해당 품목군의 HIGH 심각도 불만 조회
    high_complaints = await db.improvement_assets.find(
        {"hs_code": hs_code, "type": "complaint", "severity": "high"},
        {"_id": 0}
    ).sort("frequency", -1).limit(10).to_list(10)
    
    # 자주 발생하는 건의사항
    top_suggestions = await db.improvement_assets.find(
        {"hs_code": hs_code, "type": "suggestion"},
        {"_id": 0}
    ).sort("frequency", -1).limit(5).to_list(5)
    
    # 신제품 욕구
    product_needs = await db.improvement_assets.find(
        {"hs_code": hs_code, "type": "new_product_need"},
        {"_id": 0}
    ).sort("frequency", -1).limit(5).to_list(5)
    
    hs_info = HS_CODE_CATEGORIES.get(hs_code, {})
    
    return {
        "hs_code": hs_code,
        "category_name": hs_info.get("name", "Unknown"),
        "checklist": {
            "critical_issues": [
                {
                    "category": c.get("category"),
                    "feature_module": c.get("feature_module"),
                    "frequency": c.get("frequency"),
                    "action": "필수 확인",
                    "description": c.get("content")
                }
                for c in high_complaints
            ],
            "common_suggestions": [
                {
                    "category": s.get("category"),
                    "feature_module": s.get("feature_module"),
                    "frequency": s.get("frequency"),
                    "action": "권장 검토",
                    "description": s.get("content")
                }
                for s in top_suggestions
            ],
            "market_opportunities": [
                {
                    "category": n.get("category"),
                    "feature_module": n.get("feature_module"),
                    "frequency": n.get("frequency"),
                    "action": "기회 탐색",
                    "description": n.get("content")
                }
                for n in product_needs
            ]
        },
        "total_data_points": len(high_complaints) + len(top_suggestions) + len(product_needs)
    }

@router.get("/stats/overview")
async def get_asset_stats(
    current_user: dict = Depends(get_current_user)
):
    """전체 자산 통계"""
    from server import db
    
    # 전체 자산 수
    total_assets = await db.improvement_assets.count_documents({})
    
    # 품목군별 통계
    pipeline = [
        {"$group": {
            "_id": "$hs_code",
            "count": {"$sum": 1},
            "total_frequency": {"$sum": "$frequency"}
        }},
        {"$sort": {"total_frequency": -1}},
        {"$limit": 10}
    ]
    
    top_categories = await db.improvement_assets.aggregate(pipeline).to_list(10)
    
    # 유형별 통계
    type_pipeline = [
        {"$group": {
            "_id": "$type",
            "count": {"$sum": 1},
            "total_frequency": {"$sum": "$frequency"}
        }}
    ]
    
    by_type = await db.improvement_assets.aggregate(type_pipeline).to_list(10)
    
    return {
        "total_assets": total_assets,
        "top_categories": [
            {
                "hs_code": c["_id"],
                "name": HS_CODE_CATEGORIES.get(c["_id"], {}).get("name", "Unknown"),
                "asset_count": c["count"],
                "total_frequency": c["total_frequency"]
            }
            for c in top_categories
        ],
        "by_type": {
            t["_id"]: {"count": t["count"], "frequency": t["total_frequency"]}
            for t in by_type
        }
    }
