"""
GVIC 쇼핑몰 구매후기 크롤링 모듈
- 쇼핑몰 URL에서 구매후기 추출
- 지원: 네이버 스토어, 쿠팡, 11번가, G마켓, 옥션 등
- 크롤링된 후기를 시그널로 변환
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
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

router = APIRouter(prefix="/api/crawl", tags=["crawl"])
logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "gvic-engine-secret-key-change-in-production")

# 크롤링 설정
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
REQUEST_TIMEOUT = 30

# ==================== Models ====================

class CrawlRequest(BaseModel):
    url: str = Field(..., description="크롤링할 쇼핑몰 URL")
    crawl_type: str = Field("reviews", description="크롤링 유형: reviews, product_info, all")
    max_reviews: int = Field(50, description="최대 리뷰 수")
    convert_to_signals: bool = Field(True, description="크롤링 결과를 시그널로 변환")

class ReviewData(BaseModel):
    review_id: str
    author: Optional[str] = None
    rating: Optional[float] = None
    content: str
    date: Optional[str] = None
    helpful_count: Optional[int] = 0
    images: List[str] = []
    purchase_option: Optional[str] = None  # 구매 옵션 (색상, 사이즈 등)

class ProductInfo(BaseModel):
    product_name: str
    price: Optional[str] = None
    category: Optional[str] = None
    seller: Optional[str] = None
    rating_avg: Optional[float] = None
    review_count: Optional[int] = None
    url: str

class CrawlResult(BaseModel):
    success: bool
    url: str
    platform: str
    product_info: Optional[ProductInfo] = None
    reviews: List[ReviewData] = []
    total_reviews: int
    crawled_at: str
    signals_created: int = 0

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

def detect_platform(url: str) -> str:
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
        return "unknown"

async def fetch_html(url: str, headers: dict = None) -> str:
    """URL에서 HTML 가져오기"""
    default_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    if headers:
        default_headers.update(headers)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=default_headers, timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return ""
    except Exception as e:
        logger.error(f"Fetch error for {url}: {str(e)}")
        return ""

# ==================== 플랫폼별 크롤러 ====================

class NaverReviewCrawler:
    """네이버 스마트스토어 리뷰 크롤러 (페이지네이션 지원)"""
    
    REVIEWS_PER_PAGE = 20
    MAX_PAGES = 50  # 최대 페이지 수 제한
    
    def __init__(self):
        self.session = None
    
    async def extract_product_id(self, url: str) -> Optional[str]:
        """URL에서 상품 ID 추출"""
        # smartstore.naver.com/storename/products/12345
        match = re.search(r'/products/(\d+)', url)
        if match:
            return match.group(1)
        
        # shopping.naver.com/...productId=12345
        match = re.search(r'productId=(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    async def get_review_api_url(self, store_url: str, product_id: str, page: int) -> str:
        """리뷰 API URL 생성"""
        # 네이버 스마트스토어 리뷰 API 패턴
        return f"{store_url}/reviews?page={page}&size={self.REVIEWS_PER_PAGE}"
    
    async def crawl(self, url: str, max_reviews: int) -> tuple:
        """네이버 리뷰 크롤링 (페이지네이션)"""
        all_reviews = []
        product_info = None
        
        # 첫 페이지에서 상품 정보 추출
        html = await fetch_html(url)
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            product_info = await self._extract_product_info(soup, url)
        
        # 페이지별 크롤링
        pages_needed = min((max_reviews // self.REVIEWS_PER_PAGE) + 1, self.MAX_PAGES)
        
        for page in range(1, pages_needed + 1):
            if len(all_reviews) >= max_reviews:
                break
            
            page_reviews = await self._crawl_page(url, page)
            all_reviews.extend(page_reviews)
            
            # 리뷰가 더 없으면 중단
            if len(page_reviews) < self.REVIEWS_PER_PAGE:
                break
            
            # 요청 간 딜레이
            await asyncio.sleep(0.5)
        
        return product_info, all_reviews[:max_reviews]
    
    async def _extract_product_info(self, soup: BeautifulSoup, url: str) -> Optional[ProductInfo]:
        """상품 정보 추출"""
        try:
            product_name = soup.select_one('h3._22kNQuEXmb, .product_title, h2.title, h1[class*="product"]')
            if product_name:
                info = ProductInfo(
                    product_name=product_name.get_text(strip=True),
                    url=url
                )
                
                # 가격 추출
                price_elem = soup.select_one('._1LY7DqCnwR, .price_num, span.price, [class*="price"]')
                if price_elem:
                    info.price = price_elem.get_text(strip=True)
                
                # 평점 추출
                rating_elem = soup.select_one('[class*="rating-avg"], .review_score')
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                    if rating_match:
                        info.rating_avg = float(rating_match.group(1))
                
                # 리뷰 수 추출
                review_count_elem = soup.select_one('[class*="review-count"], .review_cnt')
                if review_count_elem:
                    count_text = review_count_elem.get_text(strip=True)
                    count_match = re.search(r'(\d+)', count_text.replace(',', ''))
                    if count_match:
                        info.review_count = int(count_match.group(1))
                
                return info
        except Exception as e:
            logger.error(f"Product info extraction error: {e}")
        
        return None
    
    async def _crawl_page(self, base_url: str, page: int) -> List[ReviewData]:
        """단일 페이지 크롤링"""
        reviews = []
        
        # 리뷰 페이지 URL 구성
        if '?' in base_url:
            page_url = f"{base_url}&reviewPage={page}"
        else:
            page_url = f"{base_url}?reviewPage={page}"
        
        html = await fetch_html(page_url)
        if not html:
            return reviews
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 리뷰 요소 선택자 (여러 버전 지원)
        review_elements = soup.select(
            '.review_item, ._1YShY6EQ56, .review_list_item, '
            '[class*="ReviewItem"], [class*="review-item"], '
            'article[class*="review"]'
        )
        
        for idx, elem in enumerate(review_elements):
            try:
                review = await self._parse_review_element(elem, idx, page)
                if review:
                    reviews.append(review)
            except Exception as e:
                logger.debug(f"Review parse error: {e}")
                continue
        
        return reviews
    
    async def _parse_review_element(self, elem, idx: int, page: int) -> Optional[ReviewData]:
        """리뷰 요소 파싱"""
        # 콘텐츠 추출
        content_elem = elem.select_one(
            '.review_content, ._2FXNMst_ak, .txt, '
            '[class*="content"], [class*="text"], p'
        )
        content = content_elem.get_text(strip=True) if content_elem else ""
        
        if not content or len(content) < 5:
            return None
        
        # 평점 추출
        rating = None
        rating_elem = elem.select_one('[class*="star"], [class*="rating"], .score')
        if rating_elem:
            rating_text = rating_elem.get_text(strip=True)
            rating_match = re.search(r'(\d+)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
        
        # 작성자 추출
        author_elem = elem.select_one('.reviewer, .user_id, [class*="author"], [class*="nickname"]')
        author = author_elem.get_text(strip=True) if author_elem else f"사용자{page}_{idx+1}"
        
        # 날짜 추출
        date_elem = elem.select_one('.date, .review_date, [class*="date"], time')
        date = date_elem.get_text(strip=True) if date_elem else None
        
        # 구매 옵션 추출
        option_elem = elem.select_one('[class*="option"], [class*="variant"]')
        purchase_option = option_elem.get_text(strip=True) if option_elem else None
        
        # 이미지 추출
        images = []
        img_elems = elem.select('img[class*="review"], img[src*="review"]')
        for img in img_elems[:3]:  # 최대 3개
            src = img.get('src') or img.get('data-src')
            if src:
                images.append(src)
        
        return ReviewData(
            review_id=f"naver_{page}_{uuid.uuid4().hex[:8]}",
            author=author,
            rating=rating,
            content=content,
            date=date,
            purchase_option=purchase_option,
            images=images
        )


async def crawl_naver_reviews(url: str, max_reviews: int) -> tuple:
    """네이버 스마트스토어 리뷰 크롤링 (레거시 호환)"""
    crawler = NaverReviewCrawler()
    return await crawler.crawl(url, max_reviews)

async def crawl_coupang_reviews(url: str, max_reviews: int) -> tuple:
    """쿠팡 리뷰 크롤링"""
    html = await fetch_html(url)
    if not html:
        return None, []
    
    soup = BeautifulSoup(html, 'html.parser')
    reviews = []
    product_info = None
    
    # 상품 정보 추출
    try:
        product_name = soup.select_one('h2.prod-buy-header__title, h1.prod-title')
        if product_name:
            product_info = ProductInfo(
                product_name=product_name.get_text(strip=True),
                url=url
            )
            
        price_elem = soup.select_one('.prod-sale-price .total-price, .prod-price')
        if price_elem and product_info:
            product_info.price = price_elem.get_text(strip=True)
            
    except Exception as e:
        logger.error(f"Coupang product info error: {e}")
    
    # 리뷰 추출
    review_elements = soup.select('.sdp-review__article__list__review, .review-content, article[class*="review"]')[:max_reviews]
    
    for idx, elem in enumerate(review_elements):
        try:
            content_elem = elem.select_one('.sdp-review__article__list__review__content, .review-text, [class*="content"]')
            content = content_elem.get_text(strip=True) if content_elem else ""
            
            if not content or len(content) < 5:
                continue
            
            # 평점
            rating = None
            rating_elem = elem.select_one('[class*="star"], .rating')
            if rating_elem:
                # 별점 클래스나 스타일에서 추출
                rating_class = rating_elem.get('class', [])
                for cls in rating_class:
                    if 'rating' in cls:
                        match = re.search(r'(\d+)', cls)
                        if match:
                            rating = float(match.group(1))
                            break
            
            author_elem = elem.select_one('.sdp-review__article__list__info__user__name, .reviewer-name')
            author = author_elem.get_text(strip=True) if author_elem else f"구매자{idx+1}"
            
            # 날짜 추출
            date_elem = elem.select_one('.sdp-review__article__list__info__product-info__reg-date, [class*="date"]')
            date = date_elem.get_text(strip=True) if date_elem else None
            
            # 구매 옵션 추출
            option_elem = elem.select_one('.sdp-review__article__list__info__product-info__name, [class*="option"]')
            purchase_option = option_elem.get_text(strip=True) if option_elem else None
            
            # 도움이 됐어요 수
            helpful_elem = elem.select_one('[class*="helpful"], [class*="vote"]')
            helpful_count = 0
            if helpful_elem:
                helpful_text = helpful_elem.get_text(strip=True)
                helpful_match = re.search(r'(\d+)', helpful_text)
                if helpful_match:
                    helpful_count = int(helpful_match.group(1))
            
            reviews.append(ReviewData(
                review_id=f"coupang_{uuid.uuid4().hex[:8]}",
                author=author,
                rating=rating,
                content=content,
                date=date,
                purchase_option=purchase_option,
                helpful_count=helpful_count
            ))
            
        except Exception as e:
            continue
    
    return product_info, reviews


class CoupangReviewCrawler:
    """쿠팡 리뷰 크롤러 (페이지네이션 지원)
    
    참고: 쿠팡은 JavaScript 렌더링이 필요한 경우가 많아
    완전한 크롤링을 위해서는 Playwright 사용을 권장합니다.
    """
    
    REVIEWS_PER_PAGE = 15
    MAX_PAGES = 30
    
    async def extract_product_id(self, url: str) -> Optional[str]:
        """URL에서 상품 ID 추출"""
        # coupang.com/vp/products/12345
        match = re.search(r'/products/(\d+)', url)
        if match:
            return match.group(1)
        
        # coupang.com/...-P12345...
        match = re.search(r'-P(\d+)', url)
        if match:
            return match.group(1)
        
        return None
    
    async def crawl(self, url: str, max_reviews: int) -> tuple:
        """쿠팡 리뷰 크롤링"""
        # 쿠팡은 API 직접 호출이 어려워 기본 크롤러 사용
        return await crawl_coupang_reviews(url, max_reviews)


async def crawl_generic_reviews(url: str, max_reviews: int) -> tuple:
    """일반적인 리뷰 크롤링 (범용)"""
    html = await fetch_html(url)
    if not html:
        return None, []
    
    soup = BeautifulSoup(html, 'html.parser')
    reviews = []
    product_info = None
    
    # 상품명 추출 시도
    title_selectors = ['h1', 'h2.title', '.product-title', '.prod-name', '[class*="product"][class*="title"]']
    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            product_info = ProductInfo(
                product_name=elem.get_text(strip=True)[:200],
                url=url
            )
            break
    
    # 리뷰 추출 시도 (다양한 셀렉터)
    review_selectors = [
        '.review', '.review-item', '.review_item',
        '[class*="review"][class*="content"]',
        '[class*="comment"]', '.user-review',
        'article[class*="review"]', 'div[class*="review"]'
    ]
    
    found_reviews = []
    for selector in review_selectors:
        elements = soup.select(selector)
        if elements:
            found_reviews = elements[:max_reviews]
            break
    
    for idx, elem in enumerate(found_reviews):
        try:
            # 텍스트 내용 추출
            content = elem.get_text(strip=True)
            
            # 너무 짧거나 긴 내용 필터링
            if len(content) < 10 or len(content) > 5000:
                continue
            
            reviews.append(ReviewData(
                review_id=f"generic_{uuid.uuid4().hex[:8]}",
                author=f"사용자{idx+1}",
                content=content[:1000]
            ))
            
        except Exception:
            continue
    
    return product_info, reviews

# ==================== 메인 크롤링 API ====================

@router.post("/reviews", response_model=CrawlResult)
async def crawl_reviews(
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """
    쇼핑몰 구매후기 크롤링
    
    지원 플랫폼:
    - 네이버 스마트스토어
    - 쿠팡
    - 11번가
    - 기타 (범용 크롤러)
    """
    from server import db
    
    user_id = current_user.get("user_id")
    platform = detect_platform(request.url)
    
    logger.info(f"Crawling reviews from {platform}: {request.url}")
    
    # 플랫폼별 크롤러 선택
    product_info = None
    reviews = []
    
    try:
        if platform == "naver":
            product_info, reviews = await crawl_naver_reviews(request.url, request.max_reviews)
        elif platform == "coupang":
            product_info, reviews = await crawl_coupang_reviews(request.url, request.max_reviews)
        else:
            product_info, reviews = await crawl_generic_reviews(request.url, request.max_reviews)
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"크롤링 오류: {str(e)}")
    
    # 크롤링 결과 저장
    crawl_record = {
        "crawl_id": f"CRL_{uuid.uuid4().hex[:12]}",
        "url": request.url,
        "platform": platform,
        "user_id": user_id,
        "product_info": product_info.dict() if product_info else None,
        "review_count": len(reviews),
        "reviews": [r.dict() for r in reviews],
        "crawled_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.crawl_results.insert_one(crawl_record)
    
    # 시그널로 변환
    signals_created = 0
    if request.convert_to_signals and reviews:
        from server import get_pipeline_engine
        pipeline = get_pipeline_engine()
        
        for review in reviews[:20]:  # 최대 20개까지 시그널 변환
            try:
                signal_content = f"[구매후기] {product_info.product_name if product_info else '상품'}\n"
                if review.rating:
                    signal_content += f"평점: {review.rating}점\n"
                signal_content += f"내용: {review.content}"
                
                await pipeline.create_signal(
                    signal_type="text",
                    content=signal_content,
                    source=f"crawl:{platform}",
                    metadata={
                        "input_method": "url_crawl",
                        "crawl_id": crawl_record["crawl_id"],
                        "platform": platform,
                        "review_id": review.review_id,
                        "product_name": product_info.product_name if product_info else None,
                        "rating": review.rating,
                        "analysis_type": "general"
                    },
                    user_id=user_id
                )
                signals_created += 1
                
            except Exception as e:
                logger.error(f"Signal creation error: {e}")
                continue
    
    return CrawlResult(
        success=True,
        url=request.url,
        platform=platform,
        product_info=product_info,
        reviews=reviews,
        total_reviews=len(reviews),
        crawled_at=crawl_record["crawled_at"],
        signals_created=signals_created
    )

@router.get("/history")
async def get_crawl_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """크롤링 이력 조회"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    results = await db.crawl_results.find(
        {"user_id": user_id},
        {"_id": 0, "reviews": 0}  # 리뷰 상세는 제외
    ).sort("crawled_at", -1).limit(limit).to_list(limit)
    
    return {
        "history": results,
        "total": len(results)
    }

