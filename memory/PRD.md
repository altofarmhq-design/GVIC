# GVIC Engine Dashboard - Product Requirements Document

---

## 🏛️ GVIC 사명 (Mission)

```
입출력설계는  친절하게 🤝
본질은       엄격하게 ⚖️
출력시그널은  신속하게 ⚡
```

---

## 💎 GVIC 강점 (Core Strength)

> **"엔진은 하나, 인터페이스는 맞춤"**

| 원칙 | 설명 |
|------|------|
| **엔진 품질 보장** | 검증된 단일 코어 |
| **유연한 적용** | 다양한 고객 요구 수용 |
| **유지보수 효율** | 엔진만 개선하면 전체 적용 |

---

## 🏗️ GVIC 아키텍처 철학

```
┌─────────────────────────────────────────────────────┐
│  [입력 설계]  ──→   GVIC ENGINE   ──→  [출력 설계]  │
│   (고객별        (유형화/분류/패턴)      (고객별     │
│    커스터마이징)     ❌ 변경 없음        커스터마이징)│
└─────────────────────────────────────────────────────┘
```

- **입력 시그널**: 고객별 협의/설계 (커스터마이징 가능)
- **GVIC 엔진**: 유형화, 분류, 패턴 발견 (고정, 변경 불가)
- **출력 시그널**: 고객별 협의/설계 (커스터마이징 가능)

---

## 프로젝트 개요
Streamlit GVIC Engine 대시보드를 React/FastAPI 기반 풀스택 애플리케이션으로 전환한 프로젝트

## 기술 스택
- **Frontend**: React.js, Shadcn/UI, Recharts, Tailwind CSS
- **Backend**: FastAPI, Python
- **Database**: MongoDB
- **Authentication**: JWT + Emergent Google OAuth
- **PDF Generation**: ReportLab (나눔고딕 폰트)
- **AI Analysis**: Gemini 3 Flash (via EMERGENT_LLM_KEY)

## 핵심 기능
1. 7개 특허 모듈 통합 처리 파이프라인
2. 사용자 인증 및 RBAC (7개 역할)
3. 외부 데이터 소스 연동
4. URL 기반 리뷰 분석
5. PDF 리포트 생성
6. **[NEW] AI 기반 시그널 분석 (GVIC 쇼케이스)**

---

## ✅ 구현 완료

### 2024년 12월
- [x] 14개 메인 탭 UI 구현
- [x] 특허 로직 백엔드 구현
- [x] MongoDB 데이터 저장
- [x] Google OAuth 인증
- [x] PDF 출력 옵션 UI
- [x] 나눔고딕 폰트 설치
- [x] 로컬 설치용 프로젝트 패키징
- [x] 탭 기능 상세 설명서 작성
- [x] DataHub 연동 확장: ComparisonTab에 URL 분석 세션 비교 기능 추가

### 2025년 2월 (이번 세션)
- [x] **AI 기반 시그널 분석 엔진 구현** (키워드 기반 → AI 기반 전환)
  - POST /api/signal-tracer/ai-analyze API
  - 시그널 유형 자동 감지 (product_review, requirement, complaint 등)
  - 숨겨진 의미 및 뉘앙스 추출 (예: "체념적 만족")
- [x] **ID 추적 체계 구현**
  - INP_ (입력 ID), MOD_ (모듈 ID), SIG_ (시그널 ID)
  - 요구자(사용자) → 입력 → 모듈 → 시그널 완전 추적
- [x] **GVIC 쇼케이스 탭 완성**
  - 시그널 입력 UI
  - 1단계: 시그널 유형 감지 표시
  - 2단계: 발견된 시그널 목록 (ID, sentiment, type, intensity, hidden_meaning)
  - 3단계: 모듈화 결과 (요약, 주요 테마, 전체 감성, 3관점 분석)
  - 자산 저장 기능
  - 자산 저장소 탭 (통계, 목록, 검색)
- [x] **로컬 환경 설정** (.bat 스크립트 제공)

---

## 🔴 진행 중 이슈 (P1)

### Issue 1: React removeChild 런타임 에러
- **상태**: 미해결 (재현 단계 필요)
- **설명**: UI 불안정성을 유발하는 반복적인 버그
- **다음 단계**: 사용자가 특정 재현 단계 제공 시 조사

### Issue 2: 로컬 환경 파일 동기화
- **상태**: 대기 중
- **설명**: 사용자의 로컬 환경이 최신 코드와 동기화 필요
- **다음 단계**: GVIC Showcase 파일 목록 제공

---

## 🟡 백로그 (P2-P3)

### P2: 자산 활용 시스템 완성
- 자산 저장 시 AI 생성 모듈 전체 저장 (MongoDB)
- Asset Repository 및 Utilization 뷰 업데이트

### P2: AI 분석 파라미터 관리 UI
- LLM 모델 선택
- 프롬프트 조정

### P3: UI 간소화
- 일반 사용자용 간소화된 인터페이스

### P3: 나머지 탭 DataHub 연결
- Convergence, SignalProcessing, Assetization 탭

### P3: 경영관리 모듈
- 서비스 플랜 및 빌링

### P3: 대시보드 UI/UX 개선
- PDF 다운로드 버튼 수정
- PDF 한글 깨짐 해결

---

## 테스트 계정
- **최고관리자**: admin@gvic.com / password

---

## 주요 파일

### Frontend
- `/app/frontend/src/components/tabs/GVICShowcaseTab.jsx` - AI 분석 쇼케이스
- `/app/frontend/src/components/tabs/` - 14개 탭 컴포넌트
- `/app/frontend/src/components/tabs/ComparisonTab.jsx` - DataHub 연동 비교 탭

### Backend
- `/app/backend/server.py` - 메인 API 서버 (3000+ lines)
- `/app/backend/core/signal_detector.py` - AI 시그널 분석 로직
- `/app/backend/core/gvic_models.py` - ID 체계 및 데이터 모델
- `/app/backend/core/data_hub.py` - DataHub 통합 데이터 관리
- `/app/backend/adapters/output_adapter.py` - PDF 생성 로직

### Scripts (로컬용)
- `/app/scripts/start_all.bat` - 로컬 시작 스크립트

---

## API 엔드포인트

### AI 분석
- `POST /api/signal-tracer/ai-analyze` - AI 기반 시그널 분석

### 자산 관리
- `GET /api/gvic-assets` - 자산 목록 조회 (통계 포함)
- `POST /api/gvic-assets` - 자산 생성
- `GET /api/gvic-assets/{asset_id}` - 자산 상세 조회
- `DELETE /api/gvic-assets/{asset_id}` - 자산 삭제

---

## 데이터 모델

### ID 체계
```
USR_YYYYMMDDHHMMSS_XXXXXX : 사용자
INP_YYYYMMDDHHMMSS_XXXXXX : 입력
MOD_YYYYMMDDHHMMSS_XXXXXX : 모듈
SIG_YYYYMMDDHHMMSS_XXXXXX : 시그널
AST_YYYYMMDDHHMMSS_XXXXXX : 자산
```

### 관계
```
User (1) → Input (N)
Input (1) → Module (N)
Module (1) → Signal (N)
Input + Module + Signals → Asset
```

---

## 3rd Party Integrations
- **OpenAI/Gemini** (via Emergent LLM Key) - AI 분석
- **MongoDB** - 데이터 저장
- **ReportLab** - PDF 생성
- **Emergent Google Auth** - 소셜 로그인
