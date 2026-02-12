# GVIC Engine Dashboard - PRD

## 원본 요구사항
- Streamlit 기반 GVIC Engine 대시보드를 React + FastAPI 웹 애플리케이션으로 변환
- 7개 특허 모듈 통합:
  1. 특허1: 수렴 제어 모듈
  2. 특허2: 신호 자산화 모듈
  3. 특허3: 파이프라인 프로세서
  4. 특허4: 비적합 처리 모듈
  5. 특허5: 가중 분배 모듈
  6. 특허6: 도메인 인터페이스
  7. **특허6-J: 다중 도메인 통합 인터페이스 시스템 (NEW)**

## 아키텍처
```
Frontend (React + Tailwind)
├── 대시보드 탭 (메트릭, 차트)
├── 처리 탭 (GVIC 엔진 실행)
├── 통합 탭 (다중 도메인 통합) ⭐ NEW
├── 데이터 탭 (IO 테스트, 로그)
├── 알림 탭 (헬스체크, 통계)
└── 설정 탭 (Σ/Ω 설정, 모듈 상태)

Backend (FastAPI + MongoDB)
├── core/ (7개 특허 모듈)
│   ├── engine.py (통합 엔진)
│   ├── patent1_convergence.py (수렴 제어)
│   ├── patent2_signal.py (신호 자산화)
│   ├── patent3_pipeline.py (파이프라인)
│   ├── patent4_nonconform.py (비적합 처리)
│   ├── patent5_distribution.py (가중 분배)
│   ├── patent6_interface.py (도메인 인터페이스)
│   ├── multi_domain_integration.py ⭐ (다중 도메인 통합)
│   ├── control.py (내부 통제)
│   └── io_interface.py (입출력)
└── utils/ (설정, 로깅)
```

## 특허 6-J: 다중 도메인 통합 인터페이스 시스템

### 핵심 구성요소
1. **Domain Adapter Manager** - 도메인별 어댑터 관리 (ERP, CRM, SCM, MES, Finance 등)
2. **Data Transformation Engine** - CDM(공통 데이터 모델) 변환 엔진
3. **Semantic Mapping Repository** - 도메인 간 필드 의미 매핑 저장소
4. **Routing Engine** - 규칙 기반 메시지 라우팅
5. **Integration Monitor** - 실시간 모니터링 (처리량, 지연시간, 에러)

### 주요 기능
- Hub-and-Spoke 아키텍처로 O(n²) → O(n) 복잡도 감소
- 자동 데이터 형식 변환 (JSON, REST, MQ, File, EDI)
- 의미 기반 필드 매핑 (유사도 점수)
- 우선순위 기반 라우팅 규칙

## 구현 완료 (2026-02-12)
- ✅ React 프론트엔드 (6개 탭, 다크 테마)
- ✅ FastAPI 백엔드 (30+ API 엔드포인트)
- ✅ 7개 특허 모듈 Python 구현
- ✅ 분배 비율 파이차트, 균형 게이지차트
- ✅ GVIC 엔진 처리 및 결과 시각화
- ✅ **다중 도메인 통합 인터페이스**
  - 도메인 어댑터 관리 (5개 기본 어댑터)
  - 의미 매핑 (6개 기본 매핑)
  - 라우팅 규칙 (4개 기본 규칙)
  - 데이터 교환 테스트
  - 실시간 모니터 (처리량, 지연시간)
- ✅ IO 테스트 (JSON, CSV, Key-Value)
- ✅ 헬스체크 및 알림 시스템
- ✅ Σ/Ω 설정 관리
- ✅ MongoDB 연동 (처리 이력 저장)

## API 엔드포인트 (신규 추가)
- `GET /api/integration/status` - 통합 시스템 상태
- `POST /api/integration/exchange` - 데이터 교환 실행
- `GET /api/integration/adapters` - 어댑터 목록
- `POST /api/integration/adapters` - 어댑터 추가
- `GET /api/integration/mappings` - 매핑 목록
- `POST /api/integration/mappings` - 매핑 추가
- `GET /api/integration/routing` - 라우팅 규칙 목록
- `POST /api/integration/routing` - 라우팅 규칙 추가

## 테스트 결과
- Backend: 100% (30+ endpoints)
- Frontend: 100% (6개 탭 모두 정상)
- Integration: 100%

## 백로그
- P1: 실시간 데이터 스트리밍 (WebSocket)
- P1: 어댑터 동적 추가 UI
- P2: 처리 이력 차트 (시계열)
- P2: 알림 라우팅 (이메일, Slack)
- P3: 다국어 지원

## 다음 단계
1. 사용자 피드백 수집
2. 추가 도메인 어댑터 구현
3. 매핑 자동 추천 기능
4. 성능 최적화
