#!/bin/bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     GVIC Engine - 7개 특허 모듈 통합 시스템               ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

INSTALL_DIR=$(pwd)
echo -e "${GREEN}[INFO]${NC} 설치 디렉토리: $INSTALL_DIR"

echo -e "${YELLOW}[1/6]${NC} 시스템 요구사항 확인..."
command -v python3 &>/dev/null && echo -e "  ${GREEN}✓${NC} Python: $(python3 --version | cut -d' ' -f2)" || { echo -e "  ${RED}✗${NC} Python3 필요"; exit 1; }
command -v node &>/dev/null && echo -e "  ${GREEN}✓${NC} Node.js: $(node --version)" || { echo -e "  ${RED}✗${NC} Node.js 필요"; exit 1; }
command -v yarn &>/dev/null && { echo -e "  ${GREEN}✓${NC} Yarn: $(yarn --version)"; USE_YARN=true; } || { echo -e "  ${YELLOW}!${NC} Yarn 없음, npm 사용"; USE_YARN=false; }

echo -e "${YELLOW}[2/6]${NC} 환경 설정 파일 생성..."
[ ! -f "backend/.env" ] && cp backend/.env.example backend/.env && echo -e "  ${GREEN}→${NC} backend/.env 생성"
[ ! -f "frontend/.env" ] && cp frontend/.env.example frontend/.env && echo -e "  ${GREEN}→${NC} frontend/.env 생성"

echo -e "${YELLOW}[3/6]${NC} Python 의존성 설치..."
cd backend
[ ! -d "venv" ] && python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo -e "  ${GREEN}✓${NC} Python 패키지 설치 완료"
cd "$INSTALL_DIR"

echo -e "${YELLOW}[4/6]${NC} Node.js 의존성 설치..."
cd frontend
[ "$USE_YARN" = true ] && yarn install --silent || npm install --silent
echo -e "  ${GREEN}✓${NC} Node.js 패키지 설치 완료"
cd "$INSTALL_DIR"

echo -e "${YELLOW}[5/6]${NC} 초기 설정 완료"
mkdir -p backend/data backend/config

echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              설치가 완료되었습니다!                       ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}[실행 방법]${NC}"
echo "  1. MongoDB 시작: mongod --dbpath /path/to/data/db"
echo "  2. Backend: cd backend && source venv/bin/activate && uvicorn server:app --host 0.0.0.0 --port 8001 --reload"
echo "  3. Frontend: cd frontend && yarn start (또는 npm start)"
echo "  4. 접속: http://localhost:3000"
echo ""
echo -e "${BLUE}[기본 계정]${NC} admin@gvic.com / password"
