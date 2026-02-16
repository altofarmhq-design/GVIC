# GVIC 시그널 온톨로지 자산화 플랫폼 - PRD

**Last Updated**: 2026-02-16

## 1. 제품 개요

### 1.1 비전
GVIC는 14개 특허를 기반으로 한 AI 기반 시그널 분석 및 자산화 플랫폼입니다.
모든 입력 시그널의 "의도"를 핵심 자산으로 취급하여, 자동 분석/축적/상품화/가치 교환을 수행합니다.

## CHANGELOG

### 2026-02-16 (최신 - P1 버그 수정: Insight Derivation)
- **[BUG FIX]** Insight Derivation 기능 수정 완료
  - 문제: `gvic_analyses` 컬렉션에서 데이터를 가져오지 못해 키워드가 0개였음
  - 수정: `gvic_analyses.result`에서 인사이트 추출, 콘텐츠에서 직접 키워드 추출
  - 개선: 핵심 인사이트 생성 로직 강화 (패턴, 트렌드, 데이터, GVIC 분석 인사이트)
  - 결과: 20개 키워드 추출, 5개 핵심 인사이트 생성 확인

### 2026-02-16 (이전 - F:실행 물리 노드 대시보드 UI 추가)
- **[FEATURE]** F:실행 탭에 물리 계층 시각화 대시보드 추가
  - 대시보드 탭: 시스템 상태, 활성 노드, 에너지 효율, 팩토리 균형
  - 물리 노드 탭: 3개 노드 상태 실시간 모니터링
  - 엔트로피 탭: dS/dt 변화율, 에너지 효율 게이지, G:정제 피드백
  - 자원 사영 탭: 5:3:2 배분 벡터 → 물리량 사영 테스트
  - 자동 갱신, 재균형, 킬스위치 임계치 표시
  - 테스트 에이전트 검증 완료 (100%)

### 2026-02-16 (이전 - 특허 F 물리 계층 집행 시스템 구현)
- **[FEATURE]** 특허 F(물리 계층 자원 집행 시스템) 완전 구현
  - 자원 사영 엔진 (1110): 배분 벡터 → 물리량 변환
  - 팩토리 평형 컨트롤러 (1120): 분산 노드 간 부하 균형
  - 엔트로피 역전 유닛 (1130): dS/dt 모니터링 및 피드백
  - 열역학적 킬스위치: 임계치 초과 시 자동 차단
  - 하드웨어 상태 보정기: 마모율 기반 가중치 재계산
  - 위상 정합 엔진: 집행 신호 동기화
  - D:LEDGER 동기화: 비가역적 증명 데이터 원장 기록
  - I:INTEGRITY 검증 연동: 무결성 1:1 대응
  - 테스트 에이전트 검증 완료 (21/21 테스트 통과, 100%)

### 2026-02-16 (이전 - 14개 특허 백엔드 리팩토링)
- **[REFACTOR]** 14개 특허 기반 백엔드 모듈 구조 완성
  - `/app/backend/patents/` 디렉토리에 11개 특허 모듈 구현
  - 총 59개+ Patent API 엔드포인트 등록
  - 테스트 에이전트 검증 완료 (45/45 테스트 통과, 100%)
  
- **특허 모듈 구현 완료:**
  | 모듈 코드 | 파일명 | 기능 | 주요 API |
  |----------|--------|------|----------|
  | J:Platform | j_platform.py | 입력 채널 관리 | /api/patent/j/channels, /stats, /validate |
  | LL:Intelligence | ll_intelligence.py | AI 의도 분석 | /api/patent/ll/analyze, /classify, /intent-types |
  | H:Core | h_core.py | 5:3:2 결이론 설정 | /api/patent/h/532-theory, /calculate-532, /sigma, /omega |
  | A:Gate | a_gate.py | 시그널 평가/필터링 | /api/patent/a/rules, /evaluate, /stats |
  | E:Shield | e_shield.py | 보안 검사 | /api/patent/e/scan, /hash, /verify-integrity |
  | G:Refine | g_refine.py | 데이터 정제 | /api/patent/g/clean, /normalize, /extract-keywords, /summarize |
  | B:Calc | b_calc.py | 가치 계산 | /api/patent/b/calculate-value, /calculate-reward |
  | C:Exec | c_exec.py | 실행 관리 | /api/patent/c/execute, /actions, /queue, /history |
  | F:Field | f_field.py | 마켓플레이스 | /api/patent/f/marketplace, /register, /listing |
  | D:Ledger | d_ledger.py | 분산원장 | /api/patent/d/record, /query, /verify-chain, /balance |
  | I:Integrity | i_integrity.py | 무결성 감사 | /api/patent/i/health, /system-check, /audit-logs |

