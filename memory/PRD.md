# GVIC Engine - Product Requirements Document

## 프로젝트 개요
GVIC(Global Value Integration Convergence) Engine은 7개의 특허를 기반으로 한 데이터 처리 및 가치 분배 시스템입니다.

## 특허 기반 아키텍처

### 수집된 특허 문서 (7개 완료)
| # | 특허명 | 시스템 코드 | 핵심 기능 |
|---|--------|------------|----------|
| 1 | 전역 수렴 제어 시스템 | - | OBC 검증, 수렴 변환, 3단계 복구 |
| 2 | 다단계 신호 전처리 | - | 벡터 변환, 정합성 판별, 재귀적 분류 |
| 3 | 신호 자산화 플랫폼 | - | 가치 산출, 자산 객체 생성 |
| 4 | 재귀적 모듈화 | - | 파이프라인 조합, AST 기반 처리 |
| 5 | 비적합 데이터 자산화 | 3000 | 비적합 감지/분류/가치평가/자산변환 |
| 6 | 가중 분배 모델 | 4000 | WDM 기반 배분, 동적 조정 |
| 6-J | 다중 도메인 통합 | - | 이기종 시스템 연동 |

## 핵심 개념

### Sigma (σ) - 분배 비율
- 공공(Public): 기본 33%
- 생산(Productive): 기본 34%
- 개인(Individual): 기본 33%
- 합계 = 1.0 (100%)

### Omega (ω) - 경계 조건
```
V_pub_min: 0.2 (20%), V_pub_max: 0.5 (50%)
V_pro_min: 0.2 (20%), V_pro_max: 0.5 (50%)
V_ind_min: 0.1 (10%), V_ind_max: 0.5 (50%)
```

## 백엔드 모듈 구조

```
/app/backend/core/
├── engine.py                    # GVIC 통합 엔진
├── patent1_convergence.py       # 특허1: 전역 수렴 제어
├── patent2_signal.py            # 특허2: 신호 전처리
├── patent3_signal_asset.py      # 특허3: 신호 자산화
├── patent3_pipeline.py          # 특허4: 파이프라인
├── patent4_nonconform.py        # 특허5: 비적합 데이터 (3000)
├── patent5_distribution.py      # 특허6: 가중 분배 (4000)
├── patent6_interface.py         # 도메인 인터페이스
├── multi_domain_integration.py  # 특허6-J: 다중 도메인 통합
├── control.py                   # 내부 통제
├── io_interface.py              # IO 인터페이스
├── visualization.py             # 시각화
└── workflow.py                  # 워크플로우
```

## 프론트엔드 모듈 구조 (리팩토링 완료)

```
/app/frontend/src/
├── App.js                       # 메인 앱 컴포넌트 (135줄)
├── lib/
│   └── api.js                   # API 함수 모듈
├── components/
│   ├── MetricCard.jsx           # 공통 메트릭 카드 컴포넌트
│   └── tabs/
│       ├── index.js             # 탭 컴포넌트 내보내기
│       ├── DashboardTab.jsx     # 대시보드 탭
│       ├── ProcessingTab.jsx    # 처리 탭
│       ├── ModelsTab.jsx        # 모델 탭
│       ├── PredictionTab.jsx    # 예측 탭
│       ├── ParetoTab.jsx        # 파레토 탭
│       ├── ComparisonTab.jsx    # 비교 탭
│       ├── MonitoringTab.jsx    # 모니터링 탭
│       ├── IntegrationTab.jsx   # 통합 탭
│       ├── DataSourcesTab.jsx   # 외부소스 탭 (P4)
│       ├── DataTab.jsx          # 데이터 탭
│       ├── AlertsTab.jsx        # 알림 탭
│       └── SettingsTab.jsx      # 설정 탭
└── components/ui/               # Shadcn UI 컴포넌트
```

## API 엔드포인트

### 대시보드
- `GET /api/dashboard` - 대시보드 데이터
- `GET /api/status` - 시스템 상태

### 처리
- `POST /api/process` - 값 처리 실행
- `GET /api/process/history` - 처리 이력

### 설정
- `GET/PUT /api/config/sigma` - 시그마 설정
- `GET/PUT /api/config/omega` - 오메가 설정

