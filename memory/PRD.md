# GVIC Engine Dashboard - Product Requirements Document

---

## 🏛️ GVIC 사명 (Mission)

```
입출력설계는  친절하게 🤝
본질은       엄격하게 ⚖️
출력시그널은  신속하게 ⚡
```

---

## 💎 GVIC 강점 (Core Strength)

> **"엔진은 하나, 인터페이스는 맞춤"**

| 원칙 | 설명 |
|------|------|
| **엔진 품질 보장** | 검증된 단일 코어 |
| **유연한 적용** | 다양한 고객 요구 수용 |
| **유지보수 효율** | 엔진만 개선하면 전체 적용 |

---

## 🏗️ GVIC 아키텍처 철학

```
┌─────────────────────────────────────────────────────┐
│  [입력 설계]  ──→   GVIC ENGINE   ──→  [출력 설계]  │
│   (고객별        (유형화/분류/패턴)      (고객별     │
│    커스터마이징)     ❌ 변경 없음        커스터마이징)│
└─────────────────────────────────────────────────────┘
```

- **입력 시그널**: 고객별 협의/설계 (커스터마이징 가능)
- **GVIC 엔진**: 유형화, 분류, 패턴 발견 (고정, 변경 불가)
- **출력 시그널**: 고객별 협의/설계 (커스터마이징 가능)

---

## 프로젝트 개요
Streamlit GVIC Engine 대시보드를 React/FastAPI 기반 풀스택 애플리케이션으로 전환한 프로젝트

## 기술 스택
- **Frontend**: React.js, Shadcn/UI, Recharts, Tailwind CSS
- **Backend**: FastAPI, Python
- **Database**: MongoDB
- **Authentication**: JWT + Emergent Google OAuth
- **PDF Generation**: ReportLab (나눔고딕 폰트)

## 핵심 기능
1. 7개 특허 모듈 통합 처리 파이프라인
2. 사용자 인증 및 RBAC (7개 역할)
3. 외부 데이터 소스 연동
4. URL 기반 리뷰 분석
5. PDF 리포트 생성

## 구현 완료 (2024년 12월)
- [x] 14개 메인 탭 UI 구현
- [x] 특허 로직 백엔드 구현
- [x] MongoDB 데이터 저장
- [x] Google OAuth 인증
- [x] PDF 출력 옵션 UI
- [x] 나눔고딕 폰트 설치
- [x] 로컬 설치용 프로젝트 패키징
- [x] 탭 기능 상세 설명서 작성
- [x] **DataHub 연동 확장**: ComparisonTab에 URL 분석 세션 비교 기능 추가

## 진행 중 이슈 (P0)
1. PDF 다운로드 버튼 클릭 불가
2. PDF 한글 깨짐 (새 분석 필요)
3. React 렌더링 오류 (에러 객체 처리)

## 백로그 (P2-P3)
- 비적합 데이터 판정 로직 수정
- 입출력 어댑터 프레임워크 확장
- 경영관리 모듈 구현

## 테스트 계정
- 최고관리자: admin@gvic.com / password

## 주요 파일
- `/app/frontend/src/components/tabs/` - 14개 탭 컴포넌트
- `/app/frontend/src/components/tabs/ComparisonTab.jsx` - DataHub 연동 비교 탭
- `/app/backend/server.py` - 메인 API 서버
- `/app/backend/core/data_hub.py` - DataHub 통합 데이터 관리
- `/app/backend/adapters/output_adapter.py` - PDF 생성 로직
