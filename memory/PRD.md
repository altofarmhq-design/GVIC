# GVIC Seller Intelligence Hub - PRD

**Last Updated**: 2026-02-16
**Version**: 3.2.0

## 1. 제품 개요

### 1.1 비전
**"데이터 사일로를 깨는 AI 인사이트 프로토콜"**

### 1.2 핵심 가치
1. 쇼핑몰 운영자가 API를 직접 연동하여 제품별 리뷰 분석
2. 4대 인사이트(강점/건의/불만/신제품욕구) 도출
3. **개선점(건의/불만/신제품욕구)만 HS Code 기반 품목군별 자산화**
4. 역직구 지원 (HS Code 10자리 세번)

---

## CHANGELOG

### 2026-02-16 (개선점 자산화 시스템 추가)

#### 개선점 자산화 모듈 ✅
- **[NEW]** Improvement Assets 모듈 (`/backend/saas/improvement_assets.py`)
  - HS Code 기반 품목군 분류 (12개 품목군)
  - 개선점만 자산화 (강점/Null 제외)
  - 제품명으로 HS Code 자동 추천
  - 품목군별 개선점 축적 (중복 시 빈도 증가)
  - 품목군 진입 시 체크리스트 제공
  - 4대 인사이트 분석 시 자동 자산화 (`auto_accumulate=true`)

#### 자산화 가치 판단

| 인사이트 유형 | 자산화 | 이유 |
|--------------|--------|------|
| 💪 강점 | ❌ | 이미 해결된 것, 각 제품 고유 |
| ⚪ Null | ❌ | 정보 가치 없음 |
| 💡 건의사항 | ✅ | 미해결 개선점 → 품목군 공통 적용 |
| ⚠️ 불만 | ✅ | 반복되는 문제 → 필수 체크리스트 |
| 🚀 신제품 욕구 | ✅ | 시장 수요 → 신제품 개발 가이드 |

#### 테스트 결과
- 테스트 에이전트 검증: **29/29 통과 (100%)**

---

## 2. HS Code 기반 품목 분류 체계

### 2.1 구조
```
HS Code (6자리) + 확장코드 (4자리) + 기능모듈 (가변)
────────────────   ─────────────────   ────────────────
8518.30           .0001                [음질][배터리][NC]
(이어폰/헤드폰)    (무선이어폰)         (기능 모듈)
```

### 2.2 지원 품목군 (12개)

| HS Code | 품목명 | 기능 모듈 |
|---------|--------|----------|
| 8518.30 | 헤드폰/이어폰 | 음질, 배터리, 착용감, 연결성, 통화품질, 노이즈캔슬링, 방수 |
| 8517.12 | 스마트폰 | 디스플레이, 카메라, 배터리, 성능, 저장공간, 내구성 |
| 8471.30 | 노트북/태블릿 | 디스플레이, 성능, 배터리, 키보드, 무게, 발열 |
| 6110.20 | 면 스웨터 | 소재감, 사이즈, 색상, 세탁성, 보온성 |
| 6203.42 | 면 바지 | 핏, 소재감, 사이즈, 내구성, 색상 |
| 6402.19 | 운동화 | 착용감, 쿠션, 사이즈, 내구성, 디자인, 통기성 |
| 3304.99 | 기타 화장품 | 보습력, 발림성, 향, 지속력, 자극성, 용량 |
| 3305.10 | 샴푸 | 세정력, 향, 두피자극, 거품, 헹굼, 용량 |
| 2106.90 | 건강기능식품 | 효능, 복용편의, 맛, 부작용, 가격, 포장 |
| 9403.20 | 금속 가구 | 조립, 내구성, 디자인, 크기, 마감 |
| 9404.21 | 매트리스 | 경도, 소재, 사이즈, 냄새, 내구성, 배송 |

---

## 3. API 엔드포인트

### 3.1 개선점 자산 API (NEW)

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | `/api/assets/hs-codes` | HS Code 목록 |
| GET | `/api/assets/hs-codes/{hs_code}` | HS Code 상세 |
| POST | `/api/assets/suggest-hs-code` | HS Code 추천 |
| POST | `/api/assets/products/{product_id}/set-hs-code` | 제품에 HS Code 설정 |
| POST | `/api/assets/accumulate` | 개선점 수동 축적 |
| POST | `/api/assets/accumulate-from-analysis/{analysis_id}` | 분석 결과에서 자동 축적 |
| GET | `/api/assets/category/{hs_code}` | 품목군별 자산 조회 |
| GET | `/api/assets/category/{hs_code}/checklist` | 품목군 진입 체크리스트 |
| GET | `/api/assets/stats/overview` | 전체 자산 통계 |

### 3.2 4대 인사이트 분석 (수정)
```
POST /api/insights/analyze?auto_accumulate=true

auto_accumulate=true: 개선점을 품목군 자산으로 자동 축적
auto_accumulate=false: 자산화 없이 분석만 수행
```

---

## 4. 코드 구조

```
/app/backend/
├── saas/
│   ├── __init__.py
│   ├── review_analyzer.py      # 리뷰 감성 분석
│   ├── qa_manager.py           # Q&A/CS 통합
│   ├── dashboard_service.py    # 대시보드 서비스
│   ├── shop_manager.py         # 쇼핑몰/제품 관리
│   ├── product_insights.py     # 4대 인사이트 분석
│   └── improvement_assets.py   # [NEW] 개선점 자산화
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
| Phase 2.5 | ✅ 100% | **개선점 자산화 (NEW)** |
| Phase 3 | ⬜ 0% | 결제 + 과금 |
| Phase 4 | ⬜ 0% | 프론트엔드 대시보드 |

**전체 진행률: 70%**

---

## 6. 다음 단계

### Phase 3: 결제 + 주기별 과금
- Stripe 결제 연동
- 구독 플랜 (Starter/Growth/Pro/Enterprise)
- 분석 주기별 자동 과금

### Phase 4: 프론트엔드 대시보드
- 쇼핑몰/제품 관리 UI
- 4대 인사이트 시각화
- 품목군별 자산 대시보드

---

## 7. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!

---

*Last Updated: 2026-02-16*
*Version: 3.2.0*
