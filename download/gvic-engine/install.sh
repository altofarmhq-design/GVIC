#!/bin/bash

#####################################################
# GVIC Engine 설치 스크립트
# 7개 특허 모듈 통합 시스템 - 로컬 서버 설치용
#####################################################

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로고 출력
echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                                                           ║"
echo "║     ██████╗ ██╗   ██╗██╗ ██████╗                         ║"
echo "║    ██╔════╝ ██║   ██║██║██╔════╝                         ║"
echo "║    ██║  ███╗██║   ██║██║██║                              ║"
echo "║    ██║   ██║╚██╗ ██╔╝██║██║                              ║"
echo "║    ╚██████╔╝ ╚████╔╝ ██║╚██████╗                         ║"
echo "║     ╚═════╝   ╚═══╝  ╚═╝ ╚═════╝  ENGINE                 ║"
echo "║                                                           ║"
echo "║          7개 특허 모듈 통합 시스템                        ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 현재 디렉토리 저장
INSTALL_DIR=$(pwd)

echo -e "${GREEN}[INFO]${NC} 설치 디렉토리: $INSTALL_DIR"
echo ""

#####################################################
# 1. 시스템 요구사항 확인
#####################################################
echo -e "${YELLOW}[1/6]${NC} 시스템 요구사항 확인 중..."

# Python 버전 확인
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "  ${GREEN}✓${NC} Python: $PYTHON_VERSION"
else
    echo -e "  ${RED}✗${NC} Python3가 설치되어 있지 않습니다."
    echo -e "    ${YELLOW}→${NC} Python 3.9 이상을 설치해주세요."
    exit 1
fi

# Node.js 버전 확인
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "  ${GREEN}✓${NC} Node.js: $NODE_VERSION"
else
    echo -e "  ${RED}✗${NC} Node.js가 설치되어 있지 않습니다."
    echo -e "    ${YELLOW}→${NC} Node.js 18 이상을 설치해주세요."
    exit 1
fi

# Yarn 확인 (없으면 npm 사용)
if command -v yarn &> /dev/null; then
    YARN_VERSION=$(yarn --version)
    echo -e "  ${GREEN}✓${NC} Yarn: $YARN_VERSION"
    USE_YARN=true
else
    echo -e "  ${YELLOW}!${NC} Yarn이 없습니다. npm을 사용합니다."
    USE_YARN=false
fi

# MongoDB 확인
if command -v mongod &> /dev/null; then
    echo -e "  ${GREEN}✓${NC} MongoDB: 설치됨"
else
    echo -e "  ${YELLOW}!${NC} MongoDB가 설치되어 있지 않습니다."
    echo -e "    ${YELLOW}→${NC} MongoDB를 설치하거나 원격 MongoDB URL을 설정해주세요."
fi

echo ""

#####################################################
# 2. 환경 설정 파일 생성
#####################################################
echo -e "${YELLOW}[2/6]${NC} 환경 설정 파일 생성 중..."

# Backend .env 파일 생성
if [ ! -f "backend/.env" ]; then
    echo -e "  ${GREEN}→${NC} backend/.env 파일 생성"
    cat > backend/.env << 'EOF'
# MongoDB 연결 설정
MONGO_URL="mongodb://localhost:27017"
DB_NAME="gvic_engine"

# CORS 설정 (프론트엔드 URL)
CORS_ORIGINS="http://localhost:3000"

# JWT 설정 (프로덕션에서는 반드시 변경하세요!)
JWT_SECRET_KEY="your-super-secret-key-change-this-in-production"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth 설정 (선택사항)
# GOOGLE_CLIENT_ID="your-google-client-id"
# GOOGLE_CLIENT_SECRET="your-google-client-secret"
EOF
else
    echo -e "  ${YELLOW}!${NC} backend/.env 파일이 이미 존재합니다. 건너뜁니다."
fi