### 2026-02-16 (이전)
- **[FIX]** URL 처리 실패 버그 수정 - 쇼핑몰 URL 크롤러 라우팅 구현
  - `signal_ingest.py`에 `detect_shopping_platform()` 함수 추가
  - 네이버 스마트스토어, 쿠팡, 11번가, G마켓, 옥션, Amazon, AliExpress URL 감지
  - 쇼핑몰 URL → 리뷰 크롤러로 라우팅 (`input_type='shopping_url'`)
  - 일반 URL → 텍스트 추출 처리 (`input_type='generic_url'`)
- **[VERIFIED]** 테스트 에이전트 검증 완료 (백엔드 17/17 통과, 프론트엔드 100%)
- **[FEATURE]** P1: API 연동 기능 구현
  - 외부 시스템 웹훅 API 엔드포인트 (`/api/webhook/signal`, `/api/webhook/signal/batch`, `/api/webhook/event`)
  - API 키 생성/관리/삭제 기능
  - API 키 기반 인증 시스템
  - 배치 시그널 수신 (최대 100개)
  - 이벤트 기반 시그널 수신
  - API 사용 가이드 UI
- **[FEATURE]** P1: PDF 리포트 생성 기능 구현
  - 시그널 분석 결과 PDF 다운로드 (`/api/report/signal`)
  - 대시보드 통계 PDF 리포트 (`/api/report/dashboard`)
  - 자산 포트폴리오 PDF 리포트 (`/api/report/assets`)
- **[FEATURE]** 외부 연동 커넥터 시스템 구현
  - Zapier, n8n, Make, 커스텀 연동 가이드
  - 시그널/배치/워크플로우 시뮬레이션 기능
  - 연동 활용 사례 가이드 (이메일→시그널, Slack 모니터링, 폼 제출 분석 등)
  - 이벤트 로그 시스템
  - 스케줄 작업 관리 (시뮬레이션)
  - 아웃바운드 웹훅 설정
- **[FEATURE]** 포인트 시스템 구현
  - 사용자별 포인트 잔액 관리 (`/api/points/balance`)
  - 포인트 적립/사용/전환 API (`/api/points/earn`, `/api/points/spend`, `/api/points/convert`)
  - 자산 축적 현황 요약 (`/api/points/asset-summary`)
  - 현금:포인트 환율 = 1:0.1
  - 기여 레벨 시스템 (입문자→기여자→숙련자→전문가→마스터)
  - 등급 시스템 (Bronze→Silver→Gold→Platinum→Diamond)
  - 포인트 적립 기준 (시그널 제출 +10P, 코드 분석 +15P, 특허/아이디어 +25P, 자산 생성 +50P 등)
  - 유료 전환 시 포인트로 현금 대체 가능
- **[UI]** API 연동 탭 추가 (API 키 관리 및 사용 가이드)
- **[UI]** 외부연동 탭 추가 (연동 플랫폼, 시뮬레이션, 활용 사례)
- **[UI]** 내 자산 탭 추가 (포인트 잔액, 자산 현황, 기여 레벨, 포인트 전환)
- **[UI]** 사용자 드롭다운에 포인트 정보 표시 (잔액, 현금 환산, 환율)
- **[UI]** J:입력 탭에 API (준비중) 표시 추가

### 2026-02-16 (이전)
- **[FIX]** AI Analyzer 초기화 오류 수정 - `LlmChat` 사용법 수정 (`model` 파라미터 → `.with_model()` 메서드)
- **[FIX]** 시그널 전송 실패 문제 해결
- **[VERIFIED]** J:입력 탭에서 시그널 분석 및 AI 응답 생성 기능 정상 작동 확인
- **[FEATURE]** HWP/HWPX/DOCX 파일 형식 지원 추가
- **[UI]** 파일 업로드 영역에 지원 형식 안내 UI 추가
- **[UI]** 지원하지 않는 파일 형식 업로드 시 에러 메시지 및 지원 형식 안내 표시
- **[FEATURE]** 3가지 AI 분석 유형 추가:
  - 📝 일반 분석: 텍스트/문서 시그널 분석
  - 💻 코드 분석: 문법 오류, 버그, 코드 품질 평가, 보안 취약점 검출
  - 💡 특허/아이디어 분석: 신규성, 실현가능성, 시장성 평가
