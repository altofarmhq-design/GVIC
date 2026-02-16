"""
SaaS Q&A Manager - 이커머스 Q&A/CS 통합 관리
- Q&A 수집 및 통합
- FAQ 자동 생성
- 응답 템플릿 관리
- CS 인사이트 분석
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import os
import jwt
import logging

router = APIRouter(prefix="/api/saas/qa", tags=["saas-qa"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# ==================== Models ====================

class QAItem(BaseModel):
    """Q&A 항목"""
    question: str = Field(..., description="질문 내용")
    answer: Optional[str] = Field(None, description="답변 내용")
    category: str = Field("general", description="카테고리")
    platform: str = Field("unknown", description="플랫폼")
    product_id: Optional[str] = None
    status: str = Field("pending", description="상태: pending, answered, archived")
    created_at: Optional[str] = None

class FAQTemplate(BaseModel):
    """FAQ 템플릿"""
    question_pattern: str
    answer_template: str
    category: str
    usage_count: int = 0
    created_at: str

class ResponseTemplate(BaseModel):
    """응답 템플릿"""
    name: str
    category: str
    template_text: str
    variables: List[str] = []
    usage_count: int = 0

class BatchQARequest(BaseModel):
    """배치 Q&A 등록"""
    items: List[QAItem]
    product_id: Optional[str] = None

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

# ==================== QA Manager Class ====================

class QAManager:
    """Q&A/CS 통합 관리자"""
    
    # Q&A 카테고리
    CATEGORIES = {
        "delivery": "배송",
        "product": "상품",
        "exchange": "교환/반품",
        "payment": "결제",
        "size": "사이즈",
        "stock": "재고",
        "event": "이벤트/쿠폰",
        "general": "기타"
    }
    
    # 기본 응답 템플릿
    DEFAULT_TEMPLATES = {
        "delivery": "안녕하세요, {store_name}입니다.\n배송 관련 문의 주셨군요.\n{answer}\n감사합니다.",
        "exchange": "안녕하세요, {store_name}입니다.\n교환/반품 문의 감사합니다.\n{answer}\n추가 문의사항 있으시면 말씀해주세요.",
        "product": "안녕하세요, {store_name}입니다.\n상품 문의 감사합니다.\n{answer}\n좋은 하루 되세요!",
        "general": "안녕하세요, {store_name}입니다.\n문의 주셔서 감사합니다.\n{answer}\n감사합니다."
    }
    
    def __init__(self, db=None):
        self.db = db
    
    def categorize_question(self, question: str) -> str:
        """질문 카테고리 자동 분류"""
        question_lower = question.lower()
        
        category_keywords = {
            "delivery": ["배송", "도착", "택배", "운송장", "언제", "며칠"],
            "exchange": ["교환", "반품", "환불", "취소", "반송", "하자"],
            "product": ["상품", "제품", "색상", "소재", "재질", "원산지"],
            "size": ["사이즈", "크기", "치수", "피팅", "큰", "작은"],
            "stock": ["재입고", "품절", "재고", "입고"],
            "payment": ["결제", "카드", "할부", "계좌", "현금"],
            "event": ["쿠폰", "할인", "이벤트", "적립"]
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in question_lower for kw in keywords):
                return category
        
        return "general"
    
    def suggest_answer(self, question: str, category: str) -> Optional[str]:
        """자동 답변 제안"""
        # FAQ 기반 답변 매칭 (간단 버전)
        faq_answers = {
            "delivery": {
                "언제": "주문 확인 후 1-3 영업일 내 출고되며, 출고 후 1-2일 내 수령하실 수 있습니다.",
                "배송비": "50,000원 이상 구매 시 무료배송이며, 미만 시 3,000원의 배송비가 발생합니다.",
                "운송장": "배송이 시작되면 문자/카카오톡으로 운송장 번호를 안내해드립니다."
            },
            "exchange": {
                "교환": "수령 후 7일 이내 교환/반품 신청이 가능합니다. 단순 변심 시 왕복 배송비 부담입니다.",
                "환불": "반품 상품 확인 후 2-3 영업일 내 환불 처리됩니다.",
                "불량": "불량 상품의 경우 배송비 무료로 교환/환불 처리해드립니다."
            },
            "size": {
                "사이즈": "상품 상세페이지에 실측 사이즈가 안내되어 있습니다. 평소 입으시는 사이즈 참고 부탁드립니다.",
                "추천": "고객님의 키와 체중을 알려주시면 사이즈 추천 도와드리겠습니다."
            },
            "stock": {
                "재입고": "현재 재입고 일정이 미정입니다. 재입고 알림 신청을 해주시면 입고 시 안내드리겠습니다.",
                "품절": "해당 옵션은 현재 품절 상태입니다. 다른 옵션 검토 부탁드립니다."
            }
        }
        
        category_faqs = faq_answers.get(category, {})
        
        for keyword, answer in category_faqs.items():
            if keyword in question:
                return answer
        
        return None
    
    def generate_faq_from_questions(self, questions: List[QAItem]) -> List[Dict[str, Any]]:
        """질문들로부터 FAQ 생성"""
        # 유사 질문 그룹핑 (간단 버전)
        category_questions = {}
        
        for q in questions:
            cat = self.categorize_question(q.question)
            if cat not in category_questions:
                category_questions[cat] = []
            category_questions[cat].append(q)
        
        faqs = []
        for category, qs in category_questions.items():
            if len(qs) >= 2:  # 2개 이상 유사 질문이 있을 때 FAQ 생성
                # 가장 대표적인 질문 선택 (가장 짧은 것)
                representative = min(qs, key=lambda x: len(x.question))
                
                # 답변이 있는 경우 사용
                answered = [q for q in qs if q.answer]
                answer = answered[0].answer if answered else self.suggest_answer(representative.question, category)
                
                faqs.append({
                    "category": category,
                    "category_name": self.CATEGORIES.get(category, "기타"),
                    "question": representative.question,
                    "answer": answer or "답변 준비 중입니다.",
                    "frequency": len(qs),
                    "sources": [q.platform for q in qs]
                })
        
        return sorted(faqs, key=lambda x: x["frequency"], reverse=True)
    
    def get_response_template(self, category: str, store_name: str, answer: str) -> str:
        """응답 템플릿 적용"""
        template = self.DEFAULT_TEMPLATES.get(category, self.DEFAULT_TEMPLATES["general"])
        return template.format(store_name=store_name, answer=answer)


# ==================== API Endpoints ====================

@router.post("/items")
async def create_qa_items(
    request: BatchQARequest,
    current_user: dict = Depends(get_current_user)
):
    """Q&A 항목 배치 등록"""
    from server import db
    
    user_id = current_user.get("user_id")
    manager = QAManager(db)
    
    created_items = []
    for item in request.items:
        qa_id = f"QA_{uuid.uuid4().hex[:12]}"
        
        # 카테고리 자동 분류
        category = item.category
        if category == "general":
            category = manager.categorize_question(item.question)
        
        # 자동 답변 제안
        suggested_answer = manager.suggest_answer(item.question, category)
        
        qa_record = {
            "qa_id": qa_id,
            "user_id": user_id,
            "product_id": request.product_id or item.product_id,
            "question": item.question,
            "answer": item.answer,
            "suggested_answer": suggested_answer,
            "category": category,
            "category_name": QAManager.CATEGORIES.get(category, "기타"),
            "platform": item.platform,
            "status": item.status,
            "created_at": item.created_at or datetime.now(timezone.utc).isoformat()
        }
        
        await db.qa_items.insert_one(qa_record)
        created_items.append({
            "qa_id": qa_id,
            "category": category,
            "has_suggested_answer": suggested_answer is not None
        })
    
    return {
        "success": True,
        "created_count": len(created_items),
        "items": created_items
    }


@router.get("/items")
async def get_qa_items(
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Q&A 항목 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    query = {"user_id": user_id}
    if status:
        query["status"] = status
    if category:
        query["category"] = category
    
    items = await db.qa_items.find(
        query, {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return {
        "items": items,
        "total": len(items)
    }


@router.put("/items/{qa_id}/answer")
async def update_qa_answer(
    qa_id: str,
    answer: str,
    current_user: dict = Depends(get_current_user)
):
    """Q&A 답변 등록/수정"""
    from server import db
    
    result = await db.qa_items.update_one(
        {"qa_id": qa_id},
        {"$set": {
            "answer": answer,
            "status": "answered",
            "answered_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Q&A 항목을 찾을 수 없습니다")
    
    return {"success": True, "qa_id": qa_id}


@router.post("/generate-faq")
async def generate_faq(
    current_user: dict = Depends(get_current_user)
):
    """FAQ 자동 생성"""
    from server import db
    
    user_id = current_user.get("user_id")
    manager = QAManager(db)
    
    # 모든 Q&A 항목 조회
    items_cursor = db.qa_items.find(
        {"user_id": user_id},
        {"_id": 0}
    )
    items = await items_cursor.to_list(500)
    
    if not items:
        return {
            "success": False,
            "message": "Q&A 데이터가 없습니다. 먼저 Q&A를 등록해주세요.",
            "faqs": []
        }
    
    # QAItem으로 변환
    qa_items = [QAItem(**{
        "question": item.get("question", ""),
        "answer": item.get("answer"),
        "category": item.get("category", "general"),
        "platform": item.get("platform", "unknown"),
        "status": item.get("status", "pending")
    }) for item in items]
    
    # FAQ 생성
    faqs = manager.generate_faq_from_questions(qa_items)
    
    # DB에 저장 및 응답용 리스트 생성
    response_faqs = []
    for faq in faqs:
        faq_record = {
            **faq,
            "faq_id": f"FAQ_{uuid.uuid4().hex[:8]}",
            "user_id": user_id,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.generated_faqs.insert_one(faq_record)
        # _id 제외하고 응답에 추가
        response_faqs.append({k: v for k, v in faq_record.items() if k != "_id"})
    
    return {
        "success": True,
        "total_questions": len(qa_items),
        "faqs_generated": len(response_faqs),
        "faqs": response_faqs
    }


@router.get("/faqs")
async def get_faqs(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """생성된 FAQ 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    query = {"user_id": user_id}
    if category:
        query["category"] = category
    
    faqs = await db.generated_faqs.find(
        query, {"_id": 0}
    ).sort("frequency", -1).to_list(100)
    
    return {
        "faqs": faqs,
        "total": len(faqs)
    }


