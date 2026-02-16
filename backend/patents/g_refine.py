"""
G: REFINE - 정제 특허 모듈
데이터 정제 및 품질 향상
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import re
import logging

router = APIRouter(prefix="/api/patent/g", tags=["G:REFINE"])
logger = logging.getLogger(__name__)

class RefineRequest(BaseModel):
    """정제 요청"""
    content: str
    options: Dict[str, bool] = {}

# ==================== 데이터 정제 ====================

@router.post("/clean")
async def clean_content(request: RefineRequest):
    """콘텐츠 정제"""
    original = request.content
    cleaned = original
    operations = []
    
    # 1. 공백 정규화
    if request.options.get("normalize_whitespace", True):
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        if cleaned != original:
            operations.append("공백 정규화")
    
    # 2. HTML 태그 제거
    if request.options.get("remove_html", True):
        before = cleaned
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        if cleaned != before:
            operations.append("HTML 태그 제거")
    
    # 3. 특수문자 정리
    if request.options.get("clean_special_chars", False):
        before = cleaned
        cleaned = re.sub(r'[^\w\s가-힣.,!?;:\'"()-]', '', cleaned)
        if cleaned != before:
            operations.append("특수문자 정리")
    
    # 4. URL 제거
    if request.options.get("remove_urls", False):
        before = cleaned
        cleaned = re.sub(r'https?://\S+', '[URL]', cleaned)
        if cleaned != before:
            operations.append("URL 치환")
    
    # 5. 이메일 마스킹
    if request.options.get("mask_emails", True):
        before = cleaned
        cleaned = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', cleaned)
        if cleaned != before:
            operations.append("이메일 마스킹")
    
    return {
        "success": True,
        "original_length": len(original),
        "cleaned_length": len(cleaned),
        "cleaned_content": cleaned,
        "operations": operations,
        "reduction_percent": round((1 - len(cleaned) / len(original)) * 100, 1) if original else 0
    }

@router.post("/normalize")
async def normalize_content(content: str):
    """콘텐츠 정규화"""
    normalized = content
    
    # 유니코드 정규화
    import unicodedata
    normalized = unicodedata.normalize('NFC', normalized)
    
    # 줄바꿈 통일
    normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
    
    # 연속 줄바꿈 제한
    normalized = re.sub(r'\n{3,}', '\n\n', normalized)
    
    return {
        "success": True,
        "normalized_content": normalized,
        "original_length": len(content),
        "normalized_length": len(normalized)
    }

@router.post("/extract-keywords")
async def extract_keywords(content: str, max_keywords: int = 10):
    """키워드 추출"""
    # 간단한 키워드 추출 (빈도 기반)
    words = re.findall(r'\b[가-힣a-zA-Z]{2,}\b', content.lower())
    
    # 불용어 제거
    stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                 '이', '가', '을', '를', '의', '에', '에서', '으로', '로', '와', '과',
                 '그', '이것', '저것', '하다', '있다', '되다'}
    
    filtered_words = [w for w in words if w not in stopwords and len(w) >= 2]
    
    # 빈도 계산
    from collections import Counter
    word_freq = Counter(filtered_words)
    top_keywords = word_freq.most_common(max_keywords)
    
    return {
        "success": True,
        "keywords": [{"word": w, "count": c} for w, c in top_keywords],
        "total_words": len(words),
        "unique_words": len(set(filtered_words))
    }

@router.post("/summarize")
async def summarize_content(content: str, max_length: int = 200):
    """콘텐츠 요약"""
    # 간단한 추출적 요약 (첫 문장들)
    sentences = re.split(r'[.!?]\s+', content)
    
    summary = ""
    for sentence in sentences:
        if len(summary) + len(sentence) <= max_length:
            summary += sentence + ". "
        else:
            break
    
    summary = summary.strip()
    if not summary and sentences:
        summary = sentences[0][:max_length] + "..."
    
    return {
        "success": True,
        "summary": summary,
        "original_length": len(content),
        "summary_length": len(summary),
        "compression_ratio": round(len(summary) / len(content) * 100, 1) if content else 0
    }

@router.get("/refine-options")
async def get_refine_options():
    """정제 옵션 목록"""
    options = [
        {"key": "normalize_whitespace", "name": "공백 정규화", "description": "연속 공백을 단일 공백으로", "default": True},
        {"key": "remove_html", "name": "HTML 태그 제거", "description": "HTML 태그 제거", "default": True},
        {"key": "clean_special_chars", "name": "특수문자 정리", "description": "불필요한 특수문자 제거", "default": False},
        {"key": "remove_urls", "name": "URL 제거", "description": "URL을 [URL]로 치환", "default": False},
        {"key": "mask_emails", "name": "이메일 마스킹", "description": "이메일을 [EMAIL]로 치환", "default": True}
    ]
    return {"success": True, "options": options}