- **[FEATURE]** 코드 파일 확장자 지원 (.py, .js, .ts, .java, .c, .cpp 등 25종+)
- **[UI]** 코드 파일 업로드 시 자동으로 "코드 분석" 모드 전환
- **[UI]** AI 분석 결과 상세 표시 UI 구현:
  - 일반 분석: 목적 분석, 기대 결과 답변, 근거, 추가 인사이트
  - 코드 분석: 문법 오류, 버그 가능성(심각도 표시), 코드 품질 점수(가독성/유지보수성/효율성), 개선 제안
  - 특허/아이디어: 핵심 개념, 종합 평가(신규성/실현가능성/시장성/혁신성 %), 시장 잠재력, 종합 추천
- **[FIX]** 대시보드 통계 오류 수정 - MongoDB pipeline_signals 컬렉션 기반 실시간 집계
- **[FIX]** 성공률 표시 버그 수정 (10000% → 100%)
- **[FIX]** 최근 처리 이력 통계 표시 수정
- **[UI]** 시간 표시 UTC→사용자 현지 시각 자동 변환
- **[FEATURE]** 5:3:2 시그널 분류 비율 설정 UI 및 조절 기능 추가
- **[FEATURE]** 비율 기반 분류 로직 구현 (백엔드 AI 분석 시 반영)
- **[FEATURE]** 자산화 단계 완전 구현:
  - A단계: 데이터 라벨링 (분류/태깅)
  - E단계: 가치 측정 (신규성, 활용가능성 점수)
  - G단계: 자산 저장 및 연결
- **[FEATURE]** 모듈화 단계 완전 구현:
  - B단계: 모듈 패키징 (유사 자산 그룹화)
  - C단계: 가격 책정 (가치 기반)
  - F단계: 판매 등록
  - I단계: 보상 분배 구조 설정 (기여자 70%, 플랫폼 20%, 큐레이터 10%)

### 1.2 핵심 철학
- **Intent as Asset**: 입력 데이터가 아닌 "의도"를 자산으로 인식
- **결이론 5:3:2**: 가치 분배 비율 (공공:생산:개인)
- **Operator-in-the-Loop**: 인간 운영자가 상품화 결정

## 2. 현재 구현 상태 (MVP)

### 2.1 완료된 기능 ✅

#### 핵심 기능
| 기능 | 상태 | 설명 |
|------|------|------|
| 14개 특허 기반 탭 UI | ✅ 완료 | J:입력 ~ I:무결성 + 대시보드, 설정, 사용자 |
| AI 시그널 분석 | ✅ 완료 | Gemini 3 Flash 연동 |
| 의도 추출 | ✅ 완료 | 시그널 유형 감지, 감성 분석 |
| 자산화 저장 | ✅ 완료 | MongoDB 저장/조회/삭제 |
| 대시보드 | ✅ 완료 | 실시간 통계, 시그널 유형별 분포 |

#### J:입력 채널 (시그널 유입)
| 채널 | 상태 | 설명 |
|------|------|------|
| 텍스트 | ✅ 활성화 | 직접 입력 |
| 파일 | ✅ 활성화 | Excel, CSV, PDF, TXT, 이미지 |
| URL | ✅ 활성화 | 웹페이지 텍스트 추출 |
| API | ⏸️ 준비중 | 다음 단계 |

#### 인증/권한
| 기능 | 상태 | 설명 |
|------|------|------|
| JWT 인증 | ✅ 완료 | 로그인/로그아웃 |
| Google OAuth | ✅ 완료 | Emergent Auth 연동 |
| 역할 기반 권한 | ✅ 완료 | super_admin/admin/operator/visitor |

#### 시스템 설정
| 기능 | 상태 | 설명 |
|------|------|------|
| Σ (시그마) 설정 | ✅ 완료 | 5:3:2 비율 조정 |
| Ω (오메가) 경계 조건 | ✅ 완료 | 값 범위 설정 |

### 2.2 14개 특허 탭 구조