@router.get("/result/{crawl_id}")
async def get_crawl_result(
    crawl_id: str,
    current_user: dict = Depends(get_current_user)
):
    """크롤링 결과 상세 조회"""
    from server import db
    
    result = await db.crawl_results.find_one(
        {"crawl_id": crawl_id},
        {"_id": 0}
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="크롤링 결과를 찾을 수 없습니다")
    
    return result

@router.get("/platforms")
async def get_supported_platforms():
    """지원 플랫폼 목록"""
    return {
        "platforms": [
            {"id": "naver", "name": "네이버 스마트스토어", "status": "supported", "url_pattern": "smartstore.naver.com, brand.naver.com"},
            {"id": "coupang", "name": "쿠팡", "status": "supported", "url_pattern": "coupang.com"},
            {"id": "11st", "name": "11번가", "status": "partial", "url_pattern": "11st.co.kr"},
            {"id": "gmarket", "name": "G마켓", "status": "partial", "url_pattern": "gmarket.co.kr"},
            {"id": "auction", "name": "옥션", "status": "partial", "url_pattern": "auction.co.kr"},
            {"id": "generic", "name": "기타", "status": "basic", "url_pattern": "기타 쇼핑몰"}
        ],
        "note": "일부 플랫폼은 JavaScript 렌더링이 필요하여 완전한 크롤링이 어려울 수 있습니다"
    }

