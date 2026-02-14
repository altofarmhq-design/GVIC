# GVIC Engine 실행 스크립트

Windows 환경에서 GVIC Engine을 쉽게 실행하기 위한 배치 파일 모음입니다.

## 📁 파일 목록

| 파일명 | 설명 |
|--------|------|
| `start_all.bat` | 백엔드와 프론트엔드 서버를 한 번에 시작 |
| `start_backend.bat` | 백엔드 서버만 시작 |
| `start_frontend.bat` | 프론트엔드 서버만 시작 |
| `stop_all.bat` | 모든 서버 프로세스 종료 |
| `check_status.bat` | 시스템 상태 확인 |
| `install_dependencies.bat` | 의존성 패키지 설치 |

## 🚀 사용 방법

### 최초 설치 시
1. `install_dependencies.bat` 실행
2. MongoDB가 실행 중인지 확인
3. `start_all.bat` 실행

### 일반 사용 시
1. MongoDB 실행 확인
2. `start_all.bat` 더블 클릭

### 서버 종료
- `stop_all.bat` 실행
- 또는 각 서버 창에서 `Ctrl+C`

## ⚙️ 설정 변경

배치 파일 내 `PROJECT_ROOT` 변수를 수정하여 프로젝트 경로를 변경할 수 있습니다.

```batch
:: 기본값
set PROJECT_ROOT=C:\GVIC

:: 예시: 다른 경로로 변경
set PROJECT_ROOT=D:\Projects\GVIC
```

## 🔧 사전 요구사항

- **Python 3.10+**: https://python.org
- **Node.js 18+**: https://nodejs.org
- **MongoDB**: https://mongodb.com
- **Yarn**: `npm install -g yarn`

## ❓ 문제 해결

### MongoDB 연결 오류
```
MongoDB를 먼저 시작해주세요.
```
→ MongoDB Compass를 실행하거나, 관리자 권한으로 `net start MongoDB` 실행

### Python 가상환경 오류
```
[경고] 가상환경이 없습니다.
```
→ `install_dependencies.bat`를 먼저 실행하여 가상환경 생성

### 포트 충돌
```
Address already in use
```
→ `stop_all.bat`으로 기존 프로세스 종료 후 재시작
