# 특허 6: 가중 분배 모델 기반의 다영역 자원 배분 시스템 및 방법

## 개요
- **발명 명칭**: 가중 분배 모델 기반의 다영역 자원 배분 시스템 및 방법 (Weighted Distribution Model-Based Multi-Domain Resource Allocation System and Method)
- **시스템 코드**: 4000
- **핵심 목적**: 수리적으로 정의된 가중 분배 모델에 따라 한정된 자원을 복수의 영역에 배분하고, 실시간 모니터링 및 동적 조정

## 시스템 구성 요소

### 4100: 모델 저장부 (Model Repository)
- **기능**: 가중 분배 모델(WDM) 저장 및 관리
- **저장 내용**:
  - 복수의 영역 정의
  - 각 영역의 기본 배분 비율
  - 최소/최대 배분 비율 (경계 조건)
  - 조정 우선순위
  - 조정 규칙
- **특징**: 복수의 모델 저장 가능, 상황별 모델 선택

### 4200: 배분 연산부 (Allocation Calculator)
- **기능**: 가중 분배 모델에 따라 영역별 배분량 산출
- **연산 방식**:
  ```
  Total_Resource = R
  For each domain i:
      Allocated[i] = R × weight[i]
  Where:
      Σ weight[i] = 1.0
      min_weight[i] ≤ weight[i] ≤ max_weight[i]
  ```

### 4300: 소비 모니터링부 (Consumption Monitor)
- **기능**: 각 영역의 실제 자원 소비량 실시간 모니터링
- **편차 산출**: 배분량과 소비량 간의 편차 계산
- **알림 생성**: 편차가 임계치 초과 시 알림

### 4400: 동적 조정부 (Dynamic Adjuster)
- **기능**: 편차 기반 배분 비율 동적 조정
- **조정 방식**: 경계 조건 내에서 조정 규칙에 따라 수행

### 4500: 분석부 (Analytics Unit)
- **기능**: 배분 이력, 소비 패턴, 조정 이력 기록 및 분석
- **출력**: 효율성 지표, 모델 개선 인사이트

## 핵심 수학식

### [수학식 1] 가중 분배 모델 정의
```
WDM = (D, W, B, C, A)

- D = {d₁, d₂, ..., dₙ} : 영역(Domain) 집합
- W = {w₁, w₂, ..., wₙ} : 기본 가중치(Weight) 벡터, Σwᵢ = 1.0
- B = {(Lᵢ, Uᵢ)} : 경계(Bound) 조건 집합, Lᵢ ≤ wᵢ ≤ Uᵢ
- C : 제약 조건 집합 (합계 조건, 경계 조건 등)
- A : 조정 규칙(Adjustment Rule) 집합
```

### [수학식 2] 경계 조건 기반 배분 연산
```
배분 함수: Alloc(R, W, B) → A

초기 배분:
Aᵢ = R × wᵢ

경계 검증 및 조정:
IF Aᵢ < R × Lᵢ THEN Aᵢ = R × Lᵢ (하한 클램핑)
IF Aᵢ > R × Uᵢ THEN Aᵢ = R × Uᵢ (상한 클램핑)

재정규화 (총합 보정):
A'ᵢ = Aᵢ × (R / Σ Aⱼ)
```

### [수학식 3] 편차 기반 동적 조정 함수
```
편차 산출:
Δᵢ(t) = Consumedᵢ(t) - Allocatedᵢ(t)
Δ_ratio(t) = Δᵢ(t) / Allocatedᵢ(t)

동적 조정 트리거:
IF |Δ_ratioᵢ(t)| > θ_trigger THEN trigger_adjustment(i)

조정량 산출:
δwᵢ = α × sign(Δᵢ) × min(|Δ_ratioᵢ|, δ_max)

파라미터:
- α : 조정 민감도 계수 (기본값 = 0.1)
- θ_trigger : 조정 트리거 임계치 (기본값 = 0.2, 즉 20%)
- δ_max : 1회 최대 조정량 (기본값 = 0.1)
```

### [수학식 4] 우선순위 기반 재배분 알고리즘
```
영역 우선순위: P = {p₁, p₂, ..., pₙ}, pᵢ ∈ ℕ

초과 자원 재배분 (gap < 0):
- 우선순위 낮은 영역부터 순차적으로 감축
- reducible = Aᵢ - R × Lᵢ (감축 가능량)
- reduction = min(reducible, excess)

부족 자원 충당 (gap > 0):
- 우선순위 높은 영역부터 순차적으로 증가
- expandable = R × Uᵢ - Aᵢ (증가 가능량)
- expansion = min(expandable, shortage)
```

