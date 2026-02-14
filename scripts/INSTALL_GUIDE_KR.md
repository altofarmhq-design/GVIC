# GVIC 엔진 대시보드 - 로컬 설치 가이드

## 📋 사전 요구사항

### 필수 소프트웨어
1. **Python 3.11+** - https://www.python.org/downloads/
2. **Node.js 18+** - https://nodejs.org/
3. **MongoDB 7.0+** - https://www.mongodb.com/try/download/community
4. **Git** - https://git-scm.com/downloads

### 환경 변수 확인
설치 후 명령 프롬프트에서 확인:
```batch
python --version
node --version
npm --version
mongod --version
```

---

## 🚀 빠른 설치 (자동)

### 1단계: 프로젝트 폴더로 이동
```batch
cd C:\your-project-folder
```

### 2단계: 설치 스크립트 실행
```batch
scripts\install_full.bat
```

### 3단계: 앱 시작
```batch
scripts\start_all.bat
```

### 4단계: 브라우저에서 접속
```
http://localhost:3000
```

---

## 📁 수동 설치

### 백엔드 설치
```batch
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 프론트엔드 설치
```batch
cd frontend
npm install
```

### MongoDB 시작
```batch
mongod --dbpath C:\data\db
```

---

## ⚙️ 환경 설정

### backend/.env
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=gvic_engine
EMERGENT_LLM_KEY=your_key_here
```

### frontend/.env
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 🔧 스크립트 설명

| 스크립트 | 설명 |
|---------|------|
| `install_full.bat` | 전체 설치 (의존성 + 환경설정) |
| `start_all.bat` | MongoDB + 백엔드 + 프론트엔드 시작 |
| `stop_all.bat` | 모든 서비스 종료 |
| `check_status.bat` | 서비스 상태 확인 |
| `update_from_preview.bat` | Preview 서버에서 최신 코드 동기화 |

---

## 🔐 기본 계정

| 역할 | 이메일 | 비밀번호 |
|-----|--------|---------|
| 슈퍼관리자 | admin@gvic.com | password |

---

## ❗ 문제 해결

### MongoDB 연결 실패
```batch
# MongoDB 서비스 확인
net start MongoDB

# 수동 시작
mongod --dbpath "C:\data\db"
```

### 백엔드 포트 충돌
```batch
# 8001 포트 사용 중인 프로세스 확인
netstat -ano | findstr :8001

# 프로세스 종료
taskkill /PID <PID번호> /F
```

### 프론트엔드 빌드 오류
```batch
cd frontend
rd /s /q node_modules
npm cache clean --force
npm install
```

---

## 📅 최근 업데이트 (2026-02-14)

### 변경된 주요 파일
- `frontend/src/App.js` - 탭 통합 (시그널추적 → 시그널분석)
- `frontend/src/components/tabs/GVICShowcaseTab.jsx` - 자산화창고 UI
- `backend/server.py` - 자산화창고 API, 자연어 검색

### 새 기능
- AI 기반 시그널 분석
- 자산화창고 (탑 10 유사 모듈)
- 자연어 검색
- 접근 제어 (공개/비공개 자산)
