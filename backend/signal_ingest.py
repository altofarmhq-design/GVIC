"""
GVIC Signal Ingestion Module
- 텍스트, URL, 파일 등 다양한 형태의 시그널 입력 처리
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
import httpx
from bs4 import BeautifulSoup
import pandas as pd
import PyPDF2
import io
import os
from datetime import datetime, timezone
from bson import ObjectId
import jwt

router = APIRouter(prefix="/api/signal", tags=["signal"])

# JWT Secret from env (must match auth.py)
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# Simple auth dependency for this module
async def get_current_user_simple(authorization: str = Header(None)):
    """간단한 인증 확인"""
    import logging
    logger = logging.getLogger(__name__)
    
    if not authorization:
        logger.error("No authorization header")
        raise HTTPException(status_code=401, detail="인증이 필요합니다. 다시 로그인해주세요.")
    
    try:
        # Bearer 토큰 추출
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        # 토큰이 비어있거나 'null', 'undefined'인 경우
        if not token or token in ('null', 'undefined', ''):
            logger.error(f"Empty or invalid token: {token}")
            raise HTTPException(status_code=401, detail="토큰이 없습니다. 다시 로그인해주세요.")
        
        # JWT 형식 검증 (3개 세그먼트)
        if token.count('.') != 2:
            logger.error(f"Invalid token format: {token[:50]}...")
            raise HTTPException(status_code=401, detail="토큰 형식이 올바르지 않습니다. 다시 로그인해주세요.")
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        logger.error("Token expired")
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다. 다시 로그인해주세요.")
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token error: {str(e)}")
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다. 다시 로그인해주세요.")

# Request Models
class TextSignalRequest(BaseModel):
    type: str = "text"
    content: str
    purpose: str = ""           # 왜 질문하는지
    expected_result: str = ""   # 기대하는 결과

class UrlSignalRequest(BaseModel):
    url: str
    purpose: str = ""
    expected_result: str = ""

# Helper Functions
def generate_signal_id():
    """시그널 고유 ID 생성"""
    return f"SIG_{ObjectId()}"

async def extract_text_from_url(url: str) -> str:
    """URL에서 텍스트 추출"""
    try:
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 불필요한 태그 제거
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                tag.decompose()
            
            # 텍스트 추출
            text = soup.get_text(separator='\n', strip=True)
            
            # 빈 줄 정리
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"URL 처리 실패: {str(e)}")

def extract_text_from_pdf(file_content: bytes) -> str:
    """PDF에서 텍스트 추출"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text_parts = []
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return '\n'.join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"PDF 처리 실패: {str(e)}")

def extract_text_from_excel(file_content: bytes, filename: str) -> str:
    """Excel/CSV에서 텍스트 추출"""
    try:
        ext = filename.split('.')[-1].lower()
        
        if ext == 'csv':
            df = pd.read_csv(io.BytesIO(file_content))
        else:
            df = pd.read_excel(io.BytesIO(file_content))
        
        # DataFrame을 텍스트로 변환
        text_parts = []
        for _, row in df.iterrows():
            row_text = ' | '.join([str(v) for v in row.values if pd.notna(v)])
            if row_text.strip():
                text_parts.append(row_text)
        
        return '\n'.join(text_parts)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Excel/CSV 처리 실패: {str(e)}")

def extract_text_from_txt(file_content: bytes) -> str:
    """TXT 파일에서 텍스트 추출"""
    try:
        # 여러 인코딩 시도
        for encoding in ['utf-8', 'cp949', 'euc-kr', 'latin-1']:
            try:
                return file_content.decode(encoding)
            except:
                continue
        return file_content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"TXT 처리 실패: {str(e)}")

# API Endpoints - 파이프라인 연동
# MongoDB와 파이프라인 엔진은 server.py에서 초기화됨

@router.post("/ingest")
async def ingest_text_signal(request: TextSignalRequest, current_user: dict = Depends(get_current_user_simple)):
    """텍스트 시그널 입력 → 파이프라인 자동 실행"""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="내용이 비어있습니다")
    
    # 파이프라인 엔진 가져오기
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    # 파이프라인 실행
    result = await pipeline.create_signal(
        signal_type="text",
        content=request.content,
        source="direct_input",
        metadata={"input_method": "text"},
        user_id=current_user.get("sub")
    )
    
    return result

@router.post("/ingest/url")
async def ingest_url_signal(request: UrlSignalRequest, current_user: dict = Depends(get_current_user_simple)):
    """URL 시그널 입력 → 파이프라인 자동 실행"""
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL이 비어있습니다")
    
    if not request.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="올바른 URL 형식이 아닙니다")
    
    # 텍스트 추출
    extracted_text = await extract_text_from_url(request.url)
    
    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="URL에서 텍스트를 추출할 수 없습니다")
    
    # 파이프라인 실행
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    result = await pipeline.create_signal(
        signal_type="url",
        content=extracted_text,
        source=request.url,
        metadata={"input_method": "url", "original_url": request.url},
        user_id=current_user.get("sub")
    )
    
    result["extracted_text"] = extracted_text[:2000]  # 프리뷰용
    return result

@router.post("/ingest/files")
async def ingest_file_signals(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user_simple)
):
    """파일 시그널 입력 - 다양한 형식 지원"""
    if not files:
        raise HTTPException(status_code=400, detail="파일이 없습니다")
    
    results = []
    
    for file in files:
        try:
            filename = file.filename
            ext = filename.split('.')[-1].lower()
            content = await file.read()
            
            extracted_text = ""
            file_type = ""
            
            # 파일 형식별 처리
            if ext == 'pdf':
                extracted_text = extract_text_from_pdf(content)
                file_type = "pdf"
            
            elif ext in ['xlsx', 'xls']:
                extracted_text = extract_text_from_excel(content, filename)
                file_type = "excel"
            
            elif ext == 'csv':
                extracted_text = extract_text_from_excel(content, filename)
                file_type = "csv"
            
            elif ext == 'txt':
                extracted_text = extract_text_from_txt(content)
                file_type = "txt"
            
            elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                # 이미지는 OCR 처리 필요 (현재는 메타데이터만)
                file_type = "image"
                extracted_text = f"[이미지 파일: {filename}] - OCR 처리 준비 중"
            
            else:
                file_type = "unknown"
                extracted_text = f"[지원하지 않는 형식: {ext}]"
            
            # 파이프라인 실행
            from server import get_pipeline_engine
            pipeline = get_pipeline_engine()
            
            pipeline_result = await pipeline.create_signal(
                signal_type="file",
                content=extracted_text,
                source=filename,
                metadata={
                    "input_method": "file",
                    "filename": filename,
                    "file_type": file_type,
                    "file_size": len(content)
                },
                user_id=current_user.get("sub")
            )
            
            results.append({
                "signal_id": pipeline_result.get("signal_id"),
                "filename": filename,
                "file_type": file_type,
                "file_size": len(content),
                "category": pipeline_result.get("category"),
                "stages_completed": pipeline_result.get("stages_completed"),
                "extracted_text": extracted_text[:500] if extracted_text else "",
                "success": pipeline_result.get("success", False)
            })
            
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    success_count = sum(1 for r in results if r.get('success'))
    
    return {
        "success": True,
        "total_files": len(files),
        "processed": success_count,
        "failed": len(files) - success_count,
        "results": results,
        "message": f"{success_count}개 파일 파이프라인 처리 완료",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