# ==================== 테스트용 샘플 데이터 생성 ====================

@router.post("/test/sample")
async def create_sample_crawl_data(
    current_user: dict = Depends(get_current_user)
):
    """테스트용 샘플 크롤링 데이터 생성"""
    from server import db
    
    user_id = current_user.get("user_id")
    
    sample_reviews = [
        ReviewData(
            review_id=f"sample_{uuid.uuid4().hex[:8]}",
            author="구매자A",
            rating=5,
            content="정말 좋은 제품이에요! 배송도 빠르고 품질도 최고입니다. 다음에도 재구매할 예정이에요.",
            date="2024-01-15"
        ),
        ReviewData(
            review_id=f"sample_{uuid.uuid4().hex[:8]}",
            author="구매자B",
            rating=4,
            content="가격 대비 괜찮은 품질입니다. 다만 포장이 조금 아쉬웠어요. 전체적으로 만족합니다.",
            date="2024-01-14"
        ),
        ReviewData(
            review_id=f"sample_{uuid.uuid4().hex[:8]}",
            author="구매자C",
            rating=5,
            content="선물용으로 구매했는데 받으신 분이 너무 좋아하세요! 품질이 기대 이상이에요.",
            date="2024-01-13"
        ),
        ReviewData(
            review_id=f"sample_{uuid.uuid4().hex[:8]}",
            author="구매자D",
            rating=3,
            content="보통이에요. 가격이 조금 비싼 감이 있지만 품질은 나쁘지 않습니다.",
            date="2024-01-12"
        ),
        ReviewData(
            review_id=f"sample_{uuid.uuid4().hex[:8]}",
            author="구매자E",
            rating=5,
            content="완전 강추합니다!! 이 가격에 이 품질은 정말 대박이에요. 주변에도 추천했어요.",
            date="2024-01-11"
        )
    ]
    
    product_info = ProductInfo(
        product_name="[테스트] 프리미엄 무선 이어폰 Pro Max",
        price="89,000원",
        category="가전/디지털",
        seller="테스트스토어",
        rating_avg=4.4,
        review_count=5,
        url="https://example.com/product/test"
    )
    
    crawl_record = {
        "crawl_id": f"CRL_{uuid.uuid4().hex[:12]}",
        "url": "https://example.com/product/test",
        "platform": "test",
        "user_id": user_id,
        "product_info": product_info.dict(),
        "review_count": len(sample_reviews),
        "reviews": [r.dict() for r in sample_reviews],
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "is_sample": True
    }
    
    await db.crawl_results.insert_one(crawl_record)
    
    # 시그널로 변환
    from server import get_pipeline_engine
    pipeline = get_pipeline_engine()
    
    signals_created = 0
    for review in sample_reviews:
        try:
            signal_content = f"[구매후기] {product_info.product_name}\n평점: {review.rating}점\n내용: {review.content}"
            
            await pipeline.create_signal(
                signal_type="text",
                content=signal_content,
                source="crawl:test",
                metadata={
                    "input_method": "url_crawl",
                    "crawl_id": crawl_record["crawl_id"],
                    "platform": "test",
                    "review_id": review.review_id,
                    "product_name": product_info.product_name,
                    "rating": review.rating,
                    "analysis_type": "general"
                },
                user_id=user_id
            )
            signals_created += 1
        except Exception as e:
            logger.error(f"Sample signal error: {e}")
    
    return {
        "success": True,
        "crawl_id": crawl_record["crawl_id"],
        "product": product_info.product_name,
        "reviews_count": len(sample_reviews),
        "signals_created": signals_created,
        "message": "테스트 샘플 데이터가 생성되었습니다"
    }
