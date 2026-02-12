# GVIC 특허 요약 - 빠른 참조 가이드

## 특허 간 관계도
```
┌─────────────────────────────────────────────────────────────────┐
│                    GVIC 통합 엔진                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [입력] ──▶ [특허2: 신호 전처리] ──▶ [특허3: 신호 자산화]        │
│                     │                        │                  │
│                     ▼                        ▼                  │
│            [특허4: 파이프라인]        [가치 산출]                │
│                     │                        │                  │
│                     ▼                        ▼                  │
│            [특허1: 수렴 제어] ◀──── [가치 분배]                  │
│                     │                                           │
│                     ▼                                           │
│            [특허6-J: 다중 도메인 통합] ──▶ [출력]                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 핵심 수학식 모음

### 특허 1: 전역 수렴 제어
```
경계 조건: Ω = { Lᵢ ≤ Pᵢ ≤ Uᵢ, ΣPᵢ = 1.0 }
위반 판정: V(P) = Σ max(0, Lᵢ - Pᵢ) + Σ max(0, Pᵢ - Uᵢ) + |ΣPᵢ - 1.0|
수렴 변환: V_conv = α·V_in + (1-α)·R
수렴 강도: α = max(0, 1 - β·V(P))
균형 지수: B = H(P) / H_max = -Σ Pᵢ·log(Pᵢ) / log(n)
```

### 특허 2: 다단계 신호 전처리
```
정합성 지수: S_idx = (V · Σ) / (|V| × |Σ|)  (코사인 유사도)
판별: S_idx ≥ τ → 정합 → 정제처리
      S_idx < τ → 비정합 → 재귀적 재분류
```

### 특허 3: 신호 자산화
```
품질 점수: Q(s) = w_c×C + w_a×A + w_f×F
관련성: R(s,d) = cos(V_s, V_d)
희소성: Sc(s) = 1 - (n_similar / N_total)
시의성: T(s) = σ(α × (t_peak - |t_s - t_event|))
종합 가치: V_total = Σ(wᵢ × Fᵢ)^γ
시너지: V_synergy = α × Σᵢⱼ (1 - sim(sᵢ, sⱼ)) × min(V(sᵢ), V(sⱼ))
유효기간: T_valid = T_base × (1 + β × Sc) × F
```

### 특허 4: 재귀적 모듈화 파이프라인
```
문법: Pipeline = Module | Seq(...) | Par(...) | Cond(...) | Loop(...)
복잡도: C(Seq) = Σ C(Pᵢ), C(Par) = max C(Pᵢ)
호환성: coverage = |required ∩ provided| / |required|
```

### 특허 6-J: 다중 도메인 통합
```
아키텍처: Hub-and-Spoke (O(n²) → O(n))
변환: Source → CDM → Target
유사도: sim(field1, field2) = Jaccard similarity
```

## 데이터 구조 요약

### Signal Object (특허 3)
```json
{
  "signal_id": "UUID",
  "source_type": "text|sensor|behavior|event",
  "timestamp": "ISO8601",
  "payload": "NORMALIZED_VECTOR",
  "metadata": { "quality_score": 0.85 },
  "context": { "domain": "ecommerce", "tags": [] }
}
```

### Asset Object (특허 3)
```json
{
  "asset_id": "UUID",
  "source_signals": ["signal_ids"],
  "value_vector": [0.5, 0.3, 0.2],
  "total_value": 100.0,
  "confidence": 0.92,
  "validity_period": "7d"
}
```

### Common Data Model (특허 6-J)
```json
{
  "message_id": "UUID",
  "source_domain": "erp",
  "target_domains": ["crm", "scm"],
  "payload": { "entities": [], "original_data": {} },
  "metadata": { "transformation_timestamp": "ISO8601" }
}
```

## 복구/장애 처리

### 특허 1: 3단계 점진적 복구
```
1단계 (소프트): P = 0.7×P_node + 0.3×P_sync (5초 대기)
2단계 (강제): P = P_sync (10초 대기)
3단계 (초기화): P = R (기본 수렴 비율)
```

### 특허 4: 체크포인트 복구
```
1. 최근 체크포인트 탐색
2. 상태 복원
3. 나머지 모듈 재실행
```

## 적용 도메인
- 이커머스: 고객 피드백, 주문 처리
- 스마트 팩토리: 설비 모니터링, 예지정비
- 헬스케어: 환자 데이터, 진료 프로세스
- 물류: 배송 최적화, 재고 관리
- 금융: 거래 처리, 리스크 관리
