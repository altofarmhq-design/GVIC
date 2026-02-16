# GVIC Seller Intelligence Hub - 로컬 설치 가이드

## 📋 시스템 요구사항

| 항목 | 최소 버전 | 권장 버전 |
|------|----------|----------|
| **Python** | 3.10+ | 3.11+ |
| **Node.js** | 18+ | 20+ |
| **MongoDB** | 6.0+ | 7.0+ |
| **RAM** | 4GB | 8GB+ |
| **디스크** | 2GB | 5GB+ |

---

## 🚀 빠른 설치 (Windows)

### 1. 프로젝트 다운로드
```
D:\gvic 폴더에 프로젝트 파일 복사
```

### 2. 설치 실행
```batch
D:\gvic\install.bat
```

### 3. 서비스 시작
```batch
D:\gvic\start_all.bat
```

### 4. 브라우저 접속
```
http://localhost:3000
```

---

## 📁 프로젝트 구조

```
D:\gvic\
├── backend/                 # FastAPI 백엔드
│   ├── saas/               # SaaS 핵심 모듈
│   │   ├── shop_manager.py      # 쇼핑몰/제품 관리
│   │   ├── product_insights.py  # 4대 인사이트 분석
│   │   ├── payment_service.py   # 결제 서비스
│   │   └── unified_payment.py   # 통합 결제 (6종)
│   ├── server.py           # 메인 서버
│   ├── auth.py             # 인증
│   ├── requirements.txt    # Python 의존성
│   └── .env               # 환경변수 (생성됨)
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/saas/    # SaaS 대시보드
│   │   ├── lib/api.js          # API 클라이언트
│   │   └── App.js              # 메인 앱
│   ├── package.json        # Node 의존성
│   └── .env               # 환경변수 (생성됨)
├── install.bat            # 설치 스크립트
├── start_backend.bat      # 백엔드 시작
├── start_frontend.bat     # 프론트엔드 시작
├── start_all.bat          # 전체 시작
└── LOCAL_INSTALL.md       # 이 문서
```

---

## ⚙️ 환경변수 설정

### backend/.env
```env
# MongoDB 연결 (로컬 또는 Atlas)
MONGO_URL=mongodb://localhost:27017
DB_NAME=gvic_database

# CORS (프론트엔드 주소)
CORS_ORIGINS=http://localhost:3000

# JWT 시크릿 (변경 필수!)
JWT_SECRET_KEY=your-secret-key-change-in-production

# Stripe (실제 키로 교체)
STRIPE_API_KEY=sk_test_your_stripe_key

# 한국 결제 (선택사항 - 설정하면 실제 연동)
# KAKAOPAY_ADMIN_KEY=your_kakaopay_key
# KAKAOPAY_CID=your_kakaopay_cid
# NAVERPAY_CLIENT_ID=your_naverpay_id
# NAVERPAY_CLIENT_SECRET=your_naverpay_secret
# TOSS_CLIENT_KEY=your_toss_key
# TOSS_SECRET_KEY=your_toss_secret
```

### frontend/.env
```env
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## 🔧 수동 설치 (단계별)

### 1. Python 가상환경 설정
```batch
cd D:\gvic\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Node.js 패키지 설치
```batch
cd D:\gvic\frontend
npm install
```

### 3. MongoDB 시작
```batch
# MongoDB 로컬 설치 시
mongod --dbpath "C:\data\db"

# 또는 MongoDB Atlas 사용 시
# backend/.env의 MONGO_URL을 Atlas 연결 문자열로 변경
```

### 4. 백엔드 시작
```batch
cd D:\gvic\backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### 5. 프론트엔드 시작
```batch
cd D:\gvic\frontend
npm start
```

---

## 🧪 테스트 계정

| 항목 | 값 |
|------|---|
| **Email** | admin@gvic.com |
| **Password** | gvicgvic! |

---

## 🌐 접속 URL

| 서비스 | URL |
|--------|-----|
| **프론트엔드** | http://localhost:3000 |
| **백엔드 API** | http://localhost:8001 |
| **API 문서** | http://localhost:8001/docs |

---

## 💳 결제 수단 설정

### Stripe (해외 카드)
1. https://stripe.com 가입
2. Dashboard > Developers > API Keys
3. Secret Key를 `STRIPE_API_KEY`에 설정

### 카카오페이
1. https://developers.kakao.com 가입
2. 앱 생성 후 Admin Key 발급
3. `KAKAOPAY_ADMIN_KEY`, `KAKAOPAY_CID` 설정

### 네이버페이
1. https://developer.pay.naver.com 가입
2. 판매자센터에서 Client ID/Secret 발급
3. `NAVERPAY_CLIENT_ID`, `NAVERPAY_CLIENT_SECRET` 설정

### 토스페이먼츠
1. https://developers.tosspayments.com 가입
2. 테스트 키 발급
3. `TOSS_CLIENT_KEY`, `TOSS_SECRET_KEY` 설정

---

## ❓ 문제 해결

### MongoDB 연결 실패
```
[해결] MongoDB가 실행 중인지 확인
mongod --dbpath "C:\data\db"

또는 MongoDB Atlas 사용:
MONGO_URL=mongodb+srv://user:pass@cluster.mongodb.net/
```

### CORS 에러
```
[해결] backend/.env 확인
CORS_ORIGINS=http://localhost:3000
```

### 포트 충돌
```
[해결] 다른 포트 사용
백엔드: uvicorn server:app --port 8002
프론트엔드: set PORT=3001 && npm start
```

---

## 📞 지원

버전: 4.0.0
최종 업데이트: 2026-02-16