### 통합 (특허 6-J)
- `GET /api/integration/status` - 통합 상태
- `POST /api/integration/exchange` - 데이터 교환
- `GET/POST /api/integration/adapters` - 어댑터 관리
- `GET/POST /api/integration/mappings` - 매핑 관리

## 구현 완료 내역

### 2026-02-12: 특허 기반 백엔드 리팩토링
- [x] 특허 1: 전역 수렴 제어 시스템 재구현
  - OmegaConstraints 클래스
  - ConvergenceController 통합
  - 3단계 복구 프로세스
  - 엔트로피 균형 지표

- [x] 특허 2: 신호 전처리 시스템 재구현
  - VectorTransformer (벡터 변환부)
  - ConformanceChecker (정합성 판별부)
  - RecursiveRemodulator (재귀적 분류)
  - AdaptiveClassifier (적응형 분류)

- [x] 특허 3: 신호 자산화 플랫폼 구현
  - SignalCollector, SignalNormalizer
  - ValueCalculator (가치 산출 알고리즘)
  - AssetObject 생성
  - IntegrityManager

- [x] 특허 4: 재귀적 모듈화 파이프라인
  - ModuleRegistry
  - PipelineBuilder
  - ExecutionEngine
  - StateManager (체크포인트 복구)

- [x] 특허 5: 비적합 데이터 자산화 (시스템 3000)
  - NonConformanceDetector (3100)
  - QuarantineStorage (3150)
  - NonConformanceClassifier (3200)
  - ValueAssessor (3300)
  - AssetConverter (3400)
  - RuleImprovementSuggester (3500)

- [x] 특허 6: 가중 분배 모델 시스템 (시스템 4000)
  - ModelRepository (4100)
  - AllocationCalculator (4200)
  - ConsumptionMonitor (4300)
  - DynamicAdjuster (4400)
  - AnalyticsUnit (4500)

- [x] GVICEngine 통합 엔진 업데이트
  - 7개 특허 모듈 통합
  - 처리 파이프라인 구현

## 테스트 결과

### API 테스트 (2026-02-12)
```bash
# Process API 테스트
curl -X POST "/api/process" -d '{"value": 5.0}'
# 결과: success=true, balance_score=0.997

# Dashboard API 테스트  
curl "/api/dashboard"
# 결과: metrics, sigma, omega, charts 정상 반환
```

### 프론트엔드 검증 (2026-02-12)
- [x] 대시보드 탭: 분배 비율(Sigma) 파이차트, 균형 상태(Omega) 게이지 정상 표시
- [x] 처리 탭: 7개 특허 파이프라인 실행 정상, 처리 결과 시각화 정상
- [x] 데이터 탭: 입출력 테스트, 활동 로그 정상
- [x] 통합 탭: 정상 작동
- [x] 모든 UI 컴포넌트가 리팩토링된 백엔드 API와 정상 연동 확인

## 구현 완료 (P0)

### 프론트엔드 업데이트 (완료)
- [x] 새로운 백엔드 모듈에 맞춘 UI 컴포넌트 업데이트
- [x] 특허 5 (비적합 데이터) 감지 알림 표시
- [x] 특허 6 (가중 분배) 분석 결과 시각화
- [x] 처리 결과 차트 (분배 결과, 수렴 변환)

## 구현 완료 (P1) - 2026-02-12

### 전체 기능 통합 테스트 (완료)
- [x] testing_agent_v3_fork를 사용한 E2E 테스트 (백엔드 29/29, 프론트엔드 6/6 탭 통과)
- [x] 엣지 케이스 검증 완료

### 코드 품질 개선 (완료)
- [x] 린터 경고 수정 (ruff) - backend/core, backend/utils 모두 통과
- [x] App.js 컴포넌트 분리 완료 (1328줄 → 135줄, 90% 감소)
  - 7개 탭 컴포넌트 분리 (DashboardTab, ProcessingTab, MonitoringTab, IntegrationTab, DataTab, AlertsTab, SettingsTab)
  - API 함수 모듈화 (/lib/api.js)
  - 공통 컴포넌트 분리 (MetricCard)

## 구현 완료 (P2) - 2026-02-12

