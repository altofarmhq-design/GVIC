# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16
**Version**: 4.0.0

## 1. 제품 개요

### 1.1 비전
**"고객 리뷰 기반 셀러 인사이트 플랫폼"**

이커머스 셀러를 위한 SaaS 서비스로, 고객 리뷰를 분석하여 4대 인사이트(강점, 건의사항, 불만, 신제품 욕구)를 추출합니다.

### 1.2 핵심 기능
- **4대 인사이트 분석**: 강점(유지/보강), 건의사항(서비스 개선), 불만(긴급 개선), 신제품 욕구(개발 기회)
- **개선점 자산화**: HS Code 기반 품목군별 개선점 DB 구축
- **다중 결제 지원**: Stripe + 한국 결제(카카오페이, 네이버페이, 토스 등)

---

## 2. 구독 플랜

| 플랜 | 월 요금 | 분석 횟수 | 제품 수 | 쇼핑몰 수 |
|------|---------|----------|---------|----------|
| **Free** | ₩0 | 10회 | 3개 | 1개 |
| **Starter** | ₩29,000 | 50회 | 5개 | 1개 |
| **Growth** | ₩99,000 | 200회 | 20개 | 3개 |
| **Pro** | ₩249,000 | 1,000회 | 50개 | 10개 |
| **Enterprise** | 협의 | 무제한 | 무제한 | 무제한 |

---

## 3. 결제 수단

| 결제 수단 | 아이콘 | 상태 | 필요 API 키 |
|----------|--------|------|------------|
| **Stripe** | 💳 | 실제 연동 | STRIPE_API_KEY |
| **카카오페이** | 🟡 | 시뮬레이션* | KAKAOPAY_ADMIN_KEY |
| **네이버페이** | 🟢 | 시뮬레이션* | NAVERPAY_CLIENT_ID |
| **토스페이먼츠** | 🔵 | 시뮬레이션* | TOSS_CLIENT_KEY |
| **삼성페이** | ⚫ | 시뮬레이션* | SAMSUNGPAY_SERVICE_ID |
| **Payco** | 🔴 | 시뮬레이션* | PAYCO_SELLER_KEY |

*시뮬레이션: API 키 설정 시 실제 연동으로 전환됨

---

## 4. 마일스톤 진행률

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 0 | ✅ 100% | 기반 구축 |
| Phase 1 | ✅ 100% | API 연동 + 온보딩 |
| Phase 2 | ✅ 100% | 4대 인사이트 엔진 |
| Phase 2.5 | ✅ 100% | 개선점 자산화 |
| Phase 3 | ✅ 100% | 결제 + 과금 |
| **Phase 4** | ✅ 100% | **프론트엔드 대시보드** |

**전체 진행률: 100%**

---

## 5. 코드 구조

```
/app/
├── backend/
│   ├── saas/
│   │   ├── review_analyzer.py
│   │   ├── qa_manager.py
│   │   ├── dashboard_service.py
│   │   ├── shop_manager.py       # 쇼핑몰/제품/API키 관리
│   │   ├── product_insights.py   # 4대 인사이트 분석
│   │   ├── improvement_assets.py # 개선점 자산화 + HS Code
│   │   ├── payment_service.py    # Stripe 결제
│   │   ├── stripe_webhook.py
│   │   └── unified_payment.py    # 통합 결제 (6개 수단)
│   └── server.py
└── frontend/
    └── src/
        ├── components/
        │   └── saas/             # SaaS 대시보드 컴포넌트
        │       ├── SaasDashboard.jsx
        │       ├── MyProductsTab.jsx
        │       ├── BillingTab.jsx
        │       └── ApiGuideTab.jsx
        ├── lib/api.js           # API 클라이언트
        └── App.js               # SaaS 라우터
```

---

## 6. API 엔드포인트

### 6.1 쇼핑몰/제품 관리
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/shop/shops` | 쇼핑몰 등록 |
| GET | `/api/shop/shops` | 쇼핑몰 목록 |
| POST | `/api/shop/shops/{id}/products` | 제품 등록 |
| GET | `/api/shop/products` | 전체 제품 목록 |

### 6.2 4대 인사이트
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | `/api/insights/analyze/{product_id}` | 제품 분석 |
| GET | `/api/insights/product/{product_id}` | 분석 결과 조회 |

### 6.3 결제
| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/payments/methods` | 결제 수단 목록 |
| POST | `/api/payments/unified/checkout` | 통합 결제 |
| GET | `/api/payments/subscription/status` | 구독 상태 |

---

## 7. 테스트 계정
- **Email**: admin@gvic.com
- **Password**: gvicgvic!

---

## 8. CHANGELOG

### 2026-02-16 (Phase 4 완료)

#### 프론트엔드 대시보드 ✅
- **[NEW]** SaaS 대시보드 리브랜딩 완료
  - 기존 특허 기반 탭 제거
  - 새 탭 구조: 대시보드, 내 상품, 결제, API 가이드, 설정
- **[NEW]** `SaasDashboard.jsx`: 메인 대시보드 (4대 인사이트 현황, 빠른 시작)
- **[NEW]** `MyProductsTab.jsx`: 쇼핑몰/제품 등록 관리
- **[NEW]** `BillingTab.jsx`: 구독 플랜 선택 및 결제 수단
- **[NEW]** `ApiGuideTab.jsx`: API 키 발급, 문서, 코드 샘플, 웹훅 설정
- **[FIX]** BillingTab price undefined 에러 수정

#### 테스트 결과
- 테스트 에이전트 검증: **Frontend 90%** (5/5 탭 정상, 1개 버그 수정)

---

## 9. 다음 단계 (P1/P2)

### P1 - 인사이트 시각화
- 4대 인사이트 상세 대시보드 (차트, 그래프)
- 제품별 트렌드 분석

### P2 - 고급 기능
- 크롤러 강화 (Playwright로 JS 기반 사이트 크롤링)
- 관리자 대시보드
- 경쟁 상품 비교 분석

---

*Last Updated: 2026-02-16*
*Version: 4.0.0*