```
┌─────────────────────────────────────────────────────────────┐
│  대시보드 │ J:입력 │ LL:의도 │ H:코어 │ A:게이트 │ E:방어막 │ G:정제 │
├─────────────────────────────────────────────────────────────┤
│  B:산출 │ C:집행 │ F:실행 │ D:원장 │ I:무결성 │ 설정 │ 사용자 │
└─────────────────────────────────────────────────────────────┘
```

| 탭 코드 | 기능 | 특허명 | 구현 상태 |
|--------|------|--------|----------|
| J | 입력 | PLATFORM | ✅ UI 완료 |
| LL | 의도 | INTELLIGENCE | ✅ AI 분석 연동 |
| H | 코어 | CORE | ✅ 시그마 설정 |
| A | 게이트 | GATE | ✅ UI 완료 |
| E | 방어막 | SHIELD | ✅ UI 완료 |
| G | 정제 | REFINE | ✅ UI 완료 |
| B | 산출 | CALC | ✅ UI 완료 |
| C | 집행 | EXEC | ✅ UI 완료 |
| F | 실행 | FIELD | ✅ UI 완료 |
| D | 원장 | LEDGER | ✅ UI 완료 |
| I | 무결성 | INTEGRITY | ✅ UI 완료 |

## 3. 기술 스택

### Frontend
- React 18+
- Tailwind CSS + Shadcn/UI
- React Router v6
- Axios

### Backend  
- FastAPI (Python)
- MongoDB
- JWT Authentication
- Emergent Integration (Gemini 3 Flash)

### 배포
- App Preview: https://intent-exchange.preview.emergentagent.com
- 로컬 환경: D:\GVIC

## 4. API 엔드포인트

### 인증
- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/auth/me` - 현재 사용자 정보
- `POST /api/auth/logout` - 로그아웃

### 시그널 분석
- `POST /api/signal-tracer/ai-analyze` - AI 분석 실행
- `GET /api/gvic-assets` - 자산 목록 조회
- `POST /api/gvic-assets` - 자산 저장
- `DELETE /api/gvic-assets/{id}` - 자산 삭제

### 설정
- `GET/PUT /api/config/sigma` - 시그마 설정
- `GET/PUT /api/config/omega` - 오메가 설정

### 대시보드
- `GET /api/dashboard` - 대시보드 데이터
- `GET /api/dashboard/realstats` - 실시간 통계

## 5. 로컬 환경 설정

### 디렉토리 구조
```
D:\GVIC\
├── backend\
│   ├── server.py
│   ├── auth.py
│   ├── .env
│   └── requirements.txt
├── frontend\
│   ├── src\
│   │   ├── App.js
│   │   └── components\tabs\patent\
│   └── package.json
├── data\db\         (MongoDB 데이터)
├── scripts\
│   ├── start_all.bat
│   └── install_full.bat
└── docs\
```

### 실행 방법
```batch
cd /d D:\GVIC
scripts\start_all.bat
```

## 6. 향후 계획

### P0 (완료)
- [x] 14개 특허 기반 백엔드 모듈 구조 완성 (2026-02-16)
- [x] 11개 특허 모듈 API 59개 엔드포인트 구현
- [ ] 각 특허 탭 프론트엔드 UI와 백엔드 API 연결

### P1 (진행중/중요)
- [ ] Insight Derivation 버그 수정 (gvic_analyzer.py의 get_insight 함수)
- [ ] 자산 상품화 기능
- [ ] 가치 교환 시스템
- [ ] 보상 분배 로직 프론트엔드 연결

### P2 (개선)
- [ ] PDF 리포트 생성
- [ ] 데이터 시각화 강화
- [ ] 성능 최적화

### P3 (미래)
- [ ] 웹 크롤러 고도화 (Playwright/Selenium)
- [ ] 실제 결제 연동 (Stripe)
- [ ] 실시간 연속 시그널 수집

## 7. 테스트 계정
- Email: admin@gvic.com
- Password: gvicgvic!
- Role: super_admin

## 8. 다음 우선순위 작업

### P2 (예정)
- [ ] 이미지 OCR 처리 기능 추가 - 이미지 파일에서 텍스트 추출

### P3 (미래)
- [ ] 백엔드 리팩토링 (특허 기반 모듈 분리)
- [ ] 벡터 유사도 검색으로 자산 검색 강화
- [ ] 실제 결제 시스템 연동 (Stripe)
- [ ] 실시간 연속 시그널 수집 기능

---
*Last Updated: 2026-02-16*
*Version: 2.1.0*