### 처리 이력 MongoDB 영구 저장 (완료)
- [x] 처리 결과 MongoDB 저장 (기존 구현 확인)
- [x] 이력 조회 API (GET /api/process/history)
- [x] ProcessingTab에 이력 목록/차트 뷰 추가

### 분석 리포트 생성 기능 (완료)
- [x] ReportLab 라이브러리 설치
- [x] PDF 리포트 생성 API (POST /api/report/generate)
- [x] 리포트 요약 API (GET /api/report/summary)
- [x] DashboardTab에 "PDF 리포트 다운로드" 버튼 추가

### 실시간 소비 모니터링 연동 (완료)
- [x] 실시간 모니터링 API (GET /api/monitor/realtime)
- [x] 분배 상태 모니터링 API (GET /api/monitor/distribution)
- [x] MonitoringTab 컴포넌트 신규 생성
  - 실시간 소비량 스택 차트
  - 분배 비율 비교 (목표 vs 실제)
  - 편차 분석
  - 2초 간격 폴링 기반 실시간 업데이트

### 동적 조정 자동화 (완료)
- [x] 자동 조정 설정 API (GET/PUT /api/adjustment/config)
- [x] 수동 조정 실행 API (POST /api/adjustment/execute)
- [x] 조정 이력 API (GET /api/adjustment/history)
- [x] SettingsTab에 DynamicAdjuster 섹션 추가
  - 자동 조정 활성화 토글
  - 편차 임계값/조정률 설정
  - 수동 조정 실행 버튼
  - 조정 이력 표시

## 향후 작업 (P3)

### 추가 기능
- [ ] 다중 모델 전환 기능
- [ ] 시계열 예측 기반 사전 조정
- [ ] 파레토 최적화 배분
- [ ] 처리 결과 비교 분석 기능

## 구현 완료 (P3) - 2026-02-12

### 다중 모델 전환 기능 (완료)
- [x] 5개 사전 정의 모델 (기본 균형, 공공 우선, 생산 우선, 개인 우선, 성장 집중)
- [x] 모델 관리 API (GET/POST/DELETE /api/models, POST /api/models/{id}/activate)
- [x] ModelsTab 컴포넌트 신규 생성
  - 모델 카드 그리드 뷰
  - 커스텀 모델 생성 다이얼로그
  - 모델 활성화/삭제 기능

### 시계열 예측 기반 사전 조정 (완료)
- [x] 이동 평균 + 지수 평활 앙상블 예측 알고리즘
- [x] 예측 분석 API (POST /api/prediction/analyze)
- [x] 예측 적용 API (POST /api/prediction/apply)
- [x] PredictionTab 컴포넌트 신규 생성
  - 예측 설정 (윈도우 크기, 예측 스텝, 신뢰도 임계값)
  - 예측 분배 비율 차트
  - 현재 vs 예측 시그마 비교

### 파레토 최적화 배분 (완료)
- [x] 4가지 최적화 목표 (균형, 공공 가치, 효율성, 리스크)
- [x] 파레토 프론트 계산 알고리즘
- [x] 파레토 최적화 API (POST /api/pareto/optimize, POST /api/pareto/apply/{index})
- [x] ParetoTab 컴포넌트 신규 생성
  - 최적화 목표 카드
  - 최적 솔루션 상세 정보
  - 파레토 프론트 산점도 차트
  - 솔루션 목록 및 적용 기능

### 처리 결과 비교 분석 기능 (완료)
- [x] 통계 분석 (최소/최대/평균/표준편차)
- [x] 트렌드 분석 (상승/하락/안정)
- [x] 이상치 탐지 (2σ 기준)
- [x] 비교 분석 API (POST /api/comparison/analyze)
- [x] ComparisonTab 컴포넌트 신규 생성
  - 자산 가치 & 균형 점수 추이 차트
  - 분배 비율 비교 스택 바 차트
  - 상세 데이터 테이블

## 향후 작업 (P4)

### 추가 기능
- [x] 외부 데이터 소스 연동 (실제 API/센서) - 완료 (2026-02-12)
- [ ] 사용자 인증 및 권한 관리
- [ ] 다국어 지원
- [ ] 모바일 반응형 UI 개선

## 구현 완료 (P4) - 2026-02-12

