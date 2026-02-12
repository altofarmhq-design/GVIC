# GVIC Engine - 7개 특허 모듈 통합 시스템

## 개요

GVIC Engine은 7개의 핵심 특허 기술을 통합한 데이터 처리 및 분석 시스템입니다. React 프론트엔드와 FastAPI 백엔드, MongoDB 데이터베이스로 구성된 풀스택 애플리케이션입니다.

## 시스템 요구사항

- **Python**: 3.9 이상
- **Node.js**: 18 이상
- **MongoDB**: 4.4 이상
- **운영체제**: Windows, macOS, Linux

## 빠른 시작

### 1. 설치 스크립트 실행

```bash
# 실행 권한 부여
chmod +x install.sh

# 설치 실행
./install.sh
```

### 2. 수동 설치

#### Backend 설치

```bash
cd backend

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 설정 변경
```

#### Frontend 설치

```bash
cd frontend

# 의존성 설치
yarn install  # 또는 npm install

# 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 설정 변경
```

## 실행 방법

### 1. MongoDB 시작

```bash
# MongoDB 서비스 시작 (시스템에 따라 다름)
mongod --dbpath /path/to/data/db

# 또는 서비스로 시작
sudo systemctl start mongod
```

### 2. Backend 서버 시작

```bash
cd backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Frontend 서버 시작

```bash
cd frontend
yarn start  # 또는 npm start
```

### 4. 브라우저에서 접속

```
http://localhost:3000
```

## 기본 계정

| 역할 | 이메일 | 비밀번호 |
|------|--------|----------|
| 최고관리자 | admin@gvic.com | password |

## 환경 설정

### Backend (.env)

```env
# MongoDB 연결 설정
MONGO_URL="mongodb://localhost:27017"
DB_NAME="gvic_engine"

# CORS 설정
CORS_ORIGINS="http://localhost:3000"

# JWT 설정 (프로덕션에서 반드시 변경!)
JWT_SECRET_KEY="your-super-secret-key-change-this"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth 설정 (선택사항)
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
```

### Frontend (.env)

```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 주요 기능

### 특허 기반 핵심 모듈 (P0-P3)

1. **수렴 처리 엔진 (Patent 1)**: 데이터 수렴 및 융합 처리
2. **신호 처리 모듈 (Patent 2)**: 신호 분석 및 필터링
3. **파이프라인 처리 (Patent 3)**: 데이터 파이프라인 관리
4. **비적합 데이터 처리 (Patent 4)**: 이상 데이터 검출 및 처리
5. **분포 분석 (Patent 5)**: 데이터 분포 통계 분석
6. **인터페이스 통합 (Patent 6)**: 다중 인터페이스 통합

### 외부 데이터 연동 (P4)

- 외부 API 데이터 소스 관리
- 데이터 자동 수집 및 폴링
- 수집 데이터 조회 및 분석

### 사용자 인증 및 권한 관리 (P5)

- JWT 기반 로컬 인증
- Google OAuth 소셜 로그인
- 7단계 역할 기반 접근 제어 (RBAC)
  - 내부: 최고관리자, 관리자, 오퍼레이터, 방문객
  - 외부: 외부관리자, 외부오퍼레이터, 외부방문객
- 신규 가입 승인 워크플로우

## 디렉토리 구조

```
gvic-engine/
├── backend/
│   ├── core/                 # 특허 기반 핵심 로직
│   │   ├── engine.py         # 메인 엔진
│   │   ├── patent1_convergence.py
│   │   ├── patent2_signal.py
│   │   ├── patent3_pipeline.py
│   │   ├── patent4_nonconform.py
│   │   ├── patent5_distribution.py
│   │   └── patent6_interface.py
│   ├── utils/                # 유틸리티
│   ├── config/               # 설정 파일
│   ├── data/                 # 데이터 저장
│   ├── auth.py               # 인증 모듈
│   ├── server.py             # FastAPI 메인
│   └── requirements.txt      # Python 의존성
├── frontend/
│   ├── src/
│   │   ├── components/       # React 컴포넌트
│   │   │   ├── tabs/         # 탭 컴포넌트들
│   │   │   └── ui/           # UI 컴포넌트 (shadcn)
│   │   ├── contexts/         # React Context
│   │   ├── pages/            # 페이지 컴포넌트
│   │   ├── lib/              # 유틸리티 및 API
│   │   ├── App.js            # 메인 앱
│   │   └── index.js          # 엔트리 포인트
│   └── package.json          # Node 의존성
├── install.sh                # 설치 스크립트
└── README.md                 # 이 문서
```

## API 엔드포인트

### 인증 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| POST | /api/auth/register | 회원가입 |
| POST | /api/auth/login | 로그인 |
| GET | /api/auth/me | 현재 사용자 정보 |
| GET | /api/auth/users | 사용자 목록 (관리자) |
| PUT | /api/auth/users/{id}/role | 역할 변경 (관리자) |
| POST | /api/auth/users/{id}/approve | 가입 승인 (관리자) |
| POST | /api/auth/users/{id}/reject | 가입 거부 (관리자) |

### 데이터 소스 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | /api/datasources | 데이터 소스 목록 |
| POST | /api/datasources | 데이터 소스 생성 |
| PUT | /api/datasources/{id} | 데이터 소스 수정 |
| DELETE | /api/datasources/{id} | 데이터 소스 삭제 |
| POST | /api/datasources/{id}/collect | 데이터 수집 |
| GET | /api/datasources/collected | 수집된 데이터 조회 |

### 엔진 API

| 메서드 | 엔드포인트 | 설명 |
|--------|-----------|------|
| GET | /api/status | 엔진 상태 |
| POST | /api/process | 데이터 처리 |
| GET | /api/models | 모델 목록 |
| POST | /api/predict | 예측 실행 |

## 문제 해결

### MongoDB 연결 오류

```bash
# MongoDB 서비스 상태 확인
sudo systemctl status mongod

# MongoDB 로그 확인
sudo tail -f /var/log/mongodb/mongod.log
```

### Backend 시작 오류

```bash
# 가상환경 활성화 확인
which python  # venv 경로가 나와야 함

# 의존성 재설치
pip install -r requirements.txt --force-reinstall
```

### Frontend 시작 오류

```bash
# node_modules 삭제 후 재설치
rm -rf node_modules
yarn install
```

## 프로덕션 배포

### 보안 설정

1. `.env` 파일의 `JWT_SECRET_KEY`를 강력한 랜덤 문자열로 변경
2. CORS 설정을 실제 도메인으로 제한
3. HTTPS 적용

### 프로세스 관리 (PM2)

```bash
# Backend
pm2 start "uvicorn server:app --host 0.0.0.0 --port 8001" --name gvic-backend

# Frontend (빌드 후)
cd frontend && yarn build
pm2 serve build 3000 --name gvic-frontend
```

## 라이선스

이 프로젝트는 내부 사용 목적으로 개발되었습니다.

## 지원

문의사항이 있으시면 관리자에게 연락해주세요.
