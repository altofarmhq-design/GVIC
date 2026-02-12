# GVIC Engine - 7개 특허 모듈 통합 시스템

## 시스템 요구사항
- Python 3.9+
- Node.js 18+
- MongoDB 4.4+

## 빠른 설치
```bash
chmod +x install.sh
./install.sh
```

## 수동 설치

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Frontend
```bash
cd frontend
yarn install
cp .env.example .env
```

## 실행
1. MongoDB: `mongod`
2. Backend: `cd backend && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload`
3. Frontend: `cd frontend && yarn start`
4. 접속: http://localhost:3000

## 기본 계정
- 이메일: admin@gvic.com
- 비밀번호: password

## 주요 기능
- 특허 기반 데이터 처리 엔진 (P0-P3)
- 외부 데이터 소스 연동 (P4)
- 사용자 인증 및 7단계 역할 관리 (P5)

## 환경 설정

### backend/.env
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="gvic_engine"
CORS_ORIGINS="http://localhost:3000"
JWT_SECRET_KEY="your-secret-key"
```

### frontend/.env
```
REACT_APP_BACKEND_URL=http://localhost:8001
```
