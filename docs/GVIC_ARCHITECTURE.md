# GVIC 특허 기반 통합 시스템 아키텍처

## 1. 시스템 개요

**GVIC (Global Value Integration & Convergence)**는 12개 특허를 기반으로 한 **시그널 온톨로지 자산화 플랫폼**입니다.

> "존재하는 시그널들의 유형, 감성, 관계를 체계적으로 정의하고, 이를 분석·자산화하여 의사결정에 활용하는 통합 시스템"

---

## 2. 핵심 철학: 결이론 (Gyeoliron)

### 5:3:2 비율
| 영역 | 비율 | 의미 |
|------|------|------|
| **공공 (Public)** | 50% | 사회적 가치, 공공 인프라 |
| **생산 (Production)** | 30% | 생산적 가치, 비즈니스 |
| **개인 (Individual)** | 20% | 개인적 가치, 소비자 |

### 수학적 표현
```
Σ = [0.5, 0.3, 0.2]^T
```

이 비율은 시스템 전체의 **전역 수렴 지표**로 작용하며, 모든 가치 산출과 자원 배분의 기준이 됩니다.

---

## 3. 시스템 흐름도

```
┌─────────────────────────────────────────────────────────────────┐
│                    GVIC 통합 시스템 흐름                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  [외부 시그널 유입]                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ LL: INTELLIGENCE │ ← 비정형 기여도 정량화, 평판 기반           │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ J: PLATFORM │ ← 외부 API 연동, 정규화                          │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ╔═════════════╗                                                 │
│  ║ H: CORE     ║ ← 전역 수렴 제어, 결이론 5:3:2 강제              │
│  ╚══════╤══════╝                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ A: GATE     │ ← 데이터 인지, 정합성 판별                       │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ E: SHIELD   │ ← 독소 데이터 검역, 격리                         │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ G: REFINE   │ ← 가치 정제, 노이즈 제거                         │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ B: CALC     │ ← 가치 산출, 5:3:2 배분 계산                     │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ C: EXEC     │ ← 가치 집행, 자원 배분                           │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ F: FIELD    │ ← 물리 계층 실행, 엔트로피 제어                  │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ D: LEDGER   │ ← 시계열 궤적 저장, 이력 보존                    │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │ I: INTEGRITY│ ← 무결성 증명, 해시 체인                         │
│  └──────┬──────┘                                                 │
│         ▼                                                        │
│  [시스템 수렴 및 자산화 완료]                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. 특허↔모듈 매핑

| 특허 | 노드명 | 백엔드 모듈 | 프론트엔드 | 핵심 기능 |
|------|--------|------------|-----------|----------|
| **H** | CORE | `core/convergence_controller.py` | 설정 | 전역 수렴 제어 |
| **A** | GATE | `core/signal_detector.py` | 시그널분석 | 데이터 인지 |
| **E** | SHIELD | `core/quarantine.py` | (자동) | 독소 검역 |
| **G** | REFINE | `core/value_refiner.py` | (자동) | 가치 정제 |
| **B** | CALC | `core/value_calculator.py` | 시그널분석 | 가치 산출 |
| **C** | EXEC | `core/resource_executor.py` | 자산화창고 | 자원 배분 |
| **D** | LEDGER | `core/trajectory_storage.py` | 데이터 | 궤적 저장 |
| **I** | INTEGRITY | `core/integrity_proof.py` | (자동) | 무결성 증명 |
| **F** | FIELD | `core/physical_executor.py` | 대시보드 | 물리 실행 |
| **J** | PLATFORM | `core/external_api.py` | 외부연동 | API 통합 |
| **LL** | INTELLIGENCE | `core/contribution_quantifier.py` | 기여도 | 기여도 정량화 |
| **GVIC** | (통합) | `server.py` | App.js | 전체 통합 |

---

## 5. 핵심 수학 모델

### 5.1 전역 수렴 지표 (특허 H)
```
Σ = [V_pub, V_pro, V_ind]^T = [0.5, 0.3, 0.2]^T
```

### 5.2 정합성 지수 (특허 A)
```
S_idx = (V_i · Σ) / (||V_i|| × ||Σ||)
```

### 5.3 독소 판별 (특허 E)
```
ΔS = -Σ P(x_i|Σ) log P(x_i|Σ)
독소 조건: ΔS > θ 또는 Z_score ∉ 허용 범위
```

### 5.4 가치 판별 지수 (특허 G)
```
D_idx = ∫|V_cand · Σ| dt - σ_noise
```

### 5.5 유량 제어 (특허 B)
```
dQ/dt = α(R_alloc - R_current) - β∇S
```

### 5.6 자원 집행 (특허 C)
```
E_res = β · (M_conv × R_alloc)
```

### 5.7 물리 실행 (특허 F)
```
E_i(t) = ∫(R_alloc · F_i - κ × dS_i/dt) dt
```

### 5.8 궤적 저장 (특허 D)
```
H(T) = Σ[S(t) · G + L(V_proof(t))]
```

### 5.9 무결성 증명 (특허 I)
```
V_proof(t) = Hash(Σ(t) ⊕ E(t) + V_proof(t-1))
```

### 5.10 기여도 정량화 (특허 LL)
```
C_i = H(D_un) × cos(θ_ref)
```

---

## 6. 시스템 생존 임계 조건 (Ω)

```
조건 1: 0.2 ≤ V_pub ≤ 0.8  (공공 인프라 유지)
조건 2: V_ind ≤ 0.5        (개인 점유 상한)
조건 3: Σ V_i = 1.0        (가치 보존 정규화)
```

---

## 7. 디렉토리 구조

```
/app/
├── backend/
│   ├── core/
│   │   ├── convergence_controller.py  # 특허 H: CORE
│   │   ├── signal_detector.py         # 특허 A: GATE
│   │   ├── quarantine.py              # 특허 E: SHIELD
│   │   ├── value_refiner.py           # 특허 G: REFINE
│   │   ├── value_calculator.py        # 특허 B: CALC
│   │   ├── resource_executor.py       # 특허 C: EXEC
│   │   ├── trajectory_storage.py      # 특허 D: LEDGER
│   │   ├── integrity_proof.py         # 특허 I: INTEGRITY
│   │   ├── physical_executor.py       # 특허 F: FIELD
│   │   ├── external_api.py            # 특허 J: PLATFORM
│   │   └── contribution_quantifier.py # 특허 LL: INTELLIGENCE
│   └── server.py                      # GVIC 통합 서버
├── frontend/
│   └── src/
│       ├── App.js                     # 메인 앱
│       └── components/tabs/           # 탭 컴포넌트
├── patents/                           # 특허 원문
├── docs/                              # 문서
│   ├── GVIC_ARCHITECTURE.md          # 본 문서
│   ├── PATENT_SUMMARY.md             # 특허 요약
│   └── MODULE_MAPPING.md             # 모듈 매핑
└── memory/
    └── PRD.md                         # 제품 요구사항
```

---

## 8. 버전 관리

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-02-15 | 초기 아키텍처 문서 작성 |

---

## 9. 참고 문서

- `/app/patents/` - 특허 원문
- `/app/docs/PATENT_SUMMARY.md` - 특허별 상세 요약
- `/app/docs/MODULE_MAPPING.md` - 모듈별 구현 가이드
