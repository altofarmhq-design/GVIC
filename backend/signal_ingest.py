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
class ClassificationRatio(BaseModel):
    wanted: int = 5
    unwanted: int = 3
    null: int = 2

class TextSignalRequest(BaseModel):
    type: str = "text"
    content: str
    purpose: str = ""           # 왜 질문하는지
    expected_result: str = ""   # 기대하는 결과
    analysis_type: str = "general"  # 분석 유형: general, code, patent_idea
    classification_ratio: ClassificationRatio = None  # 5:3:2 비율

class UrlSignalRequest(BaseModel):
    url: str
    purpose: str = ""
    expected_result: str = ""
    analysis_type: str = "general"
    classification_ratio: ClassificationRatio = None

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

def extract_text_from_hwp(file_content: bytes) -> str:
    """HWP 파일에서 텍스트 추출 (OLE 기반)"""
    try:
        import olefile
        
        ole = olefile.OleFileIO(io.BytesIO(file_content))
        
        # HWP 파일의 텍스트는 'PrvText' 또는 'BodyText/Section0' 등에 저장됨
        text_parts = []
        
        # PrvText (미리보기 텍스트) 추출 시도
        if ole.exists('PrvText'):
            prv_text = ole.openstream('PrvText').read()
            # UTF-16 LE로 디코딩
            try:
                decoded = prv_text.decode('utf-16-le', errors='ignore')
                text_parts.append(decoded)
            except:
                pass
        
        # BodyText 섹션들 추출 시도
        for entry in ole.listdir():
            entry_path = '/'.join(entry)
            if 'BodyText' in entry_path or 'Section' in entry_path:
                try:
                    stream_data = ole.openstream(entry).read()
                    # 바이너리에서 텍스트 추출 시도
                    for encoding in ['utf-16-le', 'utf-8', 'cp949']:
                        try:
                            decoded = stream_data.decode(encoding, errors='ignore')
                            # 제어 문자 제거
                            cleaned = ''.join(c for c in decoded if c.isprintable() or c in '\n\r\t ')
                            if len(cleaned) > 10:
                                text_parts.append(cleaned)
                            break
                        except:
                            continue
                except:
                    pass
        
        ole.close()
        
        if text_parts:
            return '\n'.join(text_parts)
        else:
            return "[HWP 파일에서 텍스트를 추출할 수 없습니다. 파일이 암호화되었거나 특수 형식일 수 있습니다.]"
            
    except Exception as e:
        return f"[HWP 처리 실패: {str(e)}]"

def extract_text_from_hwpx(file_content: bytes) -> str:
    """HWPX 파일에서 텍스트 추출 (ZIP + XML 기반)"""
    try:
        import zipfile
        from lxml import etree
        
        # HWPX는 ZIP 압축 파일
        with zipfile.ZipFile(io.BytesIO(file_content), 'r') as zf:
            text_parts = []
            
            # Contents 폴더 내의 XML 파일들에서 텍스트 추출
            for filename in zf.namelist():
                if filename.startswith('Contents/') and filename.endswith('.xml'):
                    try:
                        xml_content = zf.read(filename)
                        root = etree.fromstring(xml_content)
                        
                        # 모든 텍스트 노드 추출
                        for elem in root.iter():
                            if elem.text and elem.text.strip():
                                text_parts.append(elem.text.strip())
                            if elem.tail and elem.tail.strip():
                                text_parts.append(elem.tail.strip())
                    except:
                        continue
            
            if text_parts:
                return '\n'.join(text_parts)
            else:
                return "[HWPX 파일에서 텍스트를 추출할 수 없습니다.]"
                
    except Exception as e:
        return f"[HWPX 처리 실패: {str(e)}]"

def extract_text_from_docx(file_content: bytes) -> str:
    """DOCX 파일에서 텍스트 추출"""
    try:
        from docx import Document
        
        doc = Document(io.BytesIO(file_content))
        text_parts = []
        
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text)
        
        # 테이블 내용도 추출
        for table in doc.tables:
            for row in table.rows:
                row_text = ' | '.join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    text_parts.append(row_text)
        
        return '\n'.join(text_parts) if text_parts else "[DOCX 파일에서 텍스트를 추출할 수 없습니다.]"
        
    except Exception as e:
        return f"[DOCX 처리 실패: {str(e)}]"

# 지원하는 파일 형식 목록
SUPPORTED_FORMATS = {
    # 문서
    'pdf': 'PDF 문서',
    'hwp': '한글 문서',
    'hwpx': '한글 문서 (HWPX)',
    'docx': 'Word 문서',
    'txt': '텍스트',
    # 스프레드시트
    'xlsx': 'Excel',
    'xls': 'Excel',
    'csv': 'CSV',
    # 이미지
    'jpg': '이미지',
    'jpeg': '이미지',
    'png': '이미지',
    'gif': '이미지',
    'webp': '이미지',
    'bmp': '이미지',
    # 코드 파일
    'py': 'Python',
    'js': 'JavaScript',
    'ts': 'TypeScript',
    'jsx': 'React JSX',
    'tsx': 'React TSX',
    'java': 'Java',
    'c': 'C',
    'cpp': 'C++',
    'cs': 'C#',
    'go': 'Go',
    'rs': 'Rust',
    'rb': 'Ruby',
    'php': 'PHP',
    'swift': 'Swift',
    'kt': 'Kotlin',
    'html': 'HTML',
    'css': 'CSS',
    'scss': 'SCSS',
    'sql': 'SQL',
    'json': 'JSON',
    'xml': 'XML',
    'yaml': 'YAML',
    'yml': 'YAML',
    'md': 'Markdown',
    'sh': 'Shell Script',
    'bat': 'Batch Script'
}

