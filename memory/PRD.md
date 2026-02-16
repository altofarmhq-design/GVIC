# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16
**Version**: 3.1.0

## 1. 제품 개요

### 1.1 비전
**"데이터 사일로를 깨는 AI 인사이트 프로토콜"**

쇼핑몰 운영자가 GVIC API를 직접 설치하여 제품별 리뷰를 분석하고, 4대 인사이트(강점/건의/불만/신제품욕구)를 도출하는 B2B SaaS 플랫폼

### 1.2 비즈니스 모델
```
쇼핑몰 운영자 ──> GVIC 가입 ──> 결제 ──> API 키 발급 ──> 쇼핑몰 연동
                                           │
                                           ▼
                         분석 주기 설정 (일간/주간/월간)
                                           │
                                           ▼
                              주기별 자동 분석 + 과금
```

### 1.3 과금 모델 (안)
| 플랜 | 분석 주기 | 제품 수 | 월 요금 |
|------|----------|---------|---------|
| **Starter** | 월 1회 | 5개 | ₩29,000 |
| **Growth** | 주 1회 | 20개 | ₩99,000 |
| **Pro** | 일 1회 | 50개 | ₩249,000 |
| **Enterprise** | 실시간 | 무제한 | 협의 |

---

## CHANGELOG

### 2026-02-16 (Phase 1 & 2 완료)

#### Phase 1: API 연동 + 온보딩 시스템 ✅
- **[NEW]** Shop Manager 모듈 (`/backend/saas/shop_manager.py`)
  - 쇼핑몰 CRUD (등록/조회/수정/삭제)
  - 제품 CRUD (등록/조회/수정/삭제)
  - 분석 주기 설정 (daily/weekly/monthly)
  - 웹훅 설정 (URL, 이벤트, 시크릿)
  - API 키 발급/조회/삭제
  - 온보딩 상태 조회 (5단계 진행률)
  - 쇼핑몰 통계 개요

#### Phase 2: 4대 인사이트 분석 엔진 ✅
- **[NEW]** Product Insights 모듈 (`/backend/saas/product_insights.py`)
  - **강점 분석** (유지/보강): 품질, 가격, 배송, 디자인, 기능, 서비스, 재구매
  - **건의사항 분석** (서비스 개선): 색상, 사이즈, 기능, 포장, 가격, 배송, 설명서
  - **불만 분석** (개선/드롭): 품질불량, 배송지연, 오배송, 색상차이, 사이즈오류, CS불만, 환불문제
  - **신제품 욕구** (신규 개발): 신기능, 변형제품, 업그레이드, 조합제품, 특수용도
  - 종합 점수 및 트렌드 분석
  - 제품별 분석 이력 관리

#### 테스트 결과
- 테스트 에이전트 검증: **33/33 통과 (100%)**
- 모든 API JWT 인증 정상 작동
- MongoDB ObjectId 직렬화 이슈 없음

---

## 2. 4대 인사이트 프레임워크

| 분류 | 아이콘 | 액션 | 설명 |
|------|--------|------|------|
| **강점** | 💪 | 유지/보강 | 좋은 점 → 마케팅 강조, 품질 유지 |
| **건의사항** | 💡 | 서비스 개선 | 개선 요청 → 제품/서비스 보강 |
| **불만** | ⚠️ | 개선/드롭 결정 | 문제점 → 제품별 모듈화, 개선 또는 단종 제안 |
| **신제품 욕구** | 🚀 | 신규 개발 | 잠재 니즈 → 신제품 개발 기회 발굴 |

---

## 3. API 엔드포인트

### 3.1 Shop Manager API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/shop/shops` | 쇼핑몰 등록 |
| GET | `/api/shop/shops` | 쇼핑몰 목록 |
| GET | `/api/shop/shops/{shop_id}` | 쇼핑몰 상세 |
| PUT | `/api/shop/shops/{shop_id}` | 쇼핑몰 수정 |
| DELETE | `/api/shop/shops/{shop_id}` | 쇼핑몰 삭제 |
| POST | `/api/shop/shops/{shop_id}/products` | 제품 등록 |
| GET | `/api/shop/shops/{shop_id}/products` | 제품 목록 |
| GET | `/api/shop/products/{product_id}` | 제품 상세 |
| PUT | `/api/shop/products/{product_id}` | 제품 수정 |
| DELETE | `/api/shop/products/{product_id}` | 제품 삭제 |
| PUT | `/api/shop/shops/{shop_id}/schedule` | 분석 주기 설정 |
| PUT | `/api/shop/shops/{shop_id}/webhook` | 웹훅 설정 |
| POST | `/api/shop/api-keys` | API 키 발급 |
| GET | `/api/shop/api-keys` | API 키 목록 |
| DELETE | `/api/shop/api-keys/{key_id}` | API 키 삭제 |
| GET | `/api/shop/onboarding/status` | 온보딩 상태 |
| GET | `/api/shop/stats/overview` | 쇼핑몰 통계 |

### 3.2 Product Insights API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/insights/analyze` | 4대 인사이트 분석 |
| GET | `/api/insights/product/{product_id}` | 제품 분석 이력 |
| GET | `/api/insights/analysis/{analysis_id}` | 분석 상세 |
| POST | `/api/insights/product/{product_id}/analyze-now` | 즉시 분석 (크롤링+분석) |

---

## 4. 코드 구조

```
/app/backend/
├── saas/
│   ├── __init__.py
│   ├── review_analyzer.py      # 리뷰 감성 분석
│   ├── qa_manager.py           # Q&A/CS 통합
│   ├── dashboard_service.py    # 대시보드 서비스
│   ├── shop_manager.py         # [NEW] 쇼핑몰/제품 관리, API 키
│   └── product_insights.py     # [NEW] 4대 인사이트 분석 엔진
├── review_crawler.py           # 크롤러 (네이버/쿠팡)
└── server.py                   # 메인 서버
```

---

## 5. 마일스톤 진행률

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 0 | ✅ 100% | 기반 구축 (완료) |
| Phase 1 | ✅ 100% | API 연동 + 온보딩 (완료) |
| Phase 2 | ✅ 100% | 4대 인사이트 엔진 (완료) |
| Phase 3 | ⬜ 0% | 결제 + 주기별 과금 (예정) |
| Phase 4 | ⬜ 0% | 프론트엔드 대시보드 (예정) |

**전체 진행률: 65%**

---

## 6. 다음 단계 (Phase 3)

### Phase 3: 결제 + 주기별 과금
- Stripe 결제 연동
- 구독 플랜 설계 및 구현
- 과금 계산 로직
- 결제 대시보드
- 플랜 변경/해지

### Phase 4: 프론트엔드 대시보드
- 쇼핑몰/제품 관리 UI
- 4대 인사이트 대시보드
- 제품별 상세 분석
- API 연동 가이드 UI

---

## 7. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!

---

*Last Updated: 2026-02-16*
*Version: 3.1.0*