# Frontend .env 파일 생성
if [ ! -f "frontend/.env" ]; then
    echo -e "  ${GREEN}→${NC} frontend/.env 파일 생성"
    cat > frontend/.env << 'EOF'
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# 개발 모드 설정
GENERATE_SOURCEMAP=true
EOF
else
    echo -e "  ${YELLOW}!${NC} frontend/.env 파일이 이미 존재합니다. 건너뜁니다."
fi

echo ""

#####################################################
# 3. Python 가상환경 및 의존성 설치
#####################################################
echo -e "${YELLOW}[3/6]${NC} Python 의존성 설치 중..."

cd backend

# 가상환경 생성
if [ ! -d "venv" ]; then
    echo -e "  ${GREEN}→${NC} Python 가상환경 생성"
    python3 -m venv venv
fi

# 가상환경 활성화
source venv/bin/activate

# pip 업그레이드
pip install --upgrade pip > /dev/null 2>&1

# 의존성 설치
echo -e "  ${GREEN}→${NC} Python 패키지 설치 중... (시간이 걸릴 수 있습니다)"
pip install -r requirements.txt > /dev/null 2>&1

echo -e "  ${GREEN}✓${NC} Python 의존성 설치 완료"

cd "$INSTALL_DIR"
echo ""

#####################################################
# 4. Node.js 의존성 설치
#####################################################
echo -e "${YELLOW}[4/6]${NC} Node.js 의존성 설치 중..."

cd frontend

if [ "$USE_YARN" = true ]; then
    echo -e "  ${GREEN}→${NC} yarn install 실행 중... (시간이 걸릴 수 있습니다)"
    yarn install > /dev/null 2>&1
else
    echo -e "  ${GREEN}→${NC} npm install 실행 중... (시간이 걸릴 수 있습니다)"
    npm install > /dev/null 2>&1
fi

echo -e "  ${GREEN}✓${NC} Node.js 의존성 설치 완료"

cd "$INSTALL_DIR"
echo ""

#####################################################
# 5. 초기 데이터 설정
#####################################################
echo -e "${YELLOW}[5/6]${NC} 초기 설정 확인..."

# data 디렉토리 확인
if [ ! -d "backend/data" ]; then
    mkdir -p backend/data
    echo -e "  ${GREEN}→${NC} backend/data 디렉토리 생성"
fi

# config 디렉토리 확인
if [ ! -d "backend/config" ]; then
    mkdir -p backend/config
    echo -e "  ${GREEN}→${NC} backend/config 디렉토리 생성"
fi

echo -e "  ${GREEN}✓${NC} 초기 설정 완료"
echo ""

#####################################################
# 6. 설치 완료
#####################################################
echo -e "${YELLOW}[6/6]${NC} 설치 완료!"
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              설치가 완료되었습니다!                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}[실행 방법]${NC}"
echo ""
echo -e "  ${YELLOW}1. MongoDB 시작${NC} (별도 터미널)"
echo -e "     mongod --dbpath /path/to/data/db"
echo ""
echo -e "  ${YELLOW}2. Backend 서버 시작${NC} (별도 터미널)"
echo -e "     cd $INSTALL_DIR/backend"
echo -e "     source venv/bin/activate"
echo -e "     uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo ""
echo -e "  ${YELLOW}3. Frontend 서버 시작${NC} (별도 터미널)"
echo -e "     cd $INSTALL_DIR/frontend"
if [ "$USE_YARN" = true ]; then
echo -e "     yarn start"
else
echo -e "     npm start"
fi
echo ""
echo -e "  ${YELLOW}4. 브라우저에서 접속${NC}"
echo -e "     http://localhost:3000"
echo ""
echo -e "${BLUE}[기본 관리자 계정]${NC}"
echo -e "  이메일: admin@gvic.com"
echo -e "  비밀번호: password"
echo ""
echo -e "${BLUE}[문서]${NC}"
echo -e "  README.md 파일을 참조하세요."
echo ""
echo -e "${YELLOW}주의:${NC} 프로덕션 환경에서는 반드시 .env 파일의 JWT_SECRET_KEY를 변경하세요!"
echo ""