### [수학식 5] 시계열 기반 예측 조정
```
지수 이동 평균 (EMA) 예측:
EMA_C(i, t) = β × Cᵢ(t-1) + (1-β) × EMA_C(i, t-1)
β = 2 / (n + 1)  (n: 윈도우 크기)

추세 반영:
trend[i] = 선형 회귀 기울기
IF |trend[i]| > threshold THEN
    predicted_consumption[i] += trend[i] × h  (h: 예측 기간)

예측 기반 가중치:
w_predicted[i] = predicted_consumption[i] / total_predicted

신뢰도 가중 혼합:
W_final[i] = confidence × w_predicted[i] + (1-confidence) × wᵢ
```

### [수학식 6] 공정성 지표 (Fairness Index)
```
Jain's Fairness Index:
F(A) = (Σᵢ Aᵢ)² / (n × Σᵢ Aᵢ²)

범위: 1/n ≤ F ≤ 1.0
- F = 1.0 : 완전 균등 배분
- F = 1/n : 완전 불균등 (한 영역 독점)

가중 공정성 지표 (목표 대비):
F_weighted(A, W) = 1 - Σᵢ |Aᵢ/R - wᵢ| / 2
```

### [수학식 7] 다목적 최적화 배분
```
목적 함수:
minimize: Z = λ₁×Deviation + λ₂×Unfairness + λ₃×Volatility

Deviation = Σᵢ (Aᵢ - Targetᵢ)²    (목표 편차)
Unfairness = 1 - F(A)              (불공정성)
Volatility = Σᵢ |Aᵢ(t) - Aᵢ(t-1)|² (변동성)

제약 조건:
Σᵢ Aᵢ = R
Lᵢ ≤ Aᵢ/R ≤ Uᵢ for all i

λ₁, λ₂, λ₃ : 목적별 가중치 (합 = 1.0)
```

### [수학식 8] 모델 전환 조건
```
모델 선택 함수:
m*(t) = argmax_j Score(mⱼ, Context(t))
Score(mⱼ, c) = Σᵣ wᵣ × match(mⱼ.condition_r, c)

전환 조건 (히스테리시스 적용):
IF Score(m_best) - Score(m_current) > θ_switch
   AND time_since_last_switch > min_interval
THEN switch_model(m_best)

파라미터:
- θ_switch = 0.15 (전환 임계치)
- min_interval = 30분 (최소 전환 간격)
```

## 가중 분배 모델 데이터 구조
```json
{
    "model_id": "UUID",
    "domains": [
        {
            "domain_id": "STRING",
            "domain_name": "STRING",
            "base_weight": 0.5,      // 기본 배분 비율 (0-1)
            "min_weight": 0.3,       // 최소 배분 비율
            "max_weight": 0.7,       // 최대 배분 비율
            "priority": 1            // 조정 우선순위 (낮을수록 높은 우선순위)
        }
    ],
    "constraints": {
        "sum_equals_one": true,      // 배분 비율 합 = 1.0
        "respect_bounds": true       // 경계 조건 준수
    },
    "adjustment_rules": [...]        // 동적 조정 규칙
}
```

## 핵심 알고리즘

### 알고리즘 1: 경계 조건 기반 배분 연산
```python
def allocate(R, WDM):
    # 1. 초기 배분
    A = [R * w for w in WDM.weights]
    
    # 2. 경계 조건 클램핑
    clamped = []
    for i, a in enumerate(A):
        if a < R * WDM.bounds[i].min:
            A[i] = R * WDM.bounds[i].min
            clamped.append((i, 'LOWER'))
        elif a > R * WDM.bounds[i].max:
            A[i] = R * WDM.bounds[i].max
            clamped.append((i, 'UPPER'))
    
    # 3. 총합 보정 (클램핑되지 않은 영역에서 조정)
    if sum(A) != R:
        flexible = [i for i in range(len(A)) if i not in [c[0] for c in clamped]]
        adjustment = (R - sum(A)) / len(flexible) if flexible else 0
        for i in flexible:
            A[i] += adjustment
            A[i] = clamp(A[i], R * WDM.bounds[i].min, R * WDM.bounds[i].max)
    
    return A
```

