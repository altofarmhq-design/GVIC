# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16
**Version**: 3.4.0

## 1. 제품 개요

### 1.1 비전
**"데이터 사일로를 깨는 AI 인사이트 프로토콜"**

### 1.2 결제 시스템
GVIC는 6가지 결제 수단을 지원하여 사용자가 선택적으로 사용할 수 있습니다.

---

## CHANGELOG

### 2026-02-16 (통합 결제 시스템 완료)

#### 통합 결제 시스템 ✅
- **[NEW]** Unified Payment 모듈 (`/backend/saas/unified_payment.py`)
  - Strategy Pattern 기반 결제 어댑터 설계
  - 6개 결제 수단 지원
  - 결제 수단별 시뮬레이션 모드 (API 키 미설정 시)

#### 지원 결제 수단

| 결제 수단 | 아이콘 | 상태 | 필요 API 키 |
|----------|--------|------|------------|
| **Stripe** | 💳 | 실제 연동 | STRIPE_API_KEY |
| **카카오페이** | 🟡 | 시뮬레이션* | KAKAOPAY_ADMIN_KEY, KAKAOPAY_CID |
| **네이버페이** | 🟢 | 시뮬레이션* | NAVERPAY_CLIENT_ID, NAVERPAY_CLIENT_SECRET |
| **토스페이먼츠** | 🔵 | 시뮬레이션* | TOSS_CLIENT_KEY, TOSS_SECRET_KEY |
| **삼성페이** | ⚫ | 시뮬레이션* | SAMSUNGPAY_SERVICE_ID |
| **Payco** | 🔴 | 시뮬레이션* | PAYCO_SELLER_KEY, PAYCO_CP_ID |

*시뮬레이션: API 키 설정 시 실제 연동으로 전환됨

#### 테스트 결과
- 테스트 에이전트 검증: **26/26 통과 (100%)**

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

## 3. API 엔드포인트

### 3.1 통합 결제 API (NEW)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/payments/methods` | 결제 수단 목록 (6개) |
| POST | `/api/payments/unified/checkout` | 통합 결제 세션 생성 |
| POST | `/api/payments/unified/verify` | 결제 승인/검증 |
| GET | `/api/payments/unified/status/{order_id}` | 결제 상태 조회 |
| GET | `/api/payments/config/required-keys` | 필요 API 키 목록 |

### 3.2 기존 결제 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/payments/plans` | 구독 플랜 목록 |
| GET | `/api/payments/subscription/status` | 구독 상태 |
| POST | `/api/payments/subscription/cancel` | 구독 취소 |
| GET | `/api/payments/usage/check` | 사용량 확인 |

---

## 4. 코드 구조

```
/app/backend/
├── saas/
│   ├── review_analyzer.py      # 리뷰 분석
│   ├── qa_manager.py           # Q&A 관리
│   ├── dashboard_service.py    # 대시보드
│   ├── shop_manager.py         # 쇼핑몰/제품
│   ├── product_insights.py     # 4대 인사이트
│   ├── improvement_assets.py   # 개선점 자산화
│   ├── payment_service.py      # 기본 결제 (Stripe)
│   ├── stripe_webhook.py       # Stripe 웹훅
│   └── unified_payment.py      # [NEW] 통합 결제 (6개 수단)
└── server.py
```

---

## 5. 마일스톤 진행률

| Phase | 상태 | 설명 |
|-------|------|------|
| Phase 0 | ✅ 100% | 기반 구축 |
| Phase 1 | ✅ 100% | API 연동 + 온보딩 |
| Phase 2 | ✅ 100% | 4대 인사이트 엔진 |
| Phase 2.5 | ✅ 100% | 개선점 자산화 |
| Phase 3 | ✅ 100% | **결제 + 과금 (확장 완료)** |
| Phase 4 | ⬜ 0% | 프론트엔드 대시보드 |

**전체 진행률: 85%**

---

## 6. 실제 연동 시 필요한 설정

### 환경변수 (.env)

```bash
# Stripe (해외 카드)
STRIPE_API_KEY=sk_live_xxxxx

# 카카오페이
KAKAOPAY_ADMIN_KEY=xxxxx
KAKAOPAY_CID=xxxxx

# 네이버페이
NAVERPAY_CLIENT_ID=xxxxx
NAVERPAY_CLIENT_SECRET=xxxxx
NAVERPAY_CHAIN_ID=xxxxx

# 토스페이먼츠
TOSS_CLIENT_KEY=xxxxx
TOSS_SECRET_KEY=xxxxx

# 삼성페이
SAMSUNGPAY_SERVICE_ID=xxxxx

# Payco
PAYCO_SELLER_KEY=xxxxx
PAYCO_CP_ID=xxxxx
```

---

## 7. 다음 단계 (Phase 4)

### Phase 4: 프론트엔드 대시보드
- 쇼핑몰/제품 관리 UI
- 4대 인사이트 시각화
- 구독 플랜 선택 및 결제 UI (6개 결제 수단)
- 품목군별 자산 대시보드
- API 연동 가이드 UI

---

## 8. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!

---

*Last Updated: 2026-02-16*
*Version: 3.4.0*