# 코드 파일 확장자 목록
CODE_EXTENSIONS = [
    'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'cs', 'go', 'rs', 
    'rb', 'php', 'swift', 'kt', 'html', 'css', 'scss', 'sql', 'json', 
    'xml', 'yaml', 'yml', 'sh', 'bat'
]

def is_code_file(ext: str) -> bool:
    """코드 파일인지 확인"""
    return ext.lower() in CODE_EXTENSIONS

def get_recommended_analysis_type(ext: str) -> str:
    """파일 확장자에 따른 추천 분석 유형"""
    if is_code_file(ext):
        return "code"
    return "general"

def get_supported_extensions() -> list:
    """지원하는 파일 확장자 목록 반환"""
    return list(SUPPORTED_FORMATS.keys())

# API Endpoints - 파이프라인 연동
# MongoDB와 파이프라인 엔진은 server.py에서 초기화됨

@router.get("/supported-formats")
async def get_supported_formats():
    """지원하는 파일 형식 목록 조회"""
    formats_by_category = {
        "문서": [
            {"ext": "pdf", "name": "PDF 문서", "formats": ".pdf"},
            {"ext": "hwp", "name": "한글 문서", "formats": ".hwp"},
            {"ext": "hwpx", "name": "한글 문서 (OOXML)", "formats": ".hwpx"},
            {"ext": "docx", "name": "Word 문서", "formats": ".docx"},
            {"ext": "txt", "name": "텍스트", "formats": ".txt"}
        ],
        "스프레드시트": [
            {"ext": "xlsx", "name": "Excel", "formats": ".xlsx, .xls"},
            {"ext": "csv", "name": "CSV", "formats": ".csv"}
        ],
        "이미지": [
            {"ext": "image", "name": "이미지", "formats": ".jpg, .jpeg, .png, .gif, .webp, .bmp"}
        ],
        "코드": [
            {"ext": "code", "name": "프로그래밍 코드", "formats": ".py, .js, .ts, .java, .c, .cpp, .go, .html, .css, .sql 등"}
        ]
    }
    return {
        "supported_formats": SUPPORTED_FORMATS,
        "by_category": formats_by_category,
        "all_extensions": list(SUPPORTED_FORMATS.keys()),
        "code_extensions": CODE_EXTENSIONS
    }

@router.get("/analysis-types")
async def get_analysis_types():
    """사용 가능한 분석 유형 조회"""
    from core.ai_analyzer import get_analysis_types
    return {
        "analysis_types": get_analysis_types(),
        "default": "general"
    }

@router.post("/ingest")
async def ingest_text_signal(request: TextSignalRequest, current_user: dict = Depends(get_current_user_simple)):
    """텍스트 시그널 입력 → 파이프라인 자동 실행 + AI 분석"""
    if not request.content.strip():
        raise HTTPException(status_code=400, detail="내용이 비어있습니다")
    
    # 파이프라인 엔진 가져오기
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    # 분류 비율 설정 (기본값: 5:3:2)
    ratio = request.classification_ratio or ClassificationRatio()
    classification_ratio = {
        "wanted": ratio.wanted,
        "unwanted": ratio.unwanted,
        "null": ratio.null
    }
    
    # AI 분석 수행 (분석 유형 포함)
    from core.ai_analyzer import analyze_signal
    ai_result = await analyze_signal(
        content=request.content,
        purpose=request.purpose,
        expected_result=request.expected_result,
        analysis_type=request.analysis_type
    )
    
    # 파이프라인 실행 (비율 포함)
    result = await pipeline.create_signal(
        signal_type="text",
        content=request.content,
        source="direct_input",
        metadata={
            "input_method": "text",
            "purpose": request.purpose,
            "expected_result": request.expected_result,
            "analysis_type": request.analysis_type,
            "classification_ratio": classification_ratio,
            "ai_analysis": ai_result
        },
        user_id=current_user.get("sub")
    )
    
    # 관련 자산 추천 추가
    related_assets = await pipeline.find_related_assets(request.content, request.purpose)
    result["related_assets"] = related_assets
    
    # AI 분석 결과 추가
    result["ai_analysis"] = ai_result
    
    return result