### 알고리즘 2: 동적 조정 (영합 조정)
```python
def dynamic_adjust(A, consumption, params):
    alpha = params.sensitivity      # 0.1
    theta = params.trigger_threshold  # 0.2
    delta_max = params.max_adjustment  # 0.1
    
    # 편차 계산
    delta_ratios = [(c - a) / a for a, c in zip(A, consumption)]
    
    # 조정 대상 식별
    adjustments = []
    for i, delta_ratio in enumerate(delta_ratios):
        if abs(delta_ratio) > theta:
            direction = 1 if delta_ratio > 0 else -1
            magnitude = min(abs(delta_ratio) * alpha, delta_max)
            adjustments.append((i, direction * magnitude))
    
    # 영합 조정 (Zero-Sum)
    positive_sum = sum(adj for _, adj in adjustments if adj > 0)
    negative_sum = abs(sum(adj for _, adj in adjustments if adj < 0))
    
    if positive_sum > negative_sum:
        scale = negative_sum / positive_sum
        adjustments = [(i, adj * scale if adj > 0 else adj) for i, adj in adjustments]
    else:
        scale = positive_sum / negative_sum
        adjustments = [(i, adj * scale if adj < 0 else adj) for i, adj in adjustments]
    
    # 새 가중치 적용
    new_weights = weights.copy()
    for i, adj in adjustments:
        new_weights[i] = clamp(new_weights[i] + adj, bounds[i].min, bounds[i].max)
    
    return normalize(new_weights)
```

### 알고리즘 3: 우선순위 기반 계단식 재배분
```python
def priority_redistribute(A, R, priorities, bounds):
    gap = R - sum(A)
    
    if gap < 0:  # 초과 - 낮은 우선순위부터 감축
        sorted_domains = sorted(range(len(A)), key=lambda i: priorities[i], reverse=True)
        excess = abs(gap)
        for i in sorted_domains:
            reducible = A[i] - R * bounds[i].min
            if reducible > 0:
                reduction = min(reducible, excess)
                A[i] -= reduction
                excess -= reduction
                if excess <= 0:
                    break
    
    elif gap > 0:  # 부족 - 높은 우선순위부터 증가
        sorted_domains = sorted(range(len(A)), key=lambda i: priorities[i])
        shortage = gap
        for i in sorted_domains:
            expandable = R * bounds[i].max - A[i]
            if expandable > 0:
                expansion = min(expandable, shortage)
                A[i] += expansion
                shortage -= expansion
                if shortage <= 0:
                    break
    
    return A
```

## 실시예

### 1. 기업 예산 배분
| 영역 | 기본 비율 | 최소 | 최대 | 우선순위 |
|------|----------|------|------|----------|
| R&D | 50% | 30% | 70% | 1 |
| 영업/마케팅 | 30% | 15% | 45% | 2 |
| 관리/지원 | 20% | 10% | 35% | 3 |

### 2. 클라우드 컴퓨팅 자원 배분
| 영역 | 기본 비율 | 최소 | 최대 | 우선순위 |
|------|----------|------|------|----------|
| 실시간 처리 | 50% | 40% | 70% | 1 |
| 배치 처리 | 30% | 10% | 40% | 3 |
| 개발/테스트 | 20% | 5% | 30% | 2 |

### 3. 헬스케어 의료자원 배분
| 영역 | 기본 비율 | 최소 | 최대 | 우선순위 |
|------|----------|------|------|----------|
| 응급의료 | 40% | 30% | 60% | 1 |
| 수술/중환자 | 30% | 20% | 45% | 2 |
| 일반입원 | 20% | 10% | 35% | 3 |
| 외래진료 | 10% | 5% | 20% | 4 |

### 4. 물류센터 인력 배분
| 영역 | 기본 비율 | 최소 | 최대 | 우선순위 |
|------|----------|------|------|----------|
| 입고/검수 | 20% | 10% | 35% | 2 |
| 피킹 | 35% | 25% | 50% | 1 |
| 포장 | 25% | 15% | 40% | 3 |
| 출고/상차 | 20% | 10% | 30% | 2 |

## 발명의 효과
1. 수리적 정의를 통한 배분 일관성 및 투명성 확보
2. 동적 조정으로 상황 변화에 유연한 대응
3. 실시간 모니터링으로 배분-소비 괴리 신속 파악
4. 경계 조건으로 과도한 자원 점유/부족 방지
5. 배분 이력 분석으로 모델 효율성 지속 개선

## 산업상 이용 가능성
- 기업 예산 관리
- 클라우드 컴퓨팅 리소스 배분
- 프로젝트 관리
- 인력 배치
- 생산 계획
- 의료 자원 관리
- 물류/배송 자원 관리

## 핵심 개념 (GVIC 연관)
이 특허의 **가중 분배 모델(WDM)**은 GVIC 엔진에서 **Sigma(σ, 분배 비율)**의 수학적 기반을 제공합니다:
- **base_weight** = Sigma 기본값
- **min_weight / max_weight** = Omega(ω, 경계 조건)의 상/하한
- **동적 조정** = Sigma의 실시간 최적화 메커니즘

## 관련 특허
- 특허 1 (수렴 제어): 동적 조정의 수렴 조건 정의
- 특허 4 (재귀적 모듈화): 복수 모델 계층적 관리
- 특허 5 (비적합 데이터): 배분 실패 데이터의 자산화
