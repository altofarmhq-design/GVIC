# GVIC Engine Dashboard - Product Requirements Document

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

## 진행 중 이슈 (P0)
1. PDF 다운로드 버튼 클릭 불가
2. PDF 한글 깨짐 (새 분석 필요)
3. React 렌더링 오류 (에러 객체 처리)

## 백로그 (P2-P3)
- DataHub 연동 확장
- 비적합 데이터 판정 로직 수정
- 입출력 어댑터 프레임워크 확장
- 경영관리 모듈 구현

## 테스트 계정
- 최고관리자: admin@gvic.com / password

## 주요 파일
- `/app/frontend/src/components/tabs/` - 14개 탭 컴포넌트
- `/app/backend/server.py` - 메인 API 서버
- `/app/backend/adapters/output_adapter.py` - PDF 생성 로직
