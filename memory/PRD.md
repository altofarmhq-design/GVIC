# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16

## 1. 제품 개요

### 1.1 새로운 비전 (피벗)
GVIC는 14개 특허 기반의 AI 플랫폼에서 **이커머스 셀러를 위한 "Seller Intelligence Hub" SaaS**로 전환되었습니다.
핵심 가치: **"데이터 사일로를 깨는 AI 인사이트 프로토콜"**

### 1.2 핵심 문제 해결
- 여러 플랫폼(네이버, 쿠팡 등)에 흩어진 리뷰/Q&A/CS 데이터 통합
- 실시간 인사이트 도출 및 액션 아이템 제공
- 5:3:2 프레임워크로 인사이트 분류 (고객 50%, 운영 30%, 전략 20%)

## CHANGELOG

### 2026-02-16 (최신 - SaaS MVP 핵심 모듈 구현)
- **[NEW]** `/app/backend/saas/` 디렉토리 생성 - SaaS 전용 모듈
- **[NEW]** ReviewAnalyzer 구현 (`review_analyzer.py`)
  - 리뷰 감성 분석 (긍정/부정/중립)
  - 핵심 키워드 추출
  - 상품 특성/이슈/강점 식별
  - 5:3:2 인사이트 분류 (customer_insights, operation_insights, strategy_insights)
  - AI 심층 분석 (LLM 연동)
- **[NEW]** QAManager 구현 (`qa_manager.py`)
  - Q&A 자동 카테고리 분류 (배송, 교환/반품, 상품, 사이즈, 재고, 결제)
  - 자동 답변 제안
  - FAQ 자동 생성
  - 응답 템플릿 관리
- **[NEW]** DashboardService 구현 (`dashboard_service.py`)
  - 리뷰/Q&A 통합 요약
  - 5:3:2 인사이트 집계
  - 액션 아이템 자동 생성
  - 트렌드 분석
- **[ENHANCED]** 리뷰 크롤러 강화 (`review_crawler.py`)
  - NaverReviewCrawler: 페이지네이션 지원, 대량 수집
  - CoupangReviewCrawler: 개선된 파싱
  - `/api/crawl/crawl-and-analyze`: 크롤링 + 분석 통합 API
  - `/api/crawl/analyze-existing/{crawl_id}`: 기존 크롤링 재분석
- **[FIX]** MongoDB ObjectId 직렬화 이슈 수정 (qa_manager.py)
- **[VERIFIED]** 테스트 에이전트 검증 완료 (20/20 테스트 통과, 100%)

### 이전 변경사항
- 14개 특허 백엔드 모듈 구조 완성 (`/app/backend/patents/`)
- F:FIELD 물리 계층 시각화 대시보드 구현
- Insight Derivation 버그 수정
- URL 처리 실패 버그 수정

## 2. 현재 구현 상태

### 2.1 SaaS 핵심 모듈 (NEW)

| 모듈 | 파일 | 상태 | API 엔드포인트 |
|------|------|------|---------------|
| ReviewAnalyzer | `/saas/review_analyzer.py` | ✅ 완료 | `/api/saas/reviews/*` |
| QAManager | `/saas/qa_manager.py` | ✅ 완료 | `/api/saas/qa/*` |
| DashboardService | `/saas/dashboard_service.py` | ✅ 완료 | `/api/saas/dashboard/*` |

### 2.2 주요 API 엔드포인트

#### 리뷰 분석 API
- `POST /api/saas/reviews/analyze` - 리뷰 배치 분석
- `POST /api/saas/reviews/analyze-single` - 단일 리뷰 분석
- `GET /api/saas/reviews/dashboard/summary` - 리뷰 대시보드 요약
- `GET /api/saas/reviews/history` - 분석 이력 조회

#### Q&A 관리 API
- `POST /api/saas/qa/items` - Q&A 배치 등록
- `GET /api/saas/qa/items` - Q&A 목록 조회
- `PUT /api/saas/qa/items/{qa_id}/answer` - 답변 등록
- `POST /api/saas/qa/generate-faq` - FAQ 자동 생성
- `GET /api/saas/qa/stats` - Q&A 통계

#### 대시보드 API
- `GET /api/saas/dashboard/overview` - 대시보드 개요
- `GET /api/saas/dashboard/insights-532` - 5:3:2 인사이트
- `GET /api/saas/dashboard/action-items` - 액션 아이템
- `GET /api/saas/dashboard/trends` - 트렌드 데이터
- `GET /api/saas/dashboard/full` - 전체 대시보드

#### 크롤링 + 분석 통합 API
- `POST /api/crawl/crawl-and-analyze` - URL 크롤링 후 자동 분석
- `POST /api/crawl/analyze-existing/{crawl_id}` - 기존 크롤링 재분석

### 2.3 5:3:2 인사이트 프레임워크

| 분류 | 비율 | 설명 | 예시 |
|------|------|------|------|
| 고객 인사이트 | 50% | 고객 만족/불만, 니즈, 선호도 | 만족도 높음, 재구매 의향 |
| 운영 인사이트 | 30% | 배송, CS, 재고, 포장 | 배송 지연, 포장 문제 |
| 전략 인사이트 | 20% | 가격, 경쟁사, 시장 트렌드 | 가격 경쟁력, 마케팅 포인트 |

## 3. 기술 스택

### Frontend
- React 18+
- Tailwind CSS + Shadcn/UI
- React Router v6

### Backend
- FastAPI (Python)
- MongoDB
- JWT Authentication
- Emergent Integration (Gemini 3 Flash)

### 배포
- Preview URL: https://reviewhub-46.preview.emergentagent.com

## 4. 코드 구조

```
/app/backend/
├── saas/                      # NEW: SaaS 핵심 모듈
│   ├── __init__.py
│   ├── review_analyzer.py     # 리뷰 분석 엔진
│   ├── qa_manager.py          # Q&A/CS 통합 관리
│   └── dashboard_service.py   # 대시보드 서비스
├── patents/                   # 기존 14개 특허 모듈 (선택적 로딩)
├── review_crawler.py          # 강화된 크롤러 (페이지네이션)
├── gvic_analyzer.py           # GVIC 분석 엔진
└── server.py                  # 메인 서버 (SaaS 라우터 등록)
```

## 5. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!
- Role: super_admin

## 6. 향후 로드맵

### P0 - 완료
- [x] SaaS 핵심 백엔드 모듈 구현 (review_analyzer, qa_manager, dashboard_service)
- [x] 크롤러 강화 (페이지네이션, 대량 수집)
- [x] 크롤링 + 분석 통합 API

### P1 - 다음 단계
- [ ] SaaS 전용 프론트엔드 UI 구현
  - 리뷰 대시보드 페이지
  - Q&A 센터 페이지
  - 셀러 대시보드 페이지
- [ ] Stripe 결제 연동 (SaaS 구독)
- [ ] 쿠팡 크롤러 Playwright 기반 강화

### P2 - 향후 개선
- [ ] 수출입 문서 OCR 처리 모듈
- [ ] 다국어 CS 지원
- [ ] 실시간 알림 시스템

### P3 - 백로그
- [ ] 경쟁사 분석 기능
- [ ] 가격 추적 기능
- [ ] API 외부 연동 (웹훅)

## 7. 알려진 이슈
- React `removeChild` 런타임 에러 (P2, 레거시) - 미해결

---
*Last Updated: 2026-02-16*
*Version: 3.0.0 (SaaS Pivot)*
