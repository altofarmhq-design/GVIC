# GVIC 로컬 환경 설치 가이드

## 1. 사전 요구사항

### Node.js 설치 (v18 이상)
- https://nodejs.org/ 에서 LTS 버전 다운로드

### Python 설치 (3.9 이상)
- https://www.python.org/downloads/ 에서 다운로드
- 설치 시 "Add Python to PATH" 체크!

### MongoDB 설치
- https://www.mongodb.com/try/download/community 에서 다운로드
- MongoDB Compass도 함께 설치하면 데이터 확인 편리

---

## 2. 프로젝트 루트

```
D:\GVIC\
├── backend\
├── frontend\
├── data\db\     (MongoDB 데이터)
├── scripts\
└── docs\
```

---

## 3. 백엔드 설정

```cmd
cd D:\GVIC\backend

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate

# emergentintegrations 설치 (필수)
pip install emergentintegrations --extra-index-url https://d33sy5i8bnduwe.cloudfront.net/simple/

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (.env.example 복사)
copy .env.example .env

# .env 파일 열어서 EMERGENT_LLM_KEY 입력
notepad .env
```

### .env 파일 수정
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=gvic_local
JWT_SECRET_KEY=your-secret-key
EMERGENT_LLM_KEY=sk-emergent-실제키입력
```

### 백엔드 실행
```cmd
python -m uvicorn server:app --reload --host 0.0.0.0 --port 8001
```

---

## 4. 프론트엔드 설정

새 명령 프롬프트 창 열기:

```cmd
cd D:\GVIC\frontend

# 패키지 설치
npm install

# 프론트엔드 실행
npm start
```

---

## 5. 첫 번째 관리자 계정 생성

백엔드가 실행 중인 상태에서 새 명령 프롬프트:

```cmd
curl -X POST http://localhost:8001/api/auth/register -H "Content-Type: application/json" -d "{\"email\":\"admin@gvic.com\",\"password\":\"password\",\"password_confirm\":\"password\",\"name\":\"Admin\"}"
```

### 관리자 승인 처리 (MongoDB Compass 사용)
1. MongoDB Compass 실행
2. `mongodb://localhost:27017` 연결
3. `gvic_local` → `users` 컬렉션
4. 방금 생성된 사용자의 `status`를 `"pending"` → `"approved"` 로 변경
5. `role`을 `"visitor"` → `"admin"` 으로 변경

---

## 6. 접속

브라우저에서 http://localhost:3000 접속

---

## 문제 해결

### bcrypt 오류 발생 시
```cmd
pip uninstall bcrypt
pip install bcrypt==4.0.1
```

### MongoDB 연결 오류
- MongoDB 서비스가 실행 중인지 확인
- Windows: 서비스 앱에서 "MongoDB Server" 확인
- 수동 시작: `mongod --dbpath "D:\GVIC\data\db"`

### CORS 오류
- 백엔드와 프론트엔드가 모두 실행 중인지 확인
