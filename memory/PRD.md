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

## 다음 작업 (P1)

### 프론트엔드 업데이트
- [ ] 새로운 백엔드 모듈에 맞춘 UI 컴포넌트 업데이트
- [ ] 특허 5 (비적합 데이터) 시각화 탭 추가
- [ ] 특허 6 (가중 분배) 분석 대시보드 추가
- [ ] 규칙 개선 제안 표시 UI

### 기능 확장
- [ ] 실시간 소비 모니터링 연동
- [ ] 동적 조정 자동화
- [ ] 다중 모델 전환 기능

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
