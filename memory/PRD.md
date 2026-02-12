# GVIC Engine - Product Requirements Document

## 프로젝트 개요
- **프로젝트명**: GVIC Engine (Global Value Integration & Control Engine)
- **목적**: 7개 특허 모듈을 통합한 가치 분배 및 제어 시스템
- **기술 스택**: React + FastAPI + MongoDB

## 아키텍처
```
Frontend (React + Tailwind)
├── 대시보드 탭 (메트릭, 차트)
├── 처리 탭 (GVIC 엔진 실행)
├── 통합 탭 (다중 도메인 통합)
├── 데이터 탭 (IO 테스트, 로그)
├── 알림 탭 (헬스체크, 통계)
└── 설정 탭 (Σ/Ω 설정, 모듈 상태)

Backend (FastAPI + MongoDB)
├── core/ (7개 특허 모듈)
│   ├── patent1_convergence.py (전역 수렴 제어)
│   ├── patent2_signal.py (다단계 신호 전처리)
│   ├── patent3_pipeline.py (신호 자산화)
│   ├── patent4_nonconform.py (비적합 처리)
│   ├── patent5_distribution.py (가중 분배)
│   ├── patent6_interface.py (도메인 인터페이스)
│   ├── multi_domain_integration.py (다중 도메인 통합)
│   ├── engine.py (통합 엔진)
│   └── control.py (내부 통제)
└── utils/ (설정, 로깅)
```

## 구현 상태 (2026-02-12)

### 완료
- ✅ React 프론트엔드 (6개 탭, 다크 테마)
- ✅ FastAPI 백엔드 (30+ API 엔드포인트)
- ✅ 특허 6-J: 다중 도메인 통합 인터페이스 시스템
- ✅ 분배 비율 파이차트, 균형 게이지차트
- ✅ GVIC 엔진 처리 및 결과 시각화
- ✅ MongoDB 연동

### 진행 중
- 🔄 특허 1~6 상세 사양 기반 재구현 예정

## 특허 문서 분석 현황
- ✅ 특허 1: 전역 수렴 제어 시스템 (분석 완료)
- ✅ 특허 2: 다단계 신호 전처리 시스템 (분석 완료)
- ✅ 특허 3: 신호 자산화 통합 플랫폼 (분석 완료)
- ⏳ 특허 4: 대기 중
- ⏳ 특허 5: 대기 중
- ⏳ 특허 6: 대기 중
- ✅ 특허 6-J: 다중 도메인 통합 (구현 완료)

## 백로그
- P0: 나머지 특허(4,5,6) 분석 및 구현
- P1: 특허 1~3 상세 사양 기반 재구현
- P2: 실시간 WebSocket 데이터 스트리밍
- P3: 데이터 플로우 시각화