@router.post("/templates")
async def create_response_template(
    template: ResponseTemplate,
    current_user: dict = Depends(get_current_user)
):
    """응답 템플릿 생성"""
    from server import db
    
    user_id = current_user.get("user_id")
    template_id = f"TPL_{uuid.uuid4().hex[:8]}"
    
    template_record = {
        "template_id": template_id,
        "user_id": user_id,
        "name": template.name,
        "category": template.category,
        "template_text": template.template_text,
        "variables": template.variables,
        "usage_count": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.response_templates.insert_one(template_record)
    
    return {
        "success": True,
        "template_id": template_id
    }


@router.get("/templates")
async def get_response_templates(
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """응답 템플릿 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    query = {"user_id": user_id}
    if category:
        query["category"] = category
    
    templates = await db.response_templates.find(
        query, {"_id": 0}
    ).to_list(100)
    
    return {
        "templates": templates,
        "total": len(templates)
    }


@router.post("/apply-template")
async def apply_response_template(
    template_id: str,
    store_name: str,
    answer: str,
    current_user: dict = Depends(get_current_user)
):
    """응답 템플릿 적용"""
    from server import db
    
    template = await db.response_templates.find_one(
        {"template_id": template_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다")
    
    # 템플릿 적용
    response = template["template_text"].format(
        store_name=store_name,
        answer=answer
    )
    
    # 사용 횟수 증가
    await db.response_templates.update_one(
        {"template_id": template_id},
        {"$inc": {"usage_count": 1}}
    )
    
    return {
        "success": True,
        "response": response
    }


@router.get("/stats")
async def get_qa_stats(
    current_user: dict = Depends(get_current_user)
):
    """Q&A 통계"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    # 전체 통계
    total_count = await db.qa_items.count_documents({"user_id": user_id})
    pending_count = await db.qa_items.count_documents({"user_id": user_id, "status": "pending"})
    answered_count = await db.qa_items.count_documents({"user_id": user_id, "status": "answered"})
    
    # 카테고리별 통계
    category_stats = {}
    for cat_key, cat_name in QAManager.CATEGORIES.items():
        count = await db.qa_items.count_documents({"user_id": user_id, "category": cat_key})
        if count > 0:
            category_stats[cat_key] = {"name": cat_name, "count": count}
    
    return {
        "total": total_count,
        "pending": pending_count,
        "answered": answered_count,
        "answer_rate": round(answered_count / total_count * 100, 1) if total_count > 0 else 0,
        "by_category": category_stats
    }