def detect_shopping_platform(url: str) -> str:
    """URL에서 쇼핑몰 플랫폼 감지"""
    url_lower = url.lower()
    
    if "smartstore.naver.com" in url_lower or "brand.naver.com" in url_lower or "shopping.naver.com" in url_lower:
        return "naver"
    elif "coupang.com" in url_lower:
        return "coupang"
    elif "11st.co.kr" in url_lower or "11번가" in url_lower:
        return "11st"
    elif "gmarket.co.kr" in url_lower:
        return "gmarket"
    elif "auction.co.kr" in url_lower:
        return "auction"
    elif "yes24.com" in url_lower:
        return "yes24"
    elif "aliexpress" in url_lower:
        return "aliexpress"
    elif "amazon" in url_lower:
        return "amazon"
    else:
        return "generic"

@router.post("/ingest/url")
async def ingest_url_signal(request: UrlSignalRequest, current_user: dict = Depends(get_current_user_simple)):
    """URL 시그널 입력 → 파이프라인 자동 실행 (쇼핑몰 URL은 리뷰 크롤러로 라우팅)"""
    if not request.url.strip():
        raise HTTPException(status_code=400, detail="URL이 비어있습니다")
    
    if not request.url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="올바른 URL 형식이 아닙니다")
    
    # 쇼핑몰 플랫폼 감지
    platform = detect_shopping_platform(request.url)
    
    # 쇼핑몰 URL인 경우 리뷰 크롤러로 라우팅
    if platform != "generic":
        try:
            from review_crawler import crawl_naver_reviews, crawl_coupang_reviews, crawl_generic_reviews
            from server import get_pipeline_engine, db
            import uuid
            
            # 플랫폼별 크롤러 선택
            product_info = None
            reviews = []
            
            if platform == "naver":
                product_info, reviews = await crawl_naver_reviews(request.url, 20)
            elif platform == "coupang":
                product_info, reviews = await crawl_coupang_reviews(request.url, 20)
            else:
                product_info, reviews = await crawl_generic_reviews(request.url, 20)
            
            # 크롤링 결과가 있으면 시그널로 변환
            pipeline = get_pipeline_engine()
            user_id = current_user.get("sub")
            
            # 크롤링 결과 저장
            crawl_id = f"CRL_{uuid.uuid4().hex[:12]}"
            crawl_record = {
                "crawl_id": crawl_id,
                "url": request.url,
                "platform": platform,
                "user_id": user_id,
                "product_info": product_info.dict() if product_info else None,
                "review_count": len(reviews),
                "reviews": [r.dict() for r in reviews],
                "crawled_at": datetime.now(timezone.utc).isoformat()
            }
            await db.crawl_results.insert_one(crawl_record)
            
            signals_created = 0
            signal_ids = []
            
            for review in reviews[:20]:
                try:
                    signal_content = f"[구매후기] {product_info.product_name if product_info else '상품'}\n"
                    if review.rating:
                        signal_content += f"평점: {review.rating}점\n"
                    signal_content += f"내용: {review.content}"
                    
                    signal_result = await pipeline.create_signal(
                        signal_type="text",
                        content=signal_content,
                        source=f"crawl:{platform}",
                        metadata={
                            "input_method": "url_crawl",
                            "crawl_id": crawl_id,
                            "platform": platform,
                            "review_id": review.review_id,
                            "product_name": product_info.product_name if product_info else None,
                            "rating": review.rating,
                            "analysis_type": request.analysis_type
                        },
                        user_id=user_id
                    )
                    signals_created += 1
                    signal_ids.append(signal_result.get("signal_id"))
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Signal creation error: {e}")
                    continue
            
            return {
                "success": True,
                "input_type": "shopping_url",
                "platform": platform,
                "crawl_id": crawl_id,
                "product_name": product_info.product_name if product_info else "상품 정보 없음",
                "reviews_found": len(reviews),
                "signals_created": signals_created,
                "signal_ids": signal_ids[:5],  # 처음 5개만 반환
                "message": f"{platform} 쇼핑몰에서 {len(reviews)}개 리뷰를 크롤링하고 {signals_created}개 시그널을 생성했습니다."
            }
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Shopping URL crawl error: {e}")
            # 크롤링 실패 시 일반 URL 처리로 폴백
            pass
    
    # 일반 URL 처리 (쇼핑몰이 아니거나 크롤링 실패 시)
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
    result["input_type"] = "generic_url"
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
            
            # 지원하지 않는 형식 체크
            if ext not in SUPPORTED_FORMATS:
                supported_list = ', '.join([f'.{e}' for e in SUPPORTED_FORMATS.keys()])
                results.append({
                    "filename": filename,
                    "success": False,
                    "error": f"지원하지 않는 파일 형식입니다 (.{ext})",
                    "supported_formats": supported_list
                })
                continue
            
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
            
            elif ext == 'hwp':
                extracted_text = extract_text_from_hwp(content)
                file_type = "hwp"
            
            elif ext == 'hwpx':
                extracted_text = extract_text_from_hwpx(content)
                file_type = "hwpx"
            
            elif ext == 'docx':
                extracted_text = extract_text_from_docx(content)
                file_type = "docx"
            
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
