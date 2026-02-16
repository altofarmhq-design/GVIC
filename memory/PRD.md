# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16
**Version**: 3.3.0

## 1. 제품 개요

### 1.1 비전
**"데이터 사일로를 깨는 AI 인사이트 프로토콜"**

### 1.2 비즈니스 모델
```
쇼핑몰 운영자 ──> GVIC 가입 ──> 구독 플랜 선택 ──> Stripe 결제
                                      │
                                      ▼
                    API 키 발급 ──> 쇼핑몰/제품 등록
                                      │
                                      ▼
                    분석 주기 설정 ──> 주기별 자동 분석 + 과금
```

---

## CHANGELOG

### 2026-02-16 (Phase 3: 결제 시스템 완료)

#### Stripe 결제 연동 ✅
- **[NEW]** Payment Service 모듈 (`/backend/saas/payment_service.py`)
  - 5개 구독 플랜: Free / Starter / Growth / Pro / Enterprise
  - Stripe Checkout 세션 생성
  - 결제 상태 조회 (pending/paid/expired)
  - 구독 상태 관리 (활성화/취소)
  - 결제 내역 조회
  - 사용량 기록 및 한도 체크

- **[NEW]** Stripe Webhook Handler (`/backend/saas/stripe_webhook.py`)
  - checkout.session.completed 이벤트 처리
  - checkout.session.expired 이벤트 처리
  - 자동 구독 활성화

#### 테스트 결과
- 테스트 에이전트 검증: **35/35 통과 (100%)**

---

## 2. 구독 플랜

| 플랜 | 월 요금 | 분석 횟수 | 제품 수 | 쇼핑몰 수 | 기능 |
|------|---------|----------|---------|----------|------|
| **Free** | ₩0 | 10회 | 3개 | 1개 | 기본 리뷰 분석, 4대 인사이트 |
| **Starter** | ₩29,000 | 50회 | 5개 | 1개 | + Q&A 관리, 월간 리포트 |
| **Growth** | ₩99,000 | 200회 | 20개 | 3개 | + 품목군 자산, API 키, 주간 리포트 |
| **Pro** | ₩249,000 | 1,000회 | 50개 | 10개 | + 웹훅, 일간 리포트, 우선 지원 |
| **Enterprise** | 협의 | 무제한 | 무제한 | 무제한 | 전담 매니저, SLA 보장 |

---

## 3. API 엔드포인트

### 3.1 결제 API (NEW)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/payments/plans` | 구독 플랜 목록 |
| GET | `/api/payments/plans/{plan_id}` | 플랜 상세 |
| POST | `/api/payments/checkout/session` | 결제 세션 생성 |
| GET | `/api/payments/checkout/status/{session_id}` | 결제 상태 조회 |
| GET | `/api/payments/subscription/status` | 현재 구독 상태 |
| POST | `/api/payments/subscription/cancel` | 구독 취소 |
| GET | `/api/payments/transactions` | 결제 내역 |
| POST | `/api/payments/usage/record` | 사용량 기록 |
| GET | `/api/payments/usage/check` | 사용량 한도 확인 |
| POST | `/api/webhook/stripe` | Stripe 웹훅 |

### 3.2 기존 API (요약)

- **쇼핑몰/제품**: `/api/shop/*`
- **4대 인사이트**: `/api/insights/*`
- **개선점 자산**: `/api/assets/*`
- **리뷰 분석**: `/api/saas/reviews/*`
- **Q&A 관리**: `/api/saas/qa/*`
- **대시보드**: `/api/saas/dashboard/*`

---

## 4. 코드 구조

```
/app/backend/
├── saas/
│   ├── review_analyzer.py      # 리뷰 감성 분석
│   ├── qa_manager.py           # Q&A/CS 통합
│   ├── dashboard_service.py    # 대시보드 서비스
│   ├── shop_manager.py         # 쇼핑몰/제품 관리
│   ├── product_insights.py     # 4대 인사이트 분석
│   ├── improvement_assets.py   # 개선점 자산화
│   ├── payment_service.py      # [NEW] 결제 서비스
│   └── stripe_webhook.py       # [NEW] Stripe 웹훅
├── review_crawler.py           # 크롤러
└── server.py                   # 메인 서버
```

---

## 5. 마일스톤 진행률

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 0 | ✅ 100% | 기반 구축 |
| Phase 1 | ✅ 100% | API 연동 + 온보딩 |
| Phase 2 | ✅ 100% | 4대 인사이트 엔진 |
| Phase 2.5 | ✅ 100% | 개선점 자산화 |
| Phase 3 | ✅ 100% | **결제 + 과금 (NEW)** |
| Phase 4 | ⬜ 0% | 프론트엔드 대시보드 |

**전체 진행률: 85%**

---

## 6. 다음 단계 (Phase 4)

### Phase 4: 프론트엔드 대시보드
- 쇼핑몰/제품 관리 UI
- 4대 인사이트 시각화
- 품목군별 자산 대시보드
- 구독 플랜 선택 및 결제 UI
- API 연동 가이드 UI

---

## 7. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!
- Stripe: 테스트 모드 (sk_test_emergent)

---

*Last Updated: 2026-02-16*
*Version: 3.3.0*
