#!/bin/bash

#####################################################
# GVIC Engine 실행 스크립트
# 백엔드와 프론트엔드를 동시에 시작합니다
#####################################################

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR=$(pwd)

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              GVIC Engine 시작 중...                       ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# MongoDB 확인
echo -e "${YELLOW}[1/3]${NC} MongoDB 연결 확인..."
if command -v mongosh &> /dev/null; then
    if mongosh --eval "db.runCommand({ ping: 1 })" --quiet > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} MongoDB 연결 성공"
    else
        echo -e "  ${RED}✗${NC} MongoDB에 연결할 수 없습니다."
        echo -e "    ${YELLOW}→${NC} MongoDB를 먼저 시작해주세요."
        exit 1
    fi
else
    echo -e "  ${YELLOW}!${NC} mongosh가 없습니다. MongoDB 연결을 확인할 수 없습니다."
    echo -e "    ${YELLOW}→${NC} MongoDB가 실행 중인지 확인해주세요."
fi

echo ""

# Backend 시작
echo -e "${YELLOW}[2/3]${NC} Backend 서버 시작..."
cd "$INSTALL_DIR/backend"
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload &
BACKEND_PID=$!
echo -e "  ${GREEN}✓${NC} Backend 시작됨 (PID: $BACKEND_PID)"

sleep 2

# Frontend 시작
echo -e "${YELLOW}[3/3]${NC} Frontend 서버 시작..."
cd "$INSTALL_DIR/frontend"

if command -v yarn &> /dev/null; then
    yarn start &
else
    npm start &
fi
FRONTEND_PID=$!
echo -e "  ${GREEN}✓${NC} Frontend 시작됨 (PID: $FRONTEND_PID)"

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              GVIC Engine이 시작되었습니다!                ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Backend:${NC}  http://localhost:8001"
echo -e "  ${BLUE}Frontend:${NC} http://localhost:3000"
echo ""
echo -e "  ${YELLOW}종료하려면 Ctrl+C를 누르세요.${NC}"
echo ""

# 시그널 핸들러
cleanup() {
    echo ""
    echo -e "${YELLOW}서버를 종료합니다...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}종료 완료.${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 프로세스 대기
wait
