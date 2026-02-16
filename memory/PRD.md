# GVIC 시그널 온톨로지 자산화 플랫폼 - PRD

## 1. 제품 개요

### 1.1 제품명
**GVIC (Global Value Integration & Convergence)**

### 1.2 정의
> "존재하는 시그널들의 유형, 감성, 관계를 체계적으로 정의하고, 이를 분석·자산화하여 의사결정에 활용하는 통합 시스템"

### 1.3 기반
- **12개 특허** 기반 통합 시스템
- **결이론 (5:3:2)** 철학 적용

---

## 2. 핵심 철학: 결이론 (Gyeoliron)

### 2.1 5:3:2 비율
| 영역 | 비율 | 의미 |
|------|------|------|
| 공공 (Public) | 50% | 사회적 가치 |
| 생산 (Production) | 30% | 생산적 가치 |
| 개인 (Individual) | 20% | 개인적 가치 |

### 2.2 수학적 표현
```
Σ = [0.5, 0.3, 0.2]^T
```

---

## 3. 시스템 아키텍처

### 3.1 노드 구조
```
CORE (H) ─┬─ GATE (A)      : 데이터 인지
          ├─ SHIELD (E)    : 독소 검역
          ├─ REFINE (G)    : 가치 정제
          ├─ CALC (B)      : 가치 산출
          ├─ EXEC (C)      : 자원 배분
          ├─ FIELD (F)     : 물리 실행
          ├─ LEDGER (D)    : 궤적 저장
          └─ INTEGRITY (I) : 무결성 증명
```

### 3.2 특허↔모듈 매핑
| 특허 | 노드 | 백엔드 모듈 | 상태 |
|------|------|------------|------|
| H | CORE | convergence_controller.py | 🔴 |
| A | GATE | signal_detector.py | 🟡 |
| E | SHIELD | quarantine.py | 🔴 |
| G | REFINE | value_refiner.py | 🔴 |
| B | CALC | value_calculator.py | 🔴 |
| C | EXEC | resource_executor.py | 🔴 |
| D | LEDGER | trajectory_storage.py | 🔴 |
| I | INTEGRITY | integrity_proof.py | 🔴 |
| F | FIELD | physical_executor.py | 🔴 |
| J | PLATFORM | external_api.py | 🔴 |
| LL | INTELLIGENCE | contribution_quantifier.py | 🔴 |

---

## 4. 구현 현황

### 4.1 완료된 작업 (2026-02-15)
- ✅ React + FastAPI 기본 구조
- ✅ 사용자 인증 (JWT)
- ✅ 대시보드 실시간 데이터
- ✅ 시그널분석 탭 (AI 비활성화 상태)
- ✅ 특허 문서 체계 구축

### 4.2 현재 탭 구성 (7개)
1. 대시보드
2. 시그널분석
3. 비교
4. 예측
5. 데이터
6. 알림
7. 설정

---

## 5. 로드맵

### Phase 1: 핵심 모듈 (MVP)
- [ ] convergence_controller.py (특허 H)
- [ ] value_calculator.py (특허 B)
- [ ] integrity_proof.py (특허 I)
- [x] signal_detector.py (특허 A) - 부분 구현

### Phase 2: 품질 강화
- [ ] quarantine.py (특허 E)
- [ ] value_refiner.py (특허 G)
- [ ] trajectory_storage.py (특허 D)

### Phase 3: 확장
- [ ] resource_executor.py (특허 C)
- [ ] physical_executor.py (특허 F)
- [ ] external_api.py (특허 J)
- [ ] contribution_quantifier.py (특허 LL)

---

## 6. 백로그

### P0 (필수)
- [ ] 특허 H: CORE 모듈 구현
- [ ] 특허 B: 가치 산출 모듈 구현
- [ ] AI 분석 기능 활성화 (OpenAI 크레딧)

### P1 (중요)
- [ ] 특허 E: 독소 검역 모듈 구현
- [ ] 특허 G: 가치 정제 모듈 구현
- [ ] PDF 보고서 기능 (로컬 환경)

### P2 (추후)
- [ ] 배치 분석 (Excel/CSV 업로드)
- [ ] 트렌드 분석 (시계열)
- [ ] 외부 API 연동

---

## 7. 기술 스택

### 백엔드
- Python 3.9+
- FastAPI
- MongoDB (Motor)
- bcrypt, python-jose

### 프론트엔드
- React 18
- Tailwind CSS
- Shadcn/UI
- Recharts

### AI
- OpenAI GPT-4o-mini (비활성화 상태)

---

## 8. 문서 체계

```
/app/
├── patents/           # 특허 원문
├── docs/
│   ├── GVIC_ARCHITECTURE.md
│   ├── PATENT_SUMMARY.md
│   └── MODULE_MAPPING.md
└── memory/
    └── PRD.md         # 본 문서
```

---

## 9. 버전 이력

| 버전 | 날짜 | 변경 사항 |
|------|------|----------|
| 1.0.0 | 2026-02-15 | 특허 기반 PRD 재작성 |

---

## 10. 참고

- 특허 원문: `/app/patents/`
- 아키텍처: `/app/docs/GVIC_ARCHITECTURE.md`
- 모듈 매핑: `/app/docs/MODULE_MAPPING.md`