### 외부 데이터 소스 연동 기능 (완료)
- [x] 데이터 소스 CRUD API 구현
  - GET/POST /api/datasources - 목록 조회/생성
  - GET/PUT/DELETE /api/datasources/{source_id} - 상세/수정/삭제
- [x] 데이터 수집 기능
  - POST /api/datasources/{source_id}/fetch - 수동 데이터 가져오기
  - POST /api/datasources/{source_id}/process - GVIC 엔진으로 처리
  - POST /api/datasources/{source_id}/start/stop - 자동 폴링 시작/중지
  - GET /api/datasources/collected - 수집된 데이터 조회
- [x] DataSourcesTab 컴포넌트 신규 생성
  - 데이터 소스 카드 목록 (상태 배지, URL, 폴링 간격, 수집 횟수)
  - 소스 추가/수정 다이얼로그 (이름, 소스 유형, HTTP 메소드, URL, 인증 설정, 폴링 간격, 데이터 매핑 경로)
  - 데이터 가져오기/GVIC 처리/자동 수집 시작-중지/수정/삭제 버튼
  - 최근 수집 데이터 목록 (소스명, 추출값, 타임스탬프, 처리 상태)
- [x] App.js에 "외부소스" 탭 추가 (Cloud 아이콘)
- [x] api.js에 데이터 소스 관련 API 함수 추가

### 테스트 결과 (P4)
- 백엔드 API 테스트: 17/17 통과 (100%)
- 프론트엔드 UI 테스트: 모든 컴포넌트 정상 작동 (100%)
- 테스트 API: https://jsonplaceholder.typicode.com/posts/1

## 향후 작업 (P5)

### 추가 기능
- [x] 사용자 인증 및 역할 기반 접근 제어 (RBAC) - 완료 (2026-02-12)
- [ ] 대시보드 UI/UX 전면 개편
- [ ] 다국어 지원
- [ ] 모바일 반응형 UI 개선

## 구현 완료 (P5) - 2026-02-12

### 사용자 인증 및 역할 기반 접근 제어 (RBAC) (완료)
- [x] **JWT 기반 커스텀 인증**
  - 회원가입 API (POST /api/auth/register)
  - 로그인 API (POST /api/auth/login)
  - 비밀번호 변경 API (PUT /api/auth/password)
- [x] **Google OAuth 연동 (Emergent Auth)**
  - Google 세션 교환 API (POST /api/auth/google/session)
  - OAuth 콜백 처리 (/auth/callback)
- [x] **역할 기반 접근 제어 (RBAC)**
  - 3단계 역할: Admin (전체 권한), Operator (처리/리포트), Viewer (읽기 전용)
  - 역할별 메뉴/탭 접근 제한
  - API 엔드포인트 권한 검사
- [x] **사용자 관리 (Admin 전용)**
  - 사용자 목록 조회 API (GET /api/auth/users)
  - 역할 변경 API (PUT /api/auth/users/{id})
  - 사용자 삭제 API (DELETE /api/auth/users/{id})
  - UsersTab 컴포넌트
- [x] **프론트엔드 인증 UI**
  - LoginPage 컴포넌트 (로그인/회원가입 탭)
  - AuthCallback 컴포넌트 (OAuth 콜백 처리)
  - AuthContext (인증 상태 관리)
  - ProtectedRoute (인증 필요 라우트 보호)
  - 사용자 메뉴 드롭다운

### 테스트 결과 (P5)
- 백엔드 인증 API: 모든 엔드포인트 정상 작동
- JWT 토큰 발급/검증: 정상
- Google OAuth: Emergent Auth 연동 완료
- 역할별 접근 제어: 정상 작동

## 향후 작업 (P6)

### 추가 기능
- [ ] 대시보드 UI/UX 전면 개편
- [ ] 다국어 지원
- [ ] 모바일 반응형 UI 개선

## 특허 문서 저장 경로
```
/app/memory/patents/
├── patent1_convergence.md
├── patent2_signal_preprocessing.md
├── patent3_signal_assetization.md
├── patent4_recursive_modularization.md
├── patent5_nonconforming_data_assetization.md
├── patent6_weighted_distribution_model.md
└── patent6j_multi_domain_integration.md
```
