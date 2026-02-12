# 특허 3: 신호 자산화 통합 플랫폼

## 기본 정보
- **영문명**: Signal Assetization Integrated Platform and Operating Method Thereof
- **기술분야**: 이종 신호를 통합 처리하여 정량화된 가치 자산으로 생성

## 시스템 구성요소

| 구성요소 | 부호 | 설명 |
|---------|------|------|
| 신호 수집 계층 | 1100 | 이종 신호 통합 수집 (텍스트, 센서, 행동 로그 등) |
| 신호 정규화 엔진 | 1200 | Signal Object로 표준화 변환 |
| 가치 산출 엔진 | 1300 | 가치 정량화 → Asset Object 생성 |
| 출력 어댑터 계층 | 1400 | 다양한 형태로 변환 출력 |
| 무결성 관리부 | 1500 | 처리 이력 및 무결성 검증 |

## 데이터 구조

### Signal Object (신호 객체)
```json
{
    "signal_id": "UUID",
    "source_type": "ENUM (text/sensor/behavior/event)",
    "timestamp": "ISO8601",
    "payload": "NORMALIZED_VECTOR",
    "metadata": {
        "original_format": "STRING",
        "preprocessing_applied": ["LIST"],
        "quality_score": "FLOAT (0~1)"
    },
    "context": {
        "domain": "STRING",
        "relevance_tags": ["LIST"]
    }
}
```

### Asset Object (자산 객체)
```json
{
    "asset_id": "UUID",
    "source_signals": ["signal_id LIST"],
    "value_vector": ["V₁", "V₂", "V₃"],
    "total_value": "FLOAT",
    "confidence": "FLOAT (0~1)",
    "creation_timestamp": "ISO8601",
    "validity_period": "DURATION"
}
```

## 핵심 수학식

### [수학식 1] 신호 품질 점수 Q(s)
```
Q(s) = w_c × C(s) + w_a × A(s) + w_f × F(s)

여기서:
- C(s): 완전성 = 채워진 필수 필드 / 전체 필수 필드
- A(s): 정확성 = 유효 범위 내 값 / 전체 값
- F(s): 신선도 = exp(-λ × Δt)
- w_c, w_a, w_f: 가중치 (합 = 1.0)

기본값: w = [0.3, 0.4, 0.3]
```

### [수학식 2] 관련성 점수 R(s, d)
```
R(s, d) = cos(V_s, V_d) = (V_s · V_d) / (||V_s|| × ||V_d||)

여기서:
- V_s: 신호의 특징 벡터 (TF-IDF, 임베딩 등)
- V_d: 대상 도메인의 특징 벡터
- 결과: -1 ~ 1 (정규화 후 0~1)
```

### [수학식 3] 희소성 점수 Sc(s)
```
Sc(s) = 1 - (n_similar / N_total)

여기서:
- n_similar: 유사 신호 수 (유사도 임계치 이상)
- N_total: 전체 신호 풀 크기
- 결과: 0 ~ 1 (1에 가까울수록 희소)
```

### [수학식 4] 시의성 점수 T(s)
```
T(s) = σ(α × (t_peak - |t_s - t_event|))

여기서:
- σ(x) = 1 / (1 + exp(-x)) (시그모이드 함수)
- t_s: 신호 수집 시점
- t_event: 관련 이벤트 시점
- t_peak: 최적 시점 윈도우
- α: 민감도 파라미터 (기본 0.1)
```

### [수학식 5] 종합 가치 산출
```
V_total(s) = Σᵢ (wᵢ × Fᵢ(s))^γ

여기서:
- F₁ = Q(s): 품질 점수
- F₂ = R(s, d): 관련성 점수
- F₃ = Sc(s): 희소성 점수
- F₄ = T(s): 시의성 점수
- wᵢ: 가중치 (기본값 [0.25, 0.30, 0.20, 0.25])
- γ: 비선형 조정 계수 (기본값 1.0)
```

### [수학식 6] 영역별 가치 분배
```
V_domain[i] = V_total × D[i] × R(s, domain[i])

여기서:
- D[i]: 영역 i의 기본 배분 비율
- Σ V_domain[i] = V_total (정규화)
```

### [수학식 7] 가치 산출 신뢰도
```
Conf(s) = min(Q(s), σ_data, σ_model)

여기서:
- σ_data = 1 - (std(features) / max_std)
- σ_model = 일치하는 모델 수 / 전체 모델 수
```

### [수학식 8] 자산 유효 기간
```
T_valid(s) = T_base × (1 + β × Sc(s)) × F(s)

여기서:
- T_base: 기본 유효 기간 (도메인별 설정)
- β: 희소성 가중 계수 (기본값 0.5)
```

### [수학식 9] 복수 신호 시너지 가치
```
V_agg = f_agg(V(s₁), V(s₂), ...) + V_synergy

V_synergy = α × Σᵢⱼ (1 - sim(sᵢ, sⱼ)) × min(V(sᵢ), V(sⱼ))

여기서:
- f_agg: MAX, AVG, SUM, 또는 가중평균
- sim(sᵢ, sⱼ): 신호 간 유사도 (다를수록 시너지 높음)
- α: 시너지 계수 (기본값 0.2)
```

## 알고리즘

### 알고리즘 1: 신호 품질 평가
```python
def quality_score(s):
    C = count(non_null_required) / count(required)
    A = count(valid_values) / count(all_values)
    F = exp(-λ * delta_t)
    Q = 0.3 * C + 0.4 * A + 0.3 * F
    return Q
```

### 알고리즘 2: 종합 가치 산출
```python
def calculate_value(s):
    Q = quality_score(s)
    R = relevance_score(s, domain)
    Sc = scarcity_score(s)
    T = timeliness_score(s)
    
    w = [0.25, 0.30, 0.20, 0.25]
    V_total = sum(w[i] * F[i] for i, F in enumerate([Q, R, Sc, T]))
    
    return V_total
```

### 알고리즘 3: 가치 재평가 (시간 경과)
```python
def reevaluate_value(asset, t_now):
    delta_t = t_now - asset.creation_timestamp
    decay_factor = exp(-λ_asset * delta_t)
    V_updated = asset.total_value * decay_factor
    
    if t_now > asset.validity_period:
        mark_as_expired(asset)
        V_updated = 0
    
    return V_updated
```

## 적용 분야
- 이커머스 고객 피드백 자산화
- 스마트 팩토리 설비 데이터 자산화
- 헬스케어 환자 데이터 자산화
- 물류 배송 데이터 자산화
